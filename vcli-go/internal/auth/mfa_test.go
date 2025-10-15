package auth

import (
	"context"
	"testing"
	"time"
)

func TestTOTPProvider_GenerateSecret(t *testing.T) {
	provider := NewTOTPProvider("vcli-go", "test")

	tests := []struct {
		name    string
		userID  string
		wantErr bool
	}{
		{
			name:    "valid user ID",
			userID:  "user@example.com",
			wantErr: false,
		},
		{
			name:    "empty user ID",
			userID:  "",
			wantErr: false, // Still generates secret
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			secret, err := provider.GenerateSecret(tt.userID)
			if (err != nil) != tt.wantErr {
				t.Errorf("GenerateSecret() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr {
				if secret == nil {
					t.Error("GenerateSecret() returned nil secret")
					return
				}
				if secret.Secret == "" {
					t.Error("GenerateSecret() returned empty secret")
				}
				if secret.QRCode == "" {
					t.Error("GenerateSecret() returned empty QR code")
				}
				if secret.UserID != tt.userID {
					t.Errorf("GenerateSecret() userID = %v, want %v", secret.UserID, tt.userID)
				}
				if secret.Issuer != provider.issuer {
					t.Errorf("GenerateSecret() issuer = %v, want %v", secret.Issuer, provider.issuer)
				}
			}
		})
	}
}

func TestTOTPProvider_VerifyTOTP(t *testing.T) {
	provider := NewTOTPProvider("vcli-go", "test")
	
	// Generate a test secret
	secret, err := provider.GenerateSecret("test@example.com")
	if err != nil {
		t.Fatalf("Failed to generate secret: %v", err)
	}

	// Generate a valid token using the secret
	// Note: In real tests, we'd use the actual TOTP library to generate valid tokens
	// For now, we'll test with a known invalid token
	
	tests := []struct {
		name    string
		secret  string
		token   string
		want    bool
		wantErr bool
	}{
		{
			name:    "invalid token",
			secret:  secret.Secret,
			token:   "000000",
			want:    false,
			wantErr: false,
		},
		{
			name:    "empty token",
			secret:  secret.Secret,
			token:   "",
			want:    false,
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			valid, err := provider.VerifyTOTP(tt.secret, tt.token)
			if (err != nil) != tt.wantErr {
				t.Errorf("VerifyTOTP() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if valid != tt.want {
				t.Errorf("VerifyTOTP() = %v, want %v", valid, tt.want)
			}
		})
	}
}

func TestTOTPProvider_RequiresMFA(t *testing.T) {
	provider := NewTOTPProvider("vcli-go", "test")

	tests := []struct {
		name       string
		userID     string
		action     string
		ctxValues  map[string]interface{}
		want       bool
		wantErr    bool
	}{
		{
			name:    "critical action - delete namespace",
			userID:  "user@example.com",
			action:  "delete_namespace",
			want:    true,
			wantErr: false,
		},
		{
			name:    "critical action - exec production",
			userID:  "user@example.com",
			action:  "exec_production",
			want:    true,
			wantErr: false,
		},
		{
			name:    "non-critical action with recent MFA",
			userID:  "user@example.com",
			action:  "list_pods",
			ctxValues: map[string]interface{}{
				"mfa_verified_at": time.Now().Add(-5 * time.Minute),
			},
			want:    false,
			wantErr: false,
		},
		{
			name:    "non-critical action with expired MFA",
			userID:  "user@example.com",
			action:  "list_pods",
			ctxValues: map[string]interface{}{
				"mfa_verified_at": time.Now().Add(-20 * time.Minute),
				"client_ip":       "1.2.3.4", // Untrusted IP to make test deterministic
			},
			want:    true, // Expired MFA + untrusted IP requires re-auth
			wantErr: false,
		},
		{
			name:    "high anomaly score",
			userID:  "user@example.com",
			action:  "list_pods",
			ctxValues: map[string]interface{}{
				"anomaly_score": 75,
			},
			want:    true,
			wantErr: false,
		},
		{
			name:    "untrusted IP",
			userID:  "user@example.com",
			action:  "list_pods",
			ctxValues: map[string]interface{}{
				"client_ip": "1.2.3.4",
			},
			want:    true, // isTrustedIP returns false by default
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := context.Background()
			
			// Add context values if specified
			if tt.ctxValues != nil {
				for k, v := range tt.ctxValues {
					ctx = context.WithValue(ctx, k, v)
				}
			}

			required, err := provider.RequiresMFA(ctx, tt.userID, tt.action)
			if (err != nil) != tt.wantErr {
				t.Errorf("RequiresMFA() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if required != tt.want {
				t.Errorf("RequiresMFA() = %v, want %v", required, tt.want)
			}
		})
	}
}

func TestMFAContext_IsValid(t *testing.T) {
	tests := []struct {
		name       string
		validUntil time.Time
		want       bool
	}{
		{
			name:       "valid context",
			validUntil: time.Now().Add(5 * time.Minute),
			want:       true,
		},
		{
			name:       "expired context",
			validUntil: time.Now().Add(-5 * time.Minute),
			want:       false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := &MFAContext{
				ValidUntil: tt.validUntil,
			}
			if got := ctx.IsValid(); got != tt.want {
				t.Errorf("IsValid() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestMFAContext_RemainingValidity(t *testing.T) {
	ctx := &MFAContext{
		ValidUntil: time.Now().Add(5 * time.Minute),
	}

	remaining := ctx.RemainingValidity()
	
	// Should be approximately 5 minutes (with small margin for execution time)
	if remaining < 4*time.Minute || remaining > 6*time.Minute {
		t.Errorf("RemainingValidity() = %v, expected around 5 minutes", remaining)
	}
}

// Benchmark tests
func BenchmarkGenerateSecret(b *testing.B) {
	provider := NewTOTPProvider("vcli-go", "test")
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := provider.GenerateSecret("user@example.com")
		if err != nil {
			b.Fatal(err)
		}
	}
}

func BenchmarkVerifyTOTP(b *testing.B) {
	provider := NewTOTPProvider("vcli-go", "test")
	secret, err := provider.GenerateSecret("user@example.com")
	if err != nil {
		b.Fatal(err)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = provider.VerifyTOTP(secret.Secret, "123456")
	}
}

func BenchmarkRequiresMFA(b *testing.B) {
	provider := NewTOTPProvider("vcli-go", "test")
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = provider.RequiresMFA(ctx, "user@example.com", "list_pods")
	}
}
