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
