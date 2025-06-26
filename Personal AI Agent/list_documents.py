#!/usr/bin/env python3
"""
Script to list all documents in the database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Document, User
from app.core.config import settings

def main():
    """List all documents in the database"""
    # Create database engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get all documents
        documents = db.query(Document).all()
        
        print(f"Found {len(documents)} documents:")
        print("-" * 80)
        
        for doc in documents:
            user = db.query(User).filter(User.id == doc.owner_id).first()
            username = user.username if user else "Unknown"
            
            print(f"ID: {doc.id}")
            print(f"Title: {doc.title}")
            print(f"File Path: {doc.file_path}")
            print(f"Vector Namespace: {doc.vector_namespace}")
            print(f"Owner: {username} (ID: {doc.owner_id})")
            print(f"Created: {doc.created_at}")
            print("-" * 80)
    
    finally:
        db.close()

if __name__ == "__main__":
    main() 