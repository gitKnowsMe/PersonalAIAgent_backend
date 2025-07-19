"""
Dynamic query handler to replace hardcoded responses with intelligent parsing
"""

import logging
import os
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session

logger = logging.getLogger("personal_ai_agent")

class DynamicQueryHandler:
    """Handle queries dynamically by parsing actual document content"""
    
    def __init__(self):
        # Load expense keywords from environment or use defaults
        self.expense_keywords = self._load_expense_keywords()
        # Load skills keywords
        self.skills_keywords = self._load_skills_keywords()
    
    def _load_expense_keywords(self) -> List[str]:
        """Load expense keywords from environment or configuration"""
        # Try to get from environment first
        env_keywords = os.getenv("EXPENSE_KEYWORDS")
        if env_keywords:
            return [keyword.strip() for keyword in env_keywords.split(",")]
        
        # Default keywords if no environment config
        return [
            "spend", "spent", "expense", "expenses", "cost", "money", "dollar", "$",
            "budget", "payment", "paid", "purchase", "transaction", "bill", "total",
            "finance", "financial", "receipt", "invoice", "charge"
        ]
    
    def _load_skills_keywords(self) -> List[str]:
        """Load skills keywords from environment or configuration"""
        # Try to get from environment first
        env_keywords = os.getenv("SKILLS_KEYWORDS")
        if env_keywords:
            return [keyword.strip() for keyword in env_keywords.split(",")]
        
        # Default keywords if no environment config
        return [
            "skill", "skills", "technical", "programming", "experience", "competency",
            "expertise", "technology", "tools", "languages", "frameworks", "abilities"
        ]
    
    async def handle_query(self, query: str, user_id: int, chunks: List[str], db: Session) -> Optional[str]:
        """
        Attempt to handle query dynamically by parsing document content
        Returns: answer string if handled, None if should fall back to LLM
        """
        try:
            # Check if it's an expense query
            if self._is_expense_query(query):
                return await self._handle_expense_query(query, user_id, chunks, db)
            
            # Check if it's a skills query
            if self._is_skills_query(query):
                return await self._handle_skills_query(query, user_id, chunks, db)
            
            # All other queries fall back to LLM processing
            return None  # Fall back to LLM processing
            
        except Exception as e:
            logger.error(f"Error in dynamic query handling: {e}")
            return None  # Fall back to LLM processing
    
    def _is_expense_query(self, query: str) -> bool:
        """
        Check if a query is expense-related using configurable keywords
        """
        if not query:
            return False
            
        query_lower = query.lower()
        
        # Check for expense keywords
        return any(keyword in query_lower for keyword in self.expense_keywords)
    
    def _is_skills_query(self, query: str) -> bool:
        """
        Check if a query is skills-related using configurable keywords
        """
        if not query:
            return False
            
        query_lower = query.lower()
        
        # Check for skills keywords
        return any(keyword in query_lower for keyword in self.skills_keywords)
    
    async def _handle_expense_query(self, query: str, user_id: int, chunks: List[Any], db: Session) -> Optional[str]:
        """Handle expense-related queries using the enhanced financial filter"""
        try:
            # Normalize chunks to text
            chunk_texts = []
            for chunk in chunks:
                if isinstance(chunk, dict):
                    chunk_texts.append(chunk.get('content', ''))
                elif hasattr(chunk, 'page_content'):
                    chunk_texts.append(chunk.page_content)
                else:
                    chunk_texts.append(str(chunk))
            
            # Use the enhanced financial filter for better matching
            from app.utils.response_filter import financial_filter
            
            # Create a generic response that the filter can improve
            generic_response = "Based on the available information, I found some financial information."
            
            # Let the financial filter do the smart matching
            filtered_response = financial_filter.filter_financial_response(query, generic_response, chunk_texts)
            
            # If the filter provided a specific response, use it
            if filtered_response and not filtered_response.startswith("I found some financial information"):
                logger.info(f"Dynamic expense handler using financial filter result: {filtered_response}")
                return filtered_response
            
            # If no specific match, return None to fall back to LLM
            return None
        except Exception as e:
            logger.error(f"Error handling expense query dynamically: {e}")
            return None
    
    async def _handle_skills_query(self, query: str, user_id: int, chunks: List[Any], db: Session) -> Optional[str]:
        """Handle skills-related queries by creating a more targeted search"""
        try:
            from app.services.vector_store_service import search_similar_chunks
            
            # Create a more targeted query for skills
            enhanced_query = f"programming languages Java Python testing tools Selenium automation experience technical skills competencies {query}"
            
            # Search for more specific skills-related content
            skills_chunks = await search_similar_chunks(
                enhanced_query, 
                user_id=user_id, 
                top_k=10
            )
            
            # Filter chunks to get those with substantial content about skills
            substantial_chunks = []
            for chunk in skills_chunks:
                if isinstance(chunk, dict):
                    content = chunk.get('content', '')
                    metadata = chunk.get('metadata', {})
                    section = metadata.get('section_header', '').lower()
                    
                    # Look for chunks with skills-related content
                    if (len(content) > 50 and 
                        (any(skill in content.lower() for skill in ['java', 'python', 'selenium', 'programming', 'testing', 'automation', 'framework', 'tool']) or
                         any(section_keyword in section for section_keyword in ['skill', 'technical', 'accomplishment', 'summary', 'experience']))):
                        substantial_chunks.append(chunk)
            
            if substantial_chunks:
                # Use the enhanced LLM to generate a skills-focused response
                from app.utils.llm import generate_answer
                
                # Create a skills-focused query
                skills_query = "List and describe the technical skills, programming languages, tools, and technologies mentioned in the context"
                
                response, _ = await generate_answer(skills_query, substantial_chunks[:5])
                
                if response and not response.startswith("I found some relevant information"):
                    logger.info(f"Dynamic skills handler providing specialized response")
                    return response
            
            # If no specific skills found, return None to fall back to LLM
            return None
            
        except Exception as e:
            logger.error(f"Error handling skills query dynamically: {e}")
            return None
    


def get_user_documents_content(user_id: int, db: Session) -> List[str]:
    """Get content of all documents for a user"""
    try:
        from app.db.models import Document
        import os
        
        documents = db.query(Document).filter(Document.owner_id == user_id).all()
        contents = []
        
        for doc in documents:
            file_path = doc.path
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        contents.append(content)
                except Exception as e:
                    logger.error(f"Error reading document {file_path}: {e}")
                    continue
        
        return contents
        
    except Exception as e:
        logger.error(f"Error getting user documents content: {e}")
        return []


# Global instance
dynamic_query_handler = DynamicQueryHandler()