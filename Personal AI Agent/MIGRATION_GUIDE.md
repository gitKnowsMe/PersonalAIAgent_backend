# Migration Guide: Current Structure → Monorepo

This guide helps you transition from the current Personal AI Agent structure to the new monorepo architecture for hybrid deployment.

## 🎯 Migration Overview

**From**: Single repository with mixed frontend/backend
**To**: Monorepo with clear frontend/backend separation

## 📋 Pre-Migration Checklist

### 1. Backup Current Setup
```bash
# Backup your data
cp -r data/ data_backup_$(date +%Y%m%d)
cp -r static/uploads/ uploads_backup_$(date +%Y%m%d)
cp .env .env.backup

# Backup database
cp personal_ai_agent.db personal_ai_agent_backup_$(date +%Y%m%d).db

# Create git backup branch
git checkout -b backup-before-monorepo
git add .
git commit -m "Backup before monorepo migration"
git checkout main
```

### 2. Document Current Configuration
```bash
# Note your current settings
cat .env > migration_notes.txt
echo "Current Python packages:" >> migration_notes.txt
pip freeze >> migration_notes.txt
```

## 🔄 Migration Steps

### Step 1: Create New Monorepo Structure

```bash
# Create new directories
mkdir -p frontend/{src,public}
mkdir -p backend/{app,scripts,tests,data,models,logs,static}
mkdir -p docs/{getting-started,deployment,api,development,user-guide}
mkdir -p .github/{workflows,ISSUE_TEMPLATE}
mkdir -p scripts

# Create placeholder files to maintain structure
touch frontend/README.md
touch backend/README.md
touch docs/README.md
```

### Step 2: Move Backend Code

```bash
# Move all app code to backend/
mv app/ backend/
mv *.py backend/  # All Python files like main.py, setup_db.py, etc.
mv requirements.txt backend/

# Move data directories
mv data/ backend/
mv static/ backend/
mv logs/ backend/
mv models/ backend/

# Move test files to backend/tests/
mkdir -p backend/tests
mv test_*.py backend/tests/
mv tests/ backend/tests/ 2>/dev/null || true
```

### Step 3: Update Backend Structure

```bash
cd backend

# Create symlink for backward compatibility
ln -s app/main.py main.py

# Update import paths in Python files (if needed)
# This may require manual editing of some files

# Ensure environment file is in backend/
mv ../.env . 2>/dev/null || cp ../.env.example .env.example
```

### Step 4: Create Frontend Structure

```bash
cd frontend

# Initialize Next.js project
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Or manually create structure if you prefer
mkdir -p src/{app,components,lib,hooks,styles}
mkdir -p src/components/{ui,chat,documents,layout,common}
mkdir -p src/app/{auth,chat,documents,settings}
```

### Step 5: Update Configuration Files

#### Root `.gitignore`
```gitignore
# Dependencies
node_modules/
backend/.venv/
backend/__pycache__/

# Environment files
.env
.env.local
.env.production
.env.development
backend/.env

# Database
backend/data/app.db
backend/personal_ai_agent.db

# Models (too large for git)
backend/models/*.gguf
backend/models/all-MiniLM-L6-v2/

# Uploads and generated files
backend/static/uploads/
backend/static/emails/
backend/logs/*.log
backend/data/vector_db/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Build outputs
frontend/.next/
frontend/out/
frontend/dist/
backend/dist/
backend/build/

# Vercel
.vercel

# Testing
coverage/
.nyc_output
.coverage
pytest_cache/
```

#### Update `backend/app/core/config.py`
```python
# Update BASE_DIR to account for new structure
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Update paths
STATIC_DIR: str = str(BASE_DIR / "static")
UPLOAD_DIR: str = str(BASE_DIR / "static" / "uploads")
VECTOR_DB_PATH: str = str(BASE_DIR / "data" / "vector_db")
LOG_FILE: str = str(BASE_DIR / "logs" / "app.log")
```

### Step 6: Create Setup Scripts

```bash
# Copy the setup script we created
cp scripts/quick-start.sh .

# Create backend-specific setup script
cat > backend/scripts/setup.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python download_model.py
python download_embedding_model.py
python setup_db.py
EOF

chmod +x backend/scripts/setup.sh
```

### Step 7: Test Migration

```bash
# Test backend setup
cd backend
./scripts/setup.sh

# Test backend startup
source .venv/bin/activate
python main.py

# In another terminal, test API
curl http://localhost:8000/api/health-check
```

## 🔧 Post-Migration Tasks

### 1. Update Documentation

Create new documentation structure:
```bash
# Move existing docs
mv *.md docs/ 2>/dev/null || true

# Create new README files
cat > README.md << 'EOF'
# Personal AI Agent

A privacy-first AI assistant with hybrid deployment architecture.

## Quick Start

```bash
./scripts/quick-start.sh
```

See [HYBRID_DEPLOYMENT.md](./HYBRID_DEPLOYMENT.md) for detailed setup.
EOF
```

### 2. Update CORS Configuration

```python
# In backend/app/core/config.py
ALLOWED_ORIGINS: list = [
    "https://your-vercel-app.vercel.app",  # Production frontend
    "http://localhost:3000",               # Local frontend dev
    "http://127.0.0.1:3000",              # Alternative localhost
]
```

### 3. Create Frontend API Client

```typescript
// frontend/src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiClient {
  // ... (implementation from hybrid_deployment.md)
}
```

### 4. Set Up Vercel Deployment

```json
// frontend/vercel.json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "env": {
    "NEXT_PUBLIC_API_URL": "http://localhost:8000"
  }
}
```

## 📊 Verification Checklist

After migration, verify:

- [ ] Backend starts successfully: `cd backend && python main.py`
- [ ] API endpoints respond: `curl http://localhost:8000/api/health-check`
- [ ] Database is accessible: Check your existing documents
- [ ] Models are loaded: Check logs for model loading messages
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] Environment variables work: Check `.env` files
- [ ] File uploads work: Test document upload
- [ ] Gmail integration works: Test email sync (if configured)

## 🐛 Common Migration Issues

### Issue 1: Import Path Errors
```bash
# Fix Python import paths
find backend/ -name "*.py" -exec sed -i 's/from app\./from backend.app./g' {} \;
```

### Issue 2: Missing Dependencies
```bash
# Reinstall dependencies
cd backend
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue 3: Database Path Issues
```python
# Update database URL in backend/.env
DATABASE_URL=sqlite:///./data/personal_ai_agent.db
```

### Issue 4: Model Path Issues
```python
# Update model paths in backend/.env
LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
```

## 🔄 Rollback Plan

If migration fails, you can rollback:

```bash
# Return to backup branch
git checkout backup-before-monorepo

# Restore data backups
cp -r data_backup_* data/
cp -r uploads_backup_* static/uploads/
cp .env.backup .env
cp personal_ai_agent_backup_*.db personal_ai_agent.db

# Restart with original structure
python main.py
```

## 🚀 Next Steps After Migration

1. **Deploy Frontend**: Push to GitHub and deploy to Vercel
2. **Test Hybrid Setup**: Verify frontend connects to local backend
3. **Update Documentation**: Customize docs for your setup
4. **Configure CI/CD**: Set up automated testing and deployment
5. **Share with Users**: Provide updated setup instructions

## 📞 Support

If you encounter issues during migration:

1. Check the troubleshooting section in `docs/troubleshooting.md`
2. Review the backup you created before migration
3. Create an issue on GitHub with migration details
4. Join the community Discord for real-time help

The monorepo structure provides a much cleaner development experience and makes the hybrid deployment strategy much more intuitive for end users.