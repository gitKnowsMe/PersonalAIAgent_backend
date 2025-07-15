# Frontend Integration Guide

This guide explains how to integrate your Vercel v0 frontend with the Personal AI Agent backend.

## Integration Strategy

**Separate Deployment Approach** (Recommended)
- Frontend: Deploy to Vercel (your modern v0 UI)
- Backend: Run locally or on server (comprehensive API)
- Communication: CORS-enabled API calls

## Step 1: Backend Configuration

### 1.1 Update Environment Variables

Copy `.env.example` to `.env` and update CORS settings:

```bash
cp .env.example .env
```

Edit `.env` file:
```env
# Add your Vercel domain to CORS
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000,http://localhost:8000

# Ensure backend settings are correct
HOST=0.0.0.0  # Important: Change from localhost for external access
PORT=8000
DEBUG=false   # Set to false for production
```

### 1.2 Test Backend API

Start your backend:
```bash
python main.py
```

Test API endpoints:
```bash
curl http://localhost:8000/api/health-check
```

## Step 2: Frontend Configuration

### 2.1 Create API Configuration

In your v0 frontend, create `lib/api.ts`:

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiConfig = {
  baseURL: API_BASE_URL,
  endpoints: {
    // Authentication
    login: '/api/auth/login',
    register: '/api/auth/register',
    
    // Documents
    uploadDocument: '/api/documents/upload',
    getDocuments: '/api/documents/',
    deleteDocument: (id: string) => `/api/documents/${id}`,
    
    // Queries
    askQuestion: '/api/queries/',
    getQueries: '/api/queries/',
    
    // Gmail
    gmailAuth: '/api/gmail/auth-url',
    gmailCallback: '/api/gmail/callback',
    gmailSync: '/api/gmail/sync',
    gmailStatus: '/api/gmail/status',
    gmailDisconnect: '/api/gmail/disconnect',
    
    // Health
    healthCheck: '/api/health-check'
  }
};

// API client with authentication
export class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return response;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication methods
  async login(username: string, password: string) {
    const response = await this.request(apiConfig.endpoints.login, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(email: string, username: string, password: string) {
    const response = await this.request(apiConfig.endpoints.register, {
      method: 'POST',
      body: JSON.stringify({ email, username, password }),
    });
    return response.json();
  }

  // Document methods
  async uploadDocument(file: File, title: string, description?: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) formData.append('description', description);

    const response = await this.request(apiConfig.endpoints.uploadDocument, {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
    return response.json();
  }

  async getDocuments() {
    const response = await this.request(apiConfig.endpoints.getDocuments);
    return response.json();
  }

  // Query methods
  async askQuestion(question: string, source?: string) {
    const response = await this.request(apiConfig.endpoints.askQuestion, {
      method: 'POST',
      body: JSON.stringify({ question, source }),
    });
    return response.json();
  }

  // Gmail methods
  async getGmailAuthUrl() {
    const response = await this.request(apiConfig.endpoints.gmailAuth);
    return response.json();
  }

  async getGmailStatus() {
    const response = await this.request(apiConfig.endpoints.gmailStatus);
    return response.json();
  }

  async syncGmail(maxEmails?: number) {
    const response = await this.request(apiConfig.endpoints.gmailSync, {
      method: 'POST',
      body: JSON.stringify({ max_emails: maxEmails }),
    });
    return response.json();
  }
}

export const apiClient = new ApiClient();
```

### 2.2 Create Environment Variables

Create `.env.local` in your v0 frontend:

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production deployment:
```env
# .env.production
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
```

### 2.3 Update Chat Interface Component

Modify your `components/chat-interface.tsx`:

```typescript
// Update the handleSubmit function to use real API
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  if (!input.trim()) return;

  const userMessage: Message = {
    id: Date.now().toString(),
    content: input.trim(),
    role: 'user',
    timestamp: new Date(),
  };

  setMessages(prev => [...prev, userMessage]);
  setInput('');
  setIsLoading(true);

  try {
    // Replace setTimeout with actual API call
    const response = await apiClient.askQuestion(userMessage.content);
    
    const aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: response.answer || 'Sorry, I could not process your question.',
      role: 'assistant',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, aiMessage]);
  } catch (error) {
    console.error('Failed to get AI response:', error);
    const errorMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: 'Sorry, there was an error processing your request.',
      role: 'assistant',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, errorMessage]);
  } finally {
    setIsLoading(false);
  }
};
```

## Step 3: Deploy to Vercel

### 3.1 Environment Variables in Vercel

1. Go to your Vercel dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add:
   ```
   NEXT_PUBLIC_API_URL = https://your-backend-domain.com
   ```

**Important**: Your frontend is client-side only and doesn't need DATABASE_URL. The DATABASE_URL is already configured in your local backend environment.

### 3.2 Deploy

```bash
# In your v0 frontend directory
npm run build
# Push to GitHub (auto-deploys to Vercel)
```

## Step 4: Backend Deployment

For production, you need to deploy your FastAPI backend to a server:

### 4.1 Database Setup (Local PostgreSQL)

Your project is already configured with local PostgreSQL:
```env
DATABASE_URL=postgresql://personal_ai_agent@localhost:5432/personal_ai_agent
```

**Local PostgreSQL is already set up and running** - no external services needed for private deployment.

### 4.2 Backend Environment Configuration

Your `.env` is already configured for local deployment. For remote access, you may only need to update:
```env
# Your existing PostgreSQL database (already configured)
DATABASE_URL=postgresql://personal_ai_agent@localhost:5432/personal_ai_agent

# CORS - Add your Vercel domain to existing settings
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000

# Server settings - allow external access if needed
HOST=0.0.0.0  # Change from localhost for external access
PORT=8000
DEBUG=false

# Your existing Gmail OAuth settings are already configured
```

### 4.3 Local Backend Deployment

For a private, local setup, simply run your backend locally:

**Option A: Local Development Server**
```bash
# Your backend is already configured - just run it
python main.py
# Backend will be available at http://localhost:8000
```

**Option B: Local Network Access (Optional)**
If you want to access from other devices on your network:
```bash
# Update .env: HOST=0.0.0.0
# Then run: python main.py
# Backend accessible at http://your-local-ip:8000
```

**Option C: Keep Everything Local**
- Frontend: Deploy to Vercel (public)  
- Backend: Run locally (private)
- Database: Local PostgreSQL (private)
- Perfect for keeping your data private while having a modern UI

### 4.4 Database Setup

Your database is already set up and running. If you need to reset or create admin user:
```bash
# Your database is already configured - these are optional
python setup_db.py      # Only if you need to reset tables
python create_admin.py  # Only if you need a new admin user
```

## Step 5: Test Integration

1. **Test Authentication**: Try login/register from v0 frontend
2. **Test Document Upload**: Upload a PDF through the UI
3. **Test Chat**: Ask questions about uploaded documents
4. **Test Gmail**: Connect Gmail and sync emails

## API Endpoints Reference

Your backend provides these endpoints:

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration

### Documents
- `POST /api/documents/upload` - Upload PDF
- `GET /api/documents/` - List documents
- `DELETE /api/documents/{id}` - Delete document

### Queries
- `POST /api/queries/` - Ask questions
- `GET /api/queries/` - Query history

### Gmail
- `GET /api/gmail/auth-url` - Get OAuth URL
- `POST /api/gmail/sync` - Sync emails
- `GET /api/gmail/status` - Account status

## Troubleshooting

### CORS Issues
- Ensure `ALLOWED_ORIGINS` includes your Vercel domain
- Check browser console for CORS errors

### Authentication Issues
- Verify JWT token is being sent in Authorization header
- Check token expiration (default: 30 minutes)

### API Connection Issues
- Verify backend is running and accessible
- Test API endpoints with curl/Postman
- Check network/firewall settings

## Security Considerations

1. **Use HTTPS** in production
2. **Secure API keys** - Never expose in frontend code
3. **Validate origins** - Don't use `*` for CORS in production
4. **Token management** - Implement refresh tokens for longer sessions

## Next Steps

1. Add error boundaries for better error handling
2. Implement loading states for all API calls
3. Add offline support with service workers
4. Implement real-time features with WebSockets (optional)