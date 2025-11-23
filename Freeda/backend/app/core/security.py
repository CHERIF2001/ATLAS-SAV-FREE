"""Security utilities for JWT authentication."""
from fastapi import HTTPException, Header
from typing import Optional

def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """Verify JWT token and return user info.
    
    For now, this is a stub that always returns a default user.
    In production, implement proper JWT verification.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Stub implementation - replace with real JWT verification
    return {
        "email": "agent@free.fr",
        "name": "Agent Free",
        "role": "agent"
    }

def require_admin(user: dict = None) -> dict:
    """Require admin role.
    
    For now, this is a stub that always allows access.
    In production, implement proper role checking.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Stub implementation - replace with real role checking
    return user
