// Package nlp provides natural language processing capabilities for vcli-go
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This package implements a production-grade NLP parser with Zero Trust security.
// It allows users to interact with vcli using natural language in Portuguese and English.
package nlp

import (
	"context"
	"time"
)

// Language represents supported languages
type Language string

const (
	LanguagePTBR Language = "pt-BR"
	LanguageEN   Language = "en"
)

// TokenType categorizes tokens semantically
type TokenType string

const (
	TokenTypeVERB       TokenType = "VERB"
	TokenTypeNOUN       TokenType = "NOUN"
	TokenTypeIDENTIFIER TokenType = "IDENTIFIER"
	TokenTypeFILTER     TokenType = "FILTER"
	TokenTypeNUMBER     TokenType = "NUMBER"
	TokenTypePREP       TokenType = "PREPOSITION"
	TokenTypeUNKNOWN    TokenType = "UNKNOWN"
)

// Token represents a parsed token from natural language input
type Token struct {
	Raw        string    `json:"raw"`        // Original text
	Normalized string    `json:"normalized"` // Normalized form
	Type       TokenType `json:"type"`       // Semantic type
	Language   Language  `json:"language"`   // Detected language
	Confidence float64   `json:"confidence"` // Correction confidence (0-1)
	Position   int       `json:"position"`   // Position in input
}

// IntentCategory represents high-level user intent
type IntentCategory string

const (
	IntentCategoryQUERY       IntentCategory = "QUERY"       // Read operations
	IntentCategoryACTION      IntentCategory = "ACTION"      // Write operations
	IntentCategoryINVESTIGATE IntentCategory = "INVESTIGATE" // Analysis
	IntentCategoryORCHESTRATE IntentCategory = "ORCHESTRATE" // Workflows
	IntentCategoryNAVIGATE    IntentCategory = "NAVIGATE"    // UI navigation
	IntentCategoryCONFIGURE   IntentCategory = "CONFIGURE"   // Settings
	IntentCategoryHELP        IntentCategory = "HELP"        // Assistance
)

// Modifier represents command modifiers (flags, filters)
type Modifier struct {
	Type  string                 `json:"type"`            // Flag, Filter, Option
	Key   string                 `json:"key"`             // Modifier key
	Value string                 `json:"value"`           // Modifier value
	Meta  map[string]interface{} `json:"meta,omitempty"`  // Additional metadata
}

// Intent represents parsed user intent
type Intent struct {
	Category      IntentCategory `json:"category"`       // High-level category
	Verb          string         `json:"verb"`           // Primary action verb
	Target        string         `json:"target"`         // Primary target resource
	Modifiers     []Modifier     `json:"modifiers"`      // Command modifiers
	Confidence    float64        `json:"confidence"`     // Overall confidence (0-1)
	OriginalInput string         `json:"original_input"` // Original NL input
	RiskLevel     RiskLevel      `json:"risk_level"`     // Security risk assessment
}

// RiskLevel categorizes command risk
type RiskLevel string

const (
	RiskLevelLOW      RiskLevel = "LOW"      // Read-only, safe
	RiskLevelMEDIUM   RiskLevel = "MEDIUM"   // Reversible changes
	RiskLevelHIGH     RiskLevel = "HIGH"     // Significant state changes
	RiskLevelCRITICAL RiskLevel = "CRITICAL" // Irreversible destruction
)

// EntityType categorizes extracted entities
type EntityType string

const (
	EntityTypeK8S_RESOURCE EntityType = "K8S_RESOURCE" // Kubernetes resources
	EntityTypeNAMESPACE    EntityType = "NAMESPACE"    // Namespace identifier
	EntityTypeNAME         EntityType = "NAME"         // Resource name
	EntityTypeLABEL        EntityType = "LABEL"        // Label selector
	EntityTypeNUMBER       EntityType = "NUMBER"       // Numeric value
	EntityTypeSTATUS       EntityType = "STATUS"       // Status condition
	EntityTypeTIMERANGE    EntityType = "TIMERANGE"    // Time range filter
	EntityTypeWORKFLOW     EntityType = "WORKFLOW"     // Workflow identifier
)

// Entity represents an extracted entity from natural language
type Entity struct {
	Type       EntityType             `json:"type"`               // Entity type
	Value      string                 `json:"value"`              // Raw value
	Normalized string                 `json:"normalized"`         // Normalized value
	Metadata   map[string]interface{} `json:"metadata,omitempty"` // Additional metadata
	Span       [2]int                 `json:"span"`               // [start, end] position
}

// Command represents a generated vcli command
type Command struct {
	Path       []string          `json:"path"`                 // Command path (e.g., ["k8s", "get", "pods"])
	Flags      map[string]string `json:"flags"`                // Command flags
	Args       []string          `json:"args"`                 // Additional arguments
	PipeChain  []*Command        `json:"pipe_chain,omitempty"` // For command pipelines
	Confidence float64           `json:"confidence"`           // Generation confidence
}

// String returns the command as a string
func (c *Command) String() string {
	result := ""
	for _, p := range c.Path {
		result += p + " "
	}
	for k, v := range c.Flags {
		result += k + " " + v + " "
	}
	for _, a := range c.Args {
		result += a + " "
	}
	return result
}

// ClarificationOption represents a choice when intent is ambiguous
type ClarificationOption struct {
	Label       string   `json:"label"`       // User-facing label
	Command     *Command `json:"command"`     // Resulting command
	Description string   `json:"description"` // Detailed description
}

// ClarificationRequest represents ambiguity that needs user input
type ClarificationRequest struct {
	Message       string                 `json:"message"`        // Clarification prompt
	Options       []ClarificationOption  `json:"options"`        // Available choices
	AllowFreeform bool                   `json:"allow_freeform"` // Allow free-text response
}

// ParseResult represents the final parsing result
type ParseResult struct {
	Command       *Command              `json:"command"`                 // Generated command
	Intent        *Intent               `json:"intent"`                  // Parsed intent
	Entities      []Entity              `json:"entities"`                // Extracted entities
	Confidence    float64               `json:"confidence"`              // Overall confidence
	Alternatives  []*Command            `json:"alternatives,omitempty"`  // Alternative commands
	Clarification *ClarificationRequest `json:"clarification,omitempty"` // If ambiguous
}

// Parser is the main NLP interface
type Parser interface {
	// Parse parses natural language input into a command
	Parse(ctx context.Context, input string) (*ParseResult, error)
	
	// ParseWithContext parses with conversational context
	ParseWithContext(ctx context.Context, input string, sessionCtx *Context) (*ParseResult, error)
}

// Context represents conversational context
type Context struct {
	SessionID       string              `json:"session_id"`        // Session identifier
	History         []HistoryEntry      `json:"history"`           // Command history
	CurrentNS       string              `json:"current_namespace"` // Current namespace
	CurrentResource string              `json:"current_resource"`  // Current resource type
	LastResources   map[string][]string `json:"last_resources"`    // Recent resources by type
	Preferences     map[string]string   `json:"preferences"`       // User preferences
	Created         time.Time           `json:"created"`           // Context creation time
	Updated         time.Time           `json:"updated"`           // Last update time
}

// HistoryEntry represents a command in history
type HistoryEntry struct {
	Input     string    `json:"input"`     // Original NL input
	Intent    *Intent   `json:"intent"`    // Parsed intent
	Command   *Command  `json:"command"`   // Generated command
	Success   bool      `json:"success"`   // Execution success
	Error     string    `json:"error"`     // Error message if failed
	Timestamp time.Time `json:"timestamp"` // Execution timestamp
}

// Feedback represents user feedback on parsing
type Feedback struct {
	Type       FeedbackType `json:"type"`                // Feedback type
	Positive   bool         `json:"positive"`            // Positive or negative
	Input      string       `json:"input"`               // Original input
	Intent     *Intent      `json:"intent"`              // Parsed intent
	Command    *Command     `json:"command"`             // Generated command
	Correction string       `json:"correction"`          // User correction if provided
	Timestamp  time.Time    `json:"timestamp"`           // Feedback timestamp
}

// FeedbackType categorizes feedback
type FeedbackType string

const (
	FeedbackTypeExplicit FeedbackType = "EXPLICIT" // User explicitly provided
	FeedbackTypeImplicit FeedbackType = "IMPLICIT" // Inferred from execution result
)

// UserSession represents an authenticated user session
type UserSession struct {
	UserID            string    `json:"user_id"`             // User identifier
	SessionID         string    `json:"session_id"`          // Session identifier
	AuthMethod        string    `json:"auth_method"`         // Authentication method
	AuthTimestamp     time.Time `json:"auth_timestamp"`      // Authentication time
	DeviceFingerprint string    `json:"device_fingerprint"`  // Device identifier
	IPAddress         string    `json:"ip_address"`          // Client IP
	GeoLocation       string    `json:"geo_location"`        // Geographic location
	Verified          bool      `json:"verified"`            // Verification status
	MFACompleted      bool      `json:"mfa_completed"`       // MFA completion status
}

// IsExpired checks if session is expired
func (s *UserSession) IsExpired() bool {
	// Session expires after 24 hours
	return time.Since(s.AuthTimestamp) > 24*time.Hour
}
