import logging
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import (
    ALLOWED_ORIGINS,
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
    MISTRAL_API_URL,
    STORAGE_TYPE,
    TICKETS_FILE,
    DYNAMODB_TABLE_TICKETS,
    AWS_REGION,
    ENABLE_AUTO_ANALYTICS,
    ENABLE_RAG,
    CHROMA_DB_DIR
)
from app.core.container import services
from app.core.websocket import manager

#  import des routes
from app.routers import health
from app.routers.public import tickets as public_tickets
from app.routers.private import tickets as private_tickets
from app.routers.private import auth as private_auth

from app.services.storage.json_store import JSONStorage
from app.services.storage.dynamodb_store import DynamoDBStorage
from app.services.ai.mistral import MistralClient
from app.services.ai.analytics import AnalyticsService
from app.services.ai.rag import RAGService
from app.services.export import ExportService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("freeda.backend")

app = FastAPI(title="Freeda Support API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# inclusion des routes
app.include_router(health.router, tags=["health"])
app.include_router(public_tickets.router)
app.include_router(private_tickets.router)
app.include_router(private_auth.router)

@app.on_event("startup")
async def startup():
    logger.info("Starting Freeda SAV backend...")
    
    # 1. Initialisation du stockage
    if STORAGE_TYPE == "dynamodb":
        logger.info("Using DynamoDB storage")
        services.storage = DynamoDBStorage(table_name=DYNAMODB_TABLE_TICKETS, region=AWS_REGION)
    else:
        logger.info("Using JSON storage: %s", TICKETS_FILE)
        services.storage = JSONStorage(file_path=TICKETS_FILE)
        if not TICKETS_FILE.exists():
            TICKETS_FILE.write_text("{}", encoding="utf-8")

    # 2. Initialisation du client MISTRAL
    if MISTRAL_API_KEY:
        try:

            services.mistral_client = MistralClient(
                api_key=MISTRAL_API_KEY, 
                api_url=MISTRAL_API_URL, 
                default_model=MISTRAL_MODEL
            )
            logger.info(f"Mistral client initialized with model {MISTRAL_MODEL}")
        except Exception as e:
            logger.exception("Failed to initialize Mistral client: %s", e)
            services.mistral_client = None
    
    # 3. Initialisation de l'analyse
    if ENABLE_AUTO_ANALYTICS and services.mistral_client:
        services.analytics_service = AnalyticsService(services.mistral_client)
        logger.info("Analytics service enabled")
    else:
        logger.info("Analytics service disabled")
    
    # 4. IInitialisation de l'export
    services.export_service = ExportService(services.storage)
    logger.info("Export service initialized")
    
    # 5. IInitialisation du RAG
    if ENABLE_RAG and MISTRAL_API_KEY:
        try:
            services.rag_service = RAGService(
                mistral_api_key=MISTRAL_API_KEY,
                chroma_persist_dir=str(CHROMA_DB_DIR)
            )
            
            # Charger les documents si la base est vide
            stats = services.rag_service.get_stats()
            if stats['total_documents'] == 0:
                knowledge_file = Path("data/knowledge_base/faq_documents.json")
                if knowledge_file.exists():
                    logger.info(f"Loading initial knowledge from {knowledge_file}...")
                    await services.rag_service.load_from_file(str(knowledge_file))
                    stats = services.rag_service.get_stats() # modification des états
            
            logger.info(f"RAG service enabled: {stats['total_documents']} documents loaded")
        except Exception as e:
            logger.warning(f"RAG service initialization failed: {e}")
            services.rag_service = None
    else:
        logger.info("RAG service disabled")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down...")
    if services.storage:
        await services.storage.close()
    if services.mistral_client:
        await services.mistral_client.close()
    logger.info("Shutdown complete")


@app.websocket("/ws/{ticket_id}")
async def websocket_endpoint(websocket: WebSocket, ticket_id: str):
    await manager.connect(websocket, ticket_id)
    try:
        # Envoi des tickets initials si existe
        try:
            if services.storage and await services.storage.ticket_exists(ticket_id):
                ticket = await services.storage.get_ticket(ticket_id)
                await websocket.send_json({"type": "ticket_snapshot", "ticket": ticket})
        except Exception as e:
            logger.error(f"Error sending snapshot: {e}")

        while True:
            data = await websocket.receive_text()
 
    except WebSocketDisconnect:
        manager.disconnect(websocket, ticket_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, ticket_id)
