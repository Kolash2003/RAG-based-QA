import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import uuid
from app.config import settings
from app.utils.logger import logger


class VectorStore:
    """Manages vector embeddings and similarity search using ChromaDB."""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Load embedding model
        logger.info("loading_embedding_model", model=settings.embedding_model)
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        
        self.collection = None
        logger.info("vector_store_initialized")
    
    def create_collection(self, collection_name: str, reset: bool = False):
        """Create or get a collection."""
        try:
            if reset:
                try:
                    self.client.delete_collection(collection_name)
                    logger.info("collection_deleted", name=collection_name)
                except Exception:
                    pass
            
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("collection_created", name=collection_name)
        except Exception as e:
            logger.error("collection_creation_failed", error=str(e))
            raise
    
    def add_documents(self, chunks: List[Dict], document_id: str):
        """Add document chunks to vector store."""
        if not self.collection:
            raise ValueError("No collection initialized. Call create_collection first.")
        
        try:
            texts = [chunk["text"] for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Prepare metadata
            metadatas = []
            for i, chunk in enumerate(chunks):
                metadata = chunk.get("metadata", {}).copy()
                metadata.update({
                    "document_id": document_id,
                    "chunk_index": i,
                    "chunk_total": len(chunks)
                })
                metadatas.append(metadata)
            
            # Generate unique IDs
            ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(
                "documents_added",
                document_id=document_id,
                num_chunks=len(chunks)
            )
            
        except Exception as e:
            logger.error("document_addition_failed", error=str(e))
            raise
    
    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """Search for similar documents."""
        if not self.collection:
            raise ValueError("No collection initialized.")
        
        try:
            top_k = top_k or settings.top_k_results
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i]
                    })
            
            logger.info("search_completed", query=query[:50], num_results=len(formatted_results))
            return formatted_results
            
        except Exception as e:
            logger.error("search_failed", error=str(e))
            raise
    
    def delete_document(self, document_id: str):
        """Delete all chunks of a document."""
        if not self.collection:
            return
        
        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info("document_deleted", document_id=document_id)
        except Exception as e:
            logger.error("document_deletion_failed", error=str(e))
            raise
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the current collection."""
        if not self.collection:
            return {"status": "no_collection"}
        
        try:
            count = self.collection.count()
            return {
                "name": self.collection.name,
                "count": count,
                "status": "active"
            }
        except Exception as e:
            logger.error("stats_retrieval_failed", error=str(e))
            return {"status": "error", "error": str(e)}


vector_store = VectorStore()