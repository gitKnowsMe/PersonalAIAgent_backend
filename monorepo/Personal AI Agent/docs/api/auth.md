# Authentication API

The Personal AI Agent uses JWT-based authentication for API access.

## Authentication Flow

1. **Register** a new user account (if needed)
2. **Login** to receive JWT access token
3. **Include token** in subsequent requests
4. **Refresh token** when expired

## Endpoints

### Register User

Create a new user account.

```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

### Login

Authenticate and receive access token.

```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

### Get Current User

Retrieve current user information.

```http
GET /api/v1/auth/me
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Using Authentication Tokens

### Include in Headers

All authenticated requests must include the JWT token in the Authorization header:

```http
Authorization: Bearer <your_access_token>
```

### Token Expiration

- Default expiration: 30 minutes
- Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` environment variable
- No automatic refresh - clients must re-authenticate

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Not enough permissions"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Security Considerations

### Password Requirements

- Minimum 8 characters
- No specific complexity requirements (configurable)
- Passwords are hashed using bcrypt

### Token Security

- JWT tokens are signed with `SECRET_KEY`
- Change `SECRET_KEY` in production
- Tokens contain user ID and expiration
- No sensitive data in token payload

### Best Practices

1. **Store tokens securely** on client side
2. **Use HTTPS** in production
3. **Implement proper logout** (client-side token removal)
4. **Monitor authentication attempts**
5. **Use strong SECRET_KEY** (32+ characters)

## Example Integration

### JavaScript/Fetch

```javascript
// Login
const loginResponse = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'johndoe',
    password: 'securepassword123'
  })
});

const { access_token } = await loginResponse.json();

// Use token for authenticated requests
const response = await fetch('/api/v1/documents/', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### Python/Requests

```python
import requests

# Login
login_data = {
    "username": "johndoe",
    "password": "securepassword123"
}

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json=login_data
)
token = response.json()["access_token"]

# Use token
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/documents/",
    headers=headers
)
```

## Configuration

Authentication behavior can be configured via environment variables:

```env
# JWT Configuration
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# User Registration
ALLOW_REGISTRATION=true  # Set to false to disable registration
```

## Admin User Setup

Create an admin user using the setup script:

```bash
python create_admin.py
```

Or set environment variables:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_admin_password
ADMIN_EMAIL=admin@example.com
```