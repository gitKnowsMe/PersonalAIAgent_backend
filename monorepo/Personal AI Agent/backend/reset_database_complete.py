#!/usr/bin/env python3
"""
Complete Database Reset Script

WARNING: This script will DELETE ALL DATA including:
- All users and their data
- All documents and uploaded files
- All emails and email data
- All vector store indices
- All OAuth sessions

Use this script when you want to start completely fresh.
"""

import logging
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def confirm_reset():
    """Ask user to confirm the destructive operation"""
    print("🚨 WARNING: DESTRUCTIVE OPERATION 🚨")
    print("=" * 50)
    print("This script will DELETE ALL DATA:")
    print("• All users and authentication data")
    print("• All uploaded documents and files")
    print("• All email data and connections")
    print("• All vector store indices")
    print("• All database records")
    print("=" * 50)
    print()
    
    response = input("Are you ABSOLUTELY SURE you want to proceed? Type 'DELETE ALL DATA' to confirm: ")
    return response == "DELETE ALL DATA"

def find_database_files() -> List[Path]:
    """Find all possible database files"""
    base_dir = Path(__file__).parent
    
    db_locations = [
        base_dir / "personal_ai_agent.db",
        base_dir / "data" / "app.db",
        base_dir / "app.db",
        base_dir / "data" / "personal_ai_agent.db"
    ]
    
    existing_dbs = []
    for db_path in db_locations:
        if db_path.exists():
            logger.info(f"Found database: {db_path}")
            existing_dbs.append(db_path)
    
    return existing_dbs

def delete_database_files():
    """Delete all database files"""
    logger.info("=== Deleting Database Files ===")
    
    db_files = find_database_files()
    
    if not db_files:
        logger.info("No database files found")
        return True
    
    for db_path in db_files:
        try:
            db_path.unlink()
            logger.info(f"Deleted database: {db_path}")
        except Exception as e:
            logger.error(f"Failed to delete {db_path}: {e}")
            return False
    
    return True

def delete_user_uploads():
    """Delete all user upload directories"""
    logger.info("=== Deleting User Uploads ===")
    
    upload_paths = [
        Path(__file__).parent / "data" / "uploads",
        Path(__file__).parent / "static" / "uploads"
    ]
    
    for upload_path in upload_paths:
        if upload_path.exists():
            try:
                shutil.rmtree(upload_path)
                logger.info(f"Deleted upload directory: {upload_path}")
            except Exception as e:
                logger.error(f"Failed to delete {upload_path}: {e}")
                return False
        else:
            logger.info(f"Upload directory not found: {upload_path}")
    
    return True

def delete_email_data():
    """Delete all email data"""
    logger.info("=== Deleting Email Data ===")
    
    email_paths = [
        Path(__file__).parent / "data" / "emails",
        Path(__file__).parent / "static" / "emails",
        Path(__file__).parent / "data" / "email_vectors"
    ]
    
    for email_path in email_paths:
        if email_path.exists():
            try:
                shutil.rmtree(email_path)
                logger.info(f"Deleted email directory: {email_path}")
            except Exception as e:
                logger.error(f"Failed to delete {email_path}: {e}")
                return False
        else:
            logger.info(f"Email directory not found: {email_path}")
    
    return True

def delete_vector_store():
    """Delete all vector store data"""
    logger.info("=== Deleting Vector Store Data ===")
    
    vector_paths = [
        Path(__file__).parent / "data" / "vector_db",
        Path(__file__).parent / "vector_db"
    ]
    
    for vector_path in vector_paths:
        if vector_path.exists():
            try:
                shutil.rmtree(vector_path)
                logger.info(f"Deleted vector store: {vector_path}")
            except Exception as e:
                logger.error(f"Failed to delete {vector_path}: {e}")
                return False
        else:
            logger.info(f"Vector store not found: {vector_path}")
    
    return True

def delete_log_files():
    """Delete log files"""
    logger.info("=== Deleting Log Files ===")
    
    log_paths = [
        Path(__file__).parent / "logs",
        Path(__file__).parent / "*.log"
    ]
    
    for log_path in log_paths:
        if log_path.exists():
            try:
                if log_path.is_dir():
                    shutil.rmtree(log_path)
                else:
                    log_path.unlink()
                logger.info(f"Deleted logs: {log_path}")
            except Exception as e:
                logger.error(f"Failed to delete {log_path}: {e}")
                return False
    
    # Delete individual log files
    base_dir = Path(__file__).parent
    for log_file in base_dir.glob("*.log"):
        try:
            log_file.unlink()
            logger.info(f"Deleted log file: {log_file}")
        except Exception as e:
            logger.error(f"Failed to delete {log_file}: {e}")
    
    return True

def recreate_data_directories():
    """Recreate the necessary data directories"""
    logger.info("=== Recreating Data Directories ===")
    
    directories = [
        Path(__file__).parent / "data",
        Path(__file__).parent / "data" / "uploads",
        Path(__file__).parent / "data" / "emails",
        Path(__file__).parent / "data" / "vector_db",
        Path(__file__).parent / "data" / "email_vectors",
        Path(__file__).parent / "logs"
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Failed to create {directory}: {e}")
            return False
    
    return True

def initialize_fresh_database():
    """Initialize a fresh database with tables"""
    logger.info("=== Initializing Fresh Database ===")
    
    try:
        # Import database modules
        from app.db.database import Base, engine
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Fresh database initialized with all tables")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def main():
    """Main reset function"""
    logger.info("🔄 Personal AI Agent - Complete Database Reset")
    logger.info("=" * 60)
    
    # Confirm the destructive operation
    if not confirm_reset():
        logger.info("❌ Operation cancelled by user")
        sys.exit(0)
    
    logger.info("🚀 Starting complete database reset...")
    
    operations = [
        ("Deleting database files", delete_database_files),
        ("Deleting user uploads", delete_user_uploads),
        ("Deleting email data", delete_email_data),
        ("Deleting vector store", delete_vector_store),
        ("Deleting log files", delete_log_files),
        ("Recreating directories", recreate_data_directories),
        ("Initializing fresh database", initialize_fresh_database)
    ]
    
    failed_operations = []
    
    for operation_name, operation_func in operations:
        logger.info(f"\n📋 {operation_name}...")
        try:
            success = operation_func()
            if success:
                logger.info(f"✅ {operation_name} completed successfully")
            else:
                logger.error(f"❌ {operation_name} failed")
                failed_operations.append(operation_name)
        except Exception as e:
            logger.error(f"❌ {operation_name} failed with error: {e}")
            failed_operations.append(operation_name)
    
    # Summary
    logger.info("\n" + "=" * 60)
    if not failed_operations:
        logger.info("🎉 Complete database reset completed successfully!")
        logger.info("\n📋 What was reset:")
        logger.info("  ✅ All database records deleted")
        logger.info("  ✅ All user files removed")
        logger.info("  ✅ All email data cleared")
        logger.info("  ✅ All vector indices removed")
        logger.info("  ✅ Fresh database initialized")
        logger.info("\n🚀 You can now start fresh with a clean system!")
        logger.info("💡 Create a new admin user with: python create_admin.py")
    else:
        logger.error("❌ Some operations failed:")
        for failed_op in failed_operations:
            logger.error(f"  • {failed_op}")
        logger.error("\n⚠️  Manual cleanup may be required for failed operations")
        sys.exit(1)

if __name__ == "__main__":
    main() 