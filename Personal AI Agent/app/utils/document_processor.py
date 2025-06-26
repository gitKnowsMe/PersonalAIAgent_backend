import os
import logging
import tempfile
from typing import List, Dict, Any, Optional, Callable
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader, PyPDFLoader, CSVLoader, Docx2txtLoader
)

from app.utils.vector_store import add_documents_to_vector_store
from app.utils.embeddings import get_embedding_model
from app.db.models import Document, User

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Document type keywords for classification
DOCUMENT_TYPE_KEYWORDS = {
    'vacation': ['vacation', 'travel', 'trip', 'holiday', 'airline', 'flight', 'hotel', 'rental car', 'thailand', 'phuket', 'bangkok'],
    'resume': ['resume', 'cv', 'work history', 'experience', 'education', 'skill', 'professional', 'job'],
    'expense': ['expense', 'budget', 'cost', 'spent', '$', 'dollar', 'payment', 'finance']
}

# Document loader mapping
DOCUMENT_LOADERS = {
    '.pdf': lambda path: PyPDFLoader(path),
    '.docx': lambda path: Docx2txtLoader(path),
    '.csv': lambda path: CSVLoader(path),
    '.txt': lambda path: TextLoader(path, encoding='utf-8'),
    '.md': lambda path: TextLoader(path, encoding='utf-8'),
}

def identify_document_type(content: str) -> Dict[str, bool]:
    """
    Identify document type based on content
    Returns a dictionary with document types and boolean values
    """
    content_lower = content.lower()
    
    return {
        'is_vacation': any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation']),
        'is_resume': any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume']),
        'is_expense': any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense'])
    }

def get_document_loader(file_path: str):
    """
    Get the appropriate document loader based on file extension
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Document loader instance
        
    Raises:
        ValueError: If the file type is not supported
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    loader_func = DOCUMENT_LOADERS.get(file_extension)
    if loader_func:
        logger.debug(f"Using {loader_func.__name__ if hasattr(loader_func, '__name__') else 'loader'} for {file_extension} file: {file_path}")
        return loader_func(file_path)
    
    # If we don't have a specific loader, try the text loader as fallback
    logger.warning(f"No specific loader found for {file_extension}, using TextLoader as fallback for: {file_path}")
    return TextLoader(file_path, encoding='utf-8')

async def process_document(document: Document, user: User) -> int:
    """
    Process a document and add it to the vector store
    
    Args:
        document: Document object
        user: User object
        
    Returns:
        Number of chunks added to the vector store
    """
    try:
        # Get the appropriate loader
        loader = get_document_loader(document.file_path)
    
        # Load the document
        documents = loader.load()
        
        # Identify document type from content
        if documents:
            full_content = " ".join([doc.page_content for doc in documents])
            doc_types = identify_document_type(full_content)
            
            # Log document type identification
            logger.info(f"Document type identification for {document.file_path}: {doc_types}")
            
            # Add document type to metadata
            for doc in documents:
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata.update(doc_types)
        
        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = text_splitter.split_documents(documents)
    
        # Add metadata to chunks
        for chunk in chunks:
            chunk.metadata["user_id"] = user.id
            chunk.metadata["document_id"] = document.id
            chunk.metadata["file_path"] = document.file_path
        
        # Get embedding model
        embedding_model = get_embedding_model()
    
        # Add chunks to vector store
        num_chunks = await add_documents_to_vector_store(chunks, embedding_model, document.vector_namespace)
    
        logger.info(f"Document processed: {document.file_path}, added {num_chunks} chunks to vector store")
        return num_chunks
    except Exception as e:
        logger.error(f"Error processing document {document.file_path}: {str(e)}")
        raise 