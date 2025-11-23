"""
Module de parsing sécurisé des réponses LLM
"""
import json
import re
import logging
from typing import Dict, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Valeurs par défaut
DEFAULT_VALUES = {
    "motif": "Autre",
    "sentiment": "neutre",
    "urgence": "faible",
    "risque_churn": "faible"
}

# Valeurs valides
VALID_MOTIFS = ["Technique", "Réseau", "Abonnement", "Facturation", "Service client", "Autre"]
VALID_SENTIMENTS = ["positif", "neutre", "négatif"]
VALID_URGENCES = ["faible", "moyenne", "élevée"]
VALID_CHURN = ["faible", "modéré", "élevé"]


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extrait le JSON d'un texte qui peut contenir du texte avant/après
    """
    if not text:
        return None
    
    # Chercher un bloc JSON (entre { et })
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    # Si pas trouvé, essayer de trouver entre ```json et ```
    code_block = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()
    
    # Dernier recours: chercher juste après "JSON:" ou similaire
    after_json = re.search(r'(?:json|JSON):\s*(\{.*\})', text, re.DOTALL | re.IGNORECASE)
    if after_json:
        return after_json.group(1)
    
    return None


def normalize_value(value: Any, valid_values: list, default: str) -> str:
    """
    Normalise une valeur pour qu'elle soit dans la liste valide
    """
    if not value:
        return default
    
    value_str = str(value).lower().strip()
    
    # Correspondance exacte
    for v in valid_values:
        if value_str == v.lower():
            return v
    
    # Correspondance partielle
    for v in valid_values:
        if v.lower() in value_str or value_str in v.lower():
            return v
    
    return default


def parse_llm_response(raw_response: Optional[str]) -> Dict[str, str]:
    """
    Parse une réponse LLM de manière sécurisée avec fallback
    """
    if not raw_response:
        logger.warning("Réponse LLM vide, utilisation des valeurs par défaut")
        return DEFAULT_VALUES.copy()
    
    try:
        # Extraire le JSON
        json_str = extract_json_from_text(raw_response)
        
        if not json_str:
            logger.warning(f"JSON non trouvé dans: {raw_response[:100]}...")
            return DEFAULT_VALUES.copy()
        
        # Parser le JSON
        parsed = json.loads(json_str)
        
        # Extraire et normaliser les valeurs
        motif = normalize_value(
            parsed.get("motif"),
            VALID_MOTIFS,
            DEFAULT_VALUES["motif"]
        )
        
        sentiment = normalize_value(
            parsed.get("sentiment"),
            VALID_SENTIMENTS,
            DEFAULT_VALUES["sentiment"]
        )
        
        urgence = normalize_value(
            parsed.get("urgence"),
            VALID_URGENCES,
            DEFAULT_VALUES["urgence"]
        )
        
        risque_churn = normalize_value(
            parsed.get("risque_churn"),
            VALID_CHURN,
            DEFAULT_VALUES["risque_churn"]
        )
        
        return {
            "motif": motif,
            "sentiment": sentiment,
            "urgence": urgence,
            "risque_churn": risque_churn
        }
        
    except json.JSONDecodeError as e:
        logger.warning(f"Erreur parsing JSON: {e}. Texte: {raw_response[:200]}...")
        return DEFAULT_VALUES.copy()
    
    except Exception as e:
        logger.error(f"Erreur inattendue lors du parsing: {e}")
        return DEFAULT_VALUES.copy()


def add_churn_risk_flag(df_row: Dict[str, Any]) -> bool:
    """
    Ajoute une colonne is_churn_risk basée sur risque_churn
    """
    risque = str(df_row.get("risque_churn", "faible")).lower()
    return risque in ["modéré", "élevé"]


def parse_batch_responses(batch_results: list) -> list:
    """
    Parse un batch de réponses LLM
    """
    parsed_results = []
    
    for result in batch_results:
        raw_response = result.get("raw_response")
        parsed = parse_llm_response(raw_response)
        
        # Ajouter is_churn_risk
        parsed["is_churn_risk"] = add_churn_risk_flag(parsed)
        
        parsed_results.append(parsed)
    
    return parsed_results
