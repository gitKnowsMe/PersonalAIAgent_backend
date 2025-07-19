"""
Email Ingestion Service - Local Email RAG Workflow

Handles local email ingestion from .eml files and IMAP/POP3 clients
for privacy-focused, offline email processing and RAG integration.
"""

import os
import email
import logging
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
from email.utils import parsedate_to_datetime
import imaplib
import poplib
from html2text import html2text
import hashlib

from app.core.config import settings
from app.db.models import LocalEmail, EmailAttachment
from sqlalchemy.orm import Session

logger = logging.getLogger("personal_ai_agent")


class EmailIngestionService:
    """
    Local email ingestion service for .eml files and IMAP/POP3 clients.
    Designed for maximum privacy and offline functionality.
    """
    
    def __init__(self):
        self.supported_formats = ['.eml', '.msg']
        self.attachment_storage_path = Path(settings.DATA_DIR) / "email_attachments"
        self.attachment_storage_path.mkdir(parents=True, exist_ok=True)
    
    def ingest_eml_file(self, file_path: Union[str, Path], user_id: int, db: Session) -> Dict[str, Any]:
        """
        Ingest a single .eml file and extract structured data.
        
        Args:
            file_path: Path to the .eml file
            user_id: User ID for namespace isolation
            db: Database session
            
        Returns:
            Dictionary containing parsed email data
        """
        try:
            file_path = Path(file_path)
            logger.info(f"Processing .eml file: {file_path}")
            
            # Read and parse email
            with open(file_path, 'rb') as f:
                raw_email = email.message_from_bytes(f.read())
            
            # Extract structured metadata
            email_data = self._extract_email_metadata(raw_email)
            email_data['user_id'] = user_id
            email_data['source_file'] = str(file_path)
            email_data['ingestion_method'] = 'eml_file'
            
            # Extract body content
            email_data['body_text'], email_data['body_html'] = self._extract_body(raw_email)
            
            # Process attachments
            email_data['attachments'] = self._extract_attachments(raw_email, user_id)
            
            # Generate unique email ID
            email_data['email_id'] = self._generate_email_id(email_data)
            
            # Store in database
            local_email = self._store_email_in_db(email_data, db)
            
            logger.info(f"Successfully ingested email: {email_data['subject'][:50]}...")
            return email_data
            
        except Exception as e:
            logger.error(f"Error ingesting .eml file {file_path}: {e}")
            raise
    
    def ingest_eml_directory(self, directory_path: Union[str, Path], user_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        Batch ingest all .eml files from a directory.
        
        Args:
            directory_path: Path to directory containing .eml files
            user_id: User ID for namespace isolation
            db: Database session
            
        Returns:
            List of ingested email data dictionaries
        """
        directory_path = Path(directory_path)
        ingested_emails = []
        
        logger.info(f"Batch ingesting .eml files from: {directory_path}")
        
        eml_files = list(directory_path.glob("*.eml"))
        logger.info(f"Found {len(eml_files)} .eml files")
        
        for eml_file in eml_files:
            try:
                email_data = self.ingest_eml_file(eml_file, user_id, db)
                ingested_emails.append(email_data)
            except Exception as e:
                logger.error(f"Failed to ingest {eml_file}: {e}")
                continue
        
        logger.info(f"Successfully ingested {len(ingested_emails)} emails")
        return ingested_emails
    
    def connect_imap(self, server: str, port: int, username: str, password: str, 
                     use_ssl: bool = True) -> imaplib.IMAP4:
        """
        Connect to IMAP server for local email retrieval.
        
        Args:
            server: IMAP server address
            port: IMAP server port
            username: Email username
            password: Email password
            use_ssl: Whether to use SSL/TLS
            
        Returns:
            IMAP connection object
        """
        try:
            if use_ssl:
                imap = imaplib.IMAP4_SSL(server, port)
            else:
                imap = imaplib.IMAP4(server, port)
            
            imap.login(username, password)
            logger.info(f"Successfully connected to IMAP server: {server}")
            return imap
            
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server {server}: {e}")
            raise
    
    def fetch_imap_emails(self, imap_conn: imaplib.IMAP4, folder: str = "INBOX", 
                         limit: int = 100, user_id: int = None, db: Session = None) -> List[Dict[str, Any]]:
        """
        Fetch emails from IMAP server for local processing.
        
        Args:
            imap_conn: IMAP connection object
            folder: Email folder to fetch from
            limit: Maximum number of emails to fetch
            user_id: User ID for namespace isolation
            db: Database session
            
        Returns:
            List of fetched and processed email data
        """
        try:
            imap_conn.select(folder)
            
            # Search for emails (can add date filters, etc.)
            status, messages = imap_conn.search(None, 'ALL')
            email_ids = messages[0].split()
            
            # Limit the number of emails
            if limit and len(email_ids) > limit:
                email_ids = email_ids[-limit:]  # Get most recent
            
            fetched_emails = []
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = imap_conn.fetch(email_id, '(RFC822)')
                    raw_email = email.message_from_bytes(msg_data[0][1])
                    
                    # Process same as .eml file
                    email_data = self._extract_email_metadata(raw_email)
                    email_data['user_id'] = user_id
                    email_data['source_file'] = f"imap_{folder}_{email_id.decode()}"
                    email_data['ingestion_method'] = 'imap'
                    
                    email_data['body_text'], email_data['body_html'] = self._extract_body(raw_email)
                    email_data['attachments'] = self._extract_attachments(raw_email, user_id)
                    email_data['email_id'] = self._generate_email_id(email_data)
                    
                    if db:
                        self._store_email_in_db(email_data, db)
                    
                    fetched_emails.append(email_data)
                    
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            logger.info(f"Fetched {len(fetched_emails)} emails from IMAP")
            return fetched_emails
            
        except Exception as e:
            logger.error(f"Error fetching IMAP emails: {e}")
            raise
    
    def _extract_email_metadata(self, raw_email: email.message.EmailMessage) -> Dict[str, Any]:
        """Extract structured metadata from email message."""
        metadata = {}
        
        # Extract headers with proper decoding
        metadata['sender'] = self._decode_header(raw_email.get('From', ''))
        metadata['recipient'] = self._decode_header(raw_email.get('To', ''))
        metadata['subject'] = self._decode_header(raw_email.get('Subject', 'No Subject'))
        metadata['cc'] = self._decode_header(raw_email.get('Cc', ''))
        metadata['bcc'] = self._decode_header(raw_email.get('Bcc', ''))
        
        # Extract timestamp
        date_header = raw_email.get('Date')
        if date_header:
            try:
                metadata['timestamp'] = parsedate_to_datetime(date_header)
            except Exception:
                metadata['timestamp'] = datetime.now()
        else:
            metadata['timestamp'] = datetime.now()
        
        # Extract other useful headers
        metadata['message_id'] = raw_email.get('Message-ID', '')
        metadata['in_reply_to'] = raw_email.get('In-Reply-To', '')
        metadata['references'] = raw_email.get('References', '')
        
        return metadata
    
    def _extract_body(self, raw_email: email.message.EmailMessage) -> Tuple[str, str]:
        """Extract plain text and HTML body from email."""
        body_text = ""
        body_html = ""
        
        if raw_email.is_multipart():
            for part in raw_email.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # Skip attachments
                if 'attachment' in content_disposition:
                    continue
                
                if content_type == 'text/plain':
                    try:
                        body_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except Exception:
                        pass
                elif content_type == 'text/html':
                    try:
                        body_html += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except Exception:
                        pass
        else:
            # Single part message
            content_type = raw_email.get_content_type()
            try:
                payload = raw_email.get_payload(decode=True).decode('utf-8', errors='ignore')
                if content_type == 'text/plain':
                    body_text = payload
                elif content_type == 'text/html':
                    body_html = payload
                else:
                    body_text = payload  # Default to text
            except Exception:
                pass
        
        # Convert HTML to text if no plain text available
        if not body_text and body_html:
            try:
                body_text = html2text(body_html)
            except Exception:
                body_text = body_html  # Fallback
        
        return body_text.strip(), body_html.strip()
    
    def _extract_attachments(self, raw_email: email.message.EmailMessage, user_id: int) -> List[Dict[str, Any]]:
        """Extract and store email attachments securely."""
        attachments = []
        
        if not raw_email.is_multipart():
            return attachments
        
        for part in raw_email.walk():
            content_disposition = str(part.get('Content-Disposition', ''))
            
            if 'attachment' in content_disposition:
                filename = part.get_filename()
                if filename:
                    # Decode filename
                    filename = self._decode_header(filename)
                    
                    # Create secure storage path
                    user_dir = self.attachment_storage_path / f"user_{user_id}"
                    user_dir.mkdir(exist_ok=True)
                    
                    # Generate unique filename to avoid conflicts
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_filename = f"{timestamp}_{filename}"
                    file_path = user_dir / safe_filename
                    
                    # Save attachment
                    try:
                        with open(file_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        
                        attachments.append({
                            'filename': filename,
                            'stored_path': str(file_path),
                            'content_type': part.get_content_type(),
                            'size': file_path.stat().st_size
                        })
                        
                        logger.debug(f"Saved attachment: {filename}")
                        
                    except Exception as e:
                        logger.error(f"Error saving attachment {filename}: {e}")
                        continue
        
        return attachments
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header with proper charset handling."""
        if not header_value:
            return ""
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding, errors='ignore')
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            
            return decoded_string.strip()
            
        except Exception:
            return str(header_value)
    
    def _generate_email_id(self, email_data: Dict[str, Any]) -> str:
        """Generate unique email ID based on content."""
        # Use message ID if available, otherwise create hash
        if email_data.get('message_id'):
            return hashlib.md5(email_data['message_id'].encode()).hexdigest()
        
        # Create hash from sender, subject, timestamp
        content = f"{email_data.get('sender', '')}{email_data.get('subject', '')}{email_data.get('timestamp', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _store_email_in_db(self, email_data: Dict[str, Any], db: Session) -> 'LocalEmail':
        """Store email data in database."""
        try:
            # Check if email already exists
            existing_email = db.query(LocalEmail).filter(
                LocalEmail.email_id == email_data['email_id'],
                LocalEmail.user_id == email_data['user_id']
            ).first()
            
            if existing_email:
                logger.debug(f"Email already exists: {email_data['subject'][:50]}...")
                return existing_email
            
            # Create new email record
            local_email = LocalEmail(
                email_id=email_data['email_id'],
                user_id=email_data['user_id'],
                sender=email_data.get('sender', ''),
                recipient=email_data.get('recipient', ''),
                subject=email_data.get('subject', ''),
                body_text=email_data.get('body_text', ''),
                body_html=email_data.get('body_html', ''),
                timestamp=email_data.get('timestamp'),
                source_file=email_data.get('source_file', ''),
                ingestion_method=email_data.get('ingestion_method', 'unknown'),
                message_id=email_data.get('message_id', ''),
                in_reply_to=email_data.get('in_reply_to', ''),
                references=email_data.get('references', '')
            )
            
            db.add(local_email)
            db.flush()  # Get the ID
            
            # Store attachments
            for attachment_data in email_data.get('attachments', []):
                attachment = EmailAttachment(
                    email_id=local_email.id,
                    user_id=email_data['user_id'],
                    filename=attachment_data['filename'],
                    stored_path=attachment_data['stored_path'],
                    content_type=attachment_data['content_type'],
                    file_size=attachment_data['size']
                )
                db.add(attachment)
            
            db.commit()
            logger.info(f"Stored email in database: {email_data['subject'][:50]}...")
            return local_email
            
        except Exception as e:
            logger.error(f"Error storing email in database: {e}")
            db.rollback()
            raise