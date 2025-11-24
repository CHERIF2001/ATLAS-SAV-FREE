import json
import logging
from typing import List, Dict, Optional

try:
    from mistralai import Mistral
except ImportError:
    Mistral = None
    logging.warning("mistralai non installé. Installez-le avec: pip install mistralai")

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError:
    logging.warning("tenacity non installé. Installez-le avec: pip install tenacity")
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = lambda x: None
    wait_exponential = lambda **kwargs: None
    retry_if_exception_type = lambda *args: None

from src.config import MISTRAL_API_KEY, MISTRAL_MODEL, LLM_BATCH_SIZE, LLM_MAX_RETRIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClassificationError(Exception):
    pass

SYSTEM_PROMPT = """Tu es un expert en analyse de tweets clients pour un opérateur télécom.
Analyse chaque tweet et renvoie UNIQUEMENT un JSON valide avec les champs suivants:
- motif: une thématique parmi ["Technique", "Réseau", "Abonnement", "Facturation", "Service client", "Autre"]
- sentiment: "positif", "neutre" ou "négatif"
- urgence: "faible", "moyenne" ou "élevée"
- risque_churn: "faible", "modéré" ou "élevé"

Règles strictes:
- Le JSON doit être valide et parsable
- Pas de texte avant ou après le JSON
- Utilise des guillemets doubles
- sentiment: "positif" si satisfaction, "négatif" si problème/complainte, "neutre" sinon
- urgence: "élevée" si mots-clés comme "urgent", "bloqué", "aucun accès", "depuis X jours", "impossible"
- risque_churn: "élevé" si mention de résiliation, changement d'opérateur, "j'en ai marre", "je vais partir"
"""

USER_PROMPT_TEMPLATE = """Analyse ce tweet client et renvoie le JSON:

"{tweet_text}"

JSON:"""

def create_prompt(tweet_text: str) -> str:
    return USER_PROMPT_TEMPLATE.format(tweet_text=tweet_text[:500])


@retry(reraise=True, stop=stop_after_attempt(LLM_MAX_RETRIES), wait=wait_exponential(multiplier=1, min=2, max=30), retry=retry_if_exception_type((LLMClassificationError, Exception)))
def classify_one(client: Mistral, tweet_text: str) -> str:
    try:
        prompt = create_prompt(tweet_text)
        
        response = client.chat.complete(model=MISTRAL_MODEL, messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], temperature=0.1, max_tokens=200)
        
        content = response.choices[0].message.content.strip()
        
        if not content:
            raise LLMClassificationError("Réponse vide")
        
        return content
        
    except Exception as e:
        logger.error(f"Erreur classification tweet: {e}")
        raise LLMClassificationError(str(e))


def classify_tweets(client: Mistral, tweets: List[str]) -> List[Dict[str, Optional[str]]]:
    results = []
    
    for tweet in tweets:
        try:
            raw_response = classify_one(client, tweet)
            results.append({"raw_response": raw_response, "tweet": tweet})
        except Exception as e:
            logger.warning(f"Échec classification pour un tweet: {e}")
            results.append({"raw_response": None, "tweet": tweet, "error": str(e)})
    
    return results


def classify_batch(client: Mistral, texts: List[str], batch_size: int = LLM_BATCH_SIZE) -> List[Dict[str, Optional[str]]]:
    all_results = []
    total_batches = (len(texts) + batch_size - 1) // batch_size
    
    logger.info(f"Classification de {len(texts)} tweets en {total_batches} batches...")
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        logger.info(f"Traitement batch {batch_num}/{total_batches} ({len(batch)} tweets)...")
        
        try:
            batch_results = classify_tweets(client, batch)
            all_results.extend(batch_results)
            
            if i + batch_size < len(texts):
                import time
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Erreur batch {batch_num}: {e}")
            for _ in batch:
                all_results.append({"raw_response": None, "tweet": "", "error": str(e)})
    
    return all_results


def initialize_mistral_client() -> Mistral:
    if Mistral is None:
        raise ImportError("mistralai n'est pas installé. Installez-le avec: pip install mistralai")
    
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY non définie. Définissez-la dans .env ou variables d'environnement")
    
    return Mistral(api_key=MISTRAL_API_KEY)
