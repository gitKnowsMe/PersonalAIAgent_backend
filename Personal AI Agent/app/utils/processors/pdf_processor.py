"""
PDF document processor
"""

import logging
import os
from typing import Dict
from langchain_community.document_loaders import PyPDFLoader
from pypdf import PdfReader

from .base_processor import BaseDocumentProcessor

logger = logging.getLogger("personal_ai_agent")


class PDFDocumentProcessor(BaseDocumentProcessor):
    """
    Processor for PDF documents
    """
    
    # PDF-specific chunking configuration
    DEFAULT_CHUNK_SIZE = 1000  # Smaller chunks for PDFs
    DEFAULT_CHUNK_OVERLAP = 200
    MAX_PAGE_CONTENT_LENGTH = 100000  # Maximum characters per page to process
    
    async def extract_content(self, file_path: str) -> str:
        """
        Extract text content from PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            # Use LangChain's PyPDFLoader for better PDF handling
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            if not documents:
                raise ValueError(f"No content found in PDF: {file_path}")
            
            # Combine all pages
            pages_content = []
            for i, doc in enumerate(documents):
                page_content = doc.page_content.strip()
                
                # Skip empty pages
                if not page_content:
                    logger.debug(f"Skipping empty page {i+1}")
                    continue
                
                # Limit page content length to prevent memory issues
                if len(page_content) > self.MAX_PAGE_CONTENT_LENGTH:
                    logger.warning(f"Page {i+1} content truncated from {len(page_content)} to {self.MAX_PAGE_CONTENT_LENGTH} characters")
                    page_content = page_content[:self.MAX_PAGE_CONTENT_LENGTH]
                
                pages_content.append(page_content)
                logger.debug(f"Extracted {len(page_content)} characters from page {i+1}")
            
            content = "\n\n".join(pages_content)
            logger.info(f"Extracted {len(content)} characters from {len(pages_content)} pages in PDF: {file_path}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content from PDF {file_path}: {str(e)}")
            raise
    
    def extract_format_metadata(self, file_path: str) -> Dict[str, any]:
        """
        Extract PDF specific metadata
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            # Get file stats
            stat = os.stat(file_path)
            
            # Basic metadata
            metadata = {
                "source": "pdf",
                "file_extension": ".pdf",
                "file_size_bytes": stat.st_size,
                "file_modified": stat.st_mtime,
                "format_type": "pdf"
            }
            
            # Extract PDF-specific metadata using PyPDF
            try:
                reader = PdfReader(file_path)
                info = reader.metadata
                
                # Add PDF document info
                metadata["pdf_num_pages"] = len(reader.pages)
                metadata["pdf_filename"] = os.path.basename(file_path)
                
                # Add metadata from PDF if available
                if info:
                    for key in info:
                        if info[key] and str(info[key]).strip():
                            # Clean up the key name and convert to string
                            clean_key = key.lower().replace('/', '_').replace(':', '_')
                            metadata[f"pdf_{clean_key}"] = str(info[key])
                
            except Exception as pdf_error:
                logger.warning(f"Error extracting PDF metadata from {file_path}: {str(pdf_error)}")
                metadata["pdf_metadata_error"] = str(pdf_error)
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extracting PDF file metadata from {file_path}: {str(e)}")
            return {
                "source": "pdf",
                "format_type": "pdf",
                "metadata_error": str(e)
            }