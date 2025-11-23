"""
Service RAG (Retrieval-Augmented Generation) pour enrichir les réponses du chatbot.
Utilise ChromaDB pour le stockage vectoriel et Mistral pour les embeddings.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import httpx
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service de Retrieval-Augmented Generation."""
    
    def __init__(
        self,
        mistral_api_key: str,
        chroma_persist_dir: str = "./chroma_db",
        collection_name: str = "freeda_knowledge"
    ):
        self.mistral_api_key = mistral_api_key
        self.collection_name = collection_name
        
        # Initialiser ChromaDB
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=chroma_persist_dir,
            anonymized_telemetry=False
        ))
        
        # Créer ou récupérer la collection
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' chargée ({self.collection.count()} documents)")
        except:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Base de connaissances Freeda"}
            )
            logger.info(f"Collection '{collection_name}' créée")
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Génère un embedding pour un texte avec Mistral Embed.
        
        Args:
            text: Texte à vectoriser
            
        Returns:
            Vecteur d'embedding
        """
        url = "https://api.mistral.ai/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.mistral_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-embed",
            "input": [text]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    
    async def add_documents(self, documents: List[Dict[str, str]]):
        """
        Ajoute des documents à la base de connaissances.
        
        Args:
            documents: Liste de documents avec 'question', 'answer', 'category', etc.
        """
        logger.info(f"Ajout de {len(documents)} documents à la base de connaissances...")
        
        ids = []
        embeddings = []
        metadatas = []
        documents_text = []
        
        for i, doc in enumerate(documents):
            # Créer un texte combiné pour l'embedding
            combined_text = f"Question: {doc['question']}\nRéponse: {doc['answer']}"
            
            # Générer l'embedding
            try:
                embedding = await self.get_embedding(combined_text)
                
                ids.append(f"doc_{i}")
                embeddings.append(embedding)
                documents_text.append(combined_text)
                metadatas.append({
                    'question': doc['question'],
                    'answer': doc['answer'],
                    'category': doc.get('category', 'general'),
                    'source': doc.get('source', 'unknown'),
                    'type': doc.get('type', 'faq')
                })
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Traité {i + 1}/{len(documents)} documents...")
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'embedding du document {i}: {e}")
        
        # Ajouter à ChromaDB
        if embeddings:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents_text,
                metadatas=metadatas
            )
            logger.info(f"✅ {len(embeddings)} documents ajoutés à ChromaDB")
        else:
            logger.warning("Aucun document n'a pu être ajouté")
    
    async def search(
        self,
        query: str,
        n_results: int = 3,
        category: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Recherche les documents les plus pertinents pour une requête.
        
        Args:
            query: Question de l'utilisateur
            n_results: Nombre de résultats à retourner
            category: Filtrer par catégorie (optionnel)
            
        Returns:
            Liste de documents pertinents
        """
        # Générer l'embedding de la requête
        query_embedding = await self.get_embedding(query)
        
        # Préparer le filtre
        where = {"category": category} if category else None
        
        # Rechercher dans ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Formater les résultats
        documents = []
        if results and results['metadatas']:
            for i, metadata in enumerate(results['metadatas'][0]):
                documents.append({
                    'question': metadata['question'],
                    'answer': metadata['answer'],
                    'category': metadata['category'],
                    'relevance_score': 1 - results['distances'][0][i] if results['distances'] else 0
                })
        
        return documents
    
    async def get_context_for_query(
        self,
        query: str,
        max_context_length: int = 1000
    ) -> str:
        """
        Récupère le contexte pertinent pour une requête.
        
        Args:
            query: Question de l'utilisateur
            max_context_length: Longueur maximale du contexte
            
        Returns:
            Contexte formaté pour le LLM
        """
        # Rechercher les documents pertinents
        documents = await self.search(query, n_results=3)
        
        if not documents:
            return ""
        
        # Construire le contexte
        context_parts = ["Informations pertinentes de la base de connaissances:\n"]
        current_length = len(context_parts[0])
        
        for doc in documents:
            doc_text = f"\nQ: {doc['question']}\nR: {doc['answer']}\n"
            
            if current_length + len(doc_text) > max_context_length:
                break
                
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "".join(context_parts)
    
    def get_stats(self) -> Dict:
        """Retourne des statistiques sur la base de connaissances."""
        count = self.collection.count()
        
        # Compter par catégorie
        categories = {}
        if count > 0:
            all_docs = self.collection.get()
            for metadata in all_docs['metadatas']:
                cat = metadata.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
        
        return {
            'total_documents': count,
            'categories': categories,
            'collection_name': self.collection_name
        }
    
    async def load_from_file(self, filepath: str):
        """
        Charge des documents depuis un fichier JSON.
        
        Args:
            filepath: Chemin vers le fichier JSON
        """
        logger.info(f"Chargement des documents depuis {filepath}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        await self.add_documents(documents)
        
        logger.info(f"✅ {len(documents)} documents chargés depuis {filepath}")
