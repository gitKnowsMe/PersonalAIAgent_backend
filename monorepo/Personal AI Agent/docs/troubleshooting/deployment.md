# Deployment Troubleshooting Guide

This guide covers common deployment issues and their solutions for the Personal AI Agent system.

## Prerequisites Check

Before deploying, ensure all prerequisites are met:

### Backend Requirements
- ✅ PostgreSQL 12+ installed and running
- ✅ Python 3.8+ with virtual environment
- ✅ All dependencies installed (`pip install -r requirements.txt`)
- ✅ Environment variables configured in `.env`
- ✅ Gmail OAuth credentials (if using email features)
- ✅ AI models downloaded (`python download_model.py`)

### Frontend Requirements
- ✅ Node.js 18+ installed
- ✅ Dependencies installed (`npm install`)
- ✅ Environment variables configured in `.env.local`
- ✅ Backend URL properly set (`NEXT_PUBLIC_API_URL`)

## Common Issues & Solutions

### 1. Database Connection Issues

#### Problem: `psycopg2.OperationalError: connection failed`

**Symptoms:**
```
PostgreSQL connection failed: connection to server at "localhost", port 5432 failed
```

**Solutions:**
1. **Check PostgreSQL is running:**
   ```bash
   # macOS (Homebrew)
   brew services start postgresql
   
   # Ubuntu/Debian
   sudo systemctl start postgresql
   
   # Check status
   pg_isready -h localhost -p 5432
   ```

2. **Verify database exists:**
   ```bash
   psql -h localhost -U personal_ai_agent -d personal_ai_agent_dev
   ```

3. **Run setup script:**
   ```bash
   python setup_postgresql.py
   ```

4. **Check environment variables:**
   ```bash
   echo $DATABASE_URL
   # Should be: postgresql://personal_ai_agent:dev_password@localhost:5432/personal_ai_agent_dev
   ```

#### Problem: `relation "users" does not exist`

**Solution:**
```bash
python setup_db.py
```

### 2. Authentication Issues

#### Problem: `Invalid Gmail OAuth credentials`

**Symptoms:**
```
ValueError: GMAIL_CLIENT_ID must be changed from placeholder value
```

**Solutions:**
1. **Set up Google OAuth2 credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Add redirect URI: `http://localhost:8000/api/gmail/callback`

2. **Update `.env` file:**
   ```bash
   GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=GOCSPX-your_client_secret
   GMAIL_REDIRECT_URI=http://localhost:8000/api/gmail/callback
   ```

#### Problem: `Could not validate credentials` (JWT errors)

**Solutions:**
1. **Check SECRET_KEY in `.env`:**
   ```bash
   # Generate new secret key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Clear browser cookies/localStorage**

3. **Restart backend server**

### 3. Model Loading Issues

#### Problem: `FileNotFoundError: LLM model not found`

**Solutions:**
1. **Download models:**
   ```bash
   python download_model.py
   python download_embedding_model.py
   ```

2. **Check model path in `.env`:**
   ```bash
   LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
   ```

3. **Verify file exists:**
   ```bash
   ls -la models/
   ```

#### Problem: `Metal acceleration not working` (macOS)

**Solutions:**
1. **Check Metal support:**
   ```bash
   # In Python
   import llama_cpp
   print(llama_cpp.llama_supports_mlock())
   ```

2. **Update environment:**
   ```bash
   USE_METAL=true
   METAL_N_GPU_LAYERS=1
   ```

3. **Reinstall with Metal support:**
   ```bash
   pip uninstall llama-cpp-python
   CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
   ```

### 4. Frontend Deployment Issues

#### Problem: `Cannot connect to backend API`

**Symptoms:**
- Frontend shows "Backend connection failed"
- API calls return CORS errors

**Solutions:**
1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/api/health-check
   ```

2. **Update frontend environment:**
   ```bash
   # .env.local
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Configure CORS in backend `.env`:**
   ```bash
   ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000
   ```

#### Problem: `Build fails with TypeScript errors`

**Solutions:**
1. **Run type check:**
   ```bash
   npm run type-check
   ```

2. **Fix TypeScript errors or temporarily disable:**
   ```javascript
   // next.config.mjs
   typescript: {
     ignoreBuildErrors: false  // Should be false for production
   }
   ```

### 5. Vercel Deployment Issues

#### Problem: `Environment variables not found`

**Solution:**
Set environment variables in Vercel dashboard:
```
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
NEXT_PUBLIC_APP_NAME=Personal AI Agent
```

#### Problem: `API routes returning 404`

**Solution:**
Ensure API routes are properly configured and Next.js app is using App Router.

### 6. Performance Issues

#### Problem: `Slow response times`

**Solutions:**
1. **Enable caching:**
   ```python
   # Backend automatically uses TTL caching
   # Check cache hit rates in logs
   ```

2. **Optimize database:**
   ```bash
   # Run performance index migration
   python migrate_add_performance_indexes.py
   ```

3. **Check connection pooling:**
   ```python
   # Database settings in config.py
   pool_size=10
   max_overflow=20
   ```

#### Problem: `High memory usage`

**Solutions:**
1. **Limit model context:**
   ```bash
   LLM_CONTEXT_WINDOW=4096  # Reduce if needed
   ```

2. **Enable model quantization:**
   ```bash
   # Use Q4_K_M model (default)
   # Or download Q4_0 for lower memory usage
   ```

## Health Check Commands

### Backend Health
```bash
# Basic connection
python test_backend_connection.py

# PostgreSQL
python test_postgresql_final.py

# Multi-user features
python test_multi_user_scenarios.py

# Document classification
python -m pytest tests/test_document_classifier.py
```

### Frontend Health
```bash
# Local development
npm run dev

# Production build
npm run build
npm run start

# Health check
npm run health-check

# Type checking
npm run type-check
```

## Monitoring & Logs

### Backend Logs
```bash
# Application logs
tail -f logs/app.log

# Error logs
tail -f logs/errors/errors.log

# Audit logs
tail -f logs/audit/audit.log
```

### Database Monitoring
```bash
# PostgreSQL logs (macOS)
tail -f /usr/local/var/log/postgresql/*.log

# Connection count
SELECT count(*) FROM pg_stat_activity WHERE datname = 'personal_ai_agent_dev';

# Performance stats
SELECT * FROM pg_stat_database WHERE datname = 'personal_ai_agent_dev';
```

## Production Deployment Checklist

### Backend Production Setup
- [ ] PostgreSQL production database configured
- [ ] Environment variables set (no defaults)
- [ ] `DEBUG=false` in production
- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured
- [ ] Log rotation enabled
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured

### Frontend Production Setup
- [ ] Environment variables set in Vercel
- [ ] Custom domain configured (optional)
- [ ] CORS origins properly configured
- [ ] Error monitoring enabled
- [ ] Performance monitoring enabled
- [ ] CDN optimization enabled

### Security Checklist
- [ ] Strong SECRET_KEY generated
- [ ] Database credentials secured
- [ ] OAuth credentials secured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Admin accounts secured
- [ ] Audit logging enabled

## Emergency Recovery

### Database Recovery
```bash
# Backup
pg_dump -h localhost -U personal_ai_agent personal_ai_agent_dev > backup.sql

# Restore
psql -h localhost -U personal_ai_agent personal_ai_agent_dev < backup.sql

# Reset to clean state
python setup_postgresql.py
python setup_db.py
python create_admin.py
```

### Reset to Known Good State
```bash
# Backend
git checkout main
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup_postgresql.py
python setup_db.py

# Frontend
git checkout main
npm install
npm run build
```

## Getting Help

### Log Analysis
1. Check application logs for specific error messages
2. Check database logs for connection issues
3. Check browser console for frontend errors
4. Use health check scripts for automated diagnosis

### Community Support
- Check GitHub issues for similar problems
- Review documentation for configuration examples
- Use health check tools for automated diagnosis

### Escalation Path
1. Run all health check scripts
2. Collect relevant log files
3. Document reproduction steps
4. Create detailed issue report with environment info