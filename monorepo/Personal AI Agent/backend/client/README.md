# Personal AI Agent - API Client

TypeScript client library for seamless integration with the Personal AI Agent backend API.

## Installation

### For Next.js/React Projects

```bash
# Copy the client files to your project
cp -r client/ ./lib/api-client/

# Install dependencies
npm install typescript @types/node
```

### For Other Projects

```bash
# Copy the api-client.ts file to your project
cp client/api-client.ts ./src/lib/
```

## Quick Start

```typescript
import { PersonalAIClient } from './lib/api-client';

// Create client instance
const client = new PersonalAIClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  retries: 3
});

// Login
const loginResult = await client.login({
  username: 'your-username',
  password: 'your-password'
});

if (loginResult.data) {
  console.log('Logged in successfully!');
  
  // Upload document
  const file = new File(['content'], 'document.pdf', { type: 'application/pdf' });
  const uploadResult = await client.uploadDocument({
    title: 'My Document',
    description: 'Test document',
    file: file
  });
  
  // Submit query
  const queryResult = await client.submitQuery({
    question: 'What is this document about?',
    document_id: uploadResult.data?.id
  });
  
  console.log('Answer:', queryResult.data?.answer);
}
```

## API Methods

### Authentication

```typescript
// Login
const result = await client.login({
  username: 'username',
  password: 'password'
});

// Logout
await client.logout();

// Manual token management
client.setToken('your-jwt-token');
const token = client.getToken();
client.clearToken();
```

### Documents

```typescript
// Upload document
const uploadResult = await client.uploadDocument({
  title: 'Document Title',
  description: 'Optional description',
  file: fileObject
});

// Get all documents
const documents = await client.getDocuments();

// Delete document
await client.deleteDocument(documentId);
```

### Queries

```typescript
// Submit query
const queryResult = await client.submitQuery({
  question: 'Your question here',
  document_id: 123 // Optional: query specific document
});

// Get query history
const queries = await client.getQueries();
```

### Gmail Integration

```typescript
// Get Gmail accounts
const accounts = await client.getGmailAccounts();

// Connect Gmail (redirects to OAuth)
client.connectGmail();

// Sync emails
await client.syncGmailEmails(accountId, 100);

// Disconnect Gmail
await client.disconnectGmail(accountId);
```

### Health Check

```typescript
const health = await client.healthCheck();
console.log('API Status:', health.data?.status);
```

## Error Handling

```typescript
const result = await client.submitQuery({
  question: 'Test question'
});

if (result.error) {
  console.error('API Error:', result.error);
  console.error('Status Code:', result.status);
} else {
  console.log('Success:', result.data);
}
```

## Configuration

```typescript
const client = new PersonalAIClient({
  baseUrl: 'https://api.yourdomain.com',
  timeout: 30000,        // 30 seconds
  retries: 3             // Retry failed requests 3 times
});
```

## Environment Variables

```bash
# .env.local (Next.js)
NEXT_PUBLIC_API_URL=http://localhost:8000

# .env (React)
REACT_APP_API_URL=http://localhost:8000
```

## TypeScript Support

All methods are fully typed with TypeScript interfaces:

```typescript
import type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  DocumentResponse,
  QueryResponse,
  GmailAccountResponse
} from './lib/api-client';
```

## React Hook Example

```typescript
import { useState, useEffect } from 'react';
import { PersonalAIClient } from './lib/api-client';

const useApiClient = () => {
  const [client] = useState(() => new PersonalAIClient({
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }));

  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const login = async (username: string, password: string) => {
    const result = await client.login({ username, password });
    if (result.data) {
      setIsAuthenticated(true);
      return true;
    }
    return false;
  };

  const logout = async () => {
    await client.logout();
    setIsAuthenticated(false);
  };

  return { client, isAuthenticated, login, logout };
};

export default useApiClient;
```

## Production Considerations

1. **HTTPS**: Always use HTTPS in production
2. **CORS**: Ensure backend CORS is configured for your domain
3. **Token Storage**: Store JWT tokens securely (httpOnly cookies recommended)
4. **Error Handling**: Implement comprehensive error handling
5. **Rate Limiting**: Respect API rate limits

## Support

For issues or questions:
1. Check the [API documentation](http://localhost:8000/docs)
2. Review the [backend repository](../README.md)
3. Open an issue in the repository