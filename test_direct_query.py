#!/usr/bin/env python3
"""
Direct test of query functionality bypassing API authentication
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
from app.services.vector_store_service import search_similar_chunks
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_combined_search():
    """Test the combined document + email search as done in the API"""
    logger.info("=== Testing Combined Search (Documents + Emails) ===")
    
    try:
        # Get user ID (gmail_tester user)
        db = next(get_db())
        user = db.query(User).filter(User.username == 'gmail_tester').first()
        if not user:
            logger.error("Could not find gmail_tester user")
            return False
        
        user_id = user.id
        logger.info(f"Testing with user ID: {user_id} (username: {user.username})")
        
        # Test query
        query = "check the email how much was the Apple invoice?"
        logger.info(f"Testing query: '{query}'")
        
        # Search documents first
        document_chunks = await search_similar_chunks(
            query,
            user_id=user_id,
            document_id=None
        )
        logger.info(f"Found {len(document_chunks)} document chunks")
        
        # Search emails
        email_store = EmailStore()
        embedding_service = SentenceTransformerEmbeddingService()
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(query)
        
        # Search emails (same as API code)
        email_results = await email_store.search_emails(
            query_embedding=query_embedding,
            user_id=user_id,
            k=10
        )
        logger.info(f"Found {len(email_results)} email results")
        
        # Convert email results to chunks format (like in API)
        email_chunks = []
        for result in email_results:
            metadata = result.get('metadata', {})
            subject = metadata.get('subject', 'No Subject')
            sender = metadata.get('sender', 'Unknown Sender')
            email_content = f"[EMAIL from {sender}] Subject: {subject}\nContent: {result.get('text', '')}"
            
            # Create chunk dictionary with proper format for LLM
            email_chunk = {
                'text': email_content,
                'score': result.get('score', 0.0),
                'metadata': {
                    'content_type': 'email',
                    'email_id': metadata.get('email_id', ''),
                    'subject': subject,
                    'sender': sender,
                    'sender_email': metadata.get('sender', ''),
                    'date': metadata.get('date', ''),
                    'classification_tags': metadata.get('classification_tags', [])
                },
                'namespace': f"user_{user_id}_email_{metadata.get('email_id', '')}"
            }
            email_chunks.append(email_chunk)
        
        # Combine chunks
        chunks = document_chunks + email_chunks
        logger.info(f"Combined search: {len(document_chunks)} document chunks + {len(email_chunks)} email chunks = {len(chunks)} total")
        
        # Show some email results
        if email_results:
            logger.info("Top email results:")
            for i, result in enumerate(email_results[:3]):
                logger.info(f"Email {i+1}:")
                logger.info(f"  Score: {result.get('score', 0):.3f}")
                logger.info(f"  Text: {result.get('text', '')[:200]}...")
                metadata = result.get('metadata', {})
                logger.info(f"  Subject: {metadata.get('subject', 'No Subject')}")
                logger.info(f"  Sender: {metadata.get('sender', 'Unknown')}")
                logger.info(f"  Date: {metadata.get('date', 'Unknown')}")
        
        # Test LLM generation if chunks found
        if chunks:
            logger.info("Testing LLM generation with chunks...")
            from app.utils.llm import generate_answer
            
            try:
                answer, from_cache = await generate_answer(query, chunks)
                logger.info(f"Generated answer: {answer[:300]}...")
                logger.info(f"From cache: {from_cache}")
                
                # Check if it's the "prompt engineering" error
                if "prompt engineering" in answer.lower():
                    logger.error("❌ Got 'prompt engineering' error in answer")
                    return False
                else:
                    logger.info("✅ Got valid answer without prompt engineering error")
                    return True
                    
            except Exception as e:
                logger.error(f"Error generating answer: {e}")
                return False
        else:
            logger.warning("No chunks found, cannot test LLM generation")
            return False
            
    except Exception as e:
        logger.error(f"Error in combined search test: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

async def main():
    """Run the direct query test"""
    logger.info("Starting direct query test...")
    
    success = await test_combined_search()
    
    if success:
        logger.info("✅ Direct query test PASSED")
    else:
        logger.error("❌ Direct query test FAILED")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())