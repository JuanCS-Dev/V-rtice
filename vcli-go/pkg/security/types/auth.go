// Package types defines security-related types and interfaces
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This package contains core security types used across all security layers.
package types

import (
	"context"
	"time"
)

// AuthRequest represents an authentication request
type AuthRequest struct {
	Token    string            // JWT token
	MFACode  string            // MFA code (optional)
	Metadata map[string]string // Additional metadata (IP, User-Agent, etc)
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
