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
        
        # User-specific chunking preferences (can be customized per user)
        self.user_preferences = {}
        
        # Default chunking strategy optimized for payment receipts and important emails
        self.default_payment_patterns = [
            r'\$[0-9]+\.?[0-9]*',  # Dollar amounts
            r'venmo|paypal|cashapp|zelle|apple pay|google pay',  # Payment apps
            r'receipt|confirmation|transaction|payment|invoice',  # Transaction terms
            r'you (sent|paid|received|charged)',  # Payment actions
        ]
        
        # User-customizable chunking configurations
        self.base_chunk_configs = {
            'payment_receipt': {
                'chunk_size': 300,
                'overlap': 50,
                'min_chunk_size': 20,  # Very low for short receipts
                'strategy': 'preserve_payments',
                'description': 'Payment receipts with transaction data preservation'
            },
            'short_email': {
                'chunk_size': 250,
                'overlap': 30,
                'min_chunk_size': 30,
                'strategy': 'minimal',
                'description': 'Short emails with minimal processing'
            },
            'medium_email': {
                'chunk_size': 500,
                'overlap': 75,
                'min_chunk_size': 50,
                'strategy': 'balanced',
                'description': 'Medium emails with balanced chunking'
            },
            'long_email': {
                'chunk_size': 800,
                'overlap': 100,
                'min_chunk_size': 100,
                'strategy': 'comprehensive',
                'description': 'Long emails with comprehensive context'
            },
            'default': {
                'chunk_size': 400,
                'overlap': 50,
                'min_chunk_size': 30,  # Lowered from 100
                'strategy': 'adaptive',
                'description': 'Adaptive processing based on content'
            }
        }
    
    def get_user_chunking_config(self, user_id: int) -> Dict:
        """Get user-specific chunking configuration."""
        if user_id in self.user_preferences:
            user_config = self.user_preferences[user_id]
            base_config = self.base_chunk_configs.get(user_config.get('strategy', 'default'), self.base_chunk_configs['default'])
            # Merge user preferences with base config
            config = base_config.copy()
            config.update(user_config)
            return config
        return self.base_chunk_configs['default']
    
    def set_user_chunking_preferences(self, user_id: int, preferences: Dict):
        """Set user-specific chunking preferences."""
        self.user_preferences[user_id] = preferences
        logger.info(f"Updated chunking preferences for user {user_id}: {preferences}")
    
    def detect_email_type(self, email_data: Dict) -> str:
        """Detect email type based on content patterns (simplified)."""
        content = ' '.join([
            email_data.get('subject', ''),
            email_data.get('body_text', ''),
            email_data.get('sender', '')
        ]).lower()
        
        # Check for payment patterns
        for pattern in self.default_payment_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return 'payment_receipt'
        
        # Check email length
        text_length = len(email_data.get('body_text', '') + email_data.get('body_html', ''))
        if text_length < 500:
            return 'short_email'
        elif text_length > 2000:
            return 'long_email'
        else:
            return 'medium_email'
    
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
            
            # Detect email type based on content patterns
            email_type = self.detect_email_type(email_data)
            
            # Get user-specific chunking configuration
            chunk_config = self.get_user_chunking_config(user_id)
            
            # Override config based on detected email type
            if email_type in self.base_chunk_configs:
                type_config = self.base_chunk_configs[email_type].copy()
                # Merge user preferences with type-specific config
                if user_id in self.user_preferences:
                    type_config.update(self.user_preferences[user_id])
                chunk_config = type_config
            
            # Generate email-specific metadata
            metadata = await self._create_email_metadata(email_data, user_id, email_type)
            
            # Chunk the email content using user-specific strategy
            chunks = await self._chunk_email_content_user_aware(processed_text, email_data, chunk_config)
            
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
                        'chunking_strategy': chunk_config.get('strategy', 'adaptive'),
                        'user_id': user_id
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
            
            logger.info(f"User {user_id}: Processed email '{metadata['subject'][:50]}...' ({email_type}) into {len(processed_chunks)} chunks using {chunk_config.get('strategy', 'adaptive')} strategy")
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
        
        # Preserve payment URLs, shorten others
        # First protect payment-related URLs
        payment_url_patterns = [
            r'venmo\.com[^\s]*',
            r'paypal\.com[^\s]*', 
            r'cashapp\.[^\s]*',
            r'zelle\.[^\s]*'
        ]
        
        protected_urls = []
        for i, pattern in enumerate(payment_url_patterns):
            matches = re.findall(f'https?://{pattern}', text, re.IGNORECASE)
            for match in matches:
                placeholder = f'[PAYMENT_URL_{i}]'
                text = text.replace(match, placeholder)
                protected_urls.append((placeholder, match))
        
        # Remove other URLs
        text = re.sub(r'https?://[^\s]+', '[URL]', text)
        
        # Restore payment URLs with simplified format
        for placeholder, original_url in protected_urls:
            domain = re.search(r'https?://([^/]+)', original_url)
            if domain:
                text = text.replace(placeholder, f'[{domain.group(1)}]')
            else:
                text = text.replace(placeholder, '[PAYMENT_URL]')
        
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
    
    async def _chunk_email_content_user_aware(self, text: str, email_data: Dict, chunk_config: Dict) -> List[Dict]:
        """User-aware email content chunking with payment preservation."""
        if not text:
            return []
        
        strategy = chunk_config.get('strategy', 'adaptive')
        
        # Apply chunking strategy based on user preferences
        if strategy == 'preserve_payments':
            return self._create_payment_aware_chunks(text, email_data, chunk_config)
        elif strategy == 'minimal':
            return self._create_minimal_chunks(text, email_data, chunk_config)
        elif strategy == 'comprehensive':
            return self._create_comprehensive_chunks(text, email_data, chunk_config)
        else:
            # Adaptive strategy (default)
            return self._create_adaptive_chunks(text, email_data, chunk_config)
    
    def _create_payment_aware_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create chunks optimized for payment receipt preservation."""
        chunks = []
        
        # Enhanced patterns that include dollar amounts
        payment_patterns = self.default_payment_patterns + [
            r'\$[0-9]+\.?[0-9]*',  # Dollar amounts like $9.99
            r'[0-9]+\.?[0-9]*\s*USD',  # USD amounts
            r'total|subtotal|amount|cost|price|fee',  # Amount-related words
        ]
        
        # For payment emails, use paragraph-based chunking but keep payment context together
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            # Fallback to line-based if no paragraphs
            paragraphs = [line.strip() for line in content.split('\n') if line.strip()]
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            # Check if this paragraph contains payment info
            has_payment_info = any(re.search(pattern, para, re.IGNORECASE) for pattern in payment_patterns)
            
            # Calculate potential chunk size
            potential_chunk_size = len(current_chunk) + len(para) + 2  # +2 for newlines
            
            # Decide whether to start a new chunk
            should_start_new_chunk = (
                potential_chunk_size > config['chunk_size'] and 
                current_chunk and 
                len(current_chunk.strip()) >= config.get('min_chunk_size', 20)
            )
            
            if should_start_new_chunk:
                # Save current chunk
                chunk_has_payment = any(re.search(pattern, current_chunk, re.IGNORECASE) for pattern in payment_patterns)
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": {
                        "chunk_index": chunk_index,
                        "chunk_type": "payment_transaction" if chunk_has_payment else "payment_context",
                        "contains_payment": chunk_has_payment
                    }
                })
                chunk_index += 1
                
                # Start new chunk with current paragraph
                current_chunk = para
            else:
                # Add to current chunk
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= config.get('min_chunk_size', 20):
            chunk_has_payment = any(re.search(pattern, current_chunk, re.IGNORECASE) for pattern in payment_patterns)
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": {
                    "chunk_index": chunk_index,
                    "chunk_type": "payment_transaction" if chunk_has_payment else "payment_context",
                    "contains_payment": chunk_has_payment
                }
            })
        
        return chunks
    
    def _create_minimal_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create minimal chunks for short emails."""
        # For very short emails, create one chunk if it meets minimum size
        if len(content.strip()) >= config.get('min_chunk_size', 30):
            return [{
                "content": content.strip(),
                "metadata": {
                    "chunk_index": 0,
                    "chunk_type": "minimal_complete"
                }
            }]
        return []
    
    def _create_comprehensive_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create comprehensive chunks for long emails with more context."""
        return self._create_adaptive_chunks(content, email_data, config)
    
    def _create_adaptive_chunks(self, content: str, email_data: Dict, config: Dict) -> List[Dict]:
        """Create adaptive chunks based on content structure."""
        chunks = []
        chunk_size = config['chunk_size']
        overlap = config.get('overlap', 50)
        min_chunk_size = config.get('min_chunk_size', 30)
        
        # Try paragraph-based chunking first
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if len(paragraphs) > 1:
            # Multi-paragraph email
            current_chunk = ""
            chunk_index = 0
            
            for para in paragraphs:
                if len(current_chunk) + len(para) > chunk_size and current_chunk:
                    if len(current_chunk.strip()) >= min_chunk_size:
                        chunks.append({
                            "content": current_chunk.strip(),
                            "metadata": {
                                "chunk_index": chunk_index,
                                "chunk_type": "adaptive_paragraph"
                            }
                        })
                        chunk_index += 1
                    
                    # Start new chunk with overlap
                    if overlap > 0 and current_chunk:
                        current_chunk = current_chunk[-overlap:] + "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    current_chunk += "\n\n" + para if current_chunk else para
            
            # Add final chunk
            if current_chunk.strip() and len(current_chunk.strip()) >= min_chunk_size:
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": {
                        "chunk_index": chunk_index,
                        "chunk_type": "adaptive_paragraph"
                    }
                })
        else:
            # Single paragraph or short email
            if len(content.strip()) >= min_chunk_size:
                chunks.append({
                    "content": content.strip(),
                    "metadata": {
                        "chunk_index": 0,
                        "chunk_type": "adaptive_single"
                    }
                })
        
        return chunks
    
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