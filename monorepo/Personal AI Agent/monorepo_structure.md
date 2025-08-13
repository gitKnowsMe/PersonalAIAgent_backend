# Personal AI Agent - Monorepo Architecture

A comprehensive monorepo structure for hybrid deployment: Vercel frontend + local backend.

## 🏗️ Proposed Directory Structure

```
personal-ai-agent/
├── README.md                          # Main project documentation
├── .env.example                       # Environment template for backend
├── .gitignore                         # Combined gitignore for both frontend/backend
├── LICENSE                            # Project license
├── HYBRID_DEPLOYMENT.md               # Deployment guide
├── CHANGELOG.md                       # Version history
│
├── frontend/                          # Next.js frontend (Vercel deployment)
│   ├── src/
│   │   ├── app/                       # Next.js 13+ app router
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── auth/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── chat/
│   │   │   │   └── page.tsx
│   │   │   ├── documents/
│   │   │   │   ├── page.tsx
│   │   │   │   └── upload/
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   ├── components/                # Reusable UI components
│   │   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── chat/
│   │   │   │   ├── chat-interface.tsx
│   │   │   │   ├── message-list.tsx
│   │   │   │   └── input-form.tsx
│   │   │   ├── documents/
│   │   │   │   ├── upload-zone.tsx
│   │   │   │   └── document-list.tsx
│   │   │   ├── layout/
│   │   │   │   ├── header.tsx
│   │   │   │   ├── sidebar.tsx
│   │   │   │   └── footer.tsx
│   │   │   └── common/
│   │   │       ├── loading.tsx
│   │   │       ├── error-boundary.tsx
│   │   │       └── connection-status.tsx
│   │   ├── lib/                       # Utility functions and API client
│   │   │   ├── api.ts                 # API client for backend communication
│   │   │   ├── auth.ts                # Authentication utilities
│   │   │   ├── utils.ts               # General utilities
│   │   │   └── types.ts               # TypeScript type definitions
│   │   ├── hooks/                     # Custom React hooks
│   │   │   ├── use-api.ts
│   │   │   ├── use-auth.ts
│   │   │   └── use-chat.ts
│   │   └── styles/                    # Additional styles
│   │       └── components.css
│   ├── public/                        # Static assets
│   │   ├── icons/
│   │   ├── images/
│   │   └── favicon.ico
│   ├── package.json                   # Frontend dependencies
│   ├── package-lock.json
│   ├── next.config.js                 # Next.js configuration
│   ├── tailwind.config.js             # Tailwind CSS config
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── .env.local.example             # Frontend environment template
│   ├── .eslintrc.json                 # ESLint configuration
│   ├── vercel.json                    # Vercel deployment config
│   └── README.md                      # Frontend-specific documentation
│
├── backend/                           # FastAPI backend (local deployment)
│   ├── app/                           # Main application code
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── api/                       # API routes
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── documents.py
│   │   │       ├── queries.py
│   │   │       ├── gmail.py
│   │   │       ├── emails.py
│   │   │       └── sources.py
│   │   ├── core/                      # Core configuration and security
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── constants.py
│   │   │   ├── exceptions.py
│   │   │   └── security.py
│   │   ├── db/                        # Database models and connection
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── session_manager.py
│   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── query.py
│   │   │   └── email.py
│   │   ├── services/                  # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── vector_store_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── query_router.py
│   │   │   ├── gmail_service.py
│   │   │   └── email/
│   │   │       ├── __init__.py
│   │   │       ├── email_classifier.py
│   │   │       ├── email_ingestion.py
│   │   │       ├── email_processor.py
│   │   │       ├── email_query.py
│   │   │       └── email_store.py
│   │   └── utils/                     # Utility functions
│   │       ├── __init__.py
│   │       ├── llm.py
│   │       ├── document_classifier.py
│   │       ├── response_filter.py
│   │       ├── logging_config.py
│   │       └── processors/
│   │           ├── __init__.py
│   │           ├── base_processor.py
│   │           ├── pdf_processor.py
│   │           ├── financial_processor.py
│   │           └── text_processor.py
│   ├── scripts/                       # Setup and utility scripts
│   │   ├── setup.sh                   # Main setup script
│   │   ├── start.sh                   # Start backend script
│   │   ├── stop.sh                    # Stop backend script
│   │   ├── update.sh                  # Update script
│   │   └── install/                   # Installation helpers
│   │       ├── check_requirements.py
│   │       ├── download_models.py
│   │       └── setup_database.py
│   ├── tests/                         # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_utils/
│   ├── data/                          # Local data storage
│   │   ├── vector_db/                 # Vector database storage
│   │   │   ├── financial/
│   │   │   ├── long_form/
│   │   │   ├── generic/
│   │   │   └── emails/
│   │   ├── app.db                     # SQLite database (gitignored)
│   │   └── .gitkeep
│   ├── models/                        # AI model storage
│   │   ├── mistral-7b-instruct-v0.1.Q4_K_M.gguf  # (gitignored)
│   │   ├── all-MiniLM-L6-v2/          # (gitignored)
│   │   └── .gitkeep
│   ├── logs/                          # Application logs
│   │   ├── app.log                    # (gitignored)
│   │   └── .gitkeep
│   ├── static/                        # Static file storage
│   │   ├── uploads/                   # User uploaded files (gitignored)
│   │   ├── emails/                    # Email storage (gitignored)
│   │   └── .gitkeep
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Backend environment template
│   ├── main.py                        # Backend entry point (symlink to app/main.py)
│   ├── download_model.py              # Model download script
│   ├── download_embedding_model.py    # Embedding model download
│   ├── setup_db.py                    # Database setup
│   ├── create_admin.py                # Admin user creation
│   ├── setup_gmail.py                 # Gmail setup helper
│   └── README.md                      # Backend-specific documentation
│
├── docs/                              # Comprehensive documentation
│   ├── README.md                      # Documentation index
│   ├── getting-started/
│   │   ├── installation.md
│   │   ├── quickstart.md
│   │   └── configuration.md
│   ├── deployment/
│   │   ├── hybrid.md                  # Hybrid deployment guide
│   │   ├── local.md                   # Local development
│   │   ├── frontend.md                # Frontend deployment
│   │   └── backend.md                 # Backend deployment
│   ├── api/
│   │   ├── authentication.md
│   │   ├── documents.md
│   │   ├── queries.md
│   │   └── gmail.md
│   ├── development/
│   │   ├── architecture.md
│   │   ├── contributing.md
│   │   ├── testing.md
│   │   └── troubleshooting.md
│   └── user-guide/
│       ├── pdf-documents.md
│       ├── gmail-integration.md
│       └── querying.md
│
├── .github/                           # GitHub configuration
│   ├── workflows/                     # CI/CD workflows
│   │   ├── frontend-deploy.yml        # Vercel deployment
│   │   ├── backend-test.yml           # Backend testing
│   │   └── release.yml                # Release automation
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── support.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CONTRIBUTING.md
│
└── scripts/                           # Root-level scripts
    ├── quick-start.sh                 # One-command setup for entire project
    ├── dev-setup.sh                   # Development environment setup
    ├── deploy-frontend.sh             # Frontend deployment helper
    └── cleanup.sh                     # Cleanup generated files
```

## 🚀 Key Benefits of This Structure

### 1. **Clear Separation of Concerns**
- `frontend/` - All React/Next.js code for Vercel deployment
- `backend/` - All Python/FastAPI code for local deployment
- `docs/` - Comprehensive documentation
- Root level - Project coordination and scripts

### 2. **Unified Development Experience**
- Single repository clone gets everything
- Shared documentation and configuration
- Coordinated releases and versioning

### 3. **Simplified Deployment**
- Frontend deploys to Vercel automatically
- Backend runs locally with simple scripts
- Clear environment configuration for each

### 4. **Better Organization**
- Related code stays together
- Clear dependency management
- Consistent project structure

## 📋 Migration Strategy

### Phase 1: Structure Creation
1. Create new monorepo structure
2. Move existing backend code to `backend/`
3. Create frontend structure in `frontend/`
4. Set up root-level coordination

### Phase 2: Script Creation
1. Create setup scripts for automated installation
2. Update environment configuration
3. Create deployment helpers
4. Update documentation

### Phase 3: Testing and Validation
1. Test local development workflow
2. Test deployment to Vercel
3. Validate API communication
4. Performance testing

## 🛠️ Development Workflow

### For Users (Simple Setup)
```bash
# Clone the repository
git clone https://github.com/username/personal-ai-agent
cd personal-ai-agent

# Run the quick setup script
./scripts/quick-start.sh

# Everything is installed and configured!
# Backend runs locally, frontend deploys to Vercel
```

### For Developers (Advanced Setup)
```bash
# Clone repository
git clone https://github.com/username/personal-ai-agent
cd personal-ai-agent

# Setup development environment
./scripts/dev-setup.sh

# Frontend development
cd frontend
npm run dev  # Runs on localhost:3000

# Backend development
cd backend
python main.py  # Runs on localhost:8000
```

## 🔧 Configuration Files

### Root `.env.example`
```env
# This file documents all environment variables for the entire project

# Backend Configuration
# (Copy to backend/.env)

# Server Settings
HOST=localhost
PORT=8000
DEBUG=true

# Database
DATABASE_URL=sqlite:///./data/personal_ai_agent.db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS for hybrid deployment
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000

# AI Models
LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
USE_METAL=true
METAL_N_GPU_LAYERS=1

# Gmail Integration
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback

# Frontend Configuration
# (Copy to frontend/.env.local)

# API Connection
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Personal AI Agent
```

### Frontend `vercel.json`
```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "env": {
    "NEXT_PUBLIC_API_URL": "http://localhost:8000",
    "NEXT_PUBLIC_APP_NAME": "Personal AI Agent"
  },
  "functions": {
    "app/api/[...route]/route.ts": {
      "maxDuration": 30
    }
  }
}
```

## 📚 Updated Documentation Structure

The monorepo will have comprehensive documentation:

1. **Root README.md** - Project overview and quick start
2. **Frontend README.md** - Frontend development and deployment
3. **Backend README.md** - Backend development and API
4. **docs/** - Detailed guides for users and developers
5. **HYBRID_DEPLOYMENT.md** - Comprehensive deployment guide

This structure provides the best of both worlds: a simple experience for end users and a powerful development environment for contributors.