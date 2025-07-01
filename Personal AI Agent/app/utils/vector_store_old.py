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

def identify_document_type(namespace, file_path=None, sample_content=None) -> Tuple[bool, bool, bool, bool]:
    """
    Identify document type based on namespace, file path, and sample content
    Returns tuple of (is_vacation, is_resume, is_expense, is_prompt_engineering)
    """
    is_vacation = False
    is_resume = False
    is_expense = False
    is_prompt_engineering = False
    
    # Check namespace
    namespace_lower = namespace.lower()
    if any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation']):
        is_vacation = True
    if any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume']):
        is_resume = True
    if any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense']):
        is_expense = True
    if any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['prompt_engineering']):
        is_prompt_engineering = True
    
    # If file path is provided, check it too
    if file_path:
        file_path_lower = file_path.lower()
        if any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation']):
            is_vacation = True
        if any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume']):
            is_resume = True
        if any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense']):
            is_expense = True
        if any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['prompt_engineering']):
            is_prompt_engineering = True
    
    # If sample content is provided, check it as well
    if sample_content:
        content_lower = sample_content.lower()
        if any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation']):
            is_vacation = True
        if any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume']):
            is_resume = True
        if any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense']):
            is_expense = True
        if any(keyword in content_lower for keyword in DOCUMENT_TYPE_KEYWORDS['prompt_engineering']):
            is_prompt_engineering = True
    
    return (is_vacation, is_resume, is_expense, is_prompt_engineering)

def check_query_type(query: str) -> Tuple[bool, bool, bool, bool, List[int]]:
    """
    Check if the query is about vacations, skills, expenses, or prompt engineering
    
    Args:
        query: The query string
        
    Returns:
        Tuple of (is_vacation_query, is_skills_query, is_expense_query, is_prompt_engineering_query, years)
    """
    query_lower = query.lower()
    
    # Check for vacation-related keywords
    is_vacation_query = any(keyword in query_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation'])
    
    # Check for skills-related keywords
    is_skills_query = any(keyword in query_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume'])
    
    # Check for expense-related keywords
    is_expense_query = any(keyword in query_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense'])
    
    # Check for prompt engineering keywords
    is_prompt_engineering_query = any(keyword in query_lower for keyword in DOCUMENT_TYPE_KEYWORDS['prompt_engineering'])
    
    # Extract years from the query
    years = []
    for match in re.finditer(r'\b(19|20)\d{2}\b', query):
        years.append(int(match.group(0)))
    
    logger.info(f"Query type detection: Vacation={is_vacation_query}, Skills={is_skills_query}, Expense={is_expense_query}, Prompt Engineering={is_prompt_engineering_query}, Years={years}")
    
    return is_vacation_query, is_skills_query, is_expense_query, is_prompt_engineering_query, years

def prioritize_namespaces(query: str, namespaces: List[str]) -> List[str]:
    """
    Prioritize namespaces based on query content
    
    Args:
        query: The search query
        namespaces: List of namespaces to prioritize
        
    Returns:
        Prioritized list of namespaces
    """
    # Check query type
    is_vacation_query, is_skills_query, is_expense_query, is_prompt_engineering_query, years = check_query_type(query)
    
    # Dictionary to store namespace priorities
    namespace_priorities = {}
    
    # Get file paths for namespaces
    namespace_to_file_path = get_file_paths_for_namespaces()
    
    # Identify document types
    for namespace in namespaces:
        # Default priority
        priority = 0
        
        # Get file path
        file_path = namespace_to_file_path.get(namespace, "")
        
        # Identify document type
        is_vacation, is_resume, is_expense, is_prompt_engineering = identify_document_type(namespace, file_path)
        
        # Prioritize based on query type
        if is_vacation_query and is_vacation:
            priority += 10
        
        if is_skills_query and is_resume:
            priority += 10
        
        if is_expense_query and is_expense:
            priority += 10
            
        if is_prompt_engineering_query and is_prompt_engineering:
            priority += 20  # Higher priority for prompt engineering
        
        # Check for years in the namespace
        for year in years:
            if str(year) in namespace or str(year) in file_path:
                priority += 5
        
        # Store priority
        namespace_priorities[namespace] = priority
    
    # Sort namespaces by priority (descending)
    prioritized = sorted(namespaces, key=lambda ns: namespace_priorities.get(ns, 0), reverse=True)
    
    # Log the prioritization
    logger.info(f"Namespace priorities: {[(ns, namespace_priorities.get(ns, 0)) for ns in prioritized]}")
    
    return prioritized

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

async def search_similar_chunks(query: str, user_id: int = None, document_id: Optional[int] = None, top_k: int = 20, metadata_filter: dict = None):
    """
    Search for similar chunks across all namespaces for a user
    
    Args:
        query: The search query
        user_id: The user ID to filter by
        document_id: Optional document ID to filter by
        top_k: Number of results to return
        metadata_filter: Optional metadata filter
        
    Returns:
        List of similar chunks
    """
    try:
        # Get all namespaces
        namespaces = []
        
        # Debug logging
        logger.info(f"Starting search for query: '{query}', user_id: {user_id}, document_id: {document_id}")
        
        # Get all index files in the vector DB directory
        for filename in os.listdir(settings.VECTOR_DB_PATH):
            if filename.endswith(".index"):
                namespace = filename[:-6]  # Remove .index extension
                
                # Filter by user_id if provided
                if user_id is not None and not namespace.startswith(f"user_{user_id}_"):
                    continue
                    
                # Filter by document_id if provided
                if document_id is not None:
                    # Get document from database
                    engine = create_engine(settings.DATABASE_URL)
                    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                    db = SessionLocal()
                    try:
                        document = db.query(DBDocument).filter(DBDocument.id == document_id).first()
                        if document and namespace != document.vector_namespace:
                            continue
                    finally:
                        db.close()
                
                namespaces.append(namespace)
        
        # Debug logging
        logger.info(f"Found {len(namespaces)} namespaces for search: {namespaces}")
        
        if not namespaces:
            logger.warning(f"No namespaces found for user_id: {user_id}, document_id: {document_id}")
            return []
        
        # Check query type
        is_vacation_query, is_skills_query, is_expense_query, is_prompt_engineering_query, years = check_query_type(query)
        logger.info(f"Query type detection - Vacation: {is_vacation_query}, Skills: {is_skills_query}, Expense: {is_expense_query}, Prompt Engineering: {is_prompt_engineering_query}, Years: {years}")
        
        # Prioritize namespaces based on query content
        prioritized_namespaces = prioritize_namespaces(query, namespaces)
        logger.info(f"Prioritized namespaces: {prioritized_namespaces}")
        
        # Extract month from query for expense queries
        target_month = None
        if is_expense_query:
            target_month = extract_month_from_query(query)
            if target_month:
                logger.info(f"Extracted month from query: {target_month}")
        
        # Search each namespace
        all_results = []
        
        for namespace in prioritized_namespaces:
            # Debug logging
            logger.info(f"Searching namespace: {namespace}")
            
            # Prepare metadata filter
            namespace_metadata_filter = metadata_filter.copy() if metadata_filter else {}
            
            # For expense queries with a month, filter by that month
            # TODO: Month filtering disabled as chunks don't have month metadata
            # if is_expense_query and target_month:
            #     namespace_metadata_filter["month"] = target_month
            
            # Search the namespace
            namespace_results = await _search_namespace(query, namespace, top_k, namespace_metadata_filter)
            
            # Debug logging
            logger.info(f"Found {len(namespace_results)} results in namespace {namespace}")
            
            # Add results to the list
            all_results.extend(namespace_results)
        
        # Sort all results by score
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Take top_k results
        top_results = all_results[:top_k]
        
        # Further trim the results to avoid overly long prompts
        if len(top_results) > MAX_TOTAL_CHUNKS:
            logger.info(f"Trimming results from {len(top_results)} to {MAX_TOTAL_CHUNKS} to keep prompt size manageable")
            top_results = top_results[:MAX_TOTAL_CHUNKS]
        
        # Debug logging
        logger.info(f"Returning {len(top_results)} results with scores: {[round(r['score'], 2) for r in top_results]}")
        
        return top_results
    except Exception as e:
        logger.error(f"Error searching similar chunks: {str(e)}")
        return []

async def _search_namespace(query: str, namespace: str, top_k: int = 20, metadata_filter: dict = None):
    """
    Search a single namespace for similar chunks
    
    Args:
        query: The search query
        namespace: The namespace to search
        top_k: Number of results to return
        metadata_filter: Optional metadata filter
        
    Returns:
        List of similar chunks
    """
    try:
        logger.info(f"Searching namespace: {namespace} for query: '{query}'")
        
        # Get embedding model
        embedding_model = get_embedding_model()
        
        # Generate query embedding
        query_embedding = await generate_embedding(query, embedding_model)
        
        # Load index
        index_path = os.path.join(settings.VECTOR_DB_PATH, f"{namespace}.index")
        if not os.path.exists(index_path):
            logger.warning(f"Index file not found: {index_path}")
            return []
            
        # Load document map
        document_map_path = os.path.join(settings.VECTOR_DB_PATH, f"{namespace}.pkl")
        if not os.path.exists(document_map_path):
            logger.warning(f"Document map file not found: {document_map_path}")
            return []
        
        # Load index and document map
        index = faiss.read_index(index_path)
        with open(document_map_path, "rb") as f:
            document_map = pickle.load(f)
        
        # Search index
        logger.info(f"Searching index with {index.ntotal} vectors")
        D, I = index.search(np.array([query_embedding]), min(top_k * 2, index.ntotal))  # Get more results than needed for filtering
        
        # Get results
        results = []
        for i, (dist, idx) in enumerate(zip(D[0], I[0])):
            if idx < 0 or idx >= len(document_map):
                continue
                
            # Get document entry (it may be a dict or a Langchain Document)
            entry = document_map[idx]

            # Support both dict entries (our current storage) and Langchain Document objects (legacy)
            if isinstance(entry, dict):
                content = entry.get("content", "")
                metadata = entry.get("metadata", {})
            else:
                content = getattr(entry, "page_content", "")
                metadata = getattr(entry, "metadata", {})

            # Calculate score (convert L2 distance to similarity score)
            # For L2 distance, smaller is better, so we use inverse relationship
            # Using a threshold-based approach: good results typically have distance < 1.5
            score = max(0.0, 1.0 - (dist / 2.0))  # Normalize distance and invert

            # Skip low-quality results - lowered threshold for L2 distance
            if score < 0.1:
                logger.debug(f"Skipping result {i} with low score: {score:.2f} (distance: {dist:.4f})")
                continue

            # Apply metadata filter if provided
            if metadata_filter:
                if not all(metadata.get(k) == v for k, v in metadata_filter.items()):
                    logger.debug(f"Skipping result {i} due to metadata filter mismatch")
                    continue

            # Ensure we have content
            if not content:
                logger.debug(f"Skipping result {i} with empty content")
                continue

            # Add result
            results.append({
                "content": content,
                "metadata": metadata,
                "score": score,
                "namespace": namespace
            })

            # Log result details
            logger.debug(f"Result {i}: score={score:.2f}, content_length={len(content)}")
            logger.debug(f"Content snippet: {content[:100]}...")
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Take top_k results
        top_results = results[:top_k]
        
        logger.info(f"Found {len(top_results)} results in namespace {namespace} with scores: {[round(r['score'], 2) for r in top_results]}")
        
        return top_results
    except Exception as e:
        logger.error(f"Error searching namespace {namespace}: {str(e)}")
        logger.exception("Full exception details:")
        return []

def identify_document_type_from_namespace(namespace: str, file_path: str = "") -> Tuple[bool, bool, bool, bool]:
    """
    Identify document type from namespace and file path
    
    Args:
        namespace: The namespace
        file_path: The file path (optional)
        
    Returns:
        Tuple of (is_vacation, is_resume, is_expense, is_prompt_engineering)
    """
    # Convert to lowercase for case-insensitive matching
    namespace_lower = namespace.lower()
    file_path_lower = file_path.lower() if file_path else ""
    
    # Check for document types in namespace
    is_vacation = any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation'])
    is_resume = any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume'])
    is_expense = any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense'])
    is_prompt_engineering = any(keyword in namespace_lower for keyword in DOCUMENT_TYPE_KEYWORDS['prompt_engineering'])
    
    # Check for document types in file path
    if file_path:
        is_vacation = is_vacation or any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['vacation'])
        is_resume = is_resume or any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['resume'])
        is_expense = is_expense or any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['expense'])
        is_prompt_engineering = is_prompt_engineering or any(keyword in file_path_lower for keyword in DOCUMENT_TYPE_KEYWORDS['prompt_engineering'])
    
    # Special case for prompt engineering
    if "prompt" in namespace_lower or "prompt" in file_path_lower:
        is_prompt_engineering = True
    
    # Log the detection
    logger.debug(f"Document type from namespace '{namespace}': Vacation={is_vacation}, Resume={is_resume}, Expense={is_expense}, Prompt Engineering={is_prompt_engineering}")
    
    return is_vacation, is_resume, is_expense, is_prompt_engineering 