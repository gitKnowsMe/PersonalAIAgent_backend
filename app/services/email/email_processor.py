"""
Email processing service for chunking and embedding email content.
Handles email-specific processing strategies for optimal RAG performance.
Consolidates the best features from legacy and modern processors.
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import logging
import html2text

from app.services.embedding_service import SentenceTransformerEmbeddingService
from app.exceptions import (
    EmailProcessingError,
    EmailClassificationError,
    VectorStoreError
)

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Unified processor for email content chunking and embedding with advanced classification and chunking strategies."""
    
    def __init__(self):
        self.embedding_service = SentenceTransformerEmbeddingService()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
        
        # Enhanced email classification patterns (from legacy processor)
        self.classification_patterns = {
            "business": {
                "keywords": [
                    "meeting", "project", "deadline", "team", "client", "proposal",
                    "contract", "budget", "revenue", "quarterly", "annual", "report",
                    "presentation", "conference", "call", "agenda", "action items",
                    "follow up", "deliverable", "milestone", "stakeholder", "roi",
                    "kpi", "metrics", "analysis", "strategy", "implementation"
                ],
                "patterns": [
                    r'\b(meeting|conference|call)\s+(scheduled|planned|rescheduled)',
                    r'\b(project|task|deliverable)\s+(update|status|completion)',
                    r'\b(deadline|due\s+date|timeline)',
                    r'\b(quarterly|annual|monthly)\s+(report|review|meeting)',
                    r'\b(action\s+items|next\s+steps|follow\s+up)',
                    r'\b(budget|cost|expense|revenue|profit)',
                ],
                "sender_patterns": [
                    r'@(company|corp|inc|ltd|llc)',
                    r'noreply|no-reply|donotreply'
                ]
            },
            "personal": {
                "keywords": [
                    "family", "friend", "personal", "vacation", "holiday", "party",
                    "birthday", "anniversary", "wedding", "dinner", "lunch", "coffee",
                    "weekend", "home", "kids", "children", "spouse", "partner",
                    "photos", "pictures", "memories", "trip", "travel", "visit"
                ],
                "patterns": [
                    r'\b(family|friends?)\s+(gathering|reunion|visit)',
                    r'\b(vacation|holiday|trip)\s+(plans?|photos?)',
                    r'\b(birthday|anniversary|wedding)',
                    r'\b(dinner|lunch|coffee|drinks?)\s+(tonight|tomorrow|weekend)',
                    r'\b(home|house|apartment)',
                    r'\b(kids?|children|baby|toddler)',
                ],
                "sender_patterns": [
                    r'@(gmail|yahoo|hotmail|outlook|icloud|aol)',
                ]
            },
            "promotional": {
                "keywords": [
                    "sale", "discount", "offer", "deal", "promotion", "coupon",
                    "limited time", "exclusive", "special", "save", "% off",
                    "free shipping", "newsletter", "unsubscribe", "marketing",
                    "advertisement", "promo", "clearance", "black friday",
                    "cyber monday", "holiday sale", "end of season"
                ],
                "patterns": [
                    r'\b(\d+%?)\s+(off|discount|savings?)',
                    r'\b(sale|deal|offer|promotion)\s+(ends?|expires?)',
                    r'\b(limited\s+time|exclusive|special)\s+(offer|deal)',
                    r'\b(free\s+shipping|no\s+cost\s+delivery)',
                    r'\b(unsubscribe|opt\s+out|manage\s+preferences)',
                    r'\$\d+\.\d{2}\s+(was|originally|retail)',
                ],
                "sender_patterns": [
                    r'@(marketing|promo|offers|deals|sales)',
                    r'noreply|no-reply|newsletter|marketing'
                ]
            },
            "transactional": {
                "keywords": [
                    "receipt", "order", "confirmation", "invoice", "payment",
                    "transaction", "purchase", "shipped", "delivered", "tracking",
                    "refund", "return", "exchange", "subscription", "billing",
                    "account", "statement", "balance", "due", "overdue"
                ],
                "patterns": [
                    r'\b(order|transaction|purchase)\s+(#?\d+|confirmation)',
                    r'\b(receipt|invoice)\s+(for|#)',
                    r'\b(payment|billing)\s+(confirmation|receipt|due)',
                    r'\b(shipped|delivered|tracking)\s+(#?\d+|number)',
                    r'\b(refund|return|exchange)\s+(processed|approved)',
                    r'\b(subscription|membership)\s+(renewal|expiring|expired)',
                    r'\$\d+\.\d{2}\s+(charged|paid|due|owed)',
                ],
                "sender_patterns": [
                    r'@(payments|billing|orders|transactions)',
                    r'noreply|no-reply|automated|system'
                ]
            },
            "support": {
                "keywords": [
                    "support", "help", "assistance", "issue", "problem", "bug",
                    "error", "trouble", "ticket", "case", "inquiry", "question",
                    "resolution", "solution", "fix", "troubleshooting", "guide",
                    "documentation", "tutorial", "faq", "knowledge base"
                ],
                "patterns": [
                    r'\b(support|help)\s+(ticket|case|request)',
                    r'\b(issue|problem|bug)\s+(#?\d+|reported)',
                    r'\b(troubleshooting|resolution|solution)',
                    r'\b(knowledge\s+base|faq|documentation)',
                    r'\b(inquiry|question)\s+(about|regarding)',
                    r'\b(technical|customer)\s+(support|service)',
                ],
                "sender_patterns": [
                    r'@(support|help|service|customer)',
                    r'support|help|service|customer'
                ]
            }
        }
        
        # Enhanced chunking configurations per email type (from legacy processor)
        self.chunk_configs = {
            'business': {
                'chunk_size': 800,
                'overlap': 100,
                'min_chunk_size': 150,
                'strategy': 'thread_aware',
                'description': 'Business emails with thread context preservation'
            },
            'personal': {
                'chunk_size': 600,
                'overlap': 75,
                'min_chunk_size': 100,
                'strategy': 'conversation_chunks',
                'description': 'Personal emails with relationship context'
            },
            'promotional': {
                'chunk_size': 500,
                'overlap': 50,
                'min_chunk_size': 100,
                'strategy': 'content_focused',
                'description': 'Promotional emails with offer extraction'
            },
            'transactional': {
                'chunk_size': 400,
                'overlap': 40,
                'min_chunk_size': 80,
                'strategy': 'data_extraction',
                'description': 'Transactional emails with precise data matching'
            },
            'support': {
                'chunk_size': 700,
                'overlap': 100,
                'min_chunk_size': 120,
                'strategy': 'issue_focused',
                'description': 'Support emails with solution tracking'
            },
            'default': {
                'chunk_size': 400,
                'overlap': 50,
                'min_chunk_size': 100,
                'strategy': 'balanced',
                'description': 'Generic emails with balanced processing'
            },
            # Legacy compatibility
            'short_email': {  # < 500 chars
                'chunk_size': 200,
                'overlap': 25,
                'min_chunk_size': 50,
                'strategy': 'balanced'
            },
            'long_email': {  # > 2000 chars
                'chunk_size': 600,
                'overlap': 100,
                'min_chunk_size': 150,
                'strategy': 'balanced'
            },
            'generic': {
                'chunk_size': 400,
                'overlap': 50,
                'min_chunk_size': 100,
                'strategy': 'balanced',
                'description': 'Generic emails with balanced processing'
            }
        }
    
    async def process_email(self, email_data: Dict, user_id: int, classification_tags: List[str] = None) -> List[Dict]:
        """
        Process email content and generate embeddings with enhanced classification and chunking.
        
        Args:
            email_data: Parsed email data
            user_id: User ID for namespace
            classification_tags: List of classification tags for the email
            
        Returns:
            List of processed chunks with embeddings and metadata
        """
        try:
            # Convert HTML to text if needed
            processed_text = await self._prepare_text_content(email_data)
            
            # Enhance classification tags with sophisticated patterns
            enhanced_tags = await self._enhance_classification_tags(email_data, classification_tags)
            
            # Determine email type for optimal chunking strategy
            email_type = self._determine_email_type(enhanced_tags)
            
            # Generate email-specific metadata
            metadata = await self._create_email_metadata(email_data, user_id, enhanced_tags, email_type)
            
            # Chunk the email content using type-specific strategy
            chunks = await self._chunk_email_content_advanced(processed_text, email_data, email_type)
            
            # Generate embeddings for each chunk
            processed_chunks = []
            for i, chunk_data in enumerate(chunks):
                chunk_text = chunk_data if isinstance(chunk_data, str) else chunk_data.get('content', chunk_data.get('text', ''))
                
                if len(chunk_text.strip()) < 10:  # Skip very short chunks
                    continue
                
                try:
                    # Generate embedding
                    embedding = await self.embedding_service.generate_embedding(chunk_text)
                    
                    # Create chunk metadata
                    chunk_metadata = {
                        **metadata,
                        'chunk_index': i,
                        'chunk_text': chunk_text,
                        'chunk_length': len(chunk_text),
                        'chunk_word_count': len(chunk_text.split()),
                        'email_type': email_type,
                        'chunking_strategy': self.chunk_configs.get(email_type, self.chunk_configs['default']).get('strategy', 'balanced')
                    }
                    
                    # Add additional metadata from advanced chunking
                    if isinstance(chunk_data, dict) and 'metadata' in chunk_data:
                        chunk_metadata.update(chunk_data['metadata'])
                    
                    processed_chunks.append({
                        'text': chunk_text,
                        'embedding': embedding,
                        'metadata': chunk_metadata
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk {i}: {e}")
                    # Continue processing other chunks even if one fails
                    continue
            
            logger.info(f"Processed email '{metadata['subject'][:50]}...' ({email_type}) into {len(processed_chunks)} chunks")
            return processed_chunks
            
        except VectorStoreError:
            # Re-raise vector store specific errors
            raise
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            raise EmailProcessingError(f"Failed to process email: {str(e)}")
    
    async def _prepare_text_content(self, email_data: Dict) -> str:
        """Prepare and clean email text content."""
        body_text = email_data.get('body_text', '')
        body_html = email_data.get('body_html', '')
        
        # Use HTML content if text is empty or very short
        if len(body_text.strip()) < 50 and body_html:
            body_text = self.html_converter.handle(body_html)
        
        # Clean the text content
        cleaned_text = self._clean_email_text(body_text)
        
        # Add subject and important headers to content
        subject = email_data.get('subject', '')
        if subject and subject.lower() not in cleaned_text.lower():
            cleaned_text = f"Subject: {subject}\n\n{cleaned_text}"
        
        return cleaned_text
    
    def _clean_email_text(self, text: str) -> str:
        """Clean and normalize email text content."""
        if not text:
            return ''
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove email headers that appear in body
        text = re.sub(r'^(From|To|Cc|Bcc|Date|Subject):.*?\n', '', text, flags=re.MULTILINE)
        
        # Remove forwarded/reply headers
        text = re.sub(r'-----Original Message-----.*?(?=\n\n|\Z)', '', text, flags=re.DOTALL)
        text = re.sub(r'On .* wrote:.*?(?=\n\n|\Z)', '', text, flags=re.DOTALL)
        
        # Remove common email footers
        footer_patterns = [
            r'sent from my (iphone|android|mobile device)',
            r'get outlook for (ios|android)',
            r'confidentiality notice:.*',
            r'this email and any attachments.*',
            r'please consider the environment.*'
        ]
        
        for pattern in footer_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove URLs (keep them but shorten)
        text = re.sub(r'https?://[^\s]+', '[URL]', text)
        
        # Clean up extra whitespace again
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    async def _chunk_email_content(self, text: str, email_data: Dict) -> List[str]:
        """Chunk email content using email-specific strategies."""
        if not text:
            return []
        
        # Determine chunking strategy based on email length
        text_length = len(text)
        if text_length < 500:
            config = self.chunk_configs['short_email']
        elif text_length > 2000:
            config = self.chunk_configs['long_email']
        else:
            config = self.chunk_configs['default']
        
        chunks = []
        
        # Try to chunk by email structure first (paragraphs, quoted sections)
        structured_chunks = self._chunk_by_email_structure(text, config)
        
        if structured_chunks:
            # Further split large structured chunks
            for chunk in structured_chunks:
                if len(chunk) > config['chunk_size'] * 1.5:
                    sub_chunks = self._chunk_by_size(chunk, config)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(chunk)
        else:
            # Fall back to size-based chunking
            chunks = self._chunk_by_size(text, config)
        
        # Filter out chunks that are too small
        filtered_chunks = [
            chunk for chunk in chunks 
            if len(chunk.strip()) >= config['min_chunk_size']
        ]
        
        return filtered_chunks
    
    def _chunk_by_email_structure(self, text: str, config: Dict) -> List[str]:
        """Chunk email by natural structure (paragraphs, quoted sections)."""
        chunks = []
        
        # Split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        
        current_chunk = ''
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Check if adding this paragraph would exceed chunk size
            potential_chunk = current_chunk + '\n\n' + paragraph if current_chunk else paragraph
            
            if len(potential_chunk) <= config['chunk_size']:
                current_chunk = potential_chunk
            else:
                # Save current chunk if it's substantial
                if len(current_chunk) >= config['min_chunk_size']:
                    chunks.append(current_chunk)
                
                # Start new chunk with current paragraph
                current_chunk = paragraph
        
        # Add final chunk
        if len(current_chunk) >= config['min_chunk_size']:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_by_size(self, text: str, config: Dict) -> List[str]:
        """Chunk text by size with overlap."""
        chunks = []
        chunk_size = config['chunk_size']
        overlap = config['overlap']
        
        start = 0
        while start < len(text):
            end = start + chunk_size
            
            # Try to end at word boundary
            if end < len(text):
                # Look for word boundary within last 50 characters
                word_end = text.rfind(' ', end - 50, end)
                if word_end > start:
                    end = word_end
            
            chunk = text[start:end].strip()
            if len(chunk) >= config['min_chunk_size']:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + 1, end - overlap)
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    async def _enhance_classification_tags(self, email_data: Dict, classification_tags: List[str] = None) -> List[str]:
        """Enhance classification tags using sophisticated pattern matching."""
        enhanced_tags = set(classification_tags or [])
        
        # Combine text for analysis
        text_content = ' '.join([
            email_data.get('subject', ''),
            email_data.get('body_text', ''),
            email_data.get('sender', '')
        ]).lower()
        
        sender_lower = email_data.get('sender', '').lower()
        
        # Apply sophisticated pattern matching
        for email_type, patterns in self.classification_patterns.items():
            score = 0.0
            
            # Keyword matching
            keyword_matches = sum(1 for keyword in patterns["keywords"] if keyword in text_content)
            score += keyword_matches * 0.1
            
            # Pattern matching
            pattern_matches = sum(1 for pattern in patterns["patterns"] if re.search(pattern, text_content))
            score += pattern_matches * 0.3
            
            # Sender pattern matching
            sender_matches = sum(1 for pattern in patterns["sender_patterns"] if re.search(pattern, sender_lower))
            score += sender_matches * 0.2
            
            # Add tag if score meets threshold
            if score >= 0.2:  # Lower threshold for enhancement
                enhanced_tags.add(email_type)
        
        # Apply additional heuristics
        enhanced_tags = self._apply_classification_heuristics(enhanced_tags, email_data)
        
        return list(enhanced_tags)
    
    def _apply_classification_heuristics(self, tags: set, email_data: Dict) -> set:
        """Apply additional classification heuristics."""
        subject = email_data.get('subject', '').lower()
        sender = email_data.get('sender', '').lower()
        
        # Boost business emails for work domains
        work_domains = ['.com', '.org', '.edu', '.gov', '.net']
        personal_domains = ['gmail', 'yahoo', 'hotmail', 'outlook', 'icloud']
        
        if any(domain in sender for domain in work_domains) and not any(personal in sender for personal in personal_domains):
            tags.add('business')
        
        # Boost promotional for common marketing indicators
        if any(indicator in subject for indicator in ['[promo]', '[marketing]', '[newsletter]', 'unsubscribe']):
            tags.add('promotional')
        
        # Boost transactional for order/payment indicators
        if any(indicator in subject for indicator in ['order', 'receipt', 'invoice', 'payment', 'confirmation']):
            tags.add('transactional')
        
        # Boost support for support indicators
        if any(indicator in subject for indicator in ['support', 'help', 'ticket', 'case']):
            tags.add('support')
        
        return tags
    
    def _determine_email_type(self, classification_tags: List[str]) -> str:
        """Determine primary email type for chunking strategy."""
        # Priority order for email types
        type_priority = ['support', 'transactional', 'business', 'promotional', 'personal']
        
        for email_type in type_priority:
            if email_type in classification_tags:
                return email_type
        
        return 'default'
    
    async def _chunk_email_content_advanced(self, text: str, email_data: Dict, email_type: str) -> List[Dict]:
        """Advanced email content chunking using type-specific strategies."""
        if not text:
            return []
        
        # Get configuration for email type
        config = self.chunk_configs.get(email_type, self.chunk_configs['default'])
        strategy = config.get('strategy', 'balanced')
        
        # Apply chunking strategy
        if strategy == 'thread_aware':
            return self._create_thread_aware_chunks(text, email_data, config)
        elif strategy == 'conversation_chunks':
            return self._create_conversation_chunks(text, email_data, config)
        elif strategy == 'content_focused':
            return self._create_content_focused_chunks(text, email_data, config)
        elif strategy == 'data_extraction':
            return self._create_data_extraction_chunks(text, email_data, config)
        elif strategy == 'issue_focused':
            return self._create_issue_focused_chunks(text, email_data, config)
        else:
            # Balanced strategy (default)
            return self._create_balanced_chunks(text, email_data, config)
    
    def _create_thread_aware_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create chunks that preserve business thread context."""
        chunks = []
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            # Check if adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) > config['chunk_size'] and current_chunk:
                # Create chunk with metadata
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": {
                        "chunk_index": chunk_index,
                        "subject": email_data.get('subject', ''),
                        "sender": email_data.get('sender', ''),
                        "thread_context": True,
                        "chunk_type": "thread_aware"
                    }
                })
                
                # Start new chunk with overlap
                overlap = config.get('overlap', 0)
                current_chunk = current_chunk[-overlap:] + "\n\n" + para if overlap > 0 else para
                chunk_index += 1
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= config.get('min_chunk_size', 100):
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": {
                    "chunk_index": chunk_index,
                    "subject": email_data.get('subject', ''),
                    "sender": email_data.get('sender', ''),
                    "thread_context": True,
                    "chunk_type": "thread_aware"
                }
            })
        
        return chunks
    
    def _create_conversation_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create chunks for personal conversation flow."""
        # Similar to thread_aware but with personal context
        chunks = self._create_balanced_chunks(content, email_data, config)
        
        # Add conversation metadata
        for chunk in chunks:
            if isinstance(chunk, dict):
                chunk.setdefault('metadata', {}).update({
                    'conversation_context': True,
                    'chunk_type': 'conversation'
                })
        
        return chunks
    
    def _create_content_focused_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create chunks focused on promotional content."""
        chunks = self._create_balanced_chunks(content, email_data, config)
        
        # Add promotional metadata
        for chunk in chunks:
            if isinstance(chunk, dict):
                chunk.setdefault('metadata', {}).update({
                    'content_focused': True,
                    'chunk_type': 'promotional'
                })
        
        return chunks
    
    def _create_data_extraction_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create chunks for precise transactional data extraction."""
        chunks = self._create_balanced_chunks(content, email_data, config)
        
        # Add transactional metadata
        for chunk in chunks:
            if isinstance(chunk, dict):
                chunk.setdefault('metadata', {}).update({
                    'data_extraction': True,
                    'chunk_type': 'transactional'
                })
        
        return chunks
    
    def _create_issue_focused_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create chunks focused on support issues and solutions."""
        chunks = self._create_balanced_chunks(content, email_data, config)
        
        # Add support metadata
        for chunk in chunks:
            if isinstance(chunk, dict):
                chunk.setdefault('metadata', {}).update({
                    'issue_focused': True,
                    'chunk_type': 'support'
                })
        
        return chunks
    
    def _create_balanced_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create balanced chunks for generic email processing."""
        chunks = []
        chunk_size = config['chunk_size']
        overlap = config.get('overlap', 0)
        min_chunk_size = config.get('min_chunk_size', 100)
        
        # Simple character-based chunking with overlap
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at word boundary
            if end < len(content):
                last_space = content.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_content = content[start:end].strip()
            
            if chunk_content and len(chunk_content) >= min_chunk_size:
                chunks.append({
                    "content": chunk_content,
                    "metadata": {
                        "chunk_index": chunk_index,
                        "subject": email_data.get('subject', ''),
                        "sender": email_data.get('sender', ''),
                        "chunk_type": "balanced"
                    }
                })
                
                chunk_index += 1
            
            # Move start position with overlap consideration
            start = end - overlap if overlap > 0 else end
        
        return chunks
    
    async def _create_email_metadata(self, email_data: Dict, user_id: int, classification_tags: List[str] = None, email_type: str = 'default') -> Dict:
        """Create comprehensive metadata for email."""
        date = email_data.get('date')
        
        metadata = {
            'user_id': user_id,
            'content_type': 'email',
            'message_id': email_data.get('message_id', ''),
            'subject': email_data.get('subject', ''),
            'sender': email_data.get('sender', ''),
            'sender_domain': self._extract_domain(email_data.get('sender', '')),
            'recipient': email_data.get('recipient', ''),
            'date': date.isoformat() if date else None,
            'timestamp': int(date.timestamp()) if date else None,
            'has_attachments': len(email_data.get('attachments', [])) > 0,
            'attachment_count': len(email_data.get('attachments', [])),
            'thread_topic': email_data.get('thread_topic', ''),
            'in_reply_to': email_data.get('in_reply_to', ''),
            'body_length': len(email_data.get('body_text', '')),
            'processed_at': datetime.now().isoformat(),
            'email_type': email_type,
            'processing_version': 'unified_v2'
        }
        
        # Add temporal metadata
        if date:
            metadata.update({
                'year': date.year,
                'month': date.month,
                'day': date.day,
                'weekday': date.weekday(),
                'hour': date.hour
            })
        
        # Add classification tags
        metadata['classification_tags'] = classification_tags or []
        
        return metadata
    
    def _extract_domain(self, email_address: str) -> Optional[str]:
        """Extract domain from email address."""
        if not email_address:
            return None
        
        email_match = re.search(r'[\w\.-]+@([\w\.-]+)', email_address)
        if email_match:
            return email_match.group(1).lower()
        
        return None
    
    def get_chunking_strategy(self, email_type: str) -> Dict[str, Any]:
        """Get chunking strategy for email type (legacy compatibility)."""
        return self.chunk_configs.get(email_type, self.chunk_configs['default'])
    
    def classify_email_type(self, subject: Optional[str], body_text: Optional[str], 
                           sender_email: str, recipient_emails: List[str] = None) -> str:
        """
        Classify email into one of the predefined types (legacy compatibility).
        
        Args:
            subject: Email subject line
            body_text: Email body text
            sender_email: Sender email address
            recipient_emails: List of recipient email addresses
            
        Returns:
            Email type classification
        """
        try:
            # Create email_data for modern classification
            email_data = {
                'subject': subject,
                'body_text': body_text,
                'sender': sender_email,
                'recipient': recipient_emails[0] if recipient_emails else ''
            }
            
            # Use synchronous version of classification for legacy compatibility
            enhanced_tags = self._enhance_classification_tags_sync(email_data, [])
            email_type = self._determine_email_type(enhanced_tags)
            
            return email_type if email_type != 'default' else 'generic'
            
        except Exception as e:
            logger.error(f"Error classifying email: {e}")
            # For classification errors, return a safe default instead of raising
            return "generic"
    
    def _enhance_classification_tags_sync(self, email_data: Dict, classification_tags: List[str] = None) -> List[str]:
        """Synchronous version of enhance_classification_tags for legacy compatibility."""
        enhanced_tags = set(classification_tags or [])
        
        # Combine text for analysis
        text_content = ' '.join([
            email_data.get('subject', ''),
            email_data.get('body_text', ''),
            email_data.get('sender', '')
        ]).lower()
        
        sender_lower = email_data.get('sender', '').lower()
        
        # Apply sophisticated pattern matching
        for email_type, patterns in self.classification_patterns.items():
            score = 0.0
            
            # Keyword matching
            keyword_matches = sum(1 for keyword in patterns["keywords"] if keyword in text_content)
            score += keyword_matches * 0.1
            
            # Pattern matching
            pattern_matches = sum(1 for pattern in patterns["patterns"] if re.search(pattern, text_content))
            score += pattern_matches * 0.3
            
            # Sender pattern matching
            sender_matches = sum(1 for pattern in patterns["sender_patterns"] if re.search(pattern, sender_lower))
            score += sender_matches * 0.2
            
            # Add tag if score meets threshold
            if score >= 0.2:  # Lower threshold for enhancement
                enhanced_tags.add(email_type)
        
        # Apply additional heuristics
        enhanced_tags = self._apply_classification_heuristics(enhanced_tags, email_data)
        
        return list(enhanced_tags)