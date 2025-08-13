"""
Source Service - Unified Source Management

Provides centralized management of available sources for querying,
including documents and email categories.
"""

import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Document, Email, EmailAccount
from app.core.constants import EMAIL_TYPES

logger = logging.getLogger("personal_ai_agent")


class SourceItem:
    """Represents a queryable source item"""
    
    def __init__(self, source_type: str, source_id: Optional[str], display_name: str, 
                 description: Optional[str] = None, count: Optional[int] = None,
                 source_category: Optional[str] = None):
        self.source_type = source_type  # 'document', 'email_type', 'all'
        self.source_id = source_id      # document_id, email_type, or None for 'all'
        self.display_name = display_name
        self.description = description
        self.count = count
        self.source_category = source_category  # 'documents', 'emails', 'all'


class SourceService:
    """Service for managing available sources for querying"""
    
    def __init__(self):
        self.email_type_labels = {
            'business': 'Business Emails',
            'personal': 'Personal Emails', 
            'promotional': 'Promotional Emails',
            'transactional': 'Transactional Emails',
            'support': 'Support Emails',
            'generic': 'Other Emails'
        }
        
        self.email_type_descriptions = {
            'business': 'Work communications, meetings, projects',
            'personal': 'Family and friends communications',
            'promotional': 'Marketing, newsletters, deals',
            'transactional': 'Receipts, confirmations, notifications',
            'support': 'Customer service, technical support',
            'generic': 'General and uncategorized emails'
        }
    
    async def get_available_sources(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        Get all available sources for a user
        
        Args:
            user_id: User ID
            db: Database session
            
        Returns:
            List of available sources organized by category
        """
        try:
            sources = []
            
            # Add "All Sources" option first
            sources.append({
                'source_type': 'all',
                'source_id': None,
                'display_name': 'All Sources',
                'description': 'Search across all documents and emails',
                'count': None,
                'source_category': 'all'
            })
            
            # Get user's documents
            document_sources = await self._get_document_sources(user_id, db)
            sources.extend(document_sources)
            
            # Get user's email sources
            email_sources = await self._get_email_sources(user_id, db)
            sources.extend(email_sources)
            
            return sources
            
        except Exception as e:
            logger.error(f"Error getting available sources for user {user_id}: {e}")
            return []
    
    async def _get_document_sources(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get document sources for a user"""
        try:
            documents = db.query(Document).filter(Document.owner_id == user_id).all()
            
            if not documents:
                return []
            
            sources = []
            
            # Add individual documents
            for doc in documents:
                # Get category info for display
                category_info = self._get_document_category_info(doc.document_type)
                
                sources.append({
                    'source_type': 'document',
                    'source_id': str(doc.id),
                    'display_name': doc.title,
                    'description': f"{category_info['label']} • {doc.description or 'No description'}",
                    'count': None,
                    'source_category': 'documents'
                })
            
            return sources
            
        except Exception as e:
            logger.error(f"Error getting document sources: {e}")
            return []
    
    async def _get_email_sources(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get email sources for a user"""
        try:
            # Check if user has any emails
            has_emails = db.query(Email).filter(Email.user_id == user_id).first() is not None
            
            if not has_emails:
                return []
            
            sources = []
            
            # Add "All Emails" option
            total_emails = db.query(Email).filter(Email.user_id == user_id).count()
            sources.append({
                'source_type': 'email_type',
                'source_id': 'all',
                'display_name': 'All Emails',
                'description': f'All email communications ({total_emails} emails)',
                'count': total_emails,
                'source_category': 'emails'
            })
            
            # Add email type categories with counts
            for email_type in EMAIL_TYPES:
                count = db.query(Email).filter(
                    Email.user_id == user_id,
                    Email.email_type == email_type
                ).count()
                
                if count > 0:  # Only include types that have emails
                    sources.append({
                        'source_type': 'email_type',
                        'source_id': email_type,
                        'display_name': self.email_type_labels.get(email_type, email_type.title()),
                        'description': f"{self.email_type_descriptions.get(email_type, '')} ({count} emails)",
                        'count': count,
                        'source_category': 'emails'
                    })
            
            return sources
            
        except Exception as e:
            logger.error(f"Error getting email sources: {e}")
            return []
    
    def _get_document_category_info(self, document_type: str) -> Dict[str, str]:
        """Get display information for document category"""
        category_map = {
            'financial': {
                'label': 'Financial',
                'icon': '💰',
                'description': 'Bank statements, invoices, receipts'
            },
            'long_form': {
                'label': 'Long-form',
                'icon': '📚',
                'description': 'Research papers, reports, contracts'
            },
            'generic': {
                'label': 'Generic',
                'icon': '📄',
                'description': 'General documents'
            }
        }
        
        return category_map.get(document_type, {
            'label': document_type.title(),
            'icon': '📄',
            'description': 'Document'
        })
    
    async def validate_source_selection(self, source_type: str, source_id: Optional[str], 
                                      user_id: int, db: Session) -> bool:
        """
        Validate that a source selection is valid for the user
        
        Args:
            source_type: Type of source ('all', 'document', 'email_type')
            source_id: ID of the source (document_id, email_type, or None)
            user_id: User ID
            db: Database session
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if source_type == 'all':
                return source_id is None
            
            elif source_type == 'document':
                if not source_id:
                    return False
                
                # Check if document exists and belongs to user
                document = db.query(Document).filter(
                    Document.id == int(source_id),
                    Document.owner_id == user_id
                ).first()
                return document is not None
            
            elif source_type == 'email_type':
                if source_id == 'all':
                    # Check if user has any emails
                    return db.query(Email).filter(Email.user_id == user_id).first() is not None
                
                elif source_id in EMAIL_TYPES:
                    # Check if user has emails of this type
                    return db.query(Email).filter(
                        Email.user_id == user_id,
                        Email.email_type == source_id
                    ).first() is not None
                
                return False
            
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error validating source selection: {e}")
            return False
    
    def parse_source_selection(self, source_type: str, source_id: Optional[str]) -> Dict[str, Any]:
        """
        Parse source selection into parameters for query processing
        
        Args:
            source_type: Type of source
            source_id: ID of the source
            
        Returns:
            Dictionary with query parameters
        """
        params = {
            'document_id': None,
            'email_type_filter': None,
            'search_documents': True,
            'search_emails': True
        }
        
        if source_type == 'all':
            # Search everything
            params['search_documents'] = True
            params['search_emails'] = True
        
        elif source_type == 'document':
            # Search specific document only
            params['document_id'] = int(source_id) if source_id else None
            params['search_documents'] = True
            params['search_emails'] = False
        
        elif source_type == 'email_type':
            # Search emails only
            params['search_documents'] = False
            params['search_emails'] = True
            
            if source_id != 'all':
                params['email_type_filter'] = source_id
        
        return params


# Global instance
source_service = SourceService()


def get_source_service() -> SourceService:
    """Get the global source service instance"""
    return source_service 