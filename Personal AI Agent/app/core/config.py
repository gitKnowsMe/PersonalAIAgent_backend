import os
import secrets
import logging
from pathlib import Path
from typing import Optional, ClassVar
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

from app.core.constants import *

# Get the logger
logger = logging.getLogger("personal_ai_agent")

# Load environment variables from .env file (allow later duplicates to override earlier ones)
load_dotenv(override=True)

# Load Metal settings
metal_enabled = os.getenv("USE_METAL", str(USE_METAL_DEFAULT)).lower() == "true"
metal_layers = int(os.getenv("METAL_N_GPU_LAYERS", str(METAL_N_GPU_LAYERS_DEFAULT)))

# Parse MAX_FILE_SIZE environment variable (handling comments if present)
max_file_size_str = os.getenv("MAX_FILE_SIZE", str(MAX_FILE_SIZE_DEFAULT))
if max_file_size_str:
    # Extract just the number part if there's a comment
    max_file_size_str = max_file_size_str.split('#')[0].strip()
    try:
        max_file_size = int(max_file_size_str)
    except ValueError:
        logger.warning(f"Invalid MAX_FILE_SIZE value: {max_file_size_str}, using default 5MB")
        max_file_size = MAX_FILE_SIZE_DEFAULT
else:
    max_file_size = MAX_FILE_SIZE_DEFAULT

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    """Application settings"""
    
    # Project base directory
    BASE_DIR: ClassVar[Path] = BASE_DIR
    
    # Server settings
    HOST: str = os.getenv("HOST", DEFAULT_HOST)
    PORT: int = int(os.getenv("PORT", str(DEFAULT_PORT)))
    DEBUG: bool = os.getenv("DEBUG", str(DEFAULT_DEBUG)).lower() == "true"
    VERSION: str = os.getenv("VERSION", DEFAULT_VERSION)
    
    # API settings
    API_V1_STR: str = os.getenv("API_V1_STR", API_V1_PREFIX)
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Personal AI Agent")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(DEFAULT_SECRET_KEY_LENGTH))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(DEFAULT_TOKEN_EXPIRE_MINUTES)))
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/personal_ai_agent.db")
    DATABASE_TIMEOUT: int = int(os.getenv("DATABASE_TIMEOUT", str(DATABASE_TIMEOUT_DEFAULT)))
    DATABASE_POOL_PRE_PING: bool = DATABASE_POOL_PRE_PING
    
    # File upload settings
    STATIC_DIR: str = str(BASE_DIR / "static")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / "static" / UPLOADS_DIR))
    MAX_FILE_SIZE: int = max_file_size
    SUPPORTED_EXTENSIONS: list = SUPPORTED_FILE_EXTENSIONS
    
    # Vector DB settings
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", str(BASE_DIR / DATA_DIR / VECTOR_DB_DIR))
    VECTOR_SEARCH_TOP_K: int = int(os.getenv("VECTOR_SEARCH_TOP_K", str(VECTOR_SEARCH_TOP_K_DEFAULT)))
    VECTOR_SIMILARITY_THRESHOLD: float = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", str(VECTOR_SIMILARITY_THRESHOLD_DEFAULT)))
    
    # Embedding model settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", EMBEDDING_MODEL_PRIMARY)
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", str(EMBEDDING_BATCH_SIZE_DEFAULT)))
    
    # LLM settings
    LLM_MODEL_PATH: str = os.getenv(
        "LLM_MODEL_PATH", 
        str(BASE_DIR / MODELS_DIR / DEFAULT_LLM_MODEL_FILENAME)
    )
    LLM_CONTEXT_WINDOW: int = int(os.getenv("LLM_CONTEXT_WINDOW", str(LLM_CONTEXT_DEFAULT)))
    LLM_THREADS: int = int(os.getenv("LLM_THREADS", str(LLM_THREADS_DEFAULT)))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", str(LLM_TEMPERATURE_DEFAULT)))
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", str(LLM_TOP_P_DEFAULT)))
    LLM_TOP_K: int = int(os.getenv("LLM_TOP_K", str(LLM_TOP_K_DEFAULT)))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", str(LLM_MAX_TOKENS_DEFAULT)))
    
    # Metal acceleration settings
    USE_METAL: bool = metal_enabled
    METAL_N_GPU_LAYERS: int = metal_layers
    
    # CORS settings
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
    CORS_ALLOW_CREDENTIALS: bool = CORS_ALLOW_CREDENTIALS
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", LOG_LEVEL_DEFAULT)
    LOG_FILE: str = str(BASE_DIR / LOGS_DIR / "app.log")
    LOG_MAX_BYTES: int = LOG_MAX_BYTES
    LOG_BACKUP_COUNT: int = LOG_BACKUP_COUNT

settings = Settings() 