import asyncio
from pathlib import Path
from app.core.container import services
from app.core.config import MISTRAL_API_KEY, CHROMA_DB_DIR

async def main():
    rag = services.rag_service
    if not rag:
        # Initialise le service si ce n'est pas déjà fait (cas du script exécuté hors du démarrage FastAPI)
        from app.services.ai.rag import RAGService
        rag = RAGService(mistral_api_key=MISTRAL_API_KEY, chroma_persist_dir=str(CHROMA_DB_DIR))
        services.rag_service = rag
    knowledge_file = Path(__file__).parents[2] / "data" / "knowledge_base" / "faq_documents.json"
    await rag.load_from_file(str(knowledge_file))
    print(f"✅ RAG seeded with {rag.get_stats()['total_documents']} documents")

if __name__ == "__main__":
    asyncio.run(main())
