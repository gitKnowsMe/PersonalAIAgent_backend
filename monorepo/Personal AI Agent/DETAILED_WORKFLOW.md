# Personal AI Agent: Deep-Dive Workflow Documentation

## Table of Contents
1. [PDF Ingestion, Processing, and Retrieval Workflow](#pdf-ingestion-processing-and-retrieval-workflow)
    - [1.1 Upload & Ingestion](#11-upload--ingestion)
    - [1.2 Chunking & Embedding](#12-chunking--embedding)
    - [1.3 Storage & Indexing](#13-storage--indexing)
    - [1.4 Retrieval & Querying](#14-retrieval--querying)
2. [Email Ingestion, Processing, and Retrieval Workflow](#email-ingestion-processing-and-retrieval-workflow)
    - [2.1 Gmail OAuth & Sync](#21-gmail-oauth--sync)
    - [2.2 Email Parsing & Classification](#22-email-parsing--classification)
    - [2.3 Email Embedding & Indexing](#23-email-embedding--indexing)
    - [2.4 Email Query & Retrieval](#24-email-query--retrieval)
3. [Global Variables, Model Config, and Secrets](#global-variables-model-config-and-secrets)
    - [3.1 Global Variables & Constants](#31-global-variables--constants)
    - [3.2 LLM Model, Embedding Model, and Parameters](#32-llm-model-embedding-model-and-parameters)
    - [3.3 Secrets & Credentials Management](#33-secrets--credentials-management)

---

## PDF Ingestion, Processing, and Retrieval Workflow

### 1.1 Upload & Ingestion
- **Frontend**: User uploads a PDF via the web UI (`static/index.html`, `static/js/app.js`).
- **API Endpoint**: `/api/documents` (see `app/api/endpoints/documents.py`)
- **Backend Flow**:
    1. File is saved to `static/uploads/`.
    2. Metadata (title, description, file path, owner) is stored in the `Document` table (`app/db/models.py`).
    3. Triggers document processing pipeline.

### 1.2 Chunking & Embedding
- **Chunking**:
    - Handled by `app/utils/document_processor.py` and `app/utils/processors/pdf_processor.py`.
    - PDF is split into text chunks (pages, paragraphs, or semantic units).
    - Each chunk is assigned metadata: `document_id`, `chunk_index`, `section_header`, etc.
- **Embedding**:
    - Uses the embedding model (see [3.2](#32-llm-model-embedding-model-and-parameters)).
    - Embeddings are generated for each chunk using `app/services/embedding_service.py`.
    - Embedding parameters (model, dimension) are set in `app/core/config.py` and `app/core/constants.py`.

### 1.3 Storage & Indexing
- **Vector Store**:
    - Chunks and embeddings are stored in FAISS indices (`app/services/vector_store_service.py`).
    - Index files are saved in `data/vector_db/` (organized by document type/category).
    - Metadata for each chunk is stored in parallel `.pkl` files.
- **Database**:
    - Document metadata is stored in the `Document` table.
    - Chunk-level metadata is not stored in SQL, but in the vector store's docmap.

### 1.4 Retrieval & Querying
- **Query Endpoint**: `/api/queries` (see `app/api/endpoints/queries.py`)
- **Query Flow**:
    1. User submits a question via the UI.
    2. Backend determines source selection (documents, emails, or both) using `app/services/source_service.py`.
    3. For documents:
        - Calls `search_similar_chunks` in `vector_store_service.py` to find top-k relevant chunks (semantic search).
        - Chunks are scored and sorted by similarity.
    4. Top chunks are passed to the LLM for answer generation (`app/utils/llm.py`).
    5. The answer and source attribution are returned to the frontend.

---

## Email Ingestion, Processing, and Retrieval Workflow

### 2.1 Gmail OAuth & Sync
- **Frontend**: User connects Gmail via OAuth (UI in `static/index.html`, logic in `static/js/app.js`).
- **API Endpoints**: `/api/gmail/auth`, `/api/gmail/callback`, `/api/gmail/sync` (`app/api/endpoints/gmail.py`)
- **Backend Flow**:
    1. OAuth2 flow handled by `GmailService` (`app/services/gmail_service.py`).
    2. Access/refresh tokens are encrypted and stored in the `EmailAccount` table.
    3. On sync, emails are fetched using the Gmail API (Google client libraries).
    4. Raw emails are stored in the `Email` table (`app/db/models.py`).

### 2.2 Email Parsing & Classification
- **Parsing**:
    - Email bodies, headers, and attachments are parsed in `gmail_service.py` and `app/services/email_processor.py`.
    - Extracts subject, sender, recipients, date, body, and labels.
- **Classification**:
    - Email type (business, personal, transactional, etc.) is determined by `email_processor.classify_email_type()`.
    - Classification tags are stored in the `Email` table and chunk metadata.

### 2.3 Email Embedding & Indexing
- **Chunking**:
    - Emails are split into chunks (body, subject, etc.) in `email_processor.py`.
    - Each chunk is assigned metadata: `email_id`, `email_type`, `user_id`, etc.
- **Embedding**:
    - Embeddings are generated for each chunk using the same embedding model as documents.
    - Stored in FAISS indices under `data/email_vectors/` (see `vector_store_service.py`).
    - Metadata includes `content_type: 'email'` for source attribution.

### 2.4 Email Query & Retrieval
- **Query Endpoint**: `/api/queries` (see `app/api/endpoints/queries.py`)
- **Query Flow**:
    1. User submits a question, selects "All Emails" or a specific email type.
    2. Backend uses `source_service.py` to determine email search parameters.
    3. Calls `vector_store_manager.search_emails()` to find top-k relevant email chunks.
    4. Chunks are passed to the LLM for answer generation.
    5. The answer and source attribution are returned to the frontend.

---

## Global Variables, Model Config, and Secrets

### 3.1 Global Variables & Constants
- **Location**: `app/core/constants.py`, `app/core/config.py`
- **Examples**:
    - `EMBEDDING_MODEL_NAME`, `EMBEDDING_DIM`
    - `LLM_MODEL_NAME`, `LLM_TOP_P`, `LLM_TOP_K`, `LLM_TEMPERATURE`
    - `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `SECRET_KEY`, etc.
- **Usage**: Imported throughout the codebase for consistent config.

### 3.2 LLM Model, Embedding Model, and Parameters
- **LLM Model**:
    - Defined in `app/core/config.py` and `app/core/constants.py` (e.g., `LLM_MODEL_NAME`)
    - Used in `app/utils/llm.py` for answer generation.
    - Parameters:
        - `top_p`, `top_k`, `temperature` (sampling/decoding params)
        - Set in config/constants, can be overridden per request in some cases.
- **Embedding Model**:
    - Defined in `app/core/config.py` and `app/core/constants.py` (e.g., `EMBEDDING_MODEL_NAME`)
    - Used in `app/services/embedding_service.py` for chunk embedding.

### 3.3 Secrets & Credentials Management
- **Gmail OAuth**:
    - Client ID/Secret in `gmail_credentials.json` and/or `app/core/config.py` (loaded via env vars or config).
- **App Secrets**:
    - `SECRET_KEY` for JWT in `app/core/config.py` (from env or config file).
- **Other**:
    - API keys, DB credentials, etc., are loaded from environment variables or config files, never hardcoded in source.
    - Sensitive files: `gmail_credentials.json`, `.env`, `app/services/client_secret_*.json`

---

## References (Key Files/Modules)
- `app/api/endpoints/queries.py` — Query routing, retrieval, and answer generation
- `app/services/vector_store_service.py` — Vector DB, chunk search, and storage
- `app/services/embedding_service.py` — Embedding model logic
- `app/services/gmail_service.py` — Gmail OAuth, sync, and email fetch
- `app/services/email_processor.py` — Email parsing, chunking, and classification
- `app/utils/document_processor.py` — PDF/document chunking
- `app/core/config.py`, `app/core/constants.py` — Global config, model params, secrets
- `app/db/models.py` — SQLAlchemy models for Document, Email, User, etc.
- `static/js/app.js` — Frontend logic for upload, query, and display

---

*This document provides a deep technical workflow for both PDF and email features, including all major data flows, model/config locations, and secrets management. For further details, see the referenced files and modules in the codebase.* 