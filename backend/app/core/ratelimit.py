import time
from collections import defaultdict
from fastapi import HTTPException, Request

class RateLimiter:
    """
    Limiteur de débit simple en mémoire (Token Bucket simplifié).
    Pour une prod à grande échelle, utiliser Redis.
    """
    def __init__(self):
        # Stockage : {ip: [timestamp1, timestamp2, ...]}
        self.requests = defaultdict(list)
        
    def is_allowed(self, ip: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        
        # Nettoyer les anciennes requêtes de cette IP
        self.requests[ip] = [t for t in self.requests[ip] if now - t < window_seconds]
        
        # Vérifier le nombre de requêtes
        if len(self.requests[ip]) >= limit:
            return False
            
        # Ajouter la nouvelle requête
        self.requests[ip].append(now)
        return True

# Instances globales pour différents types de limites
# Limite stricte pour la création de tickets (éviter le spam de tickets)
ticket_limiter = RateLimiter()

# Limite plus souple pour les messages (conversation fluide)
message_limiter = RateLimiter()

async def check_ticket_rate_limit(request: Request):
    """
    Dépendance pour limiter la création de tickets.
    Max 5 tickets par heure par IP.
    """
    client_ip = request.client.host
    # 5 tickets / 3600 secondes (1 heure)
    if not ticket_limiter.is_allowed(client_ip, limit=5, window_seconds=3600):
        raise HTTPException(
            status_code=429, 
            detail="Trop de tickets créés. Veuillez patienter avant d'en créer un nouveau."
        )

async def check_message_rate_limit(request: Request):
    """
    Dépendance pour limiter l'envoi de messages.
    Max 20 messages par minute par IP.
    """
    client_ip = request.client.host
    # 20 messages / 60 secondes
    if not message_limiter.is_allowed(client_ip, limit=20, window_seconds=60):
        raise HTTPException(
            status_code=429, 
            detail="Vous envoyez des messages trop vite. Veuillez ralentir."
        )
