"""
Service d'export CSV des tickets pour le dashboard.
Génère un CSV enrichi avec toutes les analytics et métriques.
"""
import csv
import io
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class ExportService:
    """Service d'export CSV des tickets."""

    def __init__(self, storage):
        """
        Initialiser le service d'export.
        
        Args:
            storage: Instance de TicketStorage
        """
        self.storage = storage
        logger.info("ExportService initialized")

    async def generate_csv(
        self,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> str:
        """
        Générer un CSV avec tous les tickets filtrés.
        
        Args:
            status: Filtrer par statut
            channel: Filtrer par canal
            date_from: Date de début (ISO format)
            date_to: Date de fin (ISO format)
            
        Returns:
            str: Contenu du CSV
        """
        # Récupérer les tickets filtrés
        tickets = await self.storage.list_tickets(
            status=status,
            channel=channel,
            date_from=date_from,
            date_to=date_to
        )

        # Générer le CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # En-têtes
        headers = [
            "ticket_id",
            "created_at",
            "closed_at",
            "status",
            "channel",
            "sentiment",
            "category",
            "urgency",
            "summary",
            "messages_count",
            "resolution_duration_seconds",
            "resolution_duration_hours",
            "first_response_time_seconds",
            "avg_response_time_seconds",
        ]
        writer.writerow(headers)

        # Données
        for ticket in tickets:
            row = self._ticket_to_row(ticket)
            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        logger.info(f"CSV generated with {len(tickets)} tickets")
        return csv_content

    async def generate_single_ticket_csv(self, ticket_id: str) -> str:
        """
        Générer un CSV pour un seul ticket.
        
        Args:
            ticket_id: ID du ticket
            
        Returns:
            str: Contenu du CSV
        """
        ticket = await self.storage.get_ticket(ticket_id)

        output = io.StringIO()
        writer = csv.writer(output)

        # En-têtes
        headers = [
            "ticket_id",
            "created_at",
            "closed_at",
            "status",
            "channel",
            "sentiment",
            "category",
            "urgency",
            "summary",
            "messages_count",
            "resolution_duration_seconds",
            "resolution_duration_hours",
            "first_response_time_seconds",
            "avg_response_time_seconds",
        ]
        writer.writerow(headers)

        # Données
        row = self._ticket_to_row(ticket)
        writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        logger.info(f"CSV generated for ticket {ticket_id}")
        return csv_content

    def _ticket_to_row(self, ticket: dict) -> List[str]:
        """Convertir un ticket en ligne CSV."""
        analytics = ticket.get("analytics", {})
        
        # Calculer les métriques
        messages = ticket.get("messages", [])
        messages_count = len(messages)
        
        # Temps de première réponse (temps entre premier message user et premier message assistant)
        first_response_time = self._calculate_first_response_time(messages)
        
        # Temps de réponse moyen
        avg_response_time = self._calculate_avg_response_time(messages)
        
        # Durée de résolution
        resolution_duration = ticket.get("resolution_duration", "")
        resolution_hours = ""
        if resolution_duration:
            try:
                resolution_hours = f"{float(resolution_duration) / 3600:.2f}"
            except:
                pass

        return [
            ticket.get("ticket_id", ""),
            ticket.get("created_at", ""),
            ticket.get("closed_at", ""),
            ticket.get("status", ""),
            ticket.get("channel", ""),
            analytics.get("sentiment", ""),
            analytics.get("category", ""),
            analytics.get("urgency", ""),
            analytics.get("summary", ""),
            str(messages_count),
            str(resolution_duration) if resolution_duration else "",
            resolution_hours,
            str(first_response_time) if first_response_time else "",
            str(avg_response_time) if avg_response_time else "",
        ]

    def _calculate_first_response_time(self, messages: List[dict]) -> Optional[int]:
        """Calculer le temps de première réponse en secondes."""
        try:
            user_msg = None
            assistant_msg = None
            
            for msg in messages:
                if msg.get("role") == "user" and not user_msg:
                    user_msg = msg
                elif msg.get("role") == "assistant" and user_msg and not assistant_msg:
                    assistant_msg = msg
                    break
            
            if user_msg and assistant_msg:
                user_time = datetime.fromisoformat(user_msg["timestamp"].replace("Z", "+00:00"))
                assistant_time = datetime.fromisoformat(assistant_msg["timestamp"].replace("Z", "+00:00"))
                delta = (assistant_time - user_time).total_seconds()
                return int(delta)
        except Exception as e:
            logger.warning(f"Could not calculate first response time: {e}")
        
        return None

    def _calculate_avg_response_time(self, messages: List[dict]) -> Optional[int]:
        """Calculer le temps de réponse moyen en secondes."""
        try:
            response_times = []
            last_user_msg = None
            
            for msg in messages:
                if msg.get("role") == "user":
                    last_user_msg = msg
                elif msg.get("role") == "assistant" and last_user_msg:
                    user_time = datetime.fromisoformat(last_user_msg["timestamp"].replace("Z", "+00:00"))
                    assistant_time = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                    delta = (assistant_time - user_time).total_seconds()
                    response_times.append(delta)
                    last_user_msg = None
            
            if response_times:
                avg = sum(response_times) / len(response_times)
                return int(avg)
        except Exception as e:
            logger.warning(f"Could not calculate avg response time: {e}")
        
        return None
