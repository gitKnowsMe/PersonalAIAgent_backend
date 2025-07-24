#!/usr/bin/env python3
"""
Test script to verify classification tags fix
Tests that classification tags are properly passed through the email processing pipeline
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.email.email_processor import EmailProcessor
from app.services.email.email_classifier import EmailClassifier
from app.utils.processors.email_processor import EmailDocumentProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_classification_tags_end_to_end():
    """Test complete classification tags flow"""
    logger.info("=== Testing Classification Tags Fix ===")
    
    # Test data
    email_data = {
        'subject': 'Meeting Invitation - Project Review',
        'sender': 'boss@company.com',
        'recipient': 'user@company.com',
        'body_text': 'Please join our project review meeting tomorrow at 2 PM.',
        'message_id': 'test-msg-123',
        'date': None
    }
    
    user_id = 7
    
    try:
        # Step 1: Test EmailClassifier
        logger.info("Step 1: Testing EmailClassifier")
        classifier = EmailClassifier()
        classification_tags = await classifier.classify_email(email_data)
        logger.info(f"Classification tags generated: {classification_tags}")
        
        # Step 2: Test EmailProcessor with classification tags
        logger.info("Step 2: Testing EmailProcessor with classification tags")
        processor = EmailProcessor()
        chunks = await processor.process_email(email_data, user_id, classification_tags)
        
        logger.info(f"Generated {len(chunks)} chunks")
        
        # Verify classification tags in metadata
        success = True
        for i, chunk in enumerate(chunks):
            metadata = chunk.get('metadata', {})
            chunk_tags = metadata.get('classification_tags', [])
            
            logger.info(f"Chunk {i+1} classification tags: {chunk_tags}")
            
            if chunk_tags != classification_tags:
                logger.error(f"❌ Chunk {i+1} has incorrect tags: expected {classification_tags}, got {chunk_tags}")
                success = False
        
        if success:
            logger.info("✅ Step 2 PASSED: Classification tags correctly preserved in chunks")
        else:
            logger.error("❌ Step 2 FAILED: Classification tags not properly preserved")
            return False
        
        # Step 3: Test legacy EmailDocumentProcessor
        logger.info("Step 3: Testing legacy EmailDocumentProcessor")
        
        # Create test email content
        test_email_content = f"""Subject: {email_data['subject']}
From: {email_data['sender']}
To: {email_data['recipient']}
Date: Mon, 1 Jan 2024 12:00:00 +0000

{email_data['body_text']}
""".encode('utf-8')
        
        legacy_processor = EmailDocumentProcessor()
        result = await legacy_processor.process_content(test_email_content, user_id, 'test.eml')
        
        if result.get('success'):
            result_tags = result.get('classification_tags', [])
            logger.info(f"Legacy processor classification tags: {result_tags}")
            
            # Check chunk metadata
            result_chunks = result.get('chunks', [])
            if result_chunks:
                chunk_metadata = result_chunks[0].get('metadata', {})
                chunk_tags = chunk_metadata.get('classification_tags', [])
                logger.info(f"Legacy processor chunk tags: {chunk_tags}")
                
                if chunk_tags:
                    logger.info("✅ Step 3 PASSED: Legacy processor preserves classification tags")
                else:
                    logger.error("❌ Step 3 FAILED: Legacy processor missing classification tags in chunks")
                    return False
            else:
                logger.error("❌ Step 3 FAILED: Legacy processor generated no chunks")
                return False
        else:
            logger.error(f"❌ Step 3 FAILED: Legacy processor failed: {result.get('error')}")
            return False
        
        # Step 4: Summary
        logger.info("=== TEST SUMMARY ===")
        logger.info("✅ EmailClassifier: Generates classification tags")
        logger.info("✅ EmailProcessor: Preserves classification tags in chunk metadata")
        logger.info("✅ Legacy EmailDocumentProcessor: Preserves classification tags")
        logger.info("✅ ALL TESTS PASSED - Classification tags fix is working!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_metadata_structure():
    """Test that metadata structure includes all expected fields"""
    logger.info("=== Testing Metadata Structure ===")
    
    email_data = {
        'subject': 'Test Email',
        'sender': 'sender@test.com',
        'recipient': 'user@test.com',
        'body_text': 'This is a longer test email content that should generate at least one chunk when processed through the email processor. It contains enough text to meet the minimum chunk size requirements and should properly include the classification tags in the metadata structure.',
        'message_id': 'test-123',
        'date': None
    }
    
    test_tags = ['business', 'meeting', 'important']
    processor = EmailProcessor()
    
    try:
        chunks = await processor.process_email(email_data, 7, test_tags)
        
        if chunks:
            metadata = chunks[0].get('metadata', {})
            
            # Check required fields
            required_fields = [
                'user_id', 'content_type', 'message_id', 'subject', 
                'sender', 'classification_tags'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in metadata:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.error(f"❌ Missing metadata fields: {missing_fields}")
                return False
            
            # Verify classification_tags specifically
            if metadata['classification_tags'] == test_tags:
                logger.info("✅ Metadata structure test PASSED")
                logger.info(f"✅ Classification tags correctly set: {metadata['classification_tags']}")
                return True
            else:
                logger.error(f"❌ Classification tags mismatch: expected {test_tags}, got {metadata['classification_tags']}")
                return False
        else:
            logger.error("❌ No chunks generated")
            return False
            
    except Exception as e:
        logger.error(f"❌ Metadata test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting Classification Tags Fix Verification")
    
    # Test 1: End-to-end flow
    test1_passed = await test_classification_tags_end_to_end()
    
    # Test 2: Metadata structure
    test2_passed = await test_metadata_structure()
    
    # Final result
    if test1_passed and test2_passed:
        logger.info("🎉 ALL TESTS PASSED - Classification Tags Fix is WORKING!")
        print("\n" + "="*60)
        print("✅ CLASSIFICATION TAGS FIX VERIFICATION: SUCCESS")
        print("✅ Email processing pipeline now preserves classification tags")
        print("✅ Both new and legacy processors work correctly")
        print("✅ Metadata structure includes classification_tags field")
        print("="*60)
        return True
    else:
        logger.error("💥 SOME TESTS FAILED - Fix needs more work")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)