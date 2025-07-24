# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download AI models (~4GB total)
python download_model.py              # Mistral 7B LLM
python download_embedding_model.py    # MiniLM embedding model

# Setup database and admin user
python setup_db.py
python create_admin.py
```

### Running the Application
```bash
# Start backend (recommended - with setup validation)
python start_backend.py

# Alternative direct start
python main.py

# Start with uvicorn directly
uvicorn app.main:app --host localhost --port 8000 --reload
```

### Testing Commands
```bash
# Backend connection and health checks
python test_backend_connection.py

# Core functionality tests
python test_email_search.py           # Gmail integration
python test_api_query.py             # Query processing
python test_model_loading.py         # LLM loading
python test_classification_tags_fix.py # Document classification

# Unit tests (pytest)
python -m pytest tests/
python -m pytest tests/test_document_classifier.py
python -m pytest tests/test_document_classifier.py::test_financial_classification

# Feature-specific integration tests
python test_mixed_sources.py         # PDF + Email search
python test_source_attribution_fix.py # Source tracking
python test_performance_indexes.py   # Database performance
```

### Database Operations
```bash
# Fresh database setup
python setup_db.py

# Database migrations
python migrate_db.py
python migrate_db_constraints.py
python migrate_add_performance_indexes.py

# Email-specific database setup
python migrate_email_db.py

# Admin user management
python create_admin.py
python create_test_user.py
```

### Building and Deployment
```bash
# Build executable for current platform
python build_executable.py

# Build with models included (large file)
python build_executable.py --include-models

# Create installer package
python create_installer_package.py --platform darwin

# Trigger CI/CD builds (creates releases for all platforms)
git tag v1.0.0
git push origin v1.0.0
```

## Architecture Overview

### Core Application Structure
The application is a **privacy-first AI backend** built with FastAPI that provides local LLM processing, document analysis, and Gmail integration. Key architectural principles:

- **Local-First**: All AI processing happens locally using Mistral 7B
- **Category-Aware Processing**: Documents classified and processed with optimized strategies
- **Hybrid Database**: PostgreSQL for development, SQLite for portable executables
- **CORS-Enabled**: Designed to work with separate frontend deployments

### Application Layers

**FastAPI Application** (`app/main.py`):
- Lifespan management with startup/shutdown events
- Automatic directory creation and database initialization
- CORS middleware for frontend integration
- Static file serving for legacy frontend

**Core Configuration** (`app/core/`):
- `config.py` - Environment-based settings with validation
- `constants.py` - Application-wide constants and defaults
- `security.py` - JWT authentication and bcrypt hashing

**Database Layer** (`app/db/`):
- `database.py` - PostgreSQL connection with SQLAlchemy
- `database_portable.py` - SQLite support for executables
- `models.py` - Database schema with relationships

**API Endpoints** (`app/api/endpoints/`):
- `auth.py` - JWT authentication and user management
- `documents.py` - PDF upload and processing
- `queries.py` - AI-powered query processing with LLM
- `gmail.py` - OAuth2 flow and email synchronization
- `sources.py` - Knowledge source management

### Document Processing Pipeline

**Classification System** (`app/utils/document_classifier.py`):
- **Financial Documents**: Bank statements, invoices → 500-char chunks for transaction precision
- **Long-format Documents**: 20+ pages → 1500-char chunks for comprehensive context
- **Generic Documents**: Personal files → 1000-char balanced chunks

**Processing Flow**:
1. **Upload** → PDF validation and security checks
2. **Classification** → Category determination via content analysis
3. **Processing** → Category-specific chunking via `app/utils/processors/`
4. **Embeddings** → MiniLM model via `app/services/embedding_service.py`
5. **Storage** → FAISS indices organized by category in `app/services/vector_store_service.py`

### Gmail Integration Architecture

**OAuth2 Flow** (`app/api/endpoints/gmail.py`):
- Google Cloud Console integration
- Secure token management and refresh
- Thread-aware email processing

**Email Processing** (`app/services/email/`):
- `email_classifier.py` - Business/Personal/Promotional/Transactional/Support classification
- `email_processor.py` - Thread context preservation
- `email_store.py` - Email-specific FAISS vector storage
- `email_query.py` - Semantic search across email content

### LLM Integration

**Local Processing** (`app/utils/llm.py`):
- Mistral 7B with llama-cpp-python
- Metal acceleration on macOS (configurable GPU layers)
- Context-aware response generation
- No external API dependencies

**Query Routing** (`app/services/query_router.py`):
- Intelligent routing to PDF documents, emails, or both
- Cross-content ranking and context assembly
- Source attribution and relevance scoring

### Database Design

**Multi-User Support**:
- User-isolated document and email storage
- Namespace-based vector index organization
- JWT-based access control

**Performance Optimizations**:
- Indexed queries for document and email retrieval
- Connection pooling with pre-ping validation
- Batch processing for embeddings

### Executable Build System

**PyInstaller Configuration** (`build_executable.py`):
- Single-file executable generation
- Progressive model downloading (separates binaries from AI models)
- Platform-specific optimizations (Windows/macOS/Linux)
- Static file inclusion and dependency bundling

**CI/CD Pipeline** (`.github/workflows/build-executables.yml`):
- Matrix builds for all platforms
- Automated release creation
- Asset uploading with platform-specific naming

## Key Configuration

### Environment Variables (.env)
```bash
# Core Settings
HOST=localhost
PORT=8000
DATABASE_URL=postgresql://user:pass@localhost:5432/db  # or SQLite for portable

# Gmail Integration (required for email features)
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-your_client_secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback

# LLM Configuration
LLM_MODEL_PATH=models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
USE_METAL=true  # macOS GPU acceleration
METAL_N_GPU_LAYERS=1

# Frontend Integration
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

### Model Files
- **LLM Model**: `models/mistral-7b-instruct-v0.1.Q4_K_M.gguf` (~4GB)
- **Embedding Model**: `models/all-MiniLM-L6-v2/` (sentence-transformers format)

### Data Organization
- **User Uploads**: `data/uploads/{user_id}/`
- **PDF Vectors**: `data/vector_db/{category}/user_{user_id}_doc_{filename}.{index|pkl}`
- **Email Vectors**: `data/vector_db/emails/user_{user_id}_email_{source}_{id}.{index|pkl}`

## Development Notes

### Testing Strategy
The codebase includes comprehensive testing at multiple levels:
- **Unit Tests**: `tests/` directory with pytest
- **Integration Tests**: `test_*.py` files for end-to-end functionality  
- **Feature Tests**: Specific scenario testing (email search, document classification, etc.)

### Database Flexibility
The application supports both PostgreSQL (development) and SQLite (portable executables) through:
- Dual database configuration in `app/db/`
- Runtime database type detection
- Optimized connection settings per database type

### Frontend Integration
Designed for separation with public frontend and private backend:
- CORS configuration for cross-origin requests
- JWT-based API authentication
- Health check endpoints for backend detection
- Static file serving for legacy frontend compatibility

### Privacy Architecture
All sensitive operations happen locally:
- LLM inference via local Mistral 7B model
- Document processing and embeddings generation
- Email content storage and indexing
- No external API calls for AI processing