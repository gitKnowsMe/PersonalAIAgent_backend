"""
Text document processor for TXT, MD, CSV files
"""

import logging
import os
from typing import Dict
from langchain_community.document_loaders import TextLoader

from .base_processor import BaseDocumentProcessor

logger = logging.getLogger("personal_ai_agent")


class TextDocumentProcessor(BaseDocumentProcessor):
    """
    Processor for text-based documents (TXT, MD, CSV)
    """
    
    # Text-specific chunking configuration
    DEFAULT_CHUNK_SIZE = 2000  # Larger chunks for text files
    DEFAULT_CHUNK_OVERLAP = 400
    
    async def extract_content(self, file_path: str) -> str:
        """
        Extract text content from text file
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Extracted text content
        """
        try:
            # Use LangChain's TextLoader for better encoding handling
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            
            if not documents:
                raise ValueError(f"No content found in {file_path}")
            
            # Combine all documents (TextLoader typically returns one document)
            content = "\n\n".join(doc.page_content for doc in documents)
            
            logger.info(f"Extracted {len(content)} characters from text file: {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {str(e)}")
            # Fallback to simple file reading
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                logger.info(f"Fallback extraction successful: {len(content)} characters")
                return content
            except Exception as fallback_error:
                logger.error(f"Fallback extraction also failed: {str(fallback_error)}")
                raise
    
    def extract_format_metadata(self, file_path: str) -> Dict[str, any]:
        """
        Extract text file specific metadata
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Dictionary with text file metadata
        """
        try:
            # Get file stats
            stat = os.stat(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            metadata = {
                "source": "txt",
                "file_extension": file_ext,
                "file_size_bytes": stat.st_size,
                "file_modified": stat.st_mtime
            }
            
            # Add format-specific info
            if file_ext == '.csv':
                metadata["format_type"] = "csv"
                # TODO: Could add CSV-specific metadata like column count, delimiter detection
            elif file_ext == '.md':
                metadata["format_type"] = "markdown"
            else:
                metadata["format_type"] = "plain_text"
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extracting text file metadata from {file_path}: {str(e)}")
            return {
                "source": "txt",
                "format_type": "plain_text",
                "metadata_error": str(e)
            }