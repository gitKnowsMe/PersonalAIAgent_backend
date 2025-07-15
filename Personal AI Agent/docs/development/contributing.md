# Contributing Guide

Welcome to the Personal AI Agent project! This guide will help you contribute effectively to the codebase.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- 4GB+ RAM for local LLM testing
- Basic knowledge of FastAPI, SQLAlchemy, and modern Python

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/personal-ai-agent.git
   cd personal-ai-agent
   ```

2. **Set Up Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Download Models**
   ```bash
   python download_model.py
   python download_embedding_model.py
   ```

6. **Initialize Database**
   ```bash
   python setup_db.py
   ```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow our coding standards and architecture patterns.

### 3. Test Your Changes

```bash
# Run relevant tests
python -m pytest tests/

# Test specific functionality
python test_your_feature.py

# Manual testing
python main.py
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

### 5. Submit Pull Request

- Push to your fork
- Create pull request from your feature branch
- Fill out the PR template
- Wait for review

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

```python
# Good: Clear function names and docstrings
async def classify_document(content: str, page_count: int = None) -> DocumentClassification:
    """
    Classify a document based on its content and metadata.
    
    Args:
        content: The text content of the document
        page_count: Number of pages (optional)
    
    Returns:
        DocumentClassification with type and confidence
    """
    pass

# Good: Type hints
def process_financial_document(
    content: str, 
    chunk_size: int = 500
) -> List[DocumentChunk]:
    pass

# Good: Constants
FINANCIAL_CHUNK_SIZE = 500
LONG_FORM_CHUNK_SIZE = 1500
GENERIC_CHUNK_SIZE = 1000
```

### Import Organization

```python
# Standard library imports
import os
import logging
from typing import List, Optional, Dict

# Third-party imports
from fastapi import FastAPI, HTTPException
from sqlalchemy import Column, Integer, String
import numpy as np

# Local imports
from app.core.config import settings
from app.db.models import Document
from app.utils.processors import BaseProcessor
```

### Error Handling

```python
# Good: Specific exceptions with context
class DocumentProcessingError(Exception):
    """Raised when document processing fails"""
    def __init__(self, message: str, document_id: int = None):
        self.message = message
        self.document_id = document_id
        super().__init__(self.message)

# Good: Proper exception handling
try:
    result = process_document(content)
except DocumentProcessingError as e:
    logger.error(f"Document processing failed: {e.message}")
    raise HTTPException(status_code=422, detail=e.message)
```

### Async/Await Best Practices

```python
# Good: Async functions for I/O operations
async def save_document_chunks(chunks: List[DocumentChunk]) -> None:
    async with get_db_session() as session:
        for chunk in chunks:
            session.add(chunk)
        await session.commit()

# Good: Use async context managers
async def process_with_timeout(content: str) -> str:
    async with asyncio.timeout(30):
        return await slow_processing_function(content)
```

## Architecture Guidelines

### Component Structure

When adding new features, follow our modular architecture:

```
app/
├── api/endpoints/      # API routes
├── core/              # Configuration and core utilities
├── db/                # Database models and connections
├── services/          # Business logic services
├── utils/             # Utility functions and processors
└── schemas/           # Pydantic models
```

### Adding New Processors

1. **Inherit from BaseProcessor**
   ```python
   from app.utils.processors.base_processor import BaseProcessor
   
   class YourProcessor(BaseProcessor):
       def __init__(self):
           super().__init__(chunk_size=1000, overlap=200)
       
       def process_content(self, content: str) -> List[str]:
           # Your processing logic
           pass
   ```

2. **Register in DocumentClassifier**
   ```python
   # In app/utils/document_classifier.py
   def get_processor(self, document_type: str) -> BaseProcessor:
       processors = {
           "financial": FinancialProcessor(),
           "long_form": PDFProcessor(),
           "generic": BaseProcessor(),
           "your_type": YourProcessor(),  # Add here
       }
       return processors.get(document_type, BaseProcessor())
   ```

### Adding New API Endpoints

1. **Create endpoint file**
   ```python
   # app/api/endpoints/your_feature.py
   from fastapi import APIRouter, Depends, HTTPException
   from app.api.dependencies import get_current_user
   from app.schemas.your_feature import YourFeatureSchema
   
   router = APIRouter()
   
   @router.post("/")
   async def create_your_feature(
       data: YourFeatureSchema,
       current_user = Depends(get_current_user)
   ):
       # Implementation
       pass
   ```

2. **Register in main app**
   ```python
   # app/main.py
   from app.api.endpoints import your_feature
   
   app.include_router(
       your_feature.router, 
       prefix=f"{settings.API_V1_STR}/your-feature", 
       tags=["your-feature"]
   )
   ```

### Database Migrations

1. **Create migration script**
   ```python
   # migrate_your_feature.py
   from app.db.database import engine
   from sqlalchemy import text
   
   def migrate():
       with engine.connect() as conn:
           conn.execute(text("""
               ALTER TABLE your_table 
               ADD COLUMN new_field VARCHAR(100)
           """))
           conn.commit()
   
   if __name__ == "__main__":
       migrate()
   ```

2. **Test migration**
   ```bash
   python migrate_your_feature.py
   ```

## Testing Guidelines

### Test Structure

```python
# tests/test_your_feature.py
import pytest
from app.services.your_service import YourService

class TestYourFeature:
    @pytest.fixture
    def your_service(self):
        return YourService()
    
    def test_basic_functionality(self, your_service):
        result = your_service.process("test input")
        assert result is not None
        assert result.status == "success"
    
    @pytest.mark.asyncio
    async def test_async_functionality(self, your_service):
        result = await your_service.async_process("test input")
        assert result is not None
```

### Test Categories

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test endpoint functionality
4. **Performance Tests**: Test response times and memory usage

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific test file
python -m pytest tests/test_your_feature.py

# With coverage
python -m pytest tests/ --cov=app
```

## Documentation

### Code Documentation

```python
class DocumentProcessor:
    """
    Processes documents for vector storage and search.
    
    This class handles the complete document processing pipeline including
    classification, chunking, embedding generation, and storage.
    
    Attributes:
        chunk_size: Default chunk size for processing
        overlap: Overlap between chunks for context preservation
    
    Example:
        processor = DocumentProcessor()
        chunks = processor.process_document(content, document_type="financial")
    """
    
    async def process_document(
        self, 
        content: str, 
        document_type: str = "generic"
    ) -> List[DocumentChunk]:
        """
        Process document content into searchable chunks.
        
        Args:
            content: The document text content
            document_type: Type of document for processing strategy
            
        Returns:
            List of processed document chunks
            
        Raises:
            DocumentProcessingError: If processing fails
            ValueError: If content is empty or invalid
        """
        pass
```

### API Documentation

FastAPI automatically generates OpenAPI documentation, but add examples:

```python
@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to process"),
    current_user = Depends(get_current_user)
):
    """
    Upload and process a PDF document.
    
    - **file**: PDF file (max 10MB)
    - **returns**: Document metadata and processing status
    
    The document will be automatically classified and processed according to its type:
    - Financial documents use small chunks for transaction precision
    - Long-form documents use large chunks for context preservation
    - Generic documents use balanced chunking strategy
    """
    pass
```

## Commit Message Guidelines

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
git commit -m "feat(email): add Gmail OAuth2 integration"
git commit -m "fix(vector): resolve FAISS index corruption issue"
git commit -m "docs(api): update authentication endpoint documentation"
git commit -m "test(classifier): add unit tests for document classification"
```

## Pull Request Process

### PR Title Format

Use the same format as commit messages:
```
feat(scope): brief description of changes
```

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Changes
- List of specific changes made
- Another change
- Third change

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Documentation
- [ ] Code is documented
- [ ] API documentation updated
- [ ] User documentation updated (if needed)

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Related Issues
Closes #123
Related to #456
```

### Review Checklist

Before submitting:

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No sensitive information in commits
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

## Security Guidelines

### Sensitive Information

- Never commit API keys, passwords, or tokens
- Use environment variables for configuration
- Sanitize user inputs
- Validate file uploads properly

### Authentication

- Always use proper authentication for API endpoints
- Validate user permissions for operations
- Use secure password hashing (bcrypt)
- Implement proper session management

### Data Privacy

- Ensure user data isolation
- Implement proper access controls
- Follow privacy-by-design principles
- Document data handling practices

## Performance Considerations

### Vector Operations

- Use batch processing for embeddings
- Implement proper caching strategies
- Monitor memory usage during processing
- Optimize database queries

### API Performance

- Use async/await for I/O operations
- Implement request timeout limits
- Monitor response times
- Use appropriate data pagination

## Getting Help

### Resources

- [Architecture Documentation](architecture.md)
- [API Reference](../api/auth.md)
- [Testing Guide](testing.md)
- **CLAUDE.md** - Development commands and workflows (in project root)

### Communication

- Open GitHub issues for bugs or feature requests
- Use discussions for questions and ideas
- Follow the code of conduct in all interactions
- Be respectful and constructive in reviews

## Release Process

### Version Numbering

We follow semantic versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number incremented
- [ ] Changelog updated
- [ ] Performance benchmarks run
- [ ] Security review completed

Thank you for contributing to Personal AI Agent!