# Troubleshooting Guide

## Frontend Shows "Setup Your Personal AI" Page

### Problem
Your frontend is showing the "Setup Your Personal AI" page instead of the main application interface.

### Root Cause
The frontend cannot detect that the backend is running. This happens when:
1. **Backend is not running** (most common)
2. **Backend is not accessible** on the expected URL
3. **Frontend is checking wrong endpoint** for backend detection
4. **CORS issues** preventing frontend from accessing backend

### Solution Steps

#### 1. Check if Backend is Running
```bash
# Navigate to backend directory
cd backend/

# Check if backend process is running
ps aux | grep -E "python.*main.py|uvicorn.*main" | grep -v grep

# Test backend connectivity
python test_backend_connection.py
```

#### 2. Start the Backend
```bash
# Recommended: Use the startup script
python start_backend.py

# Or start manually
python main.py
```

#### 3. Verify Backend Endpoints
Once backend is running, test these URLs in your browser:

- **Main API**: http://localhost:8000/
  - Should return JSON with `backend_installed: true`
- **Backend Status**: http://localhost:8000/api/backend-status
  - Should return JSON with `backend_running: true`
- **Health Check**: http://localhost:8000/api/health-check
  - Should return JSON with `status: "ok"`

#### 4. Frontend Detection Logic
Update your frontend to check for backend using these endpoints:

```typescript
// Frontend detection logic
const detectBackend = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/backend-status');
    const data = await response.json();
    
    if (data.backend_installed && data.backend_running && data.ready) {
      return { detected: true, data };
    }
    
    return { detected: false, error: 'Backend not ready' };
  } catch (error) {
    return { detected: false, error: error.message };
  }
};
```

#### 5. CORS Configuration
If backend is running but frontend still can't access it, check CORS:

```bash
# Check your .env file for CORS settings
grep ALLOWED_ORIGINS .env

# Should include your frontend domain
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Gmail Connection Issues

### Problem
Gmail connection fails with various error messages.

### Solution
```bash
# Run the Gmail validation script
python validate_email_connection.py

# Fix any namespace issues
python fix_email_namespaces.py
```

### Common Gmail Issues

1. **Missing OAuth Credentials**
   - Error: "GMAIL_CLIENT_ID is required"
   - Solution: Set up Google Cloud Console OAuth credentials

2. **OAuth Session Expired**
   - Error: "oauth_session_expired"
   - Solution: Restart the OAuth flow

3. **Token Refresh Failed**
   - Error: "Token refresh failed"
   - Solution: Reconnect Gmail account

## Database Issues

### Problem
Database connection errors or missing tables.

### Solution
```bash
# Setup database
python setup_db.py

# Check database integrity
python -c "
from app.db.database import get_db
db = next(get_db())
print('Database connection successful!')
db.close()
"
```

## Model Loading Issues

### Problem
"LLM model file not found" or model loading errors.

### Solution
```bash
# Download models
python download_model.py
python download_embedding_model.py

# Verify model path in .env
grep LLM_MODEL_PATH .env
```

## Port Already in Use

### Problem
"Port 8000 is already in use" error.

### Solution
```bash
# Kill existing process
pkill -f "uvicorn.*main"

# Or use different port
uvicorn app.main:app --host localhost --port 8001 --reload
```

## Dependencies Issues

### Problem
ImportError or missing dependencies.

### Solution
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check virtual environment
which python
pip list
```

## Debugging Steps

### 1. Check Logs
```bash
# View application logs
tail -f logs/app.log

# Check for error patterns
grep -i error logs/app.log
```

### 2. Test Individual Components
```bash
# Test database
python -c "from app.db.database import get_db; next(get_db())"

# Test models
python -c "from app.utils.llm import get_llm_model; get_llm_model()"

# Test Gmail service
python -c "from app.services.gmail_service import GmailService; GmailService()"
```

### 3. Environment Check
```bash
# Check environment variables
env | grep -E "(GMAIL|DATABASE|LLM)"

# Verify file permissions
ls -la .env
ls -la models/
```

## Frontend-Backend Communication

### Common Issues

1. **Wrong API URL**
   - Frontend: `NEXT_PUBLIC_API_URL=http://localhost:8000`
   - Backend: Should be running on port 8000

2. **Authentication Issues**
   - Ensure JWT tokens are properly managed
   - Check token expiration

3. **CORS Problems**
   - Backend CORS should include frontend origin
   - Check preflight requests in browser dev tools

### Testing Communication
```bash
# Test API endpoints
curl -X GET http://localhost:8000/
curl -X GET http://localhost:8000/api/health-check
curl -X GET http://localhost:8000/api/backend-status

# Test with authentication
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password"}'
```

## Getting Help

### 1. Check System Status
```bash
# Run comprehensive check
python validate_email_connection.py

# Test backend connection
python test_backend_connection.py

# Check configuration
python -c "from app.core.config import settings; print(f'API: {settings.API_V1_STR}')"
```

### 2. Enable Debug Mode
```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG

# Restart backend to see detailed logs
python start_backend.py
```

### 3. Common Resolution Steps
1. **Stop all processes**: `pkill -f "uvicorn|python.*main"`
2. **Clear browser cache**: Hard refresh your frontend
3. **Restart backend**: `python start_backend.py`
4. **Check network**: Ensure no firewall blocking localhost:8000
5. **Test endpoints**: Use curl or browser to verify API responses

### 4. Create Minimal Test
```bash
# Test basic FastAPI
python -c "
import uvicorn
from fastapi import FastAPI
app = FastAPI()
@app.get('/')
def root():
    return {'status': 'test'}
uvicorn.run(app, host='localhost', port=8001)
"
```

This should help you identify and resolve the "Setup Your Personal AI" issue and other common problems.