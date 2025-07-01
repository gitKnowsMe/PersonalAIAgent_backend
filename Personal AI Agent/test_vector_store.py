#!/usr/bin/env python3
"""
Test script to directly check the vector store
"""
import os
import sys
import asyncio
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.utils.embeddings import get_embedding_model, generate_embedding

async def test_vector_store(query: str, namespace: str):
    """
    Test the vector store by searching for a query in a namespace
    """
    print(f"Testing vector store for query: '{query}' in namespace: {namespace}")
    
    # Get embedding model
    print("Loading embedding model...")
    embedding_model = get_embedding_model()
    
    # Generate query embedding
    print("Generating query embedding...")
    query_embedding = await generate_embedding(query, embedding_model)
    
    # Load index
    index_path = os.path.join(settings.VECTOR_DB_PATH, f"{namespace}.index")
    if not os.path.exists(index_path):
        print(f"Index file not found: {index_path}")
        return
        
    # Load document map
    document_map_path = os.path.join(settings.VECTOR_DB_PATH, f"{namespace}.pkl")
    if not os.path.exists(document_map_path):
        print(f"Document map file not found: {document_map_path}")
        return
    
    # Load index and document map
    print("Loading index and document map...")
    index = faiss.read_index(index_path)
    with open(document_map_path, "rb") as f:
        document_map = pickle.load(f)
    
    # Search index
    print(f"Searching index with {index.ntotal} vectors...")
    D, I = index.search(np.array([query_embedding]), min(20, index.ntotal))
    
    # Get results
    print(f"Found {len(I[0])} results:")
    for i, (dist, idx) in enumerate(zip(D[0], I[0])):
        if idx < 0 or idx >= len(document_map):
            continue
            
        # Get document
        document = document_map[idx]
        
        # Calculate score (convert distance to similarity score)
        score = 1.0 - min(max(0.0, dist), 1.0)
        
        # Print result
        print(f"\nResult {i+1}: score={score:.2f}")
        
        # Handle different document formats
        if hasattr(document, 'page_content'):
            content = document.page_content
            metadata = document.metadata
        elif isinstance(document, dict):
            content = document.get('content', '')
            metadata = document.get('metadata', {})
        else:
            content = str(document)
            metadata = {}
        
        print(f"Content: {content[:200]}...")
        print(f"Metadata: {metadata}")
        
        # Check if content contains "prompt engineering"
        if "prompt engineering" in content.lower():
            print("*** CONTAINS 'prompt engineering' ***")

async def main():
    """
    Main function
    """
    # Check command line arguments
    if len(sys.argv) < 3:
        print("Usage: python test_vector_store.py <query> <namespace>")
        return
    
    query = sys.argv[1]
    namespace = sys.argv[2]
    
    await test_vector_store(query, namespace)

if __name__ == "__main__":
    asyncio.run(main()) 