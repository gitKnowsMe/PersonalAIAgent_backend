#!/usr/bin/env python3
"""
Script to migrate the database schema for the Personal AI Agent.
This adds the is_admin column to the users table.
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_database():
    """Add is_admin column to users table if it doesn't exist"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Check if the column exists
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='is_admin'
        """))
        
        if result.fetchone() is None:
            print("Adding is_admin column to users table...")
            connection.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_admin BOOLEAN DEFAULT FALSE
            """))
            connection.commit()
            print("Migration completed successfully.")
        else:
            print("Column is_admin already exists in users table.")

if __name__ == "__main__":
    migrate_database() 