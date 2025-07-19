#!/usr/bin/env python3
"""
Test script to explicitly load the Mistral model and test Istanbul query
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.llm import get_llm, reset_llm, generate_response
from app.services.vector_store_service import get_vector_store_service
from app.services.embedding_service import get_embedding_service
from app.utils.llm import generate_answer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mistral_model():
    """Test with explicit Mistral model"""
    
    print("=== TESTING MISTRAL MODEL ===")
    
    # Reset the current model
    reset_llm()
    
    # Force load Mistral model
    try:
        llm = get_llm("mistral-7b")
        print("Mistral model loaded successfully")
    except Exception as e:
        print(f"Error loading Mistral model: {e}")
        return
    
    # Test simple response with Mistral
    print("\n=== SIMPLE MISTRAL RESPONSE TEST ===")
    
    simple_context = [
        "Transaction: 05/17 Foreign Exch Rt ADJ Fee 05/16 Unifree Ist 8107 / M Istanbul Card 6822 6.35"
    ]
    
    query = "How much did I spend on Istanbul Card?"
    
    try:
        response = generate_response(query, simple_context, model_name="mistral-7b")
        print(f"Query: {query}")
        print(f"Response: {response}")
        print(f"Response length: {len(response)}")
    except Exception as e:
        print(f"Error generating response: {e}")
        import traceback
        traceback.print_exc()
    
    # Now test full pipeline with vector search and Mistral
    print("\n=== FULL PIPELINE WITH MISTRAL ===")
    
    user_id = 6
    vector_store_service = get_vector_store_service()
    embedding_service = get_embedding_service()
    
    chunks = await vector_store_service.search_similar_chunks(
        query=query,
        embedding_service=embedding_service,
        user_id=user_id,
        top_k=3
    )
    
    print(f"Found {len(chunks)} chunks")
    
    if chunks:
        print(f"Best chunk: {chunks[0].get('content', '')[:100]}...")
        
        try:
            full_response, from_cache = await generate_answer(query, chunks)
            print(f"Full pipeline response: {full_response}")
        except Exception as e:
            print(f"Error in full pipeline: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mistral_model())