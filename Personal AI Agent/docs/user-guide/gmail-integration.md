# Gmail Integration User Guide

Connect your Gmail account to Personal AI Agent for unified email and document search capabilities.

## Getting Started

### Prerequisites

- Active Gmail account
- Personal AI Agent account
- Internet connection for OAuth setup

### Initial Setup

1. **Configure OAuth Credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth2 credentials
   - Add redirect URI: `http://localhost:8000/api/v1/gmail/callback`

2. **Update Environment Configuration**
   ```env
   GMAIL_CLIENT_ID=your_client_id_here
   GMAIL_CLIENT_SECRET=your_client_secret_here
   GMAIL_REDIRECT_URI=http://localhost:8000/api/v1/gmail/callback
   ```

3. **Initialize Gmail Connection**
   ```bash
   python setup_gmail.py
   ```

## Authorization Process

### Web Interface Authorization

1. Navigate to Gmail integration section
2. Click "Connect Gmail Account"
3. You'll be redirected to Google authorization
4. Sign in to your Gmail account
5. Grant permissions to Personal AI Agent
6. You'll be redirected back with confirmation

### API Authorization

```bash
# Get authorization URL
curl -X GET "http://localhost:8000/api/v1/gmail/auth-url" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Follow the returned URL in your browser
# Google will redirect to callback URL automatically
```

### Permissions Requested

- **Read access to Gmail**: View your email messages and settings
- **No send permissions**: Cannot send emails on your behalf
- **No delete permissions**: Cannot delete your emails
- **Offline access**: Maintain connection when you're not actively using the app

## Email Sync Process

### Initial Sync

After authorization, perform your first email sync:

1. **Choose sync parameters**:
   - Number of emails (default: 100, max: 1000)
   - Date range (optional)
   - Specific Gmail query (optional)

2. **Start sync process**:
   ```bash
   # Sync recent 200 emails
   curl -X POST "http://localhost:8000/api/v1/gmail/sync" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"limit": 200}'
   ```

3. **Monitor progress**:
   - Processing status updates
   - Email classification results
   - Completion notification

### Sync Strategies

#### Recent Emails (Recommended)
```json
{
  "limit": 500,
  "query": "in:inbox after:2024/01/01"
}
```

#### Specific Senders
```json
{
  "limit": 200,
  "query": "from:important@company.com OR from:client@example.com"
}
```

#### Date Range
```json
{
  "limit": 1000,
  "query": "after:2024/01/01 before:2024/03/31"
}
```

#### Category Filtering
```json
{
  "limit": 300,
  "query": "category:primary -category:promotions"
}
```

## Email Classification

Emails are automatically classified into five categories:

### Business Emails

**Characteristics:**
- Meeting invitations and calendar events
- Project updates and work communications
- Team notifications and announcements
- Professional correspondence

**Examples:**
- "Team standup meeting tomorrow at 10 AM"
- "Q4 project milestone update"
- "Client presentation feedback"

**Search optimization:**
- Work-related keywords
- Professional terminology
- Meeting and project references

### Personal Emails

**Characteristics:**
- Family and friend communications
- Personal invitations and social events
- Private conversations and updates
- Non-work related correspondence

**Examples:**
- "Family dinner this Sunday"
- "Happy birthday! Hope you have a great day"
- "Weekend hiking plans"

**Search optimization:**
- Personal names and relationships
- Social and family contexts
- Informal communication patterns

### Promotional Emails

**Characteristics:**
- Marketing and advertising content
- Newsletter subscriptions
- Product announcements and deals
- Promotional campaigns

**Examples:**
- "50% off sale this weekend only"
- "New features in our latest update"
- "Monthly newsletter from your favorite blog"

**Search optimization:**
- Marketing keywords
- Deal and promotion terms
- Brand and product names

### Transactional Emails

**Characteristics:**
- Purchase receipts and confirmations
- Account notifications and updates
- Service confirmations and bookings
- Billing and payment information

**Examples:**
- "Your receipt from Apple Store"
- "Netflix subscription renewed"
- "Uber trip receipt"

**Search optimization:**
- Transaction amounts and dates
- Service and vendor names
- Purchase and payment terms

### Support Emails

**Characteristics:**
- Customer service interactions
- Technical support conversations
- Help desk communications
- Problem resolution threads

**Examples:**
- "Your support ticket #12345 has been updated"
- "Follow-up on your technical issue"
- "Solution to your billing question"

**Search optimization:**
- Support and help keywords
- Issue and problem descriptions
- Ticket and case references

## Thread Processing

### Thread Awareness

The system maintains email thread context:

- **Conversation History**: Full thread preserved
- **Chronological Order**: Messages ordered by time
- **Context Preservation**: Related emails linked
- **Reply Chain**: Complete conversation flow

### Benefits

1. **Better Understanding**: Full conversation context
2. **Accurate Responses**: Complete information
3. **Relationship Mapping**: Understand email relationships
4. **Follow-up Tracking**: Monitor conversation progress

## Email Search Capabilities

### Natural Language Queries

```bash
# Find specific conversations
"Find emails about the quarterly review meeting"
"Show me all receipts from Apple"
"What did John say about the project deadline?"

# Category-specific searches
"Find business emails from last week"
"Show me all promotional emails from Amazon"
"Find support conversations about billing issues"

# Content-based searches
"Emails containing financial information"
"Find discussions about vacation plans"
"Show me all meeting invitations"
```

### Advanced Filtering

```bash
# Date-based queries
"Find emails from March 2024"
"Show me recent support emails"
"Find promotional emails from last month"

# Sender-based queries
"All emails from my manager"
"Find emails from family members"
"Show me customer service responses"

# Content and context
"Find emails with attachments about reports"
"Show me email threads longer than 5 messages"
"Find urgent or important emails"
```

### Cross-Content Queries

Combine email and document search:

```bash
"Find all information about Apple purchases"
"Show me everything related to Project Alpha"
"Find financial information from both emails and documents"
```

## Managing Gmail Connection

### Connection Status

Check your Gmail connection:

```bash
curl -X GET "http://localhost:8000/api/v1/gmail/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Status indicators:**
- **Connected**: Active connection with valid tokens
- **Expired**: Connection exists but tokens need refresh
- **Error**: Connection issues or permission problems
- **Not Connected**: No Gmail account linked

### Sync History

Monitor sync activities:
- **Sync ID**: Unique identifier for each sync
- **Email Count**: Number of emails processed
- **Categories**: Distribution across email types
- **Processing Time**: Duration of sync operation
- **Status**: Success or error information

### Disconnecting Gmail

To remove Gmail integration:

```bash
curl -X DELETE "http://localhost:8000/api/v1/gmail/disconnect" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "delete_emails": true,
    "revoke_access": true
  }'
```

**Options:**
- `delete_emails`: Remove processed emails from system
- `revoke_access`: Revoke OAuth tokens with Google

## Privacy and Security

### Data Privacy

- **Local Processing**: Email content processed locally
- **No External Sharing**: Data never sent to external services
- **User Isolation**: Your emails separate from other users
- **Encrypted Storage**: Secure storage of OAuth tokens

### Security Features

- **OAuth2 Standard**: Industry-standard authentication
- **Minimal Permissions**: Only necessary Gmail access
- **Token Refresh**: Automatic token renewal
- **Revocable Access**: Can disconnect anytime

### Data Retention

- **Configurable Retention**: Set how long to keep emails
- **Selective Deletion**: Remove specific email categories
- **Complete Cleanup**: Full data removal option
- **Audit Trail**: Track data access and modifications

## Troubleshooting

### Authorization Issues

**"OAuth error during authorization"**
- Verify client ID and secret in configuration
- Check redirect URI matches exactly
- Ensure Gmail API is enabled in Google Cloud Console
- Try re-authorizing with fresh credentials

**"Permission denied"**
- Check required scopes are granted
- Verify account has necessary permissions
- Try re-authorization with full permissions
- Contact administrator if using organization account

### Sync Issues

**"Sync failed - rate limit exceeded"**
- Wait before retrying (usually 1 hour)
- Reduce sync batch size
- Use more specific Gmail queries
- Spread syncs across longer time periods

**"No emails found to sync"**
- Check Gmail query syntax
- Verify date ranges are correct
- Ensure emails exist in specified criteria
- Try broader search parameters

**"Processing errors during sync"**
- Check system resources (memory, disk space)
- Review error logs for specific issues
- Try smaller batch sizes
- Restart sync process

### Search Issues

**"No email results found"**
- Verify emails were successfully synced
- Check email category filters
- Try broader search terms
- Ensure proper authentication

**"Poor search quality"**
- Use more specific search terms
- Include email context in queries
- Try different phrasings
- Check email content was properly processed

## Performance Optimization

### Sync Performance

1. **Batch Size Optimization**
   - Start with smaller batches (100-200 emails)
   - Increase gradually based on performance
   - Monitor processing times and memory usage

2. **Query Optimization**
   - Use specific Gmail search queries
   - Filter by date ranges when possible
   - Exclude unnecessary email categories

3. **Scheduling**
   - Sync during off-peak hours
   - Perform regular incremental syncs
   - Avoid concurrent large syncs

### Search Performance

1. **Query Specificity**
   - Use precise search terms
   - Include relevant context
   - Filter by email categories

2. **Result Limiting**
   - Set reasonable result limits
   - Use pagination for large result sets
   - Cache frequently accessed results

## Best Practices

### Initial Setup

1. **Start Small**: Begin with recent emails (last 3 months)
2. **Test Thoroughly**: Verify classification accuracy
3. **Monitor Resources**: Watch system performance
4. **Incremental Growth**: Gradually increase sync scope

### Ongoing Usage

1. **Regular Syncs**: Schedule periodic email updates
2. **Category Review**: Occasionally verify classification accuracy
3. **Query Refinement**: Improve search techniques over time
4. **Cleanup**: Remove old or irrelevant emails

### Security

1. **Token Management**: Monitor OAuth token status
2. **Permission Review**: Regularly review granted permissions
3. **Access Audit**: Track who has access to email data
4. **Backup Strategy**: Consider backup of important email data