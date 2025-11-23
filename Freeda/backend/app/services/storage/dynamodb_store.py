"""
Implémentation DynamoDB du stockage des tickets.
Production-ready avec retry logic, error handling, et indexes secondaires.
"""
import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import HTTPException

from .interface import TicketStorage

logger = logging.getLogger(__name__)


def decimal_to_float(obj: Any) -> Any:
    """Convertir les Decimal de DynamoDB en float/int pour JSON."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj


def float_to_decimal(obj: Any) -> Any:
    """Convertir les float/int en Decimal pour DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, int) and not isinstance(obj, bool):
        return Decimal(obj)
    elif isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [float_to_decimal(item) for item in obj]
    return obj


class DynamoDBStorage(TicketStorage):
    """
    Stockage des tickets dans DynamoDB.
    
    Table Schema:
    - Primary Key: ticket_id (String)
    - GSI1: status-created_at-index (pour filtrer par statut)
    - GSI2: channel-created_at-index (pour filtrer par canal)
    
    Attributes:
    - ticket_id: UUID unique
    - status: "en cours" | "fermé"
    - channel: "chat" | "telephone" | "whatsapp" | "sms" | "email"
    - created_at: ISO timestamp
    - closed_at: ISO timestamp (nullable)
    - resolution_duration: int (secondes, nullable)
    - analytics: dict (sentiment, category, urgency, summary)
    - messages: list of messages
    """

    def __init__(
        self,
        table_name: str,
        region: str = "eu-west-1",
        max_retries: int = 3,
    ):
        self.table_name = table_name
        self.region = region
        self.max_retries = max_retries
        
        try:
            # Initialiser le client DynamoDB
            self.dynamodb = boto3.resource("dynamodb", region_name=region)
            self.table = self.dynamodb.Table(table_name)
            
            # Vérifier que la table existe
            self.table.load()
            logger.info(f"DynamoDBStorage initialized: table={table_name}, region={region}")
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logger.error(f"DynamoDB table '{table_name}' not found in region '{region}'")
                raise HTTPException(
                    status_code=500,
                    detail=f"DynamoDB table '{table_name}' does not exist. Please create it first."
                )
            else:
                logger.error(f"Failed to connect to DynamoDB: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to connect to DynamoDB: {str(e)}"
                )
        except Exception as e:
            logger.error(f"Unexpected error initializing DynamoDB: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize DynamoDB storage: {str(e)}"
            )

    async def _retry_operation(self, operation, *args, **kwargs):
        """Exécuter une opération avec retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Exécuter l'opération dans un thread pour ne pas bloquer
                result = await asyncio.to_thread(operation, *args, **kwargs)
                return result
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                last_error = e
                
                # Erreurs non-retriables
                if error_code in ["ResourceNotFoundException", "ValidationException"]:
                    raise
                
                # Erreurs retriables (throttling, etc.)
                if error_code in ["ProvisionedThroughputExceededException", "ThrottlingException"]:
                    wait_time = (2 ** attempt) * 0.1  # Exponential backoff
                    logger.warning(
                        f"DynamoDB throttled, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                # Autres erreurs
                logger.error(f"DynamoDB error: {error_code} - {e}")
                raise HTTPException(status_code=500, detail=f"Database error: {error_code}")
            
            except BotoCoreError as e:
                last_error = e
                logger.error(f"BotoCore error: {e}")
                raise HTTPException(status_code=500, detail="Database connection error")
        
        # Si on arrive ici, toutes les tentatives ont échoué
        logger.error(f"All retry attempts failed: {last_error}")
        raise HTTPException(status_code=500, detail="Database operation failed after retries")

    async def save_ticket(self, ticket: dict) -> None:
        """Sauvegarder un ticket dans DynamoDB."""
        try:
            # Convertir les float en Decimal pour DynamoDB
            item = float_to_decimal(ticket)
            
            await self._retry_operation(self.table.put_item, Item=item)
            logger.info(f"Ticket saved to DynamoDB: {ticket['ticket_id']}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error saving ticket to DynamoDB: {e}")
            raise HTTPException(status_code=500, detail="Failed to save ticket")

    async def get_ticket(self, ticket_id: str) -> dict:
        """Récupérer un ticket depuis DynamoDB."""
        try:
            response = await self._retry_operation(
                self.table.get_item,
                Key={"ticket_id": ticket_id}
            )
            
            if "Item" not in response:
                raise HTTPException(status_code=404, detail="Ticket non trouvé")
            
            # Convertir les Decimal en float/int
            ticket = decimal_to_float(response["Item"])
            return ticket
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting ticket from DynamoDB: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve ticket")

    async def list_tickets(
        self,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[dict]:
        """Lister les tickets depuis DynamoDB avec filtres."""
        try:
            # Si on filtre par statut, utiliser le GSI status-created_at-index
            if status:
                response = await self._retry_operation(
                    self.table.query,
                    IndexName="status-created_at-index",
                    KeyConditionExpression=Key("status").eq(status),
                    ScanIndexForward=False  # Tri décroissant par created_at
                )
                items = response.get("Items", [])
            
            # Si on filtre par channel, utiliser le GSI channel-created_at-index
            elif channel:
                response = await self._retry_operation(
                    self.table.query,
                    IndexName="channel-created_at-index",
                    KeyConditionExpression=Key("channel").eq(channel),
                    ScanIndexForward=False
                )
                items = response.get("Items", [])
            
            # Sinon, faire un scan (moins performant mais nécessaire)
            else:
                response = await self._retry_operation(self.table.scan)
                items = response.get("Items", [])
            
            # Appliquer les filtres supplémentaires en mémoire
            result = items
            
            if channel and status:  # Si on a déjà filtré par status, filtrer par channel
                result = [t for t in result if t.get("channel") == channel]
            
            if status and not channel:  # Si on a déjà filtré par channel, filtrer par status
                # Déjà filtré par le query
                pass
            
            if date_from:
                result = [t for t in result if t.get("created_at", "") >= date_from]
            
            if date_to:
                result = [t for t in result if t.get("created_at", "") <= date_to]
            
            # Trier par date de création (plus récent en premier)
            result.sort(key=lambda t: t.get("created_at", ""), reverse=True)
            
            # Convertir les Decimal en float/int
            result = [decimal_to_float(ticket) for ticket in result]
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error listing tickets from DynamoDB: {e}")
            raise HTTPException(status_code=500, detail="Failed to list tickets")

    async def update_ticket_status(
        self, ticket_id: str, status: str, closed_at: Optional[str] = None
    ) -> dict:
        """Mettre à jour le statut d'un ticket dans DynamoDB."""
        try:
            # Récupérer le ticket pour calculer la durée
            ticket = await self.get_ticket(ticket_id)
            old_status = ticket.get("status")
            
            # Préparer les updates
            update_expression = "SET #status = :status"
            expression_names = {"#status": "status"}
            expression_values = {":status": status}
            
            # Si on ferme le ticket
            if status == "fermé" and closed_at:
                update_expression += ", closed_at = :closed_at"
                expression_values[":closed_at"] = closed_at
                
                # Calculer la durée de résolution
                if "created_at" in ticket:
                    try:
                        created = datetime.fromisoformat(ticket["created_at"].replace("Z", "+00:00"))
                        closed = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                        duration = int((closed - created).total_seconds())
                        
                        update_expression += ", resolution_duration = :duration"
                        expression_values[":duration"] = duration
                    except Exception as e:
                        logger.warning(f"Could not calculate resolution duration: {e}")
            
            # Si on réouvre le ticket
            if status == "en cours" and old_status == "fermé":
                update_expression += ", closed_at = :null_closed, resolution_duration = :null_duration"
                expression_values[":null_closed"] = None
                expression_values[":null_duration"] = None
            
            # Convertir les valeurs en Decimal
            expression_values = float_to_decimal(expression_values)
            
            # Mettre à jour dans DynamoDB
            response = await self._retry_operation(
                self.table.update_item,
                Key={"ticket_id": ticket_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues="ALL_NEW"
            )
            
            updated_ticket = decimal_to_float(response["Attributes"])
            logger.info(f"Ticket {ticket_id} status updated: {old_status} -> {status}")
            
            return updated_ticket
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error updating ticket status in DynamoDB: {e}")
            raise HTTPException(status_code=500, detail="Failed to update ticket status")

    async def ticket_exists(self, ticket_id: str) -> bool:
        """Vérifier si un ticket existe dans DynamoDB."""
        try:
            response = await self._retry_operation(
                self.table.get_item,
                Key={"ticket_id": ticket_id},
                ProjectionExpression="ticket_id"  # Ne récupérer que l'ID pour performance
            )
            return "Item" in response
            
        except Exception as e:
            logger.exception(f"Error checking ticket existence in DynamoDB: {e}")
            return False

    async def add_message(self, ticket_id: str, message: dict) -> None:
        """Ajouter un message à un ticket dans DynamoDB."""
        try:
            # Convertir en Decimal
            message_item = float_to_decimal(message)
            
            # Si la liste messages n'existe pas, on la crée avec le message
            # Sinon on ajoute à la fin
            await self._retry_operation(
                self.table.update_item,
                Key={"ticket_id": ticket_id},
                UpdateExpression="SET messages = list_append(if_not_exists(messages, :empty_list), :message)",
                ExpressionAttributeValues={
                    ":message": [message_item],
                    ":empty_list": []
                }
            )
            logger.info(f"Message added to ticket {ticket_id} in DynamoDB")
            
        except Exception as e:
            logger.exception(f"Error adding message to DynamoDB: {e}")
            raise HTTPException(status_code=500, detail="Failed to add message")

    async def update_ticket(self, ticket_id: str, updates: dict) -> dict:
        """Mettre à jour un ticket avec un dictionnaire de champs."""
        try:
            # Convertir en Decimal
            updates_decimal = float_to_decimal(updates)
            
            update_expression = "SET"
            expression_names = {}
            expression_values = {}
            
            for i, (key, value) in enumerate(updates_decimal.items()):
                # Ignorer ticket_id car c'est la clé
                if key == "ticket_id":
                    continue
                    
                attr_name = f"#{key}"
                attr_value = f":{key}"
                
                update_expression += f" {attr_name} = {attr_value},"
                expression_names[attr_name] = key
                expression_values[attr_value] = value
            
            # Enlever la dernière virgule
            update_expression = update_expression.rstrip(",")
            
            if not expression_names:
                return await self.get_ticket(ticket_id)
                
            response = await self._retry_operation(
                self.table.update_item,
                Key={"ticket_id": ticket_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues="ALL_NEW"
            )
            
            updated_ticket = decimal_to_float(response["Attributes"])
            logger.info(f"Ticket updated in DynamoDB: {ticket_id}")
            return updated_ticket
            
        except Exception as e:
            logger.exception(f"Error updating ticket in DynamoDB: {e}")
            raise HTTPException(status_code=500, detail="Failed to update ticket")

    async def delete_ticket(self, ticket_id: str) -> None:
        """Supprimer un ticket de DynamoDB."""
        try:
            await self._retry_operation(
                self.table.delete_item,
                Key={"ticket_id": ticket_id}
            )
            logger.info(f"Ticket deleted from DynamoDB: {ticket_id}")
            
        except Exception as e:
            logger.exception(f"Error deleting ticket from DynamoDB: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete ticket")

    async def health_check(self) -> bool:
        """Vérifier que DynamoDB est accessible."""
        try:
            await self._retry_operation(self.table.load)
            return True
        except Exception as e:
            logger.error(f"DynamoDB health check failed: {e}")
            return False

    async def close(self) -> None:
        """Fermer les connexions DynamoDB."""
        logger.info("DynamoDBStorage closed")
        # boto3 gère automatiquement les connexions, rien à faire
