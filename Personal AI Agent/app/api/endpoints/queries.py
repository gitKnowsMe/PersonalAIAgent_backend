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
        # Check if document_id is provided and valid
        if query.document_id:
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
        
        # Check if user has any documents (using cache)
        user_has_documents = has_documents_cached(current_user.id, db)
        if not user_has_documents:
            logger.warning(f"User {current_user.username} has no documents but tried to ask a question")
            # Generate dynamic no-documents message
            answer = fallback_message_service.generate_no_documents_message()
            
            # Log the query with the no-documents message
            query_log = Query(
                question=query.question,
                answer=answer,
                document_id=query.document_id,
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
            
        # Analyze the query type to provide better responses
        is_vacation_query, is_skills_query, is_expense_query, is_prompt_engineering_query, years = check_query_type(query.question)
        logger.info(f"Query types detected - Vacation: {is_vacation_query}, Skills: {is_skills_query}, Expense: {is_expense_query}, Prompt Engineering: {is_prompt_engineering_query}, Years: {years}")
        
        # Search for similar chunks using vector search (pure LLM approach)
        try:
            chunks = await search_similar_chunks(
                query.question,
                user_id=current_user.id,
                document_id=query.document_id
            )
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
            query_log = Query(
                question=query.question,
                answer=answer,
                document_id=query.document_id,
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
                "response_time_ms": round(response_time, 2)
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
                "response_time_ms": round(response_time, 2)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all queries for the current user
    """
    logger.info(f"Retrieving query history for user {current_user.username}")
    
    queries = db.query(Query).filter(Query.user_id == current_user.id).order_by(Query.created_at.desc()).all()
    return queries 
