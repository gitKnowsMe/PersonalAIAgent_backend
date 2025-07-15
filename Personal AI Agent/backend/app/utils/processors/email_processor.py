"""
Email processor for the document processing pipeline.
Integrates email processing with existing document processor architecture.
"""

from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

from app.utils.processors.base_processor import BaseDocumentProcessor
from app.services.email.email_ingestion import EmailIngestionService
from app.services.email.email_classifier import EmailClassifier
from app.services.email.email_processor import EmailProcessor

logger = logging.getLogger(__name__)


class EmailDocumentProcessor(BaseDocumentProcessor):
    """Document processor for email files (.eml)."""
    
    def __init__(self):
        super().__init__()
        self.email_ingestion = EmailIngestionService()
        self.email_classifier = EmailClassifier()
        self.email_processor = EmailProcessor()
        
        # Email-specific processing configuration
        self.supported_extensions = ['.eml', '.msg']
        self.processing_type = 'email'
    
    async def process_file(self, file_path: str, user_id: int) -> Dict:
        """
        Process email file and return structured data.
        
        Args:
            file_path: Path to email file
            user_id: User ID for processing context
            
        Returns:
            Processing result dictionary
        """
        try:
            logger.info(f"Processing email file: {file_path}")
            
            # Parse email file
            email_data = await self.email_ingestion.parse_eml_file(file_path)
            
            # Classify email
            tags = await self.email_classifier.classify_email(email_data)
            email_data['classification_tags'] = tags
            
            # Generate email ID from message ID or file path
            email_id = self._generate_email_id(email_data, file_path)
            
            # Process email content for chunking and embedding
            chunks = await self.email_processor.process_email(email_data, user_id, tags)
            
            # Prepare result
            result = {
                'success': True,
                'email_id': email_id,
                'email_data': email_data,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'classification_tags': tags,
                'processing_type': self.processing_type,
                'metadata': {
                    'user_id': user_id,
                    'file_path': file_path,
                    'subject': email_data.get('subject', ''),
                    'sender': email_data.get('sender', ''),
                    'date': email_data.get('date'),
                    'has_attachments': len(email_data.get('attachments', [])) > 0
                }
            }
            
            logger.info(f"Successfully processed email: {email_data.get('subject', 'No subject')[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error processing email file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path,
                'processing_type': self.processing_type
            }
    
    async def process_content(self, content: bytes, user_id: int, filename: str = '') -> Dict:
        """
        Process email content from bytes.
        
        Args:
            content: Raw email content
            user_id: User ID for processing context
            filename: Optional filename for reference
            
        Returns:
            Processing result dictionary
        """
        try:
            logger.info(f"Processing email content: {filename}")
            
            # Parse email content
            email_data = await self.email_ingestion.parse_eml_content(content)
            
            # Classify email
            tags = await self.email_classifier.classify_email(email_data)
            email_data['classification_tags'] = tags
            
            # Generate email ID
            email_id = self._generate_email_id(email_data, filename)
            
            # Process email content
            chunks = await self.email_processor.process_email(email_data, user_id, tags)
            
            # Prepare result
            result = {
                'success': True,
                'email_id': email_id,
                'email_data': email_data,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'classification_tags': tags,
                'processing_type': self.processing_type,
                'metadata': {
                    'user_id': user_id,
                    'filename': filename,
                    'subject': email_data.get('subject', ''),
                    'sender': email_data.get('sender', ''),
                    'date': email_data.get('date'),
                    'has_attachments': len(email_data.get('attachments', [])) > 0
                }
            }
            
            logger.info(f"Successfully processed email content: {email_data.get('subject', 'No subject')[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error processing email content {filename}: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename,
                'processing_type': self.processing_type
            }
    
    def _generate_email_id(self, email_data: Dict, file_path: str) -> str:
        """Generate unique email ID."""
        # Try to use message ID first
        message_id = email_data.get('message_id', '').strip('<>')
        if message_id:
            # Clean message ID for use as filename
            email_id = message_id.replace('@', '_at_').replace('.', '_')
            # Limit length
            if len(email_id) > 100:
                email_id = email_id[:100]
            return email_id
        
        # Fall back to file-based ID
        file_path_obj = Path(file_path)
        base_name = file_path_obj.stem
        
        # Add timestamp if available
        date = email_data.get('date')
        if date:
            timestamp = int(date.timestamp())
            return f"{base_name}_{timestamp}"
        
        return base_name
    
    def supports_file(self, file_path: str) -> bool:
        """Check if processor supports this file type."""
        file_path_obj = Path(file_path)
        return file_path_obj.suffix.lower() in self.supported_extensions
    
    async def extract_content(self, file_path: str) -> str:
        """Extract text content from email file."""
        email_data = await self.email_ingestion.parse_eml_file(file_path)
        return email_data.get('body_text', '')
    
    def extract_format_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract email-specific metadata."""
        return {
            'format': 'email',
            'processor': 'EmailDocumentProcessor',
            'supports_attachments': True,
            'supports_threading': True
        }
    
    async def get_processing_stats(self) -> Dict:
        """Get processing statistics."""
        return {
            'processor_type': self.processing_type,
            'supported_extensions': self.supported_extensions,
            'features': [
                'email_parsing',
                'mime_support',
                'classification',
                'temporal_analysis',
                'sender_analysis',
                'attachment_detection'
            ]
        }