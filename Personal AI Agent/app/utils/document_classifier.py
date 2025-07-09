"""
PDF Document Type Classifier

Classifies PDF documents into one of three optimized categories:
- financial: Transaction-based documents (bank statements, invoices, receipts)
  * Processing: Small 500-char chunks for precise transaction matching
  * Strategy: Structured parsing with exact match capabilities
- long_form: Documents 20+ pages (research papers, reports, contracts, manuals)
  * Processing: Large 1500-char chunks for comprehensive context
  * Strategy: Semantic analysis with deep understanding
- generic: Personal documents (resumes, letters, personal documents)
  * Processing: Balanced 1000-char chunks for hybrid approach
  * Strategy: Balanced precision and recall
"""

import re
import logging
from typing import Tuple, Dict, Any
from pathlib import Path

logger = logging.getLogger("personal_ai_agent")


class DocumentClassifier:
    """
    Classifies documents and determines optimal chunking strategy based on content and type
    
    Document Types:
    - financial: Bank statements, transactions - 1 transaction per chunk  
    - long_form: Reports, articles 20+ pages - ~500 tokens per chunk with overlap
    - generic: Resumes, structured docs - section-based chunking
    """
    
    def __init__(self):
        """Initialize the document classifier with adaptive chunking strategies"""
        
        # Adaptive chunking strategies per document type
        self.chunking_strategies = {
            "financial": {
                "strategy": "transaction_level",
                "description": "1 transaction per chunk for precise retrieval",
                "target_chunks": "1_per_transaction",
                "overlap": "contextual",
                "example": "100 transactions → 100 chunks"
            },
            "long_form": {
                "strategy": "token_based", 
                "description": "~500 tokens per chunk with overlap",
                "target_chunks": "500_tokens",
                "overlap": "50_tokens",
                "example": "20-page report → ~40 chunks (500 tokens each)"
            },
            "generic": {
                "strategy": "section_based",
                "description": "Section-based chunking with structure awareness",
                "target_chunks": "5_to_10_sections",
                "overlap": "section_aware",
                "example": "Resume with sections → 5-10 chunks (section-based)"
            }
        }
        
        # Financial document patterns
        self.financial_patterns = {
            "strong_indicators": [
                r'(bank|banking)\s+statement',
                r'account\s+summary',
                r'transaction\s+(history|details)',
                r'debit\s+card\s+activity',
                r'credit\s+card\s+statement',
                r'beginning\s+balance',
                r'ending\s+balance',
                r'available\s+balance'
            ],
            "transaction_patterns": [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}.*?\$?\d+\.\d{2}',  # Date + amount
                r'(debit|credit|payment|deposit|withdrawal|transfer).*?\$?\d+\.\d{2}',
                r'zelle\s+payment',
                r'ach\s+(debit|credit)',
                r'wire\s+transfer',
                r'online\s+transfer'
            ],
            "financial_keywords": [
                'account', 'balance', 'transaction', 'payment', 'deposit', 
                'withdrawal', 'transfer', 'statement', 'debit', 'credit',
                'zelle', 'paypal', 'venmo', 'ach', 'wire', 'fee', 'interest'
            ]
        }
        
        # Long-form document patterns  
        self.long_form_patterns = {
            "structural_indicators": [
                r'table\s+of\s+contents',
                r'chapter\s+\d+',
                r'section\s+\d+',
                r'abstract',
                r'introduction',
                r'conclusion',
                r'bibliography',
                r'references',
                r'appendix'
            ],
            "academic_patterns": [
                r'research\s+(paper|study|report)',
                r'literature\s+review',
                r'methodology',
                r'results\s+(and\s+)?discussion',
                r'data\s+analysis',
                r'case\s+study'
            ],
            "length_indicators": [
                r'page\s+\d{2,}',  # Page numbers in double digits
                r'(\d{2,}\s+pages?)',  # References to 10+ pages
            ]
        }
        
        # Generic structured document patterns
        self.generic_patterns = {
            "resume_indicators": [
                r'(professional\s+)?(experience|employment)',
                r'work\s+history',
                r'education',
                r'academic\s+background',
                r'skills',
                r'technical\s+skills',
                r'certifications?',
                r'achievements?',
                r'projects?',
                r'objective',
                r'summary',
                r'contact\s+information',
                r'references'
            ],
            "report_indicators": [
                r'executive\s+summary',
                r'overview',
                r'findings',
                r'recommendations',
                r'next\s+steps',
                r'action\s+items'
            ],
            "structured_patterns": [
                r'^\s*[A-Z][A-Z\s]{5,30}\s*$',  # ALL CAPS section headers
                r'^\s*\d+\.\s+[A-Z]',  # Numbered sections
                r'^\s*[•\-\*]\s+',  # Bullet points
            ]
        }
    
    def classify_document(self, content: str, filename: str = "") -> Tuple[str, Dict[str, Any]]:
        """
        Classify document type and determine optimal chunking strategy
        
        Args:
            content: Document text content
            filename: Optional filename for additional context
            
        Returns:
            Tuple of (document_type, classification_metadata)
        """
        try:
            logger.info(f"Classifying document: {filename}")
            
            content_lower = content.lower()
            content_lines = content.split('\n')
            
            # Initialize classification scores
            scores = {
                "financial": 0,
                "long_form": 0, 
                "generic": 0
            }
            
            classification_details = {
                "content_length": len(content),
                "line_count": len(content_lines),
                "avg_line_length": len(content) / len(content_lines) if content_lines else 0,
                "filename": filename
            }
            
            # Score financial indicators
            financial_score, financial_details = self._score_financial_content(content_lower, content_lines)
            scores["financial"] = financial_score
            classification_details["financial"] = financial_details
            
            # Score long-form indicators
            long_form_score, long_form_details = self._score_long_form_content(content_lower, content_lines)
            scores["long_form"] = long_form_score
            classification_details["long_form"] = long_form_details
            
            # Score generic structured indicators
            generic_score, generic_details = self._score_generic_content(content_lower, content_lines)
            scores["generic"] = generic_score
            classification_details["generic"] = generic_details
            
            # Determine document type based on highest score
            document_type = max(scores, key=scores.get)
            confidence = scores[document_type]
            
            # Apply minimum confidence thresholds
            if confidence < 0.3:
                document_type = "generic"  # Default fallback
                confidence = 0.3
            
            # Add chunking strategy information
            chunking_strategy = self.chunking_strategies[document_type].copy()
            
            classification_metadata = {
                "document_type": document_type,
                "confidence": confidence,
                "scores": scores,
                "chunking_strategy": chunking_strategy,
                "classification_details": classification_details,
                "adaptive_chunking": True
            }
            
            logger.info(f"Classified as {document_type} (confidence: {confidence:.2f}) - Strategy: {chunking_strategy['strategy']}")
            return document_type, classification_metadata
            
        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            # Fallback classification
            return "generic", {
                "document_type": "generic",
                "confidence": 0.1,
                "error": str(e),
                "chunking_strategy": self.chunking_strategies["generic"],
                "adaptive_chunking": True
            }
    
    def _score_financial_content(self, content_lower: str, lines: list) -> Tuple[float, Dict[str, Any]]:
        """
        Score content for financial document characteristics
        
        Args:
            content_lower: Lowercase content
            lines: Content split into lines
            
        Returns:
            Tuple of (score, details)
        """
        score = 0.0
        details = {
            "strong_indicators": 0,
            "transaction_count": 0,
            "keyword_matches": 0,
            "has_account_numbers": False,
            "has_balances": False,
            "transaction_density": 0.0
        }
        
        # Check for strong financial indicators
        for pattern in self.financial_patterns["strong_indicators"]:
            if re.search(pattern, content_lower):
                details["strong_indicators"] += 1
                score += 0.3  # Strong weight for clear indicators
        
        # Count transaction-like lines
        transaction_count = 0
        for line in lines:
            for pattern in self.financial_patterns["transaction_patterns"]:
                if re.search(pattern, line, re.IGNORECASE):
                    transaction_count += 1
                    break
        
        details["transaction_count"] = transaction_count
        details["transaction_density"] = transaction_count / len(lines) if lines else 0
        
        # High transaction density indicates financial document
        if details["transaction_density"] > 0.1:  # 10%+ of lines are transactions
            score += 0.4
        elif details["transaction_density"] > 0.05:  # 5%+ of lines are transactions
            score += 0.2
        
        # Check for financial keywords
        keyword_matches = 0
        for keyword in self.financial_patterns["financial_keywords"]:
            if keyword in content_lower:
                keyword_matches += 1
        
        details["keyword_matches"] = keyword_matches
        if keyword_matches >= 5:
            score += 0.2
        elif keyword_matches >= 3:
            score += 0.1
        
        # Check for account numbers and balances
        if re.search(r'account\s+(number|#)', content_lower):
            details["has_account_numbers"] = True
            score += 0.1
            
        if re.search(r'(beginning|ending|current|available)\s+balance', content_lower):
            details["has_balances"] = True
            score += 0.1
        
        return min(score, 1.0), details
    
    def _score_long_form_content(self, content_lower: str, lines: list) -> Tuple[float, Dict[str, Any]]:
        """
        Score content for long-form document characteristics
        
        Args:
            content_lower: Lowercase content
            lines: Content split into lines
            
        Returns:
            Tuple of (score, details)
        """
        score = 0.0
        details = {
            "structural_indicators": 0,
            "academic_patterns": 0,
            "estimated_pages": 0,
            "has_toc": False,
            "has_chapters": False,
            "content_density": 0.0
        }
        
        # Check for structural indicators
        for pattern in self.long_form_patterns["structural_indicators"]:
            if re.search(pattern, content_lower):
                details["structural_indicators"] += 1
                
                if "table" in pattern and "contents" in pattern:
                    details["has_toc"] = True
                    score += 0.2
                elif "chapter" in pattern:
                    details["has_chapters"] = True
                    score += 0.15
                else:
                    score += 0.1
        
        # Check for academic patterns
        for pattern in self.long_form_patterns["academic_patterns"]:
            if re.search(pattern, content_lower):
                details["academic_patterns"] += 1
                score += 0.1
        
        # Estimate document length
        content_length = len(' '.join(lines))
        estimated_pages = content_length / 2500  # Rough estimate: 2500 chars per page
        details["estimated_pages"] = estimated_pages
        details["content_density"] = content_length / len(lines) if lines else 0
        
        # Score based on length
        if estimated_pages >= 20:
            score += 0.3  # Definitely long-form
        elif estimated_pages >= 10:
            score += 0.2  # Likely long-form
        elif estimated_pages >= 5:
            score += 0.1  # Possibly long-form
        
        # High content density suggests academic/technical content
        if details["content_density"] > 80:  # Long lines suggest prose
            score += 0.1
        
        return min(score, 1.0), details
    
    def _score_generic_content(self, content_lower: str, lines: list) -> Tuple[float, Dict[str, Any]]:
        """
        Score content for generic structured document characteristics
        
        Args:
            content_lower: Lowercase content
            lines: Content split into lines
            
        Returns:
            Tuple of (score, details)
        """
        score = 0.0
        details = {
            "resume_indicators": 0,
            "report_indicators": 0,
            "structured_sections": 0,
            "bullet_points": 0,
            "has_contact_info": False,
            "section_density": 0.0
        }
        
        # Check for resume indicators
        for pattern in self.generic_patterns["resume_indicators"]:
            if re.search(pattern, content_lower):
                details["resume_indicators"] += 1
                score += 0.15
        
        # Check for report indicators
        for pattern in self.generic_patterns["report_indicators"]:
            if re.search(pattern, content_lower):
                details["report_indicators"] += 1
                score += 0.1
        
        # Count structured patterns
        structured_sections = 0
        bullet_points = 0
        
        for line in lines:
            # Check for section headers
            for pattern in self.generic_patterns["structured_patterns"]:
                if re.search(pattern, line):
                    if "A-Z" in pattern:  # Section header
                        structured_sections += 1
                    elif "•\\-\\*" in pattern:  # Bullet point
                        bullet_points += 1
                    break
        
        details["structured_sections"] = structured_sections
        details["bullet_points"] = bullet_points
        details["section_density"] = structured_sections / len(lines) if lines else 0
        
        # Score based on structure
        if structured_sections >= 3:
            score += 0.3  # Well-structured document
        elif structured_sections >= 1:
            score += 0.15
        
        if bullet_points >= 5:
            score += 0.1  # Lists suggest structured content
        
        # Check for contact information (suggests resume/profile)
        if re.search(r'(email|phone|address|linkedin)', content_lower):
            details["has_contact_info"] = True
            score += 0.1
        
        # Base score for any document (ensures minimum for fallback)
        score += 0.1
        
        return min(score, 1.0), details
    
    def get_recommended_processor_config(self, document_type: str) -> Dict[str, Any]:
        """
        Get recommended processor configuration for document type
        
        Args:
            document_type: Classified document type
            
        Returns:
            Dictionary with processor configuration
        """
        base_config = {
            "document_type": document_type,
            "chunking_strategy": self.chunking_strategies.get(document_type, self.chunking_strategies["generic"])
        }
        
        if document_type == "financial":
            return {
                **base_config,
                "processor_class": "FinancialDocumentProcessor",
                "chunking_approach": "transaction_level",
                "expected_chunks": "1_per_transaction",
                "retrieval_optimization": "precise_transaction_matching"
            }
        
        elif document_type == "long_form":
            return {
                **base_config,
                "processor_class": "BaseDocumentProcessor",
                "chunking_approach": "token_based",
                "target_tokens_per_chunk": 500,
                "overlap_tokens": 50,
                "retrieval_optimization": "semantic_context_preservation"
            }
        
        else:  # generic
            return {
                **base_config,
                "processor_class": "BaseDocumentProcessor", 
                "chunking_approach": "section_based",
                "target_sections": "5_to_10",
                "retrieval_optimization": "section_aware_search"
            }
    
    def analyze_chunking_potential(self, content: str, document_type: str) -> Dict[str, Any]:
        """
        Analyze content to estimate chunking results
        
        Args:
            content: Document content
            document_type: Classified document type
            
        Returns:
            Analysis of expected chunking performance
        """
        analysis = {
            "document_type": document_type,
            "content_length": len(content),
            "estimated_chunks": 0,
            "average_chunk_size": 0,
            "chunking_efficiency": "unknown"
        }
        
        if document_type == "financial":
            # Count potential transactions
            lines = content.split('\n')
            transaction_lines = 0
            for line in lines:
                for pattern in self.financial_patterns["transaction_patterns"]:
                    if re.search(pattern, line, re.IGNORECASE):
                        transaction_lines += 1
                        break
            
            analysis.update({
                "estimated_chunks": transaction_lines,
                "average_chunk_size": "1_transaction",
                "chunking_efficiency": "optimal" if transaction_lines > 10 else "moderate",
                "transaction_density": transaction_lines / len(lines) if lines else 0
            })
        
        elif document_type == "long_form":
            # Estimate token-based chunks
            estimated_tokens = len(content) // 4  # Rough token estimate
            estimated_chunks = estimated_tokens // 500  # 500 tokens per chunk
            
            analysis.update({
                "estimated_chunks": max(1, estimated_chunks),
                "average_chunk_size": "~500_tokens",
                "chunking_efficiency": "optimal" if estimated_chunks > 20 else "good",
                "estimated_tokens": estimated_tokens
            })
        
        else:  # generic
            # Count potential sections
            content_lower = content.lower()
            section_count = 0
            for pattern in self.generic_patterns["resume_indicators"] + self.generic_patterns["report_indicators"]:
                section_count += len(re.findall(pattern, content_lower))
            
            analysis.update({
                "estimated_chunks": max(5, min(section_count, 15)),  # 5-15 section-based chunks
                "average_chunk_size": "section_based",
                "chunking_efficiency": "optimal" if section_count >= 5 else "good",
                "detected_sections": section_count
            })
        
        return analysis


def detect_document_type(text: str, filename: str, metadata: Dict[str, Any] = None) -> str:
    """
    Classify a document into one of three types based on content, filename, and metadata.
    
    Args:
        text: Extracted text content from the document
        filename: Original filename of the document
        metadata: Optional metadata (e.g., page_count for PDFs)
        
    Returns:
        One of: 'financial', 'long_form', 'generic'
    """
    try:
        # Normalize inputs
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Check for financial document first
        if _is_financial_document(text_lower, filename_lower):
            logger.info(f"Classified '{filename}' as financial document")
            return "financial"
        
        # Check for long-form document (with page count priority)
        if _is_long_form_document(text, metadata):
            logger.info(f"Classified '{filename}' as long_form document")
            return "long_form"
        
        # Default to generic
        logger.info(f"Classified '{filename}' as generic document")
        return "generic"
        
    except Exception as e:
        logger.error(f"Error classifying document '{filename}': {e}")
        # Default to generic on error
        return "generic"


def _is_financial_document(text_lower: str, filename_lower: str) -> bool:
    """
    Check if PDF document is financial based on filename and content patterns.
    Enhanced for PDF-specific financial document detection.
    
    Args:
        text_lower: Lowercase text content
        filename_lower: Lowercase filename
        
    Returns:
        True if document appears to be financial
    """
    # Enhanced filename patterns for PDF financial documents
    financial_filename_patterns = [
        'statement', 'bank', 'invoice', 'transactions', 'receipt',
        'billing', 'payment', 'account', 'expense', 'tax', '1099',
        'w2', 'w-2', 'payroll', 'credit_card', 'mortgage', 'loan',
        'irs', 'financial', 'budget', 'quarterly', 'annual_report'
    ]
    
    if any(pattern in filename_lower for pattern in financial_filename_patterns):
        return True
    
    # Enhanced financial text patterns for PDF documents
    financial_phrases = [
        "available balance", "transaction date", "debit", "credit", 
        "account number", "posted", "payment", "reference number",
        "routing number", "transaction id", "merchant", "authorization",
        "pending", "cleared", "deposit", "withdrawal", "transfer",
        "beginning balance", "ending balance", "statement period",
        "interest earned", "service charge", "overdraft", "ach payment",
        "direct deposit", "check number", "atm withdrawal", "pos transaction",
        "wire transfer", "online payment", "mobile deposit", "fee assessed"
    ]
    
    # Count occurrences of financial phrases
    phrase_count = sum(1 for phrase in financial_phrases if phrase in text_lower)
    
    if phrase_count >= 3:
        return True
    
    # Check for date + dollar amount patterns (transaction patterns)
    # Look for patterns like: MM/DD/YYYY followed by $X.XX or -$X.XX
    date_dollar_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b.*?[-$]\$?\d+\.\d{2}'
    matches = re.findall(date_dollar_pattern, text_lower)
    
    if len(matches) >= 5:  # Multiple transaction-like patterns
        return True
    
    # Check for multiple dollar amounts (could indicate transactions)
    dollar_pattern = r'[-$]\$?\d+\.\d{2}'
    dollar_matches = re.findall(dollar_pattern, text_lower)
    
    if len(dollar_matches) >= 10:  # Many dollar amounts suggest financial document
        return True
    
    return False


def _is_long_form_document(text: str, metadata: Dict[str, Any] = None) -> bool:
    """
    Check if PDF document is long-form based on page count, length and structure.
    Enhanced for PDF documents with 20+ pages requiring deep semantic analysis.
    
    Args:
        text: Original text content (preserving case and formatting)
        metadata: Optional metadata containing page_count and other PDF info
        
    Returns:
        True if document appears to be long-form (20+ pages)
    """
    # Priority 1: Check page count from PDF metadata (most accurate)
    if metadata and isinstance(metadata, dict):
        page_count = metadata.get('page_count')
        if page_count is not None:
            logger.info(f"Using PDF page count: {page_count} pages")
            if page_count >= 20:
                logger.info(f"Document classified as long-form due to page count: {page_count} >= 20")
                return True
            elif page_count < 5:
                logger.info(f"Document classified as short due to page count: {page_count} < 5")
                return False
            # For 5-19 pages, continue with content analysis
    
    # Priority 2: Enhanced token estimation for PDF documents
    # PDFs typically have more formatting characters
    estimated_tokens = len(text) / 3.5
    
    # Threshold for 20+ page documents (approximately 6,000+ tokens)
    # Lowered from 8000 to 6000 to account for 20-page threshold instead of 50
    if estimated_tokens <= 6000:
        return False
    
    # Check for multi-paragraph sections (2+ consecutive line breaks)
    paragraph_breaks = text.split('\n\n')
    multi_paragraph_sections = len([section for section in paragraph_breaks if section.strip()])
    
    if multi_paragraph_sections < 5:
        return False
    
    # Check that it doesn't have clear transaction or table patterns
    text_lower = text.lower()
    
    # Look for table-like structures or transaction patterns
    table_indicators = [
        '\t', '|', '  +', '---', '===',  # Common table formatting
        'total:', 'subtotal:', 'amount due:'  # Invoice/statement patterns
    ]
    
    # If document has many table indicators, it might be structured financial data
    table_count = sum(1 for indicator in table_indicators if indicator in text_lower)
    
    # Look for transaction-like patterns
    transaction_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b.*?\$\d+\.\d{2}',  # Date + amount
        r'\b(debit|credit|payment|deposit|withdrawal)\b.*?\$\d+\.\d{2}'  # Transaction type + amount
    ]
    
    transaction_count = sum(len(re.findall(pattern, text_lower)) for pattern in transaction_patterns)
    
    # If document has high table/transaction indicators, it's likely structured, not long-form
    if table_count > 10 or transaction_count > 5:
        return False
    
    return True


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for a text string.
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    # Rough approximation: 1 token ≈ 4 characters for English text
    return len(text) // 4


def get_document_type_metadata(document_type: str) -> dict:
    """
    Get enhanced metadata and processing recommendations for PDF document types.
    
    Args:
        document_type: The classified document type
        
    Returns:
        Dictionary with processing metadata optimized for each category
    """
    metadata = {
        "financial": {
            "recommended_chunk_size": 200,
            "recommended_overlap": 20,
            "processing_priority": "structured",
            "search_strategy": "exact_match",
            "description": "Transaction-based documents requiring precise data extraction",
            "use_cases": ["expense tracking", "transaction analysis", "budget questions"],
            "pagination_strategy": "transaction_level",
            "context_preservation": "minimal_overlap"
        },
        "long_form": {
            "recommended_chunk_size": 600,
            "recommended_overlap": 100,
            "processing_priority": "semantic",
            "search_strategy": "semantic_similarity",
            "description": "Comprehensive documents requiring deep understanding",
            "use_cases": ["research queries", "document analysis", "comprehensive insights"],
            "pagination_strategy": "semantic_sections",
            "context_preservation": "narrative_flow"
        },
        "generic": {
            "recommended_chunk_size": 400,
            "recommended_overlap": 80,
            "processing_priority": "balanced",
            "search_strategy": "hybrid",
            "description": "Personal documents with balanced processing needs",
            "use_cases": ["resume queries", "personal document search", "general information"],
            "pagination_strategy": "logical_sections",
            "context_preservation": "moderate_overlap"
        }
    }
    
    return metadata.get(document_type, metadata["generic"])