package auth

import (
	"crypto/rand"
	"crypto/rsa"
	"testing"
	"time"
)

func generateTestKeys(t *testing.T) (*rsa.PrivateKey, *rsa.PublicKey) {
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatalf("Failed to generate private key: %v", err)
	}
	return privateKey, &privateKey.PublicKey
}

func TestJWTManager_GenerateAccessToken(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	tests := []struct {
		name        string
		userID      string
		email       string
		roles       []string
		permissions []string
		mfaVerified bool
		sessionID   string
		wantErr     bool
	}{
		{
			name:        "valid token generation",
			userID:      "user123",
			email:       "user@example.com",
			roles:       []string{"admin", "operator"},
			permissions: []string{"read", "write", "delete"},
			mfaVerified: true,
			sessionID:   "session123",
			wantErr:     false,
		},
		{
			name:        "minimal token",
			userID:      "user456",
			email:       "user2@example.com",
			roles:       []string{},
			permissions: []string{},
			mfaVerified: false,
			sessionID:   "session456",
			wantErr:     false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			token, err := manager.GenerateAccessToken(
				tt.userID,
				tt.email,
				tt.roles,
				tt.permissions,
				tt.mfaVerified,
				tt.sessionID,
			)

			if (err != nil) != tt.wantErr {
				t.Errorf("GenerateAccessToken() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr && token == "" {
				t.Error("GenerateAccessToken() returned empty token")
			}
		})
	}
}

func TestJWTManager_ValidateToken(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	// Generate a valid token
	validToken, err := manager.GenerateAccessToken(
		"user123",
		"user@example.com",
		[]string{"admin"},
		[]string{"read", "write"},
		true,
		"session123",
	)
	if err != nil {
		t.Fatalf("Failed to generate test token: %v", err)
	}

	tests := []struct {
		name    string
		token   string
		wantErr bool
	}{
		{
			name:    "valid token",
			token:   validToken,
			wantErr: false,
		},
		{
			name:    "empty token",
			token:   "",
			wantErr: true,
		},
		{
			name:    "malformed token",
			token:   "not.a.valid.jwt",
			wantErr: true,
		},
		{
			name:    "invalid signature",
			token:   "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.invalid",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			claims, err := manager.ValidateToken(tt.token)

			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateToken() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				if claims == nil {
					t.Error("ValidateToken() returned nil claims")
					return
				}
				if claims.UserID != "user123" {
					t.Errorf("ValidateToken() userID = %v, want user123", claims.UserID)
				}
				if claims.Email != "user@example.com" {
					t.Errorf("ValidateToken() email = %v, want user@example.com", claims.Email)
				}
				if !claims.MFAVerified {
					t.Error("ValidateToken() MFAVerified = false, want true")
				}
			}
		})
	}
}

func TestJWTManager_GenerateRefreshToken(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	token, err := manager.GenerateRefreshToken("user123", "session123")
	if err != nil {
		t.Errorf("GenerateRefreshToken() error = %v", err)
	}

	if token == "" {
		t.Error("GenerateRefreshToken() returned empty token")
	}
}

func TestJWTManager_ValidateRefreshToken(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	validRefreshToken, err := manager.GenerateRefreshToken("user123", "session123")
	if err != nil {
		t.Fatalf("Failed to generate test refresh token: %v", err)
	}

	tests := []struct {
		name    string
		token   string
		wantErr bool
	}{
		{
			name:    "valid refresh token",
			token:   validRefreshToken,
			wantErr: false,
		},
		{
			name:    "empty token",
			token:   "",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			claims, err := manager.ValidateRefreshToken(tt.token)

			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateRefreshToken() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				if claims == nil {
					t.Error("ValidateRefreshToken() returned nil claims")
					return
				}
				if claims.Subject != "user123" {
					t.Errorf("ValidateRefreshToken() subject = %v, want user123", claims.Subject)
				}
			}
		})
	}
}

func TestJWTManager_RefreshAccessToken(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	// Generate refresh token
	refreshToken, err := manager.GenerateRefreshToken("user123", "session123")
	if err != nil {
		t.Fatalf("Failed to generate refresh token: %v", err)
	}

	tests := []struct {
		name         string
		refreshToken string
		userID       string
		email        string
		roles        []string
		permissions  []string
		mfaVerified  bool
		wantErr      bool
	}{
		{
			name:         "valid refresh",
			refreshToken: refreshToken,
			userID:       "user123",
			email:        "user@example.com",
			roles:        []string{"admin"},
			permissions:  []string{"read", "write"},
			mfaVerified:  true,
			wantErr:      false,
		},
		{
			name:         "user ID mismatch",
			refreshToken: refreshToken,
			userID:       "different_user",
			email:        "user@example.com",
			roles:        []string{"admin"},
			permissions:  []string{"read"},
			mfaVerified:  true,
			wantErr:      true,
		},
		{
			name:         "invalid refresh token",
			refreshToken: "invalid.token",
			userID:       "user123",
			email:        "user@example.com",
			roles:        []string{},
			permissions:  []string{},
			mfaVerified:  false,
			wantErr:      true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			newAccessToken, err := manager.RefreshAccessToken(
				tt.refreshToken,
				tt.userID,
				tt.email,
				tt.roles,
				tt.permissions,
				tt.mfaVerified,
			)

			if (err != nil) != tt.wantErr {
				t.Errorf("RefreshAccessToken() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr && newAccessToken == "" {
				t.Error("RefreshAccessToken() returned empty token")
			}
		})
	}
}

func TestJWTManager_GenerateTokenPair(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	pair, err := manager.GenerateTokenPair(
		"user123",
		"user@example.com",
		[]string{"admin"},
		[]string{"read", "write"},
		true,
		"session123",
	)

	if err != nil {
		t.Errorf("GenerateTokenPair() error = %v", err)
		return
	}

	if pair == nil {
		t.Fatal("GenerateTokenPair() returned nil")
	}

	if pair.AccessToken == "" {
		t.Error("GenerateTokenPair() returned empty access token")
	}

	if pair.RefreshToken == "" {
		t.Error("GenerateTokenPair() returned empty refresh token")
	}

	if pair.TokenType != "Bearer" {
		t.Errorf("GenerateTokenPair() token type = %v, want Bearer", pair.TokenType)
	}

	if pair.ExpiresIn != int64(manager.accessTokenTTL.Seconds()) {
		t.Errorf("GenerateTokenPair() expiresIn = %v, want %v", pair.ExpiresIn, int64(manager.accessTokenTTL.Seconds()))
	}
}

func TestTokenClaims_Validation(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	// Test with wrong issuer
	wrongIssuerManager := NewJWTManager(privateKey, publicKey, "wrong-issuer")
	token, _ := wrongIssuerManager.GenerateAccessToken("user123", "user@example.com", []string{}, []string{}, false, "session123")
	
	_, err := manager.ValidateToken(token)
	if err == nil {
		t.Error("ValidateToken() should fail with wrong issuer")
	}
}

func TestJWTManager_RevokeToken(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	tests := []struct {
		name    string
		tokenID string
		wantErr bool
	}{
		{
			name:    "valid token ID",
			tokenID: "token123",
			wantErr: false,
		},
		{
			name:    "empty token ID",
			tokenID: "",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := manager.RevokeToken(tt.tokenID)
			if (err != nil) != tt.wantErr {
				t.Errorf("RevokeToken() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestJWTManager_IsTokenRevoked(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	// For now, should always return false (not revoked)
	revoked, err := manager.IsTokenRevoked("token123")
	if err != nil {
		t.Errorf("IsTokenRevoked() error = %v", err)
	}

	if revoked {
		t.Error("IsTokenRevoked() should return false (not implemented yet)")
	}
}

// Benchmark tests
func BenchmarkGenerateAccessToken(b *testing.B) {
	privateKey, publicKey := generateTestKeys(&testing.T{})
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := manager.GenerateAccessToken(
			"user123",
			"user@example.com",
			[]string{"admin"},
			[]string{"read", "write"},
			true,
			"session123",
		)
		if err != nil {
			b.Fatal(err)
		}
	}
}

func BenchmarkValidateToken(b *testing.B) {
	privateKey, publicKey := generateTestKeys(&testing.T{})
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")

	token, err := manager.GenerateAccessToken("user123", "user@example.com", []string{"admin"}, []string{"read"}, true, "session123")
	if err != nil {
		b.Fatal(err)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := manager.ValidateToken(token)
		if err != nil {
			b.Fatal(err)
		}
	}
}

func TestTokenExpiry(t *testing.T) {
	privateKey, publicKey := generateTestKeys(t)
	manager := NewJWTManager(privateKey, publicKey, "vcli-go-test")
	
	// Override TTL for testing
	manager.accessTokenTTL = 1 * time.Millisecond

	token, err := manager.GenerateAccessToken("user123", "user@example.com", []string{}, []string{}, false, "session123")
	if err != nil {
		t.Fatalf("Failed to generate token: %v", err)
	}

	// Wait for token to expire
	time.Sleep(10 * time.Millisecond)

	_, err = manager.ValidateToken(token)
	if err != ErrTokenExpired {
		t.Errorf("ValidateToken() error = %v, want %v", err, ErrTokenExpired)
	}
}
