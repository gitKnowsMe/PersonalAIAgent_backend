# Gmail API

Integrate Gmail emails for unified search and querying capabilities.

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/gmail/auth-url` | Get OAuth2 authorization URL |
| GET | `/api/v1/gmail/callback` | Handle OAuth2 callback |
| POST | `/api/v1/gmail/sync` | Sync emails from Gmail |
| GET | `/api/v1/gmail/status` | Get connection status |
| DELETE | `/api/v1/gmail/disconnect` | Disconnect Gmail account |

## Gmail OAuth Setup

Before using Gmail integration, set up OAuth2 credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable Gmail API
4. Create OAuth2 credentials (Web Application)
5. Add redirect URI: `http://localhost:8000/api/v1/gmail/callback`
6. Configure environment variables:

```env
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:8000/api/v1/gmail/callback
```

## Get Authorization URL

Get the URL for Gmail OAuth2 authorization.

```http
GET /api/v1/gmail/auth-url
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=...",
  "state": "random_state_string"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/gmail/auth-url" \
  -H "Authorization: Bearer <token>"
```

### Authorization Flow

1. **Get auth URL** from this endpoint
2. **Redirect user** to the returned URL
3. **User authorizes** access to Gmail
4. **Google redirects** to callback URL with authorization code
5. **Callback endpoint** exchanges code for access tokens

## OAuth2 Callback

Handle the OAuth2 callback from Google.

```http
GET /api/v1/gmail/callback?code=<auth_code>&state=<state>
```

**Query Parameters:**
- `code`: Authorization code from Google
- `state`: State parameter for CSRF protection

**Response:**
```json
{
  "message": "Gmail connected successfully",
  "email": "user@gmail.com",
  "status": "connected"
}
```

!!! note "Automatic Handling"
    This endpoint is called automatically by Google after user authorization. You typically don't call it directly.

## Sync Emails

Fetch and process emails from Gmail.

```http
POST /api/v1/gmail/sync
```

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "limit": 100,
  "query": "in:inbox after:2024/01/01",
  "force_resync": false
}
```

**Parameters:**
- `limit` (optional): Number of emails to sync (default: 100, max: 1000)
- `query` (optional): Gmail search query (default: recent emails)
- `force_resync` (optional): Re-process existing emails (default: false)

**Response:**
```json
{
  "sync_id": "sync_12345",
  "status": "completed",
  "emails_processed": 87,
  "emails_new": 23,
  "emails_updated": 4,
  "emails_skipped": 60,
  "categories": {
    "business": 15,
    "personal": 8,
    "promotional": 35,
    "transactional": 12,
    "support": 3
  },
  "processing_time": 45.67,
  "started_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:00:45Z"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/gmail/sync" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 200,
    "query": "in:inbox after:2024/01/01 before:2024/02/01"
  }'
```

### Gmail Search Queries

Use Gmail search syntax for targeted syncing:

```bash
# Recent emails (default)
"in:inbox after:2024/01/01"

# Specific sender
"from:apple@apple.com"

# Subject keywords
"subject:invoice OR subject:receipt"

# Date range
"after:2024/01/01 before:2024/02/01"

# Labels
"label:important"

# Exclude promotions
"-category:promotions"
```

## Get Connection Status

Check Gmail connection and sync status.

```http
GET /api/v1/gmail/status
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "connected",
  "email": "user@gmail.com",
  "connected_at": "2024-01-01T00:00:00Z",
  "last_sync": "2024-01-02T10:30:00Z",
  "total_emails": 1247,
  "sync_history": [
    {
      "sync_id": "sync_12345",
      "started_at": "2024-01-02T10:30:00Z",
      "emails_processed": 87,
      "status": "completed"
    }
  ],
  "token_status": "valid",
  "permissions": [
    "https://www.googleapis.com/auth/gmail.readonly"
  ]
}
```

**Status Values:**
- `not_connected`: No Gmail account linked
- `connected`: Active connection with valid tokens
- `expired`: Connection exists but tokens expired
- `error`: Connection error or permission issues

## Disconnect Gmail

Remove Gmail connection and delete associated data.

```http
DELETE /api/v1/gmail/disconnect
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "delete_emails": true,
  "revoke_access": true
}
```

**Parameters:**
- `delete_emails` (optional): Delete processed emails (default: false)
- `revoke_access` (optional): Revoke Google OAuth tokens (default: true)

**Response:**
```json
{
  "message": "Gmail disconnected successfully",
  "emails_deleted": 1247,
  "access_revoked": true
}
```

!!! warning "Data Deletion"
    Disconnecting with `delete_emails: true` permanently removes all processed emails and their vector embeddings.

## Email Processing

### Automatic Classification

Emails are automatically classified into categories:

- **Business**: Work-related communications, meetings, project updates
- **Personal**: Family, friends, personal communications
- **Promotional**: Marketing emails, newsletters, deals
- **Transactional**: Receipts, confirmations, account notifications
- **Support**: Customer service, technical support

### Thread Processing

- **Thread Awareness**: Related emails grouped together
- **Context Preservation**: Full conversation context maintained
- **Chronological Order**: Emails processed in temporal sequence
- **Attachment Handling**: Text extraction from supported attachments

### Data Storage

- **Vector Embeddings**: Semantic search capabilities
- **Metadata**: Sender, subject, date, labels, thread ID
- **Content**: Full email body with formatting preserved
- **Attachments**: Text content extracted and indexed

## Error Responses

### 401 Unauthorized - No Gmail Connection

```json
{
  "detail": "Gmail account not connected. Please authorize access first."
}
```

### 403 Forbidden - Insufficient Permissions

```json
{
  "detail": "Insufficient Gmail permissions. Please re-authorize with required scopes."
}
```

### 429 Rate Limited

```json
{
  "detail": "Gmail API rate limit exceeded. Please wait before retrying.",
  "retry_after": 60
}
```

### 422 Invalid Query

```json
{
  "detail": "Invalid Gmail search query: Unexpected search operator"
}
```

## Integration Examples

### Complete OAuth Flow (JavaScript)

```javascript
// Step 1: Get authorization URL
const getAuthUrl = async () => {
  const response = await fetch('/api/v1/gmail/auth-url', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { auth_url } = await response.json();
  
  // Redirect user to Google authorization
  window.location.href = auth_url;
};

// Step 2: Handle callback (automatic)
// Google redirects to /api/v1/gmail/callback

// Step 3: Sync emails
const syncEmails = async () => {
  const response = await fetch('/api/v1/gmail/sync', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      limit: 200,
      query: 'in:inbox after:2024/01/01'
    })
  });
  
  return response.json();
};
```

### Python Integration

```python
import requests

class GmailIntegration:
    def __init__(self, token):
        self.token = token
        self.base_url = "http://localhost:8000/api/v1"
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def get_auth_url(self):
        response = requests.get(
            f"{self.base_url}/gmail/auth-url",
            headers=self.headers
        )
        return response.json()["auth_url"]
    
    def sync_emails(self, limit=100, query=None):
        data = {"limit": limit}
        if query:
            data["query"] = query
            
        response = requests.post(
            f"{self.base_url}/gmail/sync",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def get_status(self):
        response = requests.get(
            f"{self.base_url}/gmail/status",
            headers=self.headers
        )
        return response.json()
```

## Best Practices

### Sync Strategy

1. **Initial Sync**: Start with recent emails (`limit: 500`)
2. **Incremental Sync**: Regular small syncs for new emails
3. **Targeted Sync**: Use queries for specific content
4. **Scheduled Sync**: Automate regular email fetching

### Performance Optimization

1. **Batch Processing**: Sync in reasonable batches (100-500 emails)
2. **Query Filtering**: Use Gmail queries to reduce processing
3. **Avoid Re-processing**: Use `force_resync: false` for existing emails
4. **Monitor Rate Limits**: Respect Gmail API quotas

### Security Considerations

1. **Minimal Permissions**: Request only required OAuth scopes
2. **Token Security**: Store refresh tokens securely
3. **Regular Cleanup**: Remove old or unused connections
4. **Audit Access**: Monitor sync activities and permissions