# PDF Documents User Guide

Learn how to upload, process, and query PDF documents effectively with Personal AI Agent.

## Document Upload

### Supported Formats

- **PDF Files**: Primary supported format
- **Text-based PDFs**: Must contain selectable text (not scanned images)
- **File Size**: Maximum 10MB (configurable)
- **Languages**: English optimized, other languages supported

### Upload Methods

#### Web Interface

1. Navigate to the upload section
2. Click "Choose File" or drag and drop
3. Select your PDF file
4. Wait for processing to complete
5. Review classification and status

#### API Upload

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

## Document Classification

The system automatically classifies documents into three categories:

### Financial Documents

**Automatically detected from:**
- Bank statements with transaction patterns
- Invoices with dollar amounts and dates
- Receipts with purchase information
- Financial reports with monetary data

**Processing characteristics:**
- Small chunks (500 characters) for precision
- Optimized for transaction queries
- Enhanced pattern recognition
- Exact amount matching

**Best for:**
- "How much did I spend on groceries?"
- "Find all Apple transactions"
- "What was my balance in March?"

### Long-form Documents

**Automatically detected from:**
- Documents with 20+ pages
- Research papers with academic structure
- Reports with complex formatting
- Contracts with legal language

**Processing characteristics:**
- Large chunks (1500 characters) for context
- Deep semantic understanding
- Narrative flow preservation
- Comprehensive analysis

**Best for:**
- "Summarize the key findings"
- "What are the main recommendations?"
- "Explain the methodology used"

### Generic Documents

**Default classification for:**
- Resumes and CVs
- Personal letters
- Short reports
- Miscellaneous documents

**Processing characteristics:**
- Balanced chunks (1000 characters)
- Hybrid processing approach
- Good for general queries
- Flexible search capabilities

**Best for:**
- "What skills are mentioned?"
- "Find contact information"
- "Summarize this document"

## Processing Pipeline

### 1. Upload Validation

The system validates:
- File format (must be PDF)
- File size (under configured limit)
- PDF structure (must be valid)
- Text content (must be extractable)

### 2. Text Extraction

- Uses PyPDF for text extraction
- Preserves document structure
- Handles various PDF versions
- Extracts metadata (page count, creation date)

### 3. Automatic Classification

- Analyzes content patterns
- Considers document structure
- Uses page count and formatting
- Assigns confidence scores

### 4. Category-Specific Processing

Based on classification:
- **Financial**: Transaction-focused chunking
- **Long-form**: Context-preserving segmentation
- **Generic**: Balanced approach

### 5. Vector Embedding

- Generates semantic embeddings
- Uses MiniLM model for consistency
- Creates searchable vector representations
- Optimizes for query performance

### 6. Storage and Indexing

- Stores in category-specific indices
- Maintains user data isolation
- Creates searchable metadata
- Enables fast retrieval

## Processing Status

Monitor document processing through status indicators:

- **Pending**: Upload received, processing queued
- **Processing**: Active text extraction and analysis
- **Completed**: Ready for queries
- **Failed**: Processing error occurred

## Querying Documents

### Financial Document Queries

```bash
# Transaction queries
"How much did I spend on Amazon in March?"
"Find all Apple transactions over $100"
"What was my total grocery spending?"

# Balance and account queries
"What was my account balance on March 15th?"
"Show me all deposits in February"
"Find overdraft fees"

# Category analysis
"Categorize my March expenses"
"What percentage was spent on dining?"
"Compare Q1 and Q2 spending"
```

### Long-form Document Queries

```bash
# Content analysis
"Summarize the main findings"
"What methodology was used in this research?"
"List the key recommendations"

# Deep understanding
"Explain the theoretical framework"
"What are the limitations mentioned?"
"How does this relate to previous work?"

# Structure queries
"What are the main sections?"
"Find the conclusion"
"Show me the abstract"
```

### Generic Document Queries

```bash
# Information extraction
"What skills are mentioned on this resume?"
"Find contact information"
"What experience is listed?"

# Content queries
"Summarize this document"
"What are the main points?"
"Find specific requirements"
```

## Best Practices

### Document Preparation

1. **Ensure text is selectable** (not scanned images)
2. **Use clear, readable fonts**
3. **Avoid heavily formatted documents** when possible
4. **Consider file size** before upload
5. **Use descriptive filenames**

### Query Optimization

1. **Be specific** in your questions
2. **Use relevant keywords** from the document
3. **Reference document context** when helpful
4. **Ask follow-up questions** for clarification
5. **Check source citations** for accuracy

### File Management

1. **Organize by category** when possible
2. **Remove duplicates** to avoid confusion
3. **Delete old documents** you no longer need
4. **Use meaningful names** for easy identification
5. **Regular cleanup** to maintain performance

## Troubleshooting

### Upload Issues

**"Invalid file type"**
- Ensure file is PDF format
- Check file extension is .pdf
- Verify file is not corrupted

**"File too large"**
- Compress PDF if possible
- Split large documents
- Check configured size limit

**"No text found"**
- Document may be scanned image
- Use OCR software first
- Try different PDF viewer to verify text

### Processing Issues

**"Processing failed"**
- Check file integrity
- Verify sufficient disk space
- Review system logs
- Try re-uploading

**"Classification incorrect"**
- Manual classification not available
- Document may have mixed content
- Processing will still work effectively

### Query Issues

**"No results found"**
- Try broader search terms
- Check document was processed successfully
- Verify you have access to the document
- Try different query phrasing

**"Poor result quality"**
- Be more specific in queries
- Use document-relevant terminology
- Try breaking complex questions into parts
- Check source citations for relevance

## Performance Tips

### Upload Performance

- **Upload during off-peak hours** for large files
- **Use stable internet connection**
- **Close other applications** to free memory
- **Monitor system resources** during processing

### Query Performance

- **Use specific queries** rather than broad searches
- **Limit search scope** when possible
- **Cache frequently used queries**
- **Monitor response times**

### System Optimization

- **Regular maintenance** of vector databases
- **Periodic cleanup** of old documents
- **Monitor disk space** usage
- **Update models** when available

## Advanced Features

### Batch Processing

For multiple documents:
1. Upload documents individually
2. Wait for each to complete processing
3. Query across all documents
4. Use filters to narrow results

### Cross-Document Queries

Search across multiple documents:
```bash
"Find all mentions of Project Alpha across my documents"
"Compare financial data between Q1 and Q2 reports"
"What do my documents say about machine learning?"
```

### Source Attribution

All responses include:
- Source document identification
- Page number references
- Confidence scores
- Original text excerpts
- Processing metadata