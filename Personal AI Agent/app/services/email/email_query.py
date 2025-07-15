"""
Email query service for processing and routing email-specific queries.
Integrates with existing query router for unified search experience.
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

from app.services.embedding_service import SentenceTransformerEmbeddingService
from app.services.email.email_store import EmailStore
from app.utils.llm import generate_response
from app.exceptions import EmailProcessingError, VectorStoreError

logger = logging.getLogger(__name__)


class EmailQueryService:
    """Service for processing email-specific queries and generating responses."""
    
    def __init__(self):
        self.embedding_service = SentenceTransformerEmbeddingService()
        self.email_store = EmailStore()
        
        # Email query patterns for classification
        self.query_patterns = {
            'temporal': [
                r'(last|past|recent)\s+(week|month|year|day|days|weeks|months)',
                r'(today|yesterday|this week|this month|this year)',
                r'(january|february|march|april|may|june|july|august|september|october|november|december)',
                r'\b(2020|2021|2022|2023|2024|2025)\b',
                r'(before|after|since)\s+\d',
            ],
            'sender': [
                r'from\s+[\w@\.-]+',
                r'emails?\s+from\s+\w+',
                r'sent\s+by\s+\w+',
                r'@\w+\.\w+',
            ],
            'category': [
                r'(receipt|invoice|bill|payment)s?',
                r'(job|work|employment|offer)s?',
                r'(travel|flight|hotel|booking)s?',
                r'(newsletter|subscription)s?',
                r'(security|alert|notification)s?',
                r'(personal|family|friend)s?',
            ],
            'attachment': [
                r'(attachment|attached|file)s?',
                r'(pdf|doc|image|photo)s?',
                r'with\s+(file|attachment)',
            ]
        }
    
    async def process_email_query(
        self, 
        query: str, 
        user_id: int,
        max_results: int = 10
    ) -> Dict:
        """
        Process email query and return relevant results.
        
        Args:
            query: User's natural language query
            user_id: User ID for filtering
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Analyze query intent
            query_analysis = await self._analyze_query(query)
            
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Perform targeted search based on query analysis
            search_results = await self._execute_targeted_search(
                query_embedding=query_embedding,
                user_id=user_id,
                query_analysis=query_analysis,
                k=max_results
            )
            
            # Generate response
            response = await self._generate_email_response(
                query=query,
                search_results=search_results,
                query_analysis=query_analysis
            )
            
            return {
                'answer': response,
                'results': search_results,
                'query_analysis': query_analysis,
                'result_count': len(search_results)
            }
            
        except VectorStoreError:
            # Re-raise vector store specific errors
            raise
        except Exception as e:
            logger.error(f"Error processing email query: {e}")
            return {
                'answer': "I encountered an error while searching your emails. Please try rephrasing your query.",
                'results': [],
                'query_analysis': {},
                'result_count': 0
            }
    
    async def _analyze_query(self, query: str) -> Dict:
        """Analyze query to understand intent and extract filters."""
        analysis = {
            'intent': 'general',
            'filters': {},
            'temporal_context': None,
            'sender_context': None,
            'category_context': [],
            'attachment_context': False
        }
        
        query_lower = query.lower()
        
        # Detect temporal context
        temporal_info = self._extract_temporal_context(query_lower)
        if temporal_info:
            analysis['intent'] = 'temporal'
            analysis['temporal_context'] = temporal_info
            analysis['filters']['date_range'] = temporal_info.get('date_range')
        
        # Detect sender context
        sender_info = self._extract_sender_context(query_lower)
        if sender_info:
            analysis['intent'] = 'sender_focused'
            analysis['sender_context'] = sender_info
            analysis['filters']['sender_filter'] = sender_info
        
        # Detect category context
        categories = self._extract_category_context(query_lower)
        if categories:
            analysis['category_context'] = categories
            analysis['filters']['tags'] = categories
            if analysis['intent'] == 'general':
                analysis['intent'] = 'category_focused'
        
        # Detect attachment context
        if self._has_attachment_context(query_lower):
            analysis['attachment_context'] = True
            analysis['filters']['has_attachments'] = True
        
        return analysis
    
    def _extract_temporal_context(self, query: str) -> Optional[Dict]:
        """Extract temporal information from query."""
        now = datetime.now()
        
        # Recent time patterns
        if re.search(r'(today|recent)', query):
            return {
                'period': 'today',
                'date_range': (now.replace(hour=0, minute=0, second=0), now)
            }
        
        if re.search(r'yesterday', query):
            yesterday = now - timedelta(days=1)
            return {
                'period': 'yesterday',
                'date_range': (
                    yesterday.replace(hour=0, minute=0, second=0),
                    yesterday.replace(hour=23, minute=59, second=59)
                )
            }
        
        # Week patterns
        week_match = re.search(r'(last|past|this)\s+week', query)
        if week_match:
            if week_match.group(1) in ['last', 'past']:
                start_date = now - timedelta(days=now.weekday() + 7)
                end_date = now - timedelta(days=now.weekday() + 1)
            else:  # this week
                start_date = now - timedelta(days=now.weekday())
                end_date = now
            
            return {
                'period': f'{week_match.group(1)}_week',
                'date_range': (start_date.replace(hour=0, minute=0, second=0), end_date)
            }
        
        # Month patterns
        month_match = re.search(r'(last|past|this)\s+month', query)
        if month_match:
            if month_match.group(1) in ['last', 'past']:
                if now.month == 1:
                    start_date = now.replace(year=now.year-1, month=12, day=1)
                    end_date = now.replace(day=1) - timedelta(days=1)
                else:
                    start_date = now.replace(month=now.month-1, day=1)
                    end_date = now.replace(day=1) - timedelta(days=1)
            else:  # this month
                start_date = now.replace(day=1)
                end_date = now
            
            return {
                'period': f'{month_match.group(1)}_month',
                'date_range': (start_date.replace(hour=0, minute=0, second=0), end_date)
            }
        
        # Specific month names
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for month_name, month_num in months.items():
            if month_name in query:
                year = now.year
                if month_num > now.month:
                    year -= 1
                
                start_date = datetime(year, month_num, 1)
                if month_num == 12:
                    end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(year, month_num + 1, 1) - timedelta(days=1)
                
                return {
                    'period': month_name,
                    'date_range': (start_date, end_date.replace(hour=23, minute=59, second=59))
                }
        
        return None
    
    def _extract_sender_context(self, query: str) -> Optional[str]:
        """Extract sender information from query."""
        # Look for email addresses
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query)
        if email_match:
            return email_match.group(0)
        
        # Look for "from" patterns
        from_match = re.search(r'from\s+([\w\.-]+)', query)
        if from_match:
            return from_match.group(1)
        
        # Look for domain patterns
        domain_match = re.search(r'@([\w\.-]+\.\w+)', query)
        if domain_match:
            return domain_match.group(1)
        
        return None
    
    def _extract_category_context(self, query: str) -> List[str]:
        """Extract email categories from query."""
        categories = []
        
        category_keywords = {
            'receipt': ['receipt', 'invoice', 'bill', 'payment', 'purchase'],
            'job_offer': ['job', 'employment', 'offer', 'position', 'interview'],
            'travel': ['travel', 'flight', 'hotel', 'booking', 'trip'],
            'financial': ['bank', 'account', 'statement', 'balance'],
            'work': ['work', 'meeting', 'project', 'colleague'],
            'personal': ['personal', 'family', 'friend'],
            'newsletter': ['newsletter', 'subscription', 'digest'],
            'security': ['security', 'alert', 'password', 'login']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query for keyword in keywords):
                categories.append(category)
        
        return categories
    
    def _has_attachment_context(self, query: str) -> bool:
        """Check if query is asking about attachments."""
        attachment_keywords = [
            'attachment', 'attached', 'file', 'pdf', 'doc', 'document', 'image'
        ]
        return any(keyword in query for keyword in attachment_keywords)
    
    async def _execute_targeted_search(
        self,
        query_embedding: List[float],
        user_id: int,
        query_analysis: Dict,
        k: int
    ) -> List[Dict]:
        """Execute search based on query analysis."""
        
        # Extract filters from analysis
        filters = query_analysis.get('filters', {})
        
        # Perform search with filters
        results = self.email_store.search_emails(
            query_embedding=query_embedding,
            user_id=user_id,
            tags=filters.get('tags'),
            date_range=filters.get('date_range'),
            sender_filter=filters.get('sender_filter'),
            k=k
        )
        
        return results
    
    async def _generate_email_response(
        self,
        query: str,
        search_results: List[Dict],
        query_analysis: Dict
    ) -> str:
        """Generate natural language response for email query."""
        
        if not search_results:
            return self._generate_no_results_response(query_analysis)
        
        # Prepare context from search results
        context_pieces = []
        for result in search_results[:5]:  # Use top 5 results
            metadata = result['metadata']
            context_pieces.append(
                f"Email from {metadata.get('sender', 'Unknown')} "
                f"on {metadata.get('date', 'Unknown date')}: "
                f"Subject: {metadata.get('subject', 'No subject')} "
                f"Content: {result['text'][:200]}..."
            )
        
        context = '\n\n'.join(context_pieces)
        
        # Create email-specific prompt
        prompt = f"""Based on the following email content, answer the user's query about their emails.

User Query: {query}

Relevant Emails:
{context}

Please provide a helpful answer that:
1. Directly addresses the user's question
2. References specific emails when relevant (mention sender, date, subject)
3. Summarizes key information found
4. Is conversational and natural

Answer:"""
        
        try:
            response = generate_response(prompt, [])
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating email response: {e}")
            # For response generation errors, return a safe fallback message
            return f"I found {len(search_results)} relevant emails for your query, but I encountered an error generating a detailed response."
    
    def _generate_no_results_response(self, query_analysis: Dict) -> str:
        """Generate response when no emails are found."""
        intent = query_analysis.get('intent', 'general')
        
        if intent == 'temporal':
            temporal = query_analysis.get('temporal_context', {})
            period = temporal.get('period', 'that time period')
            return f"I couldn't find any emails from {period}. You might want to try a different time range or check if you have emails from that period."
        
        elif intent == 'sender_focused':
            sender = query_analysis.get('sender_context', 'that sender')
            return f"I couldn't find any emails from {sender}. Please check the sender's email address or try searching for a partial match."
        
        elif intent == 'category_focused':
            categories = query_analysis.get('category_context', [])
            if categories:
                category_str = ', '.join(categories)
                return f"I couldn't find any emails categorized as {category_str}. You might want to try broader search terms."
        
        return "I couldn't find any emails matching your query. Try using different keywords or check if you have emails that match your criteria."