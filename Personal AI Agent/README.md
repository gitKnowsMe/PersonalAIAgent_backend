# Personal AI Agent

A privacy-first AI assistant for PDF documents and Gmail emails with advanced document classification and processing capabilities.

## 🚀 Key Features

- **100% Privacy**: Local LLM processing with no external API calls (except Gmail OAuth)
- **PDF + Gmail Integration**: Unified processing for PDF documents and Gmail emails  
- **Smart Content Classification**: Automatic categorization for documents and emails
- **Category-Specific Processing**: Optimized chunking and indexing per content type
- **Thread-Aware Email Processing**: Conversation context preservation
- **Cross-Platform Queries**: Search across PDFs and emails with unified results

## 📧 Gmail Integration (✅ COMPLETED)

The Personal AI Agent now includes comprehensive Gmail integration with:

### Features
- **OAuth2 Authentication**: Secure Google account connection
- **Email Classification**: 5 types (business, personal, promotional, transactional, support)
- **Thread-Aware Processing**: Preserves conversation context
- **Vector Search**: Semantic search across email content
- **Attachment Support**: Process email attachments
- **Privacy Controls**: Selective sync and content filtering

### Email Categories
- **Business**: Meeting invites, project updates, work communications
- **Personal**: Family/friend emails, personal communications
- **Promotional**: Marketing emails, newsletters, deals
- **Transactional**: Receipts, confirmations, account notifications
- **Support**: Customer service, technical support communications

## 📄 Document Categories

### Financial Documents (Bank Statements, Invoices, Receipts)
- **Processing**: Small chunks (500 chars), structured parsing
- **Use Cases**: Expense tracking, financial analysis, transaction queries

### Long-format Documents (Research Papers, Reports, Contracts)
- **Processing**: Large chunks (1500 chars), semantic analysis  
- **Use Cases**: Research queries, detailed analysis, document understanding

### Generic Documents (Resumes, Letters, Notes)
- **Processing**: Balanced chunks (1000 chars), hybrid approach
- **Use Cases**: Personal information retrieval, skill queries

## 🛠️ Setup Instructions

### 1. Environment Setup

Create a `.env` file in the root directory with the following configuration:

```env
# Personal AI Agent Environment Configuration

# Server Configuration
HOST=localhost
PORT=8000
DEBUG=true

# Database Configuration
DATABASE_URL=sqlite:///./personal_ai_agent.db

# Security Configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Gmail Integration Configuration
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback
GMAIL_MAX_EMAILS_PER_SYNC=1000
GMAIL_DEFAULT_SYNC_LIMIT=100

# LLM Configuration
LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
USE_METAL=true
METAL_N_GPU_LAYERS=1

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32
EMBEDDING_NORMALIZE=true

# Vector Store Configuration
VECTOR_DB_PATH=./data/vector_db
EMAIL_VECTOR_DB_PATH=./data/email_vectors
VECTOR_SEARCH_TOP_K=5
VECTOR_SIMILARITY_THRESHOLD=0.3

# Email Storage Configuration
EMAIL_STORAGE_DIR=./static/emails

# Logging Configuration
LOG_LEVEL=INFO
```

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth2 credentials
5. Add your client ID and secret to the `.env` file

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download AI Model

```bash
python download_model.py
```

### 5. Setup Database

```bash
python setup_db.py
```

### 6. Run the Application

```bash
python main.py
```

The application will be available at `http://localhost:8000`

## 📚 API Endpoints

### Gmail Integration
- `GET /api/gmail/auth-url` - Get OAuth2 authorization URL
- `GET /api/gmail/callback` - OAuth2 callback handler
- `POST /api/gmail/sync` - Sync emails from Gmail
- `POST /api/gmail/search` - Search emails using vector similarity
- `GET /api/gmail/status` - Get account status and sync info
- `DELETE /api/gmail/disconnect` - Disconnect Gmail account

### Document Processing
- `POST /api/documents/upload` - Upload and process PDF documents
- `GET /api/documents/` - List user documents
- `DELETE /api/documents/{id}` - Delete document

### Queries
- `POST /api/queries/` - Ask questions about documents and emails
- `GET /api/queries/` - Get query history

## 🔧 Architecture

The application uses a modern, scalable architecture:

- **FastAPI**: High-performance async API framework
- **PostgreSQL**: Metadata and user management
- **FAISS**: Vector similarity search
- **Mistral 7B**: Local language model
- **OAuth2**: Secure Gmail authentication
- **Category-Based Storage**: Organized vector indices

## 📊 Current Status

✅ **Phase 1 Complete**: Gmail Integration
- OAuth2 authentication ✅
- Email sync and processing ✅  
- Email classification ✅
- Vector storage and search ✅
- API endpoints ✅

🔄 **Phase 2 In Progress**: Security Hardening
- Rate limiting implementation
- CORS configuration
- Debug logging cleanup

📋 **Phase 3 Planned**: Advanced Features
- Email analytics and insights
- Thread summarization
- Cross-reference between emails and PDFs

## 🤝 Contributing

Please read the `IMPLEMENTATION_PLAN.md` and `Personal_AI_Agent_SRD.md` for detailed technical information.

## 📄 License

This project is licensed under the MIT License. 