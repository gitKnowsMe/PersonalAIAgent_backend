from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import time

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Document, Query, User
from app.schemas.query import QueryCreate, QueryResponse
from app.utils.llm import generate_answer
from app.services.vector_store_service import search_similar_chunks, check_query_type
# Using dynamic query handler for intelligent document parsing
from app.utils.dynamic_query_handler import dynamic_query_handler
from app.services.fallback_message_service import fallback_message_service
from app.services.error_message_service import error_message_service
from app.services.source_service import get_source_service

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Simple cache for document existence checks (5-minute TTL)
_document_cache = {}
_CACHE_TTL = 300  # 5 minutes

def has_documents_cached(user_id: int, db: Session) -> bool:
    """Check if user has documents with caching to reduce DB queries"""
    current_time = time.time()
    cache_key = f"user_docs_{user_id}"
    
    # Check cache first
    if cache_key in _document_cache:
        cached_time, has_docs = _document_cache[cache_key]
        if current_time - cached_time < _CACHE_TTL:
            return has_docs
    
    # Query database and cache result
    has_docs = db.query(Document).filter(Document.owner_id == user_id).first() is not None
    _document_cache[cache_key] = (current_time, has_docs)
    
    return has_docs


async def _search_emails(query: str, user_id: int, source_params: dict) -> List[dict]:
    """
    Helper function to search emails and return formatted chunks
    """
    from app.services.email.email_store import EmailStore
    from app.services.embedding_service import SentenceTransformerEmbeddingService
    
    logger.info(f"DEBUG: _search_emails called for user {user_id} with query '{query}'")
    email_store = EmailStore()
    embedding_service = SentenceTransformerEmbeddingService()
    email_chunks = []
    
    try:
        # Generate query embedding
        logger.info(f"DEBUG: Generating embedding for query '{query}'")
        query_embedding = await embedding_service.generate_embedding(query)
        logger.info(f"DEBUG: Generated embedding of length {len(query_embedding)}")
        
        # Detect if this is a financial/invoice query for smart email filtering
        financial_keywords = ["invoice", "receipt", "payment", "bill", "cost", "price", "amount", "total", "$", "paid", "charge"]
        is_financial_query = any(keyword in query.lower() for keyword in financial_keywords)
        logger.info(f"DEBUG: Is financial query: {is_financial_query}")
        
        # Determine email type filter
        email_type_filter = source_params.get('email_type_filter')
        logger.info(f"DEBUG: Email type filter: {email_type_filter}")
        
        # For now, always search all emails since category search has issues
        # TODO: Fix category-based search later
        logger.info(f"DEBUG: Calling email_store.search_emails for user {user_id}")
        email_results = email_store.search_emails(
            query_embedding=query_embedding,
            user_id=user_id,
            k=10
        )
        logger.info(f"DEBUG: Found {len(email_results)} email results for query: '{query}' for user {user_id}")
        
        # Convert email results to chunks format
        for i, result in enumerate(email_results):
            metadata = result.get('metadata', {})
            subject = metadata.get('subject', 'No Subject')
            sender = metadata.get('sender', 'Unknown Sender')
            email_content = f"[EMAIL from {sender}] Subject: {subject}\nContent: {result.get('text', '')}"
            logger.info(f"DEBUG: Email {i+1}: Subject='{subject}', Sender='{sender}', Score={result.get('score', 0.0)}")
            
            # Create chunk dictionary with proper format for LLM
            email_chunk = {
                'text': email_content,
                'score': result.get('score', 0.0),
                'metadata': {
                    'content_type': 'email',
                    'email_id': metadata.get('email_id', ''),
                    'subject': subject,
                    'sender': sender,
                    'sender_email': metadata.get('sender', ''),
                    'date': metadata.get('date', ''),
                    'classification_tags': metadata.get('classification_tags', [])
                },
                'namespace': f"user_{user_id}_email_{metadata.get('email_id', '')}"
            }
            email_chunks.append(email_chunk)
            
    except Exception as e:
        logger.error(f"DEBUG: Error searching emails for user {user_id}: {e}")
        logger.exception("Full exception details:")
        # Continue without email results
    
    logger.info(f"DEBUG: Returning {len(email_chunks)} email chunks for user {user_id}")
    return email_chunks


router = APIRouter()

@router.post("/ask", status_code=status.HTTP_200_OK)
async def ask_question(
    query: QueryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question about the documents
    """
    start_time = time.time()
    logger.info(f"Query request from user {current_user.username}: '{query.question}'")
    
    try:
        # Handle both new source selection and legacy document_id
        source_service = get_source_service()
        
        # Determine source parameters (prioritize new source_type/source_id over legacy document_id)
        if query.source_type is not None:
            # Use new source selection
            source_type = query.source_type
            source_id = query.source_id
            
            # Validate source selection
            if not await source_service.validate_source_selection(source_type, source_id, current_user.id, db):
                logger.warning(f"Invalid source selection: type='{source_type}', id='{source_id}' for user {current_user.username}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid source selection"
                )
            
            # Parse source parameters
            source_params = source_service.parse_source_selection(source_type, source_id)
            
        elif query.document_id:
            # Legacy document_id support
            document = db.query(Document).filter(
                Document.id == query.document_id,
                Document.owner_id == current_user.id
            ).first()
            
            if not document:
                logger.warning(f"Query failed: Document ID {query.document_id} not found for user {current_user.username}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_message_service.get_http_error_detail('document_not_found')
                )
            
            # Convert to new source parameters
            source_params = {
                'document_id': query.document_id,
                'email_type_filter': None,
                'search_documents': True,
                'search_emails': False
            }
        else:
            # Default: search all sources
            source_params = {
                'document_id': None,
                'email_type_filter': None,
                'search_documents': True,
                'search_emails': True
            }
        
        # Check if user has any documents (using cache) - but only if searching documents
        user_has_documents = has_documents_cached(current_user.id, db)
        if not user_has_documents and source_params.get('search_documents', False):
            # Only return no-documents message if actually searching documents
            if not source_params.get('search_emails', False):
                logger.warning(f"User {current_user.username} has no documents but tried to search documents only")
                # Generate dynamic no-documents message
                answer = fallback_message_service.generate_no_documents_message()
                
                # Log the query with the no-documents message
                log_document_id = source_params.get('document_id')
                
                query_log = Query(
                    question=query.question,
                    answer=answer,
                    document_id=log_document_id,
                    user_id=current_user.id
                )
                
                db.add(query_log)
                db.commit()
                db.refresh(query_log)
                
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                return {
                    "id": query_log.id,
                    "question": query_log.question,
                    "answer": answer,
                    "document_id": query_log.document_id,
                    "created_at": query_log.created_at,
                    "from_cache": False,
                    "response_time_ms": round(response_time, 2)
                }
            else:
                logger.info(f"User {current_user.username} has no documents but is searching emails - continuing")
            
        # Analyze the query type to provide better responses
        is_vacation_query, is_skills_query, is_expense_query, is_prompt_engineering_query, years = check_query_type(query.question)
        logger.info(f"Query types detected - Vacation: {is_vacation_query}, Skills: {is_skills_query}, Expense: {is_expense_query}, Prompt Engineering: {is_prompt_engineering_query}, Years: {years}")
        
        # Check for email prioritization keywords
        query_lower = query.question.lower().strip()
        email_prioritization_keywords = [
            # Current keywords
            "check emails", "search emails", "find emails", "look in emails", 
            "email search", "inbox search", "check my emails", "search my inbox",
            "check email", "find email", "look in email",
            
            # Enhanced natural variations
            "in my emails", "from emails", "email about", "emails for",
            "check inbox", "search inbox", "look in inbox",
            "my gmail", "gmail search", "email messages",
            
            # Question patterns
            "did I get an email", "any emails about", "email from",
            "emails containing", "emails with"
        ]
        prioritize_emails = any(keyword in query_lower for keyword in email_prioritization_keywords)
        logger.info(f"DEBUG: Query='{query_lower}', Keywords={email_prioritization_keywords}")
        logger.info(f"🔍 DEBUG: Prioritize emails={prioritize_emails}")
        if prioritize_emails:
            matching_keyword = next(keyword for keyword in email_prioritization_keywords if keyword in query_lower)
            logger.info(f"🔍 DEBUG: Query contains '{matching_keyword}' - PRIORITIZING EMAIL SEARCH for user {current_user.id}")
            
            # CRITICAL FIX: Override source parameters for EMAIL-ONLY search when email prioritization is detected
            logger.info(f"🔍 DEBUG: EMAIL PRIORITIZATION DETECTED - forcing email-only search")
            logger.info(f"🔍 DEBUG: Before override - search_emails={source_params.get('search_emails')}, search_documents={source_params.get('search_documents')}")
            source_params['search_emails'] = True
            source_params['search_documents'] = False  # ⭐ KEY ADDITION
            logger.info(f"🔍 DEBUG: After override - search_emails={source_params.get('search_emails')}, search_documents={source_params.get('search_documents')}")
            logger.info(f"🔍 DEBUG: CRITICAL CHECK - source_params after override: {source_params}")
        else:
            logger.info(f"🔍 DEBUG: No email prioritization keywords found in query for user {current_user.id}")
        
        # Search for similar chunks using vector search based on source selection
        try:
            document_chunks = []
            email_chunks = []
            
            # Determine search order based on email prioritization
            logger.info(f"DEBUG: Source params - search_documents: {source_params.get('search_documents')}, search_emails: {source_params.get('search_emails')}")
            if prioritize_emails:
                logger.info(f"DEBUG: EMAIL PRIORITIZED - searching emails first for user {current_user.id}")
                # Search emails first when prioritized
                if source_params['search_emails']:
                    logger.info(f"DEBUG: Calling _search_emails for user {current_user.id}")
                    email_chunks = await _search_emails(query.question, current_user.id, source_params)
                    logger.info(f"DEBUG: Found {len(email_chunks)} email chunks (prioritized) for user {current_user.id}")
                else:
                    logger.info(f"DEBUG: search_emails=False, skipping email search for user {current_user.id}")
                
                # Search documents second when emails are prioritized
                if source_params['search_documents']:
                    document_chunks = await search_similar_chunks(
                        query.question,
                        user_id=current_user.id,
                        document_id=source_params['document_id']
                    )
                    logger.info(f"DEBUG: Found {len(document_chunks)} document chunks (after email priority)")
            else:
                logger.info(f"DEBUG: Normal search order - documents first, then emails for user {current_user.id}")
                # Normal order: documents first, then emails
                if source_params['search_documents']:
                    document_chunks = await search_similar_chunks(
                        query.question,
                        user_id=current_user.id,
                        document_id=source_params['document_id']
                    )
                    logger.info(f"Found {len(document_chunks)} document chunks")
                
                if source_params['search_emails']:
                    email_chunks = await _search_emails(query.question, current_user.id, source_params)
                    logger.info(f"Found {len(email_chunks)} email chunks")
            
            # Combine chunks with prioritization
            if prioritize_emails:
                # When prioritizing emails, check if we actually have email results
                if len(email_chunks) == 0:
                    # No emails found despite email prioritization - provide helpful message
                    logger.warning(f"Email prioritization detected but no emails found for user {current_user.id}")
                    # Return helpful message suggesting to check PDFs
                    answer = "Sorry I couldn't find this information in the email, do you want me to check the pdf's?"
                    
                    try:
                        # Log the query with the fallback message
                        query_log = Query(
                            question=query.question,
                            answer=answer,
                            document_id=source_params.get('document_id'),
                            user_id=current_user.id
                        )
                        
                        db.add(query_log)
                        db.commit()
                        db.refresh(query_log)
                        
                        response_time = (time.time() - start_time) * 1000
                        
                        return {
                            "id": query_log.id,
                            "question": query_log.question,
                            "answer": answer,
                            "document_id": query_log.document_id,
                            "created_at": query_log.created_at,
                            "from_cache": False,
                            "response_time_ms": round(response_time, 2)
                        }
                    except Exception as e:
                        logger.error(f"Error in email fallback logging: {e}")
                        # Return fallback response even if logging fails
                        response_time = (time.time() - start_time) * 1000
                        return {
                            "id": None,
                            "question": query.question,
                            "answer": answer,
                            "document_id": None,
                            "created_at": None,
                            "from_cache": False,
                            "response_time_ms": round(response_time, 2)
                        }
                else:
                    # SUCCESS: We have emails when prioritizing emails - put them first!
                    logger.info(f"EMAIL PRIORITIZATION SUCCESS: Found {len(email_chunks)} email chunks for user {current_user.id}")
                    # When prioritizing emails, put email chunks first and significantly limit documents
                    # Only include document chunks if we have very few email results
                    if len(email_chunks) >= 3:
                        chunks = email_chunks + document_chunks[:2]  # Minimal documents when we have good email results
                    else:
                        chunks = email_chunks + document_chunks[:5]  # More documents if email results are sparse
                    logger.info(f"Email-prioritized search SUCCESS: {len(email_chunks)} email chunks + {len(document_chunks[:2 if len(email_chunks) >= 3 else 5])} document chunks = {len(chunks)} total")
            else:
                # Normal combination
                chunks = document_chunks + email_chunks
                logger.info(f"Combined search: {len(document_chunks)} document chunks + {len(email_chunks)} email chunks = {len(chunks)} total")

            # --- SOURCE ATTRIBUTION LOGIC ---
            sources = []
            seen_sources = set()
            
            # Smart source attribution: prioritize chunks that actually contain relevant information
            # while still respecting the ordering for LLM context
            def extract_key_terms_from_query(query_text):
                """Extract important terms from the query for relevance matching"""
                import re
                # Extract monetary amounts, numbers, and important keywords
                monetary_amounts = re.findall(r'\$[\d,]+\.?\d*', query_text.lower())
                numbers = re.findall(r'\b\d{3,}\b', query_text.lower())  # 3+ digit numbers
                # Extract merchant names and important terms (basic)
                important_words = []
                words = query_text.lower().split()
                for word in words:
                    if len(word) > 3 and word not in ['check', 'emails', 'much', 'what', 'how', 'was', 'the', 'and']:
                        important_words.append(word)
                return monetary_amounts + numbers + important_words
            
            def chunk_relevance_score(chunk, key_terms):
                """Calculate how relevant a chunk is based on key terms"""
                text = chunk.get('text', '').lower()
                score = 0
                for term in key_terms:
                    if term in text:
                        score += 1
                return score
            
            # Extract key terms from the query
            key_terms = extract_key_terms_from_query(query.question)
            logger.info(f"Extracted key terms for source attribution: {key_terms}")
            
            # Calculate relevance for all chunks and identify most relevant ones
            chunk_relevance = []
            for i, chunk in enumerate(chunks):
                if isinstance(chunk, dict):
                    relevance = chunk_relevance_score(chunk, key_terms)
                    chunk_relevance.append((i, chunk, relevance))
            
            # Sort by relevance (descending) but preserve original order for ties
            chunk_relevance.sort(key=lambda x: (-x[2], x[0]))
            
            # For source attribution, use:
            # 1. Top 3 most relevant chunks (if they have relevance > 0)
            # 2. Plus first 2 chunks (for context/prioritization)
            # This ensures we capture both prioritized sources and actual answer sources
            relevant_chunks = [item for item in chunk_relevance if item[2] > 0][:3]
            top_chunks = chunks[:2] if len(chunks) >= 2 else chunks[:1]
            
            # Combine relevant chunks and top chunks for attribution
            attribution_chunk_indices = set()
            for _, chunk, _ in relevant_chunks:
                attribution_chunk_indices.add(chunks.index(chunk))
            for i, chunk in enumerate(top_chunks):
                attribution_chunk_indices.add(i)
            
            chunks_for_attribution = [chunks[i] for i in sorted(attribution_chunk_indices)]
            
            logger.info(f"Source attribution using {len(chunks_for_attribution)} chunks: "
                       f"indices {sorted(attribution_chunk_indices)} "
                       f"(relevant chunks: {len(relevant_chunks)}, top chunks: {len(top_chunks)})")
            
            for chunk in chunks_for_attribution:
                if isinstance(chunk, dict):
                    meta = chunk.get('metadata', {})
                    ns = chunk.get('namespace', '')
                    # Email source
                    if meta.get('content_type') == 'email':
                        src_id = meta.get('email_id')
                        label = meta.get('subject') or meta.get('sender_email') or f"Email {src_id}"
                        key = f"email:{src_id}"
                        if key not in seen_sources:
                            sources.append({
                                'type': 'email',
                                'id': src_id,
                                'label': label
                            })
                            seen_sources.add(key)
                    # Document source
                    else:
                        src_id = meta.get('document_id') or meta.get('doc_id') or ns
                        title = meta.get('title', '')
                        filename = meta.get('filename', '')
                        
                        # Improve source attribution to prevent hallucination
                        if title and title.strip():
                            label = title.strip()
                        elif filename:
                            # Clean up filename for better display
                            clean_filename = filename.replace('user_7_', '').replace('.pdf', '')
                            if len(clean_filename) > 30:
                                clean_filename = clean_filename[:30] + '...'
                            label = f"Document: {clean_filename}"
                        else:
                            label = f"Document {src_id}"
                            
                        key = f"document:{src_id}"
                        if key not in seen_sources:
                            sources.append({
                                'type': 'document',
                                'id': src_id,
                                'label': label
                            })
                            seen_sources.add(key)
            # --- END SOURCE ATTRIBUTION LOGIC ---
            
        except Exception as search_error:
            logger.error(f"Error searching for chunks: {str(search_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message_service.get_http_error_detail('search_error')
            )
        
        if not chunks:
            logger.warning(f"No relevant chunks found for query: '{query.question}' by user {current_user.username}")
        
            # Generate dynamic fallback message based on query type and user documents
            query_types = {
                'is_vacation_query': is_vacation_query,
                'is_skills_query': is_skills_query,
                'is_expense_query': is_expense_query,
                'is_prompt_engineering_query': is_prompt_engineering_query
            }
            answer = fallback_message_service.generate_no_chunks_message(
                query_types, years, current_user.id, db
            )
            from_cache = False
        else:
            # Try dynamic query routing first
            try:
                dynamic_answer = await dynamic_query_handler.handle_query(query.question, current_user.id, chunks, db)
                if dynamic_answer:
                    logger.info("Query handled by specialized handler")
                    answer = dynamic_answer
                    from_cache = False
                else:
                    # Fall back to LLM generation
                    logger.info("No specialized handler available, using LLM")
                    try:
                        answer, from_cache = await generate_answer(query.question, chunks)
                    except (BrokenPipeError, OSError, IOError) as pipe_error:
                        logger.error(f"Broken pipe error while generating answer: {str(pipe_error)}")
                        answer = error_message_service.get_connection_error_message()
                        from_cache = False
                    except Exception as llm_error:
                        logger.error(f"Error generating answer: {str(llm_error)}")
                        if "broken pipe" in str(llm_error).lower() or "errno 32" in str(llm_error).lower():
                            answer = error_message_service.get_technical_difficulty_message(str(llm_error))
                            from_cache = False
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=error_message_service.get_http_error_detail('generation_error')
                            )
            except Exception as routing_error:
                logger.error(f"Error in query routing: {str(routing_error)}")
                # Fall back to LLM generation if routing fails
                try:
                    answer, from_cache = await generate_answer(query.question, chunks)
                except (BrokenPipeError, OSError, IOError) as pipe_error:
                    logger.error(f"Broken pipe error while generating answer: {str(pipe_error)}")
                    answer = error_message_service.get_connection_error_message()
                    from_cache = False
                except Exception as llm_error:
                    logger.error(f"Error generating answer: {str(llm_error)}")
                    if "broken pipe" in str(llm_error).lower() or "errno 32" in str(llm_error).lower():
                        answer = error_message_service.get_technical_difficulty_message(str(llm_error))
                        from_cache = False
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message_service.get_http_error_detail('generation_error')
                        )
        
        # Log the query
        try:
            # Use legacy document_id for compatibility with existing logging
            log_document_id = source_params.get('document_id') or query.document_id
            
            query_log = Query(
                question=query.question,
                answer=answer,
                document_id=log_document_id,
                user_id=current_user.id
            )
            
            db.add(query_log)
            db.commit()
            db.refresh(query_log)
            logger.info(f"Query logged successfully with ID: {query_log.id}")
        except Exception as db_error:
            logger.error(f"Failed to log query to database: {str(db_error)}")
            # Don't fail the request, just log the error
            db.rollback()
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Prepare response data
        if 'query_log' in locals() and hasattr(query_log, 'id') and query_log.id:
            logger.info(f"Query answered successfully: ID {query_log.id}, by user {current_user.username}, time: {response_time:.2f}ms, cached: {from_cache}")
            return {
                "id": query_log.id,
                "question": query_log.question,
                "answer": query_log.answer,
                "document_id": query_log.document_id,
                "created_at": query_log.created_at,
                "from_cache": from_cache,
                "response_time_ms": round(response_time, 2),
                "sources": sources
            }
        else:
            logger.warning(f"Query processed but not logged to database. User: {current_user.username}, time: {response_time:.2f}ms")
            return {
                "id": None,
                "question": query.question,
                "answer": answer,
                "document_id": query.document_id,
                "created_at": None,
                "from_cache": from_cache,
                "response_time_ms": round(response_time, 2),
                "sources": sources
            }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}, query: '{query.question}', by user {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message_service.get_http_error_detail('processing_error', str(e))
        )

# Add POST endpoint for /queries that calls the ask_question function
@router.post("/queries", status_code=status.HTTP_200_OK)
async def create_query(
    query: QueryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Alternative endpoint for asking questions (for compatibility)
    """
    return await ask_question(query, current_user, db)

@router.get("/queries", response_model=List[QueryResponse])
async def get_queries(
    limit: int = 50,
    offset: int = 0,
    since: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get queries for the current user with pagination and date filtering
    
    Args:
        limit: Maximum number of queries to return (default: 50, max: 100)
        offset: Number of queries to skip for pagination (default: 0)
        since: ISO date string to filter queries after this date (optional)
    """
    logger.info(f"Retrieving query history for user {current_user.username} (limit={limit}, offset={offset}, since={since})")
    
    # Validate limit
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1
        
    # Validate offset
    if offset < 0:
        offset = 0
    
    # Build query
    query = db.query(Query).filter(Query.user_id == current_user.id)
    
    # Add date filtering if provided
    if since:
        try:
            from datetime import datetime
            since_date = datetime.fromisoformat(since.replace('Z', '+00:00'))
            query = query.filter(Query.created_at >= since_date)
            logger.info(f"Filtering queries since {since_date}")
        except ValueError as e:
            logger.warning(f"Invalid since date format: {since}, error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (e.g., '2024-01-01T00:00:00Z')"
            )
    
    # Apply ordering, pagination
    queries = query.order_by(Query.created_at.desc()).offset(offset).limit(limit).all()
    
    logger.info(f"Retrieved {len(queries)} queries for user {current_user.username}")
    return queries 
