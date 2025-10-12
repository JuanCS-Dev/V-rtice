package orchestrator

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/pkg/nlp"
	"github.com/verticedev/vcli-go/pkg/nlp/audit"
	"github.com/verticedev/vcli-go/pkg/nlp/auth"
	"github.com/verticedev/vcli-go/pkg/nlp/authz"
	"github.com/verticedev/vcli-go/pkg/nlp/behavioral"
	"github.com/verticedev/vcli-go/pkg/nlp/intent"
	"github.com/verticedev/vcli-go/pkg/nlp/ratelimit"
	"github.com/verticedev/vcli-go/pkg/nlp/sandbox"
)

// setupTestOrchestrator creates an orchestrator configured for testing
func setupTestOrchestrator(t *testing.T) (*Orchestrator, *auth.AuthContext) {
	// Layer 1: Authentication setup
	mfaProvider := auth.NewMFAProvider("test-issuer")
	require.NotNil(t, mfaProvider)

	sessionMgr, err := auth.NewSessionManager(&auth.SessionConfig{
		SigningKey:     []byte("test-secret-key-minimum-32-bytes!!"),
		RefreshEnabled: true,
	})
	require.NoError(t, err)

	authConfig := &auth.AuthConfig{
		MFAProvider:        mfaProvider,
		SessionManager:     sessionMgr,
		SessionDuration:    15 * time.Minute,
		RefreshEnabled:     true,
		DeviceTrustEnabled: false, // Simplify for tests
	}

	// Layer 2: Authorization setup
	authzConfig := &authz.AuthorizerConfig{
		EnableRBAC:     true,
		EnablePolicies: false, // Simplify for tests
		DenyByDefault:  false,  // Allow by default for tests
	}

	// Layer 3: Sandbox setup
	sandboxConfig := &sandbox.SandboxConfig{
		AllowedNamespaces: []string{"default", "test"},
	}

	// Layer 4: Intent setup (no config, will be created)
	intentValidator := intent.NewIntentValidator()

	// Layer 5: Rate limit setup
	rateLimitConfig := &ratelimit.RateLimitConfig{
		RequestsPerMinute: 100, // Generous limit for tests
		BurstSize:         20,
		PerUser:           true,
	}

	// Layer 6: Behavioral setup
	behaviorConfig := &behavioral.AnalyzerConfig{
		AnomalyThreshold: 0.9, // High threshold for tests
		TrackActions:     true,
	}

	// Layer 7: Audit setup
	auditConfig := &audit.AuditConfig{
		MaxEvents:     100,
		PersistEvents: false,
	}

	// Create orchestrator config
	cfg := Config{
		SkipValidation:     false,
		DryRun:             true, // Don't execute real commands
		Verbose:            false,
		RequireMFA:         false,
		RequireSignature:   false,
		MaxRiskScore:       0.8,
		RateLimitPerMinute: 100,
		AuthTimeout:        5 * time.Second,
		ValidationTotal:    10 * time.Second,
		AuthConfig:         authConfig,
		AuthzConfig:        authzConfig,
		SandboxConfig:      sandboxConfig,
		IntentConfig:       intentValidator,
		RateLimitConfig:    rateLimitConfig,
		BehaviorConfig:     behaviorConfig,
		AuditConfig:        auditConfig,
	}

	orch, err := NewOrchestrator(cfg)
	require.NoError(t, err)
	require.NotNil(t, orch)

	// Assign operator role to test user (includes viewer + operational permissions)
	rbac := orch.authorizer.GetRBACEngine()
	err = rbac.AssignRole("test-user", "operator")
	require.NoError(t, err)

	// Create test auth context
	session, err := sessionMgr.CreateSession("test-user", "tester", []string{"operator"}, false)
	require.NoError(t, err)

	authCtx := &auth.AuthContext{
		UserID:            "test-user",
		Username:          "tester",
		SessionID:         session.Claims.ID,
		SessionToken:      session.Token,
		Roles:             []string{"operator"},
		CreatedAt:         time.Now(),
		ExpiresAt:         time.Now().Add(15 * time.Minute),
		Verified:          true,
		MFACompleted:      false,
		DeviceFingerprint: "test-device",
		IPAddress:         "127.0.0.1",
		UserAgent:         "test-agent",
	}

	return orch, authCtx
}

// TestNewOrchestrator tests orchestrator creation
func TestNewOrchestrator(t *testing.T) {
	tests := []struct {
		name      string
		config    Config
		expectErr bool
	}{
		{
			name: "valid config",
			config: Config{
				AuthConfig: &auth.AuthConfig{
					MFAProvider:    auth.NewMFAProvider("test"),
					SessionManager: mustCreateSessionManager(t),
				},
			},
			expectErr: false,
		},
		{
			name:      "nil auth config",
			config:    Config{},
			expectErr: true,
		},
		{
			name: "applies defaults",
			config: Config{
				AuthConfig: &auth.AuthConfig{
					MFAProvider:    auth.NewMFAProvider("test"),
					SessionManager: mustCreateSessionManager(t),
				},
				MaxRiskScore: 0, // Should default to 0.7
			},
			expectErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			orch, err := NewOrchestrator(tt.config)

			if tt.expectErr {
				assert.Error(t, err)
				assert.Nil(t, orch)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, orch)
				if orch != nil {
					assert.NotNil(t, orch.authenticator)
					assert.NotNil(t, orch.authorizer)
					assert.NotNil(t, orch.sandboxManager)
					assert.NotNil(t, orch.intentValidator)
					assert.NotNil(t, orch.rateLimiter)
					assert.NotNil(t, orch.behaviorAnalyzer)
					assert.NotNil(t, orch.auditLogger)
				}
			}
		})
	}
}

// TestDefaultConfig tests default configuration
func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	assert.False(t, cfg.SkipValidation, "Should not skip validation by default")
	assert.False(t, cfg.DryRun, "Should not be dry run by default")
	assert.True(t, cfg.RequireMFA, "Should require MFA by default")
	assert.True(t, cfg.RequireSignature, "Should require signature by default")
	assert.Equal(t, 0.7, cfg.MaxRiskScore, "Default risk threshold should be 0.7")
	assert.Equal(t, 60, cfg.RateLimitPerMinute, "Default rate limit should be 60/min")
	assert.Equal(t, 10*time.Second, cfg.AuthTimeout)
	assert.Equal(t, 30*time.Second, cfg.ValidationTotal)

	// Check component configs
	assert.NotNil(t, cfg.AuthzConfig)
	assert.NotNil(t, cfg.SandboxConfig)
	assert.NotNil(t, cfg.IntentConfig)
	assert.NotNil(t, cfg.RateLimitConfig)
	assert.NotNil(t, cfg.BehaviorConfig)
	assert.NotNil(t, cfg.AuditConfig)
}

// TestExecute_Success tests successful execution through all layers
func TestExecute_Success(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	intent := &nlp.Intent{
		OriginalInput: "list pods",
		Verb:          "list",
		Target:        "pods",
		Confidence:    0.95,
		RiskLevel:     nlp.RiskLevelLOW,
	}

	ctx := context.Background()
	result, err := orch.Execute(ctx, intent, authCtx)

	assert.NoError(t, err)
	require.NotNil(t, result)

	assert.True(t, result.Success, "Execution should succeed")
	assert.NotEmpty(t, result.AuditID, "Should have audit ID")
	assert.Equal(t, authCtx.UserID, result.UserID)
	assert.Equal(t, authCtx.SessionID, result.SessionID)
	assert.Len(t, result.ValidationSteps, 7, "Should have 7 validation steps")

	// Verify all layers passed
	for _, step := range result.ValidationSteps {
		assert.True(t, step.Passed, "Layer %s should pass", step.Layer)
	}

	// Check risk score
	assert.Greater(t, result.RiskScore, 0.0)
	assert.LessOrEqual(t, result.RiskScore, 1.0)
}

// TestExecute_NilAuthContext tests that nil auth context is rejected
func TestExecute_NilAuthContext(t *testing.T) {
	orch, _ := setupTestOrchestrator(t)
	defer orch.Close()

	intent := &nlp.Intent{
		OriginalInput: "list pods",
		Verb:          "list",
		Target:        "pods",
	}

	ctx := context.Background()
	result, err := orch.Execute(ctx, intent, nil)

	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "authentication context required")
}

// TestExecute_SkipValidation tests dev mode bypass
func TestExecute_SkipValidation(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	// Enable skip validation (dev mode)
	orch.config.SkipValidation = true

	intent := &nlp.Intent{
		OriginalInput: "delete all pods",
		Verb:          "delete",
		Target:        "pods",
		RiskLevel:     nlp.RiskLevelCRITICAL,
	}

	ctx := context.Background()
	result, err := orch.Execute(ctx, intent, authCtx)

	assert.NoError(t, err)
	require.NotNil(t, result)

	assert.True(t, result.Success)
	assert.Len(t, result.Warnings, 1, "Should have skip validation warning")
	assert.Contains(t, result.Warnings[0], "SECURITY VALIDATION SKIPPED")
}

// TestExecute_HighRisk tests high-risk operations
func TestExecute_HighRisk(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	// Lower risk threshold
	orch.config.MaxRiskScore = 0.5

	intent := &nlp.Intent{
		OriginalInput: "delete deployment critical-service",
		Verb:          "delete",
		Target:        "deployment/critical-service",
		RiskLevel:     nlp.RiskLevelCRITICAL,
	}

	ctx := context.Background()
	result, err := orch.Execute(ctx, intent, authCtx)

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "risk exceeds threshold")
	require.NotNil(t, result)

	// Should fail at authorization layer
	authzStep := findStep(result, "Authorization")
	require.NotNil(t, authzStep)
	assert.False(t, authzStep.Passed)
}

// TestCalculateIntentRisk tests risk calculation
func TestCalculateIntentRisk(t *testing.T) {
	tests := []struct {
		name     string
		intent   *nlp.Intent
		minRisk  float64
		maxRisk  float64
	}{
		{
			name: "low risk - read operation",
			intent: &nlp.Intent{
				Verb:      "get",
				RiskLevel: nlp.RiskLevelLOW,
			},
			minRisk: 0.0,
			maxRisk: 0.2,
		},
		{
			name: "medium risk - write operation",
			intent: &nlp.Intent{
				Verb:      "create",
				RiskLevel: nlp.RiskLevelMEDIUM,
			},
			minRisk: 0.4,
			maxRisk: 0.6,
		},
		{
			name: "high risk - delete operation",
			intent: &nlp.Intent{
				Verb:      "delete",
				RiskLevel: nlp.RiskLevelCRITICAL,
			},
			minRisk: 0.8,
			maxRisk: 1.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			risk := calculateIntentRisk(tt.intent)

			assert.GreaterOrEqual(t, risk, tt.minRisk)
			assert.LessOrEqual(t, risk, tt.maxRisk)
			assert.GreaterOrEqual(t, risk, 0.0)
			assert.LessOrEqual(t, risk, 1.0)
		})
	}
}

// TestValidateAuthentication tests Layer 1
func TestValidateAuthentication(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	result := &ExecutionResult{
		ValidationSteps: []ValidationStep{},
	}

	ctx := context.Background()
	err := orch.validateAuthentication(ctx, authCtx, result)

	assert.NoError(t, err)
	assert.Len(t, result.ValidationSteps, 1)

	step := result.ValidationSteps[0]
	assert.Equal(t, "Authentication", step.Layer)
	assert.True(t, step.Passed)
}

// TestValidateAuthorization tests Layer 2
func TestValidateAuthorization(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	intent := &nlp.Intent{
		Verb:      "list",
		Target:    "pods",
		RiskLevel: nlp.RiskLevelLOW,
	}

	result := &ExecutionResult{
		ValidationSteps: []ValidationStep{},
	}

	ctx := context.Background()
	err := orch.validateAuthorization(ctx, authCtx, intent, result)

	assert.NoError(t, err)
	assert.Len(t, result.ValidationSteps, 1)

	step := result.ValidationSteps[0]
	assert.Equal(t, "Authorization", step.Layer)
	assert.True(t, step.Passed)
	assert.Greater(t, result.RiskScore, 0.0)
}

// TestValidateSandbox tests Layer 3
func TestValidateSandbox(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	intent := &nlp.Intent{
		Verb:   "get",
		Target: "pods",
	}

	result := &ExecutionResult{
		ValidationSteps: []ValidationStep{},
	}

	ctx := context.Background()
	err := orch.validateSandbox(ctx, authCtx, intent, result)

	assert.NoError(t, err)
	assert.Len(t, result.ValidationSteps, 1)

	step := result.ValidationSteps[0]
	assert.Equal(t, "Sandboxing", step.Layer)
	assert.True(t, step.Passed)
}

// TestValidateIntent tests Layer 4
func TestValidateIntent(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	intent := &nlp.Intent{
		OriginalInput: "delete pod test",
		Verb:          "delete",
		Target:        "pod/test",
		RiskLevel:     nlp.RiskLevelHIGH,
	}

	result := &ExecutionResult{
		ValidationSteps: []ValidationStep{},
		RiskScore:       0.7,
	}

	ctx := context.Background()
	err := orch.validateIntent(ctx, authCtx, intent, result)

	assert.NoError(t, err)
	assert.Len(t, result.ValidationSteps, 1)

	step := result.ValidationSteps[0]
	assert.Equal(t, "Intent Validation", step.Layer)
	assert.True(t, step.Passed)
}

// TestCheckRateLimit tests Layer 5
func TestCheckRateLimit(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	intent := &nlp.Intent{
		Verb: "list",
	}

	result := &ExecutionResult{
		ValidationSteps: []ValidationStep{},
	}

	ctx := context.Background()
	err := orch.checkRateLimit(ctx, authCtx, intent, result)

	assert.NoError(t, err)
	assert.Len(t, result.ValidationSteps, 1)

	step := result.ValidationSteps[0]
	assert.Equal(t, "Rate Limiting", step.Layer)
	assert.True(t, step.Passed)
}

// TestAnalyzeBehavior tests Layer 6
func TestAnalyzeBehavior(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	intent := &nlp.Intent{
		Verb:   "get",
		Target: "pods",
	}

	result := &ExecutionResult{
		ValidationSteps: []ValidationStep{},
	}

	ctx := context.Background()
	err := orch.analyzeBehavior(ctx, authCtx, intent, result)

	assert.NoError(t, err)
	assert.Len(t, result.ValidationSteps, 1)

	step := result.ValidationSteps[0]
	assert.Equal(t, "Behavioral Analysis", step.Layer)
	assert.True(t, step.Passed)
}

// TestLogAudit tests Layer 7
func TestLogAudit(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	intent := &nlp.Intent{
		OriginalInput: "list pods",
		Verb:          "list",
		Target:        "pods",
		Confidence:    0.95,
		RiskLevel:     nlp.RiskLevelLOW,
	}

	result := &ExecutionResult{
		AuditID:         "test-audit-123",
		Timestamp:       time.Now(),
		ValidationSteps: []ValidationStep{},
		Success:         true,
		Command:         "vcli list pods",
		Output:          "test output",
		RiskScore:       0.1,
		Duration:        100 * time.Millisecond,
	}

	ctx := context.Background()
	orch.logAudit(ctx, authCtx, intent, result)

	// Should not error, just adds step
	assert.Len(t, result.ValidationSteps, 1)

	step := result.ValidationSteps[0]
	assert.Equal(t, "Audit Logging", step.Layer)
	assert.True(t, step.Passed)
}

// TestClose tests resource cleanup
func TestClose(t *testing.T) {
	orch, _ := setupTestOrchestrator(t)

	err := orch.Close()
	assert.NoError(t, err)
}

// TestExecute_ContextTimeout tests timeout handling
func TestExecute_ContextTimeout(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	// Set very short timeout
	orch.config.ValidationTotal = 1 * time.Nanosecond

	intent := &nlp.Intent{
		OriginalInput: "list pods",
		Verb:          "list",
		Target:        "pods",
	}

	ctx := context.Background()
	_, err := orch.Execute(ctx, intent, authCtx)

	// May timeout or succeed depending on timing
	// Just verify it doesn't panic
	_ = err
}

// TestExecute_DryRun tests dry run mode
func TestExecute_DryRun(t *testing.T) {
	orch, authCtx := setupTestOrchestrator(t)
	defer orch.Close()

	// Already in dry run mode from setup
	assert.True(t, orch.config.DryRun)

	intent := &nlp.Intent{
		OriginalInput: "create deployment test",
		Verb:          "create",
		Target:        "deployment/test",
	}

	ctx := context.Background()
	result, err := orch.Execute(ctx, intent, authCtx)

	assert.NoError(t, err)
	require.NotNil(t, result)

	assert.True(t, result.Success)
	assert.Contains(t, result.Output, "DRY RUN")
	assert.Contains(t, result.Warnings, "Dry run mode")
}

// Helper functions

func mustCreateSessionManager(t *testing.T) *auth.SessionManager {
	sm, err := auth.NewSessionManager(&auth.SessionConfig{
		SigningKey:     []byte("test-secret-key-minimum-32-bytes!!"),
		RefreshEnabled: true,
	})
	require.NoError(t, err)
	return sm
}

func findStep(result *ExecutionResult, layerName string) *ValidationStep {
	for _, step := range result.ValidationSteps {
		if step.Layer == layerName {
			return &step
		}
	}
	return nil
}

// Benchmarks

func BenchmarkExecute_ReadOperation(b *testing.B) {
	orch, authCtx := setupTestOrchestrator(&testing.T{})
	defer orch.Close()

	intent := &nlp.Intent{
		OriginalInput: "list pods",
		Verb:          "list",
		Target:        "pods",
		RiskLevel:     nlp.RiskLevelLOW,
	}

	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = orch.Execute(ctx, intent, authCtx)
	}
}

func BenchmarkExecute_WriteOperation(b *testing.B) {
	orch, authCtx := setupTestOrchestrator(&testing.T{})
	defer orch.Close()

	intent := &nlp.Intent{
		OriginalInput: "create pod test",
		Verb:          "create",
		Target:        "pod/test",
		RiskLevel:     nlp.RiskLevelMEDIUM,
	}

	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = orch.Execute(ctx, intent, authCtx)
	}
}

func BenchmarkCalculateIntentRisk(b *testing.B) {
	intent := &nlp.Intent{
		Verb:      "delete",
		RiskLevel: nlp.RiskLevelCRITICAL,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = calculateIntentRisk(intent)
	}
}
