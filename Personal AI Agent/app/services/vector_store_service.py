"""
Vector store service for managing document embeddings and similarity search
"""

import os
import pickle
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
import faiss
import numpy as np
from langchain_core.documents import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.exceptions import VectorStoreError
from app.services.embedding_service import EmbeddingService
from app.db.models import Document as DBDocument
# Document type keywords - moved from deleted ai_config.py
DOCUMENT_TYPE_KEYWORDS = {
    'vacation': [
        'vacation', 'travel', 'trip', 'holiday', 'airline', 'flight', 'hotel', 
        'rental car', 'thailand', 'phuket', 'bangkok', 'resort', 'tour', 'beach', 
        'island', 'visit', 'journey', 'tourism', 'sightseeing', 'adventure'
    ],
    'resume': [
        'resume', 'cv', 'work history', 'experience', 'education', 'skill', 
        'professional', 'job', 'technical', 'programming', 'framework', 'language', 
        'certification', 'qualification', 'expertise', 'proficiency', 'accomplishment',
        'career', 'developer', 'software', 'engineer', 'coding', 'technology', 
        'automation', 'testing', 'competency'
    ],
    'expense': [
        'expense', 'budget', 'cost', 'spent', '$', 'dollar', 'payment', 'finance', 
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 
        'september', 'october', 'november', 'december', 'money', 'price', 'pay', 
        'paid', 'bill', 'invoice', 'receipt', 'purchase', 'transaction', 'charge'
    ],
    'prompt_engineering': [
        'prompt', 'engineering', 'llm', 'ai', 'language model', 'gpt', 'instruction',
        'artificial intelligence', 'chatgpt', 'chat', 'completion', 'token',
        'parameter', 'temperature', 'top-p', 'top-k', 'context window', 'few-shot',
        'zero-shot', 'one-shot', 'chain of thought', 'cot', 'role prompting', 
        'system prompt', 'machine learning', 'transformer', 'neural network', 
        'deep learning', 'model training', 'natural language processing', 'nlp'
    ]
}

logger = logging.getLogger("personal_ai_agent")


class VectorStoreService(ABC):
    """Abstract base class for vector store services"""
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        namespace: str,
        embedding_service: EmbeddingService,
        document_type: str = None
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
        
        # Constants for more focused responses
        self.MAX_CHUNKS_PER_TYPE = 2  # Reduced from 3
        self.MAX_TOTAL_CHUNKS = 3     # Reduced from 5  
        self.HIGH_QUALITY_SCORE_THRESHOLD = 0.85
        
        # Category-specific constants
        self.CATEGORY_DIRECTORIES = {
            'financial': 'financial',
            'long_form': 'long_form', 
            'generic': 'generic'
        }
        
        # Ensure storage directory and category subdirectories exist
        os.makedirs(self.storage_path, exist_ok=True)
        for category in self.CATEGORY_DIRECTORIES.values():
            category_path = os.path.join(self.storage_path, category)
            os.makedirs(category_path, exist_ok=True)
            logger.info(f"Ensured category directory exists: {category_path}")
    
    def _get_category_from_namespace(self, namespace: str) -> str:
        """Extract document category from namespace or metadata"""
        # Try to extract category from namespace if it follows pattern
        for category in self.CATEGORY_DIRECTORIES.keys():
            if category in namespace.lower():
                return category
        return 'generic'  # Default fallback
    
    def _get_index_path(self, namespace: str, category: str = None) -> str:
        """Get the file path for the FAISS index with category organization"""
        if category is None:
            category = self._get_category_from_namespace(namespace)
        
        category_dir = self.CATEGORY_DIRECTORIES.get(category, 'generic')
        category_path = os.path.join(self.storage_path, category_dir)
        return os.path.join(category_path, f"{namespace}.index")
    
    def _get_docmap_path(self, namespace: str, category: str = None) -> str:
        """Get the file path for the document map with category organization"""
        if category is None:
            category = self._get_category_from_namespace(namespace)
            
        category_dir = self.CATEGORY_DIRECTORIES.get(category, 'generic')
        category_path = os.path.join(self.storage_path, category_dir)
        return os.path.join(category_path, f"{namespace}.pkl")
    
    def _load_index(self, namespace: str) -> Tuple[Optional[faiss.Index], Optional[List[Dict[str, Any]]]]:
        """Load index and document map from disk"""
        # Try to find the index in category directories first
        for category, category_dir in self.CATEGORY_DIRECTORIES.items():
            category_path = os.path.join(self.storage_path, category_dir)
            
            # Try both original namespace and category-prefixed namespace
            namespaces_to_try = [namespace, f"{category}_{namespace}"]
            
            for ns in namespaces_to_try:
                index_path = os.path.join(category_path, f"{ns}.index")
                docmap_path = os.path.join(category_path, f"{ns}.pkl")
                
                if os.path.exists(index_path) and os.path.exists(docmap_path):
                    try:
                        index = faiss.read_index(index_path)
                        with open(docmap_path, 'rb') as f:
                            document_map = pickle.load(f)
                        return index, document_map
                    except Exception as e:
                        logger.error(f"Error loading index for namespace {ns} from {category}: {e}")
                        continue
        
        # Fallback to root directory (for backward compatibility)
        index_path = os.path.join(self.storage_path, f"{namespace}.index")
        docmap_path = os.path.join(self.storage_path, f"{namespace}.pkl")
        
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
    
    def _save_index(self, namespace: str, index: faiss.Index, document_map: List[Dict[str, Any]], document_type: str = None):
        """Save index and document map to disk"""
        # Use document_type if provided, otherwise fall back to namespace detection
        category = document_type if document_type else self._get_category_from_namespace(namespace)
        index_path = self._get_index_path(namespace, category)
        docmap_path = self._get_docmap_path(namespace, category)
        
        try:
            # Ensure directory exists before saving
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            os.makedirs(os.path.dirname(docmap_path), exist_ok=True)
            
            faiss.write_index(index, index_path)
            with open(docmap_path, 'wb') as f:
                pickle.dump(document_map, f)
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
        embedding_service: EmbeddingService,
        document_type: str = None
    ) -> int:
        """
        Add documents to the FAISS vector store
        
        Args:
            documents: List of LangChain documents
            namespace: Namespace for the documents
            embedding_service: Service to generate embeddings
            document_type: Optional document type (financial, long_form, generic)
            
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
            
            # Save to disk with document type for correct categorization
            self._save_index(namespace, index, doc_map, document_type)
            
            logger.info(f"Added {len(documents)} documents to namespace: {namespace}")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise VectorStoreError(
                "Failed to add documents to vector store",
                details=str(e)
            )
    
    def _calculate_score(self, distance: float) -> float:
        """Convert L2 distance to similarity score (more permissive)"""
        # For L2 distance, smaller is better, so we use inverse relationship
        # Made more permissive by using a larger divisor to prevent overly strict filtering
        return max(0.0, 1.0 - (distance / 4.0))
    
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
                
                # Skip low-quality results - use higher threshold for more relevant results
                if score < 0.2:  # Increased from 0.05 for better relevance filtering
                    continue
                
                # Apply metadata filter if provided
                if metadata_filter:
                    if not all(metadata.get(k) == v for k, v in metadata_filter.items()):
                        continue
                
                # Ensure we have content
                if not content:
                    continue
                
                # Add result
                results.append({
                    "content": content,
                    "metadata": metadata,
                    "score": score,
                    "namespace": namespace
                })
                
            
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
    
    def _is_financial_query(self, query: str) -> bool:
        """Check if query is financial-related"""
        query_lower = query.lower()
        financial_keywords = [
            'paid', 'sent', 'spent', 'cost', 'price', 'money', 'dollar', '$',
            'netflix', 'uber', 'amazon', 'restaurant', 'grocery', 'gas',
            'zelle', 'venmo', 'paypal', 'transfer', 'payment', 'transaction',
            'bank', 'card', 'debit', 'credit', 'balance', 'statement'
        ]
        return any(keyword in query_lower for keyword in financial_keywords)
    
    def _extract_financial_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from financial queries"""
        entities = {}
        query_lower = query.lower()
        
        # Extract merchant/payee names
        merchant_patterns = [
            r'(?:paid|sent|spending|spent|cost|price).*?(?:for|to|at|on|in)\s+([a-zA-Z][a-zA-Z\s]{2,30})(?:\?|$)',
            r'(?:how much|what did).*?(?:for|to|at|on|in)\s+([a-zA-Z][a-zA-Z\s]{2,30})(?:\?|$)',
            r'([a-zA-Z][a-zA-Z\s]+?)(?:\s+cost|\s+price|\s+charge)',
        ]
        
        for pattern in merchant_patterns:
            match = re.search(pattern, query_lower)
            if match:
                merchant = match.group(1).strip()
                if len(merchant) > 2:
                    entities['merchant'] = merchant
                    break
        
        # Extract payment methods
        payment_methods = ['zelle', 'venmo', 'paypal', 'card', 'cash', 'transfer']
        for method in payment_methods:
            if method in query_lower:
                entities['payment_method'] = method
                break
        
        # Extract locations - be more precise with location extraction
        location_patterns = [
            r'(?:in|at|from|to|for)\s+([a-zA-Z][a-zA-Z\s]{2,20})(?:\s|$|\?|:|,)',
            r'([a-zA-Z][a-zA-Z\s]{2,20})\s+(?:restaurant|store|shop|hotel|airport)',
            r'(?:spent|cost|paid).*?(?:in|at|from|to|for)\s+([a-zA-Z][a-zA-Z\s]{2,20})(?:\s|$|\?|:|,)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1).strip()
                if len(location) > 2:
                    entities['location'] = location
                    # Also set as merchant for backward compatibility
                    if 'merchant' not in entities:
                        entities['merchant'] = location
                    break
        
        return entities
    
    def _filter_financial_results(self, results: List[Dict[str, Any]], financial_entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter and boost financial results based on extracted entities"""
        filtered_results = []
        
        for result in results:
            content = result.get('content', '').lower()
            metadata = result.get('metadata', {})
            score = result.get('score', 0)
            
            # Check for entity matches
            entity_matches = 0
            
            # Check merchant/payee match
            if 'merchant' in financial_entities:
                merchant = financial_entities['merchant']
                # Direct exact match
                if merchant in content or (metadata.get('payee') and merchant in metadata.get('payee', '').lower()):
                    entity_matches += 3  # High weight for merchant matches
                # More flexible matching for locations and airline codes
                elif len(merchant) > 3:
                    try:
                        # Use word boundaries to avoid partial matches that cause confusion
                        pattern = r'\b' + re.escape(merchant) + r'\b'
                        if re.search(pattern, content, re.IGNORECASE):
                            entity_matches += 3  # High weight for exact word matches
                        else:
                            # Special handling for airline codes and city combinations
                            # e.g., "thy istanbul" should match "unifree ist" and "istanbul"
                            merchant_words = merchant.split()
                            content_lower = content.lower()
                            
                            # Check if any word in merchant appears in content
                            word_matches = 0
                            for word in merchant_words:
                                if len(word) >= 3:  # Only check meaningful words
                                    if word in content_lower:
                                        word_matches += 1
                                    # Also check for partial matches (e.g., "ist" in "unifree ist")
                                    elif len(word) >= 4:
                                        for content_word in content_lower.split():
                                            if word in content_word or content_word in word:
                                                word_matches += 1
                                                break
                            
                            # If at least one significant word matches, consider it a match
                            if word_matches > 0:
                                entity_matches += 2  # Medium weight for partial matches
                    except Exception:
                        # Fallback to simple string matching if regex fails
                        if merchant in content:
                            entity_matches += 2
            
            # Check payment method match  
            if 'payment_method' in financial_entities:
                payment_method = financial_entities['payment_method']
                if payment_method in content or (metadata.get('payment_method') and payment_method in metadata.get('payment_method', '').lower()):
                    entity_matches += 2  # Medium weight for payment method
            
            # Check location match - ensure location-specific queries are precise
            if 'location' in financial_entities:
                location = financial_entities['location']
                try:
                    # Use word boundaries for location matching to avoid confusion
                    pattern = r'\b' + re.escape(location) + r'\b'
                    if re.search(pattern, content, re.IGNORECASE):
                        entity_matches += 3  # High weight for location matches
                    elif location in content or (metadata.get('location') and location in metadata.get('location', '').lower()):
                        entity_matches += 2  # Medium weight for partial location matches
                except Exception:
                    # Fallback to simple string matching if regex fails
                    if location in content:
                        entity_matches += 2
            
            # Apply negative filtering for location-specific queries (smarter location matching)
            if 'location' in financial_entities:
                query_location = financial_entities['location'].lower()
                # List of common travel/location keywords to check for conflicts
                common_locations = ['rome', 'istanbul', 'paris', 'london', 'berlin', 'madrid', 'barcelona', 'amsterdam', 'vienna', 'prague', 'budapest', 'warsaw', 'stockholm', 'oslo', 'copenhagen', 'helsinki', 'dublin', 'lisbon', 'athens', 'moscow', 'tokyo', 'bangkok', 'singapore', 'hong kong', 'sydney', 'melbourne', 'new york', 'los angeles', 'chicago', 'miami', 'toronto', 'vancouver']
                
                # Check if content mentions other locations
                content_lower = content.lower()
                
                # Smart location matching: check if query location contains any of the common locations
                query_location_words = query_location.split()
                query_contains_location = any(word in common_locations for word in query_location_words)
                
                other_locations_found = 0
                for location in common_locations:
                    # Only penalize if:
                    # 1. The location is not the same as query location
                    # 2. The location is not part of the query location (e.g., "istanbul" in "thy istanbul")
                    # 3. The location appears in the content
                    if (location != query_location and 
                        location not in query_location and 
                        location in content_lower):
                        # Check if it's a word boundary match to avoid false positives
                        try:
                            pattern = r'\b' + re.escape(location) + r'\b'
                            if re.search(pattern, content_lower):
                                other_locations_found += 1
                                entity_matches -= 2  # Heavier penalty for each other location mentioned
                        except Exception:
                            # If regex fails, skip this location
                            continue
                
                # If content mentions multiple other locations, it's likely not relevant
                if other_locations_found >= 2:
                    entity_matches -= 3  # Additional penalty for mixed location content
            
            # Boost score based on entity matches
            if entity_matches > 0:
                score = min(1.0, score + (entity_matches * 0.1))  # Boost but cap at 1.0
                result['score'] = score
            
            # Only include results with entity matches for financial queries
            if entity_matches > 0 or not financial_entities:
                # For financial queries, extract and clean the specific transaction data
                if 'merchant' in financial_entities:
                    merchant = financial_entities['merchant']
                    cleaned_content = self._extract_specific_transaction(result.get('content', ''), merchant)
                    if cleaned_content != result.get('content', ''):
                        result['content'] = cleaned_content
                
                filtered_results.append(result)
        
        return filtered_results
    
    def _extract_specific_transaction(self, content: str, merchant: str) -> str:
        """Extract only the specific transaction line for the merchant"""
        lines = content.split('\n')
        specific_lines = []
        
        for line in lines:
            line_lower = line.lower()
            merchant_lower = merchant.lower()
            
            # Direct match
            if merchant_lower in line_lower:
                specific_lines.append(line.strip())
            # Partial match for locations (e.g., "istanbul" matches "thy istanbul")
            elif len(merchant_lower) > 3:
                # Check if merchant is contained in any word or vice versa
                line_words = line_lower.split()
                for word in line_words:
                    if merchant_lower in word or word in merchant_lower:
                        specific_lines.append(line.strip())
                        break
        
        # If we found specific lines, return them
        if specific_lines:
            return '\n'.join(specific_lines)
        
        # Otherwise return original content
        return content

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
        Search for similar chunks across namespaces with financial query optimization
        
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
            # Check if this is a financial query and extract entities
            is_financial = self._is_financial_query(query)
            financial_entities = self._extract_financial_entities(query) if is_financial else {}
            
            # Get all namespaces from both root and category directories
            namespaces = []
            
            # Search in root directory (for backward compatibility)
            if os.path.exists(self.storage_path):
                for filename in os.listdir(self.storage_path):
                    if filename.endswith(".index"):
                        namespace = filename[:-6]  # Remove .index extension
                        
                        # Filter by user_id if provided
                        if user_id is not None and f"user_{user_id}_" not in namespace:
                            continue
                        namespaces.append(namespace)
            
            # Search in category subdirectories
            for category in self.CATEGORY_DIRECTORIES.values():
                category_path = os.path.join(self.storage_path, category)
                if os.path.exists(category_path):
                    for filename in os.listdir(category_path):
                        if filename.endswith(".index"):
                            namespace = filename[:-6]  # Remove .index extension
                            
                            # Filter by user_id if provided
                            if user_id is not None and f"user_{user_id}_" not in namespace:
                                continue
                            namespaces.append(namespace)
            
            # Prioritize financial namespaces for financial queries
            if is_financial:
                financial_namespaces = [ns for ns in namespaces if 'financial' in ns.lower()]
                other_namespaces = [ns for ns in namespaces if 'financial' not in ns.lower()]
                namespaces = financial_namespaces + other_namespaces
            
            # Filter by document_id if provided (applies to all namespaces)
            if document_id is not None:
                engine = create_engine(settings.DATABASE_URL)
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                db = SessionLocal()
                try:
                    document = db.query(DBDocument).filter(DBDocument.id == document_id).first()
                    if document:
                        # Only keep the namespace that matches this document
                        namespaces = [ns for ns in namespaces if ns == document.vector_namespace]
                finally:
                    db.close()
            
            
            if not namespaces:
                logger.warning(f"No namespaces found for user_id: {user_id}, document_id: {document_id}")
                return []
            
            # Search each namespace
            all_results = []
            
            for namespace in namespaces:
                namespace_results = await self._search_namespace(
                    query, namespace, embedding_service, top_k, metadata_filter
                )
                all_results.extend(namespace_results)
            
            # Apply financial entity filtering if this is a financial query
            if is_financial and financial_entities:
                all_results = self._filter_financial_results(all_results, financial_entities)
            
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


# Convenience functions for backward compatibility
async def search_similar_chunks(query: str, user_id: int, document_id: Optional[int] = None, 
                               top_k: int = 10, metadata_filter: dict = None) -> List[Dict[str, Any]]:
    """Convenience function for searching similar chunks"""
    from app.services.embedding_service import get_embedding_service
    
    service = get_vector_store_service()
    embedding_service = get_embedding_service()
    
    return await service.search_similar_chunks(
        query=query,
        embedding_service=embedding_service,
        user_id=user_id,
        document_id=document_id,
        top_k=top_k,
        metadata_filter=metadata_filter
    )


def check_query_type(query: str) -> tuple[bool, bool, bool, bool, list]:
    """Convenience function for checking query type (backward compatibility)"""
    # Simple keyword-based classification
    query_lower = query.lower()
    
    # Check for different query types
    vacation_keywords = ['vacation', 'travel', 'trip', 'holiday', 'thailand', 'phuket', 'bangkok']
    skills_keywords = ['skill', 'technical', 'programming', 'experience', 'competency', 'expertise']
    expense_keywords = ['expense', 'cost', 'money', 'dollar', '$', 'spent', 'paid', 'budget']
    prompt_keywords = ['prompt', 'engineering', 'llm', 'ai', 'gpt', 'language model']
    
    is_vacation_query = any(keyword in query_lower for keyword in vacation_keywords)
    is_skills_query = any(keyword in query_lower for keyword in skills_keywords)
    is_expense_query = any(keyword in query_lower for keyword in expense_keywords)
    is_prompt_engineering_query = any(keyword in query_lower for keyword in prompt_keywords)
    
    # Extract years (simple regex)
    import re
    years = re.findall(r'\b(19|20)\d{2}\b', query)
    
    return is_vacation_query, is_skills_query, is_expense_query, is_prompt_engineering_query, years


class VectorStoreManager:
    """Compatibility wrapper class for email processor"""
    
    def __init__(self):
        self.service = get_vector_store_service()
        self.embedding_service = None
    
    def _get_embedding_service(self):
        """Get embedding service instance"""
        if self.embedding_service is None:
            from app.services.embedding_service import get_embedding_service
            self.embedding_service = get_embedding_service()
        return self.embedding_service
    
    def store_email_vectors(
        self,
        user_id: int,
        email_id: int,
        email_type: str,
        chunks: List[Dict[str, Any]],
        namespace: str
    ) -> bool:
        """
        Store email vectors in the vector database
        
        Args:
            user_id: User ID
            email_id: Email ID
            email_type: Email type (business, personal, etc.)
            chunks: List of email chunks with content and metadata
            namespace: Vector namespace for the email
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from langchain_core.documents import Document
            
            # Convert chunks to Document objects
            documents = []
            for chunk in chunks:
                content = chunk.get("content", "")
                metadata = chunk.get("metadata", {})
                
                # Add email-specific metadata
                metadata.update({
                    "email_id": email_id,
                    "email_type": email_type,
                    "user_id": user_id,
                    "chunk_index": chunk.get("chunk_index", 0),
                    "content_type": "email"
                })
                
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            
            if not documents:
                logger.warning(f"No documents to store for email {email_id}")
                return False
            
            # Store in vector database using async method
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Use email type as document type for proper categorization
            chunks_added = loop.run_until_complete(
                self.service.add_documents(
                    documents=documents,
                    namespace=namespace,
                    embedding_service=self._get_embedding_service(),
                    document_type=f"email_{email_type}"
                )
            )
            
            logger.info(f"Stored {chunks_added} email chunks for email {email_id}")
            return chunks_added > 0
            
        except Exception as e:
            logger.error(f"Error storing email vectors for email {email_id}: {e}")
            return False
    
    def search_emails(
        self,
        user_id: int,
        query: str,
        email_type: Optional[str] = None,
        sender_email: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search emails using vector similarity
        
        Args:
            user_id: User ID to filter by
            query: Search query
            email_type: Optional email type filter
            sender_email: Optional sender email filter
            date_from: Optional start date filter
            date_to: Optional end date filter
            limit: Maximum number of results
            
        Returns:
            List of search results with email_id and score
        """
        try:
            # Build metadata filter
            metadata_filter = {"user_id": user_id, "content_type": "email"}
            
            if email_type:
                metadata_filter["email_type"] = email_type
            
            if sender_email:
                metadata_filter["sender"] = sender_email
            
            # Search using the vector store service
            import asyncio
            loop = asyncio.get_event_loop()
            
            results = loop.run_until_complete(
                self.service.search_similar_chunks(
                    query=query,
                    embedding_service=self._get_embedding_service(),
                    user_id=user_id,
                    top_k=limit * 2,  # Get more results to filter
                    metadata_filter=metadata_filter
                )
            )
            
            # Process results and extract email information
            email_results = []
            seen_emails = set()
            
            for result in results:
                metadata = result.get("metadata", {})
                email_id = metadata.get("email_id")
                
                if email_id and email_id not in seen_emails:
                    # Apply additional filters
                    if date_from or date_to:
                        sent_at_str = metadata.get("sent_at")
                        if sent_at_str:
                            try:
                                from datetime import datetime
                                sent_at = datetime.fromisoformat(sent_at_str.replace('Z', '+00:00'))
                                
                                if date_from and sent_at < date_from:
                                    continue
                                if date_to and sent_at > date_to:
                                    continue
                            except Exception as e:
                                logger.warning(f"Error parsing date {sent_at_str}: {e}")
                                continue
                    
                    email_results.append({
                        "email_id": email_id,
                        "score": result.get("score", 0.0),
                        "content": result.get("content", ""),
                        "metadata": metadata
                    })
                    seen_emails.add(email_id)
                    
                    if len(email_results) >= limit:
                        break
            
            logger.info(f"Found {len(email_results)} email results for query: {query}")
            return email_results
            
        except Exception as e:
            logger.error(f"Error searching emails for user {user_id}: {e}")
            return []


# Global instance for backward compatibility
_default_vector_store_manager: Optional[VectorStoreManager] = None


def get_vector_store_manager() -> VectorStoreManager:
    """Get the default vector store manager instance"""
    global _default_vector_store_manager
    
    if _default_vector_store_manager is None:
        _default_vector_store_manager = VectorStoreManager()
    
    return _default_vector_store_manager