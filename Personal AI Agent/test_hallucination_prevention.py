#!/usr/bin/env python3
"""
Test script for hallucination prevention system
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.vector_store_service import get_vector_store_service
from app.services.embedding_service import get_embedding_service
from app.utils.llm import generate_answer
from app.utils.response_filter import financial_filter, response_validator, ValidationResult


async def test_hallucination_prevention():
    """Test the hallucination prevention system with the problematic query"""
    
    print("=== Testing Hallucination Prevention System ===\n")
    
    # Initialize services
    vector_store_service = get_vector_store_service()
    embedding_service = get_embedding_service()
    
    # Test query that previously caused hallucinations
    test_query = "How much did I send to Andy Eckman via Zelle in June 2024?"
    user_id = 7  # Admin user who has the financial documents
    
    print(f"Test Query: {test_query}")
    print(f"User ID: {user_id}")
    print("-" * 50)
    
    # Step 1: Search for relevant chunks
    print("Step 1: Searching for relevant chunks...")
    try:
        chunks = await vector_store_service.search_similar_chunks(
            query=test_query,
            embedding_service=embedding_service,
            user_id=user_id,
            top_k=5
        )
        print(f"Found {len(chunks)} chunks")
        
        if chunks:
            print("Top chunk content preview:")
            top_chunk = chunks[0]
            print(f"Score: {top_chunk.get('score', 'N/A')}")
            print(f"Content: {top_chunk.get('content', '')[:200]}...")
        else:
            print("No chunks found!")
            return
            
    except Exception as e:
        print(f"Error searching chunks: {e}")
        return
    
    print("\n" + "="*50)
    
    # Step 2: Generate response with LLM
    print("Step 2: Generating LLM response...")
    try:
        response, from_cache = await generate_answer(test_query, chunks)
        print(f"Response: {response}")
        print(f"From cache: {from_cache}")
        
    except Exception as e:
        print(f"Error generating response: {e}")
        return
    
    print("\n" + "="*50)
    
    # Step 3: Test response validation
    print("Step 3: Testing response validation...")
    try:
        # Extract content from chunks for validation
        context_content = [chunk.get('content', '') for chunk in chunks]
        
        # Validate the response
        validation_result = response_validator.validate_response(response, test_query, context_content)
        
        print(f"Validation Result:")
        print(f"  Is Valid: {validation_result.is_valid}")
        print(f"  Confidence: {validation_result.confidence:.2f}")
        print(f"  Issues Found: {len(validation_result.issues)}")
        
        if validation_result.issues:
            print("  Issues:")
            for issue in validation_result.issues:
                print(f"    - {issue}")
        
        if validation_result.suggested_corrections:
            print("  Suggested Corrections:")
            for correction in validation_result.suggested_corrections:
                print(f"    - {correction}")
                
    except Exception as e:
        print(f"Error during validation: {e}")
    
    print("\n" + "="*50)
    
    # Step 4: Test financial response filtering
    print("Step 4: Testing financial response filtering...")
    try:
        filtered_response = financial_filter.filter_financial_response(test_query, response, context_content)
        
        if filtered_response != response:
            print(f"Original Response: {response}")
            print(f"Filtered Response: {filtered_response}")
            print("✅ Financial filter applied changes")
        else:
            print(f"Response: {response}")
            print("✅ No changes needed by financial filter")
            
    except Exception as e:
        print(f"Error during financial filtering: {e}")
    
    print("\n" + "="*50)
    
    # Step 5: Test entity extraction
    print("Step 5: Testing entity extraction...")
    try:
        from app.utils.response_filter import ResponseValidator
        
        validator = ResponseValidator()
        
        # Extract entities from query
        query_entities = validator._extract_entities(test_query)
        print(f"Query Entities: {query_entities}")
        
        # Extract entities from response
        response_entities = validator._extract_entities(response)
        print(f"Response Entities: {response_entities}")
        
        # Extract entities from context
        context_text = ' '.join(context_content)
        context_entities = validator._extract_entities(context_text)
        print(f"Context Entities (first 10): {context_entities[:10]}")
        
    except Exception as e:
        print(f"Error during entity extraction: {e}")
    
    print("\n" + "="*50)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_hallucination_prevention()) 