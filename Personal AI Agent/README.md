# Personal AI Agent

A privacy-first AI assistant with hybrid deployment architecture - Vercel frontend + local backend.

## 🚀 Quick Start

**One-command setup:**
```bash
git clone https://github.com/username/personal-ai-agent
cd personal-ai-agent
./scripts/quick-start.sh
```

That's it! The script will:
- ✅ Install all dependencies
- ✅ Download AI models (Mistral 7B + embeddings)
- ✅ Setup database and environment
- ✅ Configure both frontend and backend

## 🎯 Hybrid Architecture

```
┌─────────────────┐    HTTPS    ┌─────────────────┐
│   Vercel        │────────────▶│   Your Computer │
│   Frontend      │             │                 │
│ (Public Access) │             │ ┌─────────────┐ │
└─────────────────┘             │ │   Backend   │ │
                                │ │  (Private)  │ │
                                │ └─────────────┘ │
                                │ ┌─────────────┐ │
                                │ │     AI      │ │
                                │ │   Models    │ │
                                │ └─────────────┘ │
                                └─────────────────┘
```

### ✨ Benefits

- **🔒 Complete Privacy**: All AI processing stays on your computer
- **🌍 Global Access**: Fast frontend via Vercel CDN
- **💰 Zero AI Costs**: No GPT-4/Claude API fees
- **🚀 Easy Setup**: One command installs everything

## 📁 Project Structure

```
personal-ai-agent/
├── frontend/          # Next.js app → Deploy to Vercel
├── backend/           # FastAPI server → Run locally
├── scripts/           # Setup automation
├── docs/              # Documentation
└── README.md          # This file
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