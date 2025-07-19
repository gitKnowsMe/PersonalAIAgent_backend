# Personal AI Agent - Backend API

A privacy-first AI assistant backend with hybrid deployment architecture. This repository contains the **backend API only** - the frontend is deployed separately.

## 🚀 Quick Start

**Backend Setup:**
```bash
git clone https://github.com/username/personal-ai-agent-backend
cd personal-ai-agent-backend/backend

# Setup Python environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Setup PostgreSQL database
python setup_postgresql.py

# Download AI models
python download_model.py
python download_embedding_model.py

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials and Gmail OAuth settings

# Initialize database and create admin user
python setup_db.py
python create_admin.py

# Start the server
python start_backend.py
```

**API will be available at:** `http://localhost:8000`
**API Documentation:** `http://localhost:8000/docs`

## 🎯 Hybrid Architecture

```
┌─────────────────┐    API Calls    ┌─────────────────┐
│   Frontend      │────────────────▶│   Backend API   │
│ (Separate Repo) │                 │  (This Repo)    │
│                 │                 │                 │
│ • Vercel        │                 │ • FastAPI       │
│ • Netlify       │                 │ • Local LLM     │
│ • Static Host   │                 │ • Vector DB     │
└─────────────────┘                 │ • Gmail OAuth   │
                                    └─────────────────┘
```

### ✨ Benefits

- **🔒 Complete Privacy**: All AI processing stays on your server
- **🌍 Scalable**: Frontend and backend scale independently
- **💰 Zero AI Costs**: No GPT-4/Claude API fees
- **🚀 Flexible**: Use any frontend framework
- **🛡️ Production Ready**: Enterprise-grade security and monitoring
- **📊 Multi-User**: PostgreSQL-based with proper user isolation

## 📁 Backend Structure

```
backend/
├── app/
│   ├── api/endpoints/     # API routes
│   ├── core/              # Configuration
│   ├── db/                # Database models
│   ├── services/          # Business logic
│   └── utils/             # Utilities
├── data/                  # User data storage
├── models/                # LLM models
├── logs/                  # Application logs
├── .env.development       # Dev environment
├── .env.production        # Prod environment
├── Dockerfile             # Container config
└── requirements.txt       # Python dependencies
├── docs/              # Documentation
└── README.md          # This file
```

## 🛡️ Production Features

### Security & Monitoring
- **🔐 Rate Limiting**: Configurable API rate limits with brute force protection
- **📊 Session Monitoring**: Real-time user session tracking and analytics
- **📝 Audit Logging**: Comprehensive audit trails for all user actions
- **👨‍💼 Admin Dashboard**: Complete user management with safety controls
- **⚡ Performance Monitoring**: Error tracking and performance metrics
- **💾 Smart Caching**: TTL-based caching system for optimal performance

### Database Architecture
- **🐘 PostgreSQL First**: Default database for all environments
- **🔄 Connection Pooling**: Optimized connection management
- **📈 Performance Indexes**: 25+ strategic indexes for fast queries
- **🔒 Data Isolation**: Complete user data separation and security
- **🗄️ Multi-User Ready**: Proper foreign key constraints and relationships

### API Endpoints
```bash
# Authentication
POST /api/login          # User login
POST /api/register       # User registration

# Documents
POST /api/documents/upload   # PDF upload and processing
GET  /api/documents         # List user documents

# AI Queries
POST /api/queries           # AI question processing
GET  /api/queries/history   # Query history

# Gmail Integration
GET  /api/gmail/auth        # OAuth2 flow
POST /api/gmail/sync        # Email synchronization
GET  /api/emails           # Search emails

# Admin (requires admin privileges)
GET  /api/admin/users       # User management
GET  /api/admin/sessions    # Active sessions
GET  /api/admin/stats       # System statistics
```

## 🛠️ Manual Setup (Advanced)

### Frontend Development
```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### Backend Development
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python download_model.py
python download_embedding_model.py
python setup_db.py
python main.py  # http://localhost:8000
```

## ⚙️ Configuration

### Backend Environment
```bash
# Edit backend/.env
HOST=localhost
PORT=8000
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000

# Gmail Integration (optional)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
```

### Frontend Environment
```bash
# Edit frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Personal AI Agent
```

## 🚀 Deployment

### Frontend (Vercel)
1. Push repository to GitHub
2. Connect to Vercel
3. Deploy automatically
4. Set environment variable: `NEXT_PUBLIC_API_URL=http://localhost:8000`

### Backend (Local)
```bash
cd backend
python main.py
# Runs on http://localhost:8000
```

## 📚 Features

### ✅ Current Features
- **PDF Document Processing**: Upload and analyze PDF files
- **Gmail Integration**: Sync and search your emails
- **AI Chat Interface**: Ask questions about your documents
- **Document Classification**: Automatic categorization
- **Vector Search**: Semantic similarity search
- **Local LLM**: Mistral 7B for private AI processing

### 🚧 In Development
- **Advanced Frontend**: Modern React/Next.js interface
- **Real-time Chat**: WebSocket-based communication
- **Mobile Support**: Responsive design
- **Notion Integration**: Connect your knowledge base

## 🧠 AI Capabilities

### Document Processing
- **Financial Documents**: Bank statements, invoices, receipts
- **Long-format Documents**: Research papers, reports (20+ pages)
- **Generic Documents**: Resumes, letters, personal files

### Email Processing
- **Categories**: Business, personal, promotional, transactional, support
- **Thread Processing**: Conversation context preservation
- **Smart Search**: Semantic search across email content

### Query Processing
- **Cross-Content Search**: Search both PDFs and emails
- **Intelligent Routing**: Automatic source detection
- **Context Assembly**: Unified responses from multiple sources

## 📊 System Requirements

- **Python**: 3.8+ (for backend)
- **Node.js**: 18+ (for frontend development)
- **Memory**: 4GB+ RAM (for AI models)
- **Storage**: 5GB+ free space (for models and data)

## 🔧 Development

### Adding Features
1. **Backend**: Add API endpoints in `backend/app/api/endpoints/`
2. **Frontend**: Create components in `frontend/src/components/`
3. **Documentation**: Update relevant docs in `docs/`

### Testing
```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm run test
```

## 📖 Documentation

- **[Hybrid Deployment Guide](./hybrid_deployment.md)** - Complete deployment strategy
- **[Migration Guide](./MIGRATION_GUIDE.md)** - Upgrading from old structure
- **[Frontend README](./frontend/README.md)** - Frontend development
- **[Backend README](./backend/README.md)** - Backend development
- **[API Documentation](./docs/api/)** - API endpoints reference

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/username/personal-ai-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/personal-ai-agent/discussions)
- **Documentation**: [Complete Docs](./docs/)

## 🙏 Acknowledgments

- **Mistral AI**: For the excellent local LLM
- **Sentence Transformers**: For embedding models
- **FastAPI**: For the robust backend framework
- **Next.js**: For the modern frontend framework
- **Vercel**: For seamless frontend deployment

---

**Get started in 30 seconds:** `./scripts/quick-start.sh` 🚀