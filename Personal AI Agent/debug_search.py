#!/usr/bin/env python3

import asyncio
import sys
sys.path.append('.')

from app.utils.vector_store import search_similar_chunks

async def test_search():
    """Test the vector search to see what chunks are retrieved for March 2023 query"""
    
    query = "what were my total expenses for March 2023?"
    print(f"Testing query: {query}")
    print("="*50)
    
    try:
        # Search for similar chunks
        chunks = await search_similar_chunks(query, user_id=1, top_k=5)
        
        print(f"Found {len(chunks)} chunks:")
        print("-"*30)
        
        for i, chunk in enumerate(chunks):
            if hasattr(chunk, 'page_content'):
                content = chunk.page_content
                metadata = chunk.metadata
            else:
                content = chunk.get("content", "No content")
                metadata = chunk.get("metadata", {})
            
            print(f"\nChunk {i+1}:")
            print(f"Source: {metadata.get('source', 'Unknown')}")
            print(f"Namespace: {metadata.get('namespace', 'Unknown')}")
            print(f"Content preview: {content[:200]}...")
            
            # Check if this chunk contains March 2023
            if "March 2023" in content:
                print("*** THIS CHUNK CONTAINS MARCH 2023 DATA ***")
                print(f"Full content: {content}")
            
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search()) 