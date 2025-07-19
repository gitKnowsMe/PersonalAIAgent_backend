#!/usr/bin/env python3
"""
Test script for EmailStore functionality
Tests direct email search to verify it's working correctly
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.email.email_store import EmailStore
from app.services.embedding_service import SentenceTransformerEmbeddingService
from app.services.email.email_query import EmailQueryService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_email_store_basic():
    """Test basic EmailStore functionality"""
    logger.info("=== Testing EmailStore Basic Functionality ===")
    
    try:
        # Initialize EmailStore
        email_store = EmailStore()
        
        # Get user statistics
        user_id = 10  # Based on the vector files we saw
        stats = await email_store.get_email_stats(user_id)
        logger.info(f"Email stats for user {user_id}: {stats}")
        
        # Test if we can get email indices
        indices = await email_store._get_user_email_indices(user_id)
        logger.info(f"Found {len(indices)} email indices for user {user_id}")
        
        for index_path, metadata_path in indices[:3]:  # Show first 3
            logger.info(f"Index: {index_path.name}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error in basic EmailStore test: {e}")
        return False

async def test_email_search_direct():
    """Test direct email search functionality"""
    logger.info("=== Testing Direct Email Search ===")
    
    try:
        # Initialize services
        email_store = EmailStore()
        embedding_service = SentenceTransformerEmbeddingService()
        
        # Test query about Apple invoice
        query = "Apple invoice amount cost price"
        user_id = 10
        
        logger.info(f"Searching for: '{query}'")
        
        # Generate embedding for query
        query_embedding = await embedding_service.generate_embedding(query)
        logger.info(f"Generated embedding with dimension: {len(query_embedding)}")
        
        # Search emails
        results = await email_store.search_emails(
            query_embedding=query_embedding,
            user_id=user_id,
            k=10
        )
        
        logger.info(f"Found {len(results)} email results")
        
        # Display results
        for i, result in enumerate(results):
            logger.info(f"Result {i+1}:")
            logger.info(f"  Score: {result.get('score', 0):.3f}")
            logger.info(f"  Text: {result.get('text', '')[:200]}...")
            
            metadata = result.get('metadata', {})
            logger.info(f"  Subject: {metadata.get('subject', 'No Subject')}")
            logger.info(f"  Sender: {metadata.get('sender', 'Unknown')}")
            logger.info(f"  Date: {metadata.get('date', 'Unknown')}")
            logger.info(f"  Email ID: {metadata.get('email_id', 'Unknown')}")
            logger.info("  ---")
            
        return len(results) > 0
        
    except Exception as e:
        logger.error(f"Error in direct email search test: {e}")
        return False

async def test_email_query_service():
    """Test EmailQueryService functionality"""
    logger.info("=== Testing EmailQueryService ===")
    
    try:
        # Initialize service
        email_query_service = EmailQueryService()
        
        # Test the specific query from the user
        query = "check the email how much was the Apple invoice?"
        user_id = 10
        
        logger.info(f"Processing query: '{query}'")
        
        # Process query
        result = await email_query_service.process_email_query(query, user_id)
        
        logger.info(f"Query result keys: {list(result.keys())}")
        logger.info(f"Answer: {result.get('answer', 'No answer')}")
        logger.info(f"Result count: {result.get('result_count', 0)}")
        logger.info(f"Query analysis: {result.get('query_analysis', {})}")
        
        # Show search results
        search_results = result.get('results', [])
        logger.info(f"Found {len(search_results)} search results")
        
        for i, result in enumerate(search_results[:3]):  # Show first 3
            logger.info(f"Search result {i+1}:")
            logger.info(f"  Score: {result.get('score', 0):.3f}")
            logger.info(f"  Text: {result.get('text', '')[:150]}...")
            
        return len(search_results) > 0
        
    except Exception as e:
        logger.error(f"Error in EmailQueryService test: {e}")
        return False

async def test_specific_apple_email():
    """Test searching for specific Apple email by ID"""
    logger.info("=== Testing Specific Apple Email Search ===")
    
    try:
        # Check if email ID 5 exists (mentioned in user's query)
        email_store = EmailStore()
        embedding_service = SentenceTransformerEmbeddingService()
        
        user_id = 10
        apple_keywords = ["Apple", "receipt", "invoice", "purchase", "$"]
        
        # Try multiple Apple-related searches
        for keyword in apple_keywords:
            logger.info(f"Searching for keyword: '{keyword}'")
            
            query_embedding = await embedding_service.generate_embedding(keyword)
            results = await email_store.search_emails(
                query_embedding=query_embedding,
                user_id=user_id,
                k=5
            )
            
            logger.info(f"Found {len(results)} results for '{keyword}'")
            
            # Look for Apple-related content
            for result in results:
                text = result.get('text', '').lower()
                if 'apple' in text or 'invoice' in text or 'receipt' in text:
                    logger.info(f"Found Apple-related content:")
                    logger.info(f"  Score: {result.get('score', 0):.3f}")
                    logger.info(f"  Text: {result.get('text', '')[:300]}...")
                    
                    metadata = result.get('metadata', {})
                    logger.info(f"  Subject: {metadata.get('subject', 'No Subject')}")
                    logger.info(f"  Sender: {metadata.get('sender', 'Unknown')}")
                    logger.info(f"  Email ID: {metadata.get('email_id', 'Unknown')}")
                    logger.info("  ---")
                    
        return True
        
    except Exception as e:
        logger.error(f"Error in specific Apple email search: {e}")
        return False

async def main():
    """Run all email search tests"""
    logger.info("Starting EmailStore functionality tests...")
    
    tests = [
        ("Basic EmailStore", test_email_store_basic),
        ("Direct Email Search", test_email_search_direct),
        ("EmailQueryService", test_email_query_service),
        ("Specific Apple Email", test_specific_apple_email)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            result = await test_func()
            results[test_name] = result
            logger.info(f"✓ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"✗ {test_name}: ERROR - {e}")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{status}: {test_name}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())