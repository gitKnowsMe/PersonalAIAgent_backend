/**
 * Personal AI Agent Backend API Client
 * 
 * TypeScript client library for seamless frontend integration
 * with the Personal AI Agent backend API.
 */

// Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface DocumentUploadRequest {
  title: string;
  description?: string;
  file: File;
}

export interface DocumentResponse {
  id: number;
  title: string;
  description?: string;
  file_type: string;
  document_type: string;
  file_size: number;
  created_at: string;
  vector_namespace: string;
}

export interface QueryRequest {
  question: string;
  document_id?: number;
}

export interface QueryResponse {
  id: number;
  question: string;
  answer: string;
  document_id?: number;
  created_at: string;
  from_cache: boolean;
  response_time_ms: number;
  sources: Array<{
    type: string;
    id: number;
    label: string;
  }>;
}

export interface GmailAccountResponse {
  id: number;
  email_address: string;
  provider: string;
  is_active: boolean;
  sync_enabled: boolean;
  last_sync_at?: string;
  created_at: string;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
}

// Configuration
export interface ClientConfig {
  baseUrl: string;
  timeout?: number;
  retries?: number;
}

// Main API Client Class
export class PersonalAIClient {
  private baseUrl: string;
  private timeout: number;
  private retries: number;
  private token: string | null = null;

  constructor(config: ClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = config.timeout || 30000;
    this.retries = config.retries || 3;
  }

  // Authentication
  setToken(token: string) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  clearToken() {
    this.token = null;
  }

  // HTTP Client
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}/api/v1${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= this.retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        const response = await fetch(url, {
          ...config,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          return {
            error: errorText || response.statusText,
            status: response.status,
          };
        }

        const data = await response.json();
        return {
          data,
          status: response.status,
        };
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on authentication errors
        if (error instanceof Error && error.message.includes('401')) {
          break;
        }
        
        // Wait before retry (exponential backoff)
        if (attempt < this.retries) {
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
      }
    }

    return {
      error: lastError?.message || 'Network error',
      status: 0,
    };
  }

  // Form data request (for file uploads)
  private async requestFormData<T>(
    endpoint: string,
    formData: FormData
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}/api/v1${endpoint}`;
    const headers: HeadersInit = {};

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        return {
          error: errorText || response.statusText,
          status: response.status,
        };
      }

      const data = await response.json();
      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error: (error as Error).message || 'Network error',
        status: 0,
      };
    }
  }

  // API Methods

  // Authentication
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch(`${this.baseUrl}/api/v1/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      return {
        error: errorText || response.statusText,
        status: response.status,
      };
    }

    const data = await response.json();
    this.setToken(data.access_token);
    
    return {
      data,
      status: response.status,
    };
  }

  async logout(): Promise<void> {
    this.clearToken();
  }

  // Health Check
  async healthCheck(): Promise<ApiResponse<HealthCheckResponse>> {
    return this.request<HealthCheckResponse>('/health-check');
  }

  // Documents
  async uploadDocument(request: DocumentUploadRequest): Promise<ApiResponse<DocumentResponse>> {
    const formData = new FormData();
    formData.append('title', request.title);
    if (request.description) {
      formData.append('description', request.description);
    }
    formData.append('file', request.file);

    return this.requestFormData<DocumentResponse>('/documents', formData);
  }

  async getDocuments(): Promise<ApiResponse<DocumentResponse[]>> {
    return this.request<DocumentResponse[]>('/documents');
  }

  async deleteDocument(documentId: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  // Queries
  async submitQuery(request: QueryRequest): Promise<ApiResponse<QueryResponse>> {
    return this.request<QueryResponse>('/queries/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getQueries(): Promise<ApiResponse<QueryResponse[]>> {
    return this.request<QueryResponse[]>('/queries');
  }

  // Gmail Integration
  async getGmailAccounts(): Promise<ApiResponse<GmailAccountResponse[]>> {
    return this.request<GmailAccountResponse[]>('/gmail/accounts');
  }

  async connectGmail(): Promise<void> {
    // This should redirect to the OAuth flow
    window.location.href = `${this.baseUrl}/api/v1/gmail/auth?token=${this.token}`;
  }

  async syncGmailEmails(accountId: number, maxEmails?: number): Promise<ApiResponse<any>> {
    return this.request<any>('/gmail/sync', {
      method: 'POST',
      body: JSON.stringify({
        account_id: accountId,
        max_emails: maxEmails || 100,
      }),
    });
  }

  async disconnectGmail(accountId: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/gmail/disconnect/${accountId}`, {
      method: 'DELETE',
    });
  }
}

// Utility functions
export const createApiClient = (config: ClientConfig): PersonalAIClient => {
  return new PersonalAIClient(config);
};

// Default client for common usage
export const defaultClient = createApiClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// Export types for frontend use
export type {
  ApiResponse,
  LoginRequest,
  LoginResponse,
  DocumentUploadRequest,
  DocumentResponse,
  QueryRequest,
  QueryResponse,
  GmailAccountResponse,
  HealthCheckResponse,
  ClientConfig,
};