// Package context implements conversational context management
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// The Context Manager maintains session state, command history, and user preferences
// to enable natural conversational interactions with vcli-go.
package context

import (
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/verticedev/vcli-go/pkg/nlp"
)

// Manager handles conversational context for NLP sessions
type Manager struct {
	sessions      map[string]*nlp.Context // Active sessions by ID
	mu            sync.RWMutex            // Thread-safe access
	maxHistory    int                     // Maximum history entries
	sessionExpiry time.Duration           // Session expiry duration
}

// NewManager creates a new context manager
func NewManager() *Manager {
	return &Manager{
		sessions:      make(map[string]*nlp.Context),
		maxHistory:    50,                  // Keep last 50 commands
		sessionExpiry: 24 * time.Hour,      // 24 hour sessions
	}
}

// NewManagerWithOptions creates a manager with custom settings
func NewManagerWithOptions(maxHistory int, sessionExpiry time.Duration) *Manager {
	return &Manager{
		sessions:      make(map[string]*nlp.Context),
		maxHistory:    maxHistory,
		sessionExpiry: sessionExpiry,
	}
}

// CreateSession creates a new conversational session
func (m *Manager) CreateSession() *nlp.Context {
	m.mu.Lock()
	defer m.mu.Unlock()

	sessionID := uuid.New().String()
	now := time.Now()

	ctx := &nlp.Context{
		SessionID:     sessionID,
		History:       make([]nlp.HistoryEntry, 0, m.maxHistory),
		CurrentNS:     "default",
		LastResources: make(map[string][]string),
		Preferences:   make(map[string]string),
		Created:       now,
		Updated:       now,
	}

	m.sessions[sessionID] = ctx
	return ctx
}

// GetSession retrieves a session by ID
func (m *Manager) GetSession(sessionID string) (*nlp.Context, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return nil, fmt.Errorf("session not found: %s", sessionID)
	}

	// Check if session expired
	if time.Since(ctx.Updated) > m.sessionExpiry {
		return nil, fmt.Errorf("session expired: %s", sessionID)
	}

	return ctx, nil
}

// UpdateSession updates an existing session
func (m *Manager) UpdateSession(ctx *nlp.Context) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.sessions[ctx.SessionID]; !exists {
		return fmt.Errorf("session not found: %s", ctx.SessionID)
	}

	ctx.Updated = time.Now()
	m.sessions[ctx.SessionID] = ctx
	return nil
}

// DeleteSession removes a session
func (m *Manager) DeleteSession(sessionID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.sessions[sessionID]; !exists {
		return fmt.Errorf("session not found: %s", sessionID)
	}

	delete(m.sessions, sessionID)
	return nil
}

// AddToHistory adds a command to session history
func (m *Manager) AddToHistory(sessionID string, entry nlp.HistoryEntry) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return fmt.Errorf("session not found: %s", sessionID)
	}

	// Add entry with timestamp
	entry.Timestamp = time.Now()
	ctx.History = append(ctx.History, entry)

	// Trim history if it exceeds max
	if len(ctx.History) > m.maxHistory {
		ctx.History = ctx.History[len(ctx.History)-m.maxHistory:]
	}

	ctx.Updated = time.Now()
	return nil
}

// GetHistory retrieves command history
func (m *Manager) GetHistory(sessionID string, limit int) ([]nlp.HistoryEntry, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return nil, fmt.Errorf("session not found: %s", sessionID)
	}

	history := ctx.History
	if limit > 0 && limit < len(history) {
		history = history[len(history)-limit:]
	}

	return history, nil
}

// SetCurrentNamespace sets the active namespace for the session
func (m *Manager) SetCurrentNamespace(sessionID string, namespace string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return fmt.Errorf("session not found: %s", sessionID)
	}

	ctx.CurrentNS = namespace
	ctx.Updated = time.Now()
	return nil
}

// SetCurrentResource sets the active resource type
func (m *Manager) SetCurrentResource(sessionID string, resource string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return fmt.Errorf("session not found: %s", sessionID)
	}

	ctx.CurrentResource = resource
	ctx.Updated = time.Now()
	return nil
}

// TrackResource tracks recently accessed resources
func (m *Manager) TrackResource(sessionID string, resourceType string, resourceName string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return fmt.Errorf("session not found: %s", sessionID)
	}

	// Initialize resource tracking if needed
	if ctx.LastResources == nil {
		ctx.LastResources = make(map[string][]string)
	}

	// Add resource to tracking (keep last 10)
	resources := ctx.LastResources[resourceType]
	resources = append(resources, resourceName)
	if len(resources) > 10 {
		resources = resources[len(resources)-10:]
	}
	ctx.LastResources[resourceType] = resources

	ctx.Updated = time.Now()
	return nil
}

// GetLastResource retrieves the most recent resource of a type
func (m *Manager) GetLastResource(sessionID string, resourceType string) (string, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return "", fmt.Errorf("session not found: %s", sessionID)
	}

	resources, exists := ctx.LastResources[resourceType]
	if !exists || len(resources) == 0 {
		return "", fmt.Errorf("no recent resources of type: %s", resourceType)
	}

	return resources[len(resources)-1], nil
}

// SetPreference sets a user preference
func (m *Manager) SetPreference(sessionID string, key string, value string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return fmt.Errorf("session not found: %s", sessionID)
	}

	if ctx.Preferences == nil {
		ctx.Preferences = make(map[string]string)
	}

	ctx.Preferences[key] = value
	ctx.Updated = time.Now()
	return nil
}

// GetPreference retrieves a user preference
func (m *Manager) GetPreference(sessionID string, key string) (string, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return "", false
	}

	value, exists := ctx.Preferences[key]
	return value, exists
}

// ResolveReference resolves pronoun references ("it", "that", "same")
func (m *Manager) ResolveReference(sessionID string, reference string) (string, string, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	ctx, exists := m.sessions[sessionID]
	if !exists {
		return "", "", fmt.Errorf("session not found: %s", sessionID)
	}

	// Get last successful command from history
	for i := len(ctx.History) - 1; i >= 0; i-- {
		entry := ctx.History[i]
		if entry.Success && entry.Intent != nil {
			// Return resource type and name from last command
			resourceType := entry.Intent.Target

			// Get the resource name from last tracked resource
			if resources, exists := ctx.LastResources[resourceType]; exists && len(resources) > 0 {
				resourceName := resources[len(resources)-1]
				return resourceType, resourceName, nil
			}

			return resourceType, "", nil
		}
	}

	return "", "", fmt.Errorf("no previous command to reference")
}

// CleanupExpiredSessions removes expired sessions
func (m *Manager) CleanupExpiredSessions() int {
	m.mu.Lock()
	defer m.mu.Unlock()

	removed := 0
	now := time.Now()

	for sessionID, ctx := range m.sessions {
		if now.Sub(ctx.Updated) > m.sessionExpiry {
			delete(m.sessions, sessionID)
			removed++
		}
	}

	return removed
}

// GetActiveSessionCount returns number of active sessions
func (m *Manager) GetActiveSessionCount() int {
	m.mu.RLock()
	defer m.mu.RUnlock()

	return len(m.sessions)
}

// __repr__ for debugging
func (m *Manager) String() string {
	m.mu.RLock()
	defer m.mu.RUnlock()

	return fmt.Sprintf("ContextManager(sessions=%d, maxHistory=%d, expiry=%v)",
		len(m.sessions), m.maxHistory, m.sessionExpiry)
}
