"""
Email vector storage service for managing email embeddings in FAISS.
Extends existing vector store with email-specific organization and search.
"""

import os
import pickle
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
import faiss
import numpy as np
from datetime import datetime, timedelta

from app.core.config import settings
from app.services.vector_store_service import FAISSVectorStoreService
from app.exceptions import VectorStoreError, EmailProcessingError, handle_database_error

logger = logging.getLogger(__name__)


class EmailStore:
    """Vector storage service specifically for email content."""
    
    def __init__(self):
        self.vector_store_service = FAISSVectorStoreService()
        self.base_path = Path(settings.VECTOR_DB_PATH) / "emails"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Email-specific search parameters
        self.search_configs = {
            'default': {
                'k': 10,
                'score_threshold': 0.7
            },
            'recent': {  # Recent emails get higher relevance
                'k': 15,
                'score_threshold': 0.6,
                'temporal_boost': 0.1
            },
            'temporal': {  # Time-based searches
                'k': 20,
                'score_threshold': 0.5,
                'temporal_boost': 0.2
            }
        }
    
    def store_email_chunks(self, chunks: List[Dict], user_id: int, email_id: str) -> bool:
        """
        Store email chunks in vector database.
        
        Args:
            chunks: List of processed chunks with embeddings and metadata
            user_id: User ID for namespace
            email_id: Unique email identifier
            
        Returns:
            Success status
        """
        try:
            if not chunks:
                logger.warning(f"No chunks to store for email {email_id}")
                return False
            
            # Create namespace for this email
            namespace = f"user_{user_id}_email_{email_id}"
            index_path = self.base_path / f"{namespace}.index"
            metadata_path = self.base_path / f"{namespace}.pkl"
            
            # Prepare vectors and metadata
            vectors = []
            metadata_list = []
            
            for chunk in chunks:
                vectors.append(chunk['embedding'])
                metadata_list.append(chunk['metadata'])
            
            # Convert to numpy array
            vectors_array = np.array(vectors).astype('float32')
            
            # Create FAISS index
            dimension = vectors_array.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
            
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(vectors_array)
            
            # Add vectors to index
            index.add(vectors_array)
            
            # Save index and metadata
            faiss.write_index(index, str(index_path))
            
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata_list, f)
            
            logger.info(f"Stored {len(chunks)} chunks for email {email_id}")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Directory or file not found when storing email chunks: {e}")
            raise VectorStoreError(f"Storage path not accessible for email {email_id}", operation="store")
        except PermissionError as e:
            logger.error(f"Permission denied when storing email chunks: {e}")
            raise VectorStoreError(f"Permission denied storing email {email_id}", operation="store")
        except Exception as e:
            logger.error(f"Error storing email chunks: {e}")
            if "numpy" in str(e).lower() or "array" in str(e).lower():
                raise EmailProcessingError(f"Invalid embedding data for email {email_id}: {str(e)}", email_id)
            elif "faiss" in str(e).lower():
                raise VectorStoreError(f"FAISS index error for email {email_id}: {str(e)}", operation="store")
            else:
                raise VectorStoreError(f"Failed to store email chunks for {email_id}: {str(e)}", operation="store")
    
    def search_emails(
        self, 
        query_embedding: List[float], 
        user_id: int,
        tags: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        sender_filter: Optional[str] = None,
        k: int = 10
    ) -> List[Dict]:
        """
        Search email content using various filters.
        
        Args:
            query_embedding: Query vector
            user_id: User ID for namespace filtering
            tags: Classification tags to filter by
            date_range: Tuple of (start_date, end_date)
            sender_filter: Filter by sender domain or email
            k: Number of results to return
            
        Returns:
            List of relevant chunks with metadata and scores
        """
        try:
            results = []
            
            # Get all email indices for this user
            email_indices = self._get_user_email_indices(user_id)
            
            if not email_indices:
                logger.info(f"No email indices found for user {user_id}")
                return []
            
            # Search each email index
            for index_path, metadata_path in email_indices:
                try:
                    # Load index and metadata
                    index = faiss.read_index(str(index_path))
                    with open(metadata_path, 'rb') as f:
                        metadata_list = pickle.load(f)
                    
                    # Perform search
                    query_vector = np.array([query_embedding]).astype('float32')
                    faiss.normalize_L2(query_vector)
                    
                    scores, indices = index.search(query_vector, min(k * 2, index.ntotal))
                    
                    # Process results
                    for score, idx in zip(scores[0], indices[0]):
                        if idx == -1:  # Invalid index
                            continue
                        
                        metadata = metadata_list[idx]
                        
                        # Apply filters
                        if not self._apply_filters(metadata, tags, date_range, sender_filter):
                            continue
                        
                        # Calculate final score with temporal boost
                        final_score = self._calculate_final_score(score, metadata)
                        
                        results.append({
                            'text': metadata['chunk_text'],
                            'score': final_score,
                            'metadata': metadata
                        })
                        
                except FileNotFoundError:
                    logger.warning(f"Index file not found: {index_path}, skipping")
                    continue
                except Exception as e:
                    logger.warning(f"Error searching index {index_path}: {e}")
                    # Continue with other indices even if one fails
                    continue
            
            # Sort by score and return top k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:k]
            
        except VectorStoreError:
            # Re-raise specific vector store errors
            raise
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            if "embedding" in str(e).lower() or "vector" in str(e).lower():
                raise VectorStoreError(f"Invalid query embedding: {str(e)}", operation="search")
            else:
                raise VectorStoreError(f"Email search failed: {str(e)}", operation="search")
    
    def search_emails_by_category(
        self,
        query_embedding: List[float],
        user_id: int,
        categories: List[str],
        k: int = 10
    ) -> List[Dict]:
        """Search emails filtered by specific categories."""
        return self.search_emails(
            query_embedding=query_embedding,
            user_id=user_id,
            tags=categories,
            k=k
        )
    
    def search_recent_emails(
        self,
        query_embedding: List[float],
        user_id: int,
        days: int = 30,
        k: int = 10
    ) -> List[Dict]:
        """Search emails from the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.search_emails(
            query_embedding=query_embedding,
            user_id=user_id,
            date_range=(start_date, end_date),
            k=k
        )
    
    def search_emails_by_sender(
        self,
        query_embedding: List[float],
        user_id: int,
        sender: str,
        k: int = 10
    ) -> List[Dict]:
        """Search emails from specific sender."""
        return self.search_emails(
            query_embedding=query_embedding,
            user_id=user_id,
            sender_filter=sender,
            k=k
        )
    
    def _get_user_email_indices(self, user_id: int) -> List[Tuple[Path, Path]]:
        """Get all email indices for a user."""
        indices = []
        pattern = f"user_{user_id}_email_*"
        
        for index_file in self.base_path.glob(f"{pattern}.index"):
            metadata_file = index_file.with_suffix('.pkl')
            if metadata_file.exists():
                indices.append((index_file, metadata_file))
        
        return indices
    
    def _apply_filters(
        self,
        metadata: Dict,
        tags: Optional[List[str]],
        date_range: Optional[Tuple[datetime, datetime]],
        sender_filter: Optional[str]
    ) -> bool:
        """Apply filters to search results."""
        
        # Tag filter
        if tags:
            email_tags = metadata.get('classification_tags', [])
            if not any(tag in email_tags for tag in tags):
                return False
        
        # Date range filter
        if date_range:
            email_date_str = metadata.get('date')
            if email_date_str:
                try:
                    email_date = datetime.fromisoformat(email_date_str.replace('Z', '+00:00'))
                    if not (date_range[0] <= email_date <= date_range[1]):
                        return False
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid date format in metadata: {email_date_str}")
                    return False
            else:
                return False
        
        # Sender filter
        if sender_filter:
            sender = metadata.get('sender', '').lower()
            sender_domain = metadata.get('sender_domain', '').lower()
            
            filter_lower = sender_filter.lower()
            if not (filter_lower in sender or filter_lower in sender_domain):
                return False
        
        return True
    
    def _calculate_final_score(self, similarity_score: float, metadata: Dict) -> float:
        """Calculate final relevance score with temporal and priority boosts."""
        final_score = float(similarity_score)
        
        # Temporal boost for recent emails
        email_date_str = metadata.get('date')
        if email_date_str:
            try:
                email_date = datetime.fromisoformat(email_date_str.replace('Z', '+00:00'))
                days_ago = (datetime.now() - email_date.replace(tzinfo=None)).days
                
                # Boost recent emails
                if days_ago < 7:
                    final_score += 0.1
                elif days_ago < 30:
                    final_score += 0.05
                
            except (ValueError, TypeError):
                logger.debug(f"Invalid date format for temporal boost: {email_date_str}")
                pass
        
        # Priority boost based on classification
        tags = metadata.get('classification_tags', [])
        priority_boost = {
            'security': 0.15,
            'job_offer': 0.12,
            'financial': 0.10,
            'work': 0.08,
            'receipt': 0.05
        }
        
        for tag in tags:
            if tag in priority_boost:
                final_score += priority_boost[tag]
                break
        
        return final_score
    
    def delete_email(self, user_id: int, email_id: str) -> bool:
        """Delete email from vector store."""
        try:
            namespace = f"user_{user_id}_email_{email_id}"
            index_path = self.base_path / f"{namespace}.index"
            metadata_path = self.base_path / f"{namespace}.pkl"
            
            # Remove files if they exist
            if index_path.exists():
                index_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            
            logger.info(f"Deleted email {email_id} for user {user_id}")
            return True
            
        except FileNotFoundError:
            logger.warning(f"Email {email_id} not found for deletion (may already be deleted)")
            return True  # Consider it successful if already deleted
        except PermissionError as e:
            logger.error(f"Permission denied deleting email {email_id}: {e}")
            raise VectorStoreError(f"Permission denied deleting email {email_id}", operation="delete")
        except Exception as e:
            logger.error(f"Error deleting email: {e}")
            raise VectorStoreError(f"Failed to delete email {email_id}: {str(e)}", operation="delete")
    
    def get_email_stats(self, user_id: int) -> Dict:
        """Get statistics about stored emails for a user."""
        try:
            indices = self._get_user_email_indices(user_id)
            
            stats = {
                'total_emails': len(indices),
                'total_chunks': 0,
                'categories': {},
                'date_range': {'earliest': None, 'latest': None}
            }
            
            dates = []
            
            for index_path, metadata_path in indices:
                try:
                    with open(metadata_path, 'rb') as f:
                        metadata_list = pickle.load(f)
                    
                    stats['total_chunks'] += len(metadata_list)
                    
                    # Analyze first chunk (email metadata is same across chunks)
                    if metadata_list:
                        metadata = metadata_list[0]
                        
                        # Count categories
                        tags = metadata.get('classification_tags', [])
                        for tag in tags:
                            stats['categories'][tag] = stats['categories'].get(tag, 0) + 1
                        
                        # Collect dates
                        date_str = metadata.get('date')
                        if date_str:
                            try:
                                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                dates.append(date)
                            except (ValueError, TypeError):
                                logger.debug(f"Invalid date format in stats: {date_str}")
                                pass
                
                except FileNotFoundError:
                    logger.warning(f"Metadata file not found: {metadata_path}, skipping")
                except Exception as e:
                    logger.warning(f"Error reading metadata {metadata_path}: {e}")
            
            # Calculate date range
            if dates:
                stats['date_range']['earliest'] = min(dates).isoformat()
                stats['date_range']['latest'] = max(dates).isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            # Return empty stats rather than raising for statistics errors
            return {
                'total_emails': 0,
                'total_chunks': 0,
                'categories': {},
                'date_range': {'earliest': None, 'latest': None}
            }