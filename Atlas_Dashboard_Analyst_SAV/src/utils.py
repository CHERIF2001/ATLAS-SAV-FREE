"""
Utilitaires généraux
"""
import pandas as pd
import re
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_csv_with_encoding(file_path: Path, text_col: str = "full_text") -> pd.DataFrame:
    """
    Charge un CSV en essayant plusieurs encodages
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc, low_memory=False)
            if text_col in df.columns:
                logger.info(f"CSV chargé avec succès (encoding: {enc})")
                return df
        except Exception as e:
            logger.warning(f"Échec avec encoding {enc}: {e}")
            continue
    
    raise ValueError(f"Impossible de charger le CSV {file_path} avec les encodages testés")


def save_dataframe(df: pd.DataFrame, path: Path, format: str = "parquet"):
    """
    Sauvegarde un DataFrame dans différents formats
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "parquet":
        df.to_parquet(path, index=False, engine="pyarrow")
    elif format == "csv":
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        raise ValueError(f"Format non supporté: {format}")
    
    logger.info(f"Données sauvegardées: {path}")


def load_dataframe(path: Path) -> pd.DataFrame:
    """
    Charge un DataFrame depuis parquet ou CSV
    """
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    elif path.suffix == ".csv":
        return load_csv_with_encoding(path)
    else:
        raise ValueError(f"Format de fichier non supporté: {path.suffix}")


def safe_str(value) -> str:
    """
    Convertit une valeur en string de manière sécurisée
    """
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip()


def normalize_whitespace(text: str) -> str:
    """
    Normalise les espaces blancs
    """
    return re.sub(r"\s+", " ", str(text)).strip()

