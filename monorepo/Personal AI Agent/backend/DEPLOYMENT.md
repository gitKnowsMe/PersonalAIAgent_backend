# Personal AI Agent Backend - Deployment Guide

## 🚀 Deployment Overview

This backend is designed for **hybrid deployment** where the frontend runs from a separate repository while the backend provides API services. The backend supports multiple deployment strategies and environments.

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+ (production)
- LLM model files (Mistral 7B)
- Gmail OAuth credentials
- SSL certificates (production)

## 🔧 Environment Configuration

### Development Environment
```bash
# Use development environment
cp .env.development .env

# Install dependencies
pip install -r requirements.txt

# Download LLM model
python download_model.py

# Start development server
python main.py
```

### Production Environment
```bash
# Use production environment
cp .env.production .env

# Edit production variables
nano .env

# Required production variables:
# - DATABASE_URL (PostgreSQL)
# - ALLOWED_ORIGINS (your frontend domain)
# - GMAIL_CLIENT_ID/SECRET (production OAuth app)
# - SECRET_KEY (generate strong key)
```

## 🐳 Docker Deployment

### Quick Start
```bash
# Build and run with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Production Docker Setup
```bash
# 1. Configure environment
cp .env.production .env
nano .env

# 2. Ensure model files are available
mkdir -p models/
# Copy your LLM model files to models/

# 3. Build and deploy
docker-compose -f docker-compose.yml up -d

# 4. Setup SSL (if using nginx)
# Place SSL certificates in ./ssl/
```

## 🌐 Deployment Options

### 1. Self-Hosted VPS
**Recommended for privacy-focused deployments**

```bash
# On your VPS
git clone <your-backend-repo>
cd backend/

# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.production .env
nano .env

# Install system service
sudo cp systemd/personal-ai-agent.service /etc/systemd/system/
sudo systemctl enable personal-ai-agent
sudo systemctl start personal-ai-agent
```

### 2. Cloud VM (AWS/GCP/Azure)
```bash
# Use cloud-init or startup scripts
# Same as VPS setup + cloud-specific configurations
```

### 3. Container Platform (Docker)
```bash
# Use provided Dockerfile and docker-compose.yml
# Modify volumes and networking as needed
```

## 🔐 Security Configuration

### SSL/TLS Setup
```bash
# Generate SSL certificates (Let's Encrypt)
certbot certonly --nginx -d api.yourdomain.com

# Update nginx.conf with SSL configuration
```

### Environment Variables
```env
# Production security settings
SECRET_KEY=your-256-bit-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_ORIGINS=https://yourdomain.com
```

### Database Security
```sql
-- Create dedicated database user
CREATE USER personal_ai_agent WITH ENCRYPTED PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE personal_ai_agent TO personal_ai_agent;
```

## 🔄 Frontend Integration

### CORS Configuration
The backend is configured for cross-origin requests from your frontend domain:

```python
# In .env file
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### API Endpoints
All endpoints are prefixed with `/api/v1`:
- `POST /api/v1/login` - Authentication
- `GET /api/v1/documents` - Document management
- `POST /api/v1/queries` - AI queries
- `GET /api/v1/gmail/accounts` - Gmail integration
- `GET /api/v1/health-check` - Health monitoring

### Authentication Flow
1. Frontend sends credentials to `/api/v1/login`
2. Backend returns JWT token
3. Frontend includes token in `Authorization: Bearer <token>` header
4. Backend validates token for protected routes

## 📊 Monitoring & Logging

### Health Checks
```bash
# Check API health
curl http://localhost:8000/api/v1/health-check

# Check with Docker
docker-compose exec backend curl http://localhost:8000/api/v1/health-check
```

### Logging
Logs are stored in `/app/logs/app.log` (container) or `./logs/app.log` (local):
```bash
# View logs
tail -f logs/app.log

# With Docker
docker-compose logs -f backend
```

### Performance Monitoring
```bash
# Monitor resource usage
docker stats

# Check database connections
docker-compose exec db psql -U postgres -d personal_ai_agent -c "SELECT * FROM pg_stat_activity;"
```

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**
   ```bash
   # Check ALLOWED_ORIGINS in .env
   # Ensure no trailing slashes in URLs
   ```

2. **Database Connection Issues**
   ```bash
   # Check DATABASE_URL format
   # Ensure PostgreSQL is running
   docker-compose logs db
   ```

3. **Model Loading Issues**
   ```bash
   # Check LLM_MODEL_PATH
   # Ensure model files are accessible
   ls -la models/
   ```

4. **Gmail OAuth Issues**
   ```bash
   # Check OAuth credentials
   # Verify redirect URI matches frontend
   ```

## 📝 Maintenance

### Updates
```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart personal-ai-agent
# OR
docker-compose restart backend
```

### Database Migrations
```bash
# Run migrations
python migrate_db.py

# Backup before major updates
pg_dump personal_ai_agent > backup.sql
```

### Model Updates
```bash
# Update LLM model
python download_model.py

# Restart to load new model
sudo systemctl restart personal-ai-agent
```

## 🔗 Integration with Frontend

### Frontend Repository Setup
The frontend should be configured to connect to this backend:

```javascript
// Frontend environment configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
```

### API Client Library
Use the provided TypeScript client for seamless integration:
```typescript
import { PersonalAIClient } from './lib/api-client';

const client = new PersonalAIClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000
});
```

## 📖 Additional Resources

- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Frontend Integration Guide](./docs/frontend-integration.md)
- [Security Guidelines](./docs/security.md)
- [Performance Optimization](./docs/performance.md)

---

For more deployment help, check the [troubleshooting guide](./docs/troubleshooting.md) or open an issue in the repository.