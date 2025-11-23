"""
Pipeline complet d'enrichissement avec LLM
Gère les batches, retry, sauvegarde incrémentale
"""
import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from tqdm import tqdm

from src.config import PROCESSED_DIR, LLM_BATCH_SIZE
from src.llm_classification import initialize_mistral_client, classify_dataframe_batch
from src.parse_llm_outputs import parse_batch_responses
from src.utils import save_dataframe, load_dataframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def enrich_with_llm(
    df: pd.DataFrame,
    text_col: str = "text_clean",
    checkpoint_path: Optional[Path] = None,
    resume: bool = True
) -> pd.DataFrame:
    """
    Enrichit un DataFrame avec les classifications LLM
    
    Args:
        df: DataFrame avec colonnes nettoyées
        text_col: Colonne contenant le texte à classifier
        checkpoint_path: Chemin pour sauvegarder les résultats intermédiaires
        resume: Si True, reprend depuis le checkpoint si existant
    """
    df = df.copy()
    
    # Vérifier si checkpoint existe
    if resume and checkpoint_path and checkpoint_path.exists():
        logger.info(f"Chargement du checkpoint: {checkpoint_path}")
        try:
            df_checkpoint = load_dataframe(checkpoint_path)
            # Identifier les tweets déjà traités
            if "raw_llm_response" in df_checkpoint.columns:
                processed_ids = set(df_checkpoint.index)
                df_to_process = df[~df.index.isin(processed_ids)]
                logger.info(f"Reprise: {len(df_to_process)} tweets restants sur {len(df)}")
            else:
                df_to_process = df
        except Exception as e:
            logger.warning(f"Erreur chargement checkpoint: {e}. Reprise depuis le début.")
            df_to_process = df
    else:
        df_to_process = df
    
    if len(df_to_process) == 0:
        logger.info("Tous les tweets sont déjà traités!")
        return df
    
    # Initialiser client Mistral
    try:
        client = initialize_mistral_client()
    except Exception as e:
        logger.error(f"Erreur initialisation Mistral: {e}")
        raise
    
    # Préparer les textes
    texts = df_to_process[text_col].fillna("").astype(str).tolist()
    
    # Classification par batches
    logger.info(f"Début classification LLM pour {len(texts)} tweets...")
    batch_results = classify_dataframe_batch(client, texts, batch_size=LLM_BATCH_SIZE)
    
    # Parser les réponses
    logger.info("Parsing des réponses LLM...")
    parsed_results = parse_batch_responses(batch_results)
    
    # Ajouter les colonnes au DataFrame
    llm_columns = ["motif", "sentiment", "urgence", "risque_churn", "is_churn_risk"]
    
    for col in llm_columns:
        if col not in df.columns:
            df[col] = None
    
    # Remplir les valeurs pour les tweets traités
    for idx, parsed in zip(df_to_process.index, parsed_results):
        for col in llm_columns:
            if col in parsed:
                df.loc[idx, col] = parsed[col]
    
    # Ajouter les réponses brutes pour debug
    if "raw_llm_response" not in df.columns:
        df["raw_llm_response"] = None
    
    for idx, result in zip(df_to_process.index, batch_results):
        df.loc[idx, "raw_llm_response"] = result.get("raw_response")
    
    # Sauvegarder checkpoint
    if checkpoint_path:
        logger.info(f"Sauvegarde checkpoint: {checkpoint_path}")
        save_dataframe(df, checkpoint_path)
    
    logger.info("Enrichissement LLM terminé!")
    return df


def run_full_pipeline(
    input_path: Path,
    output_path: Path,
    text_col: str = "full_text",
    checkpoint_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Pipeline complet: nettoyage + enrichissement LLM
    """
    from src.cleaning import run_cleaning_on_df
    from src.utils import load_csv_with_encoding
    
    logger.info("=== Début du pipeline complet ===")
    
    # 1. Charger les données
    logger.info(f"Chargement: {input_path}")
    df = load_csv_with_encoding(input_path, text_col=text_col)
    
    # 2. Nettoyage
    logger.info("Étape 1: Nettoyage et préprocessing...")
    logger.info("⚠️  Exclusion automatique des tweets Free (comptes contenant 'free')")
    df_clean = run_cleaning_on_df(df, text_col=text_col, exclude_free=True)
    
    # Sauvegarder données nettoyées
    clean_path = PROCESSED_DIR / "tweets_cleaned.parquet"
    save_dataframe(df_clean, clean_path)
    logger.info(f"Données nettoyées sauvegardées: {clean_path}")
    
    # 3. Enrichissement LLM
    logger.info("Étape 2: Enrichissement LLM...")
    df_enriched = enrich_with_llm(
        df_clean,
        text_col="text_clean",
        checkpoint_path=checkpoint_path,
        resume=True
    )
    
    # 4. Sauvegarder résultat final
    logger.info(f"Sauvegarde résultat final: {output_path}")
    save_dataframe(df_enriched, output_path)
    
    logger.info("=== Pipeline terminé avec succès ===")
    return df_enriched
