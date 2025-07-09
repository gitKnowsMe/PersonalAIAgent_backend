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

# Debug document classification
python debug_chunks_detail.py
```

### Testing and Debugging
```bash
# Test vector store functionality
python test_vector_store.py

# Debug search functionality
python debug_search.py

# Test document classification
python -m pytest tests/test_document_classifier.py
```

## Architecture Overview - PDF Processing Focus

### Core Components

**FastAPI Application** (`app/main.py`)
- Main entry point with API endpoints for PDF processing
- Handles CORS, static files, and exception handling
- Health check endpoint at `/api/health-check`

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
4. **Embedding** (`app/utils/embeddings.py`) - MiniLM model for vector embeddings
5. **Storage** (`app/utils/vector_store.py`) - Category-organized FAISS vector database

**Document Classification System** (`app/utils/document_classifier.py`)
- **Financial Documents**: Bank statements, invoices, receipts with transaction patterns
- **Long-format Documents**: 50+ pages, research papers, reports, contracts
- **Generic Documents**: Resumes, letters, personal documents

**Query Processing Pipeline**
1. **Query Classification** (`app/utils/llm.py`) - Categorizes queries for optimal routing
2. **Category-Aware Search** (`app/utils/vector_store.py`) - Searches appropriate document categories
3. **Adaptive Retrieval** - Different strategies per document type:
   - **Financial**: Exact match + semantic search for transactions
   - **Long-format**: Deep semantic similarity with large context
   - **Generic**: Hybrid approach balancing precision and recall
4. **Response Generation** (`app/utils/llm.py`) - Mistral 7B generates category-appropriate responses

### Data Flow

**PDF Upload → Classification → Category-Specific Processing → Vector Storage**
- User uploads PDF via `/api/documents/upload`
- Document classified into financial, long-format, or generic category
- Category-specific processor handles chunking and metadata extraction
- Embeddings generated and stored in category-organized FAISS indices
- Metadata stored in database with namespace: `user_{user_id}_doc_{sanitized_filename}`
- Document type and processing status tracked in database

**Query → Category Detection → Targeted Search → Response**
- User submits query via `/api/ask` or `/api/queries`
- System determines which document categories are most relevant
- Targeted vector search across prioritized categories
- Category-specific context assembly and ranking
- LLM generates response optimized for document type
- Query and answer logged with category information

### Key Configuration

**Environment Variables** (see `app/core/config.py`)
- `LLM_MODEL_PATH`: Path to Mistral GGUF model file
- `USE_METAL`: Enable Metal acceleration on macOS (default: true)
- `METAL_N_GPU_LAYERS`: Number of GPU layers for Metal (default: 1)
- `MAX_FILE_SIZE`: Maximum PDF upload size (default: 10MB)
- `DATABASE_URL`: Database connection string

**Document Classification** (`app/utils/document_classifier.py`)
- Financial detection: Transaction patterns, dollar amounts, bank terminology
- Long-format detection: 50+ pages, academic structure, complex formatting
- Generic classification: Default for personal documents
- Category-specific processing metadata and chunking parameters

### Document Type Processing Strategies

**Financial Documents:**
- **Chunk Size**: 500 characters (small for precise transaction matching)
- **Overlap**: 50 characters (minimal to avoid duplicate transactions)
- **Strategy**: Structured parsing with exact match capabilities
- **Use Cases**: Expense tracking, transaction analysis, budget questions

**Long-format Documents (50+ pages):**
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

Documents are stored in category-organized FAISS indices:
- **Structure**: `data/vector_db/{category}/user_{user_id}_doc_{sanitized_filename}.{index|pkl}`
- **Categories**: `financial/`, `long_form/`, `generic/`
- **Benefits**: Faster category-specific searches, optimized indexing per document type
- **Isolation**: Per-user document separation within each category

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

- Server runs on `localhost:8000` by default, serves UI at `localhost:8000`
- Logs stored in `logs/app.log` with rotation (10MB max, 5 backups)
- Static files served from `static/` directory
- PDF uploads stored in category-organized directories: `static/uploads/{user_id}/{category}/`
- Vector indices organized by category: `data/vector_db/{category}/`
- Models stored in `models/` directory (downloaded via `download_model.py`)
- Document classification tests available in `tests/test_document_classifier.py`

### Current Document Support

**Primary Focus**: PDF documents with advanced processing
**Categories**: Financial (bank statements), Long-format (50+ pages), Generic (resumes, etc.)
**Processing**: Category-specific chunking and indexing strategies
**Future**: Notion integration for personal notes and knowledge management

The system is optimized for PDF document analysis with intelligent categorization to provide the most relevant and accurate responses based on document type and content structure.