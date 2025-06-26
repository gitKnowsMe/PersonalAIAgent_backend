import os
import secrets
import logging
from pathlib import Path
from typing import Optional, ClassVar
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Load environment variables from .env file
load_dotenv()

# Log environment variables for debugging
metal_enabled = os.getenv("USE_METAL", "true").lower() == "true"
metal_layers = int(os.getenv("METAL_N_GPU_LAYERS", "1"))
print(f"DEBUG ENV: USE_METAL={metal_enabled}, METAL_N_GPU_LAYERS={metal_layers}")
logger.info(f"DEBUG ENV: USE_METAL={metal_enabled}, METAL_N_GPU_LAYERS={metal_layers}")

# Parse MAX_FILE_SIZE environment variable (handling comments if present)
max_file_size_str = os.getenv("MAX_FILE_SIZE", "5242880")
if max_file_size_str:
    # Extract just the number part if there's a comment
    max_file_size_str = max_file_size_str.split('#')[0].strip()
    try:
        max_file_size = int(max_file_size_str)
    except ValueError:
        logger.warning(f"Invalid MAX_FILE_SIZE value: {max_file_size_str}, using default 5MB")
        max_file_size = 5 * 1024 * 1024  # Default to 5MB
else:
    max_file_size = 5 * 1024 * 1024  # Default to 5MB

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    """Application settings"""
    
    # Project base directory
    BASE_DIR: ClassVar[Path] = BASE_DIR
    
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Personal AI Agent"
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/personal_ai_agent.db")
    
    # File upload settings
    STATIC_DIR: str = str(BASE_DIR / "static")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "static" / "uploads"))
    MAX_FILE_SIZE: int = max_file_size
    
    # Vector DB settings
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", str(BASE_DIR / "data" / "vector_db"))
    
    # Embedding model settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # LLM settings
    LLM_MODEL_PATH: str = os.getenv(
        "LLM_MODEL_PATH", 
        str(BASE_DIR / "models" / "mistral-7b-instruct-v0.1.Q4_K_M.gguf")
    )
    LLM_CONTEXT_WINDOW: int = int(os.getenv("LLM_CONTEXT_WINDOW", "4096"))
    LLM_THREADS: int = int(os.getenv("LLM_THREADS", "4"))
    
    # Metal acceleration settings
    USE_METAL: bool = metal_enabled
    METAL_N_GPU_LAYERS: int = metal_layers
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = str(BASE_DIR / "logs" / "app.log")

settings = Settings() 