"""
Email classification service for categorizing emails with tags.
Extends the existing document classifier for email-specific patterns.
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailClassifier:
    """Classifier for email content and metadata."""
    
    def __init__(self):
        self.categories = {
            'receipt': {
                'keywords': [
                    'receipt', 'invoice', 'payment', 'order', 'purchase',
                    'transaction', 'confirmation', 'billing', 'paid',
                    'total amount', 'subtotal', 'tax', 'shipping'
                ],
                'patterns': [
                    r'\$\d+\.\d{2}',  # Dollar amounts
                    r'order\s+#?\d+',  # Order numbers
                    r'invoice\s+#?\d+',  # Invoice numbers
                    r'receipt\s+#?\d+',  # Receipt numbers
                ],
                'domains': [
                    'amazon.com', 'ebay.com', 'paypal.com', 'stripe.com',
                    'square.com', 'shopify.com', 'etsy.com'
                ]
            },
            'job_offer': {
                'keywords': [
                    'job offer', 'employment', 'position', 'salary',
                    'benefits', 'start date', 'onboarding', 'welcome',
                    'congratulations', 'hired', 'compensation'
                ],
                'patterns': [
                    r'salary.*\$[\d,]+',
                    r'annual.*\$[\d,]+',
                    r'start.*date',
                    r'first.*day'
                ],
                'domains': [
                    'linkedin.com', 'indeed.com', 'glassdoor.com',
                    'workday.com', 'bamboohr.com'
                ]
            },
            'travel': {
                'keywords': [
                    'flight', 'hotel', 'booking', 'reservation',
                    'itinerary', 'confirmation', 'check-in', 'departure',
                    'arrival', 'boarding', 'gate', 'seat'
                ],
                'patterns': [
                    r'flight\s+[A-Z]{2}\d+',  # Flight numbers
                    r'confirmation.*[A-Z0-9]{6,}',  # Confirmation codes
                    r'\d{1,2}:\d{2}\s*(AM|PM)',  # Times
                ],
                'domains': [
                    'booking.com', 'expedia.com', 'hotels.com',
                    'airbnb.com', 'delta.com', 'united.com', 'american.com'
                ]
            },
            'newsletter': {
                'keywords': [
                    'newsletter', 'unsubscribe', 'weekly', 'monthly',
                    'digest', 'updates', 'subscribe', 'mailing list'
                ],
                'patterns': [
                    r'unsubscribe',
                    r'view.*online',
                    r'forward.*friend'
                ],
                'domains': [
                    'mailchimp.com', 'constantcontact.com', 'substack.com'
                ]
            },
            'financial': {
                'keywords': [
                    'bank', 'statement', 'balance', 'account', 'deposit',
                    'withdrawal', 'transfer', 'credit', 'debit', 'overdraft',
                    'interest', 'fee', 'transaction'
                ],
                'patterns': [
                    r'account.*\d{4,}',  # Account numbers
                    r'balance.*\$[\d,]+\.\d{2}',
                    r'available.*\$[\d,]+\.\d{2}'
                ],
                'domains': [
                    'chase.com', 'bankofamerica.com', 'wellsfargo.com',
                    'citi.com', 'usbank.com', 'capitalone.com'
                ]
            },
            'work': {
                'keywords': [
                    'meeting', 'project', 'deadline', 'report', 'presentation',
                    'team', 'colleague', 'manager', 'client', 'proposal'
                ],
                'patterns': [
                    r'meeting.*\d{1,2}:\d{2}',
                    r'deadline.*\d{1,2}/\d{1,2}',
                    r'project.*update'
                ],
                'domains': []  # Work emails vary by company
            },
            'personal': {
                'keywords': [
                    'family', 'friend', 'birthday', 'anniversary',
                    'vacation', 'dinner', 'lunch', 'weekend', 'party'
                ],
                'patterns': [],
                'domains': [
                    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'
                ]
            },
            'security': {
                'keywords': [
                    'security', 'alert', 'password', 'login', 'unauthorized',
                    'suspicious', 'verify', 'authentication', 'two-factor',
                    'reset', 'breach', 'phishing'
                ],
                'patterns': [
                    r'login.*attempt',
                    r'password.*reset',
                    r'security.*code',
                    r'verify.*account'
                ],
                'domains': []
            },
            'promotional': {
                'keywords': [
                    'sale', 'discount', 'offer', 'deal', 'coupon',
                    'promotion', 'limited time', 'special', 'save',
                    'free shipping', 'clearance'
                ],
                'patterns': [
                    r'\d+%\s*off',
                    r'save.*\$\d+',
                    r'free.*shipping'
                ],
                'domains': []
            }
        }
    
    def classify_email(self, email_data: Dict) -> List[str]:
        """
        Classify email and return list of tags.
        
        Args:
            email_data: Parsed email data from EmailIngestionService
            
        Returns:
            List of classification tags
        """
        tags = []
        
        # Combine text for analysis
        text_content = ' '.join([
            email_data.get('subject', ''),
            email_data.get('body_text', ''),
            email_data.get('sender', '')
        ]).lower()
        
        sender_domain = self._extract_domain(email_data.get('sender', ''))
        
        # Check each category
        for category, criteria in self.categories.items():
            score = 0
            
            # Check keywords
            for keyword in criteria['keywords']:
                if keyword.lower() in text_content:
                    score += 1
            
            # Check patterns
            for pattern in criteria['patterns']:
                if re.search(pattern, text_content, re.IGNORECASE):
                    score += 2
            
            # Check sender domain
            if sender_domain and sender_domain in criteria['domains']:
                score += 3
            
            # Add tag if score meets threshold
            if score >= 1:  # Minimum threshold
                tags.append(category)
        
        # Add temporal tags
        tags.extend(self._get_temporal_tags(email_data))
        
        # Add priority tags
        tags.extend(self._get_priority_tags(email_data))
        
        # Ensure at least one tag
        if not tags:
            tags.append('general')
        
        return list(set(tags))  # Remove duplicates
    
    def _extract_domain(self, email_address: str) -> Optional[str]:
        """Extract domain from email address."""
        if not email_address:
            return None
        
        # Use regex to extract email from various formats
        email_match = re.search(r'[\w\.-]+@([\w\.-]+)', email_address)
        if email_match:
            return email_match.group(1).lower()
        
        return None
    
    def _get_temporal_tags(self, email_data: Dict) -> List[str]:
        """Generate temporal tags based on email date."""
        tags = []
        date = email_data.get('date')
        
        if not date or not isinstance(date, datetime):
            return tags
        
        now = datetime.now(date.tzinfo) if date.tzinfo else datetime.now()
        days_ago = (now - date).days
        
        if days_ago < 1:
            tags.append('today')
        elif days_ago < 7:
            tags.append('this_week')
        elif days_ago < 30:
            tags.append('this_month')
        elif days_ago < 365:
            tags.append('this_year')
        else:
            tags.append('older')
        
        # Add day of week and month
        tags.append(f'day_{date.strftime("%A").lower()}')
        tags.append(f'month_{date.strftime("%B").lower()}')
        
        return tags
    
    def _get_priority_tags(self, email_data: Dict) -> List[str]:
        """Generate priority tags based on email characteristics."""
        tags = []
        subject = email_data.get('subject', '').lower()
        
        # High priority indicators
        high_priority_keywords = [
            'urgent', 'asap', 'immediate', 'emergency', 'critical',
            'important', 'action required', 'deadline'
        ]
        
        if any(keyword in subject for keyword in high_priority_keywords):
            tags.append('high_priority')
        
        # Auto-generated email indicators
        auto_keywords = [
            'noreply', 'no-reply', 'donotreply', 'automated',
            'notification', 'alert', 'reminder'
        ]
        
        sender = email_data.get('sender', '').lower()
        if any(keyword in sender for keyword in auto_keywords):
            tags.append('automated')
        
        # Attachment indicator
        if email_data.get('attachments'):
            tags.append('has_attachments')
        
        return tags
    
    def get_category_priority(self, tags: List[str]) -> int:
        """
        Get priority score for email categories.
        Higher score = higher priority for search ranking.
        """
        priority_map = {
            'security': 10,
            'job_offer': 9,
            'financial': 8,
            'receipt': 7,
            'work': 6,
            'travel': 5,
            'personal': 4,
            'newsletter': 2,
            'promotional': 1,
            'general': 3
        }
        
        max_priority = 0
        for tag in tags:
            if tag in priority_map:
                max_priority = max(max_priority, priority_map[tag])
        
        return max_priority