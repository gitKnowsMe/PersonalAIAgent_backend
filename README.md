# Personal AI Agent - Backend

A powerful, privacy-first AI backend built with FastAPI that provides local LLM processing, document analysis, and Gmail integration. Designed to run locally while connecting to a public frontend.

[![Built with FastAPI](https://img.shields.io/badge/Built%20with-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![LLM Powered](https://img.shields.io/badge/LLM-Mistral%207B-FF6B6B?style=for-the-badge)](https://mistral.ai/)

## Features

- 🧠 **Local LLM Processing** - Mistral 7B with Metal acceleration on macOS
- 📄 **Advanced PDF Processing** - Category-aware document classification and chunking
- 📧 **Gmail OAuth2 Integration** - Secure email access and thread-aware processing
- 🔍 **Vector Search** - FAISS-based semantic similarity search
- 🖥️ **Cross-Platform Executables** - Windows, macOS, and Linux binaries
- 🗄️ **Flexible Database** - PostgreSQL for dev, SQLite for portability  
- 🔐 **JWT Authentication** - Secure API access with token-based auth
- 🚀 **CI/CD Pipeline** - Automated builds via GitHub Actions
- 🌐 **CORS Enabled** - Ready for frontend integration

## Quick Start

### Option 1: Download Executable (Recommended)
1. Visit [Releases](https://github.com/gitKnowsMe/PersonalAIAgent_backend/releases)
2. Download for your platform: `PersonalAIAgent-{platform}-no-models.zip`
3. Extract and run the installer
4. Models will download automatically on first run

### Option 2: Development Setup
```bash
# Clone repository
git clone https://github.com/gitKnowsMe/PersonalAIAgent_backend.git
cd PersonalAIAgent_backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download AI models (~4GB)
python download_model.py
python download_embedding_model.py

# Setup database
python setup_db.py

# Create admin user
python create_admin.py

# Start backend
python start_backend.py
```

## Architecture

### Core Components
- **FastAPI Application** - RESTful API with automatic OpenAPI docs
- **Local LLM** - Mistral 7B with llama-cpp-python for inference
- **Vector Database** - FAISS for semantic document/email search
- **Document Processing** - Category-specific PDF processing pipeline
- **Email Integration** - Gmail OAuth2 with thread-aware processing
- **Authentication** - JWT tokens with bcrypt password hashing

### Document Processing Pipeline
1. **Upload** → PDF validation and security checks
2. **Classification** → Financial, Long-format, or Generic categorization
3. **Processing** → Category-specific chunking strategies:
   - **Financial**: 500-char chunks for transaction precision
   - **Long-format**: 1500-char chunks for comprehensive context
   - **Generic**: 1000-char balanced chunks
4. **Embeddings** → MiniLM model for vector generation
5. **Storage** → Category-organized FAISS indices

### Gmail Integration
- **OAuth2 Flow** - Secure Google account connection
- **Email Classification** - Business, Personal, Promotional, Transactional, Support
- **Thread Processing** - Conversation context preservation
- **Vector Storage** - Email-specific FAISS indices for search

## API Endpoints

- `GET /` - API status and information
- `GET /docs` - Interactive API documentation
- `GET /api/health-check` - Health and capabilities check
- `POST /api/auth/login` - User authentication
- `POST /api/documents/upload` - PDF upload and processing
- `POST /api/queries/` - AI-powered query processing
- `GET /api/gmail/auth` - Gmail OAuth2 initiation
- `POST /api/gmail/sync` - Email synchronization

## Configuration

### Environment Variables
```bash
# Core Settings
HOST=localhost
PORT=8000
DATABASE_URL=sqlite:///personal_ai_agent.db

# Gmail OAuth (Required for email features)
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-your_client_secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback

# LLM Configuration
LLM_MODEL_PATH=models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
USE_METAL=true  # macOS acceleration
METAL_N_GPU_LAYERS=1

# CORS (for frontend integration)
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

### Gmail OAuth Setup
1. Create Google Cloud Console project
2. Enable Gmail API
3. Create OAuth2 credentials (Web application)
4. Add redirect URI: `http://localhost:8000/api/gmail/callback`
5. Download client configuration and update `.env`

## Development

### Testing
```bash
# Backend connection test
python test_backend_connection.py

# Core functionality tests
python test_email_search.py
python test_api_query.py
python test_model_loading.py

# Run unit tests
python -m pytest tests/

# Specific test
python -m pytest tests/test_document_classifier.py::test_financial_classification
```

### Building Executables
```bash
# Build for current platform
python build_executable.py

# Cross-platform builds (via GitHub Actions)
git tag v1.0.0
git push origin v1.0.0
# Check GitHub Actions for builds
```

## Deployment

### Local Development
```bash
python start_backend.py
# API available at http://localhost:8000
```

### Production Deployment
1. Configure environment variables for production
2. Set up PostgreSQL database
3. Configure CORS for your frontend domain
4. Deploy using Docker or VPS hosting

### Frontend Integration
This backend is designed to work with the [Personal AI Agent Frontend](https://github.com/gitKnowsMe/PersonalAIAgent_frontend):
- Frontend deployed on Vercel (public)
- Backend runs locally (private)
- Automatic backend detection and installation
- CORS-enabled communication

## Data Privacy

- **Local Processing** - All AI inference happens on your machine
- **No External LLM APIs** - Complete privacy, no data sent to third parties
- **Local Storage** - Documents and emails stored locally
- **Encrypted Authentication** - Secure JWT tokens and bcrypt hashing

## System Requirements

- **Minimum**: 8GB RAM, 15GB free disk space
- **Recommended**: 16GB RAM, SSD storage
- **Platforms**: Windows 10+, macOS 10.14+, Linux 64-bit
- **Optional**: GPU for accelerated inference (Metal on macOS)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes and add tests
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/new-feature`)
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See `/docs` directory for detailed guides
- **Issues**: Report bugs via [GitHub Issues](https://github.com/gitKnowsMe/PersonalAIAgent_backend/issues)
- **API Docs**: Available at `http://localhost:8000/docs` when running

---

**Privacy-First AI Agent** - All processing happens locally on your machine.