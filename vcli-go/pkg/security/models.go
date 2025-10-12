// Package security provides core security models for the NLP parser
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This package defines the security primitives used across all 7 layers
// of the "Guardian of Intent" (Guardião da Intenção) v2.0 security model.
package security

import (
	"time"
)

// User represents an authenticated user
type User struct {
	ID           string    `json:"id"`
	Username     string    `json:"username"`
	Email        string    `json:"email"`
	Roles        []string  `json:"roles"`
	MFAEnabled   bool      `json:"mfa_enabled"`
	MFAVerified  bool      `json:"mfa_verified"`
	CreatedAt    time.Time `json:"created_at"`
	LastLoginAt  time.Time `json:"last_login_at"`
	
	// Security context
	IP           string    `json:"ip"`
	UserAgent    string    `json:"user_agent"`
	SessionID    string    `json:"session_id"`
}

// Session represents an authenticated session
type Session struct {
	ID           string    `json:"id"`
	UserID       string    `json:"user_id"`
	Token        string    `json:"-"` // JWT token (never serialize)
	RefreshToken string    `json:"-"` // Refresh token (never serialize)
	
	CreatedAt    time.Time `json:"created_at"`
	ExpiresAt    time.Time `json:"expires_at"`
	LastActivity time.Time `json:"last_activity"`
	
	// Context
	IP           string    `json:"ip"`
	UserAgent    string    `json:"user_agent"`
	
	// Security flags
	MFAVerified  bool      `json:"mfa_verified"`
	ElevatedAuth bool      `json:"elevated_auth"` // Temporary elevation for high-risk ops
	
	// Metrics
	CommandCount int       `json:"command_count"`
	LastCommand  string    `json:"last_command"`
}

// SecurityContext contains all security-relevant information for a request
type SecurityContext struct {
	User          *User
	Session       *Session
	Timestamp     time.Time
	
	// Request context
	IP            string
	UserAgent     string
	RequestID     string
	
	// Authorization
	Roles         []string
	Permissions   []string
	
	// Risk assessment
	RiskScore     int    // 0-100
	RiskFactors   []string
	
	// Rate limiting
	RateLimitKey  string
	RateLimitHits int
	
	// Behavior analysis
	Baseline      *UserBaseline
	Anomalies     []Anomaly
}

// UserBaseline represents normal user behavior patterns
type UserBaseline struct {
	UserID        string
	
	// Temporal patterns
	TypicalHours  []int    // Hours when user is typically active (0-23)
	TypicalDays   []int    // Days when user is typically active (0-6, 0=Sunday)
	
	// Command patterns
	TopCommands   []string // Most frequent commands
	CommandRatio  CommandRatio
	
	// Resource patterns
	TopNamespaces []string
	TopResources  []string
	
	// Network patterns
	TypicalIPs    []string
	TypicalGeo    []string // Geographic locations
	
	// Updated
	LastUpdated   time.Time
	SampleSize    int // Number of commands in baseline
}

// CommandRatio represents distribution of command types
type CommandRatio struct {
	Read   float64 // Percentage of read operations
	Write  float64 // Percentage of write operations
	Delete float64 // Percentage of delete operations
}

// Anomaly represents a detected behavioral anomaly
type Anomaly struct {
	Type      AnomalyType
	Severity  float64 // 0.0-1.0
	Message   string
	Baseline  interface{} // Expected value
	Observed  interface{} // Actual value
	Timestamp time.Time
}

// AnomalyType categorizes anomalies
type AnomalyType string

const (
	AnomalyTypeTemporal   AnomalyType = "temporal"   // Unusual time/day
	AnomalyTypeCommand    AnomalyType = "command"    // Unusual command
	AnomalyTypeResource   AnomalyType = "resource"   // Unusual resource access
	AnomalyTypeFrequency  AnomalyType = "frequency"  // Unusual frequency
	AnomalyTypeNetwork    AnomalyType = "network"    // Unusual network source
	AnomalyTypeEscalation AnomalyType = "escalation" // Privilege escalation attempt
)

// AuditEntry represents a complete audit trail entry
type AuditEntry struct {
	// Unique identifier
	ID           string    `json:"id"`
	PreviousHash string    `json:"previous_hash"` // Hash of previous entry (blockchain-like)
	Hash         string    `json:"hash"`          // Hash of this entry
	Signature    string    `json:"signature"`     // Digital signature
	
	// Timestamp
	Timestamp    time.Time `json:"timestamp"`
	
	// User context
	User         AuditUser `json:"user"`
	Session      AuditSession `json:"session"`
	
	// Request
	RawInput     string    `json:"raw_input"`
	RequestID    string    `json:"request_id"`
	
	// Parsing
	Intent       string    `json:"intent"`
	Command      string    `json:"command"`
	Confidence   float64   `json:"confidence"`
	
	// Security checks (7 layers)
	AuthResult         CheckResult `json:"auth_result"`
	AuthzResult        CheckResult `json:"authz_result"`
	SandboxResult      CheckResult `json:"sandbox_result"`
	IntentValResult    CheckResult `json:"intent_validation_result"`
	RateLimitResult    CheckResult `json:"rate_limit_result"`
	BehaviorResult     BehaviorCheck `json:"behavior_result"`
	
	// Execution
	Executed         bool      `json:"executed"`
	ExecutionStatus  string    `json:"execution_status"`
	ExecutionOutput  string    `json:"execution_output,omitempty"`
	ExecutionError   string    `json:"execution_error,omitempty"`
	ExecutionTime    float64   `json:"execution_time_ms"`
	
	// Risk
	RiskLevel    string    `json:"risk_level"`
	RiskScore    int       `json:"risk_score"`
}

// AuditUser is a subset of User for audit logs
type AuditUser struct {
	ID       string   `json:"id"`
	Username string   `json:"username"`
	Email    string   `json:"email"`
	Roles    []string `json:"roles"`
}

// AuditSession is a subset of Session for audit logs
type AuditSession struct {
	ID        string `json:"id"`
	IP        string `json:"ip"`
	UserAgent string `json:"user_agent"`
}

// CheckResult represents the result of a security check
type CheckResult struct {
	Passed    bool      `json:"passed"`
	Message   string    `json:"message,omitempty"`
	Timestamp time.Time `json:"timestamp"`
	Duration  float64   `json:"duration_ms"`
}

// BehaviorCheck includes risk score and anomalies
type BehaviorCheck struct {
	CheckResult
	RiskScore int       `json:"risk_score"`
	Anomalies []Anomaly `json:"anomalies,omitempty"`
}

// RiskLevel categorizes risk levels
type RiskLevel string

const (
	RiskLevelLOW      RiskLevel = "LOW"
	RiskLevelMEDIUM   RiskLevel = "MEDIUM"
	RiskLevelHIGH     RiskLevel = "HIGH"
	RiskLevelCRITICAL RiskLevel = "CRITICAL"
)

// Permission represents a granular permission
type Permission struct {
	Resource  string   // e.g., "pods", "deployments"
	Verbs     []string // e.g., ["get", "list", "watch"]
	Namespace string   // "*" for all, or specific namespace
	Labels    map[string]string // Additional label selectors
}

// Role represents a collection of permissions
type Role struct {
	Name        string
	Description string
	Permissions []Permission
	
	// Additional constraints
	RequireMFA       bool
	RequireApproval  []string // List of roles that can approve
	TimeRestrictions TimeRestriction
}

// TimeRestriction limits when a role can be used
type TimeRestriction struct {
	AllowedHours []int    // 0-23
	AllowedDays  []int    // 0-6, 0=Sunday
	Timezone     string   // e.g., "America/Sao_Paulo"
}

// Policy represents a context-aware authorization policy
type Policy struct {
	Name        string
	Description string
	
	// Conditions
	Conditions  []Condition
	
	// Effect
	Effect      PolicyEffect // ALLOW or DENY
	
	// Priority (higher = evaluated first)
	Priority    int
}

// Condition represents a policy condition
type Condition struct {
	Type     ConditionType
	Operator ConditionOperator
	Value    interface{}
}

// PolicyEffect determines if policy allows or denies
type PolicyEffect string

const (
	PolicyEffectALLOW PolicyEffect = "ALLOW"
	PolicyEffectDENY  PolicyEffect = "DENY"
)

// ConditionType categorizes policy conditions
type ConditionType string

const (
	ConditionTypeIP        ConditionType = "ip"
	ConditionTypeTime      ConditionType = "time"
	ConditionTypeDay       ConditionType = "day"
	ConditionTypeNamespace ConditionType = "namespace"
	ConditionTypeResource  ConditionType = "resource"
	ConditionTypeRiskScore ConditionType = "risk_score"
)

// ConditionOperator defines how conditions are evaluated
type ConditionOperator string

const (
	OperatorEquals       ConditionOperator = "equals"
	OperatorNotEquals    ConditionOperator = "not_equals"
	OperatorIn           ConditionOperator = "in"
	OperatorNotIn        ConditionOperator = "not_in"
	OperatorGreaterThan  ConditionOperator = "greater_than"
	OperatorLessThan     ConditionOperator = "less_than"
	OperatorContains     ConditionOperator = "contains"
)

// RateLimitConfig defines rate limiting rules
type RateLimitConfig struct {
	// Token bucket parameters
	RequestsPerMinute int
	BurstSize         int
	
	// Cooldown after violations
	CooldownSeconds int
	
	// Penalty
	ViolationPenalty time.Duration
}

// CircuitBreakerConfig defines circuit breaker parameters
type CircuitBreakerConfig struct {
	// Failure threshold
	MaxFailures      int
	
	// Open state duration
	OpenDuration     time.Duration
	
	// Half-open test count
	HalfOpenRequests int
}

// SecurityError represents a security violation
type SecurityError struct {
	Layer      string    // Which layer detected the violation
	Type       ErrorType
	Message    string
	Details    map[string]interface{}
	Timestamp  time.Time
	
	// User context
	UserID     string
	SessionID  string
	RequestID  string
}

// ErrorType categorizes security errors
type ErrorType string

const (
	ErrorTypeAuth          ErrorType = "authentication_failed"
	ErrorTypeAuthz         ErrorType = "authorization_failed"
	ErrorTypeSandbox       ErrorType = "sandbox_violation"
	ErrorTypeIntentNotConf ErrorType = "intent_not_confirmed"
	ErrorTypeRateLimit     ErrorType = "rate_limit_exceeded"
	ErrorTypeHighRisk      ErrorType = "high_risk_detected"
	ErrorTypeAuditFail     ErrorType = "audit_logging_failed"
)

// Error implements the error interface
func (e *SecurityError) Error() string {
	return e.Message
}

// HighRiskError is returned when risk score exceeds threshold
type HighRiskError struct {
	Score      int
	Threshold  int
	Anomalies  []Anomaly
}

func (e *HighRiskError) Error() string {
	return "High risk behavior detected"
}

// IntentNotConfirmedError is returned when user doesn't confirm intent
type IntentNotConfirmedError struct {
	Command string
	Reason  string
}

func (e *IntentNotConfirmedError) Error() string {
	return "User did not confirm command intent"
}
