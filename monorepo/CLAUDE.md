# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **monorepo** containing two Personal AI Agent implementations:

1. **Personal AI Agent** (`Personal AI Agent/`) - Complete full-stack application with FastAPI backend and multiple frontend options
2. **PersonalAIAgent_frontend** (`PersonalAIAgent_frontend/`) - Standalone Next.js frontend for hybrid deployment

Both implement a privacy-first AI assistant with PDF document processing, Gmail OAuth integration, and local LLM processing (Mistral 7B) with different deployment strategies.

## Architecture Overview

This monorepo implements a sophisticated AI agent system with three distinct deployment architectures:

### Core AI Processing Pipeline
- **Document Classification**: Automatic categorization into financial, long-format, and generic documents
- **Category-Specific Processing**: Adaptive chunking (500-1500 chars) based on document type
- **Email Integration**: Thread-aware Gmail processing with OAuth2 authentication
- **Vector Search**: FAISS-based semantic search with category-aware indexing
- **Local LLM**: Mistral 7B for private AI processing with Metal acceleration on macOS

### Deployment Strategies
1. **Single Executable Backend** (Phase 2 Complete) - Desktop app with Vercel frontend
2. **Hybrid Deployment** - Separate frontend/backend with CORS integration
3. **Monolithic** - Traditional full-stack with served static frontend

## Documentation Index

### 📚 Core Documentation
- **[CLAUDE.md](CLAUDE.md)** - Main project guidance and architecture overview
- **[README.md](Personal AI Agent/README.md)** - Getting started and installation guide

### 🔧 CI/CD & Build System  
- **[CICD.md](CICD.md)** - Complete GitHub Actions workflow documentation
- **[BUILD_VERSION.md](BUILD_VERSION.md)** - Version management and release procedures
- **[.github/workflows/build-executables.yml](.github/workflows/build-executables.yml)** - Multi-platform build workflow

### 🖥️ Desktop Installer System
- **[PHASE_3_DISTRIBUTION_COMPLETE.md](PHASE_3_DISTRIBUTION_COMPLETE.md)** - Desktop installer implementation
- **[PersonalAIAgent_frontend/CLAUDE.md](PersonalAIAgent_frontend/CLAUDE.md)** - Frontend architecture and integration

### 📋 Development Guides
- **[Personal AI Agent/backend/TESTING_GUIDE.md](Personal AI Agent/backend/TESTING_GUIDE.md)** - Testing procedures
- **[Personal AI Agent/backend/DEPLOYMENT.md](Personal AI Agent/backend/DEPLOYMENT.md)** - Deployment configurations
- **[Personal AI Agent/backend/TROUBLESHOOTING.md](Personal AI Agent/backend/TROUBLESHOOTING.md)** - Common issues and solutions

## Quick Start Commands

```bash
# Option 1: Single Executable Backend (RECOMMENDED)
# 1. Visit https://your-vercel-app.vercel.app
# 2. Register/Login to the web interface
# 3. Download the executable for your platform
# 4. Double-click to install and start backend
# 5. Frontend automatically detects and connects

# Option 2: Traditional Development Setup
cd "Personal AI Agent/backend" && python start_backend.py

# Option 3: Hybrid Deployment (Advanced)
cd "Personal AI Agent/backend" && python main.py &
cd PersonalAIAgent_frontend/ && npm run dev

# Test backend connectivity and core features
cd "Personal AI Agent/backend"
python test_backend_connection.py
python test_email_search.py
python -m pytest tests/test_document_classifier.py
```

## Development Commands

### Personal AI Agent (Full-Stack)

**Backend Setup:**
```bash
cd "Personal AI Agent/backend"
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Download models (4GB+ download)
python download_model.py
python download_embedding_model.py

# Setup database and admin user
python setup_db.py
python create_admin.py

# Configure environment
cp .env.development .env
# Edit .env with Gmail OAuth credentials

# Start backend (recommended)
python start_backend.py
# OR: python main.py  # Runs on http://localhost:8000
```

**Testing Commands:**
```bash
# Backend connection and health
python test_backend_connection.py

# Core functionality tests
python test_email_search.py
python test_api_query.py
python test_model_loading.py

# Feature-specific tests
python test_classification_tags_fix.py
python test_source_attribution_fix.py
python test_mixed_sources.py

# Unit tests
python -m pytest tests/
python -m pytest tests/test_document_classifier.py

# Run single test function
python -m pytest tests/test_document_classifier.py::test_financial_classification

# Run tests with verbose output
python -m pytest tests/ -v

# Run specific feature tests
python test_classification_tags_fix.py
python test_source_attribution_fix.py  
python test_performance_indexes.py
```

**Frontend Development:**
```bash
# Legacy Static Frontend (Production-ready)
# Served automatically by backend at http://localhost:8000

# Modern Next.js Frontend (In Development)
cd "Personal AI Agent/frontend"
npm install
npm run dev      # http://localhost:3000
npm run lint
npm run type-check

# TypeScript API Client
cd "Personal AI Agent/backend/client"
npm install
npm run build
```

### PersonalAIAgent_frontend (Standalone)

**Development:**
```bash
cd PersonalAIAgent_frontend/
npm install
npm run dev      # Development server
npm run build    # Production build
npm run start    # Production server
npm run lint     # ESLint
npm run type-check # TypeScript validation
```

**Environment Setup:**
```bash
# Create .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Personal AI Agent
```

## Architecture Overview

### Core AI Processing Pipeline

**Document Classification & Processing:**
- **Financial Documents**: Bank statements, invoices → 500-char chunks for transaction precision
- **Long-format Documents**: 20+ pages → 1500-char chunks for comprehensive context  
- **Generic Documents**: Personal files → 1000-char balanced chunks

**Email Classification & Processing:**
- **Business/Personal/Promotional/Transactional/Support** categories
- Thread-aware processing with conversation context preservation
- OAuth2 Gmail integration with secure token management

**Unified Query System:**
- Cross-content search spanning PDFs and emails
- Category-aware vector search using FAISS indices
- Local LLM processing (Mistral 7B) with Metal acceleration on macOS
- Source attribution and relevance scoring

### Personal AI Agent (Full-Stack)

**Backend Architecture (FastAPI):**
- `backend/app/main.py` - Application entry point with lifespan management
- `backend/app/core/config.py` - Environment configuration with Gmail OAuth validation
- `backend/app/api/endpoints/` - RESTful API endpoints for auth, documents, queries, Gmail
- `backend/app/services/` - Business logic for PDF/email processing and LLM queries
- `backend/app/utils/processors/` - Category-specific document processors
- `backend/app/db/` - Database models and session management

**Frontend Options:**
1. **Legacy Static Frontend** (`backend/static/`) - Production-ready HTML/CSS/JS
2. **Modern Next.js Frontend** (`frontend/`) - TypeScript/Tailwind (in development)
3. **TypeScript API Client** (`backend/client/`) - Reusable client library

### PersonalAIAgent_frontend (Standalone)

**Modern Frontend Architecture:**
- **Framework**: Next.js 15 + React 19 + TypeScript
- **UI**: Tailwind CSS + Radix UI + shadcn/ui components
- **Backend Integration**: RESTful API client with JWT authentication
- **Deployment**: Vercel/Netlify compatible with CORS-enabled backend

**Key Components:**
- `app.tsx` - Main application with view routing and auth state
- `components/chat-interface.tsx` - AI chat with streaming responses
- `components/upload-interface.tsx` - Drag-and-drop document upload
- `lib/api.ts` - Comprehensive backend API client (LocalBackendClient)

## Key Technical Details

### Data Processing Flow
1. **PDF Upload** → Classification (financial/long-format/generic) → Category-specific chunking → Vector storage
2. **Gmail Sync** → Email classification → Thread-aware processing → Separate vector indices
3. **Query Processing** → Multi-source search → Context assembly → LLM response generation

### Critical Environment Variables
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

# CORS (for Vercel frontend + local backend)
ALLOWED_ORIGINS=http://localhost:3000,https://your-vercel-app.vercel.app

# Frontend Environment (.env.local for Vercel)
NEXT_PUBLIC_API_URL=http://localhost:8000  # Local backend
NEXT_PUBLIC_APP_NAME=Personal AI Agent
```

### Data Storage Structure
- **PDF Documents**: `data/vector_db/{category}/user_{user_id}_doc_{filename}.{index|pkl}`
- **Email Messages**: `data/vector_db/emails/user_{user_id}_email_{source}_{id}.{index|pkl}`
- **User Uploads**: `data/uploads/{user_id}/`
- **Database**: SQLite (dev) / PostgreSQL (prod)

## Deployment Strategies

### Option 1: Single Executable Backend (RECOMMENDED - ✅ COMPLETED)
- **Use**: Desktop application deployment for end users
- **Frontend**: Next.js on Vercel (public, accessible to everyone) - https://personal-ai-agent-frontend.vercel.app
- **Backend**: Platform-specific executable with hybrid PostgreSQL/SQLite database (private, runs locally)
- **Database**: Hybrid system - PostgreSQL for development, SQLite for portable executables
- **User Experience**: Visit web → Register → Download → Install → Download models → Auto-connect
- **Benefits**: Complete privacy, no server setup, all data local, AI processing local, zero dependencies
- **Build System**: PyInstaller-based with progressive model downloading (~100MB initial + ~4GB models)

### Desktop Installer System (Feature Branch: desktop-installer)
**Status**: ✅ Complete - All 3 phases implemented and deployed

**Phase 1 - Enhanced Frontend Detection & Installation Flow**:
- Smart backend detection across multiple ports (8000, 8080, 3001, 5000, 8888)
- Three-state routing system: `available`, `installed-not-running`, `not-installed`
- Backend installer component with platform detection (Windows/macOS/Linux)
- Real-time installation monitoring and progress tracking
- Automatic backend discovery and connection after installation

**Phase 2 - Single Executable Backend Distribution**:
- Complete PyInstaller configuration with 500+ lines of optimized build script
- Hybrid database system supporting both PostgreSQL (dev) and SQLite (portable)
- Progressive model downloading system (separates executables from AI models)
- Platform-specific executable generation with cross-platform compatibility
- Portable database mode with WAL optimization and foreign key constraints

**Phase 3 - CI/CD Pipeline & Auto-Update System**:
- GitHub Actions CI/CD pipeline for automated cross-platform builds
- Matrix strategy building Windows (.exe), macOS (.app), and Linux (.AppImage) versions
- Auto-updater system with GitHub API integration and integrity verification
- Automated release management with platform-specific download links
- Code signing infrastructure for Windows and macOS distributions

**Implementation Files**:
- `build_executable.py` - PyInstaller configuration and build system
- `app/db/database_portable.py` - Hybrid PostgreSQL/SQLite database system
- `auto_updater.py` - GitHub API-based auto-update system with integrity checks
- `.github/workflows/build-executables.yml` - Complete CI/CD pipeline
- Frontend: Enhanced backend detection, installation guide, and status monitoring

### Option 2: Hybrid Development (PersonalAIAgent_frontend + Backend)
- **Use**: Modern UI development with local backend
- **Frontend**: Next.js deployed on Vercel (public)
- **Backend**: FastAPI deployed locally (private)
- **Setup**: Configure CORS for Vercel domain, local backend for privacy

### Option 3: Monolithic (Personal AI Agent)
- **Use**: Single server, development and testing
- **Frontend**: Legacy static frontend served by FastAPI
- **Access**: http://localhost:8000
- **Setup**: `cd "Personal AI Agent/backend" && python start_backend.py`

### Option 4: Development (Both Frontends)
- **Legacy**: http://localhost:8000 (backend serves static)
- **Modern**: http://localhost:3000 (npm run dev)
- **API**: Both connect to same FastAPI backend

## Important File Locations

### Backend Core Files
- **Entry Point**: `Personal AI Agent/backend/app/main.py`
- **Configuration**: `Personal AI Agent/backend/app/core/config.py`
- **Database Models**: `Personal AI Agent/backend/app/db/models.py`
- **API Endpoints**: `Personal AI Agent/backend/app/api/endpoints/`
- **Document Processing**: `Personal AI Agent/backend/app/utils/processors/`
- **Email Services**: `Personal AI Agent/backend/app/services/email/`
- **Vector Storage**: `Personal AI Agent/backend/app/services/vector_store_service.py`

### Frontend Implementations
- **Legacy Static**: `Personal AI Agent/backend/static/` (production-ready)
- **Modern Next.js**: `Personal AI Agent/frontend/` (in development)
- **Standalone Frontend**: `PersonalAIAgent_frontend/` (complete)
- **TypeScript Client**: `Personal AI Agent/backend/client/api-client.ts`

### Configuration Files
- **Backend Environment**: `Personal AI Agent/backend/.env`
- **Backend Dependencies**: `Personal AI Agent/backend/requirements.txt`
- **Frontend Dependencies**: `PersonalAIAgent_frontend/package.json`
- **Development Rules**: `Personal AI Agent/.cursor/rules/python.mdc`

## Key Dependencies

### Backend (Python)
- **FastAPI**: 0.115.12 - Web framework with OpenAPI and lifespan management
- **SQLAlchemy**: 2.0.41 - Database ORM with PostgreSQL support
- **LangChain**: 0.3.25 - LLM integration and document processing
- **FAISS**: 1.11.0 - Vector similarity search with category-aware indexing
- **llama-cpp-python**: 0.3.9 - Local LLM inference with Metal support
- **sentence-transformers**: 4.1.0 - Text embeddings (all-MiniLM-L6-v2)
- **Google APIs**: Gmail integration with OAuth2 and thread processing
- **PostgreSQL**: Primary database with connection pooling and performance indexes
- **JWT**: Authentication with bcrypt password hashing

### Frontend (Node.js)
- **Next.js**: 15.2.4 (PersonalAIAgent_frontend) / 14.0.3 (Personal AI Agent/frontend)
- **React**: 19 (PersonalAIAgent_frontend) / 18.2.0 (Personal AI Agent/frontend)
- **TypeScript**: 5+ - Type safety across all frontend implementations
- **Tailwind CSS**: 3.4+ - Utility-first styling with custom components
- **Radix UI**: Latest - Accessible component primitives via shadcn/ui
- **Custom API Client**: TypeScript client with JWT management and error handling

## Development Guidelines

### Code Quality
- **Python**: Follow PEP 8, use type hints, modular design
- **TypeScript**: Strict typing, proper error handling, async/await patterns
- **Security**: Environment-based config, no hardcoded secrets, input validation
- **Testing**: Unit tests for utilities, integration tests for API endpoints

### Architecture Principles
- **Privacy-first**: All AI processing local, no external LLM APIs
- **Modular design**: Separate concerns, testable components
- **Config-driven**: Environment variables for all settings
- **Error handling**: Comprehensive logging and user feedback

## Development Notes

### Quick Start Commands
```bash
# RECOMMENDED: Single executable backend (completed Phase 2)
# Build executable for desktop deployment
cd "Personal AI Agent/backend"
python build_executable.py --platform [windows|darwin|linux]
python create_installer_package.py --platform [windows|darwin|linux]

# Traditional development setup
cd "Personal AI Agent/backend" && python start_backend.py

# Hybrid deployment (Vercel frontend + local backend)
cd "Personal AI Agent/backend" && python main.py &
cd PersonalAIAgent_frontend/ && npm run dev

# Test specific functionality
python test_backend_connection.py
python test_email_search.py
python -m pytest tests/test_document_classifier.py
```

### Key Dependencies
- **Backend**: FastAPI 0.115.12, SQLAlchemy 2.0.41, LangChain 0.3.25, FAISS 1.11.0, llama-cpp-python 0.3.9
- **Frontend**: Next.js 15.2.4, React 19, TypeScript 5+, Tailwind CSS 3.4+, Radix UI

### Architecture Principles
- **Privacy-first**: All AI processing local (Mistral 7B), no external LLM APIs
- **Config-driven**: Environment variables control all settings
- **Modular design**: Separate processing strategies per document/email category
- **Multi-frontend**: Legacy static (production) + modern Next.js (Vercel deployment)

## Known Issues and Fixes

### Gmail Integration Issues (Jan 2025)
**Issue**: Gmail sync returns empty error responses causing frontend console errors:
- "API Error Response: {}" (lib/api.ts:189)
- "Server error. Please try again later." (lib/api.ts:227)

**Root Cause**: Import errors in `Personal AI Agent/backend/app/api/endpoints/gmail.py`:
- Imports from non-existent `app.exceptions` instead of `app.exceptions.email_exceptions`
- Exception handling failures result in HTTP 500 with empty JSON response bodies
- Background email processing (`_process_synced_emails`) lacks proper error handling

**Status**: Phase 1 completed - Import and error handling issues resolved

**Fix Plan**:
- **Phase 1** (✅ Completed): Fixed imports, ensured structured JSON error responses, added fallback handling
- **Phase 2**: Enhance Gmail service robustness and background processing
- **Phase 3**: Improve frontend error handling and user messaging  
- **Phase 4**: Add config validation and enhanced logging

**Files Affected**:
- `Personal AI Agent/backend/app/api/endpoints/gmail.py:31-40` - Import fixes needed
- `PersonalAIAgent_frontend/lib/api.ts:189,227` - Error handling locations
- `PersonalAIAgent_frontend/components/gmail-settings.tsx:105` - Sync trigger point

### Desktop Installer UX Issues (Jan 2025)
**Issue**: Critical UX problem where "Get Started" button led users to login page with "Backend is not available" errors when no backend was running, creating a poor first-time user experience.

**Root Cause**: Application routing didn't check backend availability before directing users to authentication, causing confusion and failed login attempts.

**Status**: ✅ Fixed - Enhanced routing system implemented

### GitHub Download URL Issues (Jan 2025)
**Issue**: Backend installer download buttons redirect to 404 "Not Found" GitHub URLs, preventing users from downloading the desktop application.

**Root Cause**: Hardcoded placeholder repository URLs in `backend-installer.tsx`:
- `https://github.com/your-username/personal-ai-agent/releases/latest/download/`
- GitHub API calls to non-existent repository
- No error handling for failed API calls

**Status**: ✅ Fixed - Environment-based repository configuration implemented

**Solution Implemented**:
- **Environment Variables**: Added `NEXT_PUBLIC_GITHUB_REPO_OWNER` and `NEXT_PUBLIC_GITHUB_REPO_NAME`
- **Dynamic URLs**: All GitHub links now use environment configuration
- **Error Handling**: Comprehensive fallback UI when GitHub API fails
- **Retry Mechanism**: Users can retry failed release fetches
- **Manual Fallback**: Direct links to GitHub releases page when automated downloads fail

**Technical Changes**:
- `components/backend-installer.tsx` - Environment-based repository configuration
- `.env.example` and `.env.local` - GitHub repository configuration  
- Enhanced error states with user guidance and retry options
- Updated to correct repository: `gitKnowsMe/PersonalAIAgent_backend`

**Current Status**: ✅ Fixed - Repository `gitKnowsMe/PersonalAIAgent_backend` exists and is public but has no releases yet.
**Next Steps**: Create first release tag (`v1.0.0`) to trigger CI/CD pipeline and publish executables.

**Solution Implemented**:
- **Smart Routing**: Added backend detection service with 3-second timeout optimization
- **State Management**: Implemented three-state system (available/installed-not-running/not-installed)
- **User Flow**: "Get Started" now checks backend status before routing to appropriate view
- **Error Prevention**: Users are guided through installation process before attempting authentication
- **Real-time Detection**: Added status monitoring with automatic updates when backend becomes available

**UX Improvements**:
- `components/backend-detection.tsx` - Fast backend status detection
- `lib/app-routing.ts` - Centralized routing logic based on backend availability
- `components/start-backend-guide.tsx` - Instructions when backend is installed but not running
- `app.tsx` - View-based routing system replacing boolean state management

**Result**: Eliminated connection errors and provided seamless installation guidance for new users.

### Development Rules (from .cursor/rules/python.mdc)
- **Modular Architecture**: Code must be structured for testability and maintainability
- **Security-first**: No hardcoded values - use environment variables and config files
- **Privacy-first**: All AI processing local (Mistral 7B), no external LLM APIs
- **Framework Standards**: Follow FastAPI, PostgreSQL, and local-first RAG best practices
- **Config-driven**: Avoid hardcoded values, support for runtime configuration changes

### Important Setup Notes
- **Gmail Setup**: Requires Google Cloud Console OAuth2 credentials in `.env`
- **Model Download**: Run `python download_model.py` before first use (downloads ~4GB Mistral model)
- **Database**: SQLite for development, PostgreSQL recommended for production
- **Privacy**: All AI processing happens locally, no data sent to external LLM services
- **CORS**: Configure `ALLOWED_ORIGINS` for Vercel frontend connecting to local backend
- **Metal**: Enable on macOS for LLM acceleration via `USE_METAL=true`

## Common Development Tasks

### Single Executable Backend Development
- **Frontend Changes**: Modify `PersonalAIAgent_frontend/` components and deploy to Vercel
- **Backend Detection**: Test multi-port scanning in `PersonalAIAgent_frontend/lib/api.ts`
- **Installation Flow**: Test download and installation process using `components/backend-installer.tsx`
- **Monitoring**: Use `hooks/use-backend-monitor.ts` for real-time backend status tracking
- **Platform Testing**: Verify platform detection and download links for Windows/macOS/Linux

### Working with Documents (Backend Development)
- **PDF Classification**: Files are automatically categorized into financial, long-format, or generic types in `app/utils/document_classifier.py`
- **Testing Classification**: Use `python test_classification_tags_fix.py` to verify document categorization
- **Vector Storage**: Documents stored in `data/vector_db/{category}/` with FAISS indices

### Working with Email Integration (Backend Development)
- **OAuth Setup**: Gmail credentials must be configured in `.env` before testing email features
- **Email Sync**: Use `python test_email_search.py` to verify Gmail integration and sync functionality
- **Thread Processing**: Email conversations are processed with context preservation via `app/services/email/`

### Debugging and Testing (Backend Development)
- **Single Test**: `python -m pytest tests/test_document_classifier.py::test_financial_classification`
- **Backend Health**: `python test_backend_connection.py` verifies API connectivity
- **Model Loading**: `python test_model_loading.py` checks Mistral 7B initialization
- **Performance**: `python test_performance_indexes.py` validates database indexing

### Database Operations (Backend Development)
- **Fresh Setup**: `python setup_db.py` initializes all tables and schema
- **Admin User**: `python create_admin.py` creates administrative user account
- **Performance**: `python migrate_add_performance_indexes.py` for production optimization

### Frontend-Backend Integration Testing
- **Connection Testing**: Verify frontend can detect backend across multiple ports
- **Installation Monitoring**: Test real-time installation progress tracking
- **Status Updates**: Verify backend status changes are reflected in frontend UI
- **Error Handling**: Test network failures, timeouts, and recovery mechanisms

## Key File Locations

### Core Backend Architecture
- **Main Entry**: `Personal AI Agent/backend/app/main.py:23` - FastAPI app with lifespan management
- **Configuration**: `Personal AI Agent/backend/app/core/config.py:41` - Settings class with environment validation
- **Database Models**: `Personal AI Agent/backend/app/db/models.py` - SQLAlchemy schema
- **API Routes**: `Personal AI Agent/backend/app/api/endpoints/` - REST endpoints
- **Document Processing**: `Personal AI Agent/backend/app/utils/processors/` - Category-specific processors
- **Vector Storage**: `Personal AI Agent/backend/app/services/vector_store_service.py` - FAISS operations

### Frontend Implementations
- **Standalone Frontend**: `PersonalAIAgent_frontend/lib/api.ts:140` - LocalBackendClient with multi-port detection
- **Legacy Frontend**: `Personal AI Agent/backend/static/` - Production-ready HTML/CSS/JS
- **Modern Frontend**: `Personal AI Agent/frontend/` - Next.js with TypeScript (in development)
- **API Client**: `Personal AI Agent/backend/client/api-client.ts` - TypeScript wrapper