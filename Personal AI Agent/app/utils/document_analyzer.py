"""
Document content analysis utilities
"""

import logging
from typing import Dict

logger = logging.getLogger("personal_ai_agent")


def identify_document_type(content: str) -> Dict[str, bool]:
    """
    Identify document type based on content
    
    Args:
        content: The document content
        
    Returns:
        Dictionary with document type flags
    """
    from app.utils.ai_config import DOCUMENT_TYPE_KEYWORDS
    
    content_lower = content.lower()
    
    # Check for document types
    is_vacation = any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation'])
    is_resume = any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume'])
    is_expense = any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense'])
    is_prompt_engineering = any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['prompt_engineering'])
    
    # Special case for prompt engineering - check for title
    if "prompt engineering" in content_lower:
        is_prompt_engineering = True
    
    # Log the detection
    logger.info(f"Document type detection: Vacation={is_vacation}, Resume={is_resume}, Expense={is_expense}, Prompt Engineering={is_prompt_engineering}")
    
    return {
        "is_vacation": is_vacation,
        "is_resume": is_resume,
        "is_expense": is_expense,
        "is_prompt_engineering": is_prompt_engineering
    }


def extract_content_metadata(content: str, file_path: str) -> Dict[str, any]:
    """
    Extract metadata from document content
    
    Args:
        content: Document content
        file_path: Path to the file
        
    Returns:
        Dictionary with content metadata
    """
    import os
    from datetime import datetime
    
    # Get document type flags
    doc_types = identify_document_type(content)
    
    # Basic metadata
    metadata = {
        "source": "content_analysis",
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "content_length": len(content),
        "analyzed_at": datetime.now().isoformat(),
        **doc_types
    }
    
    return metadata