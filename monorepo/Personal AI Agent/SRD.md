# Personal AI Agent - Software Requirements Document

**Version:** 4.0  
**Date:** July 2025  
**Status:** Active Development - Gmail Integration Phase  

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [API Specifications](#api-specifications)
5. [Security Requirements](#security-requirements)
6. [Performance Requirements](#performance-requirements)
7. [Data Management](#data-management)
8. [User Interface](#user-interface)
9. [Deployment & Infrastructure](#deployment--infrastructure)
10. [Quality Assurance](#quality-assurance)
11. [Roadmap](#roadmap)

---

## 🎯 Project Overview

### Project Title
**Personal AI Agent Backend API (PDF-Focused RAG System)**

### Mission Statement
To create a sophisticated, privacy-first AI assistant backend that enables users to interact with their PDF documents and Gmail emails through natural language queries, utilizing advanced document categorization and specialized processing techniques for different content types. The system provides a robust API for frontend integration with hybrid deployment architecture.

### Key Value Propositions
- **100% Privacy**: All processing occurs on your server with no external API calls (except Gmail OAuth)
- **PDF + Gmail Integration**: Unified processing for PDF documents and Gmail emails
- **Smart Content Classification**: Automatic categorization for documents and emails
- **Adaptive Processing**: Custom chunking, pagination, and indexing strategies per content type
- **Thread-Aware Email Processing**: Conversation context preservation and intelligent search
- **Cross-Platform Queries**: Search across PDFs and emails with unified results
- **Production-Ready API**: Scalable, secure, and maintainable backend architecture
- **Hybrid Deployment**: Backend-only repository for flexible frontend integration
- **TypeScript Client**: Full-featured API client for seamless frontend development

### Document Categories & Processing Strategy

#### 📊 Financial Documents (Bank Statements, Invoices, Receipts)
- **Characteristics**: Transaction-based, structured data, tables, financial patterns
- **Processing**: Small chunks (500 chars), minimal overlap (50 chars), structured parsing
- **Use Cases**: Expense tracking, financial analysis, transaction queries

#### 📚 Long-Format Documents (Research Papers, Reports, Contracts)
- **Characteristics**: 20+ pages, narrative content, complex structure
- **Processing**: Large chunks (1500 chars), significant overlap (300 chars), semantic analysis
- **Use Cases**: Research queries, detailed analysis, comprehensive document understanding

#### 📄 Generic Documents (Resumes, Letters, Notes)
- **Characteristics**: Personal documents, varied formats, moderate length
- **Processing**: Balanced chunks (1000 chars), moderate overlap (200 chars), hybrid approach
- **Use Cases**: Personal information retrieval, skill queries, general document search

### Email Categories & Processing Strategy

#### 💼 Business Emails (Work Communications, Meeting Invites)
- **Characteristics**: Formal language, project updates, meeting invitations, work-related topics
- **Processing**: Thread-aware chunks (800 chars), context preservation, metadata-rich indexing
- **Use Cases**: Project tracking, meeting summaries, work communication analysis

#### 👨‍👩‍👧‍👦 Personal Emails (Family, Friends, Personal)
- **Characteristics**: Casual language, personal topics, family communications
- **Processing**: Conversation chunks (600 chars), relationship context, privacy-focused
- **Use Cases**: Personal relationship management, event planning, family communication

#### 🛍️ Promotional Emails (Marketing, Newsletters, Deals)
- **Characteristics**: Marketing content, promotional offers, newsletters
- **Processing**: Content-focused chunks (400 chars), offer extraction, temporal relevance
- **Use Cases**: Deal tracking, newsletter summaries, promotional analysis

#### 🧾 Transactional Emails (Receipts, Confirmations, Alerts)
- **Characteristics**: Order confirmations, receipts, account notifications
- **Processing**: Structured chunks (300 chars), data extraction, precise matching
- **Use Cases**: Purchase tracking, account monitoring, transaction analysis

#### 🔧 Support Emails (Customer Service, Technical Support)
- **Characteristics**: Problem resolution, technical discussions, support tickets
- **Processing**: Issue-focused chunks (700 chars), solution tracking, context linking
- **Use Cases**: Support history, solution lookup, technical issue tracking

### Target Users
- Privacy-conscious individuals managing PDF documents and email communications
- Professionals requiring secure document and email analysis
- Researchers working with academic papers and professional communications
- Finance professionals analyzing statements, reports, and financial emails
- Organizations needing on-premises PDF and email processing solutions
- Individuals seeking unified search across documents and email history

---

## 🏗️ System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Web Interface]
        API_CLIENT[API Client]
    end
    
    subgraph "API Layer"
        FASTAPI[FastAPI Application]
        AUTH[Authentication Service]
        MIDDLEWARE[Logging Middleware]
    end
    
    subgraph "Business Logic Layer"
        QUERY_ROUTER[Query Router]
        DOC_PROCESSOR[Document Processor]
        DOC_CLASSIFIER[Document Classifier]
        EMAIL_PROCESSOR[Email Processor]
        EMAIL_CLASSIFIER[Email Classifier]
        AI_CONFIG[AI Configuration Service]
        VECTOR_SERVICE[Vector Store Service]
        GMAIL_SERVICE[Gmail Service]
    end
    
    subgraph "AI Processing Layer"
        LLM[Local LLM (Mistral 7B)]
        EMBEDDINGS[MiniLM Embeddings]
        PDF_PROCESSOR[PDF Content Extractor]
        CATEGORY_ANALYZER[Category-Specific Analyzer]
    end
    
    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        FAISS[(FAISS Vector DB)]
        PDF_FILES[(PDF File Storage)]
        EMAIL_STORAGE[(Email Storage)]
    end
    
    subgraph "External Integration"
        GMAIL_API[Gmail API]
        OAUTH2[OAuth2 Authentication]
    end
    
    subgraph "Future Integration"
        NOTION[Notion API Integration]
        NOTES[Personal Notes Sync]
    end
    
    UI --> FASTAPI
    API_CLIENT --> FASTAPI
    FASTAPI --> AUTH
    FASTAPI --> MIDDLEWARE
    FASTAPI --> QUERY_ROUTER
    FASTAPI --> DOC_PROCESSOR
    FASTAPI --> GMAIL_SERVICE
    DOC_PROCESSOR --> DOC_CLASSIFIER
    GMAIL_SERVICE --> EMAIL_PROCESSOR
    EMAIL_PROCESSOR --> EMAIL_CLASSIFIER
    QUERY_ROUTER --> AI_CONFIG
    QUERY_ROUTER --> VECTOR_SERVICE
    DOC_PROCESSOR --> PDF_PROCESSOR
    DOC_CLASSIFIER --> CATEGORY_ANALYZER
    EMAIL_CLASSIFIER --> CATEGORY_ANALYZER
    VECTOR_SERVICE --> LLM
    VECTOR_SERVICE --> EMBEDDINGS
    VECTOR_SERVICE --> FAISS
    AUTH --> POSTGRES
    DOC_PROCESSOR --> PDF_FILES
    EMAIL_PROCESSOR --> EMAIL_STORAGE
    GMAIL_SERVICE --> GMAIL_API
    GMAIL_SERVICE --> OAUTH2
    QUERY_ROUTER --> POSTGRES
    
    %% Future integrations (dashed lines)
    NOTION -.-> NOTES
    NOTES -.-> VECTOR_SERVICE
```

### Design Patterns
- **Service-Oriented Architecture**: Clean separation of concerns
- **Factory Pattern**: Document processor registry with PDF specialization
- **Strategy Pattern**: Category-specific processing strategies
- **Repository Pattern**: Data access abstraction
- **Dependency Injection**: FastAPI dependencies

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Backend Framework** | FastAPI | 0.115.12 | High-performance async API |
| **Database** | PostgreSQL | Latest | Metadata and user management |
| **Vector Database** | FAISS | 1.11.0 | Similarity search |
| **LLM Engine** | Mistral 7B | Q4_K_M | Local language model |
| **PDF Processing** | PyPDF2, pdfplumber | Latest | Advanced PDF text extraction |
| **Embeddings** | MiniLM-L6-v2 | Latest | Document embeddings |
| **Authentication** | JWT | via PyJWT | Secure token-based auth |
| **Web Interface** | Vanilla JS + Bootstrap | 5.3.0 | Responsive UI |
| **Caching** | In-memory | Built-in | Performance optimization |
| **Future Notes** | Notion API | TBD | Personal knowledge management |

---

## 🔧 Core Components

### 1. PDF Document Processing Pipeline

```mermaid
graph LR
    UPLOAD[PDF Upload] --> VALIDATE[Security Validation]
    VALIDATE --> EXTRACT[PDF Content Extraction]
    EXTRACT --> CLASSIFY[Document Classification]
    CLASSIFY --> FINANCIAL{Financial?}
    CLASSIFY --> LONGFORM{Long-format?}
    CLASSIFY --> GENERIC{Generic?}
    FINANCIAL --> FINCHUNK[Small Chunks<br/>500 chars]
    LONGFORM --> LONGCHUNK[Large Chunks<br/>1500 chars]
    GENERIC --> GENCHUNK[Balanced Chunks<br/>1000 chars]
    FINCHUNK --> EMBED[Generate Embeddings]
    LONGCHUNK --> EMBED
    GENCHUNK --> EMBED
    EMBED --> STORE[Category-Specific Storage]
    STORE --> INDEX[Namespace Indexing]
```

**Key Features:**
- **PDF-First Focus**: Optimized specifically for PDF document processing
- **Intelligent Classification**: Automatic categorization into financial, long-format, or generic
- **Adaptive Chunking**: Category-specific chunking strategies for optimal retrieval
- **Security Scanning**: MIME type validation, malware detection
- **384-dimensional Embeddings**: MiniLM-L6-v2 model with high efficiency
- **Namespace Isolation**: User-specific vector indices with category metadata

### 2. Document Classification Engine

```mermaid
graph TD
    PDF[PDF Document] --> CONTENT[Extract Content]
    CONTENT --> ANALYZE[Content Analysis]
    ANALYZE --> PATTERNS[Pattern Recognition]
    PATTERNS --> FINANCIAL_CHECK{Financial Patterns?}
    PATTERNS --> LENGTH_CHECK{50+ Pages?}
    PATTERNS --> STRUCTURE_CHECK{Complex Structure?}
    
    FINANCIAL_CHECK -->|Yes| FINANCIAL[Financial Category]
    LENGTH_CHECK -->|Yes| LONGFORM[Long-format Category]
    STRUCTURE_CHECK -->|Default| GENERIC[Generic Category]
    
    FINANCIAL --> METADATA[Category Metadata]
    LONGFORM --> METADATA
    GENERIC --> METADATA
```

**Classification Criteria:**
- **Financial Documents**: Transaction patterns, dollar amounts, bank terminology, statement keywords
- **Long-format Documents**: 50+ pages, academic structure, research patterns, complex formatting
- **Generic Documents**: Personal documents, resumes, letters, moderate length content

### 3. Category-Specific Processing Strategies

| Category | Chunk Size | Overlap | Processing Priority | Search Strategy |
|----------|------------|---------|-------------------|-----------------|
| **Financial** | 500 chars | 50 chars | Structured parsing | Exact match + semantic |
| **Long-format** | 1500 chars | 300 chars | Semantic analysis | Deep semantic similarity |
| **Generic** | 1000 chars | 200 chars | Balanced approach | Hybrid matching |

### 4. Query Processing Engine

```mermaid
graph TD
    QUERY[User Query] --> CLASSIFY[Query Classification]
    CLASSIFY --> DETECT[Document Type Detection]
    DETECT --> PRIORITIZE[Category Prioritization]
    PRIORITIZE --> SEARCH[Category-Aware Search]
    SEARCH --> FINANCIAL_SEARCH[Financial Document Search]
    SEARCH --> LONGFORM_SEARCH[Long-format Document Search]
    SEARCH --> GENERIC_SEARCH[Generic Document Search]
    FINANCIAL_SEARCH --> RANK[Context Ranking]
    LONGFORM_SEARCH --> RANK
    GENERIC_SEARCH --> RANK
    RANK --> GENERATE[LLM Generation]
    GENERATE --> VALIDATE[Response Validation]
    VALIDATE --> CACHE[Cache Response]
    CACHE --> RETURN[Return to User]
```

**Enhanced Query Types:**
- **Financial Queries**: Transaction analysis, expense tracking, budget questions
- **Research Queries**: Academic paper analysis, long-form document insights
- **Personal Queries**: Resume information, personal document retrieval
- **Mixed Queries**: Cross-category document analysis

### 5. Future Notion Integration

**Planned Architecture:**
- **Notion API Integration**: Sync personal notes and knowledge base
- **Unified Vector Store**: Combined PDF + Notion content indexing
- **Cross-Reference Queries**: Link PDF insights with personal notes
- **Intelligent Routing**: Automatic routing between PDF documents and Notion content

---

## 🌐 API Specifications

### Authentication Endpoints

| Method | Endpoint | Description | Security |
|--------|----------|-------------|----------|
| `POST` | `/api/register` | User registration | Rate limited |
| `POST` | `/api/login` | User authentication | Rate limited |
| `GET` | `/api/health-check` | System health status | Public |

### Document Management

| Method | Endpoint | Description | Security |
|--------|----------|-------------|----------|
| `POST` | `/api/documents` | Upload PDF document | JWT required |
| `GET` | `/api/documents` | List user PDF documents with categories | JWT required |
| `DELETE` | `/api/documents/{id}` | Delete PDF document | JWT required |
| `GET` | `/api/documents/{id}/category` | Get document category info | JWT required |

### Query Processing

| Method | Endpoint | Description | Security |
|--------|----------|-------------|----------|
| `POST` | `/api/queries` | Submit query (PDFs + Emails) | JWT required |
| `GET` | `/api/queries` | Query history | JWT required |

### Gmail Integration

| Method | Endpoint | Description | Security |
|--------|----------|-------------|----------|
| `POST` | `/api/gmail/auth` | Initiate Gmail OAuth | JWT required |
| `GET` | `/api/gmail/callback` | OAuth callback handler | OAuth flow |
| `POST` | `/api/gmail/sync` | Sync Gmail emails | JWT required |
| `GET` | `/api/gmail/emails` | List user emails | JWT required |
| `GET` | `/api/gmail/status` | Get sync status | JWT required |
| `DELETE` | `/api/gmail/disconnect` | Disconnect Gmail | JWT required |

### Request/Response Examples

```json
// POST /api/queries
{
  "question": "What expenses did I have in February?",
  "document_id": null,  // Optional: specific document
  "category_filter": "financial"  // Optional: filter by document category
}

// Response
{
  "answer": "Based on your financial documents, your February expenses were...",
  "query_type": "financial_query",
  "document_categories_searched": ["financial"],
  "documents_matched": 3,
  "from_cache": false,
  "processing_time_ms": 650
}
```

---

## 🔐 Security Requirements

### Authentication & Authorization
- **JWT Token-based**: Secure session management
- **Password Hashing**: bcrypt with salt
- **Token Expiration**: Configurable TTL
- **Rate Limiting**: Protection against brute force attacks

### File Security
- **PDF-Specific Validation**: Advanced PDF integrity checking
- **Path Traversal Prevention**: Secure filename sanitization
- **MIME Type Validation**: Strict PDF file type checking
- **Content Scanning**: PDF malware detection and structure validation
- **Size Limits**: Configurable upload limits (10MB default for PDFs)

### Data Protection
- **User Isolation**: Namespace-based data separation
- **Local Processing**: No external API calls
- **Encrypted Storage**: Database encryption at rest
- **Audit Logging**: Security event tracking

### Production Hardening
- **CORS Configuration**: Strict origin policies
- **Debug Logging**: Removed in production
- **Input Validation**: Comprehensive sanitization
- **Error Handling**: No information leakage

---

## ⚡ Performance Requirements

### Response Time Targets
- **PDF Upload & Processing**: < 5 seconds for 10MB PDFs
- **Financial Query Processing**: < 2 seconds (optimized for small chunks)
- **Long-format Query Processing**: < 4 seconds (complex analysis)
- **Generic Query Processing**: < 3 seconds (balanced approach)
- **Document Listing**: < 500ms
- **User Authentication**: < 200ms

### Scalability Metrics
- **Concurrent Users**: 100+ simultaneous sessions
- **PDF Storage**: 20GB+ per user
- **Vector Indices**: 5,000+ PDF documents per user
- **Category-Specific Indices**: Separate optimization per document type
- **Memory Usage**: < 10GB RAM footprint (with PDF processing)

### Optimization Features
- **Category-Specific Caching**: Different TTL per document type
- **PDF Content Caching**: Extracted text cached for re-processing
- **Adaptive Chunking**: Dynamic chunk size based on document category
- **Lazy Loading**: Model loading on demand
- **Connection Pooling**: Database connection optimization

---

## 📊 Data Management

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL DEFAULT 'pdf',
    document_type VARCHAR(20) NOT NULL DEFAULT 'generic',  -- 'financial', 'long_form', 'generic'
    namespace VARCHAR(200) NOT NULL,
    page_count INTEGER,
    processing_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Queries table
CREATE TABLE queries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    query_type VARCHAR(50),
    document_type VARCHAR(50),
    document_id INTEGER REFERENCES documents(id),
    processing_time_ms INTEGER,
    from_cache BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Vector Storage Structure
```
data/vector_db/
├── financial/
│   ├── user_1_doc_bank_statement.index    # Financial document indices
│   ├── user_1_doc_bank_statement.pkl
│   └── user_1_doc_invoice.index
├── long_form/
│   ├── user_1_doc_research_paper.index    # Long-format document indices
│   └── user_1_doc_research_paper.pkl
├── generic/
│   ├── user_1_doc_resume.index            # Generic document indices
│   └── user_1_doc_resume.pkl
└── ...
```

### File Storage Organization
```
static/uploads/
├── 1/                          # User ID
│   ├── financial/
│   │   ├── bank_statement_jan.pdf
│   │   └── invoice_123.pdf
│   ├── long_form/
│   │   ├── research_paper.pdf
│   │   └── contract_agreement.pdf
│   └── generic/
│       ├── resume.pdf
│       └── cover_letter.pdf
├── 2/
│   └── ...
└── ...
```

---

## 🎨 User Interface

### Design Principles
- **Mobile-First**: Responsive design for all devices
- **Accessibility**: WCAG 2.1 compliance
- **Performance**: Fast loading and smooth interactions
- **Intuitive**: Clear navigation and user flows

### Key Features
- **Real-time Feedback**: Live performance metrics
- **Drag-and-Drop**: File upload interface
- **Progressive Enhancement**: Works without JavaScript
- **Dark Mode**: Theme switching capability

### User Experience Flow
1. **Authentication**: Simple login/registration
2. **Document Upload**: Drag-and-drop with progress
3. **Query Interface**: Natural language input
4. **Results Display**: Formatted answers with context
5. **History Management**: Searchable query history

---

## 🚀 Deployment & Infrastructure

### System Requirements
- **Operating System**: Linux/macOS/Windows
- **Memory**: 8GB+ RAM recommended
- **Storage**: 50GB+ available space
- **CPU**: 4+ cores for optimal performance

### Docker Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# LLM Configuration
LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
USE_METAL=true
METAL_N_GPU_LAYERS=1

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32
EMBEDDING_NORMALIZE=true

# Security
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Performance
MAX_FILE_SIZE=5242880  # 5MB
VECTOR_SEARCH_LIMIT=5
CACHE_TTL_SECONDS=300
```

---

## 🧪 Quality Assurance

### Testing Strategy
- **Unit Tests**: Service layer testing with pytest
- **Integration Tests**: API endpoint testing
- **Security Tests**: Penetration testing and vulnerability scanning
- **Performance Tests**: Load testing with realistic data

### Code Quality
- **Static Analysis**: pylint, mypy, black
- **Security Scanning**: bandit, safety
- **Dependency Management**: pip-audit
- **Code Coverage**: 85%+ target

### Monitoring & Logging
- **Structured Logging**: JSON format with correlation IDs
- **Performance Metrics**: Response times, error rates
- **Health Checks**: Database, vector store, LLM availability
- **Alerting**: Critical issue notifications

---

## 🗺️ Roadmap

### Phase 1: PDF Processing Foundation (Completed)
- ✅ Core RAG implementation
- ✅ PDF document processing
- ✅ Document classification (financial, long-format, generic)
- ✅ Category-specific chunking strategies
- ✅ User authentication and security
- ✅ Web interface

### Phase 2: PDF Enhancement & Cleanup (Completed)
- ✅ Advanced PDF text extraction and pagination
- ✅ Performance optimization for large PDFs
- ✅ Enhanced financial document parsing
- ✅ Long-format document pagination (20+ pages)
- ✅ Deep project cleanup and code optimization
- ✅ Advanced skills query handling

### Phase 3: Gmail Integration (✅ COMPLETED)
- ✅ Gmail API integration and OAuth2 authentication
- ✅ Email classification (business, personal, promotional, transactional, support)  
- ✅ Thread-aware email processing and chunking
- ✅ Email-specific vector storage and search
- ✅ Unified PDF + Email query processing
- ✅ Privacy controls and data retention policies

### Phase 4: Notion Integration (Planned Q3 2025)
- 📋 Notion API integration
- 📋 Personal notes synchronization
- 📋 Cross-reference between PDFs, emails, and notes
- 📋 Unified search across PDF + Email + Notion content
- 📋 Smart note organization and cross-linking

### Phase 5: Advanced Features (Planned Q4 2025)
- 📋 OCR for scanned PDFs
- 📋 Advanced table extraction and analysis
- 📋 Multi-language PDF and email support
- 📋 Email analytics and insights dashboard
- 📋 Advanced email filtering and automation
- 📋 Calendar integration with email/document context

### Phase 6: Enterprise Features (Future)
- 📋 Multi-tenant architecture
- 📋 Enterprise Gmail workspace integration
- 📋 Advanced compliance features (email retention, legal hold)
- 📋 API for third-party integrations
- 📋 Advanced security features (2FA, audit trails)

---

## 📚 References

### Technical Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FAISS Documentation](https://faiss.ai/)
- [Mistral AI Documentation](https://docs.mistral.ai/)

### Security Standards
- [OWASP Security Guidelines](https://owasp.org/)
- [JWT Best Practices](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)

### Performance Benchmarks
- [MiniLM Performance](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [FAISS Performance Metrics](https://github.com/facebookresearch/faiss/wiki/Performance-evaluation)

---

**Document Control:**
- **Author**: Personal AI Agent Development Team
- **Review Cycle**: Monthly
- **Next Review**: August 4, 2025
- **Version History**: Available in Git repository
