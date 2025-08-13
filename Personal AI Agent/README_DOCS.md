# Personal AI Agent Documentation

Comprehensive documentation has been created using MkDocs with Material theme.

## Documentation Structure

```
docs/
├── index.md                    # Main landing page
├── getting-started/           # Installation and setup
│   ├── installation.md       # Complete installation guide
│   ├── quickstart.md         # Quick start tutorial
│   └── configuration.md      # Configuration options
├── user-guide/               # User documentation
│   ├── pdf-documents.md      # PDF document handling
│   ├── gmail-integration.md  # Gmail setup and usage
│   ├── querying.md           # Query techniques
│   └── classification.md     # Document/email classification
├── api/                      # API documentation
│   ├── auth.md               # Authentication endpoints
│   ├── documents.md          # Document management API
│   ├── queries.md            # Query API
│   ├── gmail.md              # Gmail integration API
│   └── emails.md             # Email search API
├── development/              # Developer documentation
│   ├── architecture.md       # System architecture
│   ├── database.md           # Database schema
│   ├── vector-storage.md     # Vector storage system
│   ├── processing.md         # Processing pipeline
│   ├── testing.md            # Testing guide
│   └── contributing.md       # Contribution guidelines
├── deployment/               # Deployment guides
│   ├── local.md              # Local development setup
│   ├── production.md         # Production deployment
│   └── security.md           # Security considerations
└── troubleshooting/          # Help and support
    ├── common-issues.md      # Common problems
    ├── faq.md                # Frequently asked questions
    └── support.md            # Getting help
```

## Viewing Documentation

### Local Development
```bash
# Install MkDocs and dependencies
pip install mkdocs mkdocs-material "mkdocstrings[python]"

# Serve documentation locally
mkdocs serve

# Open in browser
open http://localhost:8000
```

### Building Static Site
```bash
# Build documentation
mkdocs build

# Output will be in site/ directory
```

### GitHub Pages Deployment
```bash
# Deploy to GitHub Pages
mkdocs gh-deploy
```

## Features

- **Material Design Theme**: Modern, responsive interface
- **Search Functionality**: Full-text search across all documentation
- **Code Highlighting**: Syntax highlighting for multiple languages
- **API Documentation**: Interactive API reference
- **Mobile Friendly**: Responsive design for all devices
- **Dark/Light Mode**: Theme switching capability

## Key Documentation Highlights

### For Users
- **[Quick Start Guide](docs/getting-started/quickstart.md)**: Get running in minutes
- **[PDF Documents Guide](docs/user-guide/pdf-documents.md)**: Comprehensive PDF handling
- **[Gmail Integration](docs/user-guide/gmail-integration.md)**: Complete email setup
- **[Querying Guide](docs/user-guide/querying.md)**: Effective search techniques

### For Developers
- **[Architecture Overview](docs/development/architecture.md)**: System design and components
- **[Contributing Guide](docs/development/contributing.md)**: How to contribute
- **[Testing Guide](docs/development/testing.md)**: Testing strategies and tools
- **[API Reference](docs/api/auth.md)**: Complete API documentation

### For Administrators
- **[Production Deployment](docs/deployment/production.md)**: Enterprise deployment
- **[Security Guide](docs/deployment/security.md)**: Security best practices
- **[Troubleshooting](docs/troubleshooting/common-issues.md)**: Problem resolution

## Documentation Standards

- **Comprehensive Coverage**: All features and functionality documented
- **Practical Examples**: Working code examples throughout
- **Step-by-Step Guides**: Clear, actionable instructions
- **Cross-References**: Linked sections for easy navigation
- **Regular Updates**: Documentation kept current with codebase

## Configuration

The documentation is configured in `mkdocs.yml` with:
- Material theme with dark/light mode
- Search functionality
- Code highlighting
- Tabbed content organization
- Social media integration
- Version management

## Contributing to Documentation

See the [Contributing Guide](docs/development/contributing.md) for information on how to improve and update the documentation.

The documentation provides a complete resource for users, developers, and administrators working with Personal AI Agent.