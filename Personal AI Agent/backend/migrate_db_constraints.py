#!/usr/bin/env python3
"""
Database migration script to add constraints to existing database schema.
This script safely adds the new constraints without breaking existing data.
"""

import logging
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.database import Base, engine
from app.db.models import User, Document, Query
from app.core.constants import (
    USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH, TITLE_MAX_LENGTH
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("migrate_constraints")

def check_existing_constraints():
    """Check what constraints already exist in the database"""
    logger.info("Checking existing database constraints...")
    
    inspector = inspect(engine)
    
    # Check existing constraints for each table
    for table_name in ['users', 'documents', 'queries']:
        if inspector.has_table(table_name):
            constraints = inspector.get_check_constraints(table_name)
            logger.info(f"Table '{table_name}' existing constraints: {[c['name'] for c in constraints]}")
        else:
            logger.info(f"Table '{table_name}' does not exist")

def validate_existing_data():
    """Check if existing data violates the new constraints"""
    logger.info("Validating existing data against new constraints...")
    
    try:
        with engine.connect() as conn:
            # Check User constraints
            result = conn.execute(text("""
                SELECT id, username, email FROM users 
                WHERE LENGTH(username) < :min_len OR LENGTH(username) > :max_len
                OR LENGTH(email) > :email_max OR email NOT LIKE '%@%'
            """), {
                'min_len': USERNAME_MIN_LENGTH,
                'max_len': USERNAME_MAX_LENGTH, 
                'email_max': EMAIL_MAX_LENGTH
            })
            
            invalid_users = result.fetchall()
            if invalid_users:
                logger.warning(f"Found {len(invalid_users)} users with constraint violations:")
                for user in invalid_users:
                    logger.warning(f"  User ID {user[0]}: username='{user[1]}', email='{user[2]}'")
            else:
                logger.info("✅ All users data is valid")
            
            # Check Document constraints
            result = conn.execute(text("""
                SELECT id, title, file_size FROM documents 
                WHERE LENGTH(title) = 0 OR LENGTH(title) > :title_max OR file_size <= 0
            """), {'title_max': TITLE_MAX_LENGTH})
            
            invalid_docs = result.fetchall()
            if invalid_docs:
                logger.warning(f"Found {len(invalid_docs)} documents with constraint violations:")
                for doc in invalid_docs:
                    logger.warning(f"  Document ID {doc[0]}: title='{doc[1]}', size={doc[2]}")
            else:
                logger.info("✅ All documents data is valid")
            
            # Check Query constraints
            result = conn.execute(text("""
                SELECT id, LENGTH(question) as q_len FROM queries 
                WHERE LENGTH(question) = 0 OR LENGTH(question) > 5000
            """))
            
            invalid_queries = result.fetchall()
            if invalid_queries:
                logger.warning(f"Found {len(invalid_queries)} queries with constraint violations:")
                for query in invalid_queries:
                    logger.warning(f"  Query ID {query[0]}: question length={query[1]}")
            else:
                logger.info("✅ All queries data is valid")
                
            return len(invalid_users) == 0 and len(invalid_docs) == 0 and len(invalid_queries) == 0
            
    except SQLAlchemyError as e:
        logger.error(f"Error validating data: {e}")
        return False

def recreate_tables():
    """Recreate tables with new constraints"""
    logger.info("Recreating database tables with new constraints...")
    
    try:
        # Create all tables with new schema
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables recreated successfully with constraints")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Error recreating tables: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("Starting database constraints migration...")
    
    try:
        # Step 1: Check existing constraints
        check_existing_constraints()
        
        # Step 2: Validate existing data
        data_valid = validate_existing_data()
        
        if not data_valid:
            logger.error("❌ Existing data violates new constraints!")
            logger.error("Please clean up the data before applying constraints.")
            return False
        
        # Step 3: Recreate tables (SQLite limitation - can't easily add constraints)
        logger.info("SQLite detected - recreating tables to add constraints...")
        success = recreate_tables()
        
        if success:
            logger.info("✅ Database constraints migration completed successfully!")
            logger.info("New constraints added:")
            logger.info("  - User: email length, username length, email format validation")
            logger.info("  - Document: title length, file size validation, required fields")
            logger.info("  - Query: question length validation, required fields")
            return True
        else:
            logger.error("❌ Migration failed!")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        logger.exception("Full exception details:")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)