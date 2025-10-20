// Package audit - Layer 7: Audit
//
// Comprehensive audit logging for compliance
package audit

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"
)

// AuditLayer records all security events
type AuditLayer interface {
	// Log records an audit event
	Log(ctx context.Context, event *AuditEvent) error
	
	// Query retrieves audit events (for compliance reports)
	Query(ctx context.Context, filter *AuditFilter) ([]*AuditEvent, error)
}

// AuditEvent represents a security event
type AuditEvent struct {
	ID        string                 `json:"id"`
	Timestamp time.Time              `json:"timestamp"`
	UserID    string                 `json:"user_id"`
	Action    string                 `json:"action"`
	Resource  string                 `json:"resource"`
	Result    string                 `json:"result"` // success, denied, error
	Reason    string                 `json:"reason"`
	Metadata  map[string]interface{} `json:"metadata"`
	IP        string                 `json:"ip,omitempty"`
	SessionID string                 `json:"session_id,omitempty"`
}

// AuditFilter for querying events
type AuditFilter struct {
	UserID    string
	Action    string
	StartTime time.Time
	EndTime   time.Time
	Limit     int
}

type auditLogger struct {
	mu     sync.Mutex
	file   *os.File
	events []*AuditEvent // In-memory buffer for queries
}

// NewAuditLayer creates audit layer
func NewAuditLayer(logPath string) (AuditLayer, error) {
	file, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0600)
	if err != nil {
		return nil, fmt.Errorf("failed to open audit log: %w", err)
	}

	return &auditLogger{
		file:   file,
		events: make([]*AuditEvent, 0),
	}, nil
}

// Log implements AuditLayer
func (a *auditLogger) Log(ctx context.Context, event *AuditEvent) error {
	a.mu.Lock()
	defer a.mu.Unlock()

	// Set timestamp if not set
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now()
	}

	// Generate ID if not set
	if event.ID == "" {
		event.ID = fmt.Sprintf("%d-%s", event.Timestamp.Unix(), event.UserID)
	}

	// Write to file
	eventJSON, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	if _, err := a.file.Write(append(eventJSON, '\n')); err != nil {
		return fmt.Errorf("failed to write event: %w", err)
	}

	// Store in memory buffer (last 1000 events)
	a.events = append(a.events, event)
	if len(a.events) > 1000 {
		a.events = a.events[1:]
	}

	return nil
}

// Query implements AuditLayer
func (a *auditLogger) Query(ctx context.Context, filter *AuditFilter) ([]*AuditEvent, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	results := make([]*AuditEvent, 0)

	for _, event := range a.events {
		// Apply filters
		if filter.UserID != "" && event.UserID != filter.UserID {
			continue
		}

		if filter.Action != "" && event.Action != filter.Action {
			continue
		}

		if !filter.StartTime.IsZero() && event.Timestamp.Before(filter.StartTime) {
			continue
		}

		if !filter.EndTime.IsZero() && event.Timestamp.After(filter.EndTime) {
			continue
		}

		results = append(results, event)

		if filter.Limit > 0 && len(results) >= filter.Limit {
			break
		}
	}

	return results, nil
}

// Close closes audit log file
func (a *auditLogger) Close() error {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.file.Close()
}

