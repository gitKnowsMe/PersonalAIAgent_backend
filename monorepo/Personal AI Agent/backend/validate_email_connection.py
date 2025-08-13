#!/usr/bin/env python3
"""
Email Connection Validation Script
Diagnoses Gmail connection issues and provides detailed status information.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate environment configuration."""
    logger.info("=== Environment Configuration Validation ===")
    
    try:
        from app.core.config import settings
        
        # Check Gmail configuration
        config_issues = []
        
        if not settings.GMAIL_CLIENT_ID:
            config_issues.append("GMAIL_CLIENT_ID is not set")
        elif settings.GMAIL_CLIENT_ID == 'your_gmail_client_id_from_google_cloud_console':
            config_issues.append("GMAIL_CLIENT_ID is still set to placeholder value")
        elif not settings.GMAIL_CLIENT_ID.endswith('.apps.googleusercontent.com'):
            config_issues.append("GMAIL_CLIENT_ID should end with '.apps.googleusercontent.com'")
        
        if not settings.GMAIL_CLIENT_SECRET:
            config_issues.append("GMAIL_CLIENT_SECRET is not set")
        elif settings.GMAIL_CLIENT_SECRET == 'your_gmail_client_secret_from_google_cloud_console':
            config_issues.append("GMAIL_CLIENT_SECRET is still set to placeholder value")
        elif not settings.GMAIL_CLIENT_SECRET.startswith('GOCSPX-'):
            config_issues.append("GMAIL_CLIENT_SECRET should start with 'GOCSPX-'")
        
        if not settings.GMAIL_REDIRECT_URI:
            config_issues.append("GMAIL_REDIRECT_URI is not set")
        elif not settings.GMAIL_REDIRECT_URI.startswith('http'):
            config_issues.append("GMAIL_REDIRECT_URI should start with 'http'")
        
        if config_issues:
            logger.error("❌ Configuration Issues Found:")
            for issue in config_issues:
                logger.error(f"  - {issue}")
            logger.error("\nTo fix these issues:")
            logger.error("1. Go to https://console.cloud.google.com/")
            logger.error("2. Create OAuth 2.0 credentials")
            logger.error("3. Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env file")
            logger.error("4. Add redirect URI: http://localhost:8000/api/gmail/callback")
            return False
        else:
            logger.info("✅ Gmail OAuth configuration is valid")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error validating environment: {e}")
        return False

def check_database_connection():
    """Check database connection and email account status."""
    logger.info("=== Database Connection Check ===")
    
    try:
        from app.db.database import get_db
        from app.db.models import User, EmailAccount, Email, OAuthSession
        
        db = next(get_db())
        
        # Check email accounts
        email_accounts = db.query(EmailAccount).all()
        logger.info(f"Found {len(email_accounts)} email accounts:")
        
        for account in email_accounts:
            logger.info(f"  - Account {account.id}: {account.email_address}")
            logger.info(f"    Provider: {account.provider}")
            logger.info(f"    Active: {account.is_active}")
            logger.info(f"    Sync Enabled: {account.sync_enabled}")
            logger.info(f"    Last Sync: {account.last_sync_at}")
            logger.info(f"    Token Expires: {account.token_expires_at}")
            
            # Check if token is expired
            if account.token_expires_at:
                if account.token_expires_at.tzinfo is None:
                    token_expiry = account.token_expires_at.replace(tzinfo=timezone.utc)
                else:
                    token_expiry = account.token_expires_at
                
                now = datetime.now(timezone.utc)
                if token_expiry <= now:
                    logger.warning(f"    ⚠️  Token is expired!")
                else:
                    logger.info(f"    ✅ Token is valid")
            else:
                logger.warning(f"    ⚠️  No token expiry information")
        
        # Check OAuth sessions
        oauth_sessions = db.query(OAuthSession).filter(
            OAuthSession.provider == "gmail"
        ).all()
        logger.info(f"Found {len(oauth_sessions)} OAuth sessions:")
        
        for session in oauth_sessions:
            logger.info(f"  - Session {session.id}: User {session.user_id}")
            logger.info(f"    State: {session.oauth_state}")
            logger.info(f"    Expires: {session.expires_at}")
            
            if session.expires_at <= datetime.utcnow():
                logger.warning(f"    ⚠️  Session is expired!")
            else:
                logger.info(f"    ✅ Session is valid")
        
        # Check emails
        total_emails = db.query(Email).count()
        logger.info(f"Total emails in database: {total_emails}")
        
        # Check processed emails
        processed_emails = db.query(Email).filter(
            Email.vector_namespace.isnot(None)
        ).count()
        logger.info(f"Processed emails (with vector namespace): {processed_emails}")
        
        unprocessed_emails = db.query(Email).filter(
            Email.vector_namespace.is_(None)
        ).count()
        logger.info(f"Unprocessed emails: {unprocessed_emails}")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        return False

def check_vector_storage():
    """Check vector storage consistency."""
    logger.info("=== Vector Storage Check ===")
    
    try:
        from app.core.config import settings
        
        vector_path = Path(settings.VECTOR_DB_PATH) / "emails"
        
        if not vector_path.exists():
            logger.warning("⚠️  Email vector directory doesn't exist")
            return True
        
        # Count vector files
        index_files = list(vector_path.glob("*.index"))
        pkl_files = list(vector_path.glob("*.pkl"))
        
        logger.info(f"Found {len(index_files)} index files and {len(pkl_files)} metadata files")
        
        # Check for orphaned files
        index_basenames = {f.stem for f in index_files}
        pkl_basenames = {f.stem for f in pkl_files}
        
        orphaned_index = index_basenames - pkl_basenames
        orphaned_pkl = pkl_basenames - index_basenames
        
        if orphaned_index:
            logger.warning(f"⚠️  Found {len(orphaned_index)} orphaned index files")
        
        if orphaned_pkl:
            logger.warning(f"⚠️  Found {len(orphaned_pkl)} orphaned metadata files")
        
        if not orphaned_index and not orphaned_pkl:
            logger.info("✅ Vector storage is consistent")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector storage check error: {e}")
        return False

def test_gmail_service():
    """Test Gmail service initialization."""
    logger.info("=== Gmail Service Test ===")
    
    try:
        from app.services.gmail_service import GmailService
        
        gmail_service = GmailService()
        logger.info("✅ Gmail service initialized successfully")
        
        # Test authorization URL generation
        test_redirect = "http://localhost:8000/api/gmail/callback"
        try:
            auth_url, state = gmail_service.get_authorization_url(test_redirect)
            logger.info("✅ Authorization URL generation successful")
            logger.info(f"State parameter: {state}")
        except Exception as e:
            logger.error(f"❌ Authorization URL generation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Gmail service test failed: {e}")
        return False

def main():
    """Main validation function."""
    logger.info("🔍 Starting Email Connection Validation...")
    
    results = {
        'environment': validate_environment(),
        'database': check_database_connection(),
        'vector_storage': check_vector_storage(),
        'gmail_service': test_gmail_service()
    }
    
    logger.info("=== Validation Summary ===")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
    
    if all(results.values()):
        logger.info("\n🎉 All validation checks passed!")
        logger.info("If you're still experiencing issues, check:")
        logger.info("1. Network connectivity")
        logger.info("2. Google Cloud Console OAuth configuration")
        logger.info("3. Frontend connection status display")
        return 0
    else:
        logger.error("\n❌ Some validation checks failed!")
        logger.error("Please fix the issues above before attempting to connect Gmail.")
        return 1

if __name__ == "__main__":
    sys.exit(main())