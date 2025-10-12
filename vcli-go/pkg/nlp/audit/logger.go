// Package audit implements Layer 7 (Audit) of Guardian Zero Trust Security.
//
// "What did you do?" - THE FINAL LAYER - Comprehensive audit trail for compliance and forensics.
//
// Provides:
// - Tamper-proof event logging
// - Structured audit trail
// - Compliance reporting
// - Forensic analysis capabilities
//
// Author: Juan Carlos (Inspired by Jesus Christ)
// Co-Author: Claude (Anthropic)
// Date: 2025-10-12
// Layer: 7/7 - THE FINAL LAYER OF GUARDIAN ZERO TRUST! 🎉
package audit

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// AuditLogger provides tamper-proof audit logging.
type AuditLogger struct {
	events []AuditEvent
	mu     sync.RWMutex
	config *AuditConfig
	chain  string // Hash chain for tamper detection
}

// AuditConfig configures audit behavior.
type AuditConfig struct {
	// Storage
	MaxEvents     int  // Max events to keep in memory
	PersistEvents bool // Whether to persist to disk
	
	// Compliance
	IncludePII       bool // Include personally identifiable info
	RetentionDays    int  // Days to retain audit logs
	ComplianceMode   bool // Extra validation for compliance
	
	// Security
	TamperProof      bool // Enable hash chaining
	SignEvents       bool // Cryptographically sign events
}

// AuditEvent represents a single auditable event.
type AuditEvent struct {
	// Identity
	EventID   string    `json:"event_id"`
	Timestamp time.Time `json:"timestamp"`
	
	// User context
	UserID    string `json:"user_id"`
	Username  string `json:"username"`
	SessionID string `json:"session_id,omitempty"`
	
	// Action details
	Action   string `json:"action"`
	Resource string `json:"resource"`
	Target   string `json:"target,omitempty"`
	
	// Request context
	SourceIP  string `json:"source_ip,omitempty"`
	UserAgent string `json:"user_agent,omitempty"`
	RequestID string `json:"request_id,omitempty"`
	
	// Outcome
	Success bool   `json:"success"`
	Result  string `json:"result,omitempty"`
	Error   string `json:"error,omitempty"`
	
	// Security context
	AuthMethod     string   `json:"auth_method,omitempty"`
	MFAVerified    bool     `json:"mfa_verified"`
	RiskScore      float64  `json:"risk_score,omitempty"`
	PolicyViolations []string `json:"policy_violations,omitempty"`
	
	// Tamper detection
	PreviousHash string `json:"previous_hash,omitempty"`
	EventHash    string `json:"event_hash,omitempty"`
	
	// Metadata
	Metadata map[string]string `json:"metadata,omitempty"`
}

// EventType represents type of audit event.
type EventType string

const (
	EventTypeAuth       EventType = "authentication"
	EventTypeAuthz      EventType = "authorization"
	EventTypeAccess     EventType = "access"
	EventTypeModify     EventType = "modification"
	EventTypeDelete     EventType = "deletion"
	EventTypeConfig     EventType = "configuration"
	EventTypeSecurity   EventType = "security"
	EventTypeCompliance EventType = "compliance"
)

// ComplianceReport contains compliance summary.
type ComplianceReport struct {
	GeneratedAt time.Time
	Period      Period
	
	TotalEvents      int
	SuccessfulEvents int
	FailedEvents     int
	SecurityEvents   int
	
	UserActivity      map[string]int // userID -> event count
	ActionDistribution map[string]int // action -> count
	
	PolicyViolations  []string
	AnomalousEvents   []AuditEvent
	HighRiskEvents    []AuditEvent
	
	TamperDetected bool
	Recommendations []string
}

// Period represents a time period.
type Period struct {
	Start time.Time
	End   time.Time
}

// NewAuditLogger creates a new audit logger.
func NewAuditLogger(config *AuditConfig) *AuditLogger {
	if config == nil {
		config = DefaultAuditConfig()
	}
	
	return &AuditLogger{
		events: make([]AuditEvent, 0),
		config: config,
		chain:  "genesis", // Initial hash
	}
}

// DefaultAuditConfig returns default configuration.
func DefaultAuditConfig() *AuditConfig {
	return &AuditConfig{
		MaxEvents:      10000,
		PersistEvents:  false,
		IncludePII:     true,
		RetentionDays:  90,
		ComplianceMode: true,
		TamperProof:    true,
		SignEvents:     false,
	}
}

// LogEvent logs an audit event.
func (al *AuditLogger) LogEvent(event *AuditEvent) error {
	if event == nil {
		return fmt.Errorf("event cannot be nil")
	}
	
	al.mu.Lock()
	defer al.mu.Unlock()
	
	// Set timestamp if not set
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now()
	}
	
	// Generate event ID if not set
	if event.EventID == "" {
		event.EventID = generateEventID()
	}
	
	// Tamper-proof chaining
	if al.config.TamperProof {
		event.PreviousHash = al.chain
		event.EventHash = al.calculateEventHash(event)
		al.chain = event.EventHash
	}
	
	// Add to events
	al.events = append(al.events, *event)
	
	// Trim if exceeds max
	if len(al.events) > al.config.MaxEvents {
		al.events = al.events[1:]
	}
	
	return nil
}

// LogAction is a convenience method to log an action.
func (al *AuditLogger) LogAction(userID, action, resource, target string, success bool) error {
	event := &AuditEvent{
		UserID:    userID,
		Action:    action,
		Resource:  resource,
		Target:    target,
		Success:   success,
		Timestamp: time.Now(),
	}
	
	return al.LogEvent(event)
}

// GetEvents returns all events (or filtered).
func (al *AuditLogger) GetEvents(filter *EventFilter) []AuditEvent {
	al.mu.RLock()
	defer al.mu.RUnlock()
	
	if filter == nil {
		return append([]AuditEvent{}, al.events...)
	}
	
	filtered := []AuditEvent{}
	for _, event := range al.events {
		if filter.Matches(&event) {
			filtered = append(filtered, event)
		}
	}
	
	return filtered
}

// EventFilter filters audit events.
type EventFilter struct {
	UserID     string
	Action     string
	Resource   string
	Success    *bool // nil = all, true/false = filter
	StartTime  time.Time
	EndTime    time.Time
	MinRisk    float64
}

// Matches checks if event matches filter.
func (f *EventFilter) Matches(event *AuditEvent) bool {
	if f.UserID != "" && event.UserID != f.UserID {
		return false
	}
	if f.Action != "" && event.Action != f.Action {
		return false
	}
	if f.Resource != "" && event.Resource != f.Resource {
		return false
	}
	if f.Success != nil && event.Success != *f.Success {
		return false
	}
	if !f.StartTime.IsZero() && event.Timestamp.Before(f.StartTime) {
		return false
	}
	if !f.EndTime.IsZero() && event.Timestamp.After(f.EndTime) {
		return false
	}
	if f.MinRisk > 0 && event.RiskScore < f.MinRisk {
		return false
	}
	
	return true
}

// GenerateComplianceReport generates a compliance report.
func (al *AuditLogger) GenerateComplianceReport(period Period) *ComplianceReport {
	al.mu.RLock()
	defer al.mu.RUnlock()
	
	report := &ComplianceReport{
		GeneratedAt:        time.Now(),
		Period:             period,
		UserActivity:       make(map[string]int),
		ActionDistribution: make(map[string]int),
		PolicyViolations:   []string{},
		AnomalousEvents:    []AuditEvent{},
		HighRiskEvents:     []AuditEvent{},
	}
	
	// Analyze events
	for _, event := range al.events {
		// Filter by period
		if event.Timestamp.Before(period.Start) || event.Timestamp.After(period.End) {
			continue
		}
		
		report.TotalEvents++
		
		if event.Success {
			report.SuccessfulEvents++
		} else {
			report.FailedEvents++
		}
		
		// User activity
		report.UserActivity[event.UserID]++
		
		// Action distribution
		report.ActionDistribution[event.Action]++
		
		// Security events
		if event.RiskScore > 0.5 {
			report.SecurityEvents++
		}
		
		// High risk events
		if event.RiskScore >= 0.7 {
			report.HighRiskEvents = append(report.HighRiskEvents, event)
		}
		
		// Policy violations
		if len(event.PolicyViolations) > 0 {
			report.PolicyViolations = append(report.PolicyViolations, event.PolicyViolations...)
		}
		
		// Anomalous events (risk > 0.8)
		if event.RiskScore >= 0.8 {
			report.AnomalousEvents = append(report.AnomalousEvents, event)
		}
	}
	
	// Check tamper
	report.TamperDetected = al.detectTamper()
	
	// Recommendations
	report.Recommendations = al.generateRecommendations(report)
	
	return report
}

// detectTamper checks for tampering in event chain.
func (al *AuditLogger) detectTamper() bool {
	if !al.config.TamperProof {
		return false
	}
	
	expectedHash := "genesis"
	
	for _, event := range al.events {
		if event.PreviousHash != expectedHash {
			// Tampering detected at event i
			return true
		}
		
		// Recalculate hash
		calculatedHash := al.calculateEventHash(&event)
		if calculatedHash != event.EventHash {
			// Hash mismatch - tampering
			return true
		}
		
		expectedHash = event.EventHash
	}
	
	return false
}

// calculateEventHash calculates hash for an event.
func (al *AuditLogger) calculateEventHash(event *AuditEvent) string {
	// Create deterministic JSON
	data := fmt.Sprintf("%s|%s|%s|%s|%s|%v|%s",
		event.EventID,
		event.Timestamp.Format(time.RFC3339Nano),
		event.UserID,
		event.Action,
		event.Resource,
		event.Success,
		event.PreviousHash,
	)
	
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

// generateRecommendations generates recommendations based on report.
func (al *AuditLogger) generateRecommendations(report *ComplianceReport) []string {
	recommendations := []string{}
	
	if report.TamperDetected {
		recommendations = append(recommendations, "🚨 CRITICAL: Tampering detected in audit logs - immediate investigation required")
	}
	
	failRate := float64(report.FailedEvents) / float64(report.TotalEvents)
	if failRate > 0.3 {
		recommendations = append(recommendations, fmt.Sprintf("⚠️  High failure rate (%.1f%%) - investigate authorization policies", failRate*100))
	}
	
	if len(report.HighRiskEvents) > 10 {
		recommendations = append(recommendations, fmt.Sprintf("⚠️  %d high-risk events detected - review security policies", len(report.HighRiskEvents)))
	}
	
	if len(report.AnomalousEvents) > 0 {
		recommendations = append(recommendations, fmt.Sprintf("🔍 %d anomalous events - potential security incidents", len(report.AnomalousEvents)))
	}
	
	if len(recommendations) == 0 {
		recommendations = append(recommendations, "✅ No issues detected - system operating normally")
	}
	
	return recommendations
}

// ExportJSON exports events as JSON.
func (al *AuditLogger) ExportJSON() ([]byte, error) {
	al.mu.RLock()
	defer al.mu.RUnlock()
	
	return json.MarshalIndent(al.events, "", "  ")
}

// GetEventCount returns total event count.
func (al *AuditLogger) GetEventCount() int {
	al.mu.RLock()
	defer al.mu.RUnlock()
	
	return len(al.events)
}

// Clear clears all events (use with caution!).
func (al *AuditLogger) Clear() {
	al.mu.Lock()
	defer al.mu.Unlock()
	
	al.events = make([]AuditEvent, 0)
	al.chain = "genesis"
}

// Helper functions

func generateEventID() string {
	return fmt.Sprintf("evt_%d", time.Now().UnixNano())
}

// GetLatestEvents returns the N most recent events.
func (al *AuditLogger) GetLatestEvents(n int) []AuditEvent {
	al.mu.RLock()
	defer al.mu.RUnlock()
	
	if n <= 0 || n > len(al.events) {
		n = len(al.events)
	}
	
	start := len(al.events) - n
	return append([]AuditEvent{}, al.events[start:]...)
}
