import os
from pathlib import Path
from dotenv import load_dotenv

# Définir le répertoire de base (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# Charger les variables d'environnement
load_dotenv(ENV_PATH)

# --- Configuration API Mistral ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-medium")
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai").rstrip("/")

# --- Configuration Serveur ---
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

# --- Configuration Services ---
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "json")
ENABLE_AUTO_ANALYTICS = os.getenv("ENABLE_AUTO_ANALYTICS", "true").lower() == "true"
ENABLE_RAG = os.getenv("ENABLE_RAG", "false").lower() == "true"

# --- Configuration AWS / DynamoDB ---
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE_TICKETS = os.getenv("DYNAMODB_TABLE_TICKETS", "freeda-tickets")

# --- Chemins de fichiers ---
DATA_DIR = BASE_DIR / "data"
TICKETS_FILE = DATA_DIR / "tickets.json"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Créer le dossier data s'il n'existe pas (sécurité)
DATA_DIR.mkdir(exist_ok=True)

# --- Prompt Système ---
SYSTEM_PROMPT = (
    "Tu es un agent du service client Free. "
    "Réponds avec empathie, professionnalisme et en apportant des solutions concrètes. "
    "Termine TOUJOURS tes réponses par '\n-- Agent Free' sur une nouvelle ligne."
)
