# Testing Guide

Comprehensive testing strategy and guidelines for the Personal AI Agent.

## Testing Philosophy

The Personal AI Agent follows a multi-layered testing approach:

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Cross-component workflows
3. **API Tests**: Endpoint functionality and contracts
4. **Performance Tests**: System performance and scalability
5. **Manual Tests**: User workflow validation

## Test Structure

### Test Organization

```
tests/
├── unit/
│   ├── test_document_classifier.py
│   ├── test_email_classifier.py
│   └── test_processors.py
├── integration/
│   ├── test_document_workflow.py
│   ├── test_email_workflow.py
│   └── test_query_workflow.py
├── api/
│   ├── test_auth_endpoints.py
│   ├── test_document_endpoints.py
│   └── test_query_endpoints.py
└── performance/
    ├── test_vector_search.py
    └── test_concurrent_processing.py
```

### Running Tests

#### All Tests
```bash
# Run complete test suite
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

#### Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# API tests
python -m pytest tests/api/

# Performance tests
python -m pytest tests/performance/
```

#### Individual Test Files
```bash
# Document classifier tests
python -m pytest tests/test_document_classifier.py

# Specific test function
python -m pytest tests/test_document_classifier.py::test_financial_classification
```

## Test Scripts

The project includes numerous test scripts for manual and automated testing:

### Model and System Tests

#### Model Loading Tests
```bash
# Test LLM model loading
python test_model_loading.py

# Test Mistral model specifically
python test_mistral_model.py

# Test embedding model
python download_embedding_model.py
```

#### Configuration Tests
```bash
# Test configuration system
python test_config_system.py

# Test error handling
python test_error_handling.py
```

### Document Processing Tests

#### Classification Tests
```bash
# Test document classification
python test_classification_tags_fix.py

# Debug document chunks
python debug_chunks_detail.py
```

#### Processing Tests
```bash
# Test bank document processing
python test_bank_only.py

# Test direct question processing
python test_direct_question.py

# Test hallucination prevention
python test_hallucination_prevention.py
```

### Email Integration Tests

#### Email Search Tests
```bash
# Test email search functionality
python test_email_search.py

# Test email sync
python test_email_sync_fix.py

# Test concurrent token refresh
python test_concurrent_token_refresh.py
```

#### Email Processing Tests
```bash
# Test direct email queries
python test_direct_query.py

# Test API query functionality
python test_api_query.py
```

### Cross-Content Tests

#### Source Attribution Tests
```bash
# Test source attribution
python test_source_attribution_fix.py

# Test direct source fixes
python test_source_fix_direct.py

# Debug source attribution
python debug_source_attribution.py
```

#### Mixed Content Tests
```bash
# Test mixed sources (PDFs + emails)
python test_mixed_sources.py

# Test specific amounts
python test_specific_amounts.py
```

### Performance Tests

#### Database Performance
```bash
# Test performance indexes
python test_performance_indexes.py

# Add performance indexes
python migrate_add_performance_indexes.py
```

#### Apple-Specific Tests
```bash
# Test Apple-specific queries
python test_apple_specific.py

# Test final Apple implementation
python test_final_apple.py

# Test filter debugging
python test_filter_debug.py
```

## Unit Testing

### Document Classifier Tests

```python
# tests/test_document_classifier.py
import pytest
from app.utils.document_classifier import DocumentClassifier

class TestDocumentClassifier:
    def test_financial_classification(self):
        classifier = DocumentClassifier()
        
        # Test bank statement content
        content = "Account Number: 1234567890\nBalance: $5,432.10\nTransaction Date: 03/15/2024"
        result = classifier.classify(content)
        
        assert result.document_type == "financial"
        assert result.confidence > 0.8
    
    def test_long_form_classification(self):
        classifier = DocumentClassifier()
        
        # Test research paper content (50+ pages)
        content = "Abstract\n" + "Lorem ipsum " * 1000  # Simulate long content
        result = classifier.classify(content, page_count=75)
        
        assert result.document_type == "long_form"
        assert result.confidence > 0.7
    
    def test_generic_classification(self):
        classifier = DocumentClassifier()
        
        # Test resume content
        content = "JOHN DOE\nSoftware Engineer\nExperience:\n- Python Development"
        result = classifier.classify(content)
        
        assert result.document_type == "generic"
```

### Email Classifier Tests

```python
# tests/test_email_classifier.py
import pytest
from app.services.email.email_classifier import EmailClassifier

class TestEmailClassifier:
    def test_business_email_classification(self):
        classifier = EmailClassifier()
        
        email_data = {
            "subject": "Team Meeting Tomorrow at 2 PM",
            "sender": "manager@company.com",
            "content": "Hi team, let's discuss the quarterly results..."
        }
        
        result = classifier.classify_email(email_data)
        assert result.category == "business"
        assert result.confidence > 0.8
    
    def test_transactional_email_classification(self):
        classifier = EmailClassifier()
        
        email_data = {
            "subject": "Your Receipt from Apple Store",
            "sender": "noreply@apple.com",
            "content": "Thank you for your purchase. Amount: $999.00"
        }
        
        result = classifier.classify_email(email_data)
        assert result.category == "transactional"
        assert result.confidence > 0.9
```

## Integration Testing

### Document Processing Workflow

```python
# tests/integration/test_document_workflow.py
import pytest
from app.api.endpoints.documents import upload_document
from app.services.vector_store_service import VectorStoreService

class TestDocumentWorkflow:
    async def test_complete_document_processing(self):
        # Upload document
        document = await upload_document(test_pdf_file, user_id=1)
        
        # Verify classification
        assert document.document_type in ["financial", "long_form", "generic"]
        
        # Verify processing
        assert document.processing_status == "completed"
        assert document.chunk_count > 0
        
        # Verify vector storage
        vector_service = VectorStoreService()
        vectors = await vector_service.search(
            user_id=1,
            query="test query",
            document_types=[document.document_type]
        )
        
        assert len(vectors) > 0
```

### Email Processing Workflow

```python
# tests/integration/test_email_workflow.py
import pytest
from app.services.gmail_service import GmailService
from app.services.email.email_processor import EmailProcessor

class TestEmailWorkflow:
    async def test_email_sync_and_search(self):
        # Mock Gmail API response
        gmail_service = GmailService()
        emails = await gmail_service.sync_emails(user_id=1, limit=10)
        
        # Verify processing
        assert len(emails) > 0
        
        for email in emails:
            assert email.category in ["business", "personal", "promotional", "transactional", "support"]
            assert email.processing_status == "completed"
        
        # Test search functionality
        search_results = await gmail_service.search_emails(
            user_id=1,
            query="test query"
        )
        
        assert isinstance(search_results, list)
```

## API Testing

### Authentication Tests

```python
# tests/api/test_auth_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuthEndpoints:
    def test_register_user(self):
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    def test_login_user(self):
        # First register
        client.post("/api/v1/auth/register", json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpassword123"
        })
        
        # Then login
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser2",
            "password": "testpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
```

### Document API Tests

```python
# tests/api/test_document_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestDocumentEndpoints:
    def test_upload_document(self):
        # Login first to get token
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Upload document
        with open("test_document.pdf", "rb") as f:
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": f},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["processing_status"] in ["processing", "completed"]
    
    def test_list_documents(self):
        token = self.get_auth_token()
        
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
```

## Performance Testing

### Vector Search Performance

```python
# tests/performance/test_vector_search.py
import time
import pytest
from app.services.vector_store_service import VectorStoreService

class TestVectorSearchPerformance:
    def test_search_response_time(self):
        vector_service = VectorStoreService()
        
        start_time = time.time()
        results = vector_service.search(
            user_id=1,
            query="test query",
            limit=10
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 2.0  # Should respond within 2 seconds
        assert len(results) <= 10
    
    def test_concurrent_searches(self):
        import asyncio
        
        async def perform_search():
            vector_service = VectorStoreService()
            return await vector_service.search(
                user_id=1,
                query="concurrent test query"
            )
        
        # Run 10 concurrent searches
        start_time = time.time()
        tasks = [perform_search() for _ in range(10)]
        results = asyncio.run(asyncio.gather(*tasks))
        end_time = time.time()
        
        total_time = end_time - start_time
        assert total_time < 10.0  # All searches within 10 seconds
        assert len(results) == 10
```

### Memory Usage Tests

```python
# tests/performance/test_memory_usage.py
import psutil
import pytest
from app.utils.llm import LLMService

class TestMemoryUsage:
    def test_llm_memory_usage(self):
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Load LLM
        llm_service = LLMService()
        llm_service.load_model()
        
        loaded_memory = process.memory_info().rss
        memory_increase = loaded_memory - initial_memory
        
        # Should use less than 8GB (in bytes)
        assert memory_increase < 8 * 1024 * 1024 * 1024
```

## Test Configuration

### pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --disable-warnings
    -v
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    api: marks tests as API tests
    performance: marks tests as performance tests
```

### Test Environment

```env
# .env.testing
DATABASE_URL=sqlite:///./test_personal_ai_agent.db
SECRET_KEY=test_secret_key_for_testing_only
LLM_MODEL_PATH=./models/test_model.gguf
DEBUG=true
LOG_LEVEL=DEBUG
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## Testing Best Practices

### Test Data Management

1. **Use fixtures** for common test data
2. **Clean up** after tests (database, files)
3. **Mock external services** (Gmail API, etc.)
4. **Use test-specific data** to avoid conflicts

### Test Isolation

1. **Independent tests** - each test should work in isolation
2. **Clean state** - reset database/vector store between tests
3. **No shared state** between test methods
4. **Deterministic results** - avoid randomness in tests

### Performance Testing

1. **Set realistic thresholds** for response times
2. **Test with realistic data sizes**
3. **Monitor memory usage** during tests
4. **Test concurrent scenarios**

### Manual Testing Checklist

#### Document Upload Flow
- [ ] Upload various PDF types (financial, long-form, generic)
- [ ] Verify classification accuracy
- [ ] Test processing status updates
- [ ] Validate vector storage

#### Gmail Integration Flow
- [ ] OAuth2 authorization flow
- [ ] Email sync functionality
- [ ] Email classification accuracy
- [ ] Search functionality

#### Query Processing Flow
- [ ] Simple document queries
- [ ] Complex cross-content queries
- [ ] Source attribution accuracy
- [ ] Response quality

#### Error Handling
- [ ] Invalid file uploads
- [ ] Network connectivity issues
- [ ] Authentication failures
- [ ] Rate limiting scenarios