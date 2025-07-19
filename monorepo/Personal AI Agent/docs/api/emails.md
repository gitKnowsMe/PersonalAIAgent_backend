# Email Search API

Search and query processed Gmail emails with advanced filtering and semantic search.

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/emails/search` | Search emails with natural language |
| GET | `/api/v1/emails/` | List processed emails |
| GET | `/api/v1/emails/{id}` | Get specific email details |
| GET | `/api/v1/emails/categories` | Get email category statistics |

## Search Emails

Perform semantic search across processed emails.

```http
POST /api/v1/emails/search
```

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "emails about Apple purchases",
  "categories": ["business", "transactional"],
  "date_from": "2024-01-01",
  "date_to": "2024-03-31",
  "sender": "apple@apple.com",
  "limit": 10,
  "include_content": true
}
```

**Parameters:**
- `query` (required): Natural language search query
- `categories` (optional): Filter by email categories
- `date_from` (optional): Start date filter (ISO date)
- `date_to` (optional): End date filter (ISO date)
- `sender` (optional): Filter by sender email
- `subject_contains` (optional): Filter by subject keywords
- `limit` (optional): Maximum results (default: 10, max: 100)
- `include_content` (optional): Include full email content (default: false)

**Response:**
```json
{
  "results": [
    {
      "id": "email_123",
      "subject": "Your Apple Purchase Receipt",
      "sender": "noreply@apple.com",
      "date": "2024-03-15T10:30:00Z",
      "category": "transactional",
      "relevance_score": 0.94,
      "snippet": "Thank you for your purchase of iPhone 15 Pro...",
      "thread_id": "thread_abc123",
      "labels": ["INBOX", "CATEGORY_PURCHASES"],
      "content": "Full email content here...",
      "attachments": [
        {
          "filename": "receipt.pdf",
          "type": "application/pdf",
          "processed": true
        }
      ]
    }
  ],
  "total_results": 15,
  "query_time": 0.45,
  "categories_found": {
    "business": 3,
    "transactional": 12
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/emails/search" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "meeting about quarterly review",
    "categories": ["business"],
    "limit": 5
  }'
```

## List Emails

Retrieve processed emails with filtering options.

```http
GET /api/v1/emails/
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 50, max: 200)
- `category` (optional): Filter by category
- `sender` (optional): Filter by sender email
- `date_from` (optional): Start date filter
- `date_to` (optional): End date filter
- `has_attachments` (optional): Filter emails with attachments

**Response:**
```json
{
  "emails": [
    {
      "id": "email_123",
      "subject": "Quarterly Review Meeting",
      "sender": "manager@company.com",
      "date": "2024-03-20T14:00:00Z",
      "category": "business",
      "thread_id": "thread_def456",
      "has_attachments": true,
      "labels": ["INBOX", "IMPORTANT"],
      "snippet": "Please find attached the quarterly review agenda..."
    }
  ],
  "total": 1247,
  "skip": 0,
  "limit": 50,
  "filters_applied": {
    "category": "business",
    "date_range": "2024-01-01 to 2024-03-31"
  }
}
```

## Get Email Details

Retrieve complete details for a specific email.

```http
GET /api/v1/emails/{id}
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "email_123",
  "gmail_id": "17a8b2c3d4e5f6g7",
  "thread_id": "thread_abc123",
  "subject": "Your Apple Purchase Receipt",
  "sender": "noreply@apple.com",
  "sender_name": "Apple Store",
  "recipients": ["user@example.com"],
  "date": "2024-03-15T10:30:00Z",
  "category": "transactional",
  "classification_confidence": 0.89,
  "labels": ["INBOX", "CATEGORY_PURCHASES"],
  "content": {
    "text": "Full plain text content...",
    "html": "<html>Full HTML content...</html>"
  },
  "attachments": [
    {
      "filename": "receipt.pdf",
      "type": "application/pdf",
      "size": 45632,
      "processed": true,
      "text_content": "Extracted text from attachment..."
    }
  ],
  "thread_context": [
    {
      "email_id": "email_122",
      "subject": "Order Confirmation",
      "date": "2024-03-14T15:20:00Z",
      "sender": "orders@apple.com"
    }
  ],
  "processing_metadata": {
    "processed_at": "2024-03-15T10:35:00Z",
    "chunk_count": 3,
    "embedding_version": "v1.0"
  }
}
```

## Get Category Statistics

Retrieve email category distribution and statistics.

```http
GET /api/v1/emails/categories
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `date_from` (optional): Start date for statistics
- `date_to` (optional): End date for statistics

**Response:**
```json
{
  "total_emails": 1247,
  "date_range": {
    "from": "2024-01-01T00:00:00Z",
    "to": "2024-03-31T23:59:59Z"
  },
  "categories": {
    "business": {
      "count": 387,
      "percentage": 31.04,
      "top_senders": [
        "team@company.com",
        "calendar@company.com"
      ]
    },
    "personal": {
      "count": 245,
      "percentage": 19.65,
      "top_senders": [
        "family@gmail.com",
        "friend@yahoo.com"
      ]
    },
    "promotional": {
      "count": 423,
      "percentage": 33.92,
      "top_senders": [
        "deals@amazon.com",
        "newsletter@medium.com"
      ]
    },
    "transactional": {
      "count": 156,
      "percentage": 12.51,
      "top_senders": [
        "noreply@apple.com",
        "receipts@uber.com"
      ]
    },
    "support": {
      "count": 36,
      "percentage": 2.89,
      "top_senders": [
        "support@stripe.com",
        "help@github.com"
      ]
    }
  },
  "trends": {
    "most_active_day": "Tuesday",
    "peak_hours": ["9:00", "14:00", "18:00"],
    "monthly_distribution": {
      "2024-01": 421,
      "2024-02": 389,
      "2024-03": 437
    }
  }
}
```

## Email Categories

### Business
Work-related emails including:
- Meeting invitations and updates
- Project communications
- Team notifications
- Work-related announcements

### Personal
Personal communications including:
- Family and friend emails
- Personal correspondence
- Social invitations
- Personal updates

### Promotional
Marketing and promotional content:
- Newsletter subscriptions
- Product announcements
- Sales and deals
- Marketing campaigns

### Transactional
Account and purchase notifications:
- Purchase receipts
- Account notifications
- Service confirmations
- Billing statements

### Support
Customer service communications:
- Technical support tickets
- Help desk responses
- Service inquiries
- Problem resolution

## Search Capabilities

### Semantic Search

The system understands context and meaning:

```bash
# These queries will find similar results:
"Apple purchase receipts"
"iPhone buying confirmations"
"transactions from Apple Store"
```

### Natural Language Queries

- "Find emails about my quarterly performance review"
- "Show me all receipts from last month"
- "What did John say about the project timeline?"
- "Find customer support conversations about billing issues"

### Advanced Filtering

Combine multiple filters for precise results:

```json
{
  "query": "meeting notes",
  "categories": ["business"],
  "sender": "team@company.com",
  "date_from": "2024-03-01",
  "date_to": "2024-03-31"
}
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Query parameter is required"
}
```

### 404 Not Found

```json
{
  "detail": "Email not found or not accessible"
}
```

### 422 Invalid Parameters

```json
{
  "detail": "Invalid date format. Use ISO date format (YYYY-MM-DD)"
}
```

## Integration Examples

### JavaScript Search

```javascript
const searchEmails = async (query, filters = {}) => {
  const requestBody = {
    query,
    limit: 20,
    include_content: false,
    ...filters
  };
  
  const response = await fetch('/api/v1/emails/search', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });
  
  return response.json();
};

// Example usage
const results = await searchEmails('Apple purchases', {
  categories: ['transactional'],
  date_from: '2024-01-01'
});
```

### Python Search

```python
import requests
from datetime import datetime, timedelta

def search_emails(query, token, **filters):
    data = {
        "query": query,
        "limit": 20,
        **filters
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/emails/search",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    return response.json()

# Example: Find recent business emails
results = search_emails(
    "project update",
    token,
    categories=["business"],
    date_from=(datetime.now() - timedelta(days=30)).isoformat()
)
```

## Performance Considerations

### Search Optimization

- **Specific queries** perform better than broad searches
- **Category filtering** significantly improves speed
- **Date ranges** help narrow search scope
- **Limit results** to reasonable numbers (10-50)

### Response Times

| Search Type | Typical Response Time |
|-------------|---------------------|
| Simple query | 0.2-0.8 seconds |
| Filtered search | 0.5-1.5 seconds |
| Complex semantic search | 1-3 seconds |

### Best Practices

1. **Use category filters** when possible
2. **Limit date ranges** for better performance
3. **Avoid very broad queries** like "email"
4. **Use pagination** for large result sets
5. **Cache frequent searches** on client side