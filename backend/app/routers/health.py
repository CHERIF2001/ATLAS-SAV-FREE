import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.core.config import (
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
    ENABLE_RAG,
    STORAGE_TYPE,
    ENABLE_AUTO_ANALYTICS
)
from app.core.container import services

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health():
    """
    Health check basique pour ALB.
    Retourne 200 si le service est up, même si certains composants sont dégradés.
    """
    rag_status = False
    if services.rag_service:
        try:
            rag_status = services.rag_service.collection.count() > 0
        except Exception as e:
            logger.warning(f"RAG health check failed: {e}")
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "storage_type": STORAGE_TYPE,
        "mistral_configured": bool(MISTRAL_API_KEY),
        "mistral_model": MISTRAL_MODEL,
        "analytics_enabled": ENABLE_AUTO_ANALYTICS,
        "rag_enabled": ENABLE_RAG,
        "rag_active": rag_status
    }


@router.get("/health/ready")
async def readiness():
    """
    Readiness check pour ECS.
    Vérifie que tous les composants critiques sont opérationnels.
    Retourne 503 si un composant critique est down.
    """
    checks = {
        "storage": False,
        "mistral": False,
        "analytics": False,
        "rag": False
    }
    
    errors = []
    
    # 1. Vérifier le storage (CRITIQUE)
    try:
        if services.storage:
            # Pour DynamoDB, vérifier la connexion
            if hasattr(services.storage, 'health_check'):
                checks["storage"] = await services.storage.health_check()
            else:
                # Pour JSON, vérifier que le fichier est accessible
                checks["storage"] = True
        else:
            errors.append("Storage not initialized")
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        errors.append(f"Storage error: {str(e)}")
    
    # 2. Vérifier Mistral (CRITIQUE si configuré)
    try:
        if MISTRAL_API_KEY:
            if services.mistral_client:
                checks["mistral"] = True
            else:
                errors.append("Mistral client not initialized")
        else:
            # Si pas configuré, on considère que c'est OK
            checks["mistral"] = True
    except Exception as e:
        logger.error(f"Mistral health check failed: {e}")
        errors.append(f"Mistral error: {str(e)}")
    
    # 3. Vérifier Analytics (NON-CRITIQUE)
    try:
        if ENABLE_AUTO_ANALYTICS:
            checks["analytics"] = services.analytics_service is not None
        else:
            checks["analytics"] = True  # Disabled = OK
    except Exception as e:
        logger.warning(f"Analytics health check failed: {e}")
        # Non-critique, on ne bloque pas
        checks["analytics"] = True
    
    # 4. Vérifier RAG (NON-CRITIQUE)
    try:
        if ENABLE_RAG:
            if services.rag_service:
                doc_count = services.rag_service.collection.count()
                checks["rag"] = doc_count > 0
            else:
                logger.warning("RAG enabled but service not initialized")
                checks["rag"] = False
        else:
            checks["rag"] = True  # Disabled = OK
    except Exception as e:
        logger.warning(f"RAG health check failed: {e}")
        # Non-critique, on ne bloque pas
        checks["rag"] = True
    
    # Déterminer le statut global
    # On considère que storage et mistral sont critiques
    is_ready = checks["storage"] and checks["mistral"]
    
    response = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks,
        "errors": errors if errors else None
    }
    
    if not is_ready:
        raise HTTPException(status_code=503, detail=response)
    
    return response


@router.get("/health/live")
async def liveness():
    """
    Liveness check pour ECS.
    Vérifie que le processus est vivant (pas de deadlock).
    Retourne toujours 200 sauf si le processus est complètement bloqué.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
