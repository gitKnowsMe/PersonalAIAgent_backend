"""
Email ingestion service for parsing .eml files and connecting to IMAP/POP3.
Handles email parsing, metadata extraction, and secure credential management.
"""

import email
import imaplib
import poplib
import ssl
from email.message import EmailMessage
from typing import Dict, List, Optional, Union, AsyncIterator, AsyncGenerator
from pathlib import Path
import logging
from datetime import datetime
import re

from app.core.config import settings
from app.db.models import User
from app.exceptions import (
    EmailProcessingError,
    NetworkError,
    AuthenticationError,
    EmailNotFoundError
)

logger = logging.getLogger(__name__)


class EmailIngestionService:
    """Service for ingesting emails from various sources."""
    
    def __init__(self):
        self.supported_formats = ['.eml', '.msg']
    
    async def parse_eml_file(self, file_path: Union[str, Path]) -> Dict:
        """
        Parse a .eml file and extract structured metadata and content.
        
        Args:
            file_path: Path to the .eml file
            
        Returns:
            Dict containing parsed email data
        """
        try:
            with open(file_path, 'rb') as f:
                msg = email.message_from_bytes(f.read())
            
            return await self._extract_email_data(msg)
            
        except FileNotFoundError:
            raise EmailNotFoundError(f"EML file not found: {file_path}")
        except PermissionError:
            raise EmailProcessingError(f"Permission denied reading EML file: {file_path}")
        except UnicodeDecodeError as e:
            raise EmailProcessingError(f"Invalid file encoding in EML file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing EML file {file_path}: {e}")
            if "corrupt" in str(e).lower() or "invalid" in str(e).lower():
                raise EmailProcessingError(f"Corrupted EML file: {file_path} - {str(e)}")
            else:
                raise EmailProcessingError(f"Failed to parse EML file {file_path}: {str(e)}")
    
    async def parse_eml_content(self, content: bytes) -> Dict:
        """
        Parse email content from bytes.
        
        Args:
            content: Raw email content as bytes
            
        Returns:
            Dict containing parsed email data
        """
        try:
            msg = email.message_from_bytes(content)
            return await self._extract_email_data(msg)
            
        except UnicodeDecodeError as e:
            raise EmailProcessingError(f"Invalid email content encoding: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing email content: {e}")
            if "corrupt" in str(e).lower() or "invalid" in str(e).lower():
                raise EmailProcessingError(f"Corrupted email content: {str(e)}")
            else:
                raise EmailProcessingError(f"Failed to parse email content: {str(e)}")
    
    async def _extract_email_data(self, msg: EmailMessage) -> Dict:
        """Extract structured data from email message."""
        
        # Extract basic headers
        email_data = {
            'message_id': msg.get('Message-ID', ''),
            'subject': self._decode_header(msg.get('Subject', '')),
            'sender': self._decode_header(msg.get('From', '')),
            'recipient': self._decode_header(msg.get('To', '')),
            'cc': self._decode_header(msg.get('CC', '')),
            'bcc': self._decode_header(msg.get('BCC', '')),
            'date': self._parse_date(msg.get('Date', '')),
            'in_reply_to': msg.get('In-Reply-To', ''),
            'references': msg.get('References', ''),
            'thread_topic': self._decode_header(msg.get('Thread-Topic', '')),
            'body_text': '',
            'body_html': '',
            'attachments': []
        }
        
        # Extract body content
        if msg.is_multipart():
            for part in msg.walk():
                await self._process_email_part(part, email_data)
        else:
            await self._process_email_part(msg, email_data)
        
        # Clean and process body text
        email_data['body_text'] = self._clean_text(email_data['body_text'])
        
        return email_data
    
    async def _process_email_part(self, part: EmailMessage, email_data: Dict):
        """Process individual parts of multipart email."""
        content_type = part.get_content_type()
        content_disposition = part.get('Content-Disposition', '')
        
        if 'attachment' in content_disposition:
            # Handle attachment
            filename = part.get_filename()
            if filename:
                email_data['attachments'].append({
                    'filename': self._decode_header(filename),
                    'content_type': content_type,
                    'size': len(part.get_payload(decode=True) or b'')
                })
        elif content_type == 'text/plain':
            # Extract plain text
            payload = part.get_payload(decode=True)
            if payload:
                email_data['body_text'] += payload.decode('utf-8', errors='ignore')
        elif content_type == 'text/html':
            # Extract HTML content
            payload = part.get_payload(decode=True)
            if payload:
                email_data['body_html'] += payload.decode('utf-8', errors='ignore')
    
    def _decode_header(self, header: str) -> str:
        """Decode email header with proper encoding handling."""
        if not header:
            return ''
        
        try:
            decoded_parts = email.header.decode_header(header)
            decoded_string = ''
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding, errors='ignore')
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            
            return decoded_string.strip()
        except UnicodeDecodeError as e:
            logger.warning(f"Unicode decode error in header '{header}': {e}")
            return header  # Return original header as fallback
        except Exception as e:
            logger.warning(f"Error decoding header '{header}': {e}")
            return header  # Return original header as fallback
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Parse RFC 2822 date format
            parsed_date = email.utils.parsedate_to_datetime(date_str)
            return parsed_date
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid date format '{date_str}': {e}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize email text content."""
        if not text:
            return ''
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove email signatures (simple heuristic)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip common signature patterns
            if any(pattern in line.lower() for pattern in [
                'sent from my iphone',
                'sent from my android',
                'confidentiality notice',
                'this email and any attachments'
            ]):
                break
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()


class IMAPEmailConnector:
    """Connector for IMAP email servers."""
    
    def __init__(self, host: str, port: int = 993, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.connection = None
    
    async def connect(self, username: str, password: str) -> bool:
        """Connect to IMAP server."""
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.connection = imaplib.IMAP4(self.host, self.port)
            
            self.connection.login(username, password)
            logger.info(f"Connected to IMAP server {self.host}")
            return True
            
        except (imaplib.IMAP4.error, ssl.SSLError) as e:
            logger.error(f"IMAP authentication or SSL error: {e}")
            raise AuthenticationError(f"IMAP authentication failed for {self.host}: {str(e)}")
        except (ConnectionRefusedError, OSError) as e:
            logger.error(f"IMAP network connection failed: {e}")
            raise NetworkError(f"Cannot connect to IMAP server {self.host}:{self.port} - {str(e)}")
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            if "timeout" in str(e).lower():
                raise NetworkError(f"IMAP connection timeout to {self.host}:{self.port}", timeout=True)
            else:
                raise NetworkError(f"IMAP connection failed to {self.host}: {str(e)}")
    
    async def fetch_emails(self, folder: str = 'INBOX', limit: int = 100) -> AsyncIterator[bytes]:
        """Fetch emails from specified folder."""
        if not self.connection:
            raise EmailProcessingError("Not connected to IMAP server - call connect() first")
        
        try:
            self.connection.select(folder)
            
            # Search for all emails
            _, message_ids = self.connection.search(None, 'ALL')
            
            # Get latest emails first
            ids = message_ids[0].split()[-limit:]
            
            for msg_id in ids:
                _, msg_data = self.connection.fetch(msg_id, '(RFC822)')
                yield msg_data[0][1]
                
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP protocol error fetching emails: {e}")
            raise EmailProcessingError(f"IMAP error fetching emails from {folder}: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            if "timeout" in str(e).lower():
                raise NetworkError(f"Timeout fetching emails from IMAP folder {folder}", timeout=True)
            else:
                raise EmailProcessingError(f"Failed to fetch emails from IMAP folder {folder}: {str(e)}")
    
    def disconnect(self):
        """Close IMAP connection."""
        if self.connection:
            self.connection.close()
            self.connection.logout()
            self.connection = None


class POP3EmailConnector:
    """Connector for POP3 email servers."""
    
    def __init__(self, host: str, port: int = 995, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.connection = None
    
    async def connect(self, username: str, password: str) -> bool:
        """Connect to POP3 server."""
        try:
            if self.use_ssl:
                self.connection = poplib.POP3_SSL(self.host, self.port)
            else:
                self.connection = poplib.POP3(self.host, self.port)
            
            self.connection.user(username)
            self.connection.pass_(password)
            
            logger.info(f"Connected to POP3 server {self.host}")
            return True
            
        except (poplib.error_proto, ssl.SSLError) as e:
            logger.error(f"POP3 authentication or SSL error: {e}")
            raise AuthenticationError(f"POP3 authentication failed for {self.host}: {str(e)}")
        except (ConnectionRefusedError, OSError) as e:
            logger.error(f"POP3 network connection failed: {e}")
            raise NetworkError(f"Cannot connect to POP3 server {self.host}:{self.port} - {str(e)}")
        except Exception as e:
            logger.error(f"POP3 connection failed: {e}")
            if "timeout" in str(e).lower():
                raise NetworkError(f"POP3 connection timeout to {self.host}:{self.port}", timeout=True)
            else:
                raise NetworkError(f"POP3 connection failed to {self.host}: {str(e)}")
    
    async def fetch_emails(self, limit: int = 100) -> AsyncGenerator[bytes, None]:
        """Fetch emails from POP3 server."""
        if not self.connection:
            raise EmailProcessingError("Not connected to POP3 server - call connect() first")
        
        try:
            num_messages = len(self.connection.list()[1])
            start_msg = max(1, num_messages - limit + 1)
            
            for i in range(start_msg, num_messages + 1):
                msg_lines = self.connection.retr(i)[1]
                msg_bytes = b'\n'.join(msg_lines)
                yield msg_bytes
                
        except poplib.error_proto as e:
            logger.error(f"POP3 protocol error fetching emails: {e}")
            raise EmailProcessingError(f"POP3 error fetching emails: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            if "timeout" in str(e).lower():
                raise NetworkError(f"Timeout fetching emails from POP3 server", timeout=True)
            else:
                raise EmailProcessingError(f"Failed to fetch emails from POP3 server: {str(e)}")
    
    def disconnect(self):
        """Close POP3 connection."""
        if self.connection:
            self.connection.quit()
            self.connection = None