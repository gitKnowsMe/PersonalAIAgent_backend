from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import logging

from app.core.config import settings
from app.core.exceptions import ConfigurationError

logger = logging.getLogger("personal_ai_agent")

# Create database engine for PostgreSQL only
try:
    # PostgreSQL-specific configuration
    connect_args = {
        "connect_timeout": settings.DATABASE_TIMEOUT,
        "application_name": "personal_ai_agent"
    }
    
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        connect_args=connect_args,
        echo=False  # Set to True for SQL debugging
    )
    
    # Test connection
    connection = engine.connect()
    connection.close()
    logger.info("PostgreSQL database connection successful!")
    
except OperationalError as e:
    logger.error(f"PostgreSQL connection failed: {e}")
    logger.error(f"DATABASE_URL: {settings.DATABASE_URL}")
    logger.error("Please ensure PostgreSQL is running and credentials are correct")
    logger.error("Run 'python setup_postgresql.py' to set up the database")
    raise ConfigurationError(f"PostgreSQL connection failed: {e}")
    
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
