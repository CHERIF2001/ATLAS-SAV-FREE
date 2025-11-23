"""
Scraper pour récupérer la FAQ publique de Free et créer une base de connaissances.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict
import httpx
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FreeFAQScraper:
    """Scraper pour la FAQ publique de Free."""
    
    def __init__(self, output_dir: str = "knowledge_base"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.base_url = "https://www.free.fr"
        
    async def scrape_faq(self) -> List[Dict[str, str]]:
        """
        Scrape la FAQ publique de Free.
        
        Returns:
            Liste de documents avec question, réponse, catégorie
        """
        documents = []
        
        # URLs de FAQ publiques (exemples - à adapter selon le site réel)
        faq_urls = [
            "/assistance/",
            "/assistance/faq/",
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for url in faq_urls:
                try:
                    logger.info(f"Scraping {self.base_url}{url}")
                    response = await client.get(f"{self.base_url}{url}")
                    
                    if response.status_code == 200:
                        docs = self._parse_faq_page(response.text, url)
                        documents.extend(docs)
                        logger.info(f"Trouvé {len(docs)} documents sur {url}")
                    else:
                        logger.warning(f"Erreur {response.status_code} sur {url}")
                        
                except Exception as e:
                    logger.error(f"Erreur lors du scraping de {url}: {e}")
                    
        return documents
    
    def _parse_faq_page(self, html: str, url: str) -> List[Dict[str, str]]:
        """Parse une page FAQ et extrait les Q&A."""
        documents = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Chercher les sections de FAQ (à adapter selon la structure réelle)
        # Ceci est un exemple générique
        faq_items = soup.find_all(['div', 'article'], class_=['faq-item', 'question', 'qa'])
        
        for item in faq_items:
            try:
                # Extraire question et réponse
                question = item.find(['h2', 'h3', 'h4', 'strong', 'dt'])
                answer = item.find(['p', 'div', 'dd'])
                
                if question and answer:
                    documents.append({
                        'question': question.get_text(strip=True),
                        'answer': answer.get_text(strip=True),
                        'category': self._extract_category(url),
                        'source': url,
                        'type': 'faq'
                    })
            except Exception as e:
                logger.debug(f"Erreur parsing item: {e}")
                
        return documents
    
    def _extract_category(self, url: str) -> str:
        """Extrait la catégorie depuis l'URL."""
        if 'internet' in url.lower():
            return 'internet'
        elif 'mobile' in url.lower():
            return 'mobile'
        elif 'facture' in url.lower() or 'facturation' in url.lower():
            return 'facturation'
        elif 'technique' in url.lower():
            return 'technique'
        else:
            return 'general'
    
    async def generate_synthetic_faq(self) -> List[Dict[str, str]]:
        """
        Génère une FAQ synthétique réaliste pour Free.
        Utilisé comme fallback si le scraping ne fonctionne pas.
        """
        logger.info("Génération d'une FAQ synthétique...")
        
        synthetic_faq = [
            # Problèmes réseau
            {
                'question': "Je n'ai plus de connexion internet, que faire ?",
                'answer': "Vérifiez d'abord que tous les voyants de votre box sont allumés. Si le voyant internet clignote rouge, débranchez votre box pendant 30 secondes puis rebranchez-la. Attendez 5 minutes que la connexion se rétablisse. Si le problème persiste, contactez le support technique.",
                'category': 'technique',
                'source': 'synthetic',
                'type': 'faq'
            },
            {
                'question': "Mon débit internet est très lent, comment l'améliorer ?",
                'answer': "Plusieurs solutions : 1) Redémarrez votre box, 2) Vérifiez que vous êtes connecté en WiFi 5GHz si votre appareil le supporte, 3) Rapprochez-vous de la box ou utilisez un câble Ethernet, 4) Vérifiez qu'aucun appareil ne consomme beaucoup de bande passante, 5) Testez votre débit sur https://test-debit.free.fr",
                'category': 'technique',
                'source': 'synthetic',
                'type': 'faq'
            },
            {
                'question': "Le WiFi se déconnecte régulièrement",
                'answer': "Cela peut être dû à des interférences. Essayez de : 1) Changer le canal WiFi dans les paramètres de votre box, 2) Éloigner la box des autres appareils électroniques, 3) Utiliser la bande 5GHz moins encombrée, 4) Mettre à jour le firmware de votre box.",
                'category': 'technique',
                'source': 'synthetic',
                'type': 'faq'
            },
            
            # Facturation
            {
                'question': "Comment comprendre ma facture Free ?",
                'answer': "Votre facture Free comprend : 1) L'abonnement mensuel (forfait fixe), 2) Les éventuels hors-forfait (appels internationaux, SMS surtaxés), 3) Les frais de mise en service si nouveau client, 4) Les options souscrites. Vous pouvez consulter le détail sur votre espace client.",
                'category': 'facturation',
                'source': 'synthetic',
                'type': 'faq'
            },
            {
                'question': "Ma facture est plus élevée que d'habitude, pourquoi ?",
                'answer': "Plusieurs raisons possibles : 1) Frais de mise en service (premier mois), 2) Consommation hors-forfait, 3) Changement d'offre, 4) Options supplémentaires activées. Consultez le détail de votre facture sur votre espace client ou contactez le service client.",
                'category': 'facturation',
                'source': 'synthetic',
                'type': 'faq'
            },
            {
                'question': "Comment modifier mon moyen de paiement ?",
                'answer': "Connectez-vous à votre espace client Free, allez dans 'Mon compte' > 'Moyens de paiement'. Vous pouvez ajouter ou modifier votre carte bancaire ou RIB pour le prélèvement automatique. Les changements sont effectifs dès la prochaine facture.",
                'category': 'facturation',
                'source': 'synthetic',
                'type': 'faq'
            },
            
            # Offres et abonnements
            {
                'question': "Quelles sont les offres Freebox disponibles ?",
                'answer': "Free propose plusieurs offres : 1) Freebox Pop (29,99€/mois, fibre jusqu'à 5Gb/s), 2) Freebox Révolution (39,99€/mois, fibre jusqu'à 1Gb/s + Player TV), 3) Freebox Delta (49,99€/mois, fibre jusqu'à 8Gb/s + services premium). Toutes incluent appels illimités et TV.",
                'category': 'commercial',
                'source': 'synthetic',
                'type': 'faq'
            },
            {
                'question': "Comment vérifier l'éligibilité à la fibre ?",
                'answer': "Rendez-vous sur free.fr/freebox/, entrez votre adresse complète dans le test d'éligibilité. Vous saurez immédiatement si la fibre est disponible chez vous et quelles offres sont compatibles.",
                'category': 'commercial',
                'source': 'synthetic',
                'type': 'faq'
            },
            {
                'question': "Comment changer d'offre Freebox ?",
                'answer': "Connectez-vous à votre espace client, allez dans 'Mon abonnement' > 'Changer d'offre'. Sélectionnez la nouvelle offre souhaitée. Le changement est effectif sous 48h. Attention : certains changements peuvent entraîner des frais.",
                'category': 'commercial',
                'source': 'synthetic',
                'type': 'faq'
            },
            
            # Résiliation
            {
                'question': "Comment résilier mon abonnement Free ?",
                'answer': "Pour résilier : 1) Envoyez un courrier recommandé avec AR à : Free - Service Résiliation - 75371 Paris Cedex 08, 2) Indiquez votre numéro d'abonné et votre souhait de résiliation, 3) Renvoyez le matériel (box) dans les 15 jours. Aucun frais de résiliation chez Free.",
                'category': 'resiliation',
                'source': 'synthetic',
                'type': 'faq'
            },
            {
                'question': "Quand dois-je renvoyer ma Freebox après résiliation ?",
                'answer': "Vous avez 15 jours après la date de résiliation effective pour renvoyer votre Freebox. Utilisez l'étiquette de retour fournie. Le non-retour peut entraîner une facturation de 300€ pour le matériel.",
                'category': 'resiliation',
                'source': 'synthetic',
                'type': 'faq'
            },
            
            # Support technique
            {
                'question': "Comment redémarrer ma Freebox ?",
                'answer': "Pour redémarrer votre Freebox : 1) Débranchez l'alimentation électrique, 2) Attendez 30 secondes, 3) Rebranchez l'alimentation, 4) Attendez 5 minutes que tous les voyants se stabilisent. Cela résout la plupart des problèmes de connexion.",
                'category': 'technique',
                'source': 'synthetic',
                'type': 'faq'
            },
            {
                'question': "Que signifient les voyants de ma Freebox ?",
                'answer': "Voyants Freebox : 1) Power (vert fixe = allumée), 2) DSL/Fibre (vert fixe = connectée, rouge = problème ligne), 3) Internet (vert fixe = connexion OK, rouge = pas d'internet), 4) WiFi (vert = activé), 5) Tel (vert = téléphone OK). Si un voyant est rouge ou clignote, consultez l'assistance.",
                'category': 'technique',
                'source': 'synthetic',
                'type': 'faq'
            },
            {
                'question': "Comment accéder à l'interface de ma Freebox ?",
                'answer': "Connectez-vous au réseau WiFi de votre Freebox, puis ouvrez un navigateur et allez sur http://mafreebox.freebox.fr ou http://192.168.0.1. Utilisez le mot de passe indiqué sous votre box. Vous pourrez configurer WiFi, ports, etc.",
                'category': 'technique',
                'source': 'synthetic',
                'type': 'faq'
            },
        ]
        
        return synthetic_faq
    
    def save_documents(self, documents: List[Dict[str, str]], filename: str = "faq_documents.json"):
        """Sauvegarde les documents dans un fichier JSON."""
        output_file = self.output_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Sauvegardé {len(documents)} documents dans {output_file}")
        return output_file
    
    async def run(self):
        """Exécute le scraping complet."""
        logger.info("Démarrage du scraping de la FAQ Free...")
        
        # Essayer de scraper le site réel
        documents = await self.scrape_faq()
        
        # Si peu de résultats, ajouter la FAQ synthétique
        if len(documents) < 10:
            logger.info("Peu de documents scrapés, ajout de la FAQ synthétique...")
            synthetic_docs = await self.generate_synthetic_faq()
            documents.extend(synthetic_docs)
        
        # Sauvegarder
        if documents:
            output_file = self.save_documents(documents)
            logger.info(f"✅ Scraping terminé : {len(documents)} documents créés")
            return output_file
        else:
            logger.error("❌ Aucun document créé")
            return None


async def main():
    """Point d'entrée principal."""
    scraper = FreeFAQScraper()
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
