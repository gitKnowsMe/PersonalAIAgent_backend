"""
Document Content Service - Access and parse user documents by type
"""

import os
import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.db.models import Document

logger = logging.getLogger("personal_ai_agent")

class DocumentContentService:
    """Service for accessing and parsing user document content"""
    
    def __init__(self):
        self.document_type_keywords = {
            'expense': ['expense', 'expenses', 'monthly', 'budget', 'spent', 'cost'],
            'resume': ['resume', 'cv', 'skill', 'experience', 'engineer'],
            'travel': ['vacation', 'travel', 'trip', 'thailand', 'holiday'],
            'prompt': ['prompt', 'ai', 'llm', 'engineering']
        }
    
    def get_user_documents(self, user_id: int, db: Session) -> List[Document]:
        """Get all documents for a user"""
        try:
            documents = db.query(Document).filter(Document.owner_id == user_id).all()
            return documents
        except Exception as e:
            logger.error(f"Error getting user documents: {e}")
            return []
    
    def get_document_content(self, document: Document) -> Optional[str]:
        """Read content from a document file"""
        try:
            file_path = document.file_path if hasattr(document, 'file_path') else document.path
            if not os.path.exists(file_path):
                logger.warning(f"Document file not found: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content
                
        except Exception as e:
            file_path = document.file_path if hasattr(document, 'file_path') else document.path
            logger.error(f"Error reading document {file_path}: {e}")
            return None
    
    def get_user_document_by_type(self, user_id: int, doc_type: str, db: Session) -> Optional[str]:
        """Get content of first document matching the specified type"""
        try:
            documents = self.get_user_documents(user_id, db)
            keywords = self.document_type_keywords.get(doc_type, [])
            
            for document in documents:
                # Check title first (contains original filename), then basename as fallback
                filename = document.title if document.title else ""
                if not filename and document.file_path:
                    filename = os.path.basename(document.file_path)
                
                filename_lower = filename.lower()
                
                # Check filename for type keywords
                if any(keyword in filename_lower for keyword in keywords):
                    content = self.get_document_content(document)
                    if content:
                        logger.info(f"Found {doc_type} document: {filename}")
                        return content
            
            # If no filename match, check content
            for document in documents:
                content = self.get_document_content(document)
                if content:
                    content_lower = content.lower()
                    if any(keyword in content_lower for keyword in keywords):
                        # Extract filename for logging
                        filename = ""
                        if document.file_path:
                            filename = os.path.basename(document.file_path)
                        elif document.title:
                            filename = document.title
                        logger.info(f"Found {doc_type} document by content: {filename}")
                        return content
            
            logger.warning(f"No {doc_type} document found for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting {doc_type} document for user {user_id}: {e}")
            return None
    
    def get_all_user_content(self, user_id: int, db: Session) -> List[str]:
        """Get content from all user documents"""
        try:
            documents = self.get_user_documents(user_id, db)
            contents = []
            
            for document in documents:
                content = self.get_document_content(document)
                if content:
                    contents.append(content)
            
            return contents
            
        except Exception as e:
            logger.error(f"Error getting all content for user {user_id}: {e}")
            return []
    
    def search_content_for_keywords(self, content: str, keywords: List[str]) -> bool:
        """Check if content contains any of the specified keywords"""
        if not content:
            return False
        
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in keywords)


# Global service instance
document_service = DocumentContentService()