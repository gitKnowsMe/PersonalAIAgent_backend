# Personal AI Agent

A privacy-first AI assistant for PDF documents and Gmail emails with advanced document classification and processing capabilities.

## 🚀 Key Features

- **100% Privacy**: Local LLM processing with no external API calls (except Gmail OAuth)
- **PDF + Gmail Integration**: Unified processing for PDF documents and Gmail emails  
- **Smart Content Classification**: Automatic categorization for documents and emails
- **Category-Specific Processing**: Optimized chunking and indexing per content type
- **Thread-Aware Email Processing**: Conversation context preservation
- **Cross-Platform Queries**: Search across PDFs and emails with unified results

## 📊 System Overview

The Personal AI Agent provides a complete personal knowledge base by intelligently processing and searching across both PDF documents and Gmail emails. The system uses specialized handling for different content types to ensure optimal relevance and accuracy.

### Document Categories

- **Financial Documents**: Bank statements, invoices, receipts with transaction-focused processing
- **Long-format Documents**: Research papers, reports, contracts with deep semantic analysis
- **Generic Documents**: Resumes, letters, notes with balanced processing approach

### Email Categories

- **Business**: Meeting invites, project updates, work communications
- **Personal**: Family/friend emails, personal communications
- **Promotional**: Marketing emails, newsletters, deals
- **Transactional**: Receipts, confirmations, account notifications
- **Support**: Customer service, technical support communications

## 🏗️ Architecture

The application uses a modern, scalable architecture:

- **FastAPI**: High-performance async API framework
- **SQLite/PostgreSQL**: Metadata and user management
- **FAISS**: Vector similarity search for semantic queries
- **Mistral 7B**: Local language model for response generation
- **OAuth2**: Secure Gmail authentication
- **Category-Based Storage**: Organized vector indices for optimal performance

## 🔄 Processing Pipeline

1. **Content Ingestion**: Upload PDFs or sync Gmail emails
2. **Classification**: Automatic categorization based on content type
3. **Processing**: Category-specific chunking and metadata extraction
4. **Embedding**: Vector representation using MiniLM model
5. **Storage**: Organized storage in FAISS vector databases
6. **Querying**: Intelligent routing and cross-content search
7. **Response**: LLM-generated answers with source attribution

## 🛡️ Privacy & Security

- All document processing happens locally
- No external API calls for document analysis
- Gmail OAuth uses industry-standard security
- Local vector storage with user isolation
- Configurable data retention policies

## 📚 Quick Links

- [Installation Guide](getting-started/installation.md) - Get started quickly
- [Gmail Integration](user-guide/gmail-integration.md) - Connect your Gmail account
- [API Reference](api/auth.md) - Complete API documentation
- [Architecture Guide](development/architecture.md) - Technical deep dive

## 🆕 What's New

### Latest Updates

- ✅ Gmail Integration with OAuth2 authentication
- ✅ Email classification and thread-aware processing
- ✅ Cross-content queries spanning PDFs and emails
- ✅ Enhanced source attribution and relevance scoring
- 🔄 Security hardening and rate limiting (in progress)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](development/contributing.md) for details on how to get involved.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.