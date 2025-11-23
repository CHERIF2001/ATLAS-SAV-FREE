"""
Conteneur pour les instances globales des services.
"""
class ServiceContainer:
    storage = None
    mistral_client = None
    analytics_service = None
    export_service = None
    rag_service = None

services = ServiceContainer()
