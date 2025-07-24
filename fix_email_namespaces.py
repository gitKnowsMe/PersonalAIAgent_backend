#!/usr/bin/env python3
"""
Email Namespace Consistency Fix Script
Ensures all email records have correct vector_namespace values.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_email_namespaces():
    """Fix email namespace inconsistencies."""
    logger.info("=== Email Namespace Consistency Fix ===")
    
    try:
        from app.db.database import get_db
        from app.db.models import Email
        from app.core.config import settings
        
        db = next(get_db())
        
        # Get all emails
        emails = db.query(Email).all()
        logger.info(f"Found {len(emails)} emails to check")
        
        fixed_count = 0
        
        for email in emails:
            expected_namespace = f"user_{email.user_id}_email_gmail_{email.id}"
            
            if email.vector_namespace != expected_namespace:
                logger.info(f"Fixing email {email.id}: '{email.vector_namespace}' -> '{expected_namespace}'")
                email.vector_namespace = expected_namespace
                fixed_count += 1
        
        if fixed_count > 0:
            db.commit()
            logger.info(f"✅ Fixed {fixed_count} email namespace inconsistencies")
        else:
            logger.info("✅ All email namespaces are consistent")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing email namespaces: {e}")
        return False

def cleanup_orphaned_oauth_sessions():
    """Clean up expired OAuth sessions."""
    logger.info("=== OAuth Session Cleanup ===")
    
    try:
        from app.db.database import get_db
        from app.db.models import OAuthSession
        from datetime import datetime
        
        db = next(get_db())
        
        # Delete expired sessions
        deleted_count = db.query(OAuthSession).filter(
            OAuthSession.expires_at <= datetime.utcnow()
        ).delete()
        
        db.commit()
        logger.info(f"✅ Cleaned up {deleted_count} expired OAuth sessions")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up OAuth sessions: {e}")
        return False

def cleanup_orphaned_vector_files():
    """Clean up orphaned vector files."""
    logger.info("=== Vector File Cleanup ===")
    
    try:
        from app.db.database import get_db
        from app.db.models import Email
        from app.core.config import settings
        
        db = next(get_db())
        
        # Get all email IDs from database
        email_ids = {email.id for email in db.query(Email).all()}
        user_ids = {email.user_id for email in db.query(Email).all()}
        
        vector_path = Path(settings.VECTOR_DB_PATH) / "emails"
        
        if not vector_path.exists():
            logger.info("No email vector directory found")
            return True
        
        # Check vector files
        index_files = list(vector_path.glob("*.index"))
        pkl_files = list(vector_path.glob("*.pkl"))
        
        orphaned_files = []
        
        for file in index_files + pkl_files:
            # Extract email ID from filename
            # Expected format: user_{user_id}_email_gmail_{email_id}.{index|pkl}
            parts = file.stem.split('_')
            if len(parts) >= 5 and parts[0] == 'user' and parts[2] == 'email':
                try:
                    user_id = int(parts[1])
                    email_id = int(parts[4])
                    
                    if user_id not in user_ids or email_id not in email_ids:
                        orphaned_files.append(file)
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse filename: {file.name}")
                    continue
        
        if orphaned_files:
            logger.info(f"Found {len(orphaned_files)} orphaned vector files")
            
            # Ask for confirmation
            response = input("Delete orphaned vector files? (y/N): ")
            if response.lower() == 'y':
                for file in orphaned_files:
                    file.unlink()
                    logger.info(f"Deleted: {file.name}")
                logger.info(f"✅ Cleaned up {len(orphaned_files)} orphaned vector files")
            else:
                logger.info("Skipped vector file cleanup")
        else:
            logger.info("✅ No orphaned vector files found")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up vector files: {e}")
        return False

def main():
    """Main fix function."""
    logger.info("🔧 Starting Email Namespace Consistency Fix...")
    
    results = {
        'namespaces': fix_email_namespaces(),
        'oauth_sessions': cleanup_orphaned_oauth_sessions(),
        'vector_files': cleanup_orphaned_vector_files()
    }
    
    logger.info("=== Fix Summary ===")
    for fix_name, result in results.items():
        status = "✅ SUCCESS" if result else "❌ FAILED"
        logger.info(f"{fix_name.replace('_', ' ').title()}: {status}")
    
    if all(results.values()):
        logger.info("\n🎉 All fixes completed successfully!")
        return 0
    else:
        logger.error("\n❌ Some fixes failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())