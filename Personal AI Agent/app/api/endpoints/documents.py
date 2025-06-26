import os
import shutil
import traceback
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Document, User
from app.schemas.document import DocumentCreate, DocumentResponse
from app.utils.document_processor import process_document

# Get the logger
logger = logging.getLogger("personal_ai_agent")

router = APIRouter()

@router.post("/documents", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def upload_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new document
    """
    logger.info(f"Document upload attempt by user {current_user.username}: {title}")
    
    try:
        # Check file size
        file_size = 0
        contents = await file.read()
        file_size = len(contents)
        await file.seek(0)
        
        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(f"Upload failed: File too large ({file_size} bytes) for user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Create user directory if it doesn't exist
        user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(user_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create unique vector namespace
        vector_namespace = f"user_{current_user.id}_doc_{title.replace(' ', '_')}"
        
        # Create document record
        new_document = Document(
            title=title,
            description=description,
            file_path=file_path,
            file_type=file.content_type,
            file_size=file_size,
            owner_id=current_user.id,
            vector_namespace=vector_namespace
        )
        
        db.add(new_document)
        db.commit()
        db.refresh(new_document)
                
        # Process document in background
        await process_document(new_document, current_user)
                
        logger.info(f"Document upload successful: ID {new_document.id}, title '{title}', by user {current_user.username}")
        
        return new_document
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}, title '{title}', by user {current_user.username}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/documents", response_model=List[DocumentResponse])
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all documents for the current user
    """
    logger.info(f"Retrieving documents for user {current_user.username}")
    
    documents = db.query(Document).filter(Document.owner_id == current_user.id).all()
    return documents

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID
    """
    logger.info(f"Retrieving document ID {document_id} for user {current_user.username}")
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    
    if not document:
        logger.warning(f"Document not found: ID {document_id}, requested by user {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document by ID
    """
    logger.info(f"Delete attempt for document ID {document_id} by user {current_user.username}")
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    
    if not document:
        logger.warning(f"Document not found for deletion: ID {document_id}, requested by user {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete the file if it exists
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            logger.error(f"Error deleting document file: {str(e)}, document ID {document_id}")
    
    # Delete the document from the database
    db.delete(document)
    db.commit()
    
    logger.info(f"Document deleted successfully: ID {document_id}, title '{document.title}', by user {current_user.username}")
    
    return None 