# Common Issues and Solutions

This guide addresses the most frequently encountered issues and their solutions.

## Installation Issues

### Python Version Problems

**Issue**: "Python version not supported"
```bash
python: command not found
# or
Python 3.7.x is not supported
```

**Solutions**:
```bash
# Check Python version
python --version
python3 --version

# Install Python 3.8+ on macOS
brew install python@3.9

# Install Python 3.8+ on Ubuntu
sudo apt update
sudo apt install python3.9 python3.9-venv

# Use specific Python version
python3.9 -m venv .venv
```

### Virtual Environment Issues

**Issue**: "Cannot activate virtual environment"
```bash
bash: .venv/bin/activate: No such file or directory
```

**Solutions**:
```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv

# Windows activation
.venv\Scripts\activate

# Linux/macOS activation
source .venv/bin/activate

# Verify activation
which python
```

### Dependency Installation Failures

**Issue**: "Failed building wheel for package"
```bash
ERROR: Failed building wheel for llama-cpp-python
```

**Solutions**:
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Install build dependencies on macOS
xcode-select --install
brew install cmake

# Install build dependencies on Ubuntu
sudo apt install build-essential cmake

# For specific packages
pip install --no-cache-dir llama-cpp-python
```

## Model Loading Issues

### Model Download Failures

**Issue**: "Model download failed or corrupted"
```bash
ConnectionError: Failed to download model
# or
OSError: Unable to load model file
```

**Solutions**:
```bash
# Check internet connection
ping huggingface.co

# Clear and re-download
rm -rf models/
python download_model.py

# Manual download verification
ls -la models/
file models/mistral-7b-instruct-v0.1.Q4_K_M.gguf

# Test model loading
python test_model_loading.py
```

### Memory Issues with Models

**Issue**: "Insufficient memory to load model"
```bash
RuntimeError: CUDA out of memory
# or
MemoryError: Unable to allocate memory
```

**Solutions**:
```bash
# Check available memory
free -h  # Linux
vm_stat | perl -ne '/page size of (\d+)/ and $size=$1; /Pages\s+([^:]+)[^\d]+(\d+)/ and printf("%-16s % 16.2f MB\n", "$1:", $2 * $size / 1048576);'  # macOS

# Use smaller model
python switch_model.py
# Select phi-2 instead of mistral-7b

# Reduce Metal layers (macOS)
# In .env file:
METAL_N_GPU_LAYERS=0
USE_METAL=false

# Reduce context window
LLM_CONTEXT_WINDOW=4096
```

### Metal/GPU Acceleration Issues

**Issue**: "Metal acceleration not working"
```bash
Warning: Metal not available, falling back to CPU
```

**Solutions**:
```bash
# Check macOS version (requires macOS 12+)
sw_vers

# Verify Metal support
system_profiler SPDisplaysDataType

# Update configuration
# In .env:
USE_METAL=true
METAL_N_GPU_LAYERS=1

# Test Metal functionality
python test_mistral_model.py
```

## Database Issues

### Database Connection Errors

**Issue**: "Cannot connect to database"
```bash
sqlalchemy.exc.OperationalError: no such table
# or
sqlite3.OperationalError: database is locked
```

**Solutions**:
```bash
# Reset database
rm personal_ai_agent.db
python setup_db.py

# Check database file permissions
ls -la personal_ai_agent.db
chmod 644 personal_ai_agent.db

# Test database connection
python -c "from app.db.database import engine; print(engine.url)"

# Run database migrations
python migrate_db.py
```

### Migration Failures

**Issue**: "Database migration failed"
```bash
sqlalchemy.exc.IntegrityError: UNIQUE constraint failed
```

**Solutions**:
```bash
# Check current schema
python list_documents.py

# Run specific migrations
python migrate_db_constraints.py
python migrate_email_db.py

# Backup and reset if needed
cp personal_ai_agent.db personal_ai_agent.db.backup
rm personal_ai_agent.db
python setup_db.py
```

## PDF Processing Issues

### Upload Failures

**Issue**: "PDF upload fails"
```bash
HTTP 422: Invalid file type
# or
HTTP 413: File too large
```

**Solutions**:
```bash
# Check file type
file document.pdf

# Check file size
ls -lh document.pdf

# Compress PDF if too large
# Use PDF compression tools or split document

# Verify PDF structure
python -c "import pypdf; pypdf.PdfReader('document.pdf')"

# Test with sample document
python test_bank_only.py
```

### Text Extraction Issues

**Issue**: "No text extracted from PDF"
```bash
Warning: Document contains no extractable text
```

**Solutions**:
```bash
# Check if PDF is text-based
# Try selecting text in PDF viewer

# For scanned documents, use OCR first
# Install tesseract
brew install tesseract  # macOS
sudo apt install tesseract-ocr  # Ubuntu

# Convert scanned PDF to text-based
# Use tools like Adobe Acrobat or online OCR

# Test extraction manually
python -c "
import pypdf
reader = pypdf.PdfReader('document.pdf')
print(reader.pages[0].extract_text())
"
```

### Classification Issues

**Issue**: "Document classified incorrectly"
```bash
Warning: Low classification confidence (0.45)
```

**Solutions**:
```bash
# Classification is automatic and cannot be manually overridden
# Processing will work regardless of classification

# Test classification manually
python debug_chunks_detail.py

# Verify document processing
python test_classification_tags_fix.py

# Check if document has mixed content
# Financial + long-form content may confuse classifier
```

## Gmail Integration Issues

### OAuth Setup Problems

**Issue**: "OAuth2 authorization fails"
```bash
HTTP 400: invalid_client
# or
HTTP 403: access_denied
```

**Solutions**:
```bash
# Verify Google Cloud Console setup
# 1. Gmail API is enabled
# 2. OAuth2 credentials created
# 3. Redirect URI matches exactly

# Check environment variables
echo $GMAIL_CLIENT_ID
echo $GMAIL_CLIENT_SECRET
echo $GMAIL_REDIRECT_URI

# Verify redirect URI format
# Must be: http://localhost:8000/api/v1/gmail/callback

# Test OAuth flow
python setup_gmail.py
```

### Email Sync Issues

**Issue**: "Email sync fails or times out"
```bash
HTTP 429: Rate limit exceeded
# or
TimeoutError: Request timed out
```

**Solutions**:
```bash
# Reduce batch size
curl -X POST "http://localhost:8000/api/v1/gmail/sync" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"limit": 50}'

# Wait for rate limit reset (usually 1 hour)
# Check Gmail API quotas in Google Cloud Console

# Use more specific queries
curl -X POST "http://localhost:8000/api/v1/gmail/sync" \
  -d '{"limit": 100, "query": "in:inbox after:2024/01/01"}'

# Test connection
python test_email_search.py
```

### Email Classification Issues

**Issue**: "Emails classified incorrectly"
```bash
Business emails showing as promotional
```

**Solutions**:
```bash
# Email classification is automatic
# System learns from patterns over time

# Verify large sample for accuracy
python test_classification_tags_fix.py

# Check specific email content
python debug_email_sync_error.py

# Classification affects search optimization but not functionality
```

## Query and Search Issues

### No Results Found

**Issue**: "Queries return no results"
```bash
"No relevant content found for the query"
```

**Solutions**:
```bash
# Verify documents are processed
python list_documents.py

# Check document processing status
# Ensure status is "completed"

# Try broader search terms
"apple" instead of "apple store purchase"

# Test with known content
python test_direct_question.py

# Check vector store integrity
python test_api_query.py
```

### Poor Result Quality

**Issue**: "Search results not relevant"
```bash
Low relevance scores or incorrect answers
```

**Solutions**:
```bash
# Be more specific in queries
"Apple transactions in March 2024" 
# instead of "Apple stuff"

# Include document context
"From my bank statement, find Apple purchases"

# Check source attribution
# Verify results cite correct documents

# Test hallucination prevention
python test_hallucination_prevention.py
```

### Response Generation Issues

**Issue**: "LLM responses are slow or fail"
```bash
TimeoutError: LLM request timed out
# or
"Unable to generate response"
```

**Solutions**:
```bash
# Check LLM model status
python test_model_loading.py

# Reduce context window
# In .env:
LLM_CONTEXT_WINDOW=4096

# Monitor system resources
top  # Linux
Activity Monitor  # macOS

# Test LLM directly
python test_mistral_model.py

# Check for memory leaks
# Restart application if memory usage high
```

## Performance Issues

### Slow Processing

**Issue**: "Document processing is very slow"
```bash
Processing times > 5 minutes for small documents
```

**Solutions**:
```bash
# Check system resources
# CPU usage, memory, disk I/O

# Optimize for your hardware
# Enable Metal on macOS:
USE_METAL=true
METAL_N_GPU_LAYERS=1

# Reduce batch sizes
EMBEDDING_BATCH_SIZE=16

# Monitor processing
python test_performance_indexes.py

# Add performance indexes
python migrate_add_performance_indexes.py
```

### High Memory Usage

**Issue**: "Application uses excessive memory"
```bash
Memory usage > 8GB
```

**Solutions**:
```bash
# Monitor memory usage
ps aux | grep python
# or use htop/Activity Monitor

# Reduce model size
# Switch to phi-2 model (smaller)
python switch_model.py

# Optimize configuration
LLM_THREADS=2
EMBEDDING_BATCH_SIZE=8
METAL_N_GPU_LAYERS=0

# Restart application periodically
# For long-running processes
```

### Vector Search Slow

**Issue**: "Search queries take too long"
```bash
Query response times > 10 seconds
```

**Solutions**:
```bash
# Rebuild vector indices
rm -rf data/vector_db/
# Re-upload documents to rebuild

# Check index sizes
du -sh data/vector_db/

# Optimize search parameters
VECTOR_SEARCH_TOP_K=3
VECTOR_SIMILARITY_THRESHOLD=0.4

# Test search performance
python test_mixed_sources.py
```

## Network and Connectivity

### API Connection Issues

**Issue**: "Cannot connect to API endpoints"
```bash
ConnectionError: [Errno 61] Connection refused
```

**Solutions**:
```bash
# Verify server is running
curl http://localhost:8000/api/v1/health-check

# Check port availability
lsof -i :8000
netstat -an | grep 8000

# Start server if not running
python main.py

# Check firewall settings
# Ensure port 8000 is open

# Try different port
# In .env:
PORT=8001
```

### Gmail API Connectivity

**Issue**: "Cannot connect to Gmail API"
```bash
ConnectionError: Failed to connect to Gmail
```

**Solutions**:
```bash
# Test internet connectivity
ping gmail.googleapis.com

# Check API quotas
# Review Google Cloud Console quotas

# Verify OAuth tokens
curl -X GET "http://localhost:8000/api/v1/gmail/status" \
  -H "Authorization: Bearer $TOKEN"

# Refresh OAuth tokens
# Re-authorize if needed

# Test Gmail connectivity
python test_email_sync_fix.py
```

## Configuration Issues

### Environment Variables

**Issue**: "Configuration not loading properly"
```bash
KeyError: 'SECRET_KEY'
# or using default values
```

**Solutions**:
```bash
# Check .env file exists
ls -la .env

# Verify environment loading
python -c "from app.core.config import settings; print(settings.SECRET_KEY)"

# Copy from example
cp .env.example .env

# Check for syntax errors in .env
# No spaces around = sign
SECRET_KEY=your_key_here

# Test configuration
python test_config_system.py
```

### File Permissions

**Issue**: "Permission denied errors"
```bash
PermissionError: [Errno 13] Permission denied
```

**Solutions**:
```bash
# Check file permissions
ls -la data/
ls -la static/

# Fix permissions
chmod -R 755 data/
chmod -R 755 static/
chmod -R 755 logs/

# Check write access
touch data/test_file
rm data/test_file

# Run with appropriate user
# Avoid running as root
```

## Error Monitoring and Logging

### Enable Debug Logging

```bash
# In .env file:
DEBUG=true
LOG_LEVEL=DEBUG

# Check logs
tail -f logs/app.log

# Increase log detail for specific issues
# Check app/utils/logging_config.py
```

### Common Error Patterns

```bash
# Database errors
grep "sqlalchemy" logs/app.log

# Model loading errors
grep "llama" logs/app.log

# Email processing errors
grep "gmail" logs/app.log

# Vector store errors
grep "faiss" logs/app.log
```

### System Health Checks

```bash
# Overall health
curl http://localhost:8000/api/v1/health-check

# Test core functionality
python test_error_handling.py

# Database health
python list_documents.py

# Model health
python test_model_loading.py

# Gmail health
curl -X GET "http://localhost:8000/api/v1/gmail/status" \
  -H "Authorization: Bearer $TOKEN"
```

## Getting Additional Help

### Diagnostic Commands

```bash
# System information
python --version
pip list | grep -E "(fastapi|sqlalchemy|llama|faiss|sentence)"

# Configuration check
python test_config_system.py

# End-to-end test
python test_mixed_sources.py

# Performance check
python test_performance_indexes.py
```

### Log Analysis

```bash
# Recent errors
tail -100 logs/app.log | grep ERROR

# Processing times
grep "processing_time" logs/app.log

# Memory usage patterns
grep "memory" logs/app.log
```

### Support Resources

- **CLAUDE.md**: Development commands and workflows
- **Architecture Documentation**: Technical deep dive
- **API Reference**: Complete endpoint documentation
- **GitHub Issues**: Report bugs and request features