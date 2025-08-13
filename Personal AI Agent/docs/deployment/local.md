# Local Development Setup

Complete guide for setting up Personal AI Agent for local development.

## Prerequisites

### System Requirements
- **Operating System**: macOS, Linux, or Windows
- **Python**: 3.8 or higher (3.9+ recommended)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 15GB free space for models and data
- **Network**: Internet connection for initial setup

### Development Tools
- Git for version control
- Code editor (VS Code, PyCharm, etc.)
- Terminal/command line access
- PDF viewer for testing document uploads

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/your-username/personal-ai-agent.git
cd personal-ai-agent
```

### 2. Python Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(fastapi|llama|faiss)"
```

### 4. Download AI Models
```bash
# Download LLM model (this may take time)
python download_model.py

# Download embedding model
python download_embedding_model.py

# Verify models
ls -la models/
```

### 5. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (see Configuration section below)
nano .env  # or your preferred editor
```

### 6. Database Setup
```bash
# Initialize database
python setup_db.py

# Create admin user
python create_admin.py

# Verify setup
python list_documents.py
```

## Configuration

### Basic Configuration (.env)
```env
# Server Settings
HOST=localhost
PORT=8000
DEBUG=true

# Database
DATABASE_URL=sqlite:///./personal_ai_agent.db

# Security
SECRET_KEY=your_development_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Settings
LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf
USE_METAL=true  # macOS only
METAL_N_GPU_LAYERS=1

# File Uploads
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./static/uploads

# Logging
LOG_LEVEL=DEBUG
```

### Gmail Integration (Optional)
```env
# Gmail OAuth (if using email features)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REDIRECT_URI=http://localhost:8000/api/v1/gmail/callback
```

## Running the Application

### Start Development Server
```bash
# Basic startup
python main.py

# Alternative with uvicorn
uvicorn app.main:app --host localhost --port 8000 --reload

# With specific environment
ENV=development python main.py
```

### Verify Installation
1. **Health Check**: Visit `http://localhost:8000/api/v1/health-check`
2. **Web Interface**: Open `http://localhost:8000`
3. **API Documentation**: Visit `http://localhost:8000/docs`

## Development Workflow

### Code Changes
1. Make code modifications
2. Server auto-reloads (with --reload flag)
3. Test changes in browser/API client
4. Run tests to verify functionality

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python test_model_loading.py

# Test document processing
python test_direct_question.py

# Test email functionality
python test_email_search.py
```

### Database Operations
```bash
# Reset database
rm personal_ai_agent.db
python setup_db.py

# Run migrations
python migrate_db.py

# View data
python list_documents.py
```

## Common Development Tasks

### Adding New Features
1. Create feature branch
2. Implement changes following architecture patterns
3. Add tests for new functionality
4. Update documentation
5. Test thoroughly

### Debugging
```bash
# Enable debug logging
# In .env: LOG_LEVEL=DEBUG

# Check logs
tail -f logs/app.log

# Test specific components
python test_model_loading.py
python test_config_system.py
```

## IDE Configuration

### VS Code Setup
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black"
}
```

### PyCharm Setup
1. Open project in PyCharm
2. Configure Python interpreter to `.venv/bin/python`
3. Set up run configuration for `main.py`
4. Configure debugger for FastAPI

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Use different port
PORT=8001 python main.py
```

**Model Loading Issues**
```bash
# Check model files
ls -la models/

# Test model loading
python test_model_loading.py

# Re-download if corrupted
rm -rf models/
python download_model.py
```

**Database Problems**
```bash
# Reset database
rm personal_ai_agent.db
python setup_db.py

# Check database integrity
sqlite3 personal_ai_agent.db "PRAGMA integrity_check;"
```

## Performance Optimization

### Development Performance
- Use SSD storage for better I/O
- Allocate sufficient RAM (8GB+)
- Enable hardware acceleration when available
- Close unnecessary applications

### Code Performance
- Use profiling tools to identify bottlenecks
- Monitor memory usage during development
- Test with realistic data volumes
- Optimize database queries

*This local setup guide provides the foundation for Personal AI Agent development. For production deployment, see the Production Deployment guide.*