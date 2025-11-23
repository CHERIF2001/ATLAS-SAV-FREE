"""
Script d'initialisation de la base de connaissances RAG.
Scrape la FAQ, génère les embeddings et initialise ChromaDB.
"""

import asyncio
import sys
from pathlib import Path
import logging

# Ajouter le répertoire racine (backend/) au path pour pouvoir importer 'app'
# scripts/ -> backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.ai.scraper import FreeFAQScraper
from app.services.ai.rag import RAGService
from app.core.config import MISTRAL_API_KEY, CHROMA_DB_DIR, DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_knowledge_base():
    """Initialise la base de connaissances complète."""
    
    logger.info("=" * 60)
    logger.info("INITIALISATION DE LA BASE DE CONNAISSANCES RAG")
    logger.info("=" * 60)
    
    if not MISTRAL_API_KEY:
        logger.error("❌ MISTRAL_API_KEY non trouvée dans .env")
        return False
    
    try:
        # Étape 1 : Scraper la FAQ
        logger.info("\n📥 Étape 1/3 : Scraping de la FAQ Free...")
        
        # Le dossier knowledge_base sera dans data/knowledge_base
        kb_dir = DATA_DIR / "knowledge_base"
        
        scraper = FreeFAQScraper(output_dir=str(kb_dir))
        faq_file = await scraper.run()
        
        if not faq_file:
            logger.error("❌ Échec du scraping")
            return False
        
        # Étape 2 : Initialiser le service RAG
        logger.info("\n🔧 Étape 2/3 : Initialisation du service RAG...")
        rag_service = RAGService(
            mistral_api_key=MISTRAL_API_KEY,
            chroma_persist_dir=str(CHROMA_DB_DIR)
        )
        
        # Étape 3 : Charger les documents dans ChromaDB
        logger.info("\n📚 Étape 3/3 : Chargement des documents dans ChromaDB...")
        await rag_service.load_from_file(str(faq_file))
        
        # Afficher les statistiques
        stats = rag_service.get_stats()
        logger.info("\n" + "=" * 60)
        logger.info("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
        logger.info("=" * 60)
        logger.info(f"📊 Statistiques:")
        logger.info(f"   - Total documents: {stats['total_documents']}")
        logger.info(f"   - Catégories: {stats['categories']}")
        logger.info(f"   - Collection: {stats['collection_name']}")
        logger.info("=" * 60)
        
        # Test de recherche
        logger.info("\n🧪 Test de recherche...")
        test_query = "problème de connexion internet"
        results = await rag_service.search(test_query, n_results=2)
        
        logger.info(f"\nRecherche: '{test_query}'")
        logger.info(f"Résultats trouvés: {len(results)}")
        for i, result in enumerate(results, 1):
            logger.info(f"\n  {i}. {result['question']}")
            logger.info(f"     Catégorie: {result['category']}")
            logger.info(f"     Score: {result['relevance_score']:.3f}")
        
        logger.info("\n✅ Base de connaissances prête à l'emploi!")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False


async def reset_knowledge_base():
    """Réinitialise complètement la base de connaissances."""
    logger.warning("⚠️  Réinitialisation de la base de connaissances...")
    
    import shutil
    
    # Supprimer ChromaDB
    if CHROMA_DB_DIR.exists():
        shutil.rmtree(CHROMA_DB_DIR)
        logger.info("✅ ChromaDB supprimée")
    
    # Supprimer les fichiers de connaissances
    kb_dir = DATA_DIR / "knowledge_base"
    if kb_dir.exists():
        shutil.rmtree(kb_dir)
        logger.info("✅ Fichiers de connaissances supprimés")
    
    logger.info("✅ Réinitialisation terminée")


async def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestion de la base de connaissances RAG")
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Réinitialiser complètement la base de connaissances'
    )
    
    args = parser.parse_args()
    
    if args.reset:
        await reset_knowledge_base()
        logger.info("\nRelancez sans --reset pour réinitialiser la base")
    else:
        success = await initialize_knowledge_base()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
