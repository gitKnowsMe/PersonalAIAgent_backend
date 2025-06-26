from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys

from app.core.config import settings

# Create database engine with better error handling
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # Check connection before using from pool
        connect_args={"connect_timeout": 5}  # Timeout after 5 seconds
    )
    # Test connection
    connection = engine.connect()
    connection.close()
    print("Database connection successful!")
except Exception as e:
    print(f"Error connecting to database: {e}")
    print(f"Using DATABASE_URL: {settings.DATABASE_URL}")
    print("Falling back to SQLite database")
    # Fall back to SQLite if PostgreSQL connection fails
    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "app.db")
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        sys.exit(1)
