# Queries API

Search and query across PDF documents and emails using natural language.

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/queries/` | Submit a new query |
| GET | `/api/v1/queries/` | List query history |
| GET | `/api/v1/queries/{id}` | Get specific query result |

## Submit Query

Ask questions about your documents and emails.

```http
POST /api/v1/queries/
```

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "string",
  "include_sources": true,
  "content_types": ["pdf", "email"],
  "document_types": ["financial", "generic"],
  "max_results": 5
}
```

**Parameters:**
- `query` (required): Natural language question
- `include_sources` (optional): Include source citations (default: true)
- `content_types` (optional): Filter by content type (`["pdf", "email"]`)
- `document_types` (optional): Filter by document type (`["financial", "long_form", "generic"]`)
- `max_results` (optional): Maximum number of source chunks (default: 5)

**Response:**
```json
{
  "id": 1,
  "query": "What were my Apple expenses in March?",
  "response": "Based on your financial documents, you had $1,247.89 in Apple-related expenses in March 2024. This includes: iPhone purchase ($899.00), App Store purchases ($67.89), and Apple Music subscription ($281.00).",
  "sources": [
    {
      "id": "doc_1_chunk_5",
      "content": "03/15/2024 APPLE STORE PURCHASE $899.00",
      "source_type": "pdf",
      "document_type": "financial",
      "filename": "bank_statement_march.pdf",
      "relevance_score": 0.92,
      "page": 2
    },
    {
      "id": "email_42_chunk_1",
      "content": "Your Apple Music subscription has been renewed for $10.99/month",
      "source_type": "email",
      "email_subject": "Apple Music Subscription Renewed",
      "sender": "noreply@apple.com",
      "date": "2024-03-01T08:00:00Z",
      "relevance_score": 0.78
    }
  ],
  "query_type": "cross_content",
  "processing_time": 2.34,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/queries/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What were my Apple expenses in March?",
    "include_sources": true,
    "content_types": ["pdf", "email"]
  }'
```

## Query Types

The system automatically determines the appropriate query strategy:

### Content-Specific Queries

- **PDF Only**: "Find information in my bank statement"
- **Email Only**: "Show me emails from Apple"
- **Cross-Content**: "Find all Apple expenses" (searches both PDFs and emails)

### Document-Type Specific

- **Financial**: Optimized for transaction and expense queries
- **Long-form**: Deep semantic search for research and analysis
- **Generic**: Balanced approach for general information

## List Query History

Retrieve previous queries and results.

```http
GET /api/v1/queries/
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 50)
- `query_type` (optional): Filter by query type
- `start_date` (optional): Filter queries after date (ISO format)
- `end_date` (optional): Filter queries before date (ISO format)

**Response:**
```json
{
  "queries": [
    {
      "id": 1,
      "query": "What were my Apple expenses in March?",
      "response_preview": "Based on your financial documents, you had $1,247.89...",
      "query_type": "cross_content",
      "source_count": 3,
      "processing_time": 2.34,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

## Get Query Details

Retrieve complete details for a specific query.

```http
GET /api/v1/queries/{id}
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
Returns the same detailed structure as the POST response, including full response text and all sources.

## Query Optimization

### Financial Queries

Best for transaction and expense analysis:

```json
{
  "query": "How much did I spend on groceries last month?",
  "document_types": ["financial"],
  "max_results": 10
}
```

### Research Queries

Best for long-form document analysis:

```json
{
  "query": "Summarize the key findings about machine learning",
  "document_types": ["long_form"],
  "max_results": 8
}
```

### Email Communication Queries

Best for email-specific searches:

```json
{
  "query": "Find emails about the quarterly review meeting",
  "content_types": ["email"],
  "max_results": 5
}
```

### Cross-Content Queries

Search across all content types:

```json
{
  "query": "Find all information about Project Alpha",
  "content_types": ["pdf", "email"],
  "max_results": 10
}
```

## Advanced Query Patterns

### Temporal Queries

- "What were my expenses in March 2024?"
- "Show me emails from last week"
- "Find documents created after January 1st"

### Entity-Based Queries

- "Find all Apple-related transactions"
- "Show communications with John Smith"
- "What projects mention machine learning?"

### Analytical Queries

- "Summarize my monthly spending patterns"
- "What are the main topics in my research papers?"
- "Analyze my email communication trends"

### Comparison Queries

- "Compare Q1 and Q2 expenses"
- "How do my March and April spending differ?"
- "Compare email volume by month"

## Response Structure

### Source Attribution

Each response includes detailed source information:

- **PDF Sources**: Document name, page number, chunk content
- **Email Sources**: Subject, sender, date, snippet
- **Relevance Score**: 0.0-1.0 confidence rating
- **Context**: Surrounding text for better understanding

### Response Quality

- **Factual Accuracy**: Responses based only on provided documents
- **Source Citations**: All claims linked to specific sources
- **Confidence Indicators**: Uncertainty acknowledged when appropriate
- **Hallucination Prevention**: Built-in safeguards against false information

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Query cannot be empty"
}
```

### 404 No Results

```json
{
  "detail": "No relevant content found for the query"
}
```

### 422 Processing Error

```json
{
  "detail": "Query processing failed: Invalid content type specified"
}
```

## Integration Examples

### JavaScript Query

```javascript
const submitQuery = async (queryText) => {
  const response = await fetch('/api/v1/queries/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: queryText,
      include_sources: true,
      content_types: ['pdf', 'email']
    })
  });
  
  return response.json();
};
```

### Python Query

```python
import requests

def query_documents(query_text, token):
    data = {
        "query": query_text,
        "include_sources": True,
        "content_types": ["pdf", "email"]
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/queries/",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    return response.json()
```

## Performance Considerations

### Query Optimization

- **Specific queries** perform better than vague ones
- **Filtered queries** (by type/date) are faster
- **Shorter queries** process more quickly
- **Semantic similarity** improves with more context

### Response Times

| Query Type | Typical Response Time |
|------------|---------------------|
| Simple PDF query | 1-3 seconds |
| Complex cross-content | 3-8 seconds |
| Large result set | 5-15 seconds |

### Best Practices

1. **Be specific** in your queries
2. **Use filters** to narrow search scope
3. **Check source attribution** for accuracy
4. **Iterate queries** for better results
5. **Monitor processing times** for optimization