#!/usr/bin/env python3
"""
Script to create an admin user for the Personal AI Agent.
"""

import os
import sys
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.db.database import SessionLocal, engine, Base
from app.db.models import User

def create_admin_user(username, password, email):
    """Create an admin user"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
            return False
        
        # Create new user with admin privileges
        hashed_password = get_password_hash(password)
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_admin=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"Admin user '{username}' created successfully.")
        return True
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Create admin user
    username = "admin"
    password = "Iomaguire1"
    email = "admin@example.com"
    
    # Ensure the database tables exist
    Base.metadata.create_all(bind=engine)
    
    # Create the admin user
    create_admin_user(username, password, email) 