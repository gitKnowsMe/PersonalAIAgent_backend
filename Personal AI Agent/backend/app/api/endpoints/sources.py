"""
Sources API endpoints for retrieving available query sources.
Provides unified access to documents and email categories.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.services.source_service import get_source_service

logger = logging.getLogger("personal_ai_agent")

router = APIRouter()


@router.get("/sources", response_model=List[Dict[str, Any]])
async def get_available_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all available sources for querying
    
    Returns a list of available sources including:
    - All Sources (search everything)
    - Individual documents
    - Email categories (business, personal, etc.)
    """
    try:
        logger.info(f"Getting available sources for user {current_user.username}")
        
        source_service = get_source_service()
        sources = await source_service.get_available_sources(current_user.id, db)
        
        logger.info(f"Found {len(sources)} available sources for user {current_user.username}")
        return sources
        
    except Exception as e:
        logger.error(f"Error getting available sources for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available sources"
        ) 