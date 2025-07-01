from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Document, Query, User
from app.schemas.query import QueryCreate, QueryResponse
from app.utils.llm import generate_answer
from app.utils.vector_store import search_similar_chunks, check_query_type

# Get the logger
logger = logging.getLogger("personal_ai_agent")

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
                    detail="Document not found"
                )
        
        # Check if user has any documents
        user_has_documents = db.query(Document).filter(Document.owner_id == current_user.id).count() > 0
        if not user_has_documents:
            logger.warning(f"User {current_user.username} has no documents but tried to ask a question")
            answer = "You haven't uploaded any documents yet. Please upload some documents before asking questions."
            
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
            
            return {
                "id": query_log.id,
                "question": query_log.question,
                "answer": answer,
                "document_id": query_log.document_id,
                "created_at": query_log.created_at
            }
            
        # Analyze the query type to provide better responses
        is_vacation_query, is_skills_query, is_expense_query, is_prompt_engineering_query, years = check_query_type(query.question)
        logger.info(f"Query types detected - Vacation: {is_vacation_query}, Skills: {is_skills_query}, Expense: {is_expense_query}, Prompt Engineering: {is_prompt_engineering_query}, Years: {years}")
        
        # Search for similar chunks
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
                detail="Error searching documents. Please try again."
            )
        
        if not chunks:
            logger.warning(f"No relevant chunks found for query: '{query.question}' by user {current_user.username}")
        
            # Provide a more specific message based on query type
            if is_vacation_query and is_skills_query and is_expense_query:
                answer = "I couldn't find any information about your vacation, skills, or expenses in the uploaded documents. Please upload relevant documents or try a more specific question."
            elif is_prompt_engineering_query:
                answer = "I couldn't find any information about prompt engineering in your uploaded documents. Please upload relevant documents about AI, machine learning, or prompt engineering and try again."
            elif is_vacation_query:
                if years:
                    answer = f"I couldn't find any information about your vacation in {', '.join(years)}. Please upload relevant travel documents or try a different question."
                else:
                    answer = "I couldn't find any information about your vacations in the uploaded documents. Please upload travel documents or try a different question."
            elif is_skills_query:
                answer = "I couldn't find any information about your technical skills in the uploaded documents. Please upload your resume or CV and try again."
            elif is_expense_query:
                if years:
                    answer = f"I couldn't find any expense information for {', '.join(years)}. Please upload relevant financial documents and try again."
                else:
                    answer = "I couldn't find any expense information in the uploaded documents. Please upload financial records and try again."
            else:
                answer = "I don't have enough information to answer that question. Please upload relevant documents first or try a different question."
        else:
            # Generate answer
            try:
                answer = await generate_answer(query.question, chunks)
            except Exception as llm_error:
                logger.error(f"Error generating answer: {str(llm_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error generating answer. Please try again."
                )
        
        # Log the query
        query_log = Query(
            question=query.question,
            answer=answer,
            document_id=query.document_id,
            user_id=current_user.id
        )
    
        db.add(query_log)
        db.commit()
        db.refresh(query_log)
        
        logger.info(f"Query answered successfully: ID {query_log.id}, by user {current_user.username}")
        
        return {
            "id": query_log.id,
            "question": query_log.question,
            "answer": query_log.answer,
            "document_id": query_log.document_id,
            "created_at": query_log.created_at
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}, query: '{query.question}', by user {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
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
