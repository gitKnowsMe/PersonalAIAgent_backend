#!/usr/bin/env python3
"""
Debug script to diagnose email sync 400 Bad Request errors.
This script provides detailed error information to help identify the root cause.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.gmail_service import GmailService
from app.db.database import get_db
from app.db.models import EmailAccount, User

# Configure logging to see all details
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def debug_email_sync():
    """Debug the email sync process step by step."""
    logger.info("🔍 Starting Email Sync Debug Session")
    logger.info("=" * 60)
    
    try:
        # Get database session
        db = next(get_db())
        
        # Find an active email account
        email_account = db.query(EmailAccount).filter(
            EmailAccount.is_active == True,
            EmailAccount.sync_enabled == True
        ).first()
        
        if not email_account:
            logger.error("❌ No active email accounts found for testing")
            logger.info("Available accounts:")
            all_accounts = db.query(EmailAccount).all()
            for acc in all_accounts:
                logger.info(f"  ID: {acc.id}, Email: {acc.email_address}, Active: {acc.is_active}, Sync: {acc.sync_enabled}")
            return
        
        logger.info(f"📧 Testing with account: {email_account.email_address}")
        logger.info(f"   Account ID: {email_account.id}")
        logger.info(f"   User ID: {email_account.user_id}")
        logger.info(f"   Active: {email_account.is_active}")
        logger.info(f"   Sync Enabled: {email_account.sync_enabled}")
        logger.info(f"   Last Sync: {email_account.last_sync_at}")
        
        # Test Gmail service initialization
        gmail_service = GmailService()
        logger.info("✅ Gmail service initialized")
        
        # Step 1: Test token validation
        logger.info("\\n🔑 Step 1: Testing token validation...")
        try:
            credentials = await gmail_service.get_valid_credentials(email_account, db)
            if credentials:
                logger.info("✅ Credentials obtained successfully")
                logger.info(f"   Token exists: {bool(credentials.token)}")
                logger.info(f"   Refresh token exists: {bool(credentials.refresh_token)}")
                logger.info(f"   Token expiry: {credentials.expiry}")
                
                # Check if token is expired
                if credentials.expiry:
                    now = datetime.now(credentials.expiry.tzinfo) if credentials.expiry.tzinfo else datetime.now()
                    if credentials.expiry <= now:
                        logger.warning("⚠️  Token is expired but was retrieved")
                    else:
                        logger.info(f"✅ Token is valid until {credentials.expiry}")
                else:
                    logger.warning("⚠️  Token has no expiry date")
            else:
                logger.error("❌ Could not obtain valid credentials")
                logger.error("This is likely the cause of the 400 Bad Request error")
                return
        except Exception as e:
            logger.error(f"❌ Token validation failed: {e}")
            logger.error("This is likely the cause of the 400 Bad Request error")
            return
        
        # Step 2: Test Gmail API connection
        logger.info("\\n📬 Step 2: Testing Gmail API connection...")
        try:
            # Check credentials attributes before building service
            logger.info(f"   Credentials token type: {type(credentials.token)}")
            logger.info(f"   Credentials expiry type: {type(credentials.expiry)}")
            logger.info(f"   Credentials expiry tzinfo: {getattr(credentials.expiry, 'tzinfo', None)}")
            
            # Try to create a new credentials object with timezone-naive expiry
            from google.oauth2.credentials import Credentials
            from datetime import timezone
            
            # Create new credentials with timezone-naive expiry
            safe_credentials = Credentials(
                token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_uri=credentials.token_uri,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                scopes=credentials.scopes
            )
            
            # Set expiry as timezone-naive UTC
            if credentials.expiry:
                if credentials.expiry.tzinfo:
                    # Convert to UTC and make naive
                    safe_credentials.expiry = credentials.expiry.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    safe_credentials.expiry = credentials.expiry
            
            logger.info(f"   Safe credentials expiry: {safe_credentials.expiry}")
            logger.info(f"   Safe credentials expiry type: {type(safe_credentials.expiry)}")
            
            from googleapiclient.discovery import build
            service = build('gmail', 'v1', credentials=safe_credentials)
            
            # Test with a simple API call
            profile = service.users().getProfile(userId='me').execute()
            logger.info("✅ Gmail API connection successful")
            logger.info(f"   Email: {profile.get('emailAddress')}")
            logger.info(f"   Messages total: {profile.get('messagesTotal')}")
            logger.info(f"   Threads total: {profile.get('threadsTotal')}")
        except Exception as e:
            logger.error(f"❌ Gmail API connection failed: {e}")
            logger.error("This is likely the cause of the 400 Bad Request error")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Check for specific error types
            error_str = str(e).lower()
            if "403" in error_str or "forbidden" in error_str:
                logger.error("   → This appears to be a permissions/scope issue")
                logger.error("   → Try disconnecting and reconnecting the Gmail account")
            elif "401" in error_str or "unauthorized" in error_str:
                logger.error("   → This appears to be an authentication issue")
                logger.error("   → The access token may be invalid or expired")
            elif "400" in error_str:
                logger.error("   → This appears to be a bad request issue")
                logger.error("   → Check the API request parameters")
            
            return
        
        # Step 3: Test actual sync with minimal parameters
        logger.info("\\n🔄 Step 3: Testing email sync with minimal parameters...")
        try:
            sync_response = await gmail_service.sync_emails(
                email_account=email_account,
                db=db,
                max_emails=1,  # Sync only 1 email to test
                sync_since=datetime.now() - timedelta(days=1)  # Only last day
            )
            
            logger.info(f"Sync Response:")
            logger.info(f"   Success: {sync_response.success}")
            logger.info(f"   Emails synced: {sync_response.emails_synced}")
            logger.info(f"   Errors: {sync_response.errors}")
            logger.info(f"   Duration: {sync_response.sync_duration_ms}ms")
            
            if sync_response.success:
                logger.info("✅ Email sync completed successfully!")
            else:
                logger.error("❌ Email sync failed")
                logger.error("Detailed errors:")
                for error in sync_response.errors:
                    logger.error(f"   → {error}")
                    
        except Exception as e:
            logger.error(f"❌ Email sync test failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
        
    except Exception as e:
        logger.error(f"❌ Debug session failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
    finally:
        db.close()


def print_troubleshooting_guide():
    """Print a troubleshooting guide based on common issues."""
    logger.info("\\n" + "=" * 60)
    logger.info("🛠️  TROUBLESHOOTING GUIDE")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Common causes of 400 Bad Request in email sync:")
    logger.info("")
    logger.info("1. **Expired or Invalid Tokens**")
    logger.info("   - Solution: Disconnect and reconnect Gmail account")
    logger.info("   - URL: http://localhost:8000 → Gmail Settings → Disconnect")
    logger.info("")
    logger.info("2. **Insufficient Permissions/Scopes**")
    logger.info("   - The app may not have been granted proper Gmail permissions")
    logger.info("   - Solution: Reconnect and grant all requested permissions")
    logger.info("")
    logger.info("3. **Gmail API Quota Exceeded**")
    logger.info("   - Solution: Wait and try again later")
    logger.info("   - Check Google Cloud Console for quota limits")
    logger.info("")
    logger.info("4. **Invalid Gmail Account State**")
    logger.info("   - Account may be disabled or have sync issues")
    logger.info("   - Solution: Check account settings in database")
    logger.info("")
    logger.info("5. **Network/Connectivity Issues**")
    logger.info("   - Solution: Check internet connection")
    logger.info("   - Verify Google services are accessible")


async def main():
    """Main debug function."""
    await debug_email_sync()
    print_troubleshooting_guide()


if __name__ == "__main__":
    asyncio.run(main())