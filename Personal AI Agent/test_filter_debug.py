#!/usr/bin/env python3
"""
Debug the financial filter to see why it's not finding Apple invoice
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
from app.utils.response_filter import financial_filter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_financial_filter():
    """Debug why the financial filter isn't working for Apple invoice"""
    logger.info("=== Debugging Financial Filter ===")
    
    try:
        # Get user
        db = next(get_db())
        user = db.query(User).filter(User.username == 'gmail_tester').first()
        if not user:
            logger.error("Could not find gmail_tester user")
            return False
        
        user_id = user.id
        
        # Search for Apple invoice
        email_store = EmailStore()
        embedding_service = SentenceTransformerEmbeddingService()
        
        query = "how much was the Apple invoice"
        logger.info(f"Testing query: '{query}'")
        
        query_embedding = await embedding_service.generate_embedding(query)
        email_results = await email_store.search_emails(
            query_embedding=query_embedding,
            user_id=user_id,
            k=3
        )
        
        logger.info(f"Found {len(email_results)} email results")
        
        # Convert to context chunks format
        context_chunks = []
        for result in email_results:
            metadata = result.get('metadata', {})
            subject = metadata.get('subject', 'No Subject')
            sender = metadata.get('sender', 'Unknown Sender')
            email_content = f"[EMAIL from {sender}] Subject: {subject}\nContent: {result.get('text', '')}"
            context_chunks.append(email_content)
        
        # Debug the filter
        logger.info("\n=== Context Chunks ===")
        for i, chunk in enumerate(context_chunks):
            logger.info(f"Chunk {i+1}: {chunk[:500]}...")
        
        # Test the financial filter
        logger.info("\n=== Testing Financial Filter ===")
        mock_response = "Based on the Apple invoice, you were charged $9.99 for iCloud+ subscription."
        
        filtered_response = financial_filter.filter_financial_response(
            query, mock_response, context_chunks
        )
        
        logger.info(f"Original response: {mock_response}")
        logger.info(f"Filtered response: {filtered_response}")
        
        # Test the smart response generation directly
        logger.info("\n=== Testing Smart Response Generation ===")
        smart_response = financial_filter._generate_safe_financial_response(
            query, context_chunks, None
        )
        logger.info(f"Smart response: {smart_response}")
        
        # Debug entity extraction
        logger.info("\n=== Entity Extraction Debug ===")
        entities = financial_filter.validator._extract_entities(query)
        logger.info(f"Query entities: {entities}")
        
        # Debug search terms
        import re
        query_words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
        potential_keywords = [word for word in query_words if len(word) > 3 and word not in 
                            {'much', 'paid', 'send', 'sent', 'money', 'amount', 'cost', 'spent', 'with', 'from', 'this', 'that', 'what', 'when', 'where', 'have', 'does'}]
        logger.info(f"Potential keywords: {potential_keywords}")
        
        # Check if 'apple' is found in context
        for i, chunk in enumerate(context_chunks):
            if 'apple' in chunk.lower():
                logger.info(f"Found 'apple' in chunk {i+1}")
                # Extract amounts from this chunk
                amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', chunk)
                logger.info(f"Amounts found in this chunk: {amounts}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in filter debug: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    asyncio.run(debug_financial_filter())