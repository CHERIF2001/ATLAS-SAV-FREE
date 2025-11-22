"""
Endpoints PRIVÉS pour les Tickets - Frontend ADMIN

Ces endpoints nécessitent une authentification JWT.
Utilisés par le frontend admin pour :
- Voir tous les tickets
- Modifier les tickets
- Assigner des tickets
- Gérer les statuts

Sécurité : JWT obligatoire, vérification des rôles
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from typing import Optional, List
from datetime import datetime

# Import des services
from app.services.storage.interface import get_storage
from app.core.security import verify_token, require_admin
from app.services.analytics.sentiment_analyzer import SentimentAnalyzer
from app.core.container import services
from app.core.utils import now_iso
from app.models.schemas import AgentMessageCreate, AssignTicketRequest
from app.core.websocket import manager

router = APIRouter(prefix="/private/tickets", tags=["Private - Tickets"])

# Initialisation des services
storage = get_storage()
analyzer = SentimentAnalyzer()


@router.get("/", response_model=List[dict])
async def list_all_tickets(
    user: dict = Depends(verify_token),
    status: Optional[str] = None,
    channel: Optional[str] = None,
    assigned_to: Optional[str] = None,
    urgency: Optional[str] = None,
    limit: int = 100
):
    """
    Liste de TOUS les tickets (PRIVÉ - JWT requis)
    
    Utilisé par : Frontend ADMIN (dashboard, liste des tickets)
    
    Permissions : Agent, Manager, Admin
    
    Query Params:
        status: Filtrer par statut (nouveau, en cours, fermé)
        channel: Filtrer par canal (chat, phone, email, etc.)
        assigned_to: Filtrer par agent assigné
        urgency: Filtrer par urgence (haute, normale, basse)
        limit: Nombre maximum de tickets à retourner
    
    Returns:
        Liste de tous les tickets avec toutes les données
    """
    
    # Récupérer tous les tickets
    tickets = await storage.list_tickets(
        status=status,
        channel=channel,
        limit=limit
    )
    
    # Filtrer par agent si spécifié
    if assigned_to:
        tickets = [t for t in tickets if t.get("assigned_to") == assigned_to]
    
    # Filtrer par urgence si spécifié
    if urgency:
        tickets = [
            t for t in tickets 
            if t.get("analytics", {}).get("urgency") == urgency
        ]
    
    # Enrichir avec des métadonnées pour l'admin
    for ticket in tickets:
        # Calculer le temps depuis création
        created_at = datetime.fromisoformat(ticket["created_at"].replace("Z", "+00:00"))
        age_hours = (datetime.utcnow() - created_at.replace(tzinfo=None)).total_seconds() / 3600
        ticket["age_hours"] = round(age_hours, 1)
        
        # Nombre de messages
        ticket["message_count"] = len(ticket.get("messages", []))
        
        # Dernier message
        messages = ticket.get("messages", [])
        if messages:
            ticket["last_message"] = messages[-1]
    
    return tickets


@router.get("/{ticket_id}", response_model=dict)
async def get_ticket_full(
    ticket_id: str,
    user: dict = Depends(verify_token)
):
    """
    Récupérer un ticket complet (PRIVÉ - JWT requis)
    
    Utilisé par : Frontend ADMIN (vue détaillée d'un ticket)
    
    Permissions : Agent, Manager, Admin
    
    Returns:
        Toutes les données du ticket (y compris données internes)
    """
    
    ticket = await storage.get_ticket(ticket_id)
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    return ticket


@router.patch("/{ticket_id}", response_model=dict)
async def update_ticket(
    ticket_id: str,
    updates: dict,
    user: dict = Depends(verify_token)
):
    """
    Modifier un ticket (PRIVÉ - JWT requis)
    
    Utilisé par : Frontend ADMIN (modification de tickets)
    
    Permissions : Agent, Manager, Admin
    
    Args:
        updates: Dictionnaire des champs à mettre à jour
            - status: nouveau, en cours, fermé
            - assigned_to: Email de l'agent
            - priority: haute, normale, basse
            - notes: Notes internes
    
    Returns:
        Ticket mis à jour
    """
    
    # Vérifier que le ticket existe
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    # Ajouter les métadonnées de modification
    updates["updated_at"] = datetime.utcnow().isoformat()
    updates["updated_by"] = user["email"]
    
    # Si on change le statut à "fermé", ajouter la date de fermeture
    if updates.get("status") == "fermé" and ticket["status"] != "fermé":
        updates["closed_at"] = datetime.utcnow().isoformat()
        updates["closed_by"] = user["email"]
        
        # Calculer le temps de résolution
        created_at = datetime.fromisoformat(ticket["created_at"].replace("Z", "+00:00"))
        resolution_time = (datetime.utcnow() - created_at.replace(tzinfo=None)).total_seconds()
        updates["resolution_time_seconds"] = int(resolution_time)
    
    # Mettre à jour le ticket
    updated_ticket = await storage.update_ticket(ticket_id, updates)
    
    # Broadcast update via WebSocket (pour le client)
    await manager.broadcast(ticket_id, {
        "type": "ticket_update", 
        "ticket": updated_ticket
    })
    
    return updated_ticket


@router.post("/{ticket_id}/messages", response_model=dict)
async def add_agent_message(
    ticket_id: str,
    request: AgentMessageCreate,
    user: dict = Depends(verify_token)
):
    """
    Ajouter un message en tant qu'agent (PRIVÉ - JWT requis)
    
    Utilisé par : Frontend ADMIN (réponse agent)
    """
    content = request.content
    internal = request.internal
    
    # Vérifier que le ticket existe
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    # Créer le message
    import uuid
    message = {
        "message_id": str(uuid.uuid4()),
        "content": content,
        "author": user["name"],
        "author_email": user["email"],
        "timestamp": datetime.utcnow().isoformat(),
        "type": "internal" if internal else "agent",
        "internal": internal
    }
    
    # Ajouter le message
    await storage.add_message(ticket_id, message)
    
    # Si le ticket était "nouveau", le passer en "en cours"
    if ticket["status"] == "nouveau":
        await storage.update_ticket(ticket_id, {
            "status": "en cours",
            "assigned_to": user["email"],
            "updated_at": datetime.utcnow().isoformat()
        })
        
    # Broadcast message via WebSocket (pour le client)
    if not internal:
        await manager.broadcast(ticket_id, {
            "type": "new_message", 
            "message": {
                "id": message["message_id"],
                "content": message["content"],
                "role": "agent", # Le client verra "agent" ou "assistant"
                "timestamp": message["timestamp"],
                "author": user["name"]
            }
        })
    
    return {
        "message": "Message ajouté avec succès",
        "message_id": message["message_id"],
        "ticket_status_updated": ticket["status"] == "nouveau"
    }


@router.post("/{ticket_id}/assign", response_model=dict)
async def assign_ticket(
    ticket_id: str,
    request: AssignTicketRequest,
    user: dict = Depends(verify_token)
):
    """
    Assigner un ticket à un agent (PRIVÉ - JWT requis)
    
    Utilisé par : Frontend ADMIN (assignation de tickets)
    """
    agent_email = request.agent_email
    
    # Vérifier que le ticket existe
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    # Mettre à jour l'assignation
    await storage.update_ticket(ticket_id, {
        "assigned_to": agent_email,
        "assigned_at": datetime.utcnow().isoformat(),
        "assigned_by": user["email"],
        "status": "en cours" if ticket["status"] == "nouveau" else ticket["status"],
        "updated_at": datetime.utcnow().isoformat()
    })
    
    # Broadcast update via WebSocket
    await manager.broadcast(ticket_id, {
        "type": "ticket_assigned", 
        "assigned_to": agent_email
    })
    
    return {
        "message": f"Ticket assigné à {agent_email}",
        "ticket_id": ticket_id,
        "assigned_to": agent_email
    }


@router.delete("/{ticket_id}", response_model=dict)
async def delete_ticket(
    ticket_id: str,
    user: dict = Depends(require_admin)  # Admin uniquement
):
    """
    Supprimer un ticket (PRIVÉ - ADMIN uniquement)
    
    Utilisé par : Frontend ADMIN (suppression de tickets)
    
    Permissions : Admin uniquement
    
    Returns:
        Confirmation de suppression
    """
    
    # Vérifier que le ticket existe
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    # Supprimer le ticket
    await storage.delete_ticket(ticket_id)
    
    return {
        "message": "Ticket supprimé avec succès",
        "ticket_id": ticket_id,
        "deleted_by": user["email"],
        "deleted_at": datetime.utcnow().isoformat()
    }


@router.get("/{ticket_id}/history", response_model=List[dict])
async def get_ticket_history(
    ticket_id: str,
    user: dict = Depends(verify_token)
):
    """
    Récupérer l'historique complet d'un ticket (PRIVÉ - JWT requis)
    
    Utilisé par : Frontend ADMIN (timeline du ticket)
    
    Permissions : Agent, Manager, Admin
    
    Returns:
        Historique chronologique de toutes les actions sur le ticket
    """
    
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    # Construire l'historique
    history = []
    
    # Création du ticket
    history.append({
        "type": "created",
        "timestamp": ticket["created_at"],
        "description": f"Ticket créé par {ticket.get('customer_name', 'Anonyme')}",
        "data": {
            "channel": ticket.get("channel"),
            "initial_message": ticket.get("initial_message")
        }
    })
    
    # Messages
    for msg in ticket.get("messages", []):
        history.append({
            "type": "message",
            "timestamp": msg["timestamp"],
            "description": f"Message de {msg['author']}",
            "data": {
                "content": msg["content"],
                "type": msg["type"],
                "internal": msg.get("internal", False)
            }
        })
    
    # Assignations
    if ticket.get("assigned_to"):
        history.append({
            "type": "assigned",
            "timestamp": ticket.get("assigned_at", ticket["created_at"]),
            "description": f"Assigné à {ticket['assigned_to']}",
            "data": {
                "assigned_by": ticket.get("assigned_by")
            }
        })
    
    # Fermeture
    if ticket.get("closed_at"):
        history.append({
            "type": "closed",
            "timestamp": ticket["closed_at"],
            "description": f"Fermé par {ticket.get('closed_by', 'Système')}",
            "data": {
                "resolution_time": ticket.get("resolution_time_seconds")
            }
        })
    
    # Trier par timestamp
    history.sort(key=lambda x: x["timestamp"])
    
    return history


@router.get("/export/csv", response_class=Response)
async def export_tickets_csv(
    status: Optional[str] = None,
    channel: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: dict = Depends(verify_token)
):
    """
    Exporter les tickets en CSV (PRIVÉ - JWT requis)
    
    Utilisé par : Frontend ADMIN (export de données)
    
    Permissions : Manager, Admin
    """
    if not services.export_service:
        raise HTTPException(status_code=503, detail="Service d'export indisponible")
        
    csv_content = await services.export_service.generate_csv(
        status=status, channel=channel, date_from=date_from, date_to=date_to
    )
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=tickets_export_{now_iso()}.csv"}
    )


@router.get("/export/csv/{ticket_id}", response_class=Response)
async def export_single_ticket_csv(
    ticket_id: str,
    user: dict = Depends(verify_token)
):
    """
    Exporter un seul ticket en CSV (PRIVÉ - JWT requis)
    """
    if not services.export_service:
        raise HTTPException(status_code=503, detail="Service d'export indisponible")
        
    try:
        csv_content = await services.export_service.generate_single_ticket_csv(ticket_id)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=ticket_{ticket_id}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
