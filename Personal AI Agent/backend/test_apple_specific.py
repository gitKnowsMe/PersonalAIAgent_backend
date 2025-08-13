#!/usr/bin/env python3
"""
Test specifically for Apple invoice information
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.email.email_store import EmailStore
from app.services.embedding_service import SentenceTransformerEmbeddingService
from app.db.database import get_db
from app.db.models import User
from app.utils.llm import generate_answer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_apple_invoice_specific():
    """Test specific Apple invoice query"""
    logger.info("=== Testing Apple Invoice Specific Query ===")
    
    try:
        # Get user
        db = next(get_db())
        user = db.query(User).filter(User.username == 'gmail_tester').first()
        if not user:
            logger.error("Could not find gmail_tester user")
            return False
        
        user_id = user.id
        
        # Search for Apple invoice specifically
        email_store = EmailStore()
        embedding_service = SentenceTransformerEmbeddingService()
        
        # Test specific Apple queries
        queries = [
            "how much was the Apple invoice",
            "Apple receipt cost amount price",
            "iCloud subscription cost",
            "Apple receipt July 2025"
        ]
        
        for query in queries:
            logger.info(f"\n--- Testing query: '{query}' ---")
            
            query_embedding = await embedding_service.generate_embedding(query)
            email_results = await email_store.search_emails(
                query_embedding=query_embedding,
                user_id=user_id,
                k=5
            )
            
            logger.info(f"Found {len(email_results)} email results")
            
            # Look for Apple results
            apple_results = []
            for result in email_results:
                text = result.get('text', '').lower()
                metadata = result.get('metadata', {})
                subject = metadata.get('subject', '').lower()
                
                if 'apple' in text or 'apple' in subject:
                    apple_results.append(result)
            
            logger.info(f"Found {len(apple_results)} Apple-related results")
            
            for i, result in enumerate(apple_results):
                logger.info(f"Apple result {i+1}:")
                logger.info(f"  Score: {result.get('score', 0):.3f}")
                metadata = result.get('metadata', {})
                logger.info(f"  Subject: {metadata.get('subject', 'No Subject')}")
                logger.info(f"  Sender: {metadata.get('sender', 'Unknown')}")
                logger.info(f"  Date: {metadata.get('date', 'Unknown')}")
                
                # Extract pricing information
                text = result.get('text', '')
                import re
                prices = re.findall(r'\$[\d.,]+', text)
                if prices:
                    logger.info(f"  Found prices: {prices}")
                
                # Look for specific Apple services
                if 'icloud' in text.lower():
                    logger.info("  ✓ iCloud service mentioned")
                if 'monthly' in text.lower():
                    logger.info("  ✓ Monthly subscription")
                
                logger.info(f"  Text preview: {text[:200]}...")
                logger.info("  ---")
            
            # Test LLM response for this query if we have Apple results
            if apple_results:
                logger.info(f"Testing LLM generation for query: '{query}'")
                
                # Convert to proper chunk format
                chunks = []
                for result in apple_results:
                    metadata = result.get('metadata', {})
                    subject = metadata.get('subject', 'No Subject')
                    sender = metadata.get('sender', 'Unknown Sender')
                    email_content = f"[EMAIL from {sender}] Subject: {subject}\nContent: {result.get('text', '')}"
                    
                    chunk = {
                        'text': email_content,
                        'score': result.get('score', 0.0),
                        'metadata': {
                            'content_type': 'email',
                            'subject': subject,
                            'sender': sender,
                        }
                    }
                    chunks.append(chunk)
                
                try:
                    answer, from_cache = await generate_answer(query, chunks)
                    logger.info(f"LLM Answer: {answer}")
                    logger.info(f"From cache: {from_cache}")
                    
                    # Check if answer contains useful information
                    answer_lower = answer.lower()
                    if '$9.99' in answer or 'icloud' in answer_lower or 'apple' in answer_lower:
                        logger.info("✅ Answer contains relevant Apple/price information")
                    else:
                        logger.warning("⚠️ Answer doesn't contain specific Apple/price information")
                        
                except Exception as e:
                    logger.error(f"Error generating LLM response: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in Apple invoice test: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    asyncio.run(test_apple_invoice_specific())