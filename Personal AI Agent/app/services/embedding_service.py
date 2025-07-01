"""
Embedding service for generating text embeddings
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.constants import EMBEDDING_MODEL_FALLBACK, EMBEDDING_BATCH_SIZE_DEFAULT, EMBEDDING_NORMALIZE
from app.core.exceptions import EmbeddingGenerationError, ModelLoadError

logger = logging.getLogger("personal_ai_agent")


class EmbeddingService(ABC):
    """Abstract base class for embedding services"""
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the embedding dimension"""
        pass


class SentenceTransformerEmbeddingService(EmbeddingService):
    """Sentence Transformer based embedding service"""
    
    def __init__(
        self,
        model_name: str = None,
        batch_size: int = None,
        normalize_embeddings: bool = None
    ):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        self.normalize_embeddings = normalize_embeddings if normalize_embeddings is not None else EMBEDDING_NORMALIZE
        self._model: Optional[SentenceTransformer] = None
        self._dimension: Optional[int] = None
    
    def _load_model(self) -> SentenceTransformer:
        """Load the embedding model lazily"""
        if self._model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Embedding model loaded successfully, dimension: {self._dimension}")
            except Exception as e:
                logger.error(f"Failed to load primary embedding model: {e}")
                try:
                    # Fallback to a smaller model
                    logger.info(f"Trying fallback model: {EMBEDDING_MODEL_FALLBACK}")
                    self._model = SentenceTransformer(EMBEDDING_MODEL_FALLBACK)
                    self._dimension = self._model.get_sentence_embedding_dimension()
                    logger.info(f"Fallback model loaded successfully, dimension: {self._dimension}")
                except Exception as fallback_error:
                    raise ModelLoadError(
                        f"Failed to load both primary and fallback embedding models",
                        details=f"Primary error: {e}, Fallback error: {fallback_error}"
                    )
        
        return self._model
    
    def get_dimension(self) -> int:
        """Get the embedding dimension"""
        if self._dimension is None:
            self._load_model()  # This will set the dimension
        return self._dimension
    
    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts in batches
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            Numpy array of embeddings
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        if not texts:
            logger.warning("Empty texts list provided to generate_embeddings")
            return np.array([])
        
        try:
            model = self._load_model()
            
            logger.debug(f"Generating embeddings for {len(texts)} texts in batches of {self.batch_size}")
            
            # Process in batches for better memory management
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                logger.debug(f"Processing batch {i // self.batch_size + 1} with {len(batch)} texts")
                
                try:
                    batch_embeddings = model.encode(
                        batch,
                        normalize_embeddings=self.normalize_embeddings,
                        show_progress_bar=False
                    )
                    all_embeddings.append(batch_embeddings)
                except Exception as batch_error:
                    logger.error(f"Error processing batch {i // self.batch_size + 1}: {batch_error}")
                    raise EmbeddingGenerationError(
                        f"Failed to generate embeddings for batch {i // self.batch_size + 1}",
                        details=str(batch_error)
                    )
            
            # Combine all batch results
            embeddings = np.vstack(all_embeddings) if len(all_embeddings) > 1 else all_embeddings[0]
            logger.debug(f"Successfully generated embeddings with shape {embeddings.shape}")
            
            return embeddings
            
        except EmbeddingGenerationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating embeddings: {e}")
            raise EmbeddingGenerationError(
                "Unexpected error during embedding generation",
                details=str(e)
            )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: The text to generate embedding for
            
        Returns:
            The embedding as a list of floats
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        if not text:
            logger.warning("Empty text provided for embedding generation")
            # Return zero vector of correct dimension
            dimension = self.get_dimension()
            return np.zeros(dimension).tolist()
        
        try:
            model = self._load_model()
            embedding = model.encode(
                text,
                normalize_embeddings=self.normalize_embeddings,
                show_progress_bar=False
            )
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating single embedding: {e}")
            raise EmbeddingGenerationError(
                "Failed to generate embedding for single text",
                details=str(e)
            )


# Global instance for backward compatibility (will be replaced with DI)
_default_embedding_service: Optional[SentenceTransformerEmbeddingService] = None


def get_embedding_service() -> SentenceTransformerEmbeddingService:
    """Get the default embedding service instance"""
    global _default_embedding_service
    
    if _default_embedding_service is None:
        _default_embedding_service = SentenceTransformerEmbeddingService()
    
    return _default_embedding_service


# Backward compatibility functions
async def generate_embeddings(texts: List[str], batch_size: int = None) -> np.ndarray:
    """Generate embeddings for a list of texts (backward compatibility)"""
    service = get_embedding_service()
    if batch_size is not None:
        service.batch_size = batch_size
    return await service.generate_embeddings(texts)


async def generate_embedding(text: str, model=None) -> List[float]:
    """Generate embedding for a single text (backward compatibility)"""
    service = get_embedding_service()
    return await service.generate_embedding(text)


def get_embedding_model():
    """Get the embedding model (backward compatibility)"""
    service = get_embedding_service()
    return service._load_model()