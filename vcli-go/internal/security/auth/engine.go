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
			Name:    "vcli_auth_duration_seconds",
			Help:    "Authentication duration",
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

	// Check if MFA is required and provided
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
