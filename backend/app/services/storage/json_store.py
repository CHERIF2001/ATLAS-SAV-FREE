"""
Implémentation JSON du stockage des tickets.
Utilise un fichier JSON avec locking pour la concurrence.
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException

from .interface import TicketStorage

logger = logging.getLogger(__name__)


class JSONStorage(TicketStorage):
    """Stockage des tickets dans un fichier JSON."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._lock = asyncio.Lock()
        logger.info(f"JSONStorage initialized with file: {file_path}")

    async def _load_all(self) -> Dict[str, dict]:
        """Charger tous les tickets depuis le fichier."""
        async with self._lock:
            if not self.file_path.exists():
                return {}
            try:
                content = await asyncio.to_thread(
                    lambda: self.file_path.read_text(encoding="utf-8")
                )
                return json.loads(content)
            except Exception as e:
                logger.exception(f"Error reading tickets file: {e}")
                return {}

    async def _save_all(self, tickets: Dict[str, dict]) -> None:
        """Sauvegarder tous les tickets dans le fichier."""
        async with self._lock:
            try:
                content = json.dumps(tickets, ensure_ascii=False, indent=2)
                await asyncio.to_thread(
                    lambda: self.file_path.write_text(content, encoding="utf-8")
                )
            except Exception as e:
                logger.exception(f"Error writing tickets file: {e}")
                raise

    async def save_ticket(self, ticket: dict) -> None:
        """Sauvegarder un ticket."""
        tickets = await self._load_all()
        tickets[ticket["ticket_id"]] = ticket
        await self._save_all(tickets)
        logger.info(f"Ticket saved: {ticket['ticket_id']}")

    async def get_ticket(self, ticket_id: str) -> dict:
        """Récupérer un ticket par son ID."""
        tickets = await self._load_all()
        if ticket_id not in tickets:
            raise HTTPException(status_code=404, detail="Ticket non trouvé")
        return tickets[ticket_id]

    async def list_tickets(
        self,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[dict]:
        """Lister les tickets avec filtres optionnels."""
        tickets = await self._load_all()
        result = list(tickets.values())

        # Filtrer par statut
        if status:
            result = [t for t in result if t.get("status") == status]

        # Filtrer par canal
        if channel:
            result = [t for t in result if t.get("channel") == channel]

        # Filtrer par date de création (from)
        if date_from:
            result = [t for t in result if t.get("created_at", "") >= date_from]

        # Filtrer par date de création (to)
        if date_to:
            result = [t for t in result if t.get("created_at", "") <= date_to]

        # Trier par date de création (plus récent en premier)
        result.sort(key=lambda t: t.get("created_at", ""), reverse=True)

        return result

    async def update_ticket_status(
        self, ticket_id: str, status: str, closed_at: Optional[str] = None
    ) -> dict:
        """Mettre à jour le statut d'un ticket."""
        tickets = await self._load_all()
        
        if ticket_id not in tickets:
            raise HTTPException(status_code=404, detail="Ticket non trouvé")

        ticket = tickets[ticket_id]
        old_status = ticket.get("status")
        ticket["status"] = status

        # Si on ferme le ticket
        if status == "fermé" and closed_at:
            ticket["closed_at"] = closed_at
            
            # Calculer la durée de résolution
            if "created_at" in ticket:
                try:
                    created = datetime.fromisoformat(ticket["created_at"].replace("Z", "+00:00"))
                    closed = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                    duration = (closed - created).total_seconds()
                    ticket["resolution_duration"] = int(duration)
                except Exception as e:
                    logger.warning(f"Could not calculate resolution duration: {e}")

        # Si on réouvre le ticket
        if status == "en cours" and old_status == "fermé":
            ticket["closed_at"] = None
            ticket["resolution_duration"] = None

        await self._save_all(tickets)
        logger.info(f"Ticket {ticket_id} status updated: {old_status} -> {status}")
        
        return ticket

    async def ticket_exists(self, ticket_id: str) -> bool:
        """Vérifier si un ticket existe."""
        tickets = await self._load_all()
        return ticket_id in tickets

    async def add_message(self, ticket_id: str, message: dict) -> None:
        """Ajouter un message à un ticket."""
        tickets = await self._load_all()
        if ticket_id not in tickets:
            raise HTTPException(status_code=404, detail="Ticket non trouvé")
        
        if "messages" not in tickets[ticket_id]:
            tickets[ticket_id]["messages"] = []
            
        tickets[ticket_id]["messages"].append(message)
        await self._save_all(tickets)
        logger.info(f"Message added to ticket {ticket_id}")

    async def update_ticket(self, ticket_id: str, updates: dict) -> dict:
        """Mettre à jour un ticket."""
        tickets = await self._load_all()
        if ticket_id not in tickets:
            raise HTTPException(status_code=404, detail="Ticket non trouvé")

        ticket = tickets[ticket_id]
        ticket.update(updates)
        
        await self._save_all(tickets)
        logger.info(f"Ticket updated: {ticket_id}")
        return ticket

    async def delete_ticket(self, ticket_id: str) -> None:
        """Supprimer un ticket."""
        tickets = await self._load_all()
        if ticket_id in tickets:
            del tickets[ticket_id]
            await self._save_all(tickets)
            logger.info(f"Ticket deleted: {ticket_id}")

    async def close(self) -> None:
        """Fermer les connexions (rien à faire pour JSON)."""
        logger.info("JSONStorage closed")
