#!/usr/bin/env python3
"""
Debug script to see exactly what chunks are being returned for Istanbul query
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store_service import get_vector_store_service
from app.services.embedding_service import get_embedding_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_chunks():
    """Show all chunks in detail for Istanbul query"""
    
    query = "how much money did I spend in Istanbul?"
    user_id = 7
    
    print(f"=== CHUNK ANALYSIS FOR ISTANBUL QUERY ===")
    print(f"Query: '{query}'")
    
    vector_store_service = get_vector_store_service()
    embedding_service = get_embedding_service()
    
    chunks = await vector_store_service.search_similar_chunks(
        query=query,
        embedding_service=embedding_service,
        user_id=user_id,
        top_k=10
    )
    
    print(f"\nFound {len(chunks)} chunks:")
    
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} ---")
        print(f"Score: {chunk.get('score', 'N/A')}")
        print(f"Namespace: {chunk.get('namespace', 'N/A')}")
        print(f"Content: {chunk.get('content', '')}")
        print("---")
    
    # Let's see if we can find the bank statement specifically
    print(f"\n=== LOOKING FOR BANK STATEMENT CHUNKS ===")
    bank_chunks = [chunk for chunk in chunks if "June_2024_Statement" in chunk.get('namespace', '')]
    
    print(f"Found {len(bank_chunks)} bank statement chunks:")
    for i, chunk in enumerate(bank_chunks):
        print(f"\nBank Chunk {i+1}:")
        print(f"Score: {chunk.get('score', 'N/A')}")
        print(f"Content: {chunk.get('content', '')}")

if __name__ == "__main__":
    asyncio.run(debug_chunks())