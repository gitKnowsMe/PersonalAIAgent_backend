from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import os
import sys
import logging

from app.core.config import settings
from app.core.constants import DATABASE_TIMEOUT_DEFAULT, SQLITE_THREAD_CHECK
from app.core.exceptions import ConfigurationError

logger = logging.getLogger("personal_ai_agent")

# Create database engine with specific error handling
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
        connect_args={"connect_timeout": settings.DATABASE_TIMEOUT}
    )
    # Test connection
    connection = engine.connect()
    connection.close()
    logger.info("Database connection successful!")
except OperationalError as e:
    logger.warning(f"Database connection failed (OperationalError): {e}")
    logger.info(f"Using DATABASE_URL: {settings.DATABASE_URL}")
    logger.info("Falling back to SQLite database")
    # Fall back to SQLite if primary database connection fails
    try:
        sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "app.db")
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": SQLITE_THREAD_CHECK})
        logger.info("SQLite fallback database initialized")
    except (OSError, SQLAlchemyError) as fallback_error:
        logger.error(f"Failed to initialize fallback database: {fallback_error}")
        raise ConfigurationError(f"Database initialization failed: {fallback_error}")
except SQLAlchemyError as e:
    logger.error(f"SQLAlchemy error during database setup: {e}")
    raise ConfigurationError(f"Database configuration error: {e}")
except Exception as e:
    logger.error(f"Unexpected error during database setup: {e}")
    raise ConfigurationError(f"Unexpected database error: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Modern SQLAlchemy declarative base"""
    pass

def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables in the database"""
    try:
        Base.metadata.create_all(bind=engine) 
        logger.info("Database tables created successfully!")
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating database tables: {e}")
        raise ConfigurationError(f"Failed to create database tables: {e}")
    except Exception as e:
        logger.error(f"Unexpected error creating database tables: {e}")
        raise ConfigurationError(f"Unexpected database table creation error: {e}")
