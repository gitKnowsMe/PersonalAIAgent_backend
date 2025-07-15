"""
API dependencies for FastAPI endpoints

Provides common dependencies like database sessions and user authentication
"""

from app.core.security import get_current_user
from app.db.database import get_db

# Re-export the dependencies for easy import
__all__ = ["get_current_user", "get_db"] 