"""
Embedding utilities - backward compatibility layer
This module now delegates to the new EmbeddingService for better architecture
"""

import logging
from typing import List
import numpy as np

from app.services.embedding_service import (
    get_embedding_service,
    generate_embeddings as _generate_embeddings,
    generate_embedding as _generate_embedding,
    get_embedding_model as _get_embedding_model
)

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Backward compatibility functions
def get_embedding_model():
    """Get the embedding model (backward compatibility)"""
    return _get_embedding_model()

def generate_embeddings(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """Generate embeddings for a list of texts (backward compatibility)"""
    import asyncio
    return asyncio.run(_generate_embeddings(texts, batch_size))

async def generate_embedding(text: str, model=None) -> List[float]:
    """Generate embedding for a single text (backward compatibility)"""
    return await _generate_embedding(text) 