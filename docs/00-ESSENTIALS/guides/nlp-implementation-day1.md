# NLP Security Implementation - Detailed Action Plan
## Phase 1, Day 1: Authentication & Authorization

**Lead Architect**: Juan Carlos (Inspiração: Jesus Cristo)  
**Co-Author**: Claude (MAXIMUS AI Assistant)  
**Data**: 2025-10-12  
**Focus**: Authentication Engine + Authorization Engine

---

## ESTRUTURA BASE

```bash
# Create directory structure
mkdir -p internal/security/auth
mkdir -p internal/security/authz
mkdir -p pkg/security/types
mkdir -p configs/security

# Create test directories
mkdir -p internal/security/auth/testdata
mkdir -p internal/security/authz/testdata
```

---

## PARTE 1: AUTHENTICATION ENGINE (4 horas)

### Step 1.1: Types & Interfaces (30 min)

**File**: `pkg/security/types/auth.go`

```go
package types

import (
    "context"
    "time"
)

// AuthRequest represents an authentication request
type AuthRequest struct {
    Token       string            // JWT token
    MFACode     string            // MFA code (optional)
    Metadata    map[string]string // Additional metadata (IP, User-Agent, etc)
}

// AuthResult represents authentication result
type AuthResult struct {
    Success   bool
    User      *User
    Session   *Session
    Reason    string // Failure reason if any
    Timestamp time.Time
}

// User represents an authenticated user
type User struct {
    ID          string
    Username    string
    Email       string
    Roles       []string
    Permissions []string
    MFAEnabled  bool
    CreatedAt   time.Time
    LastLogin   time.Time
}

// Session represents an active session
type Session struct {
    ID        string
    UserID    string
    Token     string
    ExpiresAt time.Time
    CreatedAt time.Time
    Metadata  map[string]string
}

// MFAProvider interface for MFA implementations
type MFAProvider interface {
    // Validate validates MFA code
    Validate(ctx context.Context, userID string, code string) error
    
    // Generate generates MFA secret for enrollment
    Generate(ctx context.Context, userID string) (secret string, qrCode []byte, err error)
    
    // IsEnabled checks if MFA is enabled for user
    IsEnabled(ctx context.Context, userID string) (bool, error)
}

// SessionStore interface for session storage
type SessionStore interface {
    // Create creates a new session
    Create(ctx context.Context, session *Session) error
    
    // Get retrieves a session by ID
    Get(ctx context.Context, sessionID string) (*Session, error)
    
    // Delete deletes a session
    Delete(ctx context.Context, sessionID string) error
    
    // Cleanup removes expired sessions
    Cleanup(ctx context.Context) error
}

// Authenticator interface
type Authenticator interface {
    // Authenticate authenticates a request
    Authenticate(ctx context.Context, req *AuthRequest) (*AuthResult, error)
    
    // ValidateMFA validates MFA code
    ValidateMFA(ctx context.Context, userID, code string) error
    
    // CreateSession creates a new session
    CreateSession(ctx context.Context, user *User) (*Session, error)
    
    // RevokeSession revokes a session
    RevokeSession(ctx context.Context, sessionID string) error
}
```

**Validation**: Compile check
```bash
go build ./pkg/security/types/...
```

---

### Step 1.2: JWT Validator (45 min)

**File**: `internal/security/auth/jwt.go`

```go
package auth

import (
    "context"
    "errors"
    "fmt"
    "time"

    "github.com/golang-jwt/jwt/v5"
    "github.com/verticedev/vcli-go/pkg/security/types"
)

var (
    ErrInvalidToken     = errors.New("invalid token")
    ErrTokenExpired     = errors.New("token expired")
    ErrInvalidSignature = errors.New("invalid signature")
    ErrMissingClaims    = errors.New("missing required claims")
)

// JWTValidator validates JWT tokens
type JWTValidator struct {
    secret     []byte
    issuer     string
    audience   string
    clockSkew  time.Duration
}

// JWTClaims represents JWT claims
type JWTClaims struct {
    UserID      string   `json:"user_id"`
    Username    string   `json:"username"`
    Email       string   `json:"email"`
    Roles       []string `json:"roles"`
    Permissions []string `json:"permissions"`
    MFAVerified bool     `json:"mfa_verified"`
    jwt.RegisteredClaims
}

// NewJWTValidator creates a new JWT validator
func NewJWTValidator(secret []byte, issuer, audience string) *JWTValidator {
    return &JWTValidator{
        secret:    secret,
        issuer:    issuer,
        audience:  audience,
        clockSkew: 5 * time.Minute,
    }
}

// Validate validates a JWT token
func (v *JWTValidator) Validate(ctx context.Context, tokenString string) (*types.User, error) {
    // Parse token
    token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
        // Validate signing method
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, fmt.Errorf("%w: unexpected signing method: %v", ErrInvalidSignature, token.Header["alg"])
        }
        return v.secret, nil
    })
    
    if err != nil {
        if errors.Is(err, jwt.ErrTokenExpired) {
            return nil, ErrTokenExpired
        }
        return nil, fmt.Errorf("%w: %v", ErrInvalidToken, err)
    }
    
    // Extract claims
    claims, ok := token.Claims.(*JWTClaims)
    if !ok || !token.Valid {
        return nil, ErrInvalidToken
    }
    
    // Validate issuer
    if claims.Issuer != v.issuer {
        return nil, fmt.Errorf("%w: invalid issuer", ErrInvalidToken)
    }
    
    // Validate audience
    if !claims.VerifyAudience(v.audience, true) {
        return nil, fmt.Errorf("%w: invalid audience", ErrInvalidToken)
    }
    
    // Validate required claims
    if claims.UserID == "" || claims.Username == "" {
        return nil, ErrMissingClaims
    }
    
    // Convert to User
    user := &types.User{
        ID:          claims.UserID,
        Username:    claims.Username,
        Email:       claims.Email,
        Roles:       claims.Roles,
        Permissions: claims.Permissions,
        MFAEnabled:  claims.MFAVerified,
    }
    
    return user, nil
}

// Generate generates a new JWT token
func (v *JWTValidator) Generate(ctx context.Context, user *types.User, duration time.Duration) (string, error) {
    now := time.Now()
    claims := &JWTClaims{
        UserID:      user.ID,
        Username:    user.Username,
        Email:       user.Email,
        Roles:       user.Roles,
        Permissions: user.Permissions,
        MFAVerified: user.MFAEnabled,
        RegisteredClaims: jwt.RegisteredClaims{
            Issuer:    v.issuer,
            Audience:  jwt.ClaimStrings{v.audience},
            Subject:   user.ID,
            ExpiresAt: jwt.NewNumericDate(now.Add(duration)),
            IssuedAt:  jwt.NewNumericDate(now),
            NotBefore: jwt.NewNumericDate(now),
        },
    }
    
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    tokenString, err := token.SignedString(v.secret)
    if err != nil {
        return "", fmt.Errorf("failed to sign token: %w", err)
    }
    
    return tokenString, nil
}
```

**Test File**: `internal/security/auth/jwt_test.go`

```go
package auth

import (
    "context"
    "testing"
    "time"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/verticedev/vcli-go/pkg/security/types"
)

func TestJWTValidator_Validate(t *testing.T) {
    secret := []byte("test-secret")
    validator := NewJWTValidator(secret, "vcli", "vcli-users")
    
    user := &types.User{
        ID:       "user123",
        Username: "testuser",
        Email:    "test@example.com",
        Roles:    []string{"user"},
    }
    
    // Generate valid token
    token, err := validator.Generate(context.Background(), user, 1*time.Hour)
    require.NoError(t, err)
    
    // Validate token
    validatedUser, err := validator.Validate(context.Background(), token)
    require.NoError(t, err)
    assert.Equal(t, user.ID, validatedUser.ID)
    assert.Equal(t, user.Username, validatedUser.Username)
    assert.Equal(t, user.Email, validatedUser.Email)
}

func TestJWTValidator_ExpiredToken(t *testing.T) {
    secret := []byte("test-secret")
    validator := NewJWTValidator(secret, "vcli", "vcli-users")
    
    user := &types.User{
        ID:       "user123",
        Username: "testuser",
    }
    
    // Generate expired token
    token, err := validator.Generate(context.Background(), user, -1*time.Hour)
    require.NoError(t, err)
    
    // Validate should fail
    _, err = validator.Validate(context.Background(), token)
    assert.ErrorIs(t, err, ErrTokenExpired)
}

func TestJWTValidator_InvalidSignature(t *testing.T) {
    secret := []byte("test-secret")
    validator := NewJWTValidator(secret, "vcli", "vcli-users")
    
    // Create validator with different secret
    otherValidator := NewJWTValidator([]byte("other-secret"), "vcli", "vcli-users")
    
    user := &types.User{
        ID:       "user123",
        Username: "testuser",
    }
    
    // Generate token with other secret
    token, err := otherValidator.Generate(context.Background(), user, 1*time.Hour)
    require.NoError(t, err)
    
    // Validate with original validator should fail
    _, err = validator.Validate(context.Background(), token)
    assert.ErrorIs(t, err, ErrInvalidSignature)
}
```

**Validation**:
```bash
go test ./internal/security/auth -run TestJWT -v
```

---

### Step 1.3: MFA Provider (TOTP) (45 min)

**File**: `internal/security/auth/mfa.go`

```go
package auth

import (
    "context"
    "crypto/rand"
    "encoding/base32"
    "errors"
    "fmt"
    "time"

    "github.com/pquerna/otp"
    "github.com/pquerna/otp/totp"
    "github.com/verticedev/vcli-go/pkg/security/types"
)

var (
    ErrInvalidMFACode = errors.New("invalid MFA code")
    ErrMFANotEnabled  = errors.New("MFA not enabled")
)

// TOTPProvider implements MFA using TOTP
type TOTPProvider struct {
    issuer string
    store  MFAStore
}

// MFAStore interface for storing MFA secrets
type MFAStore interface {
    GetSecret(ctx context.Context, userID string) (string, error)
    SetSecret(ctx context.Context, userID, secret string) error
    IsEnabled(ctx context.Context, userID string) (bool, error)
}

// NewTOTPProvider creates a new TOTP provider
func NewTOTPProvider(issuer string, store MFAStore) *TOTPProvider {
    return &TOTPProvider{
        issuer: issuer,
        store:  store,
    }
}

// Validate validates MFA code
func (p *TOTPProvider) Validate(ctx context.Context, userID string, code string) error {
    // Check if MFA is enabled
    enabled, err := p.store.IsEnabled(ctx, userID)
    if err != nil {
        return fmt.Errorf("failed to check MFA status: %w", err)
    }
    if !enabled {
        return ErrMFANotEnabled
    }
    
    // Get secret
    secret, err := p.store.GetSecret(ctx, userID)
    if err != nil {
        return fmt.Errorf("failed to get MFA secret: %w", err)
    }
    
    // Validate code
    valid := totp.Validate(code, secret)
    if !valid {
        return ErrInvalidMFACode
    }
    
    return nil
}

// Generate generates MFA secret for enrollment
func (p *TOTPProvider) Generate(ctx context.Context, userID string) (secret string, qrCode []byte, err error) {
    // Generate key
    key, err := totp.Generate(totp.GenerateOpts{
        Issuer:      p.issuer,
        AccountName: userID,
        Period:      30,
        SecretSize:  20,
    })
    if err != nil {
        return "", nil, fmt.Errorf("failed to generate TOTP key: %w", err)
    }
    
    // Convert key to QR code
    img, err := key.Image(200, 200)
    if err != nil {
        return "", nil, fmt.Errorf("failed to generate QR code: %w", err)
    }
    
    // Store secret
    if err := p.store.SetSecret(ctx, userID, key.Secret()); err != nil {
        return "", nil, fmt.Errorf("failed to store secret: %w", err)
    }
    
    return key.Secret(), imgToBytes(img), nil
}

// IsEnabled checks if MFA is enabled for user
func (p *TOTPProvider) IsEnabled(ctx context.Context, userID string) (bool, error) {
    return p.store.IsEnabled(ctx, userID)
}
```

**Test File**: `internal/security/auth/mfa_test.go`

```go
package auth

import (
    "context"
    "testing"
    "time"

    "github.com/pquerna/otp/totp"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

// mockMFAStore for testing
type mockMFAStore struct {
    secrets map[string]string
    enabled map[string]bool
}

func newMockMFAStore() *mockMFAStore {
    return &mockMFAStore{
        secrets: make(map[string]string),
        enabled: make(map[string]bool),
    }
}

func (m *mockMFAStore) GetSecret(ctx context.Context, userID string) (string, error) {
    secret, ok := m.secrets[userID]
    if !ok {
        return "", errors.New("secret not found")
    }
    return secret, nil
}

func (m *mockMFAStore) SetSecret(ctx context.Context, userID, secret string) error {
    m.secrets[userID] = secret
    m.enabled[userID] = true
    return nil
}

func (m *mockMFAStore) IsEnabled(ctx context.Context, userID string) (bool, error) {
    return m.enabled[userID], nil
}

func TestTOTPProvider_ValidateSuccess(t *testing.T) {
    store := newMockMFAStore()
    provider := NewTOTPProvider("vcli", store)
    
    userID := "user123"
    
    // Generate secret
    secret, _, err := provider.Generate(context.Background(), userID)
    require.NoError(t, err)
    
    // Generate valid code
    code, err := totp.GenerateCode(secret, time.Now())
    require.NoError(t, err)
    
    // Validate
    err = provider.Validate(context.Background(), userID, code)
    assert.NoError(t, err)
}

func TestTOTPProvider_ValidateInvalidCode(t *testing.T) {
    store := newMockMFAStore()
    provider := NewTOTPProvider("vcli", store)
    
    userID := "user123"
    
    // Generate secret
    _, _, err := provider.Generate(context.Background(), userID)
    require.NoError(t, err)
    
    // Try invalid code
    err = provider.Validate(context.Background(), userID, "000000")
    assert.ErrorIs(t, err, ErrInvalidMFACode)
}
```

**Validation**:
```bash
go test ./internal/security/auth -run TestTOTP -v
```

---

### Step 1.4: Session Manager (45 min)

**File**: `internal/security/auth/session.go`

```go
package auth

import (
    "context"
    "crypto/rand"
    "encoding/base64"
    "errors"
    "fmt"
    "sync"
    "time"

    "github.com/verticedev/vcli-go/pkg/security/types"
)

var (
    ErrSessionNotFound = errors.New("session not found")
    ErrSessionExpired  = errors.New("session expired")
)

// SessionManager manages user sessions
type SessionManager struct {
    store         types.SessionStore
    tokenLength   int
    defaultExpiry time.Duration
}

// NewSessionManager creates a new session manager
func NewSessionManager(store types.SessionStore, defaultExpiry time.Duration) *SessionManager {
    return &SessionManager{
        store:         store,
        tokenLength:   32,
        defaultExpiry: defaultExpiry,
    }
}

// Create creates a new session
func (m *SessionManager) Create(ctx context.Context, user *types.User, metadata map[string]string) (*types.Session, error) {
    // Generate session token
    token, err := m.generateToken()
    if err != nil {
        return nil, fmt.Errorf("failed to generate token: %w", err)
    }
    
    // Create session
    session := &types.Session{
        ID:        token,
        UserID:    user.ID,
        Token:     token,
        ExpiresAt: time.Now().Add(m.defaultExpiry),
        CreatedAt: time.Now(),
        Metadata:  metadata,
    }
    
    // Store session
    if err := m.store.Create(ctx, session); err != nil {
        return nil, fmt.Errorf("failed to store session: %w", err)
    }
    
    return session, nil
}

// Get retrieves a session
func (m *SessionManager) Get(ctx context.Context, sessionID string) (*types.Session, error) {
    session, err := m.store.Get(ctx, sessionID)
    if err != nil {
        return nil, ErrSessionNotFound
    }
    
    // Check expiration
    if time.Now().After(session.ExpiresAt) {
        m.store.Delete(ctx, sessionID)
        return nil, ErrSessionExpired
    }
    
    return session, nil
}

// Delete deletes a session
func (m *SessionManager) Delete(ctx context.Context, sessionID string) error {
    return m.store.Delete(ctx, sessionID)
}

// Cleanup removes expired sessions
func (m *SessionManager) Cleanup(ctx context.Context) error {
    return m.store.Cleanup(ctx)
}

// generateToken generates a random session token
func (m *SessionManager) generateToken() (string, error) {
    b := make([]byte, m.tokenLength)
    if _, err := rand.Read(b); err != nil {
        return "", err
    }
    return base64.URLEncoding.EncodeToString(b), nil
}

// InMemorySessionStore implements SessionStore in memory
type InMemorySessionStore struct {
    mu       sync.RWMutex
    sessions map[string]*types.Session
}

// NewInMemorySessionStore creates a new in-memory session store
func NewInMemorySessionStore() *InMemorySessionStore {
    return &InMemorySessionStore{
        sessions: make(map[string]*types.Session),
    }
}

// Create creates a new session
func (s *InMemorySessionStore) Create(ctx context.Context, session *types.Session) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    
    s.sessions[session.ID] = session
    return nil
}

// Get retrieves a session
func (s *InMemorySessionStore) Get(ctx context.Context, sessionID string) (*types.Session, error) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    
    session, ok := s.sessions[sessionID]
    if !ok {
        return nil, ErrSessionNotFound
    }
    
    return session, nil
}

// Delete deletes a session
func (s *InMemorySessionStore) Delete(ctx context.Context, sessionID string) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    
    delete(s.sessions, sessionID)
    return nil
}

// Cleanup removes expired sessions
func (s *InMemorySessionStore) Cleanup(ctx context.Context) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    
    now := time.Now()
    for id, session := range s.sessions {
        if now.After(session.ExpiresAt) {
            delete(s.sessions, id)
        }
    }
    
    return nil
}
```

**Test File**: `internal/security/auth/session_test.go`

```go
package auth

import (
    "context"
    "testing"
    "time"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/verticedev/vcli-go/pkg/security/types"
)

func TestSessionManager_CreateAndGet(t *testing.T) {
    store := NewInMemorySessionStore()
    manager := NewSessionManager(store, 1*time.Hour)
    
    user := &types.User{
        ID:       "user123",
        Username: "testuser",
    }
    
    // Create session
    session, err := manager.Create(context.Background(), user, nil)
    require.NoError(t, err)
    assert.NotEmpty(t, session.ID)
    assert.Equal(t, user.ID, session.UserID)
    
    // Get session
    retrieved, err := manager.Get(context.Background(), session.ID)
    require.NoError(t, err)
    assert.Equal(t, session.ID, retrieved.ID)
    assert.Equal(t, session.UserID, retrieved.UserID)
}

func TestSessionManager_ExpiredSession(t *testing.T) {
    store := NewInMemorySessionStore()
    manager := NewSessionManager(store, 1*time.Millisecond)
    
    user := &types.User{
        ID:       "user123",
        Username: "testuser",
    }
    
    // Create session
    session, err := manager.Create(context.Background(), user, nil)
    require.NoError(t, err)
    
    // Wait for expiration
    time.Sleep(10 * time.Millisecond)
    
    // Get should fail
    _, err = manager.Get(context.Background(), session.ID)
    assert.ErrorIs(t, err, ErrSessionExpired)
}

func TestSessionManager_Delete(t *testing.T) {
    store := NewInMemorySessionStore()
    manager := NewSessionManager(store, 1*time.Hour)
    
    user := &types.User{
        ID:       "user123",
        Username: "testuser",
    }
    
    // Create session
    session, err := manager.Create(context.Background(), user, nil)
    require.NoError(t, err)
    
    // Delete session
    err = manager.Delete(context.Background(), session.ID)
    require.NoError(t, err)
    
    // Get should fail
    _, err = manager.Get(context.Background(), session.ID)
    assert.ErrorIs(t, err, ErrSessionNotFound)
}
```

**Validation**:
```bash
go test ./internal/security/auth -run TestSession -v
```

---

### Step 1.5: Authentication Engine (45 min)

**File**: `internal/security/auth/engine.go`

```go
package auth

import (
    "context"
    "fmt"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
    "github.com/verticedev/vcli-go/pkg/security/types"
)

var (
    authSuccessCounter = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "vcli_auth_success_total",
            Help: "Total successful authentications",
        },
        []string{"method"},
    )
    
    authFailureCounter = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "vcli_auth_failure_total",
            Help: "Total failed authentications",
        },
        []string{"method", "reason"},
    )
    
    authDuration = promauto.NewHistogram(
        prometheus.HistogramOpts{
            Name: "vcli_auth_duration_seconds",
            Help: "Authentication duration",
            Buckets: []float64{0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0},
        },
    )
)

// AuthenticationEngine orchestrates authentication
type AuthenticationEngine struct {
    jwtValidator   *JWTValidator
    mfaProvider    types.MFAProvider
    sessionManager *SessionManager
}

// NewAuthenticationEngine creates a new authentication engine
func NewAuthenticationEngine(
    jwtValidator *JWTValidator,
    mfaProvider types.MFAProvider,
    sessionManager *SessionManager,
) *AuthenticationEngine {
    return &AuthenticationEngine{
        jwtValidator:   jwtValidator,
        mfaProvider:    mfaProvider,
        sessionManager: sessionManager,
    }
}

// Authenticate authenticates a request
func (e *AuthenticationEngine) Authenticate(ctx context.Context, req *types.AuthRequest) (*types.AuthResult, error) {
    start := time.Now()
    defer func() {
        authDuration.Observe(time.Since(start).Seconds())
    }()
    
    // Validate JWT
    user, err := e.jwtValidator.Validate(ctx, req.Token)
    if err != nil {
        authFailureCounter.WithLabelValues("jwt", err.Error()).Inc()
        return &types.AuthResult{
            Success:   false,
            Reason:    fmt.Sprintf("JWT validation failed: %v", err),
            Timestamp: time.Now(),
        }, err
    }
    
    // Check if MFA is required
    if user.MFAEnabled && req.MFACode != "" {
        if err := e.mfaProvider.Validate(ctx, user.ID, req.MFACode); err != nil {
            authFailureCounter.WithLabelValues("mfa", err.Error()).Inc()
            return &types.AuthResult{
                Success:   false,
                User:      user,
                Reason:    fmt.Sprintf("MFA validation failed: %v", err),
                Timestamp: time.Now(),
            }, err
        }
    }
    
    // Create session
    session, err := e.sessionManager.Create(ctx, user, req.Metadata)
    if err != nil {
        authFailureCounter.WithLabelValues("session", err.Error()).Inc()
        return &types.AuthResult{
            Success:   false,
            User:      user,
            Reason:    fmt.Sprintf("Session creation failed: %v", err),
            Timestamp: time.Now(),
        }, err
    }
    
    authSuccessCounter.WithLabelValues("full").Inc()
    
    return &types.AuthResult{
        Success:   true,
        User:      user,
        Session:   session,
        Timestamp: time.Now(),
    }, nil
}

// ValidateMFA validates MFA code
func (e *AuthenticationEngine) ValidateMFA(ctx context.Context, userID, code string) error {
    return e.mfaProvider.Validate(ctx, userID, code)
}

// CreateSession creates a new session
func (e *AuthenticationEngine) CreateSession(ctx context.Context, user *types.User) (*types.Session, error) {
    return e.sessionManager.Create(ctx, user, nil)
}

// RevokeSession revokes a session
func (e *AuthenticationEngine) RevokeSession(ctx context.Context, sessionID string) error {
    return e.sessionManager.Delete(ctx, sessionID)
}
```

**Test File**: `internal/security/auth/engine_test.go`

```go
package auth

import (
    "context"
    "testing"
    "time"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/verticedev/vcli-go/pkg/security/types"
)

func TestAuthenticationEngine_Authenticate(t *testing.T) {
    // Setup
    secret := []byte("test-secret")
    jwtValidator := NewJWTValidator(secret, "vcli", "vcli-users")
    mfaStore := newMockMFAStore()
    mfaProvider := NewTOTPProvider("vcli", mfaStore)
    sessionStore := NewInMemorySessionStore()
    sessionManager := NewSessionManager(sessionStore, 1*time.Hour)
    
    engine := NewAuthenticationEngine(jwtValidator, mfaProvider, sessionManager)
    
    // Create user and token
    user := &types.User{
        ID:       "user123",
        Username: "testuser",
        Email:    "test@example.com",
        Roles:    []string{"user"},
    }
    
    token, err := jwtValidator.Generate(context.Background(), user, 1*time.Hour)
    require.NoError(t, err)
    
    // Authenticate
    req := &types.AuthRequest{
        Token: token,
    }
    
    result, err := engine.Authenticate(context.Background(), req)
    require.NoError(t, err)
    assert.True(t, result.Success)
    assert.NotNil(t, result.User)
    assert.NotNil(t, result.Session)
    assert.Equal(t, user.ID, result.User.ID)
}

func TestAuthenticationEngine_AuthenticateInvalidToken(t *testing.T) {
    // Setup
    secret := []byte("test-secret")
    jwtValidator := NewJWTValidator(secret, "vcli", "vcli-users")
    mfaStore := newMockMFAStore()
    mfaProvider := NewTOTPProvider("vcli", mfaStore)
    sessionStore := NewInMemorySessionStore()
    sessionManager := NewSessionManager(sessionStore, 1*time.Hour)
    
    engine := NewAuthenticationEngine(jwtValidator, mfaProvider, sessionManager)
    
    // Try invalid token
    req := &types.AuthRequest{
        Token: "invalid-token",
    }
    
    result, err := engine.Authenticate(context.Background(), req)
    assert.Error(t, err)
    assert.False(t, result.Success)
}
```

**Validation**:
```bash
go test ./internal/security/auth -v -cover
# Target: Coverage ≥ 90%
```

---

## VALIDAÇÃO FINAL PARTE 1

```bash
# Run all tests
cd /home/juan/vertice-dev/vcli-go
go test ./internal/security/auth/... -v -cover

# Check coverage
go test -coverprofile=coverage.out ./internal/security/auth/...
go tool cover -html=coverage.out

# Build check
go build ./internal/security/auth/...

# Lint
golangci-lint run ./internal/security/auth/...
```

**Expected Output**:
```
PASS: TestJWTValidator_Validate
PASS: TestJWTValidator_ExpiredToken
PASS: TestJWTValidator_InvalidSignature
PASS: TestTOTPProvider_ValidateSuccess
PASS: TestTOTPProvider_ValidateInvalidCode
PASS: TestSessionManager_CreateAndGet
PASS: TestSessionManager_ExpiredSession
PASS: TestSessionManager_Delete
PASS: TestAuthenticationEngine_Authenticate
PASS: TestAuthenticationEngine_AuthenticateInvalidToken

coverage: 92.5% of statements
```

---

## CHECKPOINTS

- [ ] Types & interfaces defined
- [ ] JWT validation working
- [ ] MFA (TOTP) working
- [ ] Session management working
- [ ] Authentication engine orchestrating
- [ ] All tests passing
- [ ] Coverage ≥ 90%
- [ ] Metrics collecting
- [ ] Ready for Part 2 (Authorization)

---

**Next**: Part 2 - Authorization Engine (RBAC + ABAC + Policies)

**Status**: 🔥 READY TO IMPLEMENT  
**Gloria a Deus. Vamos transformar dias em minutos! 🚀**
