# Frequently Asked Questions

Common questions and answers about Personal AI Agent.

## General Questions

### What is Personal AI Agent?

Personal AI Agent is a privacy-first AI assistant that helps you search and query your PDF documents and Gmail emails using natural language. It runs completely locally, ensuring your data stays private.

### How is this different from other AI assistants?

- **100% Privacy**: All processing happens locally, no data sent to external APIs
- **Specialized Processing**: Optimized for documents and emails with category-specific handling
- **Unified Search**: Query across both PDFs and emails simultaneously
- **Source Attribution**: All responses include citations to original sources

### What file formats are supported?

Currently, the system supports:
- **PDF documents**: Primary format with text extraction
- **Gmail emails**: Full integration with OAuth2
- **Email attachments**: Text extraction from supported formats

Text-based PDFs work best. Scanned documents (images) require OCR preprocessing.

### Is my data secure?

Yes, your data is processed entirely on your local machine:
- No external API calls for document processing
- Local LLM (Mistral 7B) for response generation
- Gmail OAuth uses industry-standard security
- User data isolation in local databases
- Configurable data retention policies

## Installation and Setup

### What are the system requirements?

**Minimum requirements:**
- Python 3.8+
- 4GB RAM (8GB recommended)
- 10GB free disk space
- Internet connection (for setup only)

**Recommended:**
- Python 3.9+
- 16GB RAM
- SSD storage
- macOS (for Metal acceleration) or Linux

### Why is the initial download so large?

The system downloads AI models locally:
- **Mistral 7B model**: ~4GB (language understanding)
- **Embedding model**: ~100MB (semantic search)
- **Dependencies**: ~2GB (ML libraries)

This ensures complete privacy and offline operation.

### Can I use a different AI model?

Yes, the system supports multiple models:
- **Mistral 7B**: Best quality, higher memory usage
- **Phi-2**: Faster, lower memory usage
- **Custom models**: GGUF format supported

Use `python switch_model.py` to change models.

## Document Processing

### Why does document processing take so long?

Processing time depends on:
- **Document size**: Larger documents take longer
- **System resources**: CPU, memory, and disk speed
- **Classification complexity**: Mixed content takes more analysis
- **Hardware acceleration**: Metal/GPU speeds up processing

Typical times:
- Small PDF (1-5 pages): 30-60 seconds
- Medium PDF (20-50 pages): 2-5 minutes
- Large PDF (100+ pages): 5-15 minutes

### What if my document is classified incorrectly?

Document classification is automatic and affects processing optimization, but doesn't prevent functionality:

- **Financial**: Optimized for transactions and amounts
- **Long-form**: Optimized for comprehensive context
- **Generic**: Balanced processing approach

All document types work with all query types, though optimization may vary.

### Can I process scanned documents?

Not directly. Scanned documents are images and require OCR (Optical Character Recognition) first:

1. **Use OCR software** (Adobe Acrobat, online tools)
2. **Convert to text-based PDF**
3. **Upload the converted document**

The system requires selectable text to function properly.

### Why can't I find specific information I know is in my document?

Several factors affect search quality:
- **Query specificity**: Try more specific terms
- **Text extraction quality**: Check if text was properly extracted
- **Chunk boundaries**: Information might span multiple chunks
- **Processing status**: Ensure document processing completed

Try variations of your query and check the original document structure.

## Gmail Integration

### Is it safe to connect my Gmail account?

Yes, the integration uses Google's OAuth2 standard with minimal permissions:
- **Read-only access**: Cannot send or delete emails
- **No external sharing**: Emails processed locally only
- **Revocable access**: Can disconnect anytime
- **Industry standard**: Same security as other Google integrations

### How many emails can I sync?

**Technical limits:**
- Maximum per sync: 1000 emails
- Recommended batch: 100-500 emails
- Total storage: Limited by disk space only

**Practical recommendations:**
- Start with recent 3-6 months
- Sync incrementally
- Focus on important email categories

### Why are my emails classified incorrectly?

Email classification improves over time and uses multiple signals:
- **Subject line patterns**
- **Sender information**
- **Content analysis**
- **Email metadata**

Classification affects search optimization but all emails remain searchable regardless of category.

### Can I sync emails from multiple accounts?

Currently, one Gmail account per user is supported. Future versions may support multiple accounts.

## Querying and Search

### How do I write effective queries?

**Be specific:**
- "Apple transactions in March 2024" vs "Apple stuff"
- "Meeting notes from quarterly review" vs "meetings"

**Include context:**
- "From my bank statement, find grocery expenses"
- "In my research papers, explain machine learning"

**Use natural language:**
- "How much did I spend on restaurants last month?"
- "What did Sarah say about the project timeline?"

### Why do I get different results for similar queries?

Query results depend on:
- **Exact wording**: Synonyms may find different content
- **Context clues**: Additional words help focus search
- **Content classification**: Different document types optimize differently
- **Vector similarity**: Semantic matching varies with phrasing

Try rephrasing queries or being more specific.

### Can I search across both PDFs and emails simultaneously?

Yes! This is a key feature:
- **Cross-content queries**: "Find all Apple purchases"
- **Unified results**: Combined from PDFs and emails
- **Source attribution**: Clear identification of source type
- **Relevance ranking**: Best matches from all content

### How accurate are the AI responses?

Response accuracy depends on:
- **Source quality**: Better documents = better responses
- **Query clarity**: Specific questions get better answers
- **Content relevance**: Responses limited to your documents
- **Hallucination prevention**: Built-in safeguards against false information

Always check source citations for verification.

## Performance and Optimization

### Why is the system slow on my computer?

Performance factors:
- **Available RAM**: 8GB+ recommended for smooth operation
- **CPU speed**: Faster processors improve response times
- **Storage type**: SSD significantly faster than HDD
- **Background apps**: Close unnecessary applications

**Optimization tips:**
- Enable hardware acceleration (Metal on macOS)
- Reduce batch sizes for processing
- Use specific queries to limit search scope
- Regular cleanup of old documents

### How can I improve search speed?

**Query optimization:**
- Use specific terms rather than broad searches
- Filter by document type when possible
- Limit result counts for faster responses

**System optimization:**
- Enable hardware acceleration
- Increase available RAM
- Use SSD storage
- Regular maintenance of vector databases

### How much disk space does the system use?

**Base installation:** ~6GB
- Models: ~4GB
- Dependencies: ~2GB

**User data** (scales with usage):
- PDF documents: Original file size
- Vector embeddings: ~10-20% of original text size
- Email data: ~50-100MB per 1000 emails
- Database metadata: Minimal

Plan for 2-3x your document storage for optimal performance.

## Troubleshooting

### The application won't start

**Common causes:**
1. **Python version**: Requires 3.8+
2. **Missing dependencies**: Run `pip install -r requirements.txt`
3. **Port conflicts**: Another service using port 8000
4. **Missing models**: Run `python download_model.py`
5. **Database issues**: Try `python setup_db.py`

Check logs in `logs/app.log` for specific errors.

### Documents fail to upload

**Common causes:**
1. **File size**: Check maximum size limit (default 10MB)
2. **File format**: Only PDF currently supported
3. **File corruption**: Try opening in PDF viewer first
4. **Permissions**: Check write access to upload directory
5. **Disk space**: Ensure sufficient storage available

### Gmail sync fails

**Common causes:**
1. **OAuth setup**: Verify Google Cloud Console configuration
2. **Rate limits**: Wait before retrying large syncs
3. **Network issues**: Check internet connectivity
4. **Token expiration**: Re-authorize if needed
5. **API quotas**: Check Google Cloud Console quotas

### Search returns no results

**Common causes:**
1. **Processing incomplete**: Check document processing status
2. **Query too specific**: Try broader search terms
3. **Content not indexed**: Verify text extraction worked
4. **Database issues**: Check vector store integrity
5. **Empty documents**: Ensure documents contain text

## Data Management

### How do I backup my data?

**Database backup:**
```bash
cp personal_ai_agent.db personal_ai_agent.db.backup
```

**Vector embeddings backup:**
```bash
cp -r data/vector_db/ data/vector_db_backup/
```

**Document files backup:**
```bash
cp -r static/uploads/ static/uploads_backup/
```

### How do I delete my data?

**Delete specific documents:**
- Use the web interface or API
- Removes PDF, embeddings, and metadata

**Delete Gmail data:**
```bash
curl -X DELETE "/api/v1/gmail/disconnect" \
  -d '{"delete_emails": true}'
```

**Complete cleanup:**
```bash
rm personal_ai_agent.db
rm -rf data/vector_db/
rm -rf static/uploads/
```

### Can I export my data?

Currently, data export options are limited:
- **Original PDFs**: Available in `static/uploads/`
- **Database**: SQLite format, can be accessed with standard tools
- **Email content**: Stored in database, requires technical extraction

Enhanced export features are planned for future releases.

## Privacy and Security

### What data is stored locally?

**Document data:**
- Original PDF files
- Extracted text content
- Vector embeddings for search
- Processing metadata

**Email data:**
- Email content and metadata
- Vector embeddings for search
- OAuth tokens (encrypted)
- Sync history

**User data:**
- Account information
- Query history
- System logs

### Is my data encrypted?

**Local storage:**
- OAuth tokens are encrypted
- Database can be encrypted (configuration dependent)
- File system encryption recommended

**In transit:**
- Gmail OAuth uses HTTPS
- Local API calls use HTTP (localhost only)
- No external data transmission during normal operation

### Who can access my data?

Only you have access to your data:
- **Single-user system**: Designed for personal use
- **Local processing**: No external access required
- **User isolation**: Multiple users have separate data
- **No telemetry**: No usage data collected or transmitted

## Future Development

### What features are planned?

**Short term:**
- Enhanced security and rate limiting
- Performance optimizations
- Better error handling and recovery

**Medium term:**
- Notion integration
- Multiple Gmail accounts
- Enhanced analytics and insights
- Mobile companion app

**Long term:**
- Multi-user enterprise features
- Cloud deployment options
- Additional file format support
- Advanced AI capabilities

### How can I contribute or request features?

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Share ideas and ask questions
- **Pull Requests**: Contribute code improvements
- **Documentation**: Help improve guides and tutorials

### Is there a commercial version?

Currently, Personal AI Agent is open-source and free. Future commercial offerings may include:
- **Hosted solutions**: Cloud-based deployment
- **Enterprise features**: Multi-user, advanced security
- **Professional support**: Installation and customization help
- **Premium models**: Access to larger, more capable AI models