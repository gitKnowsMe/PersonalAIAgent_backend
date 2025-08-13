#!/usr/bin/env python3
"""
Migration script to convert to hybrid deployment architecture.
Moves user data from static/ to data/ and removes frontend files.
"""

import os
import shutil
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_user_data():
    """Migrate user uploads and emails from static/ to data/"""
    
    # Create data directories
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    uploads_dir = data_dir / "uploads"
    emails_dir = data_dir / "emails"
    
    uploads_dir.mkdir(exist_ok=True)
    emails_dir.mkdir(exist_ok=True)
    
    # Migrate uploads
    static_uploads = Path("static/uploads")
    if static_uploads.exists():
        logger.info(f"Migrating uploads from {static_uploads} to {uploads_dir}")
        
        # Copy all user directories
        for user_dir in static_uploads.iterdir():
            if user_dir.is_dir():
                dest_dir = uploads_dir / user_dir.name
                if dest_dir.exists():
                    logger.warning(f"Destination {dest_dir} already exists, skipping")
                    continue
                    
                shutil.copytree(user_dir, dest_dir)
                logger.info(f"Copied {user_dir} to {dest_dir}")
    
    # Migrate emails
    static_emails = Path("static/emails")
    if static_emails.exists():
        logger.info(f"Migrating emails from {static_emails} to {emails_dir}")
        
        # Copy all email files
        for email_file in static_emails.rglob("*"):
            if email_file.is_file():
                rel_path = email_file.relative_to(static_emails)
                dest_file = emails_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                if dest_file.exists():
                    logger.warning(f"Destination {dest_file} already exists, skipping")
                    continue
                    
                shutil.copy2(email_file, dest_file)
                logger.info(f"Copied {email_file} to {dest_file}")

def remove_frontend_files():
    """Remove frontend files that are no longer needed"""
    
    files_to_remove = [
        "static/css",
        "static/js", 
        "static/index.html",
        "static/error.html",
        "static/favicon.ico",
        "test_login_debug.html"
    ]
    
    for file_path in files_to_remove:
        path = Path(file_path)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                logger.info(f"Removed directory: {path}")
            else:
                path.unlink()
                logger.info(f"Removed file: {path}")
        else:
            logger.info(f"File not found (already removed): {path}")

def cleanup_empty_static():
    """Remove empty static directory if only uploads/emails remain"""
    
    static_dir = Path("static")
    if static_dir.exists():
        # After moving uploads and emails, check if static is empty or only has empty dirs
        remaining_items = list(static_dir.iterdir())
        
        # Remove empty uploads and emails directories
        for item in remaining_items:
            if item.is_dir() and not list(item.iterdir()):
                item.rmdir()
                logger.info(f"Removed empty directory: {item}")
        
        # Check if static is now empty
        if not list(static_dir.iterdir()):
            static_dir.rmdir()
            logger.info("Removed empty static directory")

def main():
    """Main migration function"""
    
    logger.info("Starting hybrid deployment migration...")
    
    try:
        # Step 1: Migrate user data
        migrate_user_data()
        
        # Step 2: Remove frontend files
        remove_frontend_files()
        
        # Step 3: Cleanup empty directories
        cleanup_empty_static()
        
        logger.info("Migration completed successfully!")
        logger.info("The backend is now configured for hybrid deployment.")
        logger.info("User data has been moved to data/ directory.")
        logger.info("Frontend files have been removed.")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    main()