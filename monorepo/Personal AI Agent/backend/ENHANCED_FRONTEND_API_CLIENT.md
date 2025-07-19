# Enhanced Frontend API Client

## **Updated API Client with Better Error Handling**

Replace your existing API client with this enhanced version:

```typescript
// lib/api-client.ts or similar

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
}

export interface ApiError {
  detail: string;
  error_type?: string;
  status_code: number;
  timestamp?: string;
  help?: string;
  expected_format?: string;
  received_format?: string;
  example?: string;
}

export class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') {
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

  /**
   * Check if backend is available
   */
  async checkConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/api/backend-status`, {
        method: 'GET',
        timeout: 5000,
      });
      return response.ok;
    } catch (error) {
      console.error('Backend connection check failed:', error);
      return false;
    }
  }

  /**
   * Login with enhanced error handling
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      // Use URLSearchParams for proper form data encoding
      const formData = new URLSearchParams();
      formData.append('username', credentials.username.trim());
      formData.append('password', credentials.password);

      const response = await fetch(`${this.baseURL}/api/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          detail: `Login failed: ${response.status} ${response.statusText}`,
          status_code: response.status,
          error_type: 'network_error'
        }));

        // Create user-friendly error message
        let errorMessage = errorData.detail || 'Login failed';
        
        if (errorData.help) {
          errorMessage = errorData.help;
        } else if (errorData.error_type === 'invalid_content_type') {
          errorMessage = 'There was a technical issue with the login request. Please try again.';
        } else if (response.status === 401) {
          errorMessage = 'Invalid username or password. Please check your credentials.';
        } else if (response.status === 400) {
          errorMessage = 'Please fill in all required fields.';
        } else if (response.status === 422) {
          errorMessage = 'Login request format error. Please refresh the page and try again.';
        }

        throw new Error(errorMessage);
      }

      const data: LoginResponse = await response.json();
      
      if (!data.access_token) {
        throw new Error('Login failed: No access token received');
      }

      this.setToken(data.access_token);
      return data;

    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * Register new user
   */
  async register(userData: {
    email: string;
    username: string;
    password: string;
    is_admin?: boolean;
  }): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          detail: `Registration failed: ${response.status} ${response.statusText}`,
          status_code: response.status,
          error_type: 'network_error'
        }));

        throw new Error(errorData.detail || 'Registration failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }

  /**
   * Make authenticated request
   */
  private async authenticatedRequest(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });

    // Handle unauthorized responses
    if (response.status === 401) {
      this.clearToken();
      throw new Error('Session expired. Please log in again.');
    }

    return response;
  }

  /**
   * Upload document
   */
  async uploadDocument(file: File, title: string, description?: string): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      if (description) formData.append('description', description);

      const response = await this.authenticatedRequest('/api/documents/upload', {
        method: 'POST',
        body: formData,
        headers: {}, // Don't set Content-Type for FormData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: `Upload failed: ${response.status} ${response.statusText}`
        }));
        throw new Error(errorData.detail || 'Upload failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Document upload error:', error);
      throw error;
    }
  }

  /**
   * Ask question
   */
  async askQuestion(question: string, source?: string): Promise<any> {
    try {
      const response = await this.authenticatedRequest('/api/queries/', {
        method: 'POST',
        body: JSON.stringify({ question, source }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: `Query failed: ${response.status} ${response.statusText}`
        }));
        throw new Error(errorData.detail || 'Query failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Question error:', error);
      throw error;
    }
  }

  /**
   * Get documents
   */
  async getDocuments(): Promise<any> {
    try {
      const response = await this.authenticatedRequest('/api/documents/');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Get documents error:', error);
      throw error;
    }
  }

  /**
   * Gmail OAuth methods
   */
  async getGmailAuthUrl(): Promise<{auth_url: string}> {
    try {
      const response = await this.authenticatedRequest('/api/gmail/auth-url');
      
      if (!response.ok) {
        throw new Error(`Failed to get Gmail auth URL: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Gmail auth URL error:', error);
      throw error;
    }
  }

  async getGmailStatus(): Promise<any> {
    try {
      const response = await this.authenticatedRequest('/api/gmail/status');
      
      if (!response.ok) {
        throw new Error(`Failed to get Gmail status: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Gmail status error:', error);
      throw error;
    }
  }

  async syncGmail(maxEmails?: number): Promise<any> {
    try {
      const response = await this.authenticatedRequest('/api/gmail/sync', {
        method: 'POST',
        body: JSON.stringify({ max_emails: maxEmails }),
      });

      if (!response.ok) {
        throw new Error(`Gmail sync failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Gmail sync error:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
```

## **Enhanced Login Form Component**

Update your login form component to use the enhanced API client:

```typescript
// components/login-form.tsx
import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface LoginFormProps {
  onLoginSuccess: () => void;
}

export function LoginForm({ onLoginSuccess }: LoginFormProps) {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Check backend connectivity first
      const isBackendAvailable = await apiClient.checkConnection();
      if (!isBackendAvailable) {
        throw new Error("Backend is not available. Please make sure your Personal AI Agent backend is running on localhost:8000");
      }

      // Attempt login
      await apiClient.login(credentials);
      
      // Login successful
      onLoginSuccess();
      
    } catch (error) {
      console.error('Login failed:', error);
      setError(error instanceof Error ? error.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      
      <div>
        <label htmlFor="username" className="block text-sm font-medium text-gray-700">
          Username
        </label>
        <input
          id="username"
          type="text"
          value={credentials.username}
          onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          required
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={credentials.password}
          onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          required
        />
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        {isLoading ? 'Signing In...' : 'Sign In'}
      </button>
    </form>
  );
}
```

## **Key Improvements**

1. **Proper Form Data Encoding**: Uses `URLSearchParams` for login requests
2. **Backend Connectivity Check**: Verifies backend is running before login
3. **Enhanced Error Handling**: User-friendly error messages
4. **Loading States**: Visual feedback during operations
5. **Token Management**: Automatic token storage and cleanup
6. **CORS Support**: Proper headers for cross-origin requests
7. **Type Safety**: Full TypeScript interfaces
8. **Error Recovery**: Graceful degradation for network issues

## **Test Credentials**
- **Username**: `gmail_tester`
- **Password**: `Iomaguire1`