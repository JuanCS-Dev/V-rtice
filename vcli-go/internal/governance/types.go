package governance

import (
	"time"
)

// Decision represents an HITL (Human-in-the-Loop) decision requiring operator review
type Decision struct {
	// Identity
	DecisionID string `json:"decision_id"`

	// Action Information
	ActionType string `json:"action_type"` // e.g., "block_ip", "quarantine_file", "terminate_process"
	Target     string `json:"target"`      // Target of the action (IP, file path, process ID, etc.)

	// Risk Assessment
	RiskLevel   RiskLevel `json:"risk_level"`
	Confidence  float64   `json:"confidence"`   // AI confidence (0.0 - 1.0)
	ThreatScore float64   `json:"threat_score"` // Threat severity score (0.0 - 1.0)
	ThreatType  string    `json:"threat_type"`  // Type of threat detected

	// Decision Status
	Status           DecisionStatus   `json:"status"`
	AutomationLevel  AutomationLevel  `json:"automation_level"`
	RecommendedActio string           `json:"recommended_action"`

	// Context & Reasoning
	Context   map[string]interface{} `json:"context"`   // Additional context metadata
	Reasoning string                 `json:"reasoning"` // AI reasoning for the decision

	// Timing
	CreatedAt   time.Time  `json:"created_at"`
	SLADeadline *time.Time `json:"sla_deadline,omitempty"`
	ResolvedAt  *time.Time `json:"resolved_at,omitempty"`

	// Operator Actions
	OperatorID       string  `json:"operator_id,omitempty"`
	OperatorDecision string  `json:"operator_decision,omitempty"` // "approve", "reject", "escalate"
	OperatorNotes    string  `json:"operator_notes,omitempty"`
	OperatorOverride *bool   `json:"operator_override,omitempty"` // Did operator override AI recommendation?
}

// RiskLevel represents the risk severity of a decision
type RiskLevel string

const (
	RiskLevelLow      RiskLevel = "LOW"
	RiskLevelMedium   RiskLevel = "MEDIUM"
	RiskLevelHigh     RiskLevel = "HIGH"
	RiskLevelCritical RiskLevel = "CRITICAL"
)

// DecisionStatus represents the current status of a decision
type DecisionStatus string

const (
	DecisionStatusPending   DecisionStatus = "PENDING"
	DecisionStatusApproved  DecisionStatus = "APPROVED"
	DecisionStatusRejected  DecisionStatus = "REJECTED"
	DecisionStatusEscalated DecisionStatus = "ESCALATED"
	DecisionStatusExpired   DecisionStatus = "EXPIRED"
	DecisionStatusExecuted  DecisionStatus = "EXECUTED"
)

// AutomationLevel represents how automated the decision execution is
type AutomationLevel string

const (
	AutomationLevelManual     AutomationLevel = "MANUAL"     // Full human review required
	AutomationLevelAdvisory   AutomationLevel = "ADVISORY"   // AI suggests, human decides
	AutomationLevelSupervised AutomationLevel = "SUPERVISED" // AI acts with human oversight
	AutomationLevelAutomated  AutomationLevel = "AUTOMATED"  // Full automation (no review)
)

// SSEEvent represents a Server-Sent Event for decision streaming
type SSEEvent struct {
	// Event metadata
	EventType string    `json:"event_type"` // "decision_pending", "decision_resolved", "heartbeat"
	EventID   string    `json:"event_id"`   // Unique event ID
	Timestamp time.Time `json:"timestamp"`  // Event timestamp

	// Event data
	Data map[string]interface{} `json:"data"`
}

// SSEMessage represents the complete SSE wire format
type SSEMessage struct {
	ID    string
	Event string
	Data  string
	Retry int // milliseconds
}

// DecisionAction represents an operator action on a decision
type DecisionAction struct {
	DecisionID string                 `json:"decision_id"`
	Action     string                 `json:"action"` // "approve", "reject", "escalate"
	OperatorID string                 `json:"operator_id"`
	Notes      string                 `json:"notes,omitempty"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
	Timestamp  time.Time              `json:"timestamp"`
}

// DecisionMetrics represents operational metrics for the decision queue
type DecisionMetrics struct {
	// Queue metrics
	TotalPending   int `json:"total_pending"`
	TotalApproved  int `json:"total_approved"`
	TotalRejected  int `json:"total_rejected"`
	TotalEscalated int `json:"total_escalated"`
	TotalExpired   int `json:"total_expired"`

	// Risk distribution
	PendingLow      int `json:"pending_low"`
	PendingMedium   int `json:"pending_medium"`
	PendingHigh     int `json:"pending_high"`
	PendingCritical int `json:"pending_critical"`

	// SLA metrics
	NearingSLA      int     `json:"nearing_sla"`       // Decisions near SLA deadline
	BreachedSLA     int     `json:"breached_sla"`      // Decisions past SLA
	AvgResponseTime float64 `json:"avg_response_time"` // Average time to decision (seconds)

	// Throughput
	DecisionsPerMinute float64 `json:"decisions_per_minute"`
	OperatorsActive    int     `json:"operators_active"`

	// Last update
	Timestamp time.Time `json:"timestamp"`
}

// DecisionFilter represents filtering options for decision queries
type DecisionFilter struct {
	Status        []DecisionStatus  `json:"status,omitempty"`
	RiskLevel     []RiskLevel       `json:"risk_level,omitempty"`
	ActionType    []string          `json:"action_type,omitempty"`
	OperatorID    string            `json:"operator_id,omitempty"`
	CreatedAfter  *time.Time        `json:"created_after,omitempty"`
	CreatedBefore *time.Time        `json:"created_before,omitempty"`
	Limit         int               `json:"limit,omitempty"`
	Offset        int               `json:"offset,omitempty"`
}

// ConnectionStatus represents the status of SSE connection to backend
type ConnectionStatus struct {
	Connected     bool      `json:"connected"`
	ServerURL     string    `json:"server_url"`
	LastHeartbeat time.Time `json:"last_heartbeat"`
	LastError     string    `json:"last_error,omitempty"`
	Reconnecting  bool      `json:"reconnecting"`
	EventsReceived int      `json:"events_received"`
	BytesReceived  int64    `json:"bytes_received"`
}

// Session represents an active operator session
type Session struct {
	SessionID    string    `json:"session_id"`
	OperatorID   string    `json:"operator_id"`
	OperatorName string    `json:"operator_name"`
	OperatorRole string    `json:"operator_role"`
	CreatedAt    time.Time `json:"created_at"`
	ExpiresAt    time.Time `json:"expires_at"`
	Active       bool      `json:"active"`
}

// SessionCreateRequest represents a session creation request
type SessionCreateRequest struct {
	OperatorID   string `json:"operator_id"`
	OperatorName string `json:"operator_name"`
	OperatorRole string `json:"operator_role"` // "soc_operator", "senior_analyst", etc.
}

// SessionStats represents session statistics
type SessionStats struct {
	TotalDecisions    int     `json:"total_decisions"`
	Approved          int     `json:"approved"`
	Rejected          int     `json:"rejected"`
	Escalated         int     `json:"escalated"`
	AvgResponseTime   float64 `json:"avg_response_time"`
	SessionDuration   float64 `json:"session_duration"`
	DecisionsPerHour  float64 `json:"decisions_per_hour"`
}
