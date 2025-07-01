#!/usr/bin/env python3
"""
Script to safely clean up deprecated and unnecessary files from the Personal AI Agent project.
This script removes files that have been identified as safe to delete during the security audit.
"""

import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).parent

# Files and directories to delete
FILES_TO_DELETE = [
    # Deprecated/Old Files
    "app/utils/ai_config_old.py",
    "app/utils/pdf_processor.py.old", 
    "app/utils/text_processor.py.old",
    "app/utils/vector_store_old.py",
    
    # Development/Temporary Files
    "notes.txt",
    "db_config.txt", 
    "performance_improvements.txt",
    "test3_monthly expenses.txt",
    
    # Log files (should be regenerated)
    "logs/app.log",
]

DIRECTORIES_TO_DELETE = [
    # Python cache directories
    "app/core/__pycache__",
    "app/utils/__pycache__",
    "app/api/__pycache__",
    "app/services/__pycache__",
    "app/db/__pycache__",
    "app/schemas/__pycache__",
    "app/api/endpoints/__pycache__",
]

def backup_file(file_path):
    """Create a backup of a file before deletion"""
    backup_path = f"{file_path}.backup"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backed up {file_path} to {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to backup {file_path}: {e}")
        return False

def delete_file(file_path):
    """Safely delete a file"""
    full_path = BASE_DIR / file_path
    
    if not full_path.exists():
        logger.info(f"File not found (already deleted?): {file_path}")
        return True
    
    try:
        # For important files, create backup first
        if file_path in ["db_config.txt", "performance_improvements.txt"]:
            backup_file(full_path)
        
        full_path.unlink()
        logger.info(f"✅ Deleted file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete {file_path}: {e}")
        return False

def delete_directory(dir_path):
    """Safely delete a directory and its contents"""
    full_path = BASE_DIR / dir_path
    
    if not full_path.exists():
        logger.info(f"Directory not found (already deleted?): {dir_path}")
        return True
    
    try:
        shutil.rmtree(full_path)
        logger.info(f"✅ Deleted directory: {dir_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete directory {dir_path}: {e}")
        return False

def update_gitignore():
    """Update .gitignore to prevent future cache/log file commits"""
    gitignore_path = BASE_DIR / ".gitignore"
    
    additional_entries = [
        "\n# Python cache files",
        "__pycache__/",
        "*.pyc",
        "*.pyo", 
        "*.pyd",
        "",
        "# Log files",
        "logs/*.log",
        "*.log",
        "",
        "# Development files",
        "notes.txt",
        "db_config.txt",
        "performance_improvements.txt",
        "",
        "# Backup files", 
        "*.backup",
        "*.old",
    ]
    
    try:
        # Read existing .gitignore
        existing_content = ""
        if gitignore_path.exists():
            existing_content = gitignore_path.read_text()
        
        # Check if entries already exist
        new_entries = []
        for entry in additional_entries:
            if entry.strip() and entry not in existing_content:
                new_entries.append(entry)
        
        if new_entries:
            # Append new entries
            with open(gitignore_path, "a") as f:
                f.write("\n".join(new_entries))
            logger.info("✅ Updated .gitignore with additional entries")
        else:
            logger.info("✅ .gitignore already contains necessary entries")
            
    except Exception as e:
        logger.error(f"❌ Failed to update .gitignore: {e}")

def main():
    """Main cleanup function"""
    logger.info("Starting deprecated file cleanup...")
    
    deleted_files = 0
    deleted_dirs = 0
    
    # Delete files
    logger.info("\n--- Deleting Files ---")
    for file_path in FILES_TO_DELETE:
        if delete_file(file_path):
            deleted_files += 1
    
    # Delete directories  
    logger.info("\n--- Deleting Directories ---")
    for dir_path in DIRECTORIES_TO_DELETE:
        if delete_directory(dir_path):
            deleted_dirs += 1
    
    # Update .gitignore
    logger.info("\n--- Updating .gitignore ---")
    update_gitignore()
    
    # Summary
    logger.info("\n--- Cleanup Summary ---")
    logger.info(f"✅ Files deleted: {deleted_files}/{len(FILES_TO_DELETE)}")
    logger.info(f"✅ Directories deleted: {deleted_dirs}/{len(DIRECTORIES_TO_DELETE)}")
    
    if deleted_files == len(FILES_TO_DELETE) and deleted_dirs == len(DIRECTORIES_TO_DELETE):
        logger.info("🎉 Cleanup completed successfully!")
    else:
        logger.warning("⚠️ Some files/directories could not be deleted. Check logs above.")
    
    logger.info("\nNOTE: Backup files (.backup) have been created for important files.")
    logger.info("You can safely delete these backup files after verifying the cleanup.")

if __name__ == "__main__":
    main()