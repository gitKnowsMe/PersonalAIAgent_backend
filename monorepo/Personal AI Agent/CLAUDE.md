# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **Personal AI Agent repository** containing both backend API and multiple frontend implementations. This repository provides:

- FastAPI REST API endpoints
- Local LLM processing (Mistral 7B)
- PDF document processing and classification
- Gmail integration via OAuth2
- Vector database for semantic search
- JWT authentication
- Cross-origin support for frontend integration
- Multiple frontend implementations (legacy static and modern Next.js)
- TypeScript API client library
- Static documentation site

## Development Commands

### Backend Setup and Installation
```bash
# Navigate to backend directory
cd backend/

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download the LLM model (Mistral 7B)
python download_model.py

# Download embedding model (sentence-transformers)
python download_embedding_model.py

# Create admin user
python create_admin.py

# Setup database
python setup_db.py

# Setup environment configuration
cp .env.development .env
# Edit .env with your Gmail OAuth credentials

# Setup Gmail integration (requires .env with OAuth credentials)
python setup_gmail.py
```

### Linting and Code Quality
```bash
# No specific linting configuration - Python code follows PEP 8 conventions
# Use standard Python linting tools:
python -m flake8 app/
python -m black app/ --check  # Code formatting check
python -m isort app/ --check-only  # Import sorting check

# TypeScript linting (frontend)
cd frontend/
npm run lint
npm run type-check
```

### Running the Backend Application
```bash
# Navigate to backend directory
cd backend/

# Start the backend with automatic setup and validation (RECOMMENDED)
python start_backend.py

# Alternative: Start manually (development mode with reload)
python main.py

# Alternative: Run with uvicorn directly
uvicorn app.main:app --host localhost --port 8000 --reload

# Test backend connection
python test_backend_connection.py

# The API will be available at:
# - Main API: http://localhost:8000/
# - Backend Status: http://localhost:8000/api/backend-status
# - Health check: http://localhost:8000/api/health-check  
# - API docs: http://localhost:8000/docs
# - OpenAPI spec: http://localhost:8000/openapi.json
```

### Database Operations
```bash
# Setup database tables
python setup_db.py

# Migrate database (general)
python migrate_db.py

# Migrate database with constraints
python migrate_db_constraints.py

# Migrate email-specific database
python migrate_email_db.py

# Add performance indexes for better query speed
python migrate_add_performance_indexes.py

# List all documents in database
python list_documents.py

# Debug document classification
python debug_chunks_detail.py
```

### Email Testing and Debugging
```bash
# Test email search functionality
python test_email_search.py

# Test API query functionality
python test_api_query.py

# Test direct email queries
python test_direct_query.py

# Test classification and source attribution
python test_classification_tags_fix.py
python test_source_attribution_fix.py

# Test mixed sources (PDFs + emails)
python test_mixed_sources.py
```

### General Testing and Debugging
```bash
# Test model loading
python test_model_loading.py
python test_mistral_model.py

# Test document classification
python -m pytest tests/test_document_classifier.py

# Test specific functionality
python test_bank_only.py
python test_direct_question.py
python test_hallucination_prevention.py

# Test error handling and configuration
python test_error_handling.py
python test_config_system.py

# Test performance optimizations
python test_performance_indexes.py

# Run all tests (if pytest is configured)
python -m pytest tests/

# Run specific test file or function
python -m pytest tests/test_document_classifier.py::test_financial_classification
```

### Documentation
```bash
# Start documentation development server
mkdocs serve

# Build static documentation
mkdocs build
```

### Environment Management
```bash
# Setup environment-specific configurations
cp .env.example .env.development
cp .env.example .env.production
cp .env.example .env.testing

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Deactivate virtual environment
deactivate
```

### Frontend Development Commands

#### Legacy Static Frontend (Fully Functional)
```bash
# The legacy frontend is served by the backend at /backend/static/
# No separate build process needed - files are served directly

# Start backend to serve static frontend
cd backend/
python main.py

# Access legacy frontend at:
# http://localhost:8000/ (main interface)
# http://localhost:8000/static/ (static files)
```

#### Modern Next.js Frontend (In Development)
```bash
# Navigate to frontend directory
cd frontend/

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# The Next.js frontend will be available at:
# http://localhost:3000/ (development)
# Backend API proxy configured automatically
```

#### TypeScript API Client
```bash
# Navigate to client directory
cd backend/client/

# Install dependencies
npm install

# Build TypeScript client
npm run build

# Run type checking
npm run type-check

# The client can be imported in any frontend project
```

#### Documentation Site
```bash
# The documentation site is built with MkDocs
# Static files are generated in /site/

# Serve documentation locally (if mkdocs is installed)
mkdocs serve

# Build static documentation
mkdocs build
```

## Architecture Overview - PDF & Email Processing

### Core Components

**FastAPI Application** (`app/main.py`)
- Main entry point with API endpoints for PDF and email processing
- Handles CORS, static files, and exception handling
- Health check endpoint at `/api/health-check`
- Modern lifespan management with startup/shutdown events

**Authentication System** (`app/api/endpoints/auth.py`)
- JWT-based authentication
- User management with bcrypt password hashing

**PDF Document Processing Pipeline**
1. **Upload** (`app/api/endpoints/documents.py`) - PDF file upload and validation
2. **Classification** (`app/utils/document_classifier.py`) - Categorize into financial, long-format, or generic
3. **Processing** (`app/utils/processors/`) - Specialized processing based on category:
   - **Financial Processor**: Small chunks (500 chars) for transaction data
   - **PDF Processor**: Standard extraction for long-format and generic documents
   - **Base Processor**: Adaptive chunking based on document type
4. **Embedding** (`app/services/embedding_service.py`) - MiniLM model for vector embeddings
5. **Storage** (`app/services/vector_store_service.py`) - Category-organized FAISS vector database

**Gmail Email Processing Pipeline**
1. **OAuth2 Authentication** (`app/api/endpoints/gmail.py`) - Google OAuth2 flow
2. **Email Ingestion** (`app/services/email/email_ingestion.py`) - Fetch emails via Gmail API
3. **Email Classification** (`app/services/email/email_classifier.py`) - Categorize into business, personal, promotional, transactional, support
4. **Thread Processing** (`app/services/email/email_processor.py`) - Process email threads with context preservation
5. **Vector Storage** (`app/services/email/email_store.py`) - Email-specific FAISS indices
6. **Email Search** (`app/services/email/email_query.py`) - Semantic search across email content

**Document Classification System** (`app/utils/document_classifier.py`)
- **Financial Documents**: Bank statements, invoices, receipts with transaction patterns
- **Long-format Documents**: 20+ pages, research papers, reports, contracts
- **Generic Documents**: Resumes, letters, personal documents

**Email Classification System** (`app/services/email/email_classifier.py`)
- **Business**: Meeting invites, project updates, work communications
- **Personal**: Family/friend emails, personal communications  
- **Promotional**: Marketing emails, newsletters, deals
- **Transactional**: Receipts, confirmations, account notifications
- **Support**: Customer service, technical support communications

**Unified Query Processing Pipeline**
1. **Query Routing** (`app/services/query_router.py`) - Routes queries to appropriate content sources (PDFs, emails, or both)
2. **Category-Aware Search** (`app/services/vector_store_service.py`) - Searches appropriate document/email categories
3. **Cross-Content Retrieval** - Different strategies per content type:
   - **PDF Financial**: Exact match + semantic search for transactions
   - **PDF Long-format**: Deep semantic similarity with large context
   - **PDF Generic**: Hybrid approach balancing precision and recall
   - **Email Business/Personal**: Thread-aware context with semantic search
   - **Email Promotional/Transactional**: Content-specific indexing
4. **Response Generation** (`app/utils/llm.py`) - Mistral 7B generates unified responses from PDF and email sources

### Data Flow

**PDF Upload → Classification → Category-Specific Processing → Vector Storage**
- User uploads PDF via `/api/documents/upload`
- Document classified into financial, long-format, or generic category
- Category-specific processor handles chunking and metadata extraction
- Embeddings generated and stored in category-organized FAISS indices
- Metadata stored in database with namespace: `user_{user_id}_doc_{sanitized_filename}`
- Document type and processing status tracked in database

**Gmail OAuth → Email Sync → Classification → Thread Processing → Vector Storage**
- User initiates OAuth flow via `/api/gmail/auth`
- Gmail API fetches emails in batches via `/api/gmail/sync`
- Emails classified into business, personal, promotional, transactional, support categories
- Thread-aware processing preserves conversation context
- Embeddings generated and stored in email-specific FAISS indices
- Email metadata stored with namespace: `user_{user_id}_email_{email_source}_{email_id}`

**Query → Content Source Routing → Multi-Modal Search → Unified Response**
- User submits query via `/api/queries/` 
- Query router determines relevance to PDFs, emails, or both
- Parallel vector search across relevant document and email categories
- Cross-content ranking and context assembly
- LLM generates unified response citing both PDF and email sources
- Query and sources logged with category attribution

### Key Configuration

**Environment Variables** (see `app/core/config.py`)
- `LLM_MODEL_PATH`: Path to Mistral GGUF model file
- `USE_METAL`: Enable Metal acceleration on macOS (default: true)
- `METAL_N_GPU_LAYERS`: Number of GPU layers for Metal (default: 1)
- `MAX_FILE_SIZE`: Maximum PDF upload size (default: 10MB)
- `DATABASE_URL`: Database connection string
- `GMAIL_CLIENT_ID`: Google OAuth2 client ID (required for Gmail integration)
- `GMAIL_CLIENT_SECRET`: Google OAuth2 client secret (required for Gmail integration)
- `GMAIL_REDIRECT_URI`: OAuth2 callback URL (default: http://localhost:8000/api/gmail/callback)
- `GMAIL_MAX_EMAILS_PER_SYNC`: Maximum emails to sync per request (default: 1000)
- `GMAIL_DEFAULT_SYNC_LIMIT`: Default number of emails to sync (default: 100)

**Document Classification** (`app/utils/document_classifier.py`)
- Financial detection: Transaction patterns, dollar amounts, bank terminology
- Long-format detection: 20+ pages, academic structure, complex formatting
- Generic classification: Default for personal documents
- Category-specific processing metadata and chunking parameters

### Document Type Processing Strategies

**Financial Documents:**
- **Chunk Size**: 500 characters (small for precise transaction matching)
- **Overlap**: 50 characters (minimal to avoid duplicate transactions)
- **Strategy**: Structured parsing with exact match capabilities
- **Use Cases**: Expense tracking, transaction analysis, budget questions

**Long-format Documents (20+ pages):**
- **Chunk Size**: 1500 characters (large for comprehensive context)
- **Overlap**: 300 characters (significant for maintaining narrative flow)
- **Strategy**: Semantic analysis with deep understanding
- **Use Cases**: Research queries, document analysis, comprehensive insights

**Generic Documents:**
- **Chunk Size**: 1000 characters (balanced approach)
- **Overlap**: 200 characters (moderate for good context preservation)
- **Strategy**: Hybrid matching combining precision and recall
- **Use Cases**: Resume queries, personal document search, general information

### Vector Store Organization

**PDF Documents** are stored in category-organized FAISS indices:
- **Structure**: `data/vector_db/{category}/user_{user_id}_doc_{sanitized_filename}.{index|pkl}`
- **Categories**: `financial/`, `long_form/`, `generic/`
- **Benefits**: Faster category-specific searches, optimized indexing per document type
- **Isolation**: Per-user document separation within each category

**Email Messages** are stored in separate FAISS indices:
- **Structure**: `data/vector_db/emails/user_{user_id}_email_{email_source}_{email_id}.{index|pkl}`
- **Email Storage**: `static/emails/` for email content and attachments  
- **Thread Context**: Email threads maintain conversation history and context
- **Cross-Reference**: Emails can reference and be searched alongside PDF content

### Response Quality Control

**Category-Aware Processing** - Different quality thresholds and processing for each document type
**Document Classification** - Automatic categorization prevents inappropriate processing
**Adaptive Context** - Category-specific context limits and relevance scoring
**Processing Validation** - Type-specific validation rules and error handling

### Future Notion Integration

**Planned Features** (Phase 3 - Q2 2025):
- **Notion API Integration**: Sync personal notes and knowledge base
- **Unified Search**: Combined PDF + Notion content queries
- **Cross-Reference**: Link PDF insights with personal Notion notes
- **Smart Organization**: Automatic categorization of notes alongside PDF documents
- **Enhanced Context**: Use personal notes to provide richer context for PDF queries

**Technical Architecture**:
- Notion content will be processed similar to generic documents
- Separate vector indices for Notion content with cross-reference capabilities
- Intelligent routing between PDF documents and Notion content based on query intent
- Unified namespace system supporting both PDF and Notion content

## Development Notes

- Backend server runs on `localhost:8000` by default, API endpoints at `localhost:8000/api/*`
- Logs stored in `logs/app.log` with rotation (10MB max, 5 backups)
- **Multiple frontend options**: Legacy static frontend (production-ready) and modern Next.js frontend (in development)
- PDF uploads stored in user directories: `data/uploads/{user_id}/`
- Email content stored in: `data/emails/`
- Vector indices organized by type: `data/vector_db/{category}/` for PDFs, `data/vector_db/emails/` for emails
- Models stored in `models/` directory (downloaded via `download_model.py`)
- Comprehensive testing suite with email and PDF-specific test files
- Environment configuration uses `.env` file (copy from `.env.development` or `.env.production`)
- Database uses PostgreSQL for all environments (development and production)
- No specific linting configuration - Python code follows standard conventions

### Development Workflow

#### Backend Development
1. **Setup**: Create virtual environment, install dependencies, download models
2. **Configuration**: Copy `.env.development` to `.env` and configure Gmail OAuth credentials
3. **Database**: Run `python setup_db.py` to initialize database tables
4. **Testing**: Use specific test scripts for individual components or `pytest` for unit tests
5. **Development**: Start server with `python main.py` or `uvicorn app.main:app --reload`

#### Frontend Development
1. **Legacy Frontend**: Already functional, served by backend at `localhost:8000`
2. **Modern Frontend**: 
   - `cd frontend/` and run `npm install` then `npm run dev`
   - Implement React components in `frontend/src/`
   - Use TypeScript API client from `backend/client/api-client.ts`
3. **API Client**: Build with `npm run build` in `backend/client/`
4. **Documentation**: Generate with `mkdocs build` if needed

#### Key Development Notes
- **Single Test Commands**: Use `python -m pytest tests/test_document_classifier.py::test_financial_classification` for specific tests
- **Environment Variables**: All configuration is in `app/core/config.py` with constants in `app/core/constants.py`
- **Database**: PostgreSQL for all environments with proper connection pooling
- **Model Loading**: Models are downloaded to `models/` directory, loaded via `app/utils/llm.py`
- **Vector Storage**: FAISS indices organized by category in `data/vector_db/`

### Multi-Frontend Architecture

This repository contains **both backend API and multiple frontend implementations**.

**Backend (FastAPI)**:
- FastAPI REST API
- Local LLM processing
- Vector database
- Gmail OAuth integration
- JWT authentication
- CORS-enabled for frontend integration
- Serves legacy static frontend

**Frontend Implementations**:

1. **Legacy Static Frontend** (`/backend/static/`):
   - Fully functional HTML/CSS/JavaScript application
   - Bootstrap 5 styling with custom CSS
   - Complete feature set: auth, PDF upload, Gmail integration, queries
   - Served directly by FastAPI backend
   - Production-ready and actively maintained

2. **Modern Next.js Frontend** (`/frontend/`):
   - Next.js 14 with React 18 and TypeScript
   - Tailwind CSS and Radix UI components
   - Configured for Vercel deployment
   - API proxy to backend configured
   - **Status**: Structure ready, components need implementation

3. **TypeScript API Client** (`/backend/client/`):
   - Complete type-safe API wrapper
   - JWT token management
   - Error handling and retries
   - Reusable across any frontend implementation

**Deployment Strategies**:
- **Development**: Backend serves legacy frontend at `localhost:8000`, Next.js at `localhost:3000`
- **Production Option 1**: Monolithic - Backend serves legacy frontend
- **Production Option 2**: Distributed - Next.js on Vercel, backend on server/VPS
- **CORS**: Configure `ALLOWED_ORIGINS` in `.env` for cross-origin requests

### Code Architecture Principles
- **Modular design**: Code structured for testability and maintainability
- **Config-driven**: Avoid hardcoded values, use environment variables and constants
- **Security-first**: Privacy-first development with local-first RAG processing
- **Type safety**: Use Pydantic models for data validation and serialization

### Cursor IDE Development Rules
The project includes development guidelines in `.cursor/rules/python.mdc`:
- Ensure all code is modular, secure, and config-driven
- Follow architecture-specific best practices (FastAPI, PostgreSQL, local-first RAG)
- Avoid hardcoding values - use environment variables and constants
- Structure code for testability and maintainability
- Support privacy-first development principles

### Current Content Support

**PDF Documents**: Advanced processing with category-specific strategies
- **Categories**: Financial (bank statements), Long-format (20+ pages), Generic (resumes, etc.)
- **Processing**: Adaptive chunking and indexing per document type

**Gmail Integration**: Full email processing pipeline  
- **Categories**: Business, Personal, Promotional, Transactional, Support
- **Processing**: Thread-aware context preservation with semantic search
- **OAuth2**: Secure Google account integration

**Unified Queries**: Cross-content search combining PDF documents and email messages for comprehensive responses

**Frontend Options**: Multiple implementations for different deployment strategies
- **Legacy Static**: Production-ready HTML/CSS/JS frontend served by backend
- **Modern Next.js**: In-development React frontend for Vercel deployment
- **CORS Configuration**: Environment-based origin management for cross-domain requests
- **API Client**: TypeScript client library for seamless frontend-backend communication
- **Authentication Flow**: JWT token management between frontend and backend

The system provides a complete personal knowledge base by intelligently processing and searching across both PDF documents and Gmail emails, with specialized handling for different content types to ensure optimal relevance and accuracy.

## Frontend Development Status

### Current State
- **✅ Legacy Static Frontend**: Fully functional with all features implemented
- **⚠️ Modern Next.js Frontend**: Configuration complete, React components need implementation
- **✅ TypeScript API Client**: Complete and ready for frontend integration
- **✅ Documentation Site**: Generated and available

### Development Priority
1. **Immediate**: Legacy frontend is production-ready and can be deployed
2. **Future**: Modern Next.js frontend for improved UX and development experience
3. **Ongoing**: API client maintenance and documentation updates

### Frontend Choice Guidelines
- **Use Legacy Frontend**: For immediate deployment, simple maintenance, no build process
- **Use Modern Frontend**: For advanced UI/UX, better developer experience, modern tooling
- **Use API Client**: For any custom frontend implementation or third-party integrations

## Testing and Quality Assurance

### Backend Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_document_classifier.py

# Run specific test function
python -m pytest tests/test_document_classifier.py::test_financial_classification

# Manual testing scripts for specific features
python test_email_search.py
python test_api_query.py
python test_model_loading.py
python test_backend_connection.py
```

### Frontend Testing
```bash
# TypeScript API client testing
cd backend/client/
npm run type-check

# Next.js frontend testing
cd frontend/
npm run lint
npm run type-check
```

### Quality Assurance
- No automated linting setup - follow Python PEP 8 conventions
- Manual testing scripts available for each major feature (email, PDF, classification)
- Error handling tests verify system resilience
- Configuration validation happens at startup via `settings.validate_gmail_config()`

## Frontend Architecture Details

### Legacy Static Frontend (`/backend/static/`)
**Status**: ✅ **Production Ready**
- **Technology**: Vanilla HTML/CSS/JavaScript with Bootstrap 5
- **Features**: Complete application with all backend integrations
- **Components**: Authentication, PDF upload, Gmail sync, query interface, performance monitoring
- **Deployment**: Served directly by FastAPI backend
- **Advantages**: No build process, immediate deployment, proven stability

### Modern Next.js Frontend (`/frontend/`)
**Status**: ⚠️ **In Development**
- **Technology Stack**: Next.js 14, React 18, TypeScript, Tailwind CSS, Radix UI
- **Configuration**: Complete with API proxy, Vercel deployment, styling setup
- **Missing**: Actual React components (`.tsx` files)
- **Purpose**: Modern UI/UX with improved performance and developer experience
- **Deployment**: Configured for Vercel with backend API integration

### TypeScript API Client (`/backend/client/`)
**Status**: ✅ **Complete**
- **Purpose**: Reusable API wrapper for any frontend implementation
- **Features**: Type-safe API calls, JWT management, error handling, file uploads
- **Usage**: Can be imported by Next.js frontend or any other JavaScript framework
- **Documentation**: Comprehensive TypeScript definitions and examples

### Static Documentation Site (`/site/`)
**Status**: ✅ **Generated**
- **Technology**: MkDocs generated static HTML
- **Content**: API documentation, user guides, development instructions
- **Deployment**: Can be served statically or via backend

**Production Configuration**: Update backend `.env` for production deployment:
```bash
# Database - PostgreSQL required for production
DATABASE_URL=postgresql://username:password@host:port/database_name

# CORS setup for modern frontend
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000
HOST=0.0.0.0  # Important for external access
DEBUG=false
```

## Important File Locations

### Backend Files
- **Configuration**: `app/core/config.py` - Main settings and environment variables
- **Constants**: `app/core/constants.py` - Application-wide constants and defaults
- **Database Models**: `app/db/models.py` - SQLAlchemy database schema
- **API Routes**: `app/api/endpoints/` - All REST API endpoints
- **Document Processing**: `app/utils/processors/` - PDF and text processing logic
- **Email Services**: `app/services/email/` - Gmail integration and email processing
- **Vector Storage**: `app/services/vector_store_service.py` - FAISS vector database operations
- **Query Processing**: `app/services/query_router.py` - Routes queries to appropriate content sources
- **LLM Integration**: `app/utils/llm.py` - Local language model integration

### Frontend Files
- **Legacy Static Frontend**: `backend/static/` - Production-ready HTML/CSS/JS application
  - `backend/static/index.html` - Main application entry point
  - `backend/static/js/app.js` - Application JavaScript (1,200+ lines)
  - `backend/static/css/style.css` - Custom styling and Bootstrap overrides
- **Modern Next.js Frontend**: `frontend/` - Next.js application structure
  - `frontend/package.json` - Next.js dependencies and scripts
  - `frontend/next.config.js` - Next.js configuration with API proxy
  - `frontend/tailwind.config.js` - Tailwind CSS configuration
  - `frontend/src/` - Source directory (components to be implemented)
- **TypeScript API Client**: `backend/client/` - Reusable API wrapper
  - `backend/client/api-client.ts` - Complete TypeScript API client
  - `backend/client/package.json` - TypeScript dependencies
- **Documentation Site**: `site/` - Static documentation files
  - Generated by MkDocs from documentation sources

### Configuration Files
- **Environment**: `.env` - Environment variables (copy from `.env.example`)
- **Backend Dependencies**: `requirements.txt` - Python package dependencies
- **Frontend Dependencies**: `frontend/package.json` - Next.js dependencies
- **API Client Dependencies**: `backend/client/package.json` - TypeScript dependencies
- **Development Rules**: `.cursor/rules/python.mdc` - Cursor IDE development guidelines
- **Database**: PostgreSQL database with comprehensive schema and indexing
- **Integration Guide**: `FRONTEND_INTEGRATION.md` - Complete setup guide for both frontend options

## Key Dependencies and Versions

### Backend (Python)
- **FastAPI**: 0.115.12 - Web framework
- **SQLAlchemy**: 2.0.41 - Database ORM
- **Pydantic**: 2.11.5 - Data validation
- **LangChain**: 0.3.25 - LLM integration
- **FAISS**: 1.11.0 - Vector similarity search
- **llama-cpp-python**: 0.3.9 - Local LLM inference
- **sentence-transformers**: 4.1.0 - Text embeddings
- **Google APIs**: Latest - Gmail integration

### Frontend (TypeScript/Node.js)
- **Next.js**: 14.0.3 - React framework
- **React**: 18.2.0 - UI library
- **TypeScript**: 5.2.0 - Type safety
- **Tailwind CSS**: 3.3.0 - Styling
- **Radix UI**: Latest - UI components