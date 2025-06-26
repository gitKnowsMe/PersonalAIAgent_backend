import os
import logging
import pickle
import faiss
import numpy as np
import re
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.utils.embeddings import generate_embeddings
from app.db.models import Document as DBDocument

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Dictionary to store namespaced indices
_indices = {}
_document_map = {}

# Query result cache
_query_cache = {}

# Define keyword patterns for document and query classification
# These could be moved to config or a database table for easier maintenance
DOCUMENT_TYPE_KEYWORDS = {
    'vacation': ['vacation', 'travel', 'trip', 'holiday', 'airline', 'flight', 'hotel', 'rental car', 'thailand', 'phuket', 'bangkok'],
    'resume': ['resume', 'cv', 'work history', 'experience', 'education', 'skill', 'professional', 'job', 'technical', 'programming', 'framework', 'language', 'certification', 'qualification', 'expertise', 'proficiency', 'accomplishment'],
    'expense': ['expense', 'budget', 'cost', 'spent', '$', 'dollar', 'payment', 'finance', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
}

QUERY_TYPE_KEYWORDS = {
    'vacation': ['vacation', 'travel', 'trip', 'holiday', 'visit', 'went', 'go', 'flight', 'hotel', 'resort', 'beach'],
    'skills': ['skill', 'skills', 'resume', 'cv', 'experience', 'qualification', 'proficiency', 'knowledge', 'programming', 'language', 'framework', 'technical', 'expertise', 'certification', 'ability', 'competency', 'proficient', 'capable', 'what can i do', 'what am i good at', 'what do i know'],
    'expense': ['expense', 'money', 'spend', 'spent', 'cost', 'budget', 'payment', 'finance', 'dollar', '$', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
}

# Maximum number of chunks to retrieve per document type
MAX_CHUNKS_PER_TYPE = 3

# Maximum total chunks to include in context
MAX_TOTAL_CHUNKS = 5

# Threshold for high-quality matches
HIGH_QUALITY_SCORE_THRESHOLD = 0.85

async def add_documents_to_vector_store(documents, embedding_model, namespace):
    """Add documents to FAISS vector store"""
    # Create directory for vector store if it doesn't exist
    os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
    
    # Generate embeddings for documents
    texts = [doc.page_content for doc in documents]
    embeddings = generate_embeddings(texts)
    
    # Create or load existing index
    index_path = os.path.join(settings.VECTOR_DB_PATH, f"{namespace}.index")
    docmap_path = os.path.join(settings.VECTOR_DB_PATH, f"{namespace}.pkl")
    
    if namespace in _indices:
        index = _indices[namespace]
        doc_map = _document_map[namespace]
    elif os.path.exists(index_path):
        # Load existing index
        index = faiss.read_index(index_path)
        with open(docmap_path, 'rb') as f:
            doc_map = pickle.load(f)
    else:
        # Create new index
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        doc_map = {}
    
    # Add documents to index
    start_id = len(doc_map)
    faiss.normalize_L2(embeddings)
    index.add(np.array(embeddings).astype('float32'))
    
    # Update document map
    for i, doc in enumerate(documents):
        doc_map[start_id + i] = {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
    
    # Save index and document map
    _indices[namespace] = index
    _document_map[namespace] = doc_map
    
    faiss.write_index(index, index_path)
    with open(docmap_path, 'wb') as f:
        pickle.dump(doc_map, f)
    
    logger.info(f"Added {len(documents)} chunks to vector store with namespace: {namespace}")
    return len(documents)

def get_file_paths_for_namespaces():
    """Get file paths for all namespaces from the database"""
    # Create database engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get all documents
        documents = db.query(DBDocument).all()
        
        # Create a mapping of namespace to file path
        namespace_to_file_path = {}
        for doc in documents:
            namespace_to_file_path[doc.vector_namespace] = doc.file_path
        
        return namespace_to_file_path
    finally:
        db.close()

def identify_document_type(namespace, file_path=None, sample_content=None) -> Tuple[bool, bool, bool]:
    """
    Identify document type based on file path and/or content
    Returns a tuple of (is_vacation, is_resume, is_expense)
    """
    is_vacation = False
    is_resume = False
    is_expense = False
    
    # Check file path first if available
    if file_path:
        file_path_lower = file_path.lower()
        if any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation']):
            is_vacation = True
        if any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume']):
            is_resume = True
        if any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense']):
            is_expense = True
    
    # If we have sample content, use it to further identify document type
    if sample_content:
        content_lower = sample_content.lower()
        
        # Check for vacation indicators
        if any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation']):
            is_vacation = True
        
        # Check for resume indicators
        if any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume']):
            is_resume = True
        
        # Check for expense indicators
        if any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense']):
            is_expense = True
    
    # Check namespace as a last resort
    namespace_lower = namespace.lower()
    if any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation']):
        is_vacation = True
    if any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume']):
        is_resume = True
    if any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense']):
        is_expense = True
    
    return (is_vacation, is_resume, is_expense)

def check_query_type(query: str) -> Tuple[bool, bool, bool, List[str]]:
    """
    Check what type of query this is based on keywords
    Returns a tuple of (is_vacation_query, is_skills_query, is_expense_query, years)
    """
    query_lower = query.lower()
    
    is_vacation_query = any(keyword in query_lower for keyword in QUERY_TYPE_KEYWORDS['vacation'])
    is_skills_query = any(keyword in query_lower for keyword in QUERY_TYPE_KEYWORDS['skills'])
    is_expense_query = any(keyword in query_lower for keyword in QUERY_TYPE_KEYWORDS['expense'])
    
    # Extract years from query
    years = re.findall(r'\b20\d\d\b', query)
    
    return (is_vacation_query, is_skills_query, is_expense_query, years)

def prioritize_namespaces(query, namespaces):
    """
    Prioritize namespaces based on query content
    Returns a list of namespaces in priority order
    """
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    # Check query type
    is_vacation_query, is_skills_query, is_expense_query, _ = check_query_type(query)
    
    # Get file paths for all namespaces
    namespace_to_file_path = get_file_paths_for_namespaces()
    
    # Score each namespace based on its name and the query
    namespace_scores = []
    for namespace in namespaces:
        score = 0
        file_path = namespace_to_file_path.get(namespace, "")
        
        # Check if namespace contains relevant keywords
        if any(keyword in namespace.lower() for keyword in DOCUMENT_TYPE_KEYWORDS['vacation']) and is_vacation_query:
            score += 10
        if any(keyword in namespace.lower() for keyword in DOCUMENT_TYPE_KEYWORDS['resume']) and is_skills_query:
            score += 10
        if any(keyword in namespace.lower() for keyword in DOCUMENT_TYPE_KEYWORDS['expense']) and is_expense_query:
            score += 10
            
        # Check if file path contains relevant keywords
        if file_path:
            if any(keyword in file_path.lower() for keyword in DOCUMENT_TYPE_KEYWORDS['vacation']) and is_vacation_query:
                score += 5
            if any(keyword in file_path.lower() for keyword in DOCUMENT_TYPE_KEYWORDS['resume']) and is_skills_query:
                score += 5
            if any(keyword in file_path.lower() for keyword in DOCUMENT_TYPE_KEYWORDS['expense']) and is_expense_query:
                score += 5
        
        namespace_scores.append((namespace, score))
    
    # Sort namespaces by score in descending order
    sorted_namespaces = [ns for ns, score in sorted(namespace_scores, key=lambda x: x[1], reverse=True)]
    
    return sorted_namespaces

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
    
    for abbr, month in month_abbr.items():
        if abbr in query_lower:
            return month
    
    return None

async def search_similar_chunks(query: str, user_id: int = None, document_id: Optional[int] = None, top_k: int = 20):
    """
    Search for chunks similar to the query
    
    Args:
        query: The query string
        user_id: User ID to filter by
        document_id: Document ID to filter by
        top_k: Number of chunks to return per namespace
        
    Returns:
        List of Document objects
    """
    # Check if we have a cached result for this query and user
    cache_key = f"{query}_{user_id}_{document_id}"
    if cache_key in _query_cache:
        logger.info(f"Using cached results for query: '{query}'")
        return _query_cache[cache_key]
        
    logger.info(f"Searching for chunks similar to: '{query}' (user_id: {user_id}, document_id: {document_id})")
    
    # Get all available namespaces
    vector_db_files = os.listdir(settings.VECTOR_DB_PATH)
    namespaces = [os.path.splitext(f)[0] for f in vector_db_files if f.endswith('.index')]
    
    # Filter namespaces by user_id
    if user_id is not None:
        user_prefix = f"user_{user_id}_"
        namespaces = [ns for ns in namespaces if ns.startswith(user_prefix)]
    
    # Filter namespaces by document_id if provided
    if document_id is not None:
        # Get the document from the database
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            document = db.query(DBDocument).filter(DBDocument.id == document_id).first()
            if document:
                namespaces = [ns for ns in namespaces if ns == document.vector_namespace]
            else:
                logger.warning(f"Document ID {document_id} not found")
                return []
        finally:
            db.close()
    
    if not namespaces:
        logger.warning(f"No namespaces found for user_id: {user_id}, document_id: {document_id}")
        return []
    
    # Prioritize namespaces based on query content
    prioritized_namespaces = prioritize_namespaces(query, namespaces)
    logger.info(f"Prioritized namespaces: {prioritized_namespaces}")
    
    # Check query type to determine which document types to prioritize
    is_vacation_query, is_skills_query, is_expense_query, years = check_query_type(query)
    
    # Dictionary to store chunks by document type
    chunks_by_type = {
        'vacation': [],
        'resume': [],
        'expense': [],
        'other': []
    }
    
    # Search each namespace in priority order
    for namespace in prioritized_namespaces:
        try:
            # Get file path for this namespace
            namespace_to_file_path = get_file_paths_for_namespaces()
            file_path = namespace_to_file_path.get(namespace, "")
            
            # Search this namespace
            namespace_chunks = await _search_namespace(query, namespace, top_k=top_k)
            
            # Early stopping if we find high-quality chunks
            if namespace_chunks and namespace_chunks[0].metadata.get('score', 0) > HIGH_QUALITY_SCORE_THRESHOLD:
                logger.info(f"Found high-quality chunk with score {namespace_chunks[0].metadata.get('score')}, stopping early")
                result = namespace_chunks[:MAX_TOTAL_CHUNKS]
                _query_cache[cache_key] = result
                return result
            
            if namespace_chunks:
                # Get a sample of content to identify document type
                sample_content = namespace_chunks[0].page_content if namespace_chunks else ""
                
                # Identify document type
                is_vacation, is_resume, is_expense = identify_document_type(namespace, file_path, sample_content)
                
                # Add chunks to the appropriate category
                if is_vacation:
                    chunks_by_type['vacation'].extend(namespace_chunks)
                elif is_resume:
                    chunks_by_type['resume'].extend(namespace_chunks)
                elif is_expense:
                    chunks_by_type['expense'].extend(namespace_chunks)
                else:
                    chunks_by_type['other'].extend(namespace_chunks)
                
                # Log the chunks found
                logger.info(f"Found {len(namespace_chunks)} results in namespace: {namespace}")
                
                # Log document types found
                vacation_count = len(chunks_by_type['vacation'])
                resume_count = len(chunks_by_type['resume'])
                expense_count = len(chunks_by_type['expense'])
                logger.info(f"Found {vacation_count} vacation results, {resume_count} resume results, {expense_count} expense results")
        except Exception as e:
            logger.error(f"Error searching namespace {namespace}: {str(e)}")
    
    # Prioritize chunks based on query type
    final_chunks = []
    
    # First, add chunks from the document type that matches the query type
    if is_vacation_query and chunks_by_type['vacation']:
        final_chunks.extend(chunks_by_type['vacation'][:MAX_CHUNKS_PER_TYPE])
        logger.info(f"Added {min(len(chunks_by_type['vacation']), MAX_CHUNKS_PER_TYPE)} vacation chunks")
    
    if is_skills_query and chunks_by_type['resume']:
        final_chunks.extend(chunks_by_type['resume'][:MAX_CHUNKS_PER_TYPE])
        logger.info(f"Added {min(len(chunks_by_type['resume']), MAX_CHUNKS_PER_TYPE)} resume chunks")
        # For skills queries, we ONLY want resume/skills chunks, not vacation or expense data
        if "skill" in query.lower() or "skills" in query.lower() or "resume" in query.lower():
            logger.info("Skills-specific query detected - excluding non-resume chunks")
            _query_cache[cache_key] = final_chunks
            return final_chunks  # Return only resume chunks for skills queries
    
    if is_expense_query and chunks_by_type['expense']:
        final_chunks.extend(chunks_by_type['expense'][:MAX_CHUNKS_PER_TYPE])
        logger.info(f"Added {min(len(chunks_by_type['expense']), MAX_CHUNKS_PER_TYPE)} expense chunks")
    
    # If we still have room, add chunks from other document types
    if len(final_chunks) < MAX_TOTAL_CHUNKS:
        # Add remaining chunks from all types
        remaining_chunks = []
        for doc_type in ['vacation', 'resume', 'expense', 'other']:
            if doc_type == 'vacation' and is_vacation_query:
                # Already added the top chunks
                remaining = chunks_by_type[doc_type][MAX_CHUNKS_PER_TYPE:]
            elif doc_type == 'resume' and is_skills_query:
                # Already added the top chunks
                remaining = chunks_by_type[doc_type][MAX_CHUNKS_PER_TYPE:]
            elif doc_type == 'expense' and is_expense_query:
                # Already added the top chunks
                remaining = chunks_by_type[doc_type][MAX_CHUNKS_PER_TYPE:]
            else:
                remaining = chunks_by_type[doc_type]
            
            remaining_chunks.extend(remaining)
        
        # Sort remaining chunks by score (assuming they have a metadata['score'] field)
        # If not, this will just maintain their original order
        remaining_chunks.sort(key=lambda x: x.metadata.get('score', 0), reverse=True)
        
        # Add as many as we have room for
        final_chunks.extend(remaining_chunks[:MAX_TOTAL_CHUNKS - len(final_chunks)])
    
    # If we still don't have any chunks, try a fallback approach with fewer restrictions
    if not final_chunks:
        logger.warning("No chunks found with primary approach, trying fallback")
        
        # Try again with a more relaxed approach - just get the top chunks from each namespace
        all_chunks = []
        for namespace in prioritized_namespaces:
            try:
                namespace_chunks = await _search_namespace(query, namespace, top_k=3)
                all_chunks.extend(namespace_chunks)
            except Exception as e:
                logger.error(f"Error in fallback search for namespace {namespace}: {str(e)}")
        
        # Sort by score and take the top MAX_TOTAL_CHUNKS
        all_chunks.sort(key=lambda x: x.metadata.get('score', 0), reverse=True)
        final_chunks = all_chunks[:MAX_TOTAL_CHUNKS]
    
    # Log the final chunks being returned
    logger.info(f"Final results include {len(final_chunks)} chunks")
    
    # Log the content of the chunks being returned (first 100 chars of each)
    for i, chunk in enumerate(final_chunks):
        namespace = chunk.metadata.get('namespace', 'unknown')
        logger.info(f"Chunk {i+1} (from {namespace}): {chunk.page_content[:100]}...")
    
    # Cache the results
    _query_cache[cache_key] = final_chunks
    
    return final_chunks

async def _search_namespace(query: str, namespace: str, top_k: int = 20):
    """
    Search for similar chunks in a specific namespace
    
    Args:
        query: The query string
        namespace: The namespace to search in
        top_k: Number of chunks to return
        
    Returns:
        List of Document objects
    """
    # Check if namespace exists
    index_path = os.path.join(settings.VECTOR_DB_PATH, f"{namespace}.index")
    docmap_path = os.path.join(settings.VECTOR_DB_PATH, f"{namespace}.pkl")
    
    if not os.path.exists(index_path) or not os.path.exists(docmap_path):
        logger.warning(f"Namespace {namespace} does not exist")
        return []
    
    # Load index and document map
    if namespace in _indices:
        index = _indices[namespace]
        doc_map = _document_map[namespace]
    else:
        index = faiss.read_index(index_path)
        with open(docmap_path, 'rb') as f:
            doc_map = pickle.load(f)
        _indices[namespace] = index
        _document_map[namespace] = doc_map
    
    # Generate query embedding
    query_embedding = generate_embeddings([query])[0]
    query_embedding = np.array([query_embedding]).astype('float32')
    faiss.normalize_L2(query_embedding)
    
    # Search index
    scores, indices = index.search(query_embedding, top_k)
    
    # Extract month and year from query for boosting
    target_month = extract_month_from_query(query)
    years = re.findall(r'\b20\d\d\b', query)
    
    # Create Document objects from search results
    documents = []
    for i, idx in enumerate(indices[0]):
        if idx != -1 and idx in doc_map:  # -1 indicates no match
            doc_data = doc_map[idx]
            content = doc_data["content"]
            
            # Calculate score boost based on content
            score_boost = 0
            
            # Boost score if content contains the target month
            if target_month and target_month in content.lower():
                score_boost += 0.5
                logger.info(f"Boosted score for result containing month {target_month}")
            
            # Boost score if content contains any of the years
            for year in years:
                if year in content:
                    score_boost += 0.3
                    logger.info(f"Boosted score for result containing year {year}")
            
            # Boost score based on keyword matches
            query_keywords = query.lower().split()
            keyword_matches = sum(1 for keyword in query_keywords if keyword in content.lower())
            if keyword_matches > 5:
                score_boost += 0.2
                logger.info(f"Boosted score for result with {keyword_matches} keyword matches")
            
            # Create Document object with boosted score
            doc = Document(
                page_content=content,
                metadata={
                    **doc_data["metadata"],
                    "score": float(scores[0][i]) + score_boost,
                    "namespace": namespace
                }
            )
            documents.append(doc)
    
    # Sort documents by boosted score
    documents.sort(key=lambda x: x.metadata["score"], reverse=True)
    
    return documents 