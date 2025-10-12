package auth

import (
	"context"
	"crypto/rand"
	"encoding/base32"
	"fmt"
	"time"

	"github.com/pquerna/otp"
	"github.com/pquerna/otp/totp"
)

// MFAProvider defines multi-factor authentication interface
type MFAProvider interface {
	// GenerateSecret creates a new MFA secret for a user
	GenerateSecret(userID string) (*MFASecret, error)

	// VerifyTOTP validates a TOTP token
	VerifyTOTP(secret, token string) (bool, error)

	// RequiresMFA determines if MFA is required based on context
	RequiresMFA(ctx context.Context, userID string, action string) (bool, error)
}

// MFASecret represents a generated MFA secret
type MFASecret struct {
	Secret    string    `json:"secret"`
	QRCode    string    `json:"qr_code"`
	UserID    string    `json:"user_id"`
	Issuer    string    `json:"issuer"`
	CreatedAt time.Time `json:"created_at"`
}

// TOTPProvider implements TOTP-based MFA
type TOTPProvider struct {
	issuer       string
	accountName  string
	periodSecs   uint
	digits       otp.Digits
	skew         uint
	secretLength int
}

// NewTOTPProvider creates a new TOTP provider
func NewTOTPProvider(issuer, accountName string) *TOTPProvider {
	return &TOTPProvider{
		issuer:       issuer,
		accountName:  accountName,
		periodSecs:   30,           // Standard TOTP period
		digits:       otp.DigitsSix, // 6-digit codes
		skew:         1,             // Allow 1 period skew for clock drift
		secretLength: 32,            // 256-bit secret
	}
}

// GenerateSecret generates a new TOTP secret for a user
func (p *TOTPProvider) GenerateSecret(userID string) (*MFASecret, error) {
	// Generate random secret
	secret := make([]byte, p.secretLength)
	if _, err := rand.Read(secret); err != nil {
		return nil, fmt.Errorf("failed to generate random secret: %w", err)
	}

	// Encode as base32
	encodedSecret := base32.StdEncoding.EncodeToString(secret)

	// Generate key
	key, err := totp.Generate(totp.GenerateOpts{
		Issuer:      p.issuer,
		AccountName: fmt.Sprintf("%s:%s", p.accountName, userID),
		Period:      p.periodSecs,
		Secret:      []byte(encodedSecret),
		Digits:      p.digits,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to generate TOTP key: %w", err)
	}

	return &MFASecret{
		Secret:    key.Secret(),
		QRCode:    key.URL(),
		UserID:    userID,
		Issuer:    p.issuer,
		CreatedAt: time.Now(),
	}, nil
}

// VerifyTOTP validates a TOTP token against a secret
func (p *TOTPProvider) VerifyTOTP(secret, token string) (bool, error) {
	valid := totp.Validate(token, secret)
	return valid, nil
}

// RequiresMFA determines if MFA is required based on context
// This implements contextual security policies
func (p *TOTPProvider) RequiresMFA(ctx context.Context, userID string, action string) (bool, error) {
	// Always require MFA for critical actions
	criticalActions := map[string]bool{
		"delete_namespace":   true,
		"apply_crd":          true,
		"exec_production":    true,
		"scale_to_zero":      true,
		"update_rbac":        true,
		"create_secret":      true,
		"delete_pvc":         true,
		"modify_network":     true,
	}

	if criticalActions[action] {
		return true, nil
	}

	// Check if user has recent MFA verification (stored in context)
	if mfaTime, ok := ctx.Value("mfa_verified_at").(time.Time); ok {
		// MFA valid for 15 minutes for non-critical actions
		if time.Since(mfaTime) < 15*time.Minute {
			return false, nil
		}
	}

	// Check anomaly score from context (set by behavior analyzer)
	if anomalyScore, ok := ctx.Value("anomaly_score").(int); ok {
		// High anomaly score requires MFA
		if anomalyScore > 60 {
			return true, nil
		}
	}

	// Check if outside trusted network
	if clientIP, ok := ctx.Value("client_ip").(string); ok {
		if !isTrustedIP(clientIP) {
			return true, nil
		}
	}

	// Check time-based policy (off-hours require MFA)
	if isOffHours() {
		return true, nil
	}

	// Default: MFA not required for routine operations
	return false, nil
}

// isTrustedIP checks if IP is in trusted network range
// In production, this would check against configured CIDR ranges
func isTrustedIP(ip string) bool {
	// TODO: Implement proper IP validation against configured ranges
	// For now, consider VPN range as trusted
	return false // Conservative default: require MFA
}

// isOffHours checks if current time is outside business hours
// In production, this would be configurable per timezone
func isOffHours() bool {
	now := time.Now()
	hour := now.Hour()
	
	// Business hours: 6 AM - 10 PM (broad range)
	if hour < 6 || hour >= 22 {
		return true
	}
	
	// Weekend
	weekday := now.Weekday()
	if weekday == time.Saturday || weekday == time.Sunday {
		return true
	}
	
	return false
}

// MFAContext represents MFA authentication context
type MFAContext struct {
	UserID       string
	Token        string
	RequiredBy   string // Action that required MFA
	VerifiedAt   time.Time
	ValidUntil   time.Time
	AnomalyScore int
	ClientIP     string
}

// IsValid checks if MFA context is still valid
func (m *MFAContext) IsValid() bool {
	return time.Now().Before(m.ValidUntil)
}

// RemainingValidity returns time until MFA context expires
func (m *MFAContext) RemainingValidity() time.Duration {
	return time.Until(m.ValidUntil)
}
