"""
Base document processor with adaptive chunking strategies
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from datetime import datetime

from app.services.vector_store_service import get_vector_store_service
from app.services.embedding_service import get_embedding_model
from app.utils.document_classifier import detect_document_type, get_document_type_metadata
from app.db.models import Document, User
from app.db.database import get_db

logger = logging.getLogger("personal_ai_agent")


class BaseDocumentProcessor(ABC):
    """
    Abstract base class for document processors with adaptive chunking strategies
    """
    
    # Token-based chunking for long-form documents (1 token ≈ 4 characters)
    DEFAULT_TOKENS_PER_CHUNK = 500  # ~2000 characters
    DEFAULT_TOKEN_OVERLAP = 50      # ~200 characters overlap
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None, chunking_strategy: str = "adaptive"):
        """
        Initialize the processor with adaptive chunking capabilities
        
        Args:
            chunk_size: Characters per chunk (for legacy fixed-size chunking)
            chunk_overlap: Character overlap between chunks
            chunking_strategy: Strategy to use - "adaptive", "token_based", or "fixed_size"
        """
        self.chunking_strategy = chunking_strategy
        
        # Convert token-based defaults to character-based for compatibility
        self.chunk_size = chunk_size or (self.DEFAULT_TOKENS_PER_CHUNK * 4)  # 2000 chars
        self.chunk_overlap = chunk_overlap or (self.DEFAULT_TOKEN_OVERLAP * 4)  # 200 chars
        
        # Initialize text splitter for fallback/standard chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Prioritize natural breaks
        )
        
        logger.info(f"Initialized processor with {chunking_strategy} chunking strategy")
    
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
    def extract_format_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract format-specific metadata from the file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with format-specific metadata
        """
        pass
    
    def create_chunks(self, content: str, base_metadata: Dict[str, Any]) -> List[LangchainDocument]:
        """
        Create chunks using adaptive strategy based on document type and content
        
        Args:
            content: Text content to chunk
            base_metadata: Base metadata to add to all chunks
            
        Returns:
            List of LangchainDocument chunks
        """
        try:
            document_type = base_metadata.get("document_type", "generic")
            
            if self.chunking_strategy == "adaptive":
                return self._create_adaptive_chunks(content, base_metadata, document_type)
            elif self.chunking_strategy == "token_based":
                return self._create_token_based_chunks(content, base_metadata)
            else:
                return self._create_fixed_size_chunks(content, base_metadata)
                
        except Exception as e:
            logger.error(f"Error creating chunks: {str(e)}")
            # Fallback to simple fixed-size chunking
            return self._create_fixed_size_chunks(content, base_metadata)
    
    def _create_adaptive_chunks(self, content: str, base_metadata: Dict[str, Any], 
                               document_type: str) -> List[LangchainDocument]:
        """
        Create chunks using adaptive strategy based on document type
        
        Args:
            content: Text content
            base_metadata: Base metadata
            document_type: Type of document (financial, long_form, generic)
            
        Returns:
            List of adaptive chunks
        """
        logger.info(f"Creating adaptive chunks for {document_type} document")
        
        if document_type == "long_form":
            return self._create_token_based_chunks(content, base_metadata)
        elif document_type == "generic":
            return self._create_section_based_chunks(content, base_metadata)
        else:
            # For financial and other types, fall back to token-based
            return self._create_token_based_chunks(content, base_metadata)
    
    def _create_token_based_chunks(self, content: str, base_metadata: Dict[str, Any]) -> List[LangchainDocument]:
        """
        Create chunks based on token count (~500 tokens per chunk with overlap)
        Optimized for long-form documents like reports
        
        Args:
            content: Text content
            base_metadata: Base metadata
            
        Returns:
            List of token-based chunks
        """
        logger.info("Creating token-based chunks for long-form content")
        
        # Use character approximation: 1 token ≈ 4 characters
        target_chunk_size = self.DEFAULT_TOKENS_PER_CHUNK * 4  # 2000 chars
        overlap_size = self.DEFAULT_TOKEN_OVERLAP * 4          # 200 chars
        
        # Create text splitter optimized for long-form content
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=target_chunk_size,
            chunk_overlap=overlap_size,
            length_function=len,
            separators=["\n\n\n", "\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        
        # Split the content
        raw_chunks = text_splitter.split_text(content)
        
        chunks = []
        for i, chunk_content in enumerate(raw_chunks):
            # Estimate token count
            estimated_tokens = len(chunk_content) // 4
            
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_type": "token_based",
                "chunk_length": len(chunk_content),
                "estimated_tokens": estimated_tokens,
                "chunking_strategy": "token_based_longform",
                "total_chunks": len(raw_chunks)
            })
            
            chunks.append(LangchainDocument(
                page_content=chunk_content.strip(),
                metadata=chunk_metadata
            ))
        
        logger.info(f"Created {len(chunks)} token-based chunks averaging {target_chunk_size//4} tokens each")
        return chunks
    
    def _create_section_based_chunks(self, content: str, base_metadata: Dict[str, Any]) -> List[LangchainDocument]:
        """
        Create chunks based on document sections (optimized for resumes, structured docs)
        
        Args:
            content: Text content
            base_metadata: Base metadata
            
        Returns:
            List of section-based chunks
        """
        logger.info("Creating section-based chunks for structured content")
        
        # Common section headers in structured documents (resumes, reports, etc.)
        section_patterns = [
            r'\n\s*(?:SUMMARY|OBJECTIVE|PROFILE|ABOUT)\s*\n',
            r'\n\s*(?:EXPERIENCE|EMPLOYMENT|WORK HISTORY|PROFESSIONAL EXPERIENCE)\s*\n',
            r'\n\s*(?:EDUCATION|ACADEMIC BACKGROUND)\s*\n',
            r'\n\s*(?:SKILLS|TECHNICAL SKILLS|COMPETENCIES)\s*\n',
            r'\n\s*(?:PROJECTS|PORTFOLIO|ACHIEVEMENTS)\s*\n',
            r'\n\s*(?:CERTIFICATIONS|LICENSES|CREDENTIALS)\s*\n',
            r'\n\s*(?:CONTACT|CONTACT INFORMATION)\s*\n',
            r'\n\s*(?:REFERENCES|RECOMMENDATIONS)\s*\n',
            # Generic section patterns
            r'\n\s*[A-Z][A-Z\s]{2,20}\s*\n',  # ALL CAPS headers
            r'\n\s*\d+\.\s*[A-Z][^.\n]{5,50}\s*\n',  # Numbered sections
            r'\n\s*Chapter\s+\d+[:\s]',  # Chapter headers
        ]
        
        sections = []
        current_section = {"header": "", "content": "", "start_pos": 0}
        
        lines = content.split('\n')
        current_content = []
        
        for line_num, line in enumerate(lines):
            # Check if this line is a section header
            is_section_header = False
            header_text = ""
            
            for pattern in section_patterns:
                if re.search(pattern, f'\n{line}\n', re.IGNORECASE):
                    is_section_header = True
                    header_text = line.strip()
                    break
            
            if is_section_header and current_content:
                # Save the previous section
                if current_section["header"] or current_content:
                    sections.append({
                        "header": current_section["header"],
                        "content": '\n'.join(current_content).strip(),
                        "line_start": current_section["start_pos"],
                        "line_end": line_num - 1
                    })
                
                # Start new section
                current_section = {
                    "header": header_text,
                    "content": "",
                    "start_pos": line_num
                }
                current_content = [line]
            else:
                current_content.append(line)
        
        # Add the last section
        if current_content:
            sections.append({
                "header": current_section["header"],
                "content": '\n'.join(current_content).strip(),
                "line_start": current_section["start_pos"],
                "line_end": len(lines) - 1
            })
        
        # If no clear sections found, fall back to paragraph-based chunking
        if len(sections) <= 1:
            return self._create_paragraph_based_chunks(content, base_metadata)
        
        # Create chunks from sections
        chunks = []
        for i, section in enumerate(sections):
            if not section["content"].strip():
                continue
                
            chunk_content = section["content"]
            
            # If section is too large, split it further
            if len(chunk_content) > 1000:  # ~250 tokens
                sub_chunks = self._split_large_section(chunk_content, section["header"])
                for j, sub_chunk in enumerate(sub_chunks):
                    chunk_metadata = base_metadata.copy()
                    chunk_metadata.update({
                        "chunk_index": len(chunks),
                        "chunk_type": "section_subsection",
                        "section_header": section["header"],
                        "subsection_index": j,
                        "chunk_length": len(sub_chunk),
                        "chunking_strategy": "section_based_structured"
                    })
                    
                    chunks.append(LangchainDocument(
                        page_content=sub_chunk.strip(),
                        metadata=chunk_metadata
                    ))
            else:
                chunk_metadata = base_metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_type": "document_section",
                    "section_header": section["header"],
                    "chunk_length": len(chunk_content),
                    "chunking_strategy": "section_based_structured"
                })
                
                chunks.append(LangchainDocument(
                    page_content=chunk_content.strip(),
                    metadata=chunk_metadata
                ))
        
        # Update total chunks count
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)
        
        logger.info(f"Created {len(chunks)} section-based chunks from {len(sections)} sections")
        return chunks
    
    def _create_paragraph_based_chunks(self, content: str, base_metadata: Dict[str, Any]) -> List[LangchainDocument]:
        """
        Create chunks based on paragraphs for documents without clear sections
        
        Args:
            content: Text content
            base_metadata: Base metadata
            
        Returns:
            List of paragraph-based chunks
        """
        logger.info("Creating paragraph-based chunks")
        
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        target_length = 800  # ~200 tokens
        
        for para in paragraphs:
            para_length = len(para)
            
            # If adding this paragraph would exceed target, finalize current chunk
            if current_length + para_length > target_length and current_chunk:
                chunk_content = '\n\n'.join(current_chunk)
                chunk_metadata = base_metadata.copy()
                chunk_metadata.update({
                    "chunk_index": len(chunks),
                    "chunk_type": "paragraph_group",
                    "chunk_length": len(chunk_content),
                    "paragraph_count": len(current_chunk),
                    "chunking_strategy": "paragraph_based"
                })
                
                chunks.append(LangchainDocument(
                    page_content=chunk_content,
                    metadata=chunk_metadata
                ))
                
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length
        
        # Add final chunk
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_index": len(chunks),
                "chunk_type": "paragraph_group",
                "chunk_length": len(chunk_content),
                "paragraph_count": len(current_chunk),
                "chunking_strategy": "paragraph_based"
            })
            
            chunks.append(LangchainDocument(
                page_content=chunk_content,
                metadata=chunk_metadata
            ))
        
        # Update total chunks count
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)
        
        logger.info(f"Created {len(chunks)} paragraph-based chunks")
        return chunks
    
    def _split_large_section(self, section_content: str, section_header: str) -> List[str]:
        """
        Split a large section into smaller sub-chunks
        
        Args:
            section_content: Content of the large section
            section_header: Header of the section
            
        Returns:
            List of sub-chunk contents
        """
        # Use text splitter for large sections
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # ~200 tokens
            chunk_overlap=80,  # ~20 tokens
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        sub_chunks = splitter.split_text(section_content)
        
        # Add section header context to each sub-chunk
        contextualized_chunks = []
        for sub_chunk in sub_chunks:
            if section_header:
                contextualized_chunk = f"{section_header}\n\n{sub_chunk}"
            else:
                contextualized_chunk = sub_chunk
            contextualized_chunks.append(contextualized_chunk)
        
        return contextualized_chunks
    
    def _create_fixed_size_chunks(self, content: str, base_metadata: Dict[str, Any]) -> List[LangchainDocument]:
        """
        Create chunks using fixed character size (fallback method)
        
        Args:
            content: Text content
            base_metadata: Base metadata
            
        Returns:
            List of fixed-size chunks
        """
        logger.info(f"Creating fixed-size chunks ({self.chunk_size} chars each)")
        
        raw_chunks = self.text_splitter.split_text(content)
        
        chunks = []
        for i, chunk_content in enumerate(raw_chunks):
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "chunk_type": "fixed_size",
                "chunk_length": len(chunk_content),
                "chunking_strategy": "fixed_size_fallback",
                "total_chunks": len(raw_chunks)
            })
            
            chunks.append(LangchainDocument(
                page_content=chunk_content.strip(),
                metadata=chunk_metadata
            ))
        
        logger.info(f"Created {len(chunks)} fixed-size chunks")
        return chunks
    
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
            
            # Step 2: Classify document type
            filename = document.file_path.split('/')[-1]  # Get filename from path
            document_type = detect_document_type(content, filename)
            
            # Step 3: Update document type in database
            db = next(get_db())
            try:
                db_document = db.query(Document).filter(Document.id == document.id).first()
                if db_document:
                    db_document.document_type = document_type
                    db.commit()
                    logger.info(f"Updated document {document.id} type to: {document_type}")
            except Exception as db_error:
                logger.error(f"Failed to update document type in database: {db_error}")
                db.rollback()
            finally:
                db.close()
            
            # Step 4: Get type-specific processing parameters
            type_metadata = get_document_type_metadata(document_type)
            
            # Step 5: Adjust chunking based on document type
            if document_type == "financial":
                # Smaller chunks for financial documents
                self._update_chunking_config(200, 20)  # Reduced from 500, 50
            elif document_type == "long_form":
                # Larger chunks for long-form documents
                self._update_chunking_config(600, 100)  # Reduced from 1500, 300
            else:
                # Default chunking for generic documents
                self._update_chunking_config(400, 80)  # Reduced from 1000, 200
            
            # Step 6: Extract format-specific metadata
            format_metadata = self.extract_format_metadata(document.file_path)
            
            # Step 7: Extract content metadata using classifier
            content_metadata = {
                "content_length": len(content),
                "estimated_tokens": len(content) // 4,
                "processing_timestamp": datetime.now().isoformat()
            }
            
            # Step 8: Combine all metadata
            base_metadata = {
                "user_id": user.id,
                "document_id": document.id,
                "document_type": document_type,
                "uploaded_at": document.created_at.isoformat(),
                **format_metadata,
                **content_metadata,
                **type_metadata
            }
            
            # Step 9: Create chunks (use specialized processor for financial documents)
            if document_type == "financial":
                from app.utils.processors.financial_processor import FinancialDocumentProcessor
                financial_processor = FinancialDocumentProcessor()
                chunks = financial_processor.create_chunks(content, base_metadata)
            else:
                chunks = self.create_chunks(content, base_metadata)
            
            if not chunks:
                logger.warning(f"No chunks created for document {document.file_path}")
                return 0
            
            # Step 10: Add to category-aware vector store
            embedding_model = get_embedding_model()
            
            # Create category-aware namespace
            category_namespace = f"{document_type}_{document.vector_namespace}"
            
            # Get vector store service and add documents
            vector_store_service = get_vector_store_service()
            chunks_added = await vector_store_service.add_documents(
                chunks, 
                category_namespace
            )
            
            logger.info(f"Successfully processed document {document.file_path}: {chunks_added} chunks added, type: {document_type}")
            return chunks_added
            
        except Exception as e:
            logger.error(f"Error processing document {document.file_path}: {str(e)}")
            raise
    
    def _update_chunking_config(self, chunk_size: int, chunk_overlap: int):
        """
        Update chunking configuration for type-specific processing
        
        Args:
            chunk_size: New chunk size
            chunk_overlap: New chunk overlap
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )