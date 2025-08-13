"""
Database Session Manager for Background Tasks

Provides proper session lifecycle management for background tasks that run
outside the scope of HTTP requests, preventing connection leaks and ensuring
proper transaction handling.
"""

import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


class BackgroundSessionManager:
    """Session manager for background tasks with proper lifecycle management."""
    
    @staticmethod
    def get_session() -> Session:
        """
        Create a new database session for background tasks.
        
        Note: Caller is responsible for closing the session.
        Use session_scope() context manager for automatic cleanup.
        
        Returns:
            New database session
        """
        return SessionLocal()
    
    @staticmethod
    @contextmanager
    def session_scope() -> Generator[Session, None, None]:
        """
        Session context manager with automatic cleanup and transaction handling.
        
        Provides:
        - Automatic session creation
        - Automatic commit on success
        - Automatic rollback on exception
        - Automatic session cleanup
        
        Yields:
            Database session
            
        Example:
            with BackgroundSessionManager.session_scope() as db:
                # Perform database operations
                user = db.query(User).first()
                # Session is automatically committed and closed
        """
        session = SessionLocal()
        try:
            logger.debug("Created new background session")
            yield session
            session.commit()
            logger.debug("Background session committed successfully")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in background session, rolling back: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error in background session, rolling back: {e}")
            raise
        finally:
            session.close()
            logger.debug("Background session closed")
    
    @staticmethod
    @contextmanager
    def readonly_session_scope() -> Generator[Session, None, None]:
        """
        Read-only session context manager for background tasks that only read data.
        
        This is optimized for read-only operations and doesn't attempt commits.
        
        Yields:
            Database session (read-only usage)
        """
        session = SessionLocal()
        try:
            logger.debug("Created new read-only background session")
            yield session
        except Exception as e:
            logger.error(f"Error in read-only background session: {e}")
            raise
        finally:
            session.close()
            logger.debug("Read-only background session closed")
    
    @staticmethod
    def test_connection() -> bool:
        """
        Test database connection for background tasks.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            from sqlalchemy import text
            with BackgroundSessionManager.session_scope() as db:
                # Simple query to test connection
                db.execute(text("SELECT 1")).fetchone()
                return True
        except Exception as e:
            logger.error(f"Background session connection test failed: {e}")
            return False


# Convenience alias for easier imports
background_session = BackgroundSessionManager.session_scope
readonly_background_session = BackgroundSessionManager.readonly_session_scope