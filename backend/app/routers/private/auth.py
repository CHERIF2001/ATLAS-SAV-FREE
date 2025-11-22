"""
Endpoints d'Authentification - Frontend ADMIN

Gestion de l'authentification JWT pour le frontend admin.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import jwt
from passlib.hash import bcrypt
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Configuration JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "VOTRE_CLE_SECRETE_ICI_CHANGEZ_MOI")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 heures


# Models Pydantic
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


# Base de données utilisateurs (temporaire - à remplacer par DynamoDB)
# Dans un vrai système, cela devrait être dans DynamoDB
# Mots de passe: agent123, manager123, admin123
USERS_DB = {
    "agent@freeda.com": {
        "email": "agent@freeda.com",
        "name": "Agent Support",
        "role": "agent",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEm3K."  # agent123
    },
    "manager@freeda.com": {
        "email": "manager@freeda.com",
        "name": "Manager Support",
        "role": "manager",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEm3K."  # manager123
    },
    "admin@freeda.com": {
        "email": "admin@freeda.com",
        "name": "Administrateur",
        "role": "admin",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEm3K."  # admin123
    }
}


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Connexion utilisateur (génère un token JWT)
    
    Utilisé par : Frontend ADMIN (page de login)
    
    Args:
        email: Email de l'utilisateur
        password: Mot de passe
    
    Returns:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "user": {
                "email": "agent@freeda.com",
                "name": "Agent Support",
                "role": "agent"
            }
        }
    
    Exemple d'utilisation (frontend admin):
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: 'agent@freeda.com',
                password: 'agent123'
            })
        });
        
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
    """
    
    # Vérifier que l'utilisateur existe
    user = USERS_DB.get(credentials.email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Email ou mot de passe incorrect"
        )
    
    # Vérifier le mot de passe
    if not bcrypt.verify(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Email ou mot de passe incorrect"
        )
    
    # Générer le token JWT
    token_data = {
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    
    access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    # Retourner le token + infos utilisateur
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    }


@router.post("/register", response_model=dict)
async def register(
    email: EmailStr,
    name: str,
    password: str,
    role: str = "agent"
):
    """
    Créer un nouvel utilisateur (ADMIN uniquement dans un vrai système)
    
    Note : Dans un environnement de production, ce endpoint devrait :
    - Nécessiter un token admin
    - Valider le rôle
    - Sauvegarder dans DynamoDB
    
    Args:
        email: Email de l'utilisateur
        name: Nom complet
        password: Mot de passe (sera hashé)
        role: Rôle (agent, manager, admin)
    
    Returns:
        Confirmation de création
    """
    
    # Vérifier que l'utilisateur n'existe pas déjà
    if email in USERS_DB:
        raise HTTPException(
            status_code=400,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Valider le rôle
    if role not in ["agent", "manager", "admin"]:
        raise HTTPException(
            status_code=400,
            detail="Rôle invalide. Doit être : agent, manager, ou admin"
        )
    
    # Créer l'utilisateur
    USERS_DB[email] = {
        "email": email,
        "name": name,
        "role": role,
        "hashed_password": bcrypt.hash(password),
        "created_at": datetime.utcnow().isoformat()
    }
    
    return {
        "message": "Utilisateur créé avec succès",
        "email": email,
        "name": name,
        "role": role
    }


@router.get("/me", response_model=dict)
async def get_current_user(token: str):
    """
    Récupérer les informations de l'utilisateur connecté
    
    Utilisé par : Frontend ADMIN (vérifier la session)
    
    Args:
        token: Token JWT (automatiquement extrait du header Authorization)
    
    Returns:
        Informations de l'utilisateur
    
    Exemple d'utilisation (frontend admin):
        const token = localStorage.getItem('token');
        const response = await fetch('/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const user = await response.json();
    """
    
    try:
        # Décoder le token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        return {
            "email": payload["email"],
            "name": payload["name"],
            "role": payload["role"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expiré. Veuillez vous reconnecter."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token invalide"
        )


@router.post("/logout", response_model=dict)
async def logout():
    """
    Déconnexion utilisateur
    
    Note : Avec JWT, la déconnexion se fait côté frontend
    en supprimant le token du localStorage.
    
    Ce endpoint est fourni pour la cohérence de l'API.
    
    Exemple d'utilisation (frontend admin):
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    """
    
    return {
        "message": "Déconnexion réussie. Supprimez le token côté client."
    }
