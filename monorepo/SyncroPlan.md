# Personal AI Agent - Frontend & Backend Synchronization Plan

## 🎯 **Project Goal**
Synchronize and configure the Personal AI Agent backend and PersonalAIAgent_frontend to work in perfect harmony, preparing for separate deployment:
- **Frontend**: Deploy to Vercel (port 3000 during development)
- **Backend**: Keep local/on-premise (port 8000)
- **Communication**: Secure API integration with CORS configuration

## 📋 **Current Architecture Analysis**

### Backend (Personal AI Agent/backend)
- **Framework**: FastAPI with JWT authentication
- **Database**: SQLite/PostgreSQL with SQLAlchemy
- **Features**: Document processing, Gmail integration, Vector search, AI queries
- **Port**: 8000
- **API**: REST endpoints with OAuth2 form-based authentication

### Frontend (PersonalAIAgent_frontend)
- **Framework**: Next.js 15 with TypeScript
- **UI**: shadcn/ui with Radix primitives, Tailwind CSS
- **Features**: Chat interface, document upload, Gmail settings, authentication
- **Port**: 3000
- **Communication**: HTTP client with JWT token management

## 🔄 **Synchronization Strategy**

### Phase 1: Environment Configuration & CORS Setup

#### 1.1 Backend Configuration Updates

**File: `Personal AI Agent/backend/.env`**
```env
# Server Configuration
HOST=0.0.0.0  # Important: Allow external connections
PORT=8000
DEBUG=false   # Set to false for production-like testing

# CORS Configuration for Frontend Integration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://*.vercel.app

# JWT Configuration
SECRET_KEY=your-super-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60  # Increased for better UX

# Database Configuration
DATABASE_URL=sqlite:///./personal_ai_agent.db

# Gmail OAuth Configuration (for production)
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./data/uploads

# Vector Database Configuration
VECTOR_DB_PATH=./data/vector_db
```

**File: `Personal AI Agent/backend/app/core/config.py` - CORS Enhancement**
```python
# Add to Settings class
CORS_SETTINGS = {
    "allow_origins": [
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://*.vercel.app",
        # Add your Vercel domain when deployed
    ],
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["*"],
    "expose_headers": ["*"]
}

# Frontend URL for redirects
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
```

#### 1.2 Frontend Configuration Updates

**File: `PersonalAIAgent_frontend/.env.local`**
```env
# Backend API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000

# Environment
NODE_ENV=development

# Gmail OAuth (matches backend)
NEXT_PUBLIC_GMAIL_CLIENT_ID=your-gmail-client-id

# Feature Flags
NEXT_PUBLIC_ENABLE_GMAIL=true
NEXT_PUBLIC_ENABLE_DOCUMENT_UPLOAD=true
```

**File: `PersonalAIAgent_frontend/next.config.mjs` - API Proxy Configuration**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
  
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: 'http://localhost:3000' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,DELETE,PATCH,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization' },
        ],
      },
    ]
  },
}

export default nextConfig
```

### Phase 2: API Client Standardization

#### 2.1 Enhanced API Client

**File: `PersonalAIAgent_frontend/lib/api-client.ts`**
```typescript
export interface ApiConfig {
  baseURL: string;
  timeout: number;
  retries: number;
}

export class UnifiedApiClient {
  private baseURL: string;
  private timeout: number;
  private retries: number;
  private token: string | null = null;

  constructor(config?: Partial<ApiConfig>) {
    const defaultConfig: ApiConfig = {
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: 30000, // 30 seconds
      retries: 3
    };
    
    const finalConfig = { ...defaultConfig, ...config };
    this.baseURL = finalConfig.baseURL;
    this.timeout = finalConfig.timeout;
    this.retries = finalConfig.retries;
    
    // Load token from storage
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  // Token management
  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  // Connection check
  async checkConnection(): Promise<boolean> {
    try {
      const response = await this.request('/api/health-check', { 
        method: 'GET',
        timeout: 5000 
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  // Core request method with retry logic
  private async request(endpoint: string, options: RequestInit & { timeout?: number } = {}): Promise<Response> {
    const { timeout = this.timeout, ...fetchOptions } = options;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  // Authentication methods
  async login(credentials: { username: string; password: string }): Promise<{ access_token: string; token_type: string }> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username.trim());
    formData.append('password', credentials.password);

    const response = await this.request('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Login failed: ${response.status}`);
    }

    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(userData: { email: string; username: string; password: string }): Promise<any> {
    const response = await this.request('/api/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Registration failed: ${response.status}`);
    }

    return response.json();
  }

  // Document methods
  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.request('/api/documents', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }

    return response.json();
  }

  async getDocuments(): Promise<any[]> {
    const response = await this.request('/api/documents');
    
    if (!response.ok) {
      throw new Error(`Failed to fetch documents: ${response.status}`);
    }

    return response.json();
  }

  async deleteDocument(id: string): Promise<void> {
    const response = await this.request(`/api/documents/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete document: ${response.status}`);
    }
  }

  // Query methods
  async submitQuery(question: string, documentId?: string): Promise<any> {
    const response = await this.request('/api/queries/', {
      method: 'POST',
      body: JSON.stringify({ 
        question, 
        document_id: documentId || null 
      }),
    });

    if (!response.ok) {
      throw new Error(`Query failed: ${response.status}`);
    }

    return response.json();
  }

  async getQueries(): Promise<any[]> {
    const response = await this.request('/api/queries');
    
    if (!response.ok) {
      throw new Error(`Failed to fetch queries: ${response.status}`);
    }

    return response.json();
  }

  // Gmail methods
  initiateGmailAuth(): void {
    if (!this.token) {
      throw new Error('Authentication required');
    }
    window.location.href = `${this.baseURL}/api/gmail/auth-url?token=${this.token}`;
  }

  async getGmailStatus(): Promise<any> {
    const response = await this.request('/api/gmail/status');
    
    if (!response.ok) {
      throw new Error(`Failed to get Gmail status: ${response.status}`);
    }

    return response.json();
  }

  async syncGmail(): Promise<any> {
    const response = await this.request('/api/gmail/sync', {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Gmail sync failed: ${response.status}`);
    }

    return response.json();
  }

  async disconnectGmail(): Promise<void> {
    const response = await this.request('/api/gmail/disconnect', {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to disconnect Gmail: ${response.status}`);
    }
  }
}

// Export singleton instance
export const apiClient = new UnifiedApiClient();
```

#### 2.2 React Hook for API Integration

**File: `PersonalAIAgent_frontend/hooks/use-api.ts`**
```typescript
import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';

export interface UseApiState {
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  isConnected: boolean;
}

export function useApi() {
  const [state, setState] = useState<UseApiState>({
    isLoading: false,
    error: null,
    isAuthenticated: !!apiClient.token,
    isConnected: false,
  });

  // Check backend connection on mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const connected = await apiClient.checkConnection();
        setState(prev => ({ ...prev, isConnected: connected }));
      } catch {
        setState(prev => ({ ...prev, isConnected: false }));
      }
    };

    checkConnection();
    
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  const login = useCallback(async (credentials: { username: string; password: string }) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      await apiClient.login(credentials);
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        isAuthenticated: true 
      }));
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Login failed' 
      }));
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    apiClient.clearToken();
    setState(prev => ({ 
      ...prev, 
      isAuthenticated: false 
    }));
  }, []);

  const register = useCallback(async (userData: { email: string; username: string; password: string }) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    
    try {
      await apiClient.register(userData);
      setState(prev => ({ ...prev, isLoading: false }));
    } catch (error) {
      setState(prev => ({ 
        ...prev, 
        isLoading: false, 
        error: error instanceof Error ? error.message : 'Registration failed' 
      }));
      throw error;
    }
  }, []);

  return {
    ...state,
    login,
    logout,
    register,
    client: apiClient,
  };
}
```

### Phase 3: Component Integration Updates

#### 3.1 Authentication Components

**File: `PersonalAIAgent_frontend/components/auth/login-form.tsx`**
```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useApi } from '@/hooks/use-api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Wifi, WifiOff } from 'lucide-react';

export function LoginForm() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const { login, register, isLoading, error, isConnected } = useApi();
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [registerData, setRegisterData] = useState({ email: '', username: '', password: '' });
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isConnected) {
      alert('Backend is not available. Please ensure the Personal AI Agent backend is running on localhost:8000');
      return;
    }

    try {
      await login(credentials);
      router.push('/chat');
    } catch (error) {
      // Error handled by useApi hook
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isConnected) {
      alert('Backend is not available. Please ensure the Personal AI Agent backend is running on localhost:8000');
      return;
    }

    try {
      await register(registerData);
      setIsRegisterMode(false);
      alert('Registration successful! Please log in.');
    } catch (error) {
      // Error handled by useApi hook
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl font-bold">
              {isRegisterMode ? 'Create Account' : 'Login'}
            </CardTitle>
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-500" />
              )}
              <span className={`text-xs ${isConnected ? 'text-green-500' : 'text-red-500'}`}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          <CardDescription>
            {isRegisterMode 
              ? 'Create a new account to get started' 
              : 'Enter your credentials to access your Personal AI Agent'
            }
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {!isConnected && (
            <Alert className="mb-4">
              <WifiOff className="h-4 w-4" />
              <AlertDescription>
                Backend not available. Please start the Personal AI Agent backend on port 8000.
              </AlertDescription>
            </Alert>
          )}

          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {isRegisterMode ? (
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-2">
                <Input
                  type="email"
                  placeholder="Email"
                  value={registerData.email}
                  onChange={(e) => setRegisterData(prev => ({ ...prev, email: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Input
                  type="text"
                  placeholder="Username"
                  value={registerData.username}
                  onChange={(e) => setRegisterData(prev => ({ ...prev, username: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Input
                  type="password"
                  placeholder="Password"
                  value={registerData.password}
                  onChange={(e) => setRegisterData(prev => ({ ...prev, password: e.target.value }))}
                  required
                />
              </div>
              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading || !isConnected}
              >
                {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Create Account
              </Button>
            </form>
          ) : (
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Input
                  type="text"
                  placeholder="Username"
                  value={credentials.username}
                  onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Input
                  type="password"
                  placeholder="Password"
                  value={credentials.password}
                  onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                  required
                />
              </div>
              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading || !isConnected}
              >
                {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Sign In
              </Button>
            </form>
          )}

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => setIsRegisterMode(!isRegisterMode)}
              className="text-sm text-blue-500 hover:underline"
            >
              {isRegisterMode 
                ? 'Already have an account? Sign in' 
                : "Don't have an account? Sign up"
              }
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Phase 4: Testing & Validation Framework

#### 4.1 Backend Testing Script

**File: `Personal AI Agent/backend/test_integration.py`**
```python
#!/usr/bin/env python3
"""
Integration testing script for frontend-backend synchronization
"""

import requests
import json
import sys
import time
from typing import Dict, Any

class IntegrationTester:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session = requests.Session()
        self.token = None
    
    def test_health_check(self) -> bool:
        """Test backend health check endpoint"""
        try:
            response = self.session.get(f"{self.backend_url}/api/health-check", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def test_cors_headers(self) -> bool:
        """Test CORS configuration"""
        try:
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            response = self.session.options(f"{self.backend_url}/api/login", headers=headers)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            }
            
            print(f"CORS Headers: {cors_headers}")
            return 'http://localhost:3000' in response.headers.get('Access-Control-Allow-Origin', '')
        except Exception as e:
            print(f"CORS test failed: {e}")
            return False
    
    def test_login(self, username: str = "test_user", password: str = "test_password") -> bool:
        """Test login endpoint"""
        try:
            data = {
                'username': username,
                'password': password
            }
            response = self.session.post(
                f"{self.backend_url}/api/login",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get('access_token')
                return True
            else:
                print(f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Login test failed: {e}")
            return False
    
    def test_authenticated_endpoint(self) -> bool:
        """Test authenticated endpoint with token"""
        if not self.token:
            print("No token available for authenticated test")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = self.session.get(f"{self.backend_url}/api/documents", headers=headers)
            return response.status_code in [200, 204]  # Accept empty results
        except Exception as e:
            print(f"Authenticated endpoint test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("🔍 Running Frontend-Backend Integration Tests...")
        print("=" * 50)
        
        results = {}
        
        # Test 1: Health Check
        print("1. Testing health check endpoint...")
        results['health_check'] = self.test_health_check()
        print(f"   ✅ PASS" if results['health_check'] else f"   ❌ FAIL")
        
        # Test 2: CORS Configuration
        print("2. Testing CORS configuration...")
        results['cors'] = self.test_cors_headers()
        print(f"   ✅ PASS" if results['cors'] else f"   ❌ FAIL")
        
        # Test 3: Login Endpoint
        print("3. Testing login endpoint...")
        results['login'] = self.test_login()
        print(f"   ✅ PASS" if results['login'] else f"   ❌ FAIL")
        
        # Test 4: Authenticated Endpoint
        print("4. Testing authenticated endpoint...")
        results['authenticated'] = self.test_authenticated_endpoint()
        print(f"   ✅ PASS" if results['authenticated'] else f"   ❌ FAIL")
        
        print("\n📊 Test Summary:")
        print("=" * 50)
        passed = sum(results.values())
        total = len(results)
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed! Frontend-backend synchronization is ready.")
        else:
            print("⚠️  Some tests failed. Please check the configuration.")
        
        return results

if __name__ == "__main__":
    tester = IntegrationTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if not all(results.values()):
        sys.exit(1)
```

#### 4.2 Frontend Testing Component

**File: `PersonalAIAgent_frontend/components/dev/connection-tester.tsx`**
```typescript
'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Wifi, WifiOff, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface TestResult {
  name: string;
  status: 'pending' | 'success' | 'error';
  message?: string;
}

export function ConnectionTester() {
  const [tests, setTests] = useState<TestResult[]>([
    { name: 'Backend Connection', status: 'pending' },
    { name: 'Health Check', status: 'pending' },
    { name: 'CORS Configuration', status: 'pending' },
    { name: 'Authentication Flow', status: 'pending' },
  ]);
  const [isRunning, setIsRunning] = useState(false);

  const updateTest = (index: number, status: TestResult['status'], message?: string) => {
    setTests(prev => prev.map((test, i) => 
      i === index ? { ...test, status, message } : test
    ));
  };

  const runTests = async () => {
    setIsRunning(true);
    
    // Reset all tests
    setTests(prev => prev.map(test => ({ ...test, status: 'pending' })));

    // Test 1: Backend Connection
    try {
      const connected = await apiClient.checkConnection();
      updateTest(0, connected ? 'success' : 'error', 
        connected ? 'Backend is reachable' : 'Backend is not responding');
      
      if (!connected) {
        // Skip remaining tests if backend is not connected
        for (let i = 1; i < tests.length; i++) {
          updateTest(i, 'error', 'Skipped due to connection failure');
        }
        setIsRunning(false);
        return;
      }
    } catch (error) {
      updateTest(0, 'error', `Connection failed: ${error}`);
      setIsRunning(false);
      return;
    }

    // Test 2: Health Check
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/health-check`);
      updateTest(1, response.ok ? 'success' : 'error',
        response.ok ? 'Health check passed' : `Health check failed: ${response.status}`);
    } catch (error) {
      updateTest(1, 'error', `Health check error: ${error}`);
    }

    // Test 3: CORS Configuration
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/health-check`, {
        method: 'OPTIONS',
        headers: {
          'Origin': window.location.origin,
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type,Authorization'
        }
      });
      
      const corsHeaders = {
        origin: response.headers.get('Access-Control-Allow-Origin'),
        methods: response.headers.get('Access-Control-Allow-Methods'),
        headers: response.headers.get('Access-Control-Allow-Headers'),
      };
      
      const corsWorking = corsHeaders.origin && (
        corsHeaders.origin === '*' || 
        corsHeaders.origin.includes(window.location.origin)
      );
      
      updateTest(2, corsWorking ? 'success' : 'error',
        corsWorking ? 'CORS properly configured' : `CORS issue: ${JSON.stringify(corsHeaders)}`);
    } catch (error) {
      updateTest(2, 'error', `CORS test error: ${error}`);
    }

    // Test 4: Authentication Flow (mock test)
    try {
      // Test login endpoint format
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: 'test', password: 'test' })
      });
      
      // We expect 401 for invalid credentials, which means the endpoint is working
      updateTest(3, response.status === 401 ? 'success' : 'error',
        response.status === 401 ? 'Authentication endpoint responding correctly' : 
        `Unexpected response: ${response.status}`);
    } catch (error) {
      updateTest(3, 'error', `Authentication test error: ${error}`);
    }

    setIsRunning(false);
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'pending':
        return <Loader2 className="h-4 w-4 animate-spin text-gray-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getStatusBadge = (status: TestResult['status']) => {
    switch (status) {
      case 'pending':
        return <Badge variant="secondary">Pending</Badge>;
      case 'success':
        return <Badge variant="default" className="bg-green-500">Pass</Badge>;
      case 'error':
        return <Badge variant="destructive">Fail</Badge>;
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wifi className="h-5 w-5" />
          Frontend-Backend Connection Test
        </CardTitle>
        <CardDescription>
          Test the connection and configuration between frontend and backend
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <Button 
          onClick={runTests} 
          disabled={isRunning}
          className="w-full"
        >
          {isRunning ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Running Tests...
            </>
          ) : (
            'Run Connection Tests'
          )}
        </Button>

        <div className="space-y-3">
          {tests.map((test, index) => (
            <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                {getStatusIcon(test.status)}
                <div>
                  <div className="font-medium">{test.name}</div>
                  {test.message && (
                    <div className="text-sm text-gray-500">{test.message}</div>
                  )}
                </div>
              </div>
              {getStatusBadge(test.status)}
            </div>
          ))}
        </div>

        <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm">
          <strong>Expected Configuration:</strong>
          <ul className="mt-2 space-y-1 list-disc list-inside">
            <li>Backend running on <code>localhost:8000</code></li>
            <li>Frontend running on <code>localhost:3000</code></li>
            <li>CORS configured for frontend origin</li>
            <li>Authentication endpoints responding</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Phase 5: Deployment Preparation

#### 5.1 Vercel Configuration

**File: `PersonalAIAgent_frontend/vercel.json`**
```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://your-backend-domain.com",
    "NEXT_PUBLIC_FRONTEND_URL": "https://your-frontend.vercel.app"
  },
  "build": {
    "env": {
      "NEXT_PUBLIC_API_URL": "https://your-backend-domain.com"
    }
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend-domain.com/api/:path*"
    }
  ]
}
```

#### 5.2 Production Environment Configuration

**File: `PersonalAIAgent_frontend/.env.production`**
```env
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
NEXT_PUBLIC_FRONTEND_URL=https://your-frontend.vercel.app
NEXT_PUBLIC_GMAIL_CLIENT_ID=your-production-gmail-client-id
NODE_ENV=production
```

**File: `Personal AI Agent/backend/.env.production`**
```env
# Production Backend Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# CORS for production frontend
ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://*.vercel.app

# Database (use PostgreSQL in production)
DATABASE_URL=postgresql://user:password@localhost:5432/personal_ai_agent

# Security
SECRET_KEY=your-super-secure-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Gmail OAuth (production credentials)
GMAIL_CLIENT_ID=your-production-gmail-client-id
GMAIL_CLIENT_SECRET=your-production-gmail-client-secret

# Frontend URL for OAuth redirects
FRONTEND_URL=https://your-frontend.vercel.app
```

## 🚀 **Implementation Roadmap**

### Week 1: Configuration & Setup
1. **Day 1-2**: Backend environment configuration and CORS setup
2. **Day 3-4**: Frontend environment configuration and API client updates
3. **Day 5-7**: Testing framework implementation and validation

### Week 2: Component Integration
1. **Day 1-3**: Authentication components update
2. **Day 4-5**: Document management integration
3. **Day 6-7**: Gmail integration synchronization

### Week 3: Testing & Optimization
1. **Day 1-3**: Comprehensive testing and bug fixes
2. **Day 4-5**: Performance optimization and error handling
3. **Day 6-7**: Documentation and deployment preparation

### Week 4: Production Deployment
1. **Day 1-2**: Vercel frontend deployment
2. **Day 3-4**: Backend production configuration
3. **Day 5-7**: End-to-end testing and monitoring setup

## 📊 **Success Metrics**

### Technical Metrics
- ✅ 100% API endpoint compatibility
- ✅ < 2 second response times for all operations
- ✅ Zero CORS-related errors
- ✅ 99% uptime for both frontend and backend

### User Experience Metrics
- ✅ Seamless authentication flow
- ✅ Real-time connection status indication
- ✅ Graceful error handling and recovery
- ✅ Consistent UI/UX across all features

### Security Metrics
- ✅ JWT token security validation
- ✅ HTTPS enforcement in production
- ✅ Input validation and sanitization
- ✅ OAuth flow security compliance

## 🔧 **Maintenance & Monitoring**

### Health Checks
- Backend API health monitoring
- Frontend build and deployment status
- Database connection monitoring
- OAuth token refresh tracking

### Logging & Analytics
- API request/response logging
- Error tracking and alerting
- Performance metrics collection
- User interaction analytics

### Update Procedures
- Backend API versioning strategy
- Frontend deployment rollback procedures
- Database migration management
- Security patch deployment process

This comprehensive plan ensures seamless synchronization between the Personal AI Agent backend and frontend, preparing for successful separate deployment while maintaining optimal user experience and system reliability.