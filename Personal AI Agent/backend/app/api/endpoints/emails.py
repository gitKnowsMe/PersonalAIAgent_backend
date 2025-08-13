"""
Email API endpoints for uploading, processing, and querying emails.
Provides comprehensive email management capabilities for the RAG system.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import json

from app.api.dependencies import get_current_user, get_db
from app.db.models import User, Email, EmailAccount, EmailAttachment, Query
from app.schemas.email import (
    EmailResponse, EmailUploadResponse, EmailQueryRequest, EmailQueryResponse,
    EmailAccountResponse, EmailStatsResponse, EmailSearchRequest
)
from app.services.email import (
    EmailIngestionService, EmailClassifier, EmailProcessor, 
    EmailStore, EmailQueryService
)
from app.utils.processors.email_processor import EmailDocumentProcessor
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/emails", tags=["emails"])

# Initialize email services
email_ingestion = EmailIngestionService()
email_classifier = EmailClassifier()
email_processor_service = EmailProcessor()
email_store = EmailStore()
email_query_service = EmailQueryService()
email_document_processor = EmailDocumentProcessor()


@router.post("/upload", response_model=EmailUploadResponse)
async def upload_email_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and process .eml email file.
    
    Args:
        file: .eml email file
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Upload and processing result
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.eml'):
            raise HTTPException(
                status_code=400,
                detail="Only .eml files are supported"
            )
        
        # Check file size
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=400,
                detail="Email file too large (max 50MB)"
            )
        
        # Process email in background
        background_tasks.add_task(
            process_email_background,
            content=content,
            filename=file.filename,
            user_id=current_user.id
        )
        
        return EmailUploadResponse(
            success=True,
            message=f"Email '{file.filename}' uploaded successfully and is being processed",
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading email file: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while uploading email"
        )


@router.post("/query", response_model=EmailQueryResponse)
async def query_emails(
    request: EmailQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Query emails using natural language.
    
    Args:
        request: Email query request
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Query results and generated response
    """
    try:
        # Process email query
        result = await email_query_service.process_email_query(
            query=request.query,
            user_id=current_user.id,
            max_results=request.max_results or 10
        )
        
        # Log query
        try:
            db_query = Query(
                question=request.query,
                answer=result['answer'],
                user_id=current_user.id
            )
            db.add(db_query)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to log email query: {e}")
            db.rollback()
        
        return EmailQueryResponse(
            answer=result['answer'],
            results=result['results'],
            query_analysis=result['query_analysis'],
            result_count=result['result_count']
        )
        
    except Exception as e:
        logger.error(f"Error processing email query: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing query"
        )


@router.post("/search", response_model=List[Dict[str, Any]])
async def search_emails(
    request: EmailSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Advanced email search with filters.
    
    Args:
        request: Search request with filters
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of matching email chunks
    """
    try:
        from app.services.embedding_service import SentenceTransformerEmbeddingService
        embedding_service = SentenceTransformerEmbeddingService()
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(request.query)
        
        # Prepare date range
        date_range = None
        if request.start_date and request.end_date:
            date_range = (request.start_date, request.end_date)
        
        # Search emails
        results = email_store.search_emails(
            query_embedding=query_embedding,
            user_id=current_user.id,
            tags=request.categories,
            date_range=date_range,
            sender_filter=request.sender,
            k=request.max_results or 20
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while searching emails"
        )


@router.get("/stats", response_model=EmailStatsResponse)
async def get_email_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get email statistics for current user.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Email statistics and analytics
    """
    try:
        # Get database stats
        total_emails = db.query(Email).filter(Email.user_id == current_user.id).count()
        total_accounts = db.query(EmailAccount).filter(EmailAccount.user_id == current_user.id).count()
        total_attachments = db.query(EmailAttachment).filter(EmailAttachment.user_id == current_user.id).count()
        
        # Get recent emails count
        recent_date = datetime.now() - timedelta(days=30)
        recent_emails = db.query(Email).filter(
            Email.user_id == current_user.id,
            Email.sent_at >= recent_date
        ).count()
        
        # Get vector store stats
        vector_stats = email_store.get_email_stats(current_user.id)
        
        return EmailStatsResponse(
            total_emails=total_emails,
            total_accounts=total_accounts,
            total_attachments=total_attachments,
            recent_emails=recent_emails,
            vector_stats=vector_stats
        )
        
    except Exception as e:
        logger.error(f"Error getting email stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting statistics"
        )


@router.get("/accounts", response_model=List[EmailAccountResponse])
async def get_email_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's email accounts.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of user's email accounts
    """
    try:
        accounts = db.query(EmailAccount).filter(
            EmailAccount.user_id == current_user.id
        ).all()
        
        return [
            EmailAccountResponse(
                id=account.id,
                email_address=account.email_address,
                provider=account.provider,
                is_active=account.is_active,
                sync_enabled=account.sync_enabled,
                last_sync_at=account.last_sync_at,
                created_at=account.created_at
            )
            for account in accounts
        ]
        
    except Exception as e:
        logger.error(f"Error getting email accounts: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting email accounts"
        )


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific email by ID.
    
    Args:
        email_id: Email ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Email details
    """
    try:
        email = db.query(Email).filter(
            Email.id == email_id,
            Email.user_id == current_user.id
        ).first()
        
        if not email:
            raise HTTPException(
                status_code=404,
                detail="Email not found"
            )
        
        return EmailResponse(
            id=email.id,
            subject=email.subject,
            sender_email=email.sender_email,
            sender_name=email.sender_name,
            recipient_emails=json.loads(email.recipient_emails or "[]"),
            body_text=email.body_text,
            body_html=email.body_html,
            email_type=email.email_type,
            has_attachments=email.has_attachments,
            sent_at=email.sent_at,
            created_at=email.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email {email_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while getting email"
        )


@router.delete("/{email_id}")
async def delete_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete email by ID.
    
    Args:
        email_id: Email ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    try:
        email = db.query(Email).filter(
            Email.id == email_id,
            Email.user_id == current_user.id
        ).first()
        
        if not email:
            raise HTTPException(
                status_code=404,
                detail="Email not found"
            )
        
        # Delete from vector store
        if email.vector_namespace:
            email_store.delete_email(current_user.id, str(email_id))
        
        # Delete from database
        db.delete(email)
        db.commit()
        
        return {"message": "Email deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting email {email_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal server error while deleting email"
        )


async def process_email_background(
    content: bytes,
    filename: str,
    user_id: int
):
    """
    Background task to process uploaded email.
    
    Args:
        content: Email file content
        filename: Original filename
        user_id: User ID
    """
    from app.db.session_manager import background_session
    
    try:
        logger.info(f"Processing email background task: {filename}")
        
        # Process email content (outside database session)
        result = await email_document_processor.process_content(
            content=content,
            user_id=user_id,
            filename=filename
        )
        
        if not result['success']:
            logger.error(f"Failed to process email {filename}: {result.get('error')}")
            return
        
        # Store in vector database (outside database session)
        chunks = result['chunks']
        email_id = result['email_id']
        
        if chunks:
            success = email_store.store_email_chunks(chunks, user_id, email_id)
            if not success:
                logger.error(f"Failed to store email chunks for {filename}")
                return
        
        # Store email metadata in database (with proper session management)
        with background_session() as db:
            email_data = result['email_data']
            
            db_email = Email(
                user_id=user_id,
                message_id=email_data.get('message_id', email_id),
                subject=email_data.get('subject', ''),
                sender_email=email_data.get('sender', ''),
                recipient_emails=json.dumps([email_data.get('recipient', '')]),
                body_text=email_data.get('body_text', ''),
                body_html=email_data.get('body_html', ''),
                email_type='generic',  # Could be enhanced with classification
                has_attachments=len(email_data.get('attachments', [])) > 0,
                sent_at=email_data.get('date') or datetime.now(),
                vector_namespace=f"user_{user_id}_email_{email_id}"
            )
            
            db.add(db_email)
            # Session is automatically committed by the context manager
        
        logger.info(f"Successfully processed email {filename}")
        
    except Exception as e:
        logger.error(f"Error in background email processing: {e}")
        # Session rollback is handled automatically by the context manager