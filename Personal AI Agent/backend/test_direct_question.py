#!/usr/bin/env python3
"""
Test with a more direct question about the transaction
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

async def test_direct_questions():
    """Test with more direct questions"""
    
    # Use only the bank statement chunk
    bank_chunk = {
        'content': 'investments.\n05/17 Foreign Exch Rt ADJ Fee 05/16 Unifree Ist 8107 / M Istanbul Card 6822 6.35',
        'score': 0.51,
        'namespace': 'user_6_doc_June_2024_Statement_'
    }
    
    chunks = [bank_chunk]
    
    # Test different question formats
    questions = [
        "What is the amount for the Istanbul Card transaction?",
        "How much did the Istanbul Card cost?",
        "What is the dollar amount for Istanbul Card 6822?",
        "Show me the transaction amount for Unifree Ist",
        "What was the charge for the Istanbul Card?"
    ]
    
    print(f"=== TESTING DIRECT QUESTIONS ===")
    print(f"Chunk content: {bank_chunk['content']}")
    
    for i, query in enumerate(questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"Query: '{query}'")
        
        try:
            answer, from_cache = await generate_answer(query, chunks)
            print(f"Answer: {answer}")
            
            # Check if answer contains the amount
            if "6.35" in answer:
                print("✓ FOUND the amount!")
            else:
                print("⚠ Amount not found")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_direct_questions())