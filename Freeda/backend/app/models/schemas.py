from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class TicketCreate(BaseModel):
    initial_message: str
    customer_name: Optional[str] = None
    channel: str = "chat"

class MessageCreate(BaseModel):
    message: str
    author_name: Optional[str] = None

class Message(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str

class Ticket(BaseModel):
    ticket_id: str
    status: str
    channel: Optional[str] = None
    created_at: str
    closed_at: Optional[str] = None
    resolution_duration: Optional[int] = None  # en secondes
    analytics: Optional[Dict[str, Any]] = None
    messages: List[Message]

class StatusUpdate(BaseModel):
    status: str  # "en cours" ou "fermé"

class AgentMessageCreate(BaseModel):
    content: str
    internal: bool = False

class AssignTicketRequest(BaseModel):
    agent_email: str
