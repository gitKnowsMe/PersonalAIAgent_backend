import os
import logging
from typing import Dict, Type
from app.db.models import Document, User
from app.utils.processors import TextDocumentProcessor, PDFDocumentProcessor, BaseDocumentProcessor

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Registry of file extensions to processor classes
PROCESSOR_REGISTRY: Dict[str, Type[BaseDocumentProcessor]] = {
    '.txt': TextDocumentProcessor,
    '.md': TextDocumentProcessor,
    '.csv': TextDocumentProcessor,
    '.pdf': PDFDocumentProcessor,
    # Easy to add new formats by creating processor and adding to registry!
}

def get_file_extension(file_path: str) -> str:
    """
    Get the file extension from a file path
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension (lowercase)
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower()

def get_processor_for_file(file_path: str) -> BaseDocumentProcessor:
    """
    Get the appropriate processor for a file type
    
    Args:
        file_path: Path to the file
        
    Returns:
        Instance of the appropriate processor
        
    Raises:
        ValueError: If file type is not supported
    """
    file_extension = get_file_extension(file_path)
    
    if file_extension not in PROCESSOR_REGISTRY:
        raise ValueError(f"Unsupported file type: {file_extension}")
    
    processor_class = PROCESSOR_REGISTRY[file_extension]
    return processor_class()

async def process_document(document: Document, user: User) -> int:
    """
    Process a document and add it to the vector store
    This function determines the file type and calls the appropriate processor
    
    Args:
        document: Document object
        user: User object
        
    Returns:
        Number of chunks added to the vector store
    """
    try:
        file_extension = get_file_extension(document.file_path)
        logger.info(f"Processing {file_extension} document: {document.file_path}")
        
        # Get the appropriate processor
        processor = get_processor_for_file(document.file_path)
        
        # Process the document
        return await processor.process_document(document, user)
        
    except Exception as e:
        logger.error(f"Error processing document {document.file_path}: {str(e)}")
        raise 