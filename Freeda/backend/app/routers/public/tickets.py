from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from typing import Optional
import uuid

from app.services.storage.interface import get_storage
from app.core.config import SYSTEM_PROMPT, ENABLE_RAG
from app.core.container import services
from app.core.utils import normalize_agent_signature
from app.core.websocket import manager
from app.core.ratelimit import check_ticket_rate_limit, check_message_rate_limit
from app.models.schemas import TicketCreate, MessageCreate, StatusUpdate
from app.services.ai.smart_reply import smart_reply

router = APIRouter(prefix="/public/tickets", tags=["Public - Tickets"])

storage = get_storage()

async def get_rag_context(user_msg: str) -> str:
    if not ENABLE_RAG or not services.rag_service:
        return SYSTEM_PROMPT
        
    try:
        ctx = await services.rag_service.get_context(user_msg)
        if ctx:
            return f"{SYSTEM_PROMPT}\n\nUtilise les infos suivantes :\n{ctx}"
    except:
        pass
        
    return SYSTEM_PROMPT

def gen_id() -> str:
    return f"FRE-{str(uuid.uuid4())[:8].upper()}"

@router.post("/", response_model=dict, dependencies=[Depends(check_ticket_rate_limit)])
async def create_ticket(req: TicketCreate):
    t_id = gen_id()
    
    # Init ticket structure
    ticket = {
        "ticket_id": t_id,
        "initial_message": req.initial_message,
        "customer_name": req.customer_name or "Anonyme",
        "channel": req.channel,
        "status": "nouveau",
        "created_at": datetime.utcnow().isoformat(),
        "messages": [{
            "message_id": str(uuid.uuid4()),
            "content": req.initial_message,
            "author": req.customer_name or "Client",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "client"
        }],
        "public": True
    }
    
    # Analytics part
    if services.analytics_service:
        try:
            hist = [{"role": "user", "content": req.initial_message}]
            ticket["analytics"] = await services.analytics_service.analyze_ticket(hist)
        except Exception as e:
            print(f"Analytics error: {e}")
            ticket["analytics"] = {
                "sentiment": "neutre", "urgency": "moyenne", 
                "category": "autre", "churn_risk": 0, "summary": "Erreur"
            }
    
    # AI Reply logic
    bot_msg = None
    if req.channel == "chat":
        try:
            # Try smart reply first
            quick_rep = smart_reply.get_quick_response(req.initial_message)
            
            if quick_rep:
                bot_text = quick_rep
            else:
                # Fallback to Mistral
                sys_prompt = await get_rag_context(req.initial_message)
                msgs = [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": req.initial_message}
                ]
                
                if services.mistral_client:
                    bot_text = await services.mistral_client.chat(msgs)
                    bot_text = normalize_agent_signature(bot_text)
                else:
                    bot_text = "Je prends note. Un agent va répondre."

            bot_msg = {
                "message_id": str(uuid.uuid4()),
                "content": bot_text,
                "author": "Assistant Free",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "assistant"
            }
            ticket["messages"].append(bot_msg)
        except Exception as e:
            print(f"AI Error: {e}")

    await storage.save_ticket(ticket)
    
    # WS Broadcasts
    await manager.broadcast(t_id, {
        "type": "ticket_created", 
        "ticket": {"ticket_id": t_id, "status": ticket["status"], "created_at": ticket["created_at"]}
    })
    
    await manager.broadcast(t_id, {
        "type": "new_message", 
        "message": {
            "id": ticket["messages"][0]["message_id"],
            "content": ticket["messages"][0]["content"],
            "role": "user",
            "timestamp": ticket["messages"][0]["timestamp"]
        }
    })
    
    if bot_msg:
        await manager.broadcast(t_id, {
            "type": "new_message", 
            "message": {
                "id": bot_msg["message_id"],
                "content": bot_msg["content"],
                "role": "assistant",
                "timestamp": bot_msg["timestamp"]
            }
        })
    
    resp = {
        "ticket_id": t_id,
        "message": "Ticket créé",
        "tracking_url": f"/public/tickets/{t_id}",
        "estimated_response_time": "Sous 2 heures",
        "analytics": ticket.get("analytics")
    }
    
    if bot_msg:
        resp["assistant_message"] = bot_msg
        
    return resp

@router.get("/{ticket_id}", response_model=dict)
async def get_ticket(ticket_id: str):
    t = await storage.get_ticket(ticket_id)
    
    if not t:
        raise HTTPException(404, "Ticket introuvable")
    
    # Filter public info
    res = {
        "ticket_id": t["ticket_id"],
        "status": t["status"],
        "created_at": t["created_at"],
        "customer_name": t.get("customer_name", "Anonyme"),
        "messages": [
            {
                "message_id": m["message_id"],
                "content": m["content"],
                "author": m["author"],
                "timestamp": m["timestamp"],
                "type": m["type"]
            }
            for m in t.get("messages", [])
        ],
        "last_update": t.get("updated_at", t["created_at"])
    }
    
    labels = {
        "nouveau": "Nouveau - En attente",
        "en cours": "En cours - Prise en charge",
        "ferme": "Résolu"
    }
    res["status_label"] = labels.get(t["status"], t["status"])
    
    return res

@router.post("/{ticket_id}/messages", response_model=dict, dependencies=[Depends(check_message_rate_limit)])
async def add_message(ticket_id: str, req: MessageCreate):
    msg_content = req.message
    author = req.author_name
    
    t = await storage.get_ticket(ticket_id)
    if not t:
        raise HTTPException(404, "Ticket introuvable")
    
    if t["status"] == "ferme":
        raise HTTPException(400, "Ticket fermé")
    
    new_msg = {
        "message_id": str(uuid.uuid4()),
        "content": msg_content,
        "author": author or t.get("customer_name", "Client"),
        "timestamp": datetime.utcnow().isoformat(),
        "type": "client"
    }
    
    if "messages" not in t:
        t["messages"] = []
    t["messages"].append(new_msg)
    
    # Update analytics
    if services.analytics_service:
        try:
            hist = []
            for m in t.get("messages", []):
                role = "assistant" if m["type"] == "assistant" else "user"
                hist.append({"role": role, "content": m["content"]})
            
            ana_res = await services.analytics_service.analyze_ticket(hist)
            t["analytics"] = ana_res
            new_msg["sentiment"] = ana_res.get("sentiment", "neutre")
            
        except Exception as e:
            print(f"Analytics update error: {e}")
            
    await storage.save_ticket(t)
            
    # AI Reply
    bot_msg = None
    try:
        quick = smart_reply.get_quick_response(msg_content)
        
        if quick:
            bot_txt = quick
        else:
            hist = t.get("messages", [])
            sys_p = await get_rag_context(msg_content)
            model_msgs = [{"role": "system", "content": sys_p}]
            
            # Context window: last 5 msgs
            for m in hist[-5:]:
                r = "assistant" if m["type"] == "assistant" else "user"
                model_msgs.append({"role": r, "content": m["content"]})
                
            model_msgs.append({"role": "user", "content": msg_content})
            
            if services.mistral_client:
                bot_txt = await services.mistral_client.chat(model_msgs)
                bot_txt = normalize_agent_signature(bot_txt)
            else:
                bot_txt = None
        
        if bot_txt:
            bot_msg = {
                "message_id": str(uuid.uuid4()),
                "content": bot_txt,
                "author": "Assistant Free",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "assistant"
            }
            await storage.add_message(ticket_id, bot_msg)
            
    except Exception as e:
        print(f"SmartReply error: {e}")
        
    # Broadcasts
    await manager.broadcast(ticket_id, {
        "type": "new_message", 
        "message": {
            "id": new_msg["message_id"],
            "content": new_msg["content"],
            "role": "user",
            "timestamp": new_msg["timestamp"]
        }
    })
    
    if bot_msg:
        await manager.broadcast(ticket_id, {
            "type": "new_message", 
            "message": {
                "id": bot_msg["message_id"],
                "content": bot_msg["content"],
                "role": "assistant",
                "timestamp": bot_msg["timestamp"]
            }
        })
    
    ret = {
        "message": "Message ajouté",
        "message_id": new_msg["message_id"],
        "timestamp": new_msg["timestamp"]
    }
    
    if bot_msg:
        ret["assistant_message"] = bot_msg
        
    return ret

@router.get("/{ticket_id}/status", response_model=dict)
async def get_status(ticket_id: str):
    t = await storage.get_ticket(ticket_id)
    if not t:
        raise HTTPException(404, "Ticket introuvable")
    
    status_map = {
        "nouveau": {"label": "Nouveau", "description": "En attente...", "color": "blue"},
        "en cours": {"label": "En cours", "description": "Traitement en cours...", "color": "orange"},
        "ferme": {"label": "Résolu", "description": "Terminé.", "color": "green"}
    }
    
    curr = t["status"]
    
    return {
        "ticket_id": ticket_id,
        "status": curr,
        "status_info": status_map.get(curr, {"label": curr, "color": "gray"}),
        "last_update": t.get("updated_at", t["created_at"]),
        "message_count": len(t.get("messages", []))
    }

@router.patch("/{ticket_id}/status", response_model=dict)
async def update_status(ticket_id: str, update: StatusUpdate):
    if update.status != "fermé":
        raise HTTPException(400, "Action non autorisée")
        
    t = await storage.get_ticket(ticket_id)
    if not t:
        raise HTTPException(404, "Introuvable")
        
    if t["status"] == "fermé":
        return {"message": "Déjà fermé", "status": "fermé"}
        
    closed_at = datetime.utcnow().isoformat()
    await storage.update_ticket_status(ticket_id, "fermé", closed_at)
    
    await manager.broadcast(ticket_id, {"type": "status_updated", "status": "fermé"})
    
    return {"message": "Ticket fermé", "status": "fermé", "closed_at": closed_at}
