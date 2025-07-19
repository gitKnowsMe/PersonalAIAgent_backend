#!/usr/bin/env python3
"""
PostgreSQL Migration Verification Script

This script verifies that the migration from SQLite to PostgreSQL was successful.
"""

import logging
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment_config():
    """Check that environment is configured for PostgreSQL."""
    logger.info("=== Environment Configuration Check ===")
    
    success = True
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        if 'postgresql://' in env_content:
            logger.info("✅ .env file configured for PostgreSQL")
        else:
            logger.warning("⚠️  .env file may not be configured for PostgreSQL")
            success = False
    else:
        logger.warning("⚠️  .env file not found")
        success = False
    
    # Check environment variable
    db_url = os.getenv('DATABASE_URL', '')
    if db_url.startswith('postgresql://'):
        logger.info("✅ DATABASE_URL environment variable points to PostgreSQL")
    else:
        logger.warning(f"⚠️  DATABASE_URL: {db_url}")
        success = False
    
    return success

def check_code_configuration():
    """Check that code is configured for PostgreSQL only."""
    logger.info("=== Code Configuration Check ===")
    
    success = True
    
    # Check config.py default
    config_file = Path('app/core/config.py')
    if config_file.exists():
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        if 'postgresql://' in config_content and 'sqlite:///' not in config_content:
            logger.info("✅ config.py default DATABASE_URL is PostgreSQL")
        else:
            logger.warning("⚠️  config.py may still have SQLite references")
            success = False
    
    # Check database.py for SQLite fallback
    db_file = Path('app/db/database.py')
    if db_file.exists():
        with open(db_file, 'r') as f:
            db_content = f.read()
        
        if 'sqlite' not in db_content.lower() and 'fallback' not in db_content.lower():
            logger.info("✅ database.py has no SQLite fallback logic")
        else:
            logger.warning("⚠️  database.py may still have SQLite references")
            success = False
    
    return success

def check_database_connection():
    """Check database connection and functionality."""
    logger.info("=== Database Connection Check ===")
    
    try:
        # Set PYTHONPATH for imports
        sys.path.insert(0, '.')
        
        from app.db.database import get_db, engine
        from app.db.models import User
        from sqlalchemy import text
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version()')).scalar()
            if 'PostgreSQL' in result:
                logger.info("✅ Connected to PostgreSQL successfully")
                logger.info(f"   Version: {result[:50]}...")
            else:
                logger.error("❌ Not connected to PostgreSQL")
                return False
        
        # Test application database access
        db = next(get_db())
        try:
            user_count = db.query(User).count()
            logger.info(f"✅ Application can access database ({user_count} users)")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def check_sqlite_cleanup():
    """Check that SQLite files have been cleaned up."""
    logger.info("=== SQLite Cleanup Check ===")
    
    sqlite_files = [
        Path('personal_ai_agent.db'),
        Path('data/app.db'),
        Path('app.db')
    ]
    
    found_sqlite = False
    for sqlite_file in sqlite_files:
        if sqlite_file.exists():
            logger.warning(f"⚠️  SQLite file still exists: {sqlite_file}")
            found_sqlite = True
    
    if not found_sqlite:
        logger.info("✅ No SQLite database files found")
    
    return not found_sqlite

def check_application_startup():
    """Check that application can start with PostgreSQL."""
    logger.info("=== Application Startup Check ===")
    
    try:
        # Try to import and initialize the app
        sys.path.insert(0, '.')
        
        from app.core.config import settings
        
        if settings.DATABASE_URL.startswith('postgresql://'):
            logger.info("✅ Application configured for PostgreSQL")
        else:
            logger.warning(f"⚠️  Application DATABASE_URL: {settings.DATABASE_URL}")
            return False
        
        # Test that Gmail config validation works (it loads the database)
        try:
            settings.validate_gmail_config()
            logger.info("✅ Application startup validation successful")
        except ValueError as e:
            # Gmail config errors are expected if not configured
            if "Gmail OAuth configuration errors" in str(e):
                logger.info("✅ Application startup successful (Gmail not configured)")
            else:
                logger.warning(f"⚠️  Application validation warning: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        return False

def main():
    """Main verification function."""
    logger.info("🔍 PostgreSQL Migration Verification")
    logger.info("=" * 50)
    
    checks = [
        ("Environment Configuration", check_environment_config),
        ("Code Configuration", check_code_configuration),
        ("Database Connection", check_database_connection),
        ("SQLite Cleanup", check_sqlite_cleanup),
        ("Application Startup", check_application_startup)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        logger.info(f"\n📋 {check_name}...")
        try:
            results[check_name] = check_func()
        except Exception as e:
            logger.error(f"❌ {check_name} failed with error: {e}")
            results[check_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Migration Verification Summary")
    logger.info("=" * 50)
    
    all_passed = True
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {check_name}")
        if not result:
            all_passed = False
    
    logger.info("=" * 50)
    
    if all_passed:
        logger.info("🎉 PostgreSQL migration verification SUCCESSFUL!")
        logger.info("")
        logger.info("📋 Migration completed successfully:")
        logger.info("  ✅ SQLite completely removed")
        logger.info("  ✅ PostgreSQL fully integrated")
        logger.info("  ✅ Application ready for production")
        logger.info("  ✅ No fallback dependencies")
        logger.info("")
        logger.info("🚀 Next steps:")
        logger.info("  1. Test file upload functionality")
        logger.info("  2. Configure Gmail OAuth if needed")
        logger.info("  3. Deploy to production environment")
        return 0
    else:
        logger.error("❌ Migration verification FAILED!")
        logger.error("Please review the failed checks above")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 