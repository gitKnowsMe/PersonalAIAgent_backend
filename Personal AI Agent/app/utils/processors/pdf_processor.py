"""
PDF document processor with adaptive chunking strategies
Optimized for different document types: financial, long-form, and generic
"""

import logging
import os
from typing import Dict, Any, List

from langchain_community.document_loaders import PyPDFLoader
from pypdf import PdfReader
from langchain_core.documents import Document as LangchainDocument
from app.utils.processors.base_processor import BaseDocumentProcessor

logger = logging.getLogger("personal_ai_agent")


class PDFDocumentProcessor(BaseDocumentProcessor):
    """
    PDF processor with adaptive chunking based on document type
    - Financial documents: Transaction-level chunking
    - Long-form documents: Token-based chunking (~500 tokens)
    - Generic documents: Section-based chunking
    """
    
    def __init__(self, document_type: str = "generic", chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize PDF processor with document type for adaptive chunking
        
        Args:
            document_type: Type of document (financial, long_form, generic)
            chunk_size: Custom chunk size (optional)
            chunk_overlap: Custom chunk overlap (optional)
        """
        self.document_type = document_type
        
        # Choose chunking strategy based on document type
        if document_type == "financial":
            chunking_strategy = "adaptive"  # Will use financial processor's transaction-level chunking
        elif document_type == "long_form":
            chunking_strategy = "token_based"  # 500 tokens per chunk
        else:  # generic
            chunking_strategy = "adaptive"  # Will use section-based chunking
        
        super().__init__(chunk_size, chunk_overlap, chunking_strategy)
        logger.info(f"Initialized PDF processor for {document_type} documents with {chunking_strategy} chunking")
    
    async def extract_content(self, file_path: str) -> str:
        """
        Extract text content from PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            # Use PyPDFLoader for text extraction
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            if not documents:
                raise ValueError(f"No content found in PDF: {file_path}")
            
            # Combine all pages with page breaks
            text_content = ""
            for i, doc in enumerate(documents):
                page_content = doc.page_content.strip()
                
                if not page_content:
                    continue
                
                # Enhanced page breaks for long-form documents (20+ pages)
                if i > 0:
                    if len(documents) >= 20:
                        # Long-form documents: Add page number and enhanced breaks
                        text_content += f"\n\n--- Page {i+1} ---\n\n"
                    else:
                        # Standard documents: Simple page breaks
                        text_content += "\n\n--- Page Break ---\n\n"
                else:
                    # First page for long-form documents
                    if len(documents) >= 20:
                        text_content += f"--- Page 1 ---\n\n"
                
                text_content += page_content
            
            # Clean up extracted text
            text_content = self._clean_extracted_text(text_content)
            
            logger.info(f"Extracted {len(text_content)} characters from PDF with {len(documents)} pages")
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting content from PDF {file_path}: {str(e)}")
            raise
    
    def extract_format_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract PDF-specific metadata
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            metadata = {
                "format": "pdf",
                "document_type": self.document_type
            }
            
            if not os.path.exists(file_path):
                return metadata
            
            # Open PDF to extract metadata
            reader = PdfReader(file_path)
            
            # Basic PDF information
            metadata.update({
                "page_count": len(reader.pages),
                "pdf_metadata": reader.metadata if reader.metadata else {},
                "is_encrypted": reader.is_encrypted
            })
            
            # Analyze content characteristics for better chunking
            total_text_length = 0
            has_structured_sections = False
            has_transaction_patterns = False
            
            # Sample first few pages to determine document characteristics
            sample_pages = min(3, len(reader.pages))
            sample_text = ""
            
            for page_num in range(sample_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                sample_text += page_text
                total_text_length += len(page_text)
            
            # Detect document characteristics
            sample_lower = sample_text.lower()
        
            # Check for financial patterns
            financial_keywords = ['balance', 'transaction', 'payment', 'deposit', 'withdrawal', 'statement', 'account']
            transaction_patterns = ['$', 'debit', 'credit', 'zelle', 'ach']
            
            financial_score = sum(1 for keyword in financial_keywords if keyword in sample_lower)
            transaction_score = sum(1 for pattern in transaction_patterns if pattern in sample_lower)
            
            if financial_score >= 3 or transaction_score >= 2:
                has_transaction_patterns = True
            
            # Check for structured sections
            section_patterns = ['summary', 'introduction', 'conclusion', 'chapter', 'section', 'experience', 'education', 'skills']
            section_score = sum(1 for pattern in section_patterns if pattern in sample_lower)
            
            if section_score >= 2:
                has_structured_sections = True
            
            # Determine optimal chunking approach
            avg_page_length = total_text_length / sample_pages if sample_pages > 0 else 0
            
            chunking_metadata = {
                "avg_page_length": avg_page_length,
                "has_structured_sections": has_structured_sections,
                "has_transaction_patterns": has_transaction_patterns,
                "financial_score": financial_score,
                "transaction_score": transaction_score,
                "section_score": section_score
            }
            
            # Add recommended chunking strategy
            if has_transaction_patterns and self.document_type == "financial":
                chunking_metadata["recommended_strategy"] = "transaction_level"
            elif avg_page_length > 2000 and len(reader.pages) > 10:  # Long-form document
                chunking_metadata["recommended_strategy"] = "token_based"
            elif has_structured_sections:
                chunking_metadata["recommended_strategy"] = "section_based"
            else:
                chunking_metadata["recommended_strategy"] = "paragraph_based"
            
            metadata["chunking_analysis"] = chunking_metadata
            
            logger.info(f"Extracted PDF metadata: {len(reader.pages)} pages, type: {self.document_type}, strategy: {chunking_metadata.get('recommended_strategy', 'default')}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting PDF metadata from {file_path}: {str(e)}")
            return {"format": "pdf", "document_type": self.document_type, "error": str(e)}
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted PDF text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        import re
        
        # Normalize line breaks
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        
        # Remove excessive blank lines (keep max 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Clean up spaces
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r' +\n', '\n', text)   # Remove trailing spaces
        text = re.sub(r'\n +', '\n', text)   # Remove leading spaces
        
        # Handle common PDF extraction artifacts
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        
        # Handle page numbers and headers/footers (basic cleanup)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip likely page numbers (standalone numbers)
            if re.match(r'^\d+$', line) and len(line) <= 3:
                continue
            
            # Skip very short lines that are likely artifacts (but keep transaction lines)
            if len(line) < 3 and not re.search(r'\$\d', line):
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def create_chunks(self, content: str, base_metadata: Dict[str, Any]) -> List[LangchainDocument]:
        """
        Create adaptive chunks based on document type and content analysis
        
        Args:
            content: PDF text content
            base_metadata: Base metadata including PDF-specific info
            
        Returns:
            List of optimally chunked documents
        """
        try:
            # Add document type to metadata for adaptive chunking
            enhanced_metadata = base_metadata.copy()
            enhanced_metadata["document_type"] = self.document_type
            
            # Use chunking analysis if available
            chunking_analysis = base_metadata.get("chunking_analysis", {})
            recommended_strategy = chunking_analysis.get("recommended_strategy")
            
            if recommended_strategy:
                logger.info(f"Using recommended chunking strategy: {recommended_strategy}")
                
                # Override chunking strategy based on analysis
                if recommended_strategy == "transaction_level" and self.document_type == "financial":
                    # Use financial processor for transaction-level chunking
                    from app.utils.processors.financial_processor import FinancialDocumentProcessor
                    financial_processor = FinancialDocumentProcessor()
                    return financial_processor.create_chunks(content, enhanced_metadata)
                
                elif recommended_strategy == "token_based":
                    # Use token-based chunking for long-form
                    return self._create_token_based_chunks(content, enhanced_metadata)
                
                elif recommended_strategy == "section_based":
                    # Use section-based chunking for structured docs
                    return self._create_section_based_chunks(content, enhanced_metadata)
            
            # Fall back to adaptive chunking based on document type
            logger.info(f"Using adaptive chunking for {self.document_type} document")
            return super().create_chunks(content, enhanced_metadata)
            
        except Exception as e:
            logger.error(f"Error creating PDF chunks: {str(e)}")
            # Ultimate fallback
            return self._create_fixed_size_chunks(content, base_metadata)