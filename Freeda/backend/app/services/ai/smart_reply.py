import re
from typing import Optional

class SmartReplyService:
    """
    Service de réponses intelligentes pour réduire les coûts d'API IA.
    Gère les réponses pré-enregistrées pour les questions fréquentes.
    """
    
    def __init__(self):
        # Règles de réponses rapides (Regex -> Réponse)
        # L'ordre est important : les règles sont testées séquentiellement
        self.rules = [
            # Salutations
            (r"\b(bonjour|salut|hello|coucou|hey)\b", 
             "Bonjour ! Je suis l'assistant virtuel de Free. Comment puis-je vous aider aujourd'hui ?"),
            
            # Politesse
            (r"\b(merci|remercie|cimer|top|super)\b", 
             "Je vous en prie ! Ravi d'avoir pu vous aider. Avez-vous d'autres questions ?"),
            
            (r"\b(au revoir|bye|adieu|a\+|bonne journ(ée|ee)|bonne soir(ée|ee))\b", 
             "Au revoir ! Toute l'équipe Free vous souhaite une excellente journée."),
            
            # Facturation
            (r"\b(facture|payer|paiement|prélèvement|montant)\b", 
             "Vous pouvez consulter, télécharger et payer vos factures directement sur votre Espace Abonné : https://subscribe.free.fr/login/\n\nRubrique 'Mon abonnement' > 'Mes factures'."),
            
            # Identifiants
            (r"\b(mot de passe|mdp|password|identifiant|connexion|connecter)\b", 
             "Pour récupérer vos identifiants ou réinitialiser votre mot de passe, rendez-vous sur la page de connexion de l'Espace Abonné et cliquez sur 'Mot de passe oublié'."),
            
            # Contact Humain
            (r"\b(humain|personne|agent|conseiller|téléphone|appeler|3244)\b", 
             "Si je ne parviens pas à vous aider, vous pouvez contacter nos conseillers au 3244 (appel gratuit depuis une ligne Freebox) ou via l'assistance en visio Face to Free."),
            
            # Boutiques
            (r"\b(boutique|magasin|center|shop|agence)\b", 
             "Trouvez la boutique Free (Free Center) la plus proche de chez vous ici : https://www.free.fr/boutiques/"),
             
            # Déménagement
            (r"\b(déménagement|déménager|démenagement|demenager)\b", 
             "Vous déménagez ? Déclarez votre déménagement directement dans votre Espace Abonné, rubrique 'Mon abonnement' > 'Déménager mon abonnement'. Pensez à le faire 15 jours avant !"),
             
            # Panne générale (Exemple simple)
            (r"\b(panne générale|incident|coupure générale)\b", 
             "Vous pouvez vérifier l'état du réseau Free dans votre zone sur : https://www.free-reseau.fr/ ou sur votre Espace Abonné.")
        ]

    def get_quick_response(self, message: str) -> Optional[str]:
        """
        Vérifie si le message correspond à une règle de réponse rapide.
        Retourne la réponse si trouvée, sinon None.
        Coût : 0€ (Pas d'appel IA)
        """
        # Nettoyage basique
        message_lower = message.lower().strip()
        
        # Vérification des règles
        for pattern, response in self.rules:
            # Recherche du pattern dans le message
            if re.search(pattern, message_lower):
                return response
                
        return None

# Instance globale
smart_reply = SmartReplyService()
