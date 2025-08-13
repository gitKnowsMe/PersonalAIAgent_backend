# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download the LLM model (Phi-2 by default, or use switch_model.py for Mistral)
python download_model.py

# Download embedding model (sentence-transformers)
python download_embedding_model.py

# Switch between AI models (Phi-2/Mistral)
python switch_model.py

# Create admin user
python create_admin.py

# Setup database
python setup_db.py

# Setup Gmail integration (requires .env with OAuth credentials)
python setup_gmail.py
```

### Running the Application
```bash
# Start the server (development mode with reload)
python main.py

# Alternative: Run with uvicorn directly
uvicorn app.main:app --host localhost --port 8000 --reload
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
- Static files served from `static/` directory (legacy frontend - replaced by v0 frontend)
- PDF uploads stored in user directories: `static/uploads/{user_id}/`
- Email content stored in: `static/emails/`
- Vector indices organized by type: `data/vector_db/{category}/` for PDFs, `data/vector_db/emails/` for emails
- Models stored in `models/` directory (downloaded via `download_model.py`)
- Comprehensive testing suite with email and PDF-specific test files
- Environment configuration uses `.env` file (copy from `.env.example`)
- Database uses SQLite for development (`personal_ai_agent.db`), PostgreSQL required for production
- No specific linting configuration - Python code follows standard conventions

### Development Workflow
1. **Setup**: Create virtual environment, install dependencies, download models
2. **Configuration**: Copy `.env.example` to `.env` and configure Gmail OAuth credentials
3. **Database**: Run `python setup_db.py` to initialize database tables
4. **Testing**: Use specific test scripts for individual components or `pytest` for unit tests
5. **Development**: Start server with `python main.py` or `uvicorn app.main:app --reload`

### Code Architecture Principles
- **Modular design**: Code structured for testability and maintainability
- **Config-driven**: Avoid hardcoded values, use environment variables and constants
- **Security-first**: Privacy-first development with local-first RAG processing
- **Type safety**: Use Pydantic models for data validation and serialization

### Current Content Support

**PDF Documents**: Advanced processing with category-specific strategies
- **Categories**: Financial (bank statements), Long-format (20+ pages), Generic (resumes, etc.)
- **Processing**: Adaptive chunking and indexing per document type

**Gmail Integration**: Full email processing pipeline  
- **Categories**: Business, Personal, Promotional, Transactional, Support
- **Processing**: Thread-aware context preservation with semantic search
- **OAuth2**: Secure Google account integration

**Unified Queries**: Cross-content search combining PDF documents and email messages for comprehensive responses

**Frontend**: Modern Vercel v0 Next.js frontend (primary interface)
- **Production Deployment**: v0 frontend on Vercel + backend API
- **CORS Configuration**: Environment-based origin management for cross-domain requests
- **API Client**: TypeScript client library for seamless frontend-backend communication
- **Authentication Flow**: JWT token management between frontend and backend

The system provides a complete personal knowledge base by intelligently processing and searching across both PDF documents and Gmail emails, with specialized handling for different content types to ensure optimal relevance and accuracy.

## Testing and Quality Assurance

- Run comprehensive test suite with: `python -m pytest tests/`
- Individual test files available for specific components
- No automated linting setup - follow Python PEP 8 conventions
- Manual testing scripts available for each major feature (email, PDF, classification)
- Error handling tests verify system resilience

## Frontend Architecture

**Primary Frontend**: Vercel v0 Next.js application (replaces legacy static frontend)
- **Repository**: https://github.com/gitKnowsMe/PersonalAIAgent
- **Technology Stack**: Next.js 15, TypeScript, Tailwind CSS, Radix UI
- **Key Components**: Landing page, chat interface, upload interface, sidebar
- **Design**: Modern dark theme with gradient backgrounds and animations

**Deployment Strategy**: Distributed architecture
- **Frontend**: Deploy v0 to Vercel (primary user interface)
- **Backend**: FastAPI server (local/cloud) providing comprehensive API
- **Communication**: CORS-enabled REST API calls with JWT authentication

**Production Configuration**: Update backend `.env` for production deployment:
```bash
# Database - PostgreSQL required for production
DATABASE_URL=postgresql://username:password@host:port/database_name

# CORS setup for Vercel frontend
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000
HOST=0.0.0.0  # Important for external access
DEBUG=false
```

**Integration Guide**: `FRONTEND_INTEGRATION.md` - Complete setup and deployment instructions

**API Client**: TypeScript client library handles:
- JWT authentication and token management
- Document upload and management APIs
- AI query processing and chat interface
- Gmail OAuth integration and email sync
- Error handling and loading states

## Important File Locations

- **Configuration**: `app/core/config.py` - Main settings and environment variables
- **Constants**: `app/core/constants.py` - Application-wide constants and defaults
- **Database Models**: `app/db/models.py` - SQLAlchemy database schema
- **API Routes**: `app/api/endpoints/` - All REST API endpoints
- **Document Processing**: `app/utils/processors/` - PDF and text processing logic
- **Email Services**: `app/services/email/` - Gmail integration and email processing
- **Vector Storage**: `app/services/vector_store_service.py` - FAISS vector database operations
- **Query Processing**: `app/services/query_router.py` - Routes queries to appropriate content sources
- **LLM Integration**: `app/utils/llm.py` - Local language model integration
- **Frontend Integration**: `FRONTEND_INTEGRATION.md` - Vercel v0 integration guide

### Key Configuration Files
- **Environment**: `.env` - Environment variables (copy from `.env.example`)
- **Dependencies**: `requirements.txt` - Python package dependencies
- **Development Rules**: `.cursor/rules/python.mdc` - Cursor IDE development guidelines
- **Database**: `personal_ai_agent.db` - SQLite database file (development)