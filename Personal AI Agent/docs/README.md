# Personal AI Agent Documentation

This directory contains comprehensive documentation for the Personal AI Agent project.

## Documentation Structure

### Getting Started
- **[Installation](getting-started/installation.md)** - Setup and installation guide
- **[Quick Start](getting-started/quickstart.md)** - Get running in minutes
- **[Configuration](getting-started/configuration.md)** - Advanced configuration options

### User Guides
- **[PDF Documents](user-guide/pdf-documents.md)** - Upload and query PDF documents
- **[Gmail Integration](user-guide/gmail-integration.md)** - Connect and search your Gmail
- **[Querying Data](user-guide/querying.md)** - Effective search strategies
- **[Document Classification](user-guide/classification.md)** - Understanding document types

### API Reference
- **[Authentication](api/auth.md)** - JWT-based authentication
- **[Documents](api/documents.md)** - PDF upload and management
- **[Queries](api/queries.md)** - Natural language search
- **[Gmail](api/gmail.md)** - Gmail integration
- **[Email Search](api/emails.md)** - Email search and filtering

### Development
- **[Architecture](development/architecture.md)** - System architecture overview
- **[Database Schema](development/database.md)** - Database design and schema
- **[Vector Storage](development/vector-storage.md)** - FAISS vector storage
- **[Processing Pipeline](development/processing.md)** - Document processing flow
- **[Testing](development/testing.md)** - Testing strategies and tools
- **[Contributing](development/contributing.md)** - Contribution guidelines

### Deployment
- **[Local Setup](deployment/local.md)** - Local development setup
- **[Production](deployment/production.md)** - Production deployment
- **[Security](deployment/security.md)** - Security considerations

### Troubleshooting
- **[Common Issues](troubleshooting/common-issues.md)** - Frequent problems and solutions
- **[FAQ](troubleshooting/faq.md)** - Frequently asked questions
- **[Support](troubleshooting/support.md)** - Getting help and support

## Viewing Documentation

### Local Development

To view the documentation locally:

```bash
# Install MkDocs (if not already installed)
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve documentation locally
mkdocs serve

# Open in browser
open http://localhost:8000
```

### Building Static Site

To build the documentation as a static site:

```bash
# Build documentation
mkdocs build

# Output will be in site/ directory
ls site/
```

### GitHub Pages Deployment

To deploy to GitHub Pages:

```bash
# Deploy to gh-pages branch
mkdocs gh-deploy
```

## Documentation Standards

### Writing Guidelines

1. **Clear Structure**: Use consistent heading hierarchy
2. **Code Examples**: Include working examples for all procedures
3. **Screenshots**: Add visuals for UI-related documentation
4. **Cross-References**: Link to related sections
5. **Updates**: Keep documentation current with code changes

### Markdown Features

The documentation uses MkDocs Material theme with extensions:

- **Admonitions**: Info, warning, and tip boxes
- **Code Highlighting**: Syntax highlighting for multiple languages
- **Tabs**: Organize related content
- **Tables**: Structured data presentation
- **Mermaid**: Diagrams and flowcharts

### Code Examples

```python
# Always include complete, working examples
from app.services.query_service import QueryService

query_service = QueryService()
result = query_service.search("example query")
```

```bash
# Include command-line examples with expected output
curl -X GET "http://localhost:8000/api/v1/health-check"
# Expected: {"status": "ok", "version": "1.0.0"}
```

### Admonitions

!!! note "Information"
    Use note admonitions for helpful information.

!!! warning "Warning"
    Use warning admonitions for important caveats.

!!! tip "Pro Tip"
    Use tip admonitions for advanced techniques.

!!! danger "Critical"
    Use danger admonitions for critical warnings.

## Contributing to Documentation

### Adding New Pages

1. Create markdown file in appropriate directory
2. Add to navigation in `mkdocs.yml`
3. Follow existing style and structure
4. Test locally with `mkdocs serve`
5. Submit pull request

### Updating Existing Pages

1. Make changes to markdown files
2. Verify links and formatting
3. Test locally
4. Update last modified date if significant changes
5. Submit pull request

### Best Practices

1. **Keep It Current**: Update docs with code changes
2. **Test Examples**: Verify all code examples work
3. **User Focus**: Write from user perspective
4. **Search Optimization**: Use clear headings and keywords
5. **Accessibility**: Include alt text for images

## Documentation Maintenance

### Regular Updates

- **API Changes**: Update API docs with endpoint changes
- **Feature Additions**: Document new features thoroughly
- **Bug Fixes**: Update troubleshooting guides
- **Performance**: Update benchmarks and optimization tips

### Quality Checks

- **Link Checking**: Verify all internal and external links
- **Code Validation**: Test all code examples
- **Spelling**: Use spell check tools
- **Formatting**: Consistent markdown formatting
- **Navigation**: Logical organization and flow

## Getting Help

### Documentation Issues

- **GitHub Issues**: Report documentation bugs
- **Pull Requests**: Suggest improvements
- **Discussions**: Ask questions about documentation

### Style Questions

- Follow existing patterns in the documentation
- Check MkDocs Material documentation for features
- Ask maintainers for clarification on style decisions

## Resources

- **[MkDocs](https://www.mkdocs.org/)** - Documentation generator
- **[Material Theme](https://squidfunk.github.io/mkdocs-material/)** - Theme documentation
- **[Markdown Guide](https://www.markdownguide.org/)** - Markdown syntax reference
- **[Mermaid](https://mermaid-js.github.io/mermaid/)** - Diagram syntax