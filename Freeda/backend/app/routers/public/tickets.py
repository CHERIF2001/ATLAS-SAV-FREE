"""
Endpoints PUBLICS pour les Tickets - Frontend CLIENT

Ces endpoints sont accessibles SANS authentification.
Utilises par le frontend client pour :
- Creer des tickets depuis le ChatBot
- Suivre un ticket avec son ID
- Ajouter des messages a un ticket

Securite : Limite aux operations necessaires pour les clients
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from typing import Optional
import uuid

# Import des services
from app.services.storage.interface import get_storage
from app.core.config import SYSTEM_PROMPT, ENABLE_RAG
from app.core.container import services
from app.core.utils import normalize_agent_signature
from app.core.websocket import manager
from app.core.ratelimit import check_ticket_rate_limit, check_message_rate_limit
from app.models.schemas import TicketCreate, MessageCreate, StatusUpdate
from app.services.ai.smart_reply import smart_reply



router = APIRouter(prefix="/public/tickets", tags=["Public - Tickets"])

# Initialisation des services
storage = get_storage()

async def get_system_prompt_with_context(user_message: str) -> str:
    """Ajoute le contexte RAG au prompt systeme si active."""
    if not ENABLE_RAG or not services.rag_service:
        return SYSTEM_PROMPT
        
    try:
        context = await services.rag_service.get_context_for_query(user_message)
        if context:
            return f"{SYSTEM_PROMPT}\n\nUtilise les informations suivantes pour repondre :\n{context}"
    except Exception as e:
        pass
        
    return SYSTEM_PROMPT


def generate_ticket_id() -> str:
    """Generer un ID de ticket unique et court pour les clients"""
    # Format: FRE-XXXXXX (6 caracteres alphanumeriques)
    short_id = str(uuid.uuid4())[:8].upper()
    return f"FRE-{short_id}"


@router.post("/", response_model=dict, dependencies=[Depends(check_ticket_rate_limit)])
async def create_ticket_public(request: TicketCreate):
    """
    Creer un nouveau ticket (PUBLIC - sans authentification)
    
    Utilise par : Frontend CLIENT (ChatBot, formulaires de contact)
    """
    initial_message = request.initial_message
    customer_name = request.customer_name
    channel = request.channel
    
    # Generer un ID unique
    ticket_id = generate_ticket_id()
    
    # Creer le ticket
    ticket = {
        "ticket_id": ticket_id,
        "initial_message": initial_message,
        "customer_name": customer_name or "Anonyme",
        "channel": channel,
        "status": "nouveau",
        "created_at": datetime.utcnow().isoformat(),
        "messages": [
            {
                "message_id": str(uuid.uuid4()),
                "content": initial_message,
                "author": customer_name or "Client",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "client"
            }
        ],
        "public": True  # Indique que c'est un ticket cree publiquement
    }
    
    # Analyser le sentiment et l'urgence avec Mistral (Improved Analytics)
    if services.analytics_service:
        try:
            # On passe l'historique des messages (ici juste le premier)
            messages_history = [{"role": "user", "content": initial_message}]
            analytics_result = await services.analytics_service.analyze_ticket(messages_history)
            ticket["analytics"] = analytics_result
        except Exception as e:
            print(f"Erreur analytics: {e}")
            ticket["analytics"] = {
                "sentiment": "neutre",
                "urgency": "moyenne",
                "category": "autre",
                "churn_risk": 0,
                "summary": "Erreur analyse"
            }
    
    # Generer une reponse IA si c'est un chat
    assistant_message = None
    if channel == "chat":
        try:
            # 1. Tenter une reponse rapide (GRATUIT)
            quick_response = smart_reply.get_quick_response(initial_message)
            
            if quick_response:
                # Utiliser la reponse rapide
                assistant_text = quick_response
            else:
                # 2. Sinon, utiliser Mistral AI (PAYANT)
                system_prompt = await get_system_prompt_with_context(initial_message)
                messages_for_model = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": initial_message}
                ]
                
                if services.mistral_client:
                    assistant_text = await services.mistral_client.chat(messages_for_model)
                    assistant_text = normalize_agent_signature(assistant_text)
                else:
                    assistant_text = "Je prends note de votre demande. Un agent va vous repondre sous peu."

            assistant_message = {
                "message_id": str(uuid.uuid4()),
                "content": assistant_text,
                "author": "Assistant Free",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "assistant"
            }
            ticket["messages"].append(assistant_message)
        except Exception as e:
            print(f"Erreur IA/SmartReply: {e}")

    # Sauvegarder dans DynamoDB
    await storage.save_ticket(ticket)
    
    # Broadcast via WebSocket
    # 1. Ticket created
    await manager.broadcast(ticket_id, {
        "type": "ticket_created", 
        "ticket": {
            "ticket_id": ticket_id, 
            "status": ticket["status"], 
            "created_at": ticket["created_at"]
        }
    })
    
    # 2. User message
    await manager.broadcast(ticket_id, {
        "type": "new_message", 
        "message": {
            "id": ticket["messages"][0]["message_id"],
            "content": ticket["messages"][0]["content"],
            "role": "user",
            "timestamp": ticket["messages"][0]["timestamp"]
        }
    })
    
    # 3. Assistant message (if any)
    if assistant_message:
        await manager.broadcast(ticket_id, {
            "type": "new_message", 
            "message": {
                "id": assistant_message["message_id"],
                "content": assistant_message["content"],
                "role": "assistant",
                "timestamp": assistant_message["timestamp"]
            }
        })
    
    response = {
        "ticket_id": ticket_id,
        "message": "Ticket cree avec succes",
        "tracking_url": f"/public/tickets/{ticket_id}",
        "estimated_response_time": "Sous 2 heures",
        "analytics": ticket.get("analytics")
    }
    
    if assistant_message:
        response["assistant_message"] = assistant_message
        
    return response


@router.get("/{ticket_id}", response_model=dict)
async def get_ticket_public(ticket_id: str):
    """
    Recuperer un ticket par son ID (PUBLIC)
    
    Utilise par : Frontend CLIENT (page de suivi)
    
    Args:
        ticket_id: ID du ticket (ex: FRE-A1B2C3D4)
    
    Returns:
        Informations publiques du ticket (sans donnees sensibles)
    """
    
    ticket = await storage.get_ticket(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket non trouve. Verifiez l'ID du ticket."
        )
    
    # Ne retourner que les informations publiques
    # (pas d'infos agents, pas de donnees internes)
    public_ticket = {
        "ticket_id": ticket["ticket_id"],
        "status": ticket["status"],
        "created_at": ticket["created_at"],
        "customer_name": ticket.get("customer_name", "Anonyme"),
        "messages": [
            {
                "message_id": msg["message_id"],
                "content": msg["content"],
                "author": msg["author"],
                "timestamp": msg["timestamp"],
                "type": msg["type"]
            }
            for msg in ticket.get("messages", [])
        ],
        "last_update": ticket.get("updated_at", ticket["created_at"])
    }
    
    # Ajouter le statut en francais
    status_labels = {
        "nouveau": "Nouveau - En attente de prise en charge",
        "en cours": "En cours - Un agent travaille sur votre demande",
        "ferme": "Resolu - Votre demande a ete traitee"
    }
    public_ticket["status_label"] = status_labels.get(
        ticket["status"], 
        ticket["status"]
    )
    
    return public_ticket


@router.post("/{ticket_id}/messages", response_model=dict, dependencies=[Depends(check_message_rate_limit)])
async def add_message_public(
    ticket_id: str,
    request: MessageCreate
):
    """
    Ajouter un message a un ticket (PUBLIC)
    
    Utilise par : Frontend CLIENT (reponse du client)
    """
    content = request.message
    author_name = request.author_name
    
    # Verifier que le ticket existe
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouve")
    
    # Verifier que le ticket n'est pas ferme
    if ticket["status"] == "ferme":
        raise HTTPException(
            status_code=400,
            detail="Ce ticket est ferme. Veuillez creer un nouveau ticket si besoin."
        )
    
    # Creer le message
    message = {
        "message_id": str(uuid.uuid4()),
        "content": content,
        "author": author_name or ticket.get("customer_name", "Client"),
        "timestamp": datetime.utcnow().isoformat(),
        "type": "client"
    }
    
    # Ajouter le message au ticket en memoire
    if "messages" not in ticket:
        ticket["messages"] = []
    ticket["messages"].append(message)
    
    # Analyser le nouveau message et mettre a jour le ticket
    if services.analytics_service:
        try:
            # Recuperer l'historique complet pour une meilleure analyse
            history = ticket.get("messages", [])
            # Convertir pour l'analytics service
            messages_history = []
            for msg in history:
                role = "assistant" if msg["type"] == "assistant" else "user"
                messages_history.append({"role": role, "content": msg["content"]})
            
            # Le message est deja dans l'historique maintenant
            
            analytics_result = await services.analytics_service.analyze_ticket(messages_history)
            
            # Mettre a jour les analytics du ticket
            ticket["analytics"] = analytics_result
            
            # Ajouter le sentiment au message individuel (optionnel, pour compatibilite)
            message["sentiment"] = analytics_result.get("sentiment", "neutre")
            
        except Exception as e:
            print(f"Erreur analyse message: {e}")
            
    # Sauvegarder le ticket avec le nouveau message et les analytics
    await storage.save_ticket(ticket)
            

        
    # Generer une reponse IA
    assistant_message = None
    try:
        # 1. Tenter une reponse rapide (GRATUIT)
        quick_response = smart_reply.get_quick_response(content)
        
        if quick_response:
            assistant_text = quick_response
        else:
            # 2. Sinon, utiliser Mistral AI (PAYANT)
            # Recuperer l'historique pour le contexte
            history = ticket.get("messages", [])
            
            system_prompt = await get_system_prompt_with_context(content)
            messages_for_model = [{"role": "system", "content": system_prompt}]
            
            # Ajouter les derniers messages au contexte (max 5)
            for msg in history[-5:]:
                role = "assistant" if msg["type"] == "assistant" else "user"
                messages_for_model.append({"role": role, "content": msg["content"]})
                
            # Ajouter le message actuel
            messages_for_model.append({"role": "user", "content": content})
            
            if services.mistral_client:
                assistant_text = await services.mistral_client.chat(messages_for_model)
                assistant_text = normalize_agent_signature(assistant_text)
            else:
                assistant_text = None
        
        if assistant_text:
            assistant_message = {
                "message_id": str(uuid.uuid4()),
                "content": assistant_text,
                "author": "Assistant Free",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "assistant"
            }
            
            await storage.add_message(ticket_id, assistant_message)
    except Exception as e:
        print(f"Erreur IA/SmartReply: {e}")
        
    # Broadcast via WebSocket
    # 1. User message
    await manager.broadcast(ticket_id, {
        "type": "new_message", 
        "message": {
            "id": message["message_id"],
            "content": message["content"],
            "role": "user",
            "timestamp": message["timestamp"]
        }
    })
    
    # 2. Assistant message (if any)
    if assistant_message:
        await manager.broadcast(ticket_id, {
            "type": "new_message", 
            "message": {
                "id": assistant_message["message_id"],
                "content": assistant_message["content"],
                "role": "assistant",
                "timestamp": assistant_message["timestamp"]
            }
        })
    
    response = {
        "message": "Message ajoute avec succes",
        "message_id": message["message_id"],
        "timestamp": message["timestamp"]
    }
    
    if assistant_message:
        response["assistant_message"] = assistant_message
        
    return response


@router.get("/{ticket_id}/status", response_model=dict)
async def get_ticket_status_public(ticket_id: str):
    """
    Recuperer uniquement le statut d un ticket (PUBLIC)
    
    Utilise par : Frontend CLIENT (verification rapide du statut)
    
    Args:
        ticket_id: ID du ticket
    
    Returns:
        Statut actuel du ticket
    """
    
    ticket = await storage.get_ticket(ticket_id)
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouve")
    
    status_info = {
        "nouveau": {
            "label": "Nouveau",
            "description": "Votre demande a ete enregistree et sera traitee rapidement.",
            "color": "blue"
        },
        "en cours": {
            "label": "En cours",
            "description": "Un agent travaille actuellement sur votre demande.",
            "color": "orange"
        },
        "ferme": {
            "label": "Resolu",
            "description": "Votre demande a ete traitee avec succes.",
            "color": "green"
        }
    }
    
    current_status = ticket["status"]
    
    return {
        "ticket_id": ticket_id,
        "status": current_status,
        "status_info": status_info.get(current_status, {
            "label": current_status,
            "description": "Statut en cours de traitement",
            "color": "gray"
        }),
        "last_update": ticket.get("updated_at", ticket["created_at"]),
        "message_count": len(ticket.get("messages", []))
    }


@router.patch("/{ticket_id}/status", response_model=dict)
async def update_ticket_status_public(
    ticket_id: str,
    update: StatusUpdate
):
    """
    Mettre à jour le statut d'un ticket (PUBLIC)
    
    Permet au client de fermer son ticket.
    Seul le statut 'fermé' est autorisé publiquement.
    """
    
    if update.status != "fermé":
        raise HTTPException(
            status_code=400, 
            detail="Seule la fermeture du ticket est autorisée publiquement"
        )
        
    ticket = await storage.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
        
    # Si déjà fermé, rien à faire
    if ticket["status"] == "fermé":
        return {"message": "Ticket déjà fermé", "status": "fermé"}
        
    # Mettre à jour le statut
    closed_at = datetime.utcnow().isoformat()
    await storage.update_ticket_status(ticket_id, "fermé", closed_at)
    
    # Broadcast via WebSocket
    await manager.broadcast(ticket_id, {
        "type": "status_updated", 
        "status": "fermé"
    })
    
    return {
        "message": "Ticket fermé avec succès",
        "status": "fermé",
        "closed_at": closed_at
    }
