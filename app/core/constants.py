"""
Application constants to replace hard-coded values
"""

# Server Configuration Constants
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000
DEFAULT_DEBUG = True

# Application Constants
DEFAULT_VERSION = "0.1.0"
DEFAULT_DESCRIPTION = "A fully private AI assistant for your documents"

# Security Constants
DEFAULT_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours - Extended from 15 minutes to prevent frequent logouts
DEFAULT_LOGIN_ENDPOINT = "/api/login"
DEFAULT_SECRET_KEY_LENGTH = 32

# File Upload Constants - PDF-focused processing
MAX_FILE_SIZE_DEFAULT = 10 * 1024 * 1024  # 10MB - Increased for PDF files
SUPPORTED_FILE_EXTENSIONS = ['.pdf']  # PDF-only processing

# LLM Constants
LLM_CONTEXT_DEFAULT = 2048  # Phi-2 model training context window (fixed context overflow)
LLM_THREADS_DEFAULT = 4
LLM_TEMPERATURE_DEFAULT = 0.7
LLM_TOP_P_DEFAULT = 0.9
LLM_TOP_K_DEFAULT = 40
LLM_MAX_TOKENS_DEFAULT = 512  # Reduced to allow more context
LLM_REPEAT_PENALTY_DEFAULT = 1.1

# Embedding Constants
EMBEDDING_MODEL_PRIMARY = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MODEL_FALLBACK = "paraphrase-MiniLM-L3-v2"
EMBEDDING_DIMENSION = 384
EMBEDDING_BATCH_SIZE_DEFAULT = 32
EMBEDDING_NORMALIZE = True

# Vector Store Constants
VECTOR_SEARCH_TOP_K_DEFAULT = 5
VECTOR_SIMILARITY_THRESHOLD_DEFAULT = 0.3
VECTOR_MAX_CHUNKS_DEFAULT = 3
VECTOR_CHUNK_OVERLAP_DEFAULT = 0.2
VECTOR_SCORE_THRESHOLD = 0.2
MAX_CHUNKS_PER_TYPE = 2
MAX_TOTAL_CHUNKS = 3
HIGH_QUALITY_SCORE_THRESHOLD = 0.85

# Database Constants (PostgreSQL)
DATABASE_TIMEOUT_DEFAULT = 30
DATABASE_POOL_PRE_PING = True

# Logging Constants
LOG_LEVEL_DEFAULT = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Metal/GPU Constants
METAL_N_GPU_LAYERS_DEFAULT = 1
USE_METAL_DEFAULT = True

# API Constants
API_V1_PREFIX = "/api"
OPENAPI_URL_SUFFIX = "/openapi.json"

# CORS Constants
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Directory Names
LOGS_DIR = "logs"
STATIC_DIR = "static"
UPLOADS_DIR = "uploads"
MODELS_DIR = "models"
DATA_DIR = "data"
VECTOR_DB_DIR = "vector_db"

# Default Model Filenames
DEFAULT_LLM_MODEL_FILENAME = "phi-2-instruct-Q4_K_M.gguf"

# Response Template Constants
MIN_RESPONSE_LENGTH_DEFAULT = 10
MAX_RESPONSE_LENGTH_DEFAULT = 2048
HALLUCINATION_THRESHOLD_DEFAULT = 0.9

# Validation Constants
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 8
EMAIL_MAX_LENGTH = 254
TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 1000

# HTTP Status Code Mappings (for consistency)
HTTP_SUCCESS = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_REQUEST_ENTITY_TOO_LARGE = 413
HTTP_INTERNAL_SERVER_ERROR = 500

# Gmail Integration Constants
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email'
]
GMAIL_MAX_EMAILS_PER_SYNC = 1000
GMAIL_DEFAULT_SYNC_LIMIT = 100
GMAIL_API_RATE_LIMIT = 250  # Requests per minute

# Email Processing Constants
EMAIL_CHUNK_SIZE_BUSINESS = 800
EMAIL_CHUNK_SIZE_PERSONAL = 600
EMAIL_CHUNK_SIZE_PROMOTIONAL = 400
EMAIL_CHUNK_SIZE_TRANSACTIONAL = 300
EMAIL_CHUNK_SIZE_SUPPORT = 700
EMAIL_CHUNK_SIZE_GENERIC = 500

EMAIL_CHUNK_OVERLAP_BUSINESS = 160
EMAIL_CHUNK_OVERLAP_PERSONAL = 120
EMAIL_CHUNK_OVERLAP_PROMOTIONAL = 80
EMAIL_CHUNK_OVERLAP_TRANSACTIONAL = 60
EMAIL_CHUNK_OVERLAP_SUPPORT = 140
EMAIL_CHUNK_OVERLAP_GENERIC = 100

# Email Classification Constants
EMAIL_TYPES = ['business', 'personal', 'promotional', 'transactional', 'support', 'generic']
EMAIL_CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.6

# Token Encryption Constants
TOKEN_ENCRYPTION_SALT = b'email_token_salt_2024'
TOKEN_ENCRYPTION_ITERATIONS = 100000