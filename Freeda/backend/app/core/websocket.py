from typing import Dict, Set, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, ticket_id: str):
        await websocket.accept()
        if ticket_id not in self.active_connections:
            self.active_connections[ticket_id] = set()
        self.active_connections[ticket_id].add(websocket)

    def disconnect(self, websocket: WebSocket, ticket_id: str):
        if ticket_id in self.active_connections:
            self.active_connections[ticket_id].discard(websocket)
            if not self.active_connections[ticket_id]:
                del self.active_connections[ticket_id]

    async def broadcast(self, ticket_id: str, message: dict):
        if ticket_id not in self.active_connections:
            return
        disconnected = set()
        for conn in list(self.active_connections[ticket_id]):
            try:
                await conn.send_json(message)
            except Exception:
                disconnected.add(conn)
        
        for conn in disconnected:
            self.disconnect(conn, ticket_id)

# Instance globale
manager = ConnectionManager()
