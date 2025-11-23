"""
Configuration centralisée du projet
"""
from pathlib import Path
import os

# Charger .env si disponible (optionnel)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Si python-dotenv n'est pas installé, on continue sans
    pass

# Chemins
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# API Mistral
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-medium-latest")

# Configuration LLM
LLM_BATCH_SIZE = 20
LLM_MAX_RETRIES = 3
LLM_TIMEOUT = 60

# Configuration preprocessing
SPACY_MODEL = "fr_core_news_sm"
BATCH_SIZE_PREPROC = 1000

# Colonnes attendues dans le CSV
TEXT_COLUMN = "full_text"  # ou "tweet_text" selon le fichier
DATE_COLUMN = "created_at"
USER_COLUMN = "screen_name"  # Colonne pour identifier les comptes (exclure Free)

# Filtrage
EXCLUDE_FREE_ACCOUNTS = True  # Exclure automatiquement les tweets des comptes Free

# Couleurs pour le dashboard
COLORS = {
    "sentiment": {
        "positif": "#10B981",  # vert
        "neutre": "#6B7280",   # gris
        "négatif": "#EF4444"   # rouge
    },
    "urgence": {
        "faible": "#10B981",
        "moyenne": "#F59E0B",
        "élevée": "#EF4444"
    },
    "churn": {
        "faible": "#10B981",
        "modéré": "#F59E0B",
        "élevé": "#EF4444"
    }
}
