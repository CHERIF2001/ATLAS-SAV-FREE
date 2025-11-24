import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import httpx
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class RAGService:
    
    def __init__(self, mistral_api_key: str, chroma_persist_dir: str = "./chroma_db", collection_name: str = "freeda_knowledge"):
        self.mistral_api_key = mistral_api_key
        self.collection_name = collection_name
        
        self.chroma_client = chromadb.Client(Settings(persist_directory=chroma_persist_dir, anonymized_telemetry=False))
        
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' chargée ({self.collection.count()} documents)")
        except:
            self.collection = self.chroma_client.create_collection(name=collection_name, metadata={"description": "Base de connaissances Freeda"})
            logger.info(f"Collection '{collection_name}' créée")
    
    async def get_embedding(self, text: str) -> List[float]:
        url = "https://api.mistral.ai/v1/embeddings"
        headers = {"Authorization": f"Bearer {self.mistral_api_key}", "Content-Type": "application/json"}
        payload = {"model": "mistral-embed", "input": [text]}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    
    async def add_documents(self, documents: List[Dict[str, str]]):
        logger.info(f"Ajout de {len(documents)} documents à la base de connaissances...")
        
        ids = []
        embeddings = []
        metadatas = []
        docs_text = []
        
        for i, doc in enumerate(documents):
            combined = f"Question: {doc['question']}\nRéponse: {doc['answer']}"
            
            try:
                emb = await self.get_embedding(combined)
                
                ids.append(f"doc_{i}")
                embeddings.append(emb)
                docs_text.append(combined)
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
        
        if embeddings:
            self.collection.add(ids=ids, embeddings=embeddings, documents=docs_text, metadatas=metadatas)
            logger.info(f"✅ {len(embeddings)} documents ajoutés à ChromaDB")
        else:
            logger.warning("Aucun document n'a pu être ajouté")
    
    async def search(self, query: str, n_results: int = 3, category: Optional[str] = None) -> List[Dict[str, str]]:
        q_emb = await self.get_embedding(query)
        where = {"category": category} if category else None
        
        results = self.collection.query(query_embeddings=[q_emb], n_results=n_results, where=where)
        
        docs = []
        if results and results['metadatas']:
            for i, meta in enumerate(results['metadatas'][0]):
                docs.append({
                    'question': meta['question'],
                    'answer': meta['answer'],
                    'category': meta['category'],
                    'relevance_score': 1 - results['distances'][0][i] if results['distances'] else 0
                })
        
        return docs
    
    async def get_context(self, query: str, max_context_length: int = 1000) -> str:
        docs = await self.search(query, n_results=3)
        
        if not docs:
            return ""
        
        ctx_parts = ["Informations pertinentes de la base de connaissances:\n"]
        curr_len = len(ctx_parts[0])
        
        for doc in docs:
            doc_txt = f"\nQ: {doc['question']}\nR: {doc['answer']}\n"
            
            if curr_len + len(doc_txt) > max_context_length:
                break
                
            ctx_parts.append(doc_txt)
            curr_len += len(doc_txt)
        
        return "".join(ctx_parts)
    
    def get_stats(self) -> Dict:
        count = self.collection.count()
        
        cats = {}
        if count > 0:
            all_docs = self.collection.get()
            for meta in all_docs['metadatas']:
                cat = meta.get('category', 'unknown')
                cats[cat] = cats.get(cat, 0) + 1
        
        return {'total_documents': count, 'categories': cats, 'collection_name': self.collection_name}
    
    async def load_from_file(self, filepath: str):
        logger.info(f"Chargement des documents depuis {filepath}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            docs = json.load(f)
        
        await self.add_documents(docs)
        
        logger.info(f"✅ {len(docs)} documents chargés depuis {filepath}")
