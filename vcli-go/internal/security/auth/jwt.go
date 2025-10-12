// Package auth implements Layer 1: Authentication
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This package provides JWT validation, MFA, and session management.
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
	secret    []byte
	issuer    string
	audience  string
	clockSkew time.Duration
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
	validAudience := false
	for _, aud := range claims.Audience {
		if aud == v.audience {
			validAudience = true
			break
		}
	}
	if !validAudience {
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
