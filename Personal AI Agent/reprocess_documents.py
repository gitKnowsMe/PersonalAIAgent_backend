#!/usr/bin/env python3
"""
Script to reprocess all documents for a user with the updated chunking strategy.
"""

import os
import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Document, User
from app.utils.document_processor import process_document
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("reprocess_documents")

async def reprocess_documents(user_id):
    """Reprocess all documents for a user"""
    # Create database engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found")
            return
        
        # Get all documents for user
        documents = db.query(Document).filter(Document.owner_id == user_id).all()
        
        if not documents:
            logger.info(f"No documents found for user {user.username}")
            return
        
        logger.info(f"Found {len(documents)} documents for user {user.username}")
        
        # Process each document
        for document in documents:
            logger.info(f"Reprocessing document: {document.title} (ID: {document.id})")
            
            # Delete existing vector store files
            vector_namespace = document.vector_namespace
            index_path = os.path.join(settings.VECTOR_DB_PATH, f"{vector_namespace}.index")
            docmap_path = os.path.join(settings.VECTOR_DB_PATH, f"{vector_namespace}.pkl")
            
            if os.path.exists(index_path):
                os.remove(index_path)
                logger.info(f"Deleted existing index file: {index_path}")
            
            if os.path.exists(docmap_path):
                os.remove(docmap_path)
                logger.info(f"Deleted existing document map file: {docmap_path}")
            
            # Reprocess document
            try:
                await process_document(document, user)
                logger.info(f"Successfully reprocessed document: {document.title}")
            except Exception as e:
                logger.error(f"Error reprocessing document {document.id}: {str(e)}")
    
    finally:
        db.close()

async def main():
    """Main function"""
    logger.info("Starting document reprocessing")
    
    # User ID to reprocess documents for
    user_id = 3  # Change this to the appropriate user ID
    
    await reprocess_documents(user_id)
    
    logger.info("Document reprocessing complete")

if __name__ == "__main__":
    asyncio.run(main()) 