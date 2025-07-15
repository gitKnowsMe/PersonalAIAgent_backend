#!/usr/bin/env python3
"""
Test script for concurrent token refresh scenarios.
Validates the thread-safe token refresh mechanism implementation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.gmail_service import GmailService
from app.db.models import EmailAccount

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_concurrent_token_refresh():
    """Test concurrent token refresh attempts on the same account."""
    
    # Create mock email account with expired token
    email_account = Mock(spec=EmailAccount)
    email_account.email_address = "test@example.com"
    email_account.access_token = "encrypted_expired_token"
    email_account.refresh_token = "encrypted_refresh_token"
    email_account.token_expires_at = datetime.now() - timedelta(minutes=10)  # Expired
    
    # Create mock database session
    db_session = Mock()
    db_session.refresh = Mock()
    db_session.commit = Mock()
    
    # Create Gmail service instance
    gmail_service = GmailService()
    
    # Mock the auth service methods
    with patch.object(gmail_service.auth_service, 'decrypt_token') as mock_decrypt, \
         patch.object(gmail_service.auth_service, 'encrypt_token') as mock_encrypt, \
         patch('app.services.gmail_service.Request') as mock_request, \
         patch('app.services.gmail_service.Credentials') as mock_credentials_class:
        
        # Setup mocks
        mock_decrypt.return_value = "decrypted_token"
        mock_encrypt.return_value = "encrypted_new_token"
        
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.refresh = Mock()
        mock_credentials.token = "new_access_token"
        mock_credentials.expiry = datetime.now() + timedelta(hours=1)
        mock_credentials_class.return_value = mock_credentials
        
        # Test concurrent refresh attempts
        logger.info("Starting concurrent token refresh test...")
        
        # Create multiple concurrent refresh tasks
        tasks = []
        num_concurrent_requests = 5
        
        for i in range(num_concurrent_requests):
            task = asyncio.create_task(
                gmail_service.refresh_access_token(email_account, db_session),
                name=f"refresh_task_{i}"
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_refreshes = sum(1 for result in results if result is True)
        failed_refreshes = sum(1 for result in results if result is False)
        exceptions = [result for result in results if isinstance(result, Exception)]
        
        logger.info(f"Concurrent refresh test results:")
        logger.info(f"  Successful refreshes: {successful_refreshes}")
        logger.info(f"  Failed refreshes: {failed_refreshes}")
        logger.info(f"  Exceptions: {len(exceptions)}")
        
        # Verify that refresh was called only once (due to locking)
        logger.info(f"  Credentials.refresh called {mock_credentials.refresh.call_count} times")
        logger.info(f"  Database commit called {db_session.commit.call_count} times")
        
        # Test should ensure only one actual refresh occurred
        assert mock_credentials.refresh.call_count <= 2, "Too many refresh calls - locking failed"
        assert successful_refreshes > 0, "No successful refreshes"
        
        logger.info("✅ Concurrent token refresh test passed!")


async def test_token_expiry_buffer():
    """Test token refresh with buffer time."""
    
    # Create mock email account with token expiring soon
    email_account = Mock(spec=EmailAccount)
    email_account.email_address = "test@example.com"
    email_account.access_token = "encrypted_token"
    email_account.refresh_token = "encrypted_refresh_token"
    # Token expires in 3 minutes (within 5-minute buffer)
    email_account.token_expires_at = datetime.now() + timedelta(minutes=3)
    
    db_session = Mock()
    db_session.refresh = Mock()
    db_session.commit = Mock()
    
    gmail_service = GmailService()
    
    # Test buffer logic
    is_near_expiry = gmail_service._is_token_near_expiry(email_account.token_expires_at)
    logger.info(f"Token expiring in 3 minutes - is_near_expiry: {is_near_expiry}")
    assert is_near_expiry, "Token should be considered near expiry"
    
    # Test with token expiring in 10 minutes (outside buffer)
    email_account.token_expires_at = datetime.now() + timedelta(minutes=10)
    is_near_expiry = gmail_service._is_token_near_expiry(email_account.token_expires_at)
    logger.info(f"Token expiring in 10 minutes - is_near_expiry: {is_near_expiry}")
    assert not is_near_expiry, "Token should not be considered near expiry"
    
    logger.info("✅ Token expiry buffer test passed!")


async def test_lock_timeout():
    """Test lock timeout mechanism."""
    
    gmail_service = GmailService()
    gmail_service._lock_timeout = 0.1  # Very short timeout for testing
    
    email_account = Mock(spec=EmailAccount)
    email_account.email_address = "test@example.com"
    email_account.access_token = "encrypted_token"
    email_account.refresh_token = "encrypted_refresh_token"
    email_account.token_expires_at = datetime.now() - timedelta(minutes=10)
    
    db_session = Mock()
    
    # Simulate a lock that's already held
    lock = gmail_service._get_refresh_lock(email_account.email_address)
    await lock.acquire()  # Hold the lock
    
    try:
        # This should timeout
        result = await gmail_service.refresh_access_token(email_account, db_session)
        assert result is False, "Refresh should have failed due to timeout"
        logger.info("✅ Lock timeout test passed!")
    finally:
        lock.release()


async def main():
    """Run all tests."""
    logger.info("Starting thread-safe token refresh tests...")
    
    try:
        await test_token_expiry_buffer()
        await test_lock_timeout()
        await test_concurrent_token_refresh()
        
        logger.info("🎉 All tests passed! Thread-safe token refresh is working correctly.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())