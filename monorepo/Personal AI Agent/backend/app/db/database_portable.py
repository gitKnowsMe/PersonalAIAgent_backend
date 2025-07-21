"""
Portable Database Configuration for Single Executable Deployment

This module provides a database configuration that can work with both PostgreSQL 
(for development/server deployment) and SQLite (for single executable deployment).
"""

import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from app.core.config import settings

logger = logging.getLogger("personal_ai_agent")

class Base(DeclarativeBase):
    """Modern SQLAlchemy declarative base"""
    pass

def get_database_config():
    """
    Determine database configuration based on environment.
    
    Returns:
        dict: Database configuration with engine and connection details
    """
    # Check if we're in portable/executable mode
    portable_mode = os.getenv("PORTABLE_MODE", "false").lower() == "true"
    database_url = os.getenv("DATABASE_URL", "")
    
    if portable_mode or "sqlite" in database_url.lower():
        return get_sqlite_config()
    else:
        return get_postgresql_config()

def get_sqlite_config():
    """Configure SQLite for portable deployment."""
    logger.info("Configuring SQLite database for portable deployment")
    
    # Use data directory for SQLite file
    data_dir = Path(settings.BASE_DIR) / "data"
    data_dir.mkdir(exist_ok=True)
    
    db_file = data_dir / "personal_ai_agent_portable.db"
    database_url = f"sqlite:///{db_file}"
    
    # SQLite-specific configuration
    connect_args = {
        "check_same_thread": False,  # Allow multiple threads
        "timeout": 20,  # 20 second timeout
        "isolation_level": None,  # Autocommit mode
    }
    
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
    
    return {
        "engine": engine,
        "database_url": database_url,
        "database_type": "sqlite",
        "data_dir": data_dir,
        "db_file": db_file
    }

def get_postgresql_config():
    """Configure PostgreSQL for development/server deployment."""
    logger.info("Configuring PostgreSQL database for server deployment")
    
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
        echo=False
    )
    
    return {
        "engine": engine,
        "database_url": settings.DATABASE_URL,
        "database_type": "postgresql",
        "connect_args": connect_args
    }

def create_portable_database():
    """
    Create and initialize database for portable deployment.
    
    This function ensures the database exists and has the correct schema.
    """
    config = get_database_config()
    engine = config["engine"]
    
    try:
        # Test connection
        with engine.connect() as connection:
            if config["database_type"] == "sqlite":
                # Enable foreign key constraints for SQLite
                connection.execute(text("PRAGMA foreign_keys = ON"))
                # Enable WAL mode for better concurrency
                connection.execute(text("PRAGMA journal_mode = WAL"))
                # Set reasonable timeout
                connection.execute(text("PRAGMA busy_timeout = 30000"))
                logger.info("SQLite database configured with foreign keys and WAL mode")
            
        # Create all tables
        from app.db.models import Base
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database tables created successfully ({config['database_type']})")
        
        return config
        
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        raise
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        raise

# Initialize database configuration
try:
    db_config = create_portable_database()
    engine = db_config["engine"]
    database_type = db_config["database_type"]
    
    logger.info(f"Database initialized: {database_type}")
    
    # Test connection
    with engine.connect() as connection:
        if database_type == "postgresql":
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"PostgreSQL connection successful: {version[:50]}...")
        else:
            result = connection.execute(text("SELECT sqlite_version()"))
            version = result.fetchone()[0]
            logger.info(f"SQLite connection successful: version {version}")
    
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    # For executable deployment, we should continue with a fallback
    if os.getenv("PORTABLE_MODE") == "true":
        logger.warning("Continuing in portable mode with fallback configuration")
        # Create a minimal SQLite configuration as fallback
        data_dir = Path.cwd() / "data"
        data_dir.mkdir(exist_ok=True)
        db_file = data_dir / "personal_ai_agent_portable.db"
        database_url = f"sqlite:///{db_file}"
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
        database_type = "sqlite"
    else:
        raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_database_info():
    """Get information about the current database configuration."""
    return {
        "type": database_type,
        "url": db_config.get("database_url", "unknown") if 'db_config' in globals() else "unknown",
        "portable_mode": os.getenv("PORTABLE_MODE", "false").lower() == "true",
        "engine": engine.__class__.__name__
    }

def migrate_postgresql_to_sqlite():
    """
    Utility function to migrate data from PostgreSQL to SQLite for portable deployment.
    
    This is used during the executable creation process.
    """
    logger.info("Starting PostgreSQL to SQLite migration for portable deployment")
    
    # This would be implemented during the executable build process
    # to export user data from PostgreSQL and import into SQLite
    pass

def create_tables():
    """Create all tables in the database"""
    try:
        from app.db.models import Base
        Base.metadata.create_all(bind=engine) 
        logger.info(f"Database tables created successfully ({database_type})")
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error creating database tables: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating database tables: {e}")
        raise