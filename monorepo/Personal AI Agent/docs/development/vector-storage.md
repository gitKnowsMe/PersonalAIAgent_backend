# Vector Storage System

Understanding the FAISS-based vector storage architecture for semantic search capabilities.

## Overview

Personal AI Agent uses FAISS (Facebook AI Similarity Search) for efficient vector storage and retrieval, enabling semantic search across documents and emails.

## Architecture

### Storage Organization

```
data/vector_db/
├── financial/          # Financial documents
├── long_form/         # Long-form documents  
├── generic/           # Generic documents
└── emails/            # Email messages
```

### Index Structure

Each content item gets its own FAISS index:
- `user_{id}_doc_{filename}.index` - FAISS index file
- `user_{id}_doc_{filename}.pkl` - Metadata pickle file

## Implementation Details

### Embedding Generation

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(text_chunks)
```

### Index Creation

```python
import faiss
import numpy as np

# Create FAISS index
dimension = 384  # MiniLM embedding dimension
index = faiss.IndexFlatIP(dimension)  # Inner product similarity

# Add vectors
vectors = np.array(embeddings).astype('float32')
index.add(vectors)

# Save index
faiss.write_index(index, f"{namespace}.index")
```

### Search Implementation

```python
def search_vectors(query_vector, top_k=5):
    # Load index
    index = faiss.read_index(f"{namespace}.index")
    
    # Search
    scores, indices = index.search(query_vector, top_k)
    
    return scores, indices
```

## Performance Optimization

### Index Types

- **IndexFlatIP**: Exact search, good for smaller datasets
- **IndexIVFFlat**: Approximate search, better for large datasets
- **IndexHNSW**: Graph-based, excellent for high-dimensional data

### Memory Management

- Lazy loading of indexes
- LRU cache for frequently accessed indexes
- Batch processing for embedding generation

## User Data Isolation

Each user's vectors are stored in separate indexes with user-specific namespaces, ensuring complete data isolation and privacy.

*This is a placeholder for detailed vector storage documentation. Full implementation details would include FAISS configuration, optimization strategies, and maintenance procedures.*