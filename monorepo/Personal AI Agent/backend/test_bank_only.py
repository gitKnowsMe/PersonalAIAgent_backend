#!/usr/bin/env python3
"""
Test the Istanbul query with only bank statement data
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.llm import generate_answer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bank_only():
    """Test with only the bank statement chunk"""
    
    query = "how much money did I spend in Istanbul?"
    
    # Use only the bank statement chunk
    bank_chunk = {
        'content': 'investments.\n05/17 Foreign Exch Rt ADJ Fee 05/16 Unifree Ist 8107 / M Istanbul Card 6822 6.35',
        'score': 0.51,
        'namespace': 'user_6_doc_June_2024_Statement_'
    }
    
    chunks = [bank_chunk]
    
    print(f"=== TESTING WITH BANK STATEMENT ONLY ===")
    print(f"Query: '{query}'")
    print(f"Chunk content: {bank_chunk['content']}")
    
    try:
        answer, from_cache = await generate_answer(query, chunks)
        print(f"\nSUCCESS!")
        print(f"Answer: {answer}")
        print(f"From cache: {from_cache}")
        
        # Check if answer contains the amount
        if "6.35" in answer:
            print("✓ Answer contains the Istanbul Card amount!")
        else:
            print("⚠ Answer doesn't contain the expected amount")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bank_only())