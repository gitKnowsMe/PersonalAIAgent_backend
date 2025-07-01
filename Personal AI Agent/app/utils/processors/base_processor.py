"""
Base document processor with common functionality
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from datetime import datetime

from app.utils.vector_store import add_documents_to_vector_store
from app.utils.embeddings import get_embedding_model
from app.utils.document_analyzer import extract_content_metadata
from app.db.models import Document, User

logger = logging.getLogger("personal_ai_agent")


class BaseDocumentProcessor(ABC):
    """
    Abstract base class for document processors
    """
    
    # Default chunking configuration
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize the processor
        
        Args:
            chunk_size: Size of text chunks (characters)
            chunk_overlap: Overlap between chunks (characters)
        """
        self.chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or self.DEFAULT_CHUNK_OVERLAP
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    @abstractmethod
    async def extract_content(self, file_path: str) -> str:
        """
        Extract text content from the file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text content
        """
        pass
    
    @abstractmethod
    def extract_format_metadata(self, file_path: str) -> Dict[str, any]:
        """
        Extract format-specific metadata from the file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with format-specific metadata
        """
        pass
    
    def create_chunks(self, content: str, base_metadata: Dict[str, any]) -> List[LangchainDocument]:
        """
        Split content into chunks and create LangchainDocument objects
        
        Args:
            content: Text content to chunk
            base_metadata: Base metadata to add to all chunks
            
        Returns:
            List of LangchainDocument chunks
        """
        try:
            # Split content into chunks
            text_chunks = self.text_splitter.split_text(content)
            logger.info(f"Split content into {len(text_chunks)} chunks")
            
            # Create LangchainDocument objects
            documents = []
            for i, chunk in enumerate(text_chunks):
                if chunk.strip():  # Skip empty chunks
                    chunk_metadata = base_metadata.copy()
                    chunk_metadata.update({
                        "chunk_index": i,
                        "chunk_length": len(chunk),
                        "total_chunks": len(text_chunks)
                    })
                    
                    doc = LangchainDocument(
                        page_content=chunk,
                        metadata=chunk_metadata
                    )
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error creating chunks: {str(e)}")
            raise
    
    async def process_document(self, document: Document, user: User) -> int:
        """
        Main processing method that orchestrates the entire workflow
        
        Args:
            document: Document object from database
            user: User object
            
        Returns:
            Number of chunks added to vector store
        """
        try:
            logger.info(f"Processing document: {document.file_path}")
            
            # Step 1: Extract content
            content = await self.extract_content(document.file_path)
            logger.info(f"Extracted {len(content)} characters of content")
            
            # Step 2: Extract format-specific metadata
            format_metadata = self.extract_format_metadata(document.file_path)
            
            # Step 3: Extract content metadata
            content_metadata = extract_content_metadata(content, document.file_path)
            
            # Step 4: Combine all metadata
            base_metadata = {
                "user_id": user.id,
                "document_id": document.id,
                "uploaded_at": document.created_at.isoformat(),
                **format_metadata,
                **content_metadata
            }
            
            # Step 5: Create chunks
            chunks = self.create_chunks(content, base_metadata)
            
            if not chunks:
                logger.warning(f"No chunks created for document {document.file_path}")
                return 0
            
            # Step 6: Add to vector store
            embedding_model = get_embedding_model()
            chunks_added = await add_documents_to_vector_store(
                chunks, 
                embedding_model,
                document.vector_namespace
            )
            
            logger.info(f"Successfully processed document {document.file_path}: {chunks_added} chunks added")
            return chunks_added
            
        except Exception as e:
            logger.error(f"Error processing document {document.file_path}: {str(e)}")
            raise