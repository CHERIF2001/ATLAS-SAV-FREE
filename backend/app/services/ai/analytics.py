"""
Service d'analyse automatique des tickets avec Mistral AI.
Optimisé pour le coût et la pertinence.
"""
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

ANALYTICS_PROMPT = """Tu es un expert en analyse de support client pour Free.

TACHE : Analyser la conversation et extraire les indicateurs clés.

CONVERSATION :
{conversation}

FORMAT DE REPONSE ATTENDU (JSON UNIQUEMENT) :
{{
  "sentiment": "positif" | "neutre" | "negatif",
  "category": "facturation" | "technique" | "commercial" | "resiliation" | "autre",
  "urgency": "basse" | "moyenne" | "haute",
  "churn_risk": 0 à 100 (probabilité de départ),
  "summary": "résumé TRES PRECIS du problème technique ou commercial (max 15 mots)",
  "next_action": "action recommandée pour l'agent"
}}

CRITERES STRICTS :
- Sentiment : 
    * 'negatif' : Problème technique, panne, plainte, insatisfaction, résiliation.
    * 'neutre' : Demande d'information, question simple, procédure administrative sans plainte.
    * 'positif' : Remerciement, satisfaction, confirmation de résolution.
- Summary : Ne jamais mettre "Demande de support". Etre précis (ex: "Panne fibre depuis 3 jours", "Erreur facture 49€").
- Churn Risk : > 80 si mention de 'résiliation', 'concurrent', 'trop cher', 'départ'.
- Urgence : 'haute' si panne totale, blocage bloquant ou risque de churn élevé.

REPONDS UNIQUEMENT AVEC LE JSON."""


class AnalyticsService:
    """Service d'analyse automatique des tickets."""

    def __init__(self, mistral_client):
        self.mistral_client = mistral_client
        logger.info("AnalyticsService initialized")

    async def analyze_ticket(self, messages: List[Dict[str, Any]]) -> dict:
        """
        Analyser une conversation complète.
        
        Args:
            messages: Liste des messages du ticket [{"role": "user", "content": "..."}, ...]
            
        Returns:
            dict: Analytics complets
        """
        if not self.mistral_client:
            return self._get_default_analytics()

        # 1. Optimisation Coût : Ne pas analyser si le dernier message est trivial
        last_msg = messages[-1]["content"] if messages else ""
        if len(last_msg) < 5 or last_msg.lower() in ["ok", "merci", "d'accord", "non", "oui"]:
            logger.info("Skipping analytics for trivial message")
            return self._get_default_analytics()

        try:
            # 2. Préparer le contexte (Derniers 5 messages pour garder le contexte sans exploser les tokens)
            recent_messages = messages[-5:]
            conversation_text = "\n".join([f"{m.get('role', 'user').upper()}: {m.get('content', '')}" for m in recent_messages])
            
            prompt = ANALYTICS_PROMPT.format(conversation=conversation_text)
            
            # 3. Appel Mistral (Mode JSON si possible, sinon prompt strict)
            response = await self.mistral_client.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            # 4. Parsing robuste
            analytics = self._parse_analytics_response(response)
            analytics["analyzed_at"] = self._now_iso()
            
            # 5. ALERTE CHURN (Simulation)
            if analytics["churn_risk"] > 80:
                logger.critical(f"🚨 ALERTE CHURN DETECTEE ! Risque: {analytics['churn_risk']}% - Résumé: {analytics['summary']}")
                # Ici, on pourrait appeler un webhook Slack/Discord ou envoyer un email
                analytics["alert"] = "URGENT_RETENTION"
            
            return analytics
            
        except Exception as e:
            logger.exception(f"Error analyzing ticket: {e}")
            return self._get_default_analytics()

    def _parse_analytics_response(self, response: str) -> dict:
        """Parser la réponse JSON de Mistral avec nettoyage."""
        import re
        try:
            # Nettoyage des balises markdown ```json ... ```
            clean_response = re.sub(r'```json\s*|\s*```', '', response).strip()
            
            # Extraction du premier bloc JSON valide
            json_match = re.search(r'\{.*\}', clean_response, re.DOTALL)
            if json_match:
                clean_response = json_match.group(0)
            
            data = json.loads(clean_response)
            
            # Validation et valeurs par défaut
            return {
                "sentiment": data.get("sentiment", "neutre"),
                "category": data.get("category", "autre"),
                "urgency": data.get("urgency", "moyenne"),
                "churn_risk": min(max(int(data.get("churn_risk", 0)), 0), 100),
                "summary": data.get("summary", "Analyse en cours")[:100],
                "next_action": data.get("next_action", "Vérifier le dossier")[:100]
            }
            
        except Exception as e:
            logger.error(f"Analytics parsing error: {e} on response: {response}")
            return self._get_default_analytics()

    def _get_default_analytics(self) -> dict:
        return {
            "sentiment": "neutre",
            "category": "autre",
            "urgency": "moyenne",
            "churn_risk": 0,
            "summary": "En attente d'analyse",
            "next_action": "À traiter",
            "analyzed_at": self._now_iso()
        }

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat() + "Z"
