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

# Download the LLM model (Mistral 7B)
python download_model.py

# Create admin user
python create_admin.py

# Setup database
python setup_db.py
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

# Migrate database
python migrate_db.py

# List all documents in database
python list_documents.py

# Reprocess all documents
python reprocess_documents.py
```

### Testing and Debugging
```bash
# Test vector store functionality
python test_vector_store.py

# Test new query processing
python test_new_query.py

# Test performance
python test_performance.py

# Debug search functionality
python debug_search.py
```

## Architecture Overview

### Core Components

**FastAPI Application** (`app/main.py`)
- Main entry point with API endpoints
- Handles CORS, static files, and exception handling
- Health check endpoint at `/api/health-check`

**Authentication System** (`app/api/endpoints/auth.py`)
- JWT-based authentication
- User management with bcrypt password hashing

**Document Processing Pipeline**
1. **Upload** (`app/api/endpoints/documents.py`) - File upload and validation
2. **Processing** (`app/utils/document_processor.py`) - Text extraction from PDFs, DOCX, TXT
3. **Chunking** - Documents split into semantic chunks
4. **Embedding** (`app/utils/embeddings.py`) - BGE-Small model for vector embeddings
5. **Storage** (`app/utils/vector_store.py`) - FAISS vector database with PostgreSQL/SQLite metadata

**Query Processing Pipeline**
1. **Query Classification** (`app/utils/llm.py:76`) - Categorizes queries as personal_data, general_knowledge, or mixed
2. **Document Type Detection** (`app/utils/vector_store.py:152`) - Identifies vacation, resume, expense, or prompt engineering queries
3. **Namespace Prioritization** (`app/utils/vector_store.py:185`) - Prioritizes relevant document types based on query
4. **Vector Search** (`app/utils/vector_store.py:271`) - Semantic similarity search across user documents
5. **Response Generation** (`app/utils/llm.py:282`) - Mistral 7B model generates answers from context

### Data Flow

**Document Upload → Processing → Vector Storage**
- User uploads document via `/api/documents/upload`
- Document processed into chunks with metadata
- Embeddings generated and stored in FAISS index
- Metadata stored in database with namespace: `user_{user_id}_doc_{sanitized_filename}`

**Query → Search → Generation → Response**
- User submits query via `/api/ask` or `/api/queries`
- Query classified and document types identified
- Vector search across prioritized namespaces
- Context chunks ranked by similarity score
- LLM generates response using retrieved context
- Query and answer logged to database

### Key Configuration

**Environment Variables** (see `app/core/config.py`)
- `LLM_MODEL_PATH`: Path to Mistral GGUF model file
- `USE_METAL`: Enable Metal acceleration on macOS (default: true)
- `METAL_N_GPU_LAYERS`: Number of GPU layers for Metal (default: 1)
- `MAX_FILE_SIZE`: Maximum upload file size (default: 5MB)
- `DATABASE_URL`: Database connection string

**AI Configuration** (`app/utils/ai_config.py`)
- Response validation and quality assessment
- Query classification keywords for different document types
- System prompts for different query types
- LLM generation parameters (temperature, top_p, etc.)

### Document Type Detection

The system automatically detects and prioritizes document types:
- **Vacation**: Keywords like "vacation", "travel", "trip", "thailand"
- **Resume/Skills**: Keywords like "resume", "cv", "skills", "experience"
- **Expenses**: Keywords like "expense", "cost", "budget", "monthly", specific months
- **Prompt Engineering**: Keywords like "prompt", "ai", "llm", "engineering"

### Vector Store Namespacing

Documents are stored in namespaced FAISS indices:
- Format: `user_{user_id}_doc_{sanitized_filename}`
- Each namespace has separate `.index` and `.pkl` files in `data/vector_db/`
- Supports per-user document isolation and targeted search

### Response Quality Control

**Query Classification** - Prevents hallucination by categorizing query intent
**Response Validation** - Checks for empty responses, errors, and hallucination indicators
**Context Filtering** - Limits context chunks (max 5) to prevent prompt overflow
**Score Thresholding** - Only uses high-quality vector matches (score > 0.2)

## Development Notes

- Server runs on `localhost:8000` by default, serves UI at `localhost:8000`
- Logs stored in `logs/app.log` with rotation (10MB max, 5 backups)
- Static files served from `static/` directory
- File uploads stored in `static/uploads/{user_id}/`
- Vector indices stored in `data/vector_db/`
- Models stored in `models/` directory (downloaded via `download_model.py`)