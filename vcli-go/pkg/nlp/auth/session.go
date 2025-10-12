// Package auth provides Layer 1 (Authentication) of the Guardian Zero Trust Security.
package auth

import (
"crypto/rand"
"encoding/base64"
"errors"
"fmt"
"time"

"github.com/golang-jwt/jwt/v5"
)

// SessionManager manages JWT-based user sessions with security features.
// Part of Layer 1: Authentication - tracks authenticated user sessions.
type SessionManager struct {
signingKey     []byte
issuer         string
tokenDuration  time.Duration
refreshEnabled bool
revokedTokens  map[string]time.Time // Simple revocation store (token ID -> revocation time)
}

// SessionClaims represents the JWT claims for a user session.
type SessionClaims struct {
UserID          string   `json:"user_id"`
Username        string   `json:"username"`
Roles           []string `json:"roles"`
Permissions     []string `json:"permissions"`
DeviceID        string   `json:"device_id,omitempty"`
IPAddress       string   `json:"ip_address,omitempty"`
MFACompleted    bool     `json:"mfa_completed"`
jwt.RegisteredClaims
}

// Session represents an active user session.
type Session struct {
Token        string
RefreshToken string
Claims       *SessionClaims
CreatedAt    time.Time
ExpiresAt    time.Time
Renewable    bool
}

// SessionConfig defines session management configuration.
type SessionConfig struct {
TokenDuration   time.Duration
RefreshDuration time.Duration
RefreshEnabled  bool
Issuer          string
SigningKey      []byte
}

// NewSessionManager creates a new session manager with configuration.
func NewSessionManager(config *SessionConfig) (*SessionManager, error) {
if config == nil {
return nil, errors.New("session config cannot be nil")
}

if len(config.SigningKey) < 32 {
return nil, errors.New("signing key must be at least 32 bytes")
}

if config.TokenDuration == 0 {
config.TokenDuration = 15 * time.Minute // Default: 15 minutes
}

if config.RefreshDuration == 0 {
config.RefreshDuration = 7 * 24 * time.Hour // Default: 7 days
}

if config.Issuer == "" {
config.Issuer = "vcli-nlp-guardian"
}

return &SessionManager{
signingKey:     config.SigningKey,
issuer:         config.Issuer,
tokenDuration:  config.TokenDuration,
refreshEnabled: config.RefreshEnabled,
revokedTokens:  make(map[string]time.Time),
}, nil
}

// CreateSession creates a new JWT session for an authenticated user.
func (sm *SessionManager) CreateSession(userID, username string, roles []string, mfaCompleted bool) (*Session, error) {
if userID == "" {
return nil, errors.New("userID cannot be empty")
}

now := time.Now()
expiresAt := now.Add(sm.tokenDuration)

// Generate unique token ID
tokenID, err := generateTokenID()
if err != nil {
return nil, fmt.Errorf("failed to generate token ID: %w", err)
}

claims := &SessionClaims{
UserID:       userID,
Username:     username,
Roles:        roles,
MFACompleted: mfaCompleted,
RegisteredClaims: jwt.RegisteredClaims{
ID:        tokenID,
Issuer:    sm.issuer,
Subject:   userID,
IssuedAt:  jwt.NewNumericDate(now),
ExpiresAt: jwt.NewNumericDate(expiresAt),
NotBefore: jwt.NewNumericDate(now),
},
}

token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
tokenString, err := token.SignedString(sm.signingKey)
if err != nil {
return nil, fmt.Errorf("failed to sign token: %w", err)
}

session := &Session{
Token:     tokenString,
Claims:    claims,
CreatedAt: now,
ExpiresAt: expiresAt,
Renewable: sm.refreshEnabled,
}

// Generate refresh token if enabled
if sm.refreshEnabled {
refreshToken, err := sm.createRefreshToken(userID, username, roles, mfaCompleted)
if err != nil {
return nil, fmt.Errorf("failed to create refresh token: %w", err)
}
session.RefreshToken = refreshToken
}

return session, nil
}

// ValidateSession validates a JWT token and returns the session claims.
func (sm *SessionManager) ValidateSession(tokenString string) (*SessionClaims, error) {
if tokenString == "" {
return nil, errors.New("token cannot be empty")
}

// Parse and validate token
token, err := jwt.ParseWithClaims(tokenString, &SessionClaims{}, func(token *jwt.Token) (interface{}, error) {
// Verify signing method
if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
}
return sm.signingKey, nil
})

if err != nil {
return nil, fmt.Errorf("failed to parse token: %w", err)
}

if !token.Valid {
return nil, errors.New("token is invalid")
}

claims, ok := token.Claims.(*SessionClaims)
if !ok {
return nil, errors.New("invalid token claims")
}

// Check if token is revoked
if sm.isRevoked(claims.ID) {
return nil, errors.New("token has been revoked")
}

return claims, nil
}

// RefreshSession creates a new session using a valid refresh token.
func (sm *SessionManager) RefreshSession(refreshToken string) (*Session, error) {
if !sm.refreshEnabled {
return nil, errors.New("refresh tokens are disabled")
}

if refreshToken == "" {
return nil, errors.New("refresh token cannot be empty")
}

// Parse refresh token (same structure as access token but longer duration)
token, err := jwt.ParseWithClaims(refreshToken, &SessionClaims{}, func(token *jwt.Token) (interface{}, error) {
if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
}
return sm.signingKey, nil
})

if err != nil {
return nil, fmt.Errorf("invalid refresh token: %w", err)
}

if !token.Valid {
return nil, errors.New("refresh token is invalid or expired")
}

claims, ok := token.Claims.(*SessionClaims)
if !ok {
return nil, errors.New("invalid refresh token claims")
}

// Check if revoked
if sm.isRevoked(claims.ID) {
return nil, errors.New("refresh token has been revoked")
}

// Create new session
return sm.CreateSession(claims.UserID, claims.Username, claims.Roles, claims.MFACompleted)
}

// RevokeSession revokes a session by token ID.
func (sm *SessionManager) RevokeSession(tokenID string) error {
if tokenID == "" {
return errors.New("tokenID cannot be empty")
}

sm.revokedTokens[tokenID] = time.Now()
return nil
}

// RevokeSessionByToken revokes a session by parsing the token and extracting its ID.
func (sm *SessionManager) RevokeSessionByToken(tokenString string) error {
claims, err := sm.ValidateSession(tokenString)
if err != nil {
// Even if validation fails, try to extract token ID for revocation
token, parseErr := jwt.Parse(tokenString, nil)
if parseErr == nil && token != nil {
if claims, ok := token.Claims.(jwt.MapClaims); ok {
if jti, ok := claims["jti"].(string); ok {
return sm.RevokeSession(jti)
}
}
}
return fmt.Errorf("failed to extract token ID: %w", err)
}

return sm.RevokeSession(claims.ID)
}

// IsSessionValid checks if a session is valid without returning claims.
func (sm *SessionManager) IsSessionValid(tokenString string) bool {
_, err := sm.ValidateSession(tokenString)
return err == nil
}

// ExtendSession extends a session's expiration time.
func (sm *SessionManager) ExtendSession(tokenString string, duration time.Duration) (*Session, error) {
claims, err := sm.ValidateSession(tokenString)
if err != nil {
return nil, fmt.Errorf("cannot extend invalid session: %w", err)
}

// Create new session with extended duration
now := time.Now()
expiresAt := now.Add(duration)

// Generate new token ID
newTokenID, err := generateTokenID()
if err != nil {
return nil, fmt.Errorf("failed to generate new token ID: %w", err)
}

// Create new claims with extended expiration
newClaims := &SessionClaims{
UserID:       claims.UserID,
Username:     claims.Username,
Roles:        claims.Roles,
Permissions:  claims.Permissions,
DeviceID:     claims.DeviceID,
IPAddress:    claims.IPAddress,
MFACompleted: claims.MFACompleted,
RegisteredClaims: jwt.RegisteredClaims{
ID:        newTokenID,
Issuer:    sm.issuer,
Subject:   claims.UserID,
IssuedAt:  jwt.NewNumericDate(now),
ExpiresAt: jwt.NewNumericDate(expiresAt),
NotBefore: jwt.NewNumericDate(now),
},
}

token := jwt.NewWithClaims(jwt.SigningMethodHS256, newClaims)
newTokenString, err := token.SignedString(sm.signingKey)
if err != nil {
return nil, fmt.Errorf("failed to sign extended token: %w", err)
}

// Revoke old token
sm.RevokeSession(claims.ID)

return &Session{
Token:     newTokenString,
Claims:    newClaims,
CreatedAt: now,
ExpiresAt: expiresAt,
Renewable: sm.refreshEnabled,
}, nil
}

// CleanupRevokedTokens removes expired revoked tokens from memory.
func (sm *SessionManager) CleanupRevokedTokens() int {
cleaned := 0
now := time.Now()
maxAge := 24 * time.Hour // Keep revoked tokens for 24 hours

for tokenID, revokedAt := range sm.revokedTokens {
if now.Sub(revokedAt) > maxAge {
delete(sm.revokedTokens, tokenID)
cleaned++
}
}

return cleaned
}

// GetRevokedTokenCount returns the number of currently revoked tokens.
func (sm *SessionManager) GetRevokedTokenCount() int {
return len(sm.revokedTokens)
}

// isRevoked checks if a token ID is in the revoked list.
func (sm *SessionManager) isRevoked(tokenID string) bool {
_, exists := sm.revokedTokens[tokenID]
return exists
}

// createRefreshToken creates a long-lived refresh token.
func (sm *SessionManager) createRefreshToken(userID, username string, roles []string, mfaCompleted bool) (string, error) {
now := time.Now()
expiresAt := now.Add(7 * 24 * time.Hour) // 7 days default

refreshTokenID, err := generateTokenID()
if err != nil {
return "", fmt.Errorf("failed to generate refresh token ID: %w", err)
}

claims := &SessionClaims{
UserID:       userID,
		Username:     username,
		Roles:        roles,
		MFACompleted: mfaCompleted,
RegisteredClaims: jwt.RegisteredClaims{
ID:        refreshTokenID,
Issuer:    sm.issuer,
Subject:   userID,
IssuedAt:  jwt.NewNumericDate(now),
ExpiresAt: jwt.NewNumericDate(expiresAt),
NotBefore: jwt.NewNumericDate(now),
},
}

token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
tokenString, err := token.SignedString(sm.signingKey)
if err != nil {
return "", fmt.Errorf("failed to sign refresh token: %w", err)
}

return tokenString, nil
}

// generateTokenID generates a cryptographically secure random token ID.
func generateTokenID() (string, error) {
b := make([]byte, 32)
if _, err := rand.Read(b); err != nil {
return "", err
}
return base64.URLEncoding.EncodeToString(b), nil
}

// GenerateSigningKey generates a new cryptographically secure signing key.
func GenerateSigningKey() ([]byte, error) {
key := make([]byte, 64) // 512-bit key
if _, err := rand.Read(key); err != nil {
return nil, fmt.Errorf("failed to generate signing key: %w", err)
}
return key, nil
}
