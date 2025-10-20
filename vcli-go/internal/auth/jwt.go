package auth

import (
	"context"
	"crypto/rsa"
	"errors"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var (
	// ErrInvalidToken is returned when token validation fails
	ErrInvalidToken = errors.New("invalid token")
	
	// ErrTokenExpired is returned when token has expired
	ErrTokenExpired = errors.New("token expired")
	
	// ErrTokenNotYetValid is returned when token is used before its nbf claim
	ErrTokenNotYetValid = errors.New("token not yet valid")
)

// TokenClaims represents JWT token claims
type TokenClaims struct {
	UserID       string   `json:"user_id"`
	Email        string   `json:"email"`
	Roles        []string `json:"roles"`
	Permissions  []string `json:"permissions"`
	MFAVerified  bool     `json:"mfa_verified"`
	SessionID    string   `json:"session_id"`
	AnomalyScore int      `json:"anomaly_score,omitempty"`
	jwt.RegisteredClaims
}

// JWTManager handles JWT token generation and validation
type JWTManager struct {
	privateKey       *rsa.PrivateKey
	publicKey        *rsa.PublicKey
	issuer           string
	accessTokenTTL   time.Duration
	refreshTokenTTL  time.Duration
	signingMethod    jwt.SigningMethod
	tokenStore       TokenStore // Token revocation store
}

// NewJWTManager creates a new JWT manager
func NewJWTManager(privateKey *rsa.PrivateKey, publicKey *rsa.PublicKey, issuer string) *JWTManager {
	// Initialize with in-memory store (5 minute cleanup interval)
	// For production, pass RedisTokenStore instead
	store := NewInMemoryTokenStore(5 * time.Minute)
	
	return &JWTManager{
		privateKey:      privateKey,
		publicKey:       publicKey,
		issuer:          issuer,
		accessTokenTTL:  15 * time.Minute,
		refreshTokenTTL: 7 * 24 * time.Hour,
		signingMethod:   jwt.SigningMethodRS256,
		tokenStore:      store,
	}
}

// GenerateAccessToken generates a new access token
func (m *JWTManager) GenerateAccessToken(userID, email string, roles, permissions []string, mfaVerified bool, sessionID string) (string, error) {
	now := time.Now()
	
	claims := &TokenClaims{
		UserID:      userID,
		Email:       email,
		Roles:       roles,
		Permissions: permissions,
		MFAVerified: mfaVerified,
		SessionID:   sessionID,
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    m.issuer,
			Subject:   userID,
			Audience:  jwt.ClaimStrings{"vcli-go"},
			ExpiresAt: jwt.NewNumericDate(now.Add(m.accessTokenTTL)),
			NotBefore: jwt.NewNumericDate(now),
			IssuedAt:  jwt.NewNumericDate(now),
			ID:        generateTokenID(),
		},
	}

	token := jwt.NewWithClaims(m.signingMethod, claims)
	
	signedToken, err := token.SignedString(m.privateKey)
	if err != nil {
		return "", fmt.Errorf("failed to sign token: %w", err)
	}

	return signedToken, nil
}

// GenerateRefreshToken generates a new refresh token
func (m *JWTManager) GenerateRefreshToken(userID, sessionID string) (string, error) {
	now := time.Now()
	
	claims := &jwt.RegisteredClaims{
		Issuer:    m.issuer,
		Subject:   userID,
		Audience:  jwt.ClaimStrings{"vcli-go-refresh"},
		ExpiresAt: jwt.NewNumericDate(now.Add(m.refreshTokenTTL)),
		NotBefore: jwt.NewNumericDate(now),
		IssuedAt:  jwt.NewNumericDate(now),
		ID:        generateTokenID(),
	}

	token := jwt.NewWithClaims(m.signingMethod, claims)
	
	signedToken, err := token.SignedString(m.privateKey)
	if err != nil {
		return "", fmt.Errorf("failed to sign refresh token: %w", err)
	}

	return signedToken, nil
}

// ValidateToken validates and parses a JWT token
func (m *JWTManager) ValidateToken(tokenString string) (*TokenClaims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &TokenClaims{}, func(token *jwt.Token) (interface{}, error) {
		// Verify signing method
		if token.Method != m.signingMethod {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Method)
		}
		return m.publicKey, nil
	})

	if err != nil {
		if errors.Is(err, jwt.ErrTokenExpired) {
			return nil, ErrTokenExpired
		}
		if errors.Is(err, jwt.ErrTokenNotValidYet) {
			return nil, ErrTokenNotYetValid
		}
		return nil, fmt.Errorf("%w: %v", ErrInvalidToken, err)
	}

	claims, ok := token.Claims.(*TokenClaims)
	if !ok || !token.Valid {
		return nil, ErrInvalidToken
	}

	// Additional validation
	if err := m.validateClaims(claims); err != nil {
		return nil, err
	}

	return claims, nil
}

// ValidateRefreshToken validates a refresh token
func (m *JWTManager) ValidateRefreshToken(tokenString string) (*jwt.RegisteredClaims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &jwt.RegisteredClaims{}, func(token *jwt.Token) (interface{}, error) {
		if token.Method != m.signingMethod {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Method)
		}
		return m.publicKey, nil
	})

	if err != nil {
		if errors.Is(err, jwt.ErrTokenExpired) {
			return nil, ErrTokenExpired
		}
		if errors.Is(err, jwt.ErrTokenNotValidYet) {
			return nil, ErrTokenNotYetValid
		}
		return nil, fmt.Errorf("%w: %v", ErrInvalidToken, err)
	}

	claims, ok := token.Claims.(*jwt.RegisteredClaims)
	if !ok || !token.Valid {
		return nil, ErrInvalidToken
	}

	// Verify audience is for refresh tokens
	expectedAud := "vcli-go-refresh"
	found := false
	for _, aud := range claims.Audience {
		if aud == expectedAud {
			found = true
			break
		}
	}
	if !found {
		return nil, fmt.Errorf("%w: invalid audience for refresh token", ErrInvalidToken)
	}

	return claims, nil
}

// RefreshAccessToken generates a new access token from a valid refresh token
func (m *JWTManager) RefreshAccessToken(refreshToken string, userID, email string, roles, permissions []string, mfaVerified bool) (string, error) {
	// Validate refresh token
	claims, err := m.ValidateRefreshToken(refreshToken)
	if err != nil {
		return "", fmt.Errorf("invalid refresh token: %w", err)
	}

	// Verify subject matches
	if claims.Subject != userID {
		return "", fmt.Errorf("%w: user ID mismatch", ErrInvalidToken)
	}

	// Generate new access token
	// Extract session ID from refresh token ID (in production, you'd look this up)
	sessionID := claims.ID
	
	return m.GenerateAccessToken(userID, email, roles, permissions, mfaVerified, sessionID)
}

// validateClaims performs additional claim validation
func (m *JWTManager) validateClaims(claims *TokenClaims) error {
	// Verify issuer
	if claims.Issuer != m.issuer {
		return fmt.Errorf("%w: invalid issuer", ErrInvalidToken)
	}

	// Verify audience
	expectedAud := "vcli-go"
	found := false
	for _, aud := range claims.Audience {
		if aud == expectedAud {
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("%w: invalid audience", ErrInvalidToken)
	}

	// Verify required fields
	if claims.UserID == "" {
		return fmt.Errorf("%w: missing user ID", ErrInvalidToken)
	}

	if claims.SessionID == "" {
		return fmt.Errorf("%w: missing session ID", ErrInvalidToken)
	}

	return nil
}

// RevokeToken marks a token as revoked
func (m *JWTManager) RevokeToken(tokenID string) error {
	if tokenID == "" {
		return errors.New("token ID cannot be empty")
	}
	
	// Store revocation with expiry matching token TTL
	// This prevents the revocation list from growing indefinitely
	expiresAt := time.Now().Add(m.accessTokenTTL)
	
	return m.tokenStore.RevokeToken(context.Background(), tokenID, expiresAt)
}

// IsTokenRevoked checks if a token has been revoked
func (m *JWTManager) IsTokenRevoked(tokenID string) (bool, error) {
	if tokenID == "" {
		return false, errors.New("token ID cannot be empty")
	}
	
	return m.tokenStore.IsRevoked(context.Background(), tokenID)
}

// generateTokenID generates a unique token identifier
func generateTokenID() string {
	// Use high-resolution timestamp + random component
	return fmt.Sprintf("%d-%s", time.Now().UnixNano(), generateRandomString(16))
}

// generateRandomString generates a random string of specified length
func generateRandomString(length int) string {
	// Simple implementation - in production, use crypto/rand
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}

// TokenPair represents access and refresh token pair
type TokenPair struct {
	AccessToken  string    `json:"access_token"`
	RefreshToken string    `json:"refresh_token"`
	TokenType    string    `json:"token_type"`
	ExpiresIn    int64     `json:"expires_in"` // seconds
	IssuedAt     time.Time `json:"issued_at"`
}

// GenerateTokenPair generates both access and refresh tokens
func (m *JWTManager) GenerateTokenPair(userID, email string, roles, permissions []string, mfaVerified bool, sessionID string) (*TokenPair, error) {
	accessToken, err := m.GenerateAccessToken(userID, email, roles, permissions, mfaVerified, sessionID)
	if err != nil {
		return nil, fmt.Errorf("failed to generate access token: %w", err)
	}

	refreshToken, err := m.GenerateRefreshToken(userID, sessionID)
	if err != nil {
		return nil, fmt.Errorf("failed to generate refresh token: %w", err)
	}

	return &TokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    "Bearer",
		ExpiresIn:    int64(m.accessTokenTTL.Seconds()),
		IssuedAt:     time.Now(),
	}, nil
}
