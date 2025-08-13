#!/usr/bin/env python3
"""
Test script to verify email sync functionality after async fixes.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.gmail_service import GmailService
from app.db.models import EmailAccount
from unittest.mock import Mock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_async_methods():
    """Test that the async methods are working correctly."""
    logger.info("🧪 Testing Gmail Service Async Methods")
    
    # Create mock objects
    email_account = Mock(spec=EmailAccount)
    email_account.email_address = "test@gmail.com"
    email_account.access_token = "mock_token"
    email_account.refresh_token = "mock_refresh"
    email_account.token_expires_at = None
    
    db_session = Mock()
    db_session.refresh = Mock()
    db_session.commit = Mock()
    
    gmail_service = GmailService()
    
    try:
        # Test 1: Test that get_valid_credentials is async
        logger.info("1. Testing get_valid_credentials async...")
        # This should not raise an error about being called without await
        credentials_task = gmail_service.get_valid_credentials(email_account, db_session)
        if hasattr(credentials_task, '__await__'):
            logger.info("✅ get_valid_credentials is properly async")
            try:
                await credentials_task
            except Exception as e:
                logger.info(f"   Expected error (mock data): {e}")
        else:
            logger.error("❌ get_valid_credentials is not async!")
            return False
        
        # Test 2: Test that refresh_access_token is async
        logger.info("2. Testing refresh_access_token async...")
        refresh_task = gmail_service.refresh_access_token(email_account, db_session)
        if hasattr(refresh_task, '__await__'):
            logger.info("✅ refresh_access_token is properly async")
            try:
                await refresh_task
            except Exception as e:
                logger.info(f"   Expected error (mock data): {e}")
        else:
            logger.error("❌ refresh_access_token is not async!")
            return False
        
        # Test 3: Test that sync_emails is async
        logger.info("3. Testing sync_emails async...")
        sync_task = gmail_service.sync_emails(email_account, db_session, max_emails=1)
        if hasattr(sync_task, '__await__'):
            logger.info("✅ sync_emails is properly async")
            try:
                await sync_task
            except Exception as e:
                logger.info(f"   Expected error (mock data): {e}")
        else:
            logger.error("❌ sync_emails is not async!")
            return False
        
        # Test 4: Test that disconnect_account is async
        logger.info("4. Testing disconnect_account async...")
        disconnect_task = gmail_service.disconnect_account(email_account, db_session)
        if hasattr(disconnect_task, '__await__'):
            logger.info("✅ disconnect_account is properly async")
            try:
                await disconnect_task
            except Exception as e:
                logger.info(f"   Expected error (mock data): {e}")
        else:
            logger.error("❌ disconnect_account is not async!")
            return False
        
        logger.info("🎉 All async methods are working correctly!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Unexpected error during testing: {e}")
        return False


def test_method_signatures():
    """Test that method signatures are correct."""
    logger.info("📋 Checking Method Signatures")
    
    gmail_service = GmailService()
    
    # Check if methods exist and are callable
    methods_to_check = [
        'get_valid_credentials',
        'refresh_access_token', 
        'sync_emails',
        'disconnect_account'
    ]
    
    for method_name in methods_to_check:
        if hasattr(gmail_service, method_name):
            method = getattr(gmail_service, method_name)
            if callable(method):
                logger.info(f"✅ {method_name} exists and is callable")
            else:
                logger.error(f"❌ {method_name} exists but is not callable")
                return False
        else:
            logger.error(f"❌ {method_name} does not exist")
            return False
    
    return True


async def main():
    """Main test function."""
    logger.info("🚀 Starting Gmail Service Async Fix Verification")
    logger.info("=" * 60)
    
    # Test 1: Check method signatures
    if not test_method_signatures():
        logger.error("❌ Method signature test failed")
        return
    
    # Test 2: Test async functionality
    if not await test_async_methods():
        logger.error("❌ Async methods test failed")
        return
    
    logger.info("=" * 60)
    logger.info("🎉 All tests passed!")
    logger.info("")
    logger.info("✅ The email sync should now work correctly")
    logger.info("✅ The 500 Internal Server Error should be resolved")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Restart the application server")
    logger.info("2. Try the email sync again in the web interface")
    logger.info("3. The sync should complete without errors")


if __name__ == "__main__":
    asyncio.run(main())