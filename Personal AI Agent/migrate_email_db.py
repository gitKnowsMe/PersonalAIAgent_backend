#!/usr/bin/env python3
"""
Email Database Migration Script

Adds email-related tables to the existing database for Gmail integration support.
This script is safe to run multiple times - it will only create tables that don't exist.
"""

import logging
import sys
from sqlalchemy import text

from app.core.config import settings
from app.db.database import engine, get_db
from app.db.models import Base, EmailAccount, Email, EmailAttachment

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_email_tables():
    """
    Create email-related tables in the database
    """
    try:
        logger.info("Starting email database migration...")
        
        # Test database connection
        logger.info("Testing database connection...")
        db = next(get_db())
        try:
            db.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
        finally:
            db.close()
        
        # Create all tables (existing tables will be skipped)
        logger.info("Creating email tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify email tables were created
        logger.info("Verifying email tables...")
        
        with engine.connect() as conn:
            # Check if email tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('email_accounts', 'emails', 'email_attachments')
            """))
            
            existing_tables = [row[0] for row in result.fetchall()]
            
            expected_tables = ['email_accounts', 'emails', 'email_attachments']
            
            for table in expected_tables:
                if table in existing_tables:
                    logger.info(f"✅ Table '{table}' exists")
                else:
                    logger.warning(f"⚠️  Table '{table}' not found")
        
        logger.info("🎉 Email database migration completed successfully!")
        logger.info("\n📋 Next steps:")
        logger.info("1. Configure Gmail API credentials: python setup_gmail.py")
        logger.info("2. Install dependencies: pip install -r requirements.txt")
        logger.info("3. Start the application: python main.py")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


def check_email_tables():
    """
    Check if email tables already exist
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('email_accounts', 'emails', 'email_attachments')
            """))
            
            existing_tables = [row[0] for row in result.fetchall()]
            
            if len(existing_tables) == 3:
                logger.info("✅ All email tables already exist")
                return True
            elif len(existing_tables) > 0:
                logger.info(f"⚠️  Partial email tables exist: {existing_tables}")
                return False
            else:
                logger.info("📝 No email tables found - migration needed")
                return False
                
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return False


def show_email_schema():
    """
    Display the email database schema
    """
    print("\n📊 Email Database Schema:")
    print("=" * 50)
    
    print("\n📋 EmailAccount Table:")
    print("- id (Primary Key)")
    print("- user_id (Foreign Key to users)")
    print("- email_address (Gmail address)")
    print("- provider (gmail, outlook, etc.)")
    print("- access_token (Encrypted OAuth token)")
    print("- refresh_token (Encrypted refresh token)")
    print("- token_expires_at")
    print("- is_active, sync_enabled")
    print("- last_sync_at, created_at")
    
    print("\n📧 Email Table:")
    print("- id (Primary Key)")
    print("- email_account_id (Foreign Key)")
    print("- user_id (Foreign Key)")
    print("- message_id (Gmail message ID)")
    print("- thread_id (Gmail thread ID)")
    print("- subject, sender_email, sender_name")
    print("- recipient_emails, cc_emails, bcc_emails (JSON)")
    print("- body_text, body_html")
    print("- email_type (business, personal, promotional, etc.)")
    print("- is_read, is_important, has_attachments")
    print("- gmail_labels (JSON array)")
    print("- sent_at, created_at")
    print("- vector_namespace (for vector storage)")
    
    print("\n📎 EmailAttachment Table:")
    print("- id (Primary Key)")
    print("- email_id (Foreign Key)")
    print("- user_id (Foreign Key)")
    print("- filename, file_path, file_size")
    print("- mime_type, attachment_id")
    print("- is_downloaded, created_at")


if __name__ == "__main__":
    print("🔧 Personal AI Agent - Email Database Migration")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print(__doc__)
        show_email_schema()
        sys.exit(0)
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--check', '-c', 'check']:
        check_email_tables()
        sys.exit(0)
    
    if len(sys.argv) > 1 and sys.argv[1] in ['--schema', '-s', 'schema']:
        show_email_schema()
        sys.exit(0)
    
    # Check if migration is needed
    if check_email_tables():
        print("✅ Email tables already exist. No migration needed.")
        print("Use --check to verify or --schema to view table structure")
    else:
        print("📝 Starting email database migration...")
        success = migrate_email_tables()
        
        if success:
            print("\n✅ Migration completed successfully!")
        else:
            print("\n❌ Migration failed. Check logs for details.")
            sys.exit(1)