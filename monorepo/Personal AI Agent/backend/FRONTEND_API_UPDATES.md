# Frontend API Client Updates

## Gmail Connection Error Handling

### Enhanced Error Messages

The backend now provides more detailed error messages for Gmail connection failures. Update your frontend to handle these specific error cases:

### OAuth Callback Error Handling

```typescript
// Handle OAuth callback errors in your frontend
const handleOAuthCallback = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const error = urlParams.get('error');
  const details = urlParams.get('details');

  if (error) {
    switch (error) {
      case 'oauth_session_expired':
        showError('Gmail OAuth session expired. Please try connecting again.');
        break;
      case 'oauth_session_not_found':
        showError('Gmail OAuth session not found. Please restart the connection process.');
        break;
      case 'oauth_expired':
        showError('Gmail OAuth flow expired. Please try again.');
        break;
      case 'user_not_found':
        showError('User account not found. Please login again.');
        break;
      case 'oauth_failed':
        showError(`Gmail connection failed: ${details || 'Unknown error'}`);
        break;
      default:
        showError('Gmail connection failed. Please try again.');
    }
  }
};
```

### Gmail Sync Error Handling

```typescript
// Enhanced error handling for Gmail sync
const syncGmailEmails = async (accountId: number, maxEmails: number = 100) => {
  try {
    const result = await client.syncGmailEmails(accountId, maxEmails);
    if (result.error) {
      // Handle specific error types
      switch (result.status) {
        case 401:
          showError('Gmail authentication failed. Please reconnect your account.');
          // Redirect to reconnection flow
          break;
        case 403:
          showError('Gmail permission error. Please reconnect with proper permissions.');
          break;
        case 429:
          showError('Gmail API rate limit exceeded. Please try again in a few minutes.');
          break;
        case 503:
          showError('Network error. Please check your connection and try again.');
          break;
        default:
          showError(`Gmail sync failed: ${result.error}`);
      }
    } else {
      showSuccess(`Successfully synced ${result.data.emails_synced} emails`);
    }
  } catch (error) {
    showError('Gmail sync failed: ' + error.message);
  }
};
```

### Connection Status Monitoring

```typescript
// Enhanced connection status checking
const checkGmailConnectionStatus = async () => {
  try {
    const accounts = await client.getGmailAccounts();
    
    if (accounts.error) {
      return { connected: false, error: accounts.error };
    }
    
    const activeAccounts = accounts.data.filter(account => account.is_active);
    
    if (activeAccounts.length === 0) {
      return { connected: false, error: 'No active Gmail accounts' };
    }
    
    // Check individual account status
    const accountStatuses = await Promise.all(
      activeAccounts.map(async (account) => {
        const status = await client.getGmailStatus(account.id);
        return {
          account: account.email_address,
          connected: status.data?.is_connected || false,
          lastSync: status.data?.last_sync_at,
          totalEmails: status.data?.total_emails || 0
        };
      })
    );
    
    return {
      connected: accountStatuses.some(status => status.connected),
      accounts: accountStatuses
    };
    
  } catch (error) {
    return { connected: false, error: error.message };
  }
};
```

### Configuration Validation

```typescript
// Add configuration validation check
const validateBackendConfig = async () => {
  try {
    const health = await client.healthCheck();
    
    if (health.error) {
      if (health.error.includes('Gmail OAuth configuration')) {
        showError('Backend Gmail configuration is invalid. Please check server configuration.');
        return false;
      }
    }
    
    return true;
  } catch (error) {
    showError('Backend connectivity check failed: ' + error.message);
    return false;
  }
};
```

## Updated API Client Methods

### Gmail Account Management

```typescript
// Enhanced Gmail account methods
class PersonalAIClient {
  // ... existing methods

  async getGmailAccounts(): Promise<ApiResponse<GmailAccountResponse[]>> {
    return this.request<GmailAccountResponse[]>('GET', '/gmail/accounts');
  }

  async getGmailStatus(accountId: number): Promise<ApiResponse<GmailStatusResponse>> {
    return this.request<GmailStatusResponse>('GET', `/gmail/status/${accountId}`);
  }

  async syncGmailEmails(accountId: number, maxEmails: number = 100): Promise<ApiResponse<GmailSyncResponse>> {
    return this.request<GmailSyncResponse>('POST', '/gmail/sync', {
      account_id: accountId,
      max_emails: maxEmails
    });
  }

  async disconnectGmail(accountId: number): Promise<ApiResponse<any>> {
    return this.request<any>('DELETE', `/gmail/disconnect/${accountId}`);
  }

  // Helper method to initiate Gmail OAuth flow
  connectGmail(): void {
    const token = this.getToken();
    if (!token) {
      throw new Error('Authentication required. Please login first.');
    }
    
    // Redirect to Gmail auth endpoint with token
    window.location.href = `${this.config.baseUrl}/gmail/auth?token=${token}`;
  }
}
```

### TypeScript Interface Updates

```typescript
// Updated interfaces
interface GmailAccountResponse {
  id: number;
  email_address: string;
  provider: string;
  is_active: boolean;
  sync_enabled: boolean;
  last_sync_at: string | null;
  created_at: string;
}

interface GmailStatusResponse {
  account_id: number;
  email_address: string;
  is_connected: boolean;
  sync_enabled: boolean;
  last_sync_at: string | null;
  total_emails: number;
  unread_emails: number;
  sync_errors: string[];
}

interface GmailSyncResponse {
  success: boolean;
  emails_synced: number;
  emails_processed: number;
  errors: string[];
  sync_duration_ms: number;
}
```

## Required Frontend Changes

### 1. Environment Variables

Update your frontend environment variables:

```bash
# .env.local or .env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Error Display Component

Create a comprehensive error display component:

```typescript
interface ErrorDisplayProps {
  error: string | null;
  onRetry?: () => void;
  onReconnect?: () => void;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onRetry, onReconnect }) => {
  if (!error) return null;

  const isAuthError = error.includes('authentication') || error.includes('unauthorized');
  const isRateLimitError = error.includes('rate limit') || error.includes('quota');
  const isNetworkError = error.includes('network') || error.includes('connection');

  return (
    <div className="error-display">
      <p>{error}</p>
      {isAuthError && onReconnect && (
        <button onClick={onReconnect}>Reconnect Gmail</button>
      )}
      {isRateLimitError && (
        <p>Please wait a few minutes before trying again.</p>
      )}
      {isNetworkError && onRetry && (
        <button onClick={onRetry}>Retry</button>
      )}
    </div>
  );
};
```

### 3. Connection Status Component

```typescript
const GmailConnectionStatus: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      const result = await checkGmailConnectionStatus();
      setStatus(result);
      setLoading(false);
    };

    checkStatus();
  }, []);

  if (loading) return <div>Checking Gmail connection...</div>;

  return (
    <div className="gmail-status">
      {status.connected ? (
        <div className="connected">
          <span>✅ Gmail Connected</span>
          {status.accounts && (
            <div className="account-details">
              {status.accounts.map((account: any) => (
                <div key={account.account}>
                  <span>{account.account}</span>
                  <span>{account.totalEmails} emails</span>
                  <span>Last sync: {account.lastSync || 'Never'}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="disconnected">
          <span>❌ Gmail Not Connected</span>
          {status.error && <p>{status.error}</p>}
          <button onClick={() => client.connectGmail()}>
            Connect Gmail
          </button>
        </div>
      )}
    </div>
  );
};
```

## Testing Your Changes

1. **Configuration Test**: Run the validation script:
   ```bash
   cd backend
   python validate_email_connection.py
   ```

2. **Namespace Fix**: Run the namespace fix script:
   ```bash
   cd backend
   python fix_email_namespaces.py
   ```

3. **Frontend Integration**: Test the OAuth flow end-to-end:
   - Login to your frontend
   - Click "Connect Gmail"
   - Complete OAuth flow
   - Verify connection status display
   - Test email sync functionality

## Important Notes

- The backend now uses a 60-minute OAuth session timeout (increased from 30 minutes)
- Token refresh logic has been simplified to avoid deadlocks
- Error messages are more specific and actionable
- All email vector storage uses consistent namespaces
- Configuration validation runs at startup with detailed error messages

If you encounter any issues, check the backend logs and run the validation script to identify specific problems.