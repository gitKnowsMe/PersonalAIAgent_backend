"""
Vector store utilities - backward compatibility layer
This module now delegates to the new VectorStoreService for better architecture
"""

import logging
import re
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from app.services.vector_store_service import get_vector_store_service
from app.services.embedding_service import get_embedding_service
from app.utils.ai_config import DOCUMENT_TYPE_KEYWORDS

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Constants for backward compatibility
MAX_CHUNKS_PER_TYPE = 3
MAX_TOTAL_CHUNKS = 5
HIGH_QUALITY_SCORE_THRESHOLD = 0.85


async def add_documents_to_vector_store(documents, embedding_model, namespace):
    """Add documents to FAISS vector store (backward compatibility)"""
    vector_store_service = get_vector_store_service()
    embedding_service = get_embedding_service()
    
    return await vector_store_service.add_documents(
        documents=documents,
        namespace=namespace,
        embedding_service=embedding_service
    )


async def search_similar_chunks(query: str, user_id: int = None, document_id: Optional[int] = None, top_k: int = 20, metadata_filter: dict = None):
    """
    Search for similar chunks across all namespaces for a user (backward compatibility)
    """
    vector_store_service = get_vector_store_service()
    embedding_service = get_embedding_service()
    
    return await vector_store_service.search_similar_chunks(
        query=query,
        embedding_service=embedding_service,
        user_id=user_id,
        document_id=document_id,
        top_k=top_k,
        metadata_filter=metadata_filter
    )


def check_query_type(query: str):
    """
    Check query type based on keywords
    Returns: (is_vacation, is_skills, is_expense, is_prompt_engineering, years)
    """
    query_lower = query.lower()
    
    # Check for different types
    is_vacation = any(keyword in query_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation'])
    is_skills = any(keyword in query_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume'])
    is_expense = any(keyword in query_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense'])
    is_prompt_engineering = any(keyword in query_lower for keyword in DOCUMENT_TYPE_KEYWORDS['prompt_engineering'])
    
    # Extract years
    years = re.findall(r'\b(19|20)\d{2}\b', query)
    
    return is_vacation, is_skills, is_expense, is_prompt_engineering, years


def extract_month_from_query(query: str) -> Optional[str]:
    """
    Extract month name from a query
    Returns the month name if found, None otherwise
    """
    query_lower = query.lower()
    months = ['january', 'february', 'march', 'april', 'may', 'june', 
              'july', 'august', 'september', 'october', 'november', 'december']
    
    for month in months:
        if month in query_lower:
            return month
    
    # Check for abbreviations
    month_abbr = {
        'jan': 'january', 'feb': 'february', 'mar': 'march', 'apr': 'april',
        'jun': 'june', 'jul': 'july', 'aug': 'august', 'sep': 'september', 
        'sept': 'september', 'oct': 'october', 'nov': 'november', 'dec': 'december'
    }
    
    for abbr, full_name in month_abbr.items():
        if abbr in query_lower:
            return full_name
    
    return None


def prioritize_namespaces(query: str, namespaces: List[str]) -> List[str]:
    """
    Prioritize namespaces based on query content
    """
    query_lower = query.lower()
    
    # Check for document type keywords
    vacation_keywords = DOCUMENT_TYPE_KEYWORDS['vacation']
    resume_keywords = DOCUMENT_TYPE_KEYWORDS['resume']
    expense_keywords = DOCUMENT_TYPE_KEYWORDS['expense']
    prompt_keywords = DOCUMENT_TYPE_KEYWORDS['prompt_engineering']
    
    # Score namespaces
    namespace_scores = {}
    
    for namespace in namespaces:
        score = 0
        namespace_lower = namespace.lower()
        
        # Check if query suggests this type
        if any(keyword in query_lower for keyword in vacation_keywords):
            if 'vacation' in namespace_lower or 'travel' in namespace_lower:
                score += 10
        
        if any(keyword in query_lower for keyword in resume_keywords):
            if 'resume' in namespace_lower or 'cv' in namespace_lower:
                score += 10
        
        if any(keyword in query_lower for keyword in expense_keywords):
            if 'expense' in namespace_lower or 'budget' in namespace_lower:
                score += 10
        
        if any(keyword in query_lower for keyword in prompt_keywords):
            if 'prompt' in namespace_lower or 'engineering' in namespace_lower:
                score += 10
        
        namespace_scores[namespace] = score
    
    # Sort by score (descending) and return
    return sorted(namespaces, key=lambda x: namespace_scores.get(x, 0), reverse=True)