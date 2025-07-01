"""
Vector store service for managing document embeddings and similarity search
"""

import os
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import faiss
import numpy as np
from langchain_core.documents import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.exceptions import VectorStoreError
from app.services.embedding_service import EmbeddingService
from app.db.models import Document as DBDocument
from app.utils.ai_config import DOCUMENT_TYPE_KEYWORDS

logger = logging.getLogger("personal_ai_agent")


class VectorStoreService(ABC):
    """Abstract base class for vector store services"""
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        namespace: str,
        embedding_service: EmbeddingService
    ) -> int:
        """Add documents to the vector store"""
        pass
    
    @abstractmethod
    async def search_similar_chunks(
        self,
        query: str,
        embedding_service: EmbeddingService,
        user_id: int = None,
        document_id: Optional[int] = None,
        top_k: int = 20,
        metadata_filter: dict = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        pass


class FAISSVectorStoreService(VectorStoreService):
    """FAISS-based vector store service"""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or settings.VECTOR_DB_PATH
        self._indices: Dict[str, faiss.Index] = {}
        self._document_maps: Dict[str, List[Dict[str, Any]]] = {}
        
        # Constants
        self.MAX_CHUNKS_PER_TYPE = 3
        self.MAX_TOTAL_CHUNKS = 5
        self.HIGH_QUALITY_SCORE_THRESHOLD = 0.85
        
        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _get_index_path(self, namespace: str) -> str:
        """Get the file path for the FAISS index"""
        return os.path.join(self.storage_path, f"{namespace}.index")
    
    def _get_docmap_path(self, namespace: str) -> str:
        """Get the file path for the document map"""
        return os.path.join(self.storage_path, f"{namespace}.pkl")
    
    def _load_index(self, namespace: str) -> Tuple[Optional[faiss.Index], Optional[List[Dict[str, Any]]]]:
        """Load index and document map from disk"""
        index_path = self._get_index_path(namespace)
        docmap_path = self._get_docmap_path(namespace)
        
        if not os.path.exists(index_path) or not os.path.exists(docmap_path):
            return None, None
        
        try:
            index = faiss.read_index(index_path)
            with open(docmap_path, 'rb') as f:
                document_map = pickle.load(f)
            return index, document_map
        except Exception as e:
            logger.error(f"Error loading index for namespace {namespace}: {e}")
            raise VectorStoreError(
                f"Failed to load vector store for namespace {namespace}",
                details=str(e)
            )
    
    def _save_index(self, namespace: str, index: faiss.Index, document_map: List[Dict[str, Any]]):
        """Save index and document map to disk"""
        index_path = self._get_index_path(namespace)
        docmap_path = self._get_docmap_path(namespace)
        
        try:
            faiss.write_index(index, index_path)
            with open(docmap_path, 'wb') as f:
                pickle.dump(document_map, f)
            logger.debug(f"Saved index for namespace {namespace}")
        except Exception as e:
            logger.error(f"Error saving index for namespace {namespace}: {e}")
            raise VectorStoreError(
                f"Failed to save vector store for namespace {namespace}",
                details=str(e)
            )
    
    async def add_documents(
        self,
        documents: List[Document],
        namespace: str,
        embedding_service: EmbeddingService
    ) -> int:
        """
        Add documents to the FAISS vector store
        
        Args:
            documents: List of LangChain documents
            namespace: Namespace for the documents
            embedding_service: Service to generate embeddings
            
        Returns:
            Number of documents added
            
        Raises:
            VectorStoreError: If adding documents fails
        """
        if not documents:
            logger.warning("No documents provided to add_documents")
            return 0
        
        try:
            # Generate embeddings for documents
            texts = [doc.page_content for doc in documents]
            embeddings = await embedding_service.generate_embeddings(texts)
            
            # Load existing or create new index
            if namespace in self._indices:
                index = self._indices[namespace]
                doc_map = self._document_maps[namespace]
            else:
                index, doc_map = self._load_index(namespace)
                if index is None:
                    # Create new index
                    dimension = embedding_service.get_dimension()
                    index = faiss.IndexFlatL2(dimension)
                    doc_map = []
                
                self._indices[namespace] = index
                self._document_maps[namespace] = doc_map
            
            # Add embeddings to index
            index.add(embeddings)
            
            # Add documents to document map
            for doc in documents:
                doc_entry = {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                doc_map.append(doc_entry)
            
            # Save to disk
            self._save_index(namespace, index, doc_map)
            
            logger.info(f"Added {len(documents)} documents to namespace: {namespace}")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise VectorStoreError(
                "Failed to add documents to vector store",
                details=str(e)
            )
    
    def _calculate_score(self, distance: float) -> float:
        """Convert L2 distance to similarity score"""
        # For L2 distance, smaller is better, so we use inverse relationship
        return max(0.0, 1.0 - (distance / 2.0))
    
    async def _search_namespace(
        self,
        query: str,
        namespace: str,
        embedding_service: EmbeddingService,
        top_k: int = 20,
        metadata_filter: dict = None
    ) -> List[Dict[str, Any]]:
        """Search a single namespace for similar chunks"""
        try:
            logger.debug(f"Searching namespace: {namespace} for query: '{query}'")
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding(query)
            
            # Load index if not in memory
            if namespace not in self._indices:
                index, doc_map = self._load_index(namespace)
                if index is None:
                    logger.warning(f"No index found for namespace: {namespace}")
                    return []
                self._indices[namespace] = index
                self._document_maps[namespace] = doc_map
            
            index = self._indices[namespace]
            doc_map = self._document_maps[namespace]
            
            # Search index
            logger.debug(f"Searching index with {index.ntotal} vectors")
            D, I = index.search(
                np.array([query_embedding]), 
                min(top_k * 2, index.ntotal)
            )
            
            # Get results
            results = []
            for i, (dist, idx) in enumerate(zip(D[0], I[0])):
                if idx < 0 or idx >= len(doc_map):
                    continue
                
                entry = doc_map[idx]
                content = entry.get("content", "")
                metadata = entry.get("metadata", {})
                
                # Calculate score
                score = self._calculate_score(dist)
                
                # Skip low-quality results
                if score < 0.1:
                    logger.debug(f"Skipping result {i} with low score: {score:.2f} (distance: {dist:.4f})")
                    continue
                
                # Apply metadata filter if provided
                if metadata_filter:
                    if not all(metadata.get(k) == v for k, v in metadata_filter.items()):
                        logger.debug(f"Skipping result {i} due to metadata filter mismatch")
                        continue
                
                # Ensure we have content
                if not content:
                    logger.debug(f"Skipping result {i} with empty content")
                    continue
                
                # Add result
                results.append({
                    "content": content,
                    "metadata": metadata,
                    "score": score,
                    "namespace": namespace
                })
                
                logger.debug(f"Result {i}: score={score:.2f}, content_length={len(content)}")
            
            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Take top_k results
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching namespace {namespace}: {e}")
            raise VectorStoreError(
                f"Failed to search namespace {namespace}",
                details=str(e)
            )
    
    async def search_similar_chunks(
        self,
        query: str,
        embedding_service: EmbeddingService,
        user_id: int = None,
        document_id: Optional[int] = None,
        top_k: int = 20,
        metadata_filter: dict = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks across namespaces
        
        Args:
            query: The search query
            embedding_service: Service to generate embeddings
            user_id: The user ID to filter by
            document_id: Optional document ID to filter by
            top_k: Number of results to return
            metadata_filter: Optional metadata filter
            
        Returns:
            List of similar chunks
            
        Raises:
            VectorStoreError: If search fails
        """
        try:
            # Get all namespaces
            namespaces = []
            
            logger.debug(f"Starting search for query: '{query}', user_id: {user_id}, document_id: {document_id}")
            
            # Get all index files in the vector DB directory
            for filename in os.listdir(self.storage_path):
                if filename.endswith(".index"):
                    namespace = filename[:-6]  # Remove .index extension
                    
                    # Filter by user_id if provided
                    if user_id is not None and not namespace.startswith(f"user_{user_id}_"):
                        continue
                    
                    # Filter by document_id if provided
                    if document_id is not None:
                        # Get document from database
                        engine = create_engine(settings.DATABASE_URL)
                        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                        db = SessionLocal()
                        try:
                            document = db.query(DBDocument).filter(DBDocument.id == document_id).first()
                            if document and namespace != document.vector_namespace:
                                continue
                        finally:
                            db.close()
                    
                    namespaces.append(namespace)
            
            logger.debug(f"Found {len(namespaces)} namespaces for search: {namespaces}")
            
            if not namespaces:
                logger.warning(f"No namespaces found for user_id: {user_id}, document_id: {document_id}")
                return []
            
            # Search each namespace
            all_results = []
            
            for namespace in namespaces:
                namespace_results = await self._search_namespace(
                    query, namespace, embedding_service, top_k, metadata_filter
                )
                logger.debug(f"Found {len(namespace_results)} results in namespace {namespace}")
                all_results.extend(namespace_results)
            
            # Sort all results by score
            all_results.sort(key=lambda x: x["score"], reverse=True)
            
            # Take top results
            return all_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching for similar chunks: {e}")
            raise VectorStoreError(
                "Failed to search for similar chunks",
                details=str(e)
            )


# Global instance for backward compatibility
_default_vector_store_service: Optional[FAISSVectorStoreService] = None


def get_vector_store_service() -> FAISSVectorStoreService:
    """Get the default vector store service instance"""
    global _default_vector_store_service
    
    if _default_vector_store_service is None:
        _default_vector_store_service = FAISSVectorStoreService()
    
    return _default_vector_store_service