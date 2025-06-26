import os
import numpy as np
import logging
from typing import List, Union
from sentence_transformers import SentenceTransformer

from app.core.config import settings

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Global embedding model
_embedding_model = None

def get_embedding_model():
    """Get the embedding model (lazy loading)"""
    global _embedding_model
    
    if _embedding_model is None:
        try:
            # Try to load the model directly from Hugging Face
            logger.info(f"Loading embedding model from Hugging Face: sentence-transformers/all-MiniLM-L6-v2")
            
            try:
                _embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                logger.info("Embedding model loaded successfully from Hugging Face")
            except Exception as model_error:
                # If that fails, try a more minimal model
                logger.warning(f"Failed to load primary embedding model: {str(model_error)}. Trying minimal model.")
                _embedding_model = SentenceTransformer("paraphrase-MiniLM-L3-v2")
                logger.info("Minimal embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    return _embedding_model

def generate_embeddings(texts: List[str], batch_size: int = 8) -> np.ndarray:
    """
    Generate embeddings for a list of texts in batches for better performance
    
    Args:
        texts: List of texts to generate embeddings for
        batch_size: Number of texts to process in each batch
        
    Returns:
        Numpy array of embeddings
    """
    if not texts:
        logger.warning("Empty texts list provided to generate_embeddings")
        return np.array([])
    
    try:
        # Get the embedding model
        model = get_embedding_model()
        
        # Generate embeddings in batches
        logger.debug(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")
        
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1} with {len(batch)} texts")
            batch_embeddings = model.encode(batch, normalize_embeddings=True)
            all_embeddings.append(batch_embeddings)
            
        # Combine all batch results
        embeddings = np.vstack(all_embeddings) if len(all_embeddings) > 1 else all_embeddings[0]
        logger.debug(f"Successfully generated embeddings with shape {embeddings.shape}")
        
        return embeddings
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        # Return a default embedding of the correct dimension instead of raising
        # This allows the application to continue working even if embedding fails
        try:
            # Try to get the model to determine dimension
            model = get_embedding_model()
            # Create a zero embedding with the correct dimension
            dim = model.get_sentence_embedding_dimension()
            logger.info(f"Using fallback zero embeddings with dimension {dim}")
            # Return one zero embedding per text
            return np.zeros((len(texts), dim), dtype=np.float32)
        except Exception as inner_e:
            logger.error(f"Failed to create default embeddings: {str(inner_e)}")
            # If all else fails, return a small default embedding
            logger.info("Using hardcoded fallback embeddings with dimension 384")
            return np.zeros((len(texts), 384), dtype=np.float32) 