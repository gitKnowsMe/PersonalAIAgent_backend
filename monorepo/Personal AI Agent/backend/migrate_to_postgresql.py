#!/usr/bin/env python3
"""
Migration script to move from SQLite to PostgreSQL

This script will:
1. Export existing SQLite data (if any)
2. Set up PostgreSQL
3. Import data to PostgreSQL
4. Update configuration files
"""

import logging
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def export_sqlite_data():
    """Export data from existing SQLite databases."""
    logger.info("=== Exporting SQLite Data ===")
    
    base_dir = Path(__file__).parent
    db_locations = [
        base_dir / "personal_ai_agent.db",
        base_dir / "data" / "app.db"
    ]
    
    exported_data = {}
    
    for db_path in db_locations:
        if db_path.exists():
            logger.info(f"Exporting from: {db_path}")
            try:
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables = [row[0] for row in cursor.fetchall()]
                
                db_data = {}
                for table in tables:
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    db_data[table] = [dict(row) for row in rows]
                    logger.info(f"  - Exported {len(rows)} rows from {table}")
                
                exported_data[str(db_path)] = db_data
                conn.close()
                
            except sqlite3.Error as e:
                logger.error(f"Error exporting from {db_path}: {e}")
    
    # Save exported data
    if exported_data:
        export_file = base_dir / f"sqlite_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(exported_data, f, indent=2, default=str)
        logger.info(f"Data exported to: {export_file}")
        return export_file
    else:
        logger.info("No SQLite data found to export")
        return None

def cleanup_sqlite_files():
    """Remove SQLite database files after successful migration."""
    logger.info("=== Cleaning up SQLite files ===")
    
    base_dir = Path(__file__).parent
    sqlite_files = [
        base_dir / "personal_ai_agent.db",
        base_dir / "data" / "app.db",
        base_dir / "app.db"
    ]
    
    for file_path in sqlite_files:
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Removed: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}")

def update_start_backend_script():
    """Update start_backend.py to use PostgreSQL defaults."""
    logger.info("=== Updating start_backend.py ===")
    
    script_path = Path(__file__).parent / "start_backend.py"
    if script_path.exists():
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Update the default .env creation
        old_db_url = 'DATABASE_URL=sqlite:///./personal_ai_agent.db'
        new_db_url = 'DATABASE_URL=postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev'
        
        if old_db_url in content:
            content = content.replace(old_db_url, new_db_url)
            with open(script_path, 'w') as f:
                f.write(content)
            logger.info("Updated start_backend.py with PostgreSQL defaults")
        else:
            logger.info("start_backend.py already updated or not found")

def main():
    """Main migration function."""
    logger.info("🔄 SQLite to PostgreSQL Migration")
    logger.info("=" * 50)
    
    # Step 1: Export existing SQLite data
    export_file = export_sqlite_data()
    
    # Step 2: Setup PostgreSQL (user should run setup_postgresql.py)
    logger.info("\n📋 Next steps:")
    logger.info("1. Install PostgreSQL if not already installed")
    logger.info("2. Run: python setup_postgresql.py")
    logger.info("3. Restart the application")
    
    if export_file:
        logger.info(f"4. Your SQLite data has been exported to: {export_file}")
        logger.info("   You can import this data manually if needed")
    
    # Step 3: Update configuration files
    update_start_backend_script()
    
    # Ask user if they want to clean up SQLite files
    response = input("\nRemove SQLite database files? (y/N): ")
    if response.lower() == 'y':
        cleanup_sqlite_files()
    
    logger.info("\n🎉 Migration preparation completed!")
    logger.info("Run 'python setup_postgresql.py' to complete the setup")

if __name__ == "__main__":
    main() 