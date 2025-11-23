"""
Script principal pour exécuter le pipeline complet
"""
import argparse
from pathlib import Path
import logging

from src.config import RAW_DIR, PROCESSED_DIR
from src.pipeline_enrichment import run_full_pipeline
from src.utils import load_csv_with_encoding

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Pipeline d'enrichissement de tweets")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Chemin vers le fichier CSV d'entrée (défaut: data/raw/free_tweet_export.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Chemin vers le fichier de sortie (défaut: data/processed/tweets_enriched.parquet)"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Chemin vers le fichier checkpoint (défaut: data/processed/tweets_enrichment_checkpoint.parquet)"
    )
    parser.add_argument(
        "--text-col",
        type=str,
        default="full_text",
        help="Nom de la colonne contenant le texte (défaut: full_text)"
    )
    
    args = parser.parse_args()
    
    # Chemins par défaut
    if args.input is None:
        input_path = RAW_DIR / "free_tweet_export.csv"
    else:
        input_path = Path(args.input)
    
    if args.output is None:
        output_path = PROCESSED_DIR / "tweets_enriched.parquet"
    else:
        output_path = Path(args.output)
    
    if args.checkpoint is None:
        checkpoint_path = PROCESSED_DIR / "tweets_enrichment_checkpoint.parquet"
    else:
        checkpoint_path = Path(args.checkpoint)
    
    # Vérifier que le fichier d'entrée existe
    if not input_path.exists():
        logger.error(f"Fichier d'entrée introuvable: {input_path}")
        logger.info("Placez votre fichier CSV dans data/raw/ ou spécifiez --input")
        return
    
    logger.info("=== Démarrage du pipeline ===")
    logger.info(f"Entrée: {input_path}")
    logger.info(f"Sortie: {output_path}")
    logger.info(f"Checkpoint: {checkpoint_path}")
    
    try:
        df_result = run_full_pipeline(
            input_path=input_path,
            output_path=output_path,
            text_col=args.text_col,
            checkpoint_path=checkpoint_path
        )
        
        logger.info(f"✅ Pipeline terminé avec succès!")
        logger.info(f"📊 {len(df_result)} tweets traités")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution du pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
