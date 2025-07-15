"""
Enhanced configuration management with Pydantic BaseSettings.

Provides type-safe configuration with automatic validation, environment-specific
settings, and comprehensive error handling to replace hardcoded values.
"""

import os
import secrets
import logging
from pathlib import Path
from typing import List, Optional, Union, ClassVar
from enum import Enum

from pydantic import field_validator, Field, EmailStr
from pydantic.networks import HttpUrl
from pydantic_settings import BaseSettings

logger = logging.getLogger("personal_ai_agent")


class EnvironmentType(str, Enum):
    """Supported environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Supported log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ServerSettings(BaseSettings):
    """Server configuration settings."""
    
    host: str = Field(default="localhost", description="Server host address")
    port: int = Field(default=8000, ge=1024, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    reload: bool = Field(default=False, description="Enable auto-reload in development")
    workers: int = Field(default=1, ge=1, le=8, description="Number of worker processes")
    
    model_config = {"env_prefix": "SERVER_"}


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        min_length=32,
        description="Secret key for JWT tokens and encryption"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, 
        ge=1, 
        le=10080,  # Max 1 week
        description="Access token expiration time in minutes"
    )
    
    # Password requirements
    password_min_length: int = Field(default=8, ge=6, le=128)
    password_require_special: bool = Field(default=True)
    password_require_numbers: bool = Field(default=True)
    password_require_uppercase: bool = Field(default=True)
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if v == "your_super_secure_secret_key_here_32_chars_minimum":
            raise ValueError("SECRET_KEY must be changed from default placeholder")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    model_config = {"env_prefix": "SECURITY_"}


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(
        default="sqlite:///./personal_ai_agent.db",
        description="Database connection URL"
    )
    timeout: int = Field(default=30, ge=5, le=300, description="Database timeout in seconds")
    pool_pre_ping: bool = Field(default=True, description="Enable connection pool pre-ping")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    
    # Migration settings
    auto_migrate: bool = Field(default=True, description="Automatically run migrations")
    backup_before_migrate: bool = Field(default=True, description="Backup database before migrations")
    
    @field_validator('url')
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")
        return v
    
    model_config = {"env_prefix": "DATABASE_"}


class FileUploadSettings(BaseSettings):
    """File upload configuration settings."""
    
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,  # Min 1KB
        le=100 * 1024 * 1024,  # Max 100MB
        description="Maximum file size in bytes"
    )
    supported_extensions: str = Field(
        default=".pdf",
        description="Supported file extensions (comma-separated)"
    )
    upload_dir: Path = Field(
        default_factory=lambda: Path("./static/uploads"),
        description="Directory for uploaded files"
    )
    temp_dir: Path = Field(
        default_factory=lambda: Path("./temp"),
        description="Directory for temporary files"
    )
    cleanup_temp_files: bool = Field(default=True, description="Automatically cleanup temp files")
    
    @field_validator('supported_extensions')
    @classmethod
    def validate_extensions(cls, v):
        if isinstance(v, str):
            # Parse comma-separated string
            extensions = [ext.strip() for ext in v.split(',') if ext.strip()]
        else:
            extensions = v
        
        valid_extensions = {'.pdf', '.txt', '.docx', '.doc', '.eml', '.msg'}
        for ext in extensions:
            if ext.lower() not in valid_extensions:
                raise ValueError(f"Unsupported file extension: {ext}")
        
        return ','.join([ext.lower() for ext in extensions])
    
    @property
    def max_file_size_mb(self) -> float:
        """Get max file size in MB for display."""
        return self.max_file_size / (1024 * 1024)
    
    model_config = {"env_prefix": "UPLOAD_"}


class LLMSettings(BaseSettings):
    """Large Language Model configuration settings."""
    
    model_path: Path = Field(
        default_factory=lambda: Path("./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"),
        description="Path to LLM model file"
    )
    context_window: int = Field(default=8192, ge=1024, le=32768, description="Context window size")
    max_tokens: int = Field(default=512, ge=1, le=4096, description="Maximum output tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling")
    top_k: int = Field(default=40, ge=1, le=100, description="Top-k sampling")
    threads: int = Field(default=4, ge=1, le=16, description="Number of threads")
    
    # GPU/Metal acceleration
    use_metal: bool = Field(default=True, description="Enable Metal acceleration on macOS")
    metal_layers: int = Field(default=1, ge=0, le=80, description="Number of GPU layers for Metal")
    use_cuda: bool = Field(default=False, description="Enable CUDA acceleration")
    cuda_layers: int = Field(default=0, ge=0, le=80, description="Number of GPU layers for CUDA")
    
    @field_validator('model_path')
    @classmethod
    def validate_model_path(cls, v):
        if not isinstance(v, Path):
            v = Path(v)
        # Don't require file to exist during validation (might be downloaded later)
        return v
    
    model_config = {"env_prefix": "LLM_"}


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration settings."""
    
    model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model name"
    )
    dimension: int = Field(default=384, ge=128, le=4096, description="Embedding dimension")
    batch_size: int = Field(default=32, ge=1, le=256, description="Batch size for embedding")
    normalize: bool = Field(default=True, description="Normalize embeddings")
    cache_embeddings: bool = Field(default=True, description="Cache computed embeddings")
    
    model_config = {"env_prefix": "EMBEDDING_"}


class VectorStoreSettings(BaseSettings):
    """Vector store configuration settings."""
    
    path: Path = Field(
        default_factory=lambda: Path("./data/vector_db"),
        description="Vector database path"
    )
    search_top_k: int = Field(default=10, ge=1, le=100, description="Top K results for search")
    similarity_threshold: float = Field(
        default=0.3, 
        ge=0.0, 
        le=1.0, 
        description="Similarity threshold for relevance"
    )
    chunk_size: int = Field(default=1000, ge=100, le=4000, description="Document chunk size")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Chunk overlap size")
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        if info.data and 'chunk_size' in info.data and v >= info.data['chunk_size']:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v
    
    model_config = {"env_prefix": "VECTOR_"}


class GmailSettings(BaseSettings):
    """Gmail integration configuration settings."""
    
    client_id: Optional[str] = Field(
        default=None,
        description="Gmail OAuth2 client ID from Google Cloud Console"
    )
    client_secret: Optional[str] = Field(
        default=None,
        description="Gmail OAuth2 client secret from Google Cloud Console"
    )
    redirect_uri: HttpUrl = Field(
        default="http://localhost:8000/api/gmail/callback",
        description="OAuth2 redirect URI"
    )
    
    # Email sync settings
    max_emails_per_sync: int = Field(
        default=100, 
        ge=1, 
        le=1000, 
        description="Maximum emails to sync per request"
    )
    default_sync_limit: int = Field(
        default=50, 
        ge=1, 
        le=500, 
        description="Default number of emails to sync"
    )
    sync_frequency_minutes: int = Field(
        default=30, 
        ge=5, 
        le=1440, 
        description="Automatic sync frequency in minutes"
    )
    
    # API rate limiting
    api_rate_limit: int = Field(
        default=250, 
        ge=10, 
        le=1000, 
        description="Gmail API requests per minute"
    )
    
    @field_validator('client_id')
    @classmethod
    def validate_client_id(cls, v):
        if v and v == "your_gmail_client_id_from_google_cloud_console":
            raise ValueError("GMAIL_CLIENT_ID must be changed from placeholder value")
        if v and not v.endswith('.apps.googleusercontent.com'):
            raise ValueError("GMAIL_CLIENT_ID should end with '.apps.googleusercontent.com'")
        return v
    
    @field_validator('client_secret')
    @classmethod
    def validate_client_secret(cls, v):
        if v and v == "your_gmail_client_secret_from_google_cloud_console":
            raise ValueError("GMAIL_CLIENT_SECRET must be changed from placeholder value")
        if v and not v.startswith('GOCSPX-'):
            raise ValueError("GMAIL_CLIENT_SECRET should start with 'GOCSPX-'")
        return v
    
    @property
    def is_configured(self) -> bool:
        """Check if Gmail is properly configured."""
        return bool(self.client_id and self.client_secret)
    
    model_config = {"env_prefix": "GMAIL_"}


class EmailProcessingSettings(BaseSettings):
    """Email processing configuration settings."""
    
    # Storage settings
    storage_dir: Path = Field(
        default_factory=lambda: Path("./static/emails"),
        description="Email storage directory"
    )
    vector_db_path: Path = Field(
        default_factory=lambda: Path("./data/email_vectors"),
        description="Email vector database path"
    )
    
    # Processing settings
    chunk_size_business: int = Field(default=800, ge=200, le=2000)
    chunk_size_personal: int = Field(default=600, ge=200, le=2000)
    chunk_size_promotional: int = Field(default=400, ge=200, le=2000)
    chunk_size_transactional: int = Field(default=300, ge=200, le=2000)
    chunk_size_generic: int = Field(default=500, ge=200, le=2000)
    
    # Classification settings
    classification_confidence_threshold: float = Field(
        default=0.6, 
        ge=0.1, 
        le=0.95,
        description="Minimum confidence for email classification"
    )
    auto_classify: bool = Field(default=True, description="Automatically classify emails")
    
    model_config = {"env_prefix": "EMAIL_"}


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    file_path: Path = Field(
        default_factory=lambda: Path("./logs/app.log"),
        description="Log file path"
    )
    max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,
        description="Maximum log file size in bytes"
    )
    backup_count: int = Field(default=5, ge=1, le=20, description="Number of backup log files")
    
    # Console logging
    console_enabled: bool = Field(default=True, description="Enable console logging")
    console_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Console log format"
    )
    
    # File logging
    file_enabled: bool = Field(default=True, description="Enable file logging")
    file_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        description="File log format"
    )
    
    # Structured logging
    json_logging: bool = Field(default=False, description="Enable JSON structured logging")
    
    model_config = {"env_prefix": "LOG_"}


class CORSSettings(BaseSettings):
    """CORS configuration settings."""
    
    allowed_origins: str = Field(
        default="*",
        description="Allowed origins for CORS (comma-separated)"
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    allow_methods: str = Field(default="*", description="Allowed HTTP methods (comma-separated)")
    allow_headers: str = Field(default="*", description="Allowed HTTP headers (comma-separated)")
    
    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v):
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(',') if origin.strip()]
        else:
            origins = v
        # In production, warn if using wildcard
        if "*" in origins and len(origins) > 1:
            logger.warning("CORS: Wildcard '*' should not be mixed with specific origins")
        return ','.join(origins)
    
    model_config = {"env_prefix": "CORS_"}


class MonitoringSettings(BaseSettings):
    """Monitoring and metrics configuration."""
    
    enabled: bool = Field(default=True, description="Enable monitoring")
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    health_check_enabled: bool = Field(default=True, description="Enable health check endpoint")
    
    # Performance monitoring
    track_performance: bool = Field(default=True, description="Track performance metrics")
    slow_query_threshold: float = Field(
        default=1.0, 
        ge=0.1, 
        le=10.0, 
        description="Slow query threshold in seconds"
    )
    
    # Error monitoring
    error_tracking_enabled: bool = Field(default=True, description="Enable error tracking")
    error_alert_threshold: int = Field(
        default=10, 
        ge=1, 
        le=100, 
        description="Error count threshold for alerts"
    )
    
    model_config = {"env_prefix": "MONITORING_"}