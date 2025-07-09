"""
Dynamic Query Router - Route queries to appropriate handlers
"""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session

# Handlers temporarily disabled - using dynamic query handler approach
# from app.services.expense_handler import expense_handler
# from app.services.skills_handler import skills_handler
# from app.services.vacation_handler import vacation_handler

logger = logging.getLogger("personal_ai_agent")

class QueryRouter:
    """Route queries to appropriate specialized handlers"""
    
    def __init__(self):
        # Handlers temporarily disabled - using dynamic query handler approach
        # self.expense_handler = expense_handler
        # self.skills_handler = skills_handler
        # self.vacation_handler = vacation_handler
        pass
    
    async def route_query(self, query: str, user_id: int, chunks: List[str], db: Session) -> Optional[str]:
        """
        Route query to appropriate handler
        Returns: answer string if handled, None if should fall back to LLM
        """
        try:
            # Handlers temporarily disabled - using dynamic query handler approach
            # No specialized handler available, falling back to LLM
            logger.info("Query router disabled, falling back to LLM")
            return None
            
        except Exception as e:
            logger.error(f"Error in query routing: {e}")
            return None


# Global router instance
query_router = QueryRouter()