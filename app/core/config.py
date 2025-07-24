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

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file (allow later duplicates to override earlier ones)
# Ensure we load from the correct path
env_file = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_file, override=True)

# Gmail OAuth credentials will be loaded from environment variables (.env file)

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

class Settings:
    """Application settings"""
    
    # Project base directory
    BASE_DIR: ClassVar[Path] = BASE_DIR
    
    # Server settings
    HOST: str = os.getenv("HOST", DEFAULT_HOST)
    PORT: int = int(os.getenv("PORT", str(DEFAULT_PORT)))
    DEBUG: bool = os.getenv("DEBUG", str(DEFAULT_DEBUG)).lower() == "true"
    VERSION: str = os.getenv("VERSION", DEFAULT_VERSION)
    
    # Frontend settings (for OAuth redirects in hybrid deployment)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", f"http://{os.getenv('HOST', DEFAULT_HOST)}:{os.getenv('PORT', str(DEFAULT_PORT))}")
    
    # API settings
    API_V1_STR: str = os.getenv("API_V1_STR", API_V1_PREFIX)
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Personal AI Agent")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(DEFAULT_SECRET_KEY_LENGTH))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(DEFAULT_TOKEN_EXPIRE_MINUTES)))
    
    # Database settings (PostgreSQL only)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev")
    DATABASE_TIMEOUT: int = int(os.getenv("DATABASE_TIMEOUT", str(DATABASE_TIMEOUT_DEFAULT)))
    DATABASE_POOL_PRE_PING: bool = DATABASE_POOL_PRE_PING
    
    # File upload settings
    STATIC_DIR: str = str(BASE_DIR / "static")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BASE_DIR / DATA_DIR / "uploads"))
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
    
    # CORS settings for hybrid deployment
    ALLOWED_ORIGINS: list = (
        os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",") 
        if os.getenv("ALLOWED_ORIGINS") 
        else ["http://localhost:3000", "http://localhost:3001"]
    )
    CORS_ALLOW_CREDENTIALS: bool = CORS_ALLOW_CREDENTIALS
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", LOG_LEVEL_DEFAULT)
    LOG_FILE: str = str(BASE_DIR / LOGS_DIR / "app.log")
    LOG_MAX_BYTES: int = LOG_MAX_BYTES
    LOG_BACKUP_COUNT: int = LOG_BACKUP_COUNT
    
    # Gmail Integration settings (loaded from environment variables)
    GMAIL_CLIENT_ID: str = os.getenv("GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET: str = os.getenv("GMAIL_CLIENT_SECRET")
    GMAIL_REDIRECT_URI: str = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8000/api/gmail/callback")
    
    GMAIL_MAX_EMAILS_PER_SYNC: int = int(os.getenv("GMAIL_MAX_EMAILS_PER_SYNC", str(GMAIL_MAX_EMAILS_PER_SYNC)))
    GMAIL_DEFAULT_SYNC_LIMIT: int = int(os.getenv("GMAIL_DEFAULT_SYNC_LIMIT", str(GMAIL_DEFAULT_SYNC_LIMIT)))
    
    # Email processing settings
    EMAIL_STORAGE_DIR: str = str(BASE_DIR / DATA_DIR / "emails")
    EMAIL_VECTOR_DB_PATH: str = str(BASE_DIR / DATA_DIR / "email_vectors")
    
    # File upload settings
    UPLOAD_STORAGE_DIR: str = str(BASE_DIR / DATA_DIR / "uploads")
    
    def validate_gmail_config(self) -> None:
        """Validate Gmail OAuth configuration with detailed error messages"""
        errors = []
        warnings = []
        
        # Check required variables
        if not self.GMAIL_CLIENT_ID:
            errors.append("GMAIL_CLIENT_ID is required")
        elif not self.GMAIL_CLIENT_ID.endswith('.apps.googleusercontent.com'):
            warnings.append("GMAIL_CLIENT_ID should end with '.apps.googleusercontent.com'")
        elif self.GMAIL_CLIENT_ID == 'your_gmail_client_id_from_google_cloud_console':
            errors.append("GMAIL_CLIENT_ID is still set to placeholder value")
        
        if not self.GMAIL_CLIENT_SECRET:
            errors.append("GMAIL_CLIENT_SECRET is required")
        elif not self.GMAIL_CLIENT_SECRET.startswith('GOCSPX-'):
            warnings.append("GMAIL_CLIENT_SECRET should start with 'GOCSPX-'")
        elif self.GMAIL_CLIENT_SECRET == 'your_gmail_client_secret_from_google_cloud_console':
            errors.append("GMAIL_CLIENT_SECRET is still set to placeholder value")
        
        # Validate redirect URI
        if not self.GMAIL_REDIRECT_URI:
            errors.append("GMAIL_REDIRECT_URI is required")
        elif not self.GMAIL_REDIRECT_URI.startswith("http"):
            errors.append(f"GMAIL_REDIRECT_URI must start with 'http': {self.GMAIL_REDIRECT_URI}")
        elif not self.GMAIL_REDIRECT_URI.endswith('/api/gmail/callback'):
            warnings.append(f"GMAIL_REDIRECT_URI should end with '/api/gmail/callback': {self.GMAIL_REDIRECT_URI}")
        
        # Report errors and warnings
        if warnings:
            for warning in warnings:
                logger.warning(f"Gmail OAuth configuration warning: {warning}")
        
        if errors:
            logger.error("Gmail OAuth configuration errors found:")
            for error in errors:
                logger.error(f"  - {error}")
            logger.error("Please check your .env file or environment variables")
            logger.error("Gmail OAuth Setup Guide:")
            logger.error("  1. Go to https://console.cloud.google.com/")
            logger.error("  2. Create a new project or select existing one")
            logger.error("  3. Enable Gmail API")
            logger.error("  4. Create OAuth 2.0 credentials")
            logger.error("  5. Add authorized redirect URI: http://localhost:8000/api/gmail/callback")
            logger.error("  6. Copy Client ID and Client Secret to .env file")
            logger.error("GMAIL_CLIENT_ID should end with '.apps.googleusercontent.com'")
            logger.error("GMAIL_CLIENT_SECRET should start with 'GOCSPX-'")
            raise ValueError(f"Gmail OAuth configuration errors: {'; '.join(errors)}")
        
        logger.info("Gmail OAuth configuration validated successfully")

settings = Settings()

# Validate Gmail configuration at startup (only if not in testing mode)
import sys
if "pytest" not in sys.modules and "unittest" not in sys.modules:
    try:
        settings.validate_gmail_config()
    except ValueError as e:
        logger.warning(f"Gmail configuration validation failed: {e}")
        logger.warning("Gmail features will be disabled until configuration is fixed") 