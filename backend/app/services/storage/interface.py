"""Storage interface and factory for ticket storage implementations."""
from abc import ABC, abstractmethod
from typing import List, Optional

class TicketStorage(ABC):
    """Interface abstraite pour le stockage des tickets."""

    @abstractmethod
    async def save_ticket(self, ticket: dict) -> None:
        """Sauvegarder un ticket."""
        pass

    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> dict:
        """Récupérer un ticket par son ID."""
        pass

    @abstractmethod
    async def list_tickets(
        self,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[dict]:
        """Lister les tickets avec filtres optionnels."""
        pass

    @abstractmethod
    async def update_ticket_status(
        self, ticket_id: str, status: str, closed_at: Optional[str] = None
    ) -> dict:
        """Mettre à jour le statut d'un ticket."""
        pass

    @abstractmethod
    async def ticket_exists(self, ticket_id: str) -> bool:
        """Vérifier si un ticket existe."""
        pass

    @abstractmethod
    async def add_message(self, ticket_id: str, message: dict) -> None:
        """Ajouter un message à un ticket."""
        pass

    @abstractmethod
    async def update_ticket(self, ticket_id: str, updates: dict) -> dict:
        """Mettre à jour un ticket avec un dictionnaire de champs."""
        pass

    @abstractmethod
    async def delete_ticket(self, ticket_id: str) -> None:
        """Supprimer un ticket."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Fermer les connexions et libérer les ressources."""
        pass

def get_storage() -> TicketStorage:
    """Factory to obtain the appropriate storage implementation.

    - If STORAGE_TYPE == "dynamodb", returns a DynamoDBStorage instance.
    - Otherwise, returns a JSONStorage instance using the configured TICKETS_FILE.
    """
    from app.core.config import STORAGE_TYPE, TICKETS_FILE, DYNAMODB_TABLE_TICKETS, AWS_REGION
    if STORAGE_TYPE == "dynamodb":
        from app.services.storage.dynamodb_store import DynamoDBStorage
        return DynamoDBStorage(table_name=DYNAMODB_TABLE_TICKETS, region=AWS_REGION)
    else:
        from app.services.storage.json_store import JSONStorage
        return JSONStorage(file_path=TICKETS_FILE)
