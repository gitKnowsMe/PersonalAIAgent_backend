# Quick Start Guide

Get up and running with Personal AI Agent in minutes.

## Prerequisites

Make sure you've completed the [installation](installation.md) process.

## 1. Start the Server

```bash
# Activate your virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Start the server
python main.py
```

The server will start on `http://localhost:8000`.

## 2. Upload Your First Document

### Via Web Interface

1. Open `http://localhost:8000` in your browser
2. Log in with your admin credentials
3. Click "Upload Document"
4. Select a PDF file
5. Wait for processing to complete

### Via API

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/your/document.pdf"
```

## 3. Ask Your First Question

### Via Web Interface

1. Navigate to the query section
2. Type your question: "What is this document about?"
3. Press Enter or click "Ask"
4. View the AI-generated response with source citations

### Via API

```bash
curl -X POST "http://localhost:8000/api/v1/queries/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "include_sources": true
  }'
```

## 4. Connect Gmail (Optional)

1. Set up Gmail OAuth credentials in your `.env` file:
   ```env
   GMAIL_CLIENT_ID=your_client_id
   GMAIL_CLIENT_SECRET=your_client_secret
   ```

2. Initialize Gmail connection:
   ```bash
   python setup_gmail.py
   ```

3. Authorize via web interface or API endpoint

## 5. Query Across Content Types

Once you have both PDFs and emails, you can ask questions that span both:

```
"Find information about my Apple expenses from both my bank statements and emails"
```

The system will automatically search across all your content types and provide unified results.

## Example Queries

### PDF Document Queries

- **Financial**: "What were my total expenses in March?"
- **Research**: "Summarize the key findings about machine learning"
- **Personal**: "What skills are listed on my resume?"

### Email Queries

- **Business**: "Find emails about the quarterly review meeting"
- **Personal**: "Show me emails from my family last month"
- **Support**: "Find my conversation with customer service"

### Cross-Content Queries

- **Mixed**: "Find all information about my Apple purchases"
- **Timeline**: "Show me all communications about project X"
- **Financial**: "Compare expenses from statements and email receipts"

## Understanding Document Classification

The system automatically classifies your content:

### PDF Documents

- **Financial**: Bank statements, invoices → Small chunks for precise transactions
- **Long-form**: Research papers, reports → Large chunks for context
- **Generic**: Resumes, letters → Balanced processing

### Emails

- **Business**: Work communications → Professional context
- **Personal**: Family/friends → Personal context
- **Promotional**: Marketing → Content filtering
- **Transactional**: Receipts → Transaction parsing
- **Support**: Customer service → Issue tracking

## Tips for Better Results

1. **Be Specific**: "Find Apple transactions in March" vs "Find expenses"
2. **Use Context**: "In my bank statement" or "from my emails"
3. **Ask Follow-ups**: The system maintains query context
4. **Check Sources**: Always verify the provided citations

## Next Steps

- [Learn about Gmail Integration](../user-guide/gmail-integration.md)
- [Explore Document Classification](../user-guide/classification.md)
- [Advanced Configuration](configuration.md)
- [API Reference](../api/auth.md)

## Performance Tips

- **Model Performance**: Use Metal acceleration on macOS (`USE_METAL=true`)
- **Batch Uploads**: Upload multiple documents at once for efficiency
- **Regular Cleanup**: Periodically clean up old documents and emails
- **Memory Usage**: Monitor system resources during large processing jobs