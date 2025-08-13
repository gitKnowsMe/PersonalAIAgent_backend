# Frontend Login Fix Guide

## **Root Cause**
The frontend is sending login requests in JSON format, but the backend expects OAuth2 form data format.

## **Current Frontend Code (WRONG)**
```typescript
// In login-form.tsx or API client
const response = await fetch('/api/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: loginData.username,
    password: loginData.password
  })
});
```

## **Fixed Frontend Code (CORRECT)**
```typescript
// Method 1: Using URLSearchParams (Recommended)
const response = await fetch('/api/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  },
  body: new URLSearchParams({
    username: loginData.username,
    password: loginData.password
  })
});

// Method 2: Using FormData (Alternative)
const formData = new FormData();
formData.append('username', loginData.username);
formData.append('password', loginData.password);

const response = await fetch('/api/login', {
  method: 'POST',
  body: formData  // Don't set Content-Type, let browser set it
});
```

## **API Client Update**
If using an API client (like `backendClient.login()`), update the method:

```typescript
// In lib/api.ts or similar
async login(username: string, password: string) {
  const response = await fetch(`${this.baseURL}/api/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
      username,
      password
    })
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Login failed: ${response.status} ${response.statusText} - ${errorText}`);
  }
  
  const data = await response.json();
  this.setToken(data.access_token);
  return data;
}
```

## **Files to Update**
1. **`components/login-form.tsx`** - Update the login form submission
2. **`lib/api.ts`** or **`lib/backend-client.ts`** - Update the API client login method
3. **Any other authentication-related API calls**

## **Testing**
After making changes:
1. Open browser developer tools
2. Go to Network tab
3. Try to login
4. Check the request:
   - **Content-Type**: Should be `application/x-www-form-urlencoded`
   - **Request Body**: Should show `username=gmail_tester&password=Iomaguire1`
   - **NOT JSON format**

## **Expected Result**
- Login should succeed with valid credentials
- User should be redirected to main application
- JWT token should be stored and used for authenticated requests

## **Test Credentials**
- **Username**: `gmail_tester`
- **Password**: `Iomaguire1`