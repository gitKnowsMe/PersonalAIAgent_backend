# Configuration Guide

Comprehensive configuration options for Personal AI Agent.

## Environment Variables

The application uses environment variables for configuration. Copy `.env.example` to `.env` and customize:

### Core Settings

```env
# Server Configuration
HOST=localhost
PORT=8000
DEBUG=true

# Database Configuration
DATABASE_URL=sqlite:///./personal_ai_agent.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/dbname
```

### Security Configuration

```env
# Security - IMPORTANT: Change in production!
SECRET_KEY=your_super_secure_secret_key_minimum_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

!!! danger "Security Warning"
    Always change the `SECRET_KEY` in production. Use a secure random string of at least 32 characters.

### LLM Configuration

```env
# Model Settings
LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
LLM_CONTEXT_WINDOW=8192
LLM_THREADS=4

# Hardware Acceleration
USE_METAL=true           # macOS Metal acceleration
METAL_N_GPU_LAYERS=1     # Number of GPU layers
```

#### Model Options

| Model | Size | Performance | Memory |
|-------|------|-------------|--------|
| Mistral 7B Q4_K_M | 4.1GB | Balanced | 6GB RAM |
| Mistral 7B Q8_0 | 7.7GB | High Quality | 10GB RAM |
| Phi-2 Q4_K_M | 1.7GB | Fast | 3GB RAM |

### Embedding Configuration

```env
# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32
EMBEDDING_NORMALIZE=true
```

### Vector Storage

```env
# Vector Database Paths
VECTOR_DB_PATH=./data/vector_db
EMAIL_VECTOR_DB_PATH=./data/email_vectors

# Search Parameters
VECTOR_SEARCH_TOP_K=5
VECTOR_SIMILARITY_THRESHOLD=0.3
```

### File Upload Settings

```env
# File Limits
MAX_FILE_SIZE=10485760    # 10MB in bytes
UPLOAD_DIR=./static/uploads

# Supported formats are automatically detected
```

### Gmail Integration

```env
# OAuth2 Credentials (from Google Cloud Console)
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback

# Sync Settings
GMAIL_MAX_EMAILS_PER_SYNC=1000
GMAIL_DEFAULT_SYNC_LIMIT=100
```

#### Setting up Gmail OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Gmail API
4. Create OAuth2 credentials
5. Add authorized redirect URI: `http://localhost:8000/api/gmail/callback`
6. Copy client ID and secret to `.env`

### CORS Configuration

```env
# CORS Settings (for production)
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
```

### Logging Configuration

```env
# Logging Level
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Log file settings are configured in app/utils/logging_config.py
```

## Advanced Configuration

### Database Migration

For existing installations, migrate the database:

```bash
# General migration
python migrate_db.py

# Add constraints
python migrate_db_constraints.py

# Email-specific migration
python migrate_email_db.py
```

### Model Switching

Switch between different LLM models:

```bash
# Interactive model switching
python switch_model.py
```

### Performance Tuning

#### Memory Optimization

```env
# Reduce memory usage
LLM_THREADS=2
EMBEDDING_BATCH_SIZE=16
METAL_N_GPU_LAYERS=0    # Disable GPU if memory constrained
```

#### Speed Optimization

```env
# Maximize performance
LLM_THREADS=8           # Use more CPU cores
EMBEDDING_BATCH_SIZE=64 # Larger batches
USE_METAL=true          # Enable GPU acceleration
METAL_N_GPU_LAYERS=1
```

### Document Processing

#### Financial Document Settings

```python
# In app/utils/processors/financial_processor.py
CHUNK_SIZE = 500        # Small chunks for transactions
OVERLAP = 50           # Minimal overlap
```

#### Long-form Document Settings

```python
# In app/utils/processors/pdf_processor.py
CHUNK_SIZE = 1500      # Large chunks for context
OVERLAP = 300          # Significant overlap
```

## Configuration Files

### Main Configuration

- `app/core/config.py` - Primary configuration class
- `app/core/constants.py` - Application constants
- `.env` - Environment variables

### Development Configurations

- `.env.development` - Development settings
- `.env.testing` - Testing environment
- `.env.production` - Production settings

## Validation and Testing

### Configuration Validation

```bash
# Test configuration system
python test_config_system.py

# Verify model loading
python test_model_loading.py
```

### Environment-Specific Testing

```bash
# Test with specific environment
ENV=testing python test_api_query.py

# Test Gmail configuration
python test_email_search.py
```

## Production Considerations

### Security

- Use strong `SECRET_KEY`
- Configure specific `ALLOWED_ORIGINS`
- Use PostgreSQL instead of SQLite
- Enable HTTPS
- Set `DEBUG=false`

### Performance

- Use production-grade database
- Configure proper logging levels
- Set up monitoring
- Use reverse proxy (nginx)
- Configure file upload limits

### Monitoring

```env
# Add monitoring configuration
LOG_LEVEL=WARNING
SENTRY_DSN=your_sentry_dsn  # Optional error tracking
```

## Troubleshooting Configuration

### Common Issues

**Model Not Loading**
```bash
# Check model path
ls -la ./models/
python test_model_loading.py
```

**Database Connection Issues**
```bash
# Test database
python -c "from app.db.database import engine; print(engine.url)"
```

**Gmail OAuth Errors**
- Verify redirect URI matches exactly
- Check client ID and secret
- Ensure Gmail API is enabled

For more help, see [Troubleshooting Guide](../troubleshooting/common-issues.md).