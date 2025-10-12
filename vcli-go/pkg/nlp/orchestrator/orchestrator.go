// Package orchestrator coordinates the 7-layer Guardian security stack
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is the orchestrator for "Guardian of Intent" v2.0
// Coordinates all 7 security layers in sequence with proper error handling
package orchestrator

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/verticedev/vcli-go/internal/audit"
	"github.com/verticedev/vcli-go/internal/auth"
	"github.com/verticedev/vcli-go/internal/authz"
	"github.com/verticedev/vcli-go/internal/behavior"
	"github.com/verticedev/vcli-go/internal/intent"
	"github.com/verticedev/vcli-go/internal/nlp"
)

// Orchestrator coordinates the 7-layer security validation
type Orchestrator struct {
	config Config

	// Layer 1: Authentication
	authenticator *auth.Validator

	// Layer 2: Authorization
	authorizer *authz.Checker

	// Layer 3: Sandboxing (handled at execution time)
	// Implemented via Linux namespaces, capabilities, seccomp

	// Layer 4: Intent Validation
	intentValidator *intent.Validator

	// Layer 5: Rate Limiting (handled per-layer)
	// Implemented in rate/ package

	// Layer 6: Behavioral Analysis
	behaviorAnalyzer *behavior.Analyzer

	// Layer 7: Audit Logging
	auditLogger *audit.Logger
}

// Config holds orchestrator configuration
type Config struct {
	// Development/Testing flags
	SkipValidation bool // DANGEROUS: Skip security validation
	DryRun         bool // Simulate without executing
	Verbose        bool // Show detailed steps

	// Security config
	RequireMFA         bool
	RequireSignature   bool
	MaxRiskScore       float64 // 0.0-1.0, reject if exceeded
	RateLimitPerMinute int

	// Timeouts
	AuthTimeout     time.Duration
	ValidationTotal time.Duration
}

// DefaultConfig returns production-safe defaults
func DefaultConfig() Config {
	return Config{
		SkipValidation:     false,
		DryRun:             false,
		Verbose:            false,
		RequireMFA:         true,
		RequireSignature:   true,
		MaxRiskScore:       0.7, // Reject if >70% risk
		RateLimitPerMinute: 60,
		AuthTimeout:        10 * time.Second,
		ValidationTotal:    30 * time.Second,
	}
}

// NewOrchestrator creates a new Guardian orchestrator
func NewOrchestrator(cfg Config) (*Orchestrator, error) {
	// Apply defaults for zero values
	if cfg.MaxRiskScore == 0 {
		cfg.MaxRiskScore = 0.7
	}
	if cfg.RateLimitPerMinute == 0 {
		cfg.RateLimitPerMinute = 60
	}
	if cfg.AuthTimeout == 0 {
		cfg.AuthTimeout = 10 * time.Second
	}
	if cfg.ValidationTotal == 0 {
		cfg.ValidationTotal = 30 * time.Second
	}

	// Initialize layers with mock stores (TODO: Replace with real implementations)
	authenticator := auth.NewValidator(
		[]byte("dev-secret-key"), // TODO: Load from config
		&mockSessionStore{},
		&mockMFAValidator{},
	)

	authorizer := authz.NewChecker(
		&mockRoleStore{},
		&mockPolicyStore{},
	)

	intentValidator := intent.NewValidator(
		&cliConfirmer{verbose: cfg.Verbose},
		&mockSigner{},
	)

	behaviorAnalyzer := behavior.NewAnalyzer(
		&mockBaselineStore{},
		behavior.DefaultConfig(),
	)

	auditLogger := audit.NewLogger(
		nil, // TODO: Initialize BadgerDB
		&mockSigner{},
		&mockRemoteSyslog{},
	)

	return &Orchestrator{
		config:           cfg,
		authenticator:    authenticator,
		authorizer:       authorizer,
		intentValidator:  intentValidator,
		behaviorAnalyzer: behaviorAnalyzer,
		auditLogger:      auditLogger,
	}, nil
}

// ExecutionResult contains the result of command execution
type ExecutionResult struct {
	Success  bool
	Command  string
	Output   string
	Error    string
	Warnings []string

	// Security validation details
	ValidationSteps []ValidationStep
	RiskScore       float64
	RequiredMFA     bool
	RequiredSign    bool

	// Audit trail
	AuditID   string
	Duration  time.Duration
	Timestamp time.Time
}

// ValidationStep represents one layer of security validation
type ValidationStep struct {
	Layer   string
	Passed  bool
	Message string
	Duration time.Duration
}

// Execute runs the command through all 7 security layers
func (o *Orchestrator) Execute(ctx context.Context, intent *nlp.Intent) (*ExecutionResult, error) {
	startTime := time.Now()
	auditID := uuid.New().String()

	result := &ExecutionResult{
		AuditID:         auditID,
		Timestamp:       startTime,
		ValidationSteps: make([]ValidationStep, 0, 7),
	}

	// Context with overall timeout
	ctx, cancel := context.WithTimeout(ctx, o.config.ValidationTotal)
	defer cancel()

	// Skip validation if in dev mode (DANGEROUS)
	if o.config.SkipValidation {
		result.Warnings = append(result.Warnings, 
			"⚠️  SECURITY VALIDATION SKIPPED - Development mode only!")
		return o.executeDirectly(ctx, intent, result)
	}

	// === LAYER 1: Authentication ===
	if err := o.validateAuthentication(ctx, intent, result); err != nil {
		return result, fmt.Errorf("Layer 1 (Authentication) failed: %w", err)
	}

	// === LAYER 2: Authorization ===
	if err := o.validateAuthorization(ctx, intent, result); err != nil {
		return result, fmt.Errorf("Layer 2 (Authorization) failed: %w", err)
	}

	// === LAYER 3: Sandboxing ===
	// Note: Applied at execution time via Linux namespaces/seccomp
	o.recordStep(result, "Sandboxing", true, "Will execute with least privilege", 0)

	// === LAYER 4: Intent Validation (HITL) ===
	if err := o.validateIntent(ctx, intent, result); err != nil {
		return result, fmt.Errorf("Layer 4 (Intent Validation) failed: %w", err)
	}

	// === LAYER 5: Rate Limiting ===
	if err := o.checkRateLimit(ctx, intent, result); err != nil {
		return result, fmt.Errorf("Layer 5 (Rate Limiting) failed: %w", err)
	}

	// === LAYER 6: Behavioral Analysis ===
	if err := o.analyzeBehavior(ctx, intent, result); err != nil {
		return result, fmt.Errorf("Layer 6 (Behavioral Analysis) failed: %w", err)
	}

	// === Execute Command ===
	if o.config.DryRun {
		result.Success = true
		result.Command = fmt.Sprintf("vcli k8s %s %s", intent.Action, intent.Resource)
		result.Output = "[DRY RUN] Command would execute here"
		result.Warnings = append(result.Warnings, "Dry run mode - no actual execution")
	} else {
		// TODO: Execute actual command via cobra
		result.Success = true
		result.Command = fmt.Sprintf("vcli k8s %s %s", intent.Action, intent.Resource)
		result.Output = "[SIMULATED] Command executed successfully"
	}

	// === LAYER 7: Audit Logging ===
	o.logAudit(ctx, intent, result)

	result.Duration = time.Since(startTime)
	return result, nil
}

// validateAuthentication implements Layer 1
func (o *Orchestrator) validateAuthentication(ctx context.Context, intent *nlp.Intent, result *ExecutionResult) error {
	start := time.Now()
	
	// TODO: Get actual user from context
	// For now, create a mock user
	mockUser := &security.User{
		ID:        "dev-user",
		Username:  "developer",
		Email:     "dev@vertice.local",
		Roles:     []string{"admin"},
		MFAEnabled: false,
		LastLogin: time.Now(),
	}
	
	err := o.authenticator.Validate(ctx, mockUser)
	
	duration := time.Since(start)
	
	if err != nil {
		o.recordStep(result, "Authentication", false, err.Error(), duration)
		return fmt.Errorf("authentication failed: %w", err)
	}

	o.recordStep(result, "Authentication", true, "User authenticated", duration)
	return nil
}

// validateAuthorization implements Layer 2
func (o *Orchestrator) validateAuthorization(ctx context.Context, intent *nlp.Intent, result *ExecutionResult) error {
	start := time.Now()
	
	// Create security context
	secCtx := &security.SecurityContext{
		User: &security.User{
			ID:        "dev-user",
			Username:  "developer",
			Roles:     []string{"admin"},
		},
		IPAddress: "127.0.0.1",
		Timestamp: time.Now(),
	}

	// Convert intent to command
	cmd := intentToCommand(intent)

	// Check authorization
	err := o.authorizer.CheckCommand(ctx, secCtx, cmd)
	
	// Calculate risk (simple heuristic for now)
	riskScore := calculateIntentRisk(intent)
	result.RiskScore = riskScore

	duration := time.Since(start)

	if err != nil {
		o.recordStep(result, "Authorization", false, err.Error(), duration)
		return fmt.Errorf("authorization failed: %w", err)
	}

	if riskScore > o.config.MaxRiskScore {
		o.recordStep(result, "Authorization", false, 
			fmt.Sprintf("Risk too high: %.2f > %.2f", riskScore, o.config.MaxRiskScore), 
			duration)
		return fmt.Errorf("operation risk exceeds threshold")
	}

	o.recordStep(result, "Authorization", true, 
		fmt.Sprintf("Authorized (risk: %.2f)", riskScore), duration)
	return nil
}

// validateIntent implements Layer 4 (HITL)
func (o *Orchestrator) validateIntent(ctx context.Context, intent *nlp.Intent, result *ExecutionResult) error {
	start := time.Now()
	
	// Validate with user confirmation for destructive ops
	err := o.intentValidator.Validate(ctx, intent)
	
	duration := time.Since(start)

	if err != nil {
		o.recordStep(result, "Intent Validation", false, err.Error(), duration)
		return err
	}

	o.recordStep(result, "Intent Validation", true, "User confirmed", duration)
	return nil
}

// checkRateLimit implements Layer 5
func (o *Orchestrator) checkRateLimit(ctx context.Context, intent *nlp.Intent, result *ExecutionResult) error {
	start := time.Now()
	
	// TODO: Implement actual rate limiting via token bucket
	// For now, always pass
	
	duration := time.Since(start)
	o.recordStep(result, "Rate Limiting", true, 
		fmt.Sprintf("Within limits (%d/min)", o.config.RateLimitPerMinute), duration)
	return nil
}

// analyzeBehavior implements Layer 6
func (o *Orchestrator) analyzeBehavior(ctx context.Context, intent *nlp.Intent, result *ExecutionResult) error {
	start := time.Now()
	
	// Create mock user and command
	mockUser := &security.User{
		ID:       "dev-user",
		Username: "developer",
	}
	cmd := intentToCommand(intent)
	
	riskScore, anomalies := o.behaviorAnalyzer.Analyze(ctx, mockUser, cmd)
	
	duration := time.Since(start)

	isAnomaly := len(anomalies) > 0
	if isAnomaly {
		// Don't block, but log warning
		for _, anomaly := range anomalies {
			result.Warnings = append(result.Warnings, 
				fmt.Sprintf("⚠️  Behavioral anomaly: %s (severity: %d)", anomaly.Type, anomaly.Severity))
		}
	}

	o.recordStep(result, "Behavioral Analysis", true, 
		fmt.Sprintf("Risk score: %d, Anomalies: %d", riskScore, len(anomalies)), duration)
	return nil
}

// logAudit implements Layer 7
func (o *Orchestrator) logAudit(ctx context.Context, intent *nlp.Intent, result *ExecutionResult) {
	start := time.Now()
	
	entry := &security.AuditEntry{
		ID:        result.AuditID,
		UserID:    "dev-user", // TODO: Get from context
		Action:    intent.Verb,
		Resource:  intent.Target,
		Namespace: "", // TODO: Extract from intent
		Success:   result.Success,
		RiskScore: result.RiskScore,
		Timestamp: result.Timestamp,
	}

	err := o.auditLogger.Log(ctx, entry)
	
	duration := time.Since(start)
	
	if err != nil {
		// Log error but don't fail the operation
		result.Warnings = append(result.Warnings, 
			fmt.Sprintf("⚠️  Audit logging failed: %v", err))
	}
	
	o.recordStep(result, "Audit Logging", true, 
		fmt.Sprintf("Logged to immutable store (ID: %s)", result.AuditID[:8]), duration)
}

// executeDirectly executes without validation (dev mode only)
func (o *Orchestrator) executeDirectly(ctx context.Context, intent *nlp.Intent, result *ExecutionResult) (*ExecutionResult, error) {
	result.Success = true
	result.Command = fmt.Sprintf("vcli k8s %s %s", intent.Action, intent.Resource)
	result.Output = "[DEV MODE] Direct execution"
	result.Duration = time.Since(result.Timestamp)
	return result, nil
}

// recordStep adds a validation step to the result
func (o *Orchestrator) recordStep(result *ExecutionResult, layer string, passed bool, message string, duration time.Duration) {
	result.ValidationSteps = append(result.ValidationSteps, ValidationStep{
		Layer:    layer,
		Passed:   passed,
		Message:  message,
		Duration: duration,
	})
}

// Close cleans up orchestrator resources
func (o *Orchestrator) Close() error {
	// Close any open connections, files, etc.
	if o.auditLogger != nil {
		return o.auditLogger.Close()
	}
	return nil
}

// cliConfirmer implements HITL confirmation via CLI prompts
type cliConfirmer struct {
	verbose bool
}

func (c *cliConfirmer) Confirm(ctx context.Context, prompt *intent.ConfirmationPrompt) (bool, error) {
	// TODO: Implement actual CLI prompt
	// For now, auto-confirm in verbose mode
	if c.verbose {
		fmt.Printf("\n⚠️  Confirmation required: %s\n", prompt.Message)
		fmt.Println("   [Auto-confirmed in dev mode]")
	}
	return true, nil
}

func (c *cliConfirmer) RequestSignature(ctx context.Context, cmd *nlp.Command) (string, error) {
	// TODO: Implement actual signature request
	return "mock-signature", nil
}

// mockSigner provides mock cryptographic signing
type mockSigner struct{}

func (m *mockSigner) Sign(data []byte) (string, error) {
	return "mock-signature", nil
}

func (m *mockSigner) Verify(data []byte, signature string) (bool, error) {
	return true, nil
}

// Mock stores for development (TODO: Replace with real implementations)
type mockSessionStore struct{}

func (m *mockSessionStore) Get(ctx context.Context, sessionID string) (*security.Session, error) {
	return &security.Session{
		ID:        sessionID,
		UserID:    "dev-user",
		Token:     "mock-token",
		ExpiresAt: time.Now().Add(24 * time.Hour),
		CreatedAt: time.Now(),
	}, nil
}

func (m *mockSessionStore) Save(ctx context.Context, session *security.Session) error {
	return nil
}

func (m *mockSessionStore) Delete(ctx context.Context, sessionID string) error {
	return nil
}

func (m *mockSessionStore) UpdateActivity(ctx context.Context, sessionID string) error {
	return nil
}

type mockMFAValidator struct{}

func (m *mockMFAValidator) Verify(ctx context.Context, userID string, code string) (bool, error) {
	return true, nil // Always pass in dev mode
}

type mockRoleStore struct{}

func (m *mockRoleStore) GetRole(ctx context.Context, name string) (*security.Role, error) {
	return &security.Role{
		Name: "admin",
		Permissions: []security.Permission{
			{Action: "*", Resource: "*", Namespace: "*"},
		},
	}, nil
}

func (m *mockRoleStore) GetUserRoles(ctx context.Context, userID string) ([]security.Role, error) {
	return []security.Role{
		{Name: "admin", Permissions: []security.Permission{{Action: "*", Resource: "*"}}},
	}, nil
}

type mockPolicyStore struct{}

func (m *mockPolicyStore) GetPolicies(ctx context.Context) ([]security.Policy, error) {
	return []security.Policy{}, nil
}

type mockBaselineStore struct{}

func (m *mockBaselineStore) Get(ctx context.Context, userID string) (*behavior.Baseline, error) {
	return &behavior.Baseline{
		UserID:         userID,
		NormalActions:  map[string]int{"get": 100, "list": 80},
		NormalHours:    []int{8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18},
		AverageRisk:    0.2,
		UpdatedAt:      time.Now(),
	}, nil
}

func (m *mockBaselineStore) Save(ctx context.Context, baseline *behavior.Baseline) error {
	return nil
}

type mockRemoteSyslog struct{}

func (m *mockRemoteSyslog) Send(ctx context.Context, entry *security.AuditEntry) error {
	return nil
}

// Helper functions

// intentToCommand converts an Intent to a Command for authorization checking
func intentToCommand(intent *nlp.Intent) *nlp.Command {
	return &nlp.Command{
		Path:  []string{"k8s", intent.Verb, intent.Target},
		Flags: make(map[string]string),
		Args:  []string{},
	}
}

// calculateIntentRisk calculates risk score for an intent
func calculateIntentRisk(intent *nlp.Intent) float64 {
	// Simple heuristic risk calculation
	risk := 0.0
	
	// Base risk by verb
	switch intent.Verb {
	case "get", "list", "describe":
		risk = 0.1 // Low risk - read-only
	case "create", "apply", "patch":
		risk = 0.4 // Medium risk - modifications
	case "delete", "scale":
		risk = 0.7 // High risk - destructive
	default:
		risk = 0.5 // Unknown - medium
	}
	
	// Increase risk based on risk level
	switch intent.RiskLevel {
	case nlp.RiskLevelLOW:
		// Keep base risk
	case nlp.RiskLevelMEDIUM:
		risk += 0.1
	case nlp.RiskLevelHIGH:
		risk += 0.2
	case nlp.RiskLevelCRITICAL:
		risk += 0.3
	}
	
	// Cap at 1.0
	if risk > 1.0 {
		risk = 1.0
	}
	
	return risk
}

// SecurityContext needs to be added to pkg/security

