// Package security - The Guardian: Zero Trust NLP Security Orchestrator
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is the main orchestrator for the 7-layer security validation system.
// Every natural language command passes through all 7 layers before execution.
//
// The 7 Layers:
//  1. Authentication - "Who are you?"
//  2. Authorization - "What can you do?"
//  3. Sandboxing - "What is your scope?"
//  4. Intent Validation - "Are you sure?"
//  5. Flow Control - "How often?"
//  6. Behavioral Analysis - "Is this normal for you?"
//  7. Audit - "What did you do?"
package security

import (
	"context"
	"fmt"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"

	"github.com/verticedev/vcli-go/internal/security/auth"
	"github.com/verticedev/vcli-go/internal/security/audit"
	"github.com/verticedev/vcli-go/internal/security/authz"
	"github.com/verticedev/vcli-go/internal/security/behavioral"
	"github.com/verticedev/vcli-go/internal/security/flow_control"
	"github.com/verticedev/vcli-go/internal/security/intent_validation"
	"github.com/verticedev/vcli-go/internal/security/sandbox"
	pkgnlp "github.com/verticedev/vcli-go/pkg/nlp"
)

// Guardian is the main orchestrator of security-first NLP
type Guardian interface {
	// ParseSecure performs full security-validated parsing
	ParseSecure(ctx context.Context, req *ParseRequest) (*SecureParseResult, error)

	// ValidateCommand checks if command passes all 7 layers
	ValidateCommand(ctx context.Context, cmd *pkgnlp.Command, user *auth.UserIdentity) (*ValidationResult, error)

	// Execute runs validated command with full audit trail
	Execute(ctx context.Context, cmd *pkgnlp.Command, user *auth.UserIdentity) (*ExecutionResult, error)
}

// ParseRequest encapsulates all request data
type ParseRequest struct {
	Input         string            // Natural language input
	Token         string            // Auth token
	SessionCtx    *pkgnlp.Context   // Session context
	ClientContext *ClientContext    // IP, location, device
}

// ClientContext provides contextual information about the client
type ClientContext struct {
	IP        string
	UserAgent string
	Location  string
	DeviceID  string
	Timestamp time.Time
}

// SecureParseResult includes security metadata
type SecureParseResult struct {
	ParseResult        *pkgnlp.ParseResult // NLP parse result
	SecurityDecision   *SecurityDecision   // All layer decisions
	RequiresConfirm    bool                // HITL confirmation needed
	ReverseTranslation string              // Human-readable translation
	RiskScore          float64             // Behavioral risk (0-1)
	AuditID            string              // Audit log entry ID
	User               *auth.UserIdentity  // Authenticated user
}

// SecurityDecision aggregates all layer decisions
type SecurityDecision struct {
	Authenticated bool
	Authorized    bool
	SandboxPassed bool
	IntentValid   bool
	FlowAllowed   bool
	BehavioralOK  bool
	AuditLogged   bool

	Layers [7]*LayerDecision
}

// LayerDecision represents a single layer's decision
type LayerDecision struct {
	LayerName string
	Passed    bool
	Duration  time.Duration
	Error     error
	Metadata  map[string]interface{}
}

// ValidationResult from ValidateCommand
type ValidationResult struct {
	Valid    bool
	Decision *SecurityDecision
	Reason   string
}

// ExecutionResult from Execute
type ExecutionResult struct {
	Success  bool
	Output   string
	Error    error
	Duration time.Duration
	AuditID  string
}

// guardian implements Guardian interface
type guardian struct {
	// 7 Layers
	auth       auth.AuthLayer
	authz      authz.AuthzLayer
	sandbox    sandbox.SandboxLayer
	intent     intent_validation.IntentValidationLayer
	flow       flow_control.FlowControlLayer
	behavioral behavioral.BehavioralLayer
	audit      audit.AuditLayer

	// NLP Parser
	parser pkgnlp.Parser

	// Metrics
	metricsRegistry *prometheus.Registry
}

// Metrics
var (
	parseRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "nlp_parse_requests_total",
			Help: "Total number of NLP parse requests",
		},
		[]string{"result"}, // success, blocked, error
	)

	parseDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "nlp_parse_duration_seconds",
			Help:    "NLP parse duration by layer",
			Buckets: prometheus.ExponentialBuckets(0.001, 2, 10), // 1ms to ~1s
		},
		[]string{"layer"},
	)

	securityBlocksTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "nlp_security_blocks_total",
			Help: "Total number of security blocks",
		},
		[]string{"reason"},
	)
)

// NewGuardian creates a new Guardian orchestrator
func NewGuardian(
	authLayer auth.AuthLayer,
	authzLayer authz.AuthzLayer,
	sandboxLayer sandbox.SandboxLayer,
	intentLayer intent_validation.IntentValidationLayer,
	flowLayer flow_control.FlowControlLayer,
	behavioralLayer behavioral.BehavioralLayer,
	auditLayer audit.AuditLayer,
	parser pkgnlp.Parser,
) Guardian {
	return &guardian{
		auth:       authLayer,
		authz:      authzLayer,
		sandbox:    sandboxLayer,
		intent:     intentLayer,
		flow:       flowLayer,
		behavioral: behavioralLayer,
		audit:      auditLayer,
		parser:     parser,
	}
}

// ParseSecure implements Guardian.ParseSecure
//
// This is the main entry point. All 7 layers are executed in sequence.
func (g *guardian) ParseSecure(ctx context.Context, req *ParseRequest) (*SecureParseResult, error) {
	startTime := time.Now()
	decision := &SecurityDecision{
		Layers: [7]*LayerDecision{},
	}

	// Layer 1: Authentication
	user, err := g.executeLayer(ctx, "auth", func() (interface{}, error) {
		if g.auth == nil {
			return nil, fmt.Errorf("auth layer not configured")
		}
		return g.auth.ValidateToken(ctx, req.Token)
	})
	if err != nil {
		decision.Layers[0] = &LayerDecision{
			LayerName: "authentication",
			Passed:    false,
			Error:     err,
			Duration:  time.Since(startTime),
		}
		securityBlocksTotal.WithLabelValues("authentication").Inc()
		parseRequestsTotal.WithLabelValues("blocked").Inc()
		return nil, fmt.Errorf("authentication failed: %w", err)
	}
	decision.Layers[0] = &LayerDecision{
		LayerName: "authentication",
		Passed:    true,
		Duration:  time.Since(startTime),
	}
	decision.Authenticated = true
	userIdentity := user.(*auth.UserIdentity)

	// TODO: Implement remaining layers (Day 2-7)
	// Layer 2: Authorization
	// Layer 3: Sandboxing
	// Layer 4: Intent Validation
	// Layer 5: Flow Control
	// Layer 6: Behavioral Analysis
	// Layer 7: Audit

	// For Day 1, we stop here and return partial result
	result := &SecureParseResult{
		SecurityDecision: decision,
		User:             userIdentity,
	}

	parseRequestsTotal.WithLabelValues("success").Inc()
	return result, nil
}

// executeLayer executes a single layer and records metrics
func (g *guardian) executeLayer(ctx context.Context, layerName string, fn func() (interface{}, error)) (interface{}, error) {
	start := time.Now()
	defer func() {
		parseDuration.WithLabelValues(layerName).Observe(time.Since(start).Seconds())
	}()

	return fn()
}

// ValidateCommand implements Guardian.ValidateCommand
func (g *guardian) ValidateCommand(ctx context.Context, cmd *pkgnlp.Command, user *auth.UserIdentity) (*ValidationResult, error) {
	// TODO: Implement (Day 7)
	return nil, fmt.Errorf("not yet implemented")
}

// Execute implements Guardian.Execute
func (g *guardian) Execute(ctx context.Context, cmd *pkgnlp.Command, user *auth.UserIdentity) (*ExecutionResult, error) {
	// TODO: Implement (Day 7)
	return nil, fmt.Errorf("not yet implemented")
}
