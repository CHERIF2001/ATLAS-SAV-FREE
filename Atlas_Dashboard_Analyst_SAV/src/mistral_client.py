import os
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")
if not API_KEY:
    raise ValueError("MISTRAL_API_KEY manquant. Ajoute-le dans un fichier .env à la racine du projet.")

client = Mistral(api_key=API_KEY)
