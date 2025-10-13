package intent

import (
"context"
"testing"
"time"

"strings"
"github.com/stretchr/testify/assert"
"github.com/stretchr/testify/require"
)

func TestNewIntentValidator(t *testing.T) {
validator := NewIntentValidator()
assert.NotNil(t, validator)
assert.NotNil(t, validator.riskAnalyzer)
}

func TestRiskLevel_String(t *testing.T) {
	tests := []struct {
		level    RiskLevel
		expected string
	}{
		{RiskLevelSafe, "SAFE"},
		{RiskLevelLow, "LOW"},
		{RiskLevelMedium, "MEDIUM"},
		{RiskLevelHigh, "HIGH"},
		{RiskLevelCritical, "CRITICAL"},
		{RiskLevel(99), "UNKNOWN"},
	}
	
	for _, tt := range tests {
		assert.Equal(t, tt.expected, tt.level.String())
	}
}

func TestCalculateRisk_SafeCommands(t *testing.T) {
analyzer := NewRiskAnalyzer()

intent := &CommandIntent{
Action:   "get",
Resource: "pods",
}

risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelSafe, risk)
}

func TestCalculateRisk_MediumCommands(t *testing.T) {
analyzer := NewRiskAnalyzer()

intent := &CommandIntent{
Action:   "scale",
Resource: "deployment",
Target:   "myapp",
}

risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelMedium, risk)
}

func TestCalculateRisk_HighCommands(t *testing.T) {
analyzer := NewRiskAnalyzer()

intent := &CommandIntent{
Action:   "delete",
Resource: "pod",
Target:   "mypod",
}

risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelHigh, risk)
}

func TestCalculateRisk_CriticalCommands(t *testing.T) {
analyzer := NewRiskAnalyzer()

t.Run("Delete namespace", func(t *testing.T) {
intent := &CommandIntent{
Action:   "delete",
Resource: "namespace",
Target:   "production",
}

risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelCritical, risk)
})

t.Run("Delete with wildcard", func(t *testing.T) {
intent := &CommandIntent{
Action:      "delete",
Resource:    "pods",
Target:      "all",
HasWildcard: true,
}

risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelCritical, risk)
})
}

func TestValidateIntent_SafeCommand(t *testing.T) {
validator := NewIntentValidator()
ctx := context.Background()

intent := &CommandIntent{
Action:   "get",
Resource: "pods",
}

result, err := validator.ValidateIntent(ctx, intent)
require.NoError(t, err)

assert.Equal(t, RiskLevelSafe, result.RiskLevel)
assert.False(t, result.RequiresHITL)
assert.False(t, result.RequiresSignature)
assert.Empty(t, result.Warnings)
}

func TestValidateIntent_MediumRisk(t *testing.T) {
validator := NewIntentValidator()
ctx := context.Background()

intent := &CommandIntent{
Action:   "scale",
Resource: "deployment",
Target:   "myapp",
}

result, err := validator.ValidateIntent(ctx, intent)
require.NoError(t, err)

assert.Equal(t, RiskLevelMedium, result.RiskLevel)
assert.True(t, result.RequiresHITL)
assert.False(t, result.RequiresSignature)
assert.NotNil(t, result.ConfirmationToken)
assert.True(t, result.IsReversible)
}

func TestValidateIntent_HighRisk(t *testing.T) {
validator := NewIntentValidator()
ctx := context.Background()

intent := &CommandIntent{
Action:   "delete",
Resource: "pod",
Target:   "critical-pod",
}

result, err := validator.ValidateIntent(ctx, intent)
require.NoError(t, err)

assert.Equal(t, RiskLevelHigh, result.RiskLevel)
assert.True(t, result.RequiresHITL)
assert.True(t, result.RequiresSignature)
assert.NotEmpty(t, result.Warnings)
assert.False(t, result.IsReversible)
}

func TestValidateIntent_CriticalRisk(t *testing.T) {
validator := NewIntentValidator()
ctx := context.Background()

intent := &CommandIntent{
Action:      "delete",
Resource:    "namespace",
Target:      "production",
HasWildcard: false,
}

result, err := validator.ValidateIntent(ctx, intent)
require.NoError(t, err)

assert.Equal(t, RiskLevelCritical, result.RiskLevel)
found := false
	for _, w := range result.Warnings {
		if strings.Contains(w, "🚨 CRITICAL") {
			found = true
			break
		}
	}
	assert.True(t, found)
}

func TestConfirmIntent(t *testing.T) {
validator := NewIntentValidator()
ctx := context.Background()

// Create intent with HITL requirement
intent := &CommandIntent{
Action:   "delete",
Resource: "pod",
}

result, _ := validator.ValidateIntent(ctx, intent)
token := result.ConfirmationToken.Token

// Confirm intent
result.ConfirmationToken.UserID = "user123"
err := validator.ConfirmIntent(ctx, token, "user123")
require.NoError(t, err)

// Check confirmed
assert.True(t, validator.IsConfirmed(token))
}

func TestConfirmIntent_Expired(t *testing.T) {
validator := NewIntentValidator()
ctx := context.Background()

// Create expired token
token := &ConfirmationToken{
Token:     "expired-token",
ExpiresAt: time.Now().Add(-1 * time.Hour),
UserID:    "user123",
}
validator.confirmations[token.Token] = token

err := validator.ConfirmIntent(ctx, token.Token, "user123")
assert.Error(t, err)
assert.Contains(t, err.Error(), "expired")
}

func TestConfirmIntent_UserMismatch(t *testing.T) {
validator := NewIntentValidator()
ctx := context.Background()

token := &ConfirmationToken{
Token:     "token123",
ExpiresAt: time.Now().Add(5 * time.Minute),
UserID:    "user1",
}
validator.confirmations[token.Token] = token

err := validator.ConfirmIntent(ctx, token.Token, "user2")
assert.Error(t, err)
assert.Contains(t, err.Error(), "mismatch")
}

func TestGenerateWarnings(t *testing.T) {
validator := NewIntentValidator()

t.Run("Wildcard warning", func(t *testing.T) {
intent := &CommandIntent{
Action:      "delete",
Resource:    "pods",
HasWildcard: true,
}

warnings := validator.generateWarnings(intent, RiskLevelHigh)
assert.Contains(t, warnings[0], "MULTIPLE")
})

t.Run("System namespace warning", func(t *testing.T) {
intent := &CommandIntent{
Action:    "update",
Namespace: "kube-system",
}

warnings := validator.generateWarnings(intent, RiskLevelMedium)
assert.Contains(t, warnings[0], "SYSTEM")
})

t.Run("Delete warning", func(t *testing.T) {
intent := &CommandIntent{
Action: "delete",
}

warnings := validator.generateWarnings(intent, RiskLevelHigh)
found := false
for _, w := range warnings {
if strings.Contains(w, "IRREVERSIBLE") {
found = true
break
}
}
assert.True(t, found)
})
}

func TestCheckReversibility(t *testing.T) {
validator := NewIntentValidator()

t.Run("Delete is not reversible", func(t *testing.T) {
intent := &CommandIntent{Action: "delete"}
reversible, _ := validator.checkReversibility(intent)
assert.False(t, reversible)
})

t.Run("Scale is reversible", func(t *testing.T) {
intent := &CommandIntent{Action: "scale", Target: "deployment"}
reversible, undo := validator.checkReversibility(intent)
assert.True(t, reversible)
assert.NotEmpty(t, undo)
})

t.Run("Read is reversible", func(t *testing.T) {
intent := &CommandIntent{Action: "get"}
reversible, _ := validator.checkReversibility(intent)
assert.True(t, reversible)
})
}

func TestCleanupExpiredTokens(t *testing.T) {
validator := NewIntentValidator()

// Add expired token
expired := &ConfirmationToken{
Token:     "expired",
ExpiresAt: time.Now().Add(-1 * time.Hour),
}
validator.confirmations[expired.Token] = expired

// Add valid token
valid := &ConfirmationToken{
Token:     "valid",
ExpiresAt: time.Now().Add(1 * time.Hour),
}
validator.confirmations[valid.Token] = valid

removed := validator.CleanupExpiredTokens()
assert.Equal(t, 1, removed)
assert.Len(t, validator.confirmations, 1)
}

func TestGetPendingConfirmations(t *testing.T) {
validator := NewIntentValidator()

// Add pending
pending := &ConfirmationToken{
Token:     "pending",
ExpiresAt: time.Now().Add(5 * time.Minute),
Confirmed: false,
}
validator.confirmations[pending.Token] = pending

// Add confirmed
confirmed := &ConfirmationToken{
Token:     "confirmed",
ExpiresAt: time.Now().Add(5 * time.Minute),
Confirmed: true,
}
validator.confirmations[confirmed.Token] = confirmed

pendingList := validator.GetPendingConfirmations()
assert.Len(t, pendingList, 1)
assert.Equal(t, "pending", pendingList[0].Token)
}

func TestRiskToScore(t *testing.T) {
analyzer := NewRiskAnalyzer()

assert.Equal(t, 0.0, analyzer.RiskToScore(RiskLevelSafe))
assert.Equal(t, 0.25, analyzer.RiskToScore(RiskLevelLow))
assert.Equal(t, 0.5, analyzer.RiskToScore(RiskLevelMedium))
assert.Equal(t, 0.75, analyzer.RiskToScore(RiskLevelHigh))
assert.Equal(t, 1.0, analyzer.RiskToScore(RiskLevelCritical))
}

// TestGetConfirmationToken tests token retrieval
func TestGetConfirmationToken(t *testing.T) {
validator := NewIntentValidator()

// Non-existent token
token, exists := validator.GetConfirmationToken("nonexistent")
assert.Nil(t, token)
assert.False(t, exists)

// Create a token
testToken := &ConfirmationToken{
Token:     "test123",
Command:   "delete pod",
RiskLevel: RiskLevelHigh,
ExpiresAt: time.Now().Add(5 * time.Minute),
}
validator.confirmations[testToken.Token] = testToken

// Retrieve existing token
retrieved, exists := validator.GetConfirmationToken("test123")
assert.NotNil(t, retrieved)
assert.True(t, exists)
assert.Equal(t, "test123", retrieved.Token)
assert.Equal(t, "delete pod", retrieved.Command)
}

// TestExplainRisk tests risk explanations
func TestExplainRisk(t *testing.T) {
validator := NewIntentValidator()

tests := []struct {
name     string
intent   *CommandIntent
risk     RiskLevel
contains string
}{
{
name:     "Safe explanation",
intent:   &CommandIntent{Action: "get", Resource: "pods"},
risk:     RiskLevelSafe,
contains: "read-only",
},
{
name:     "Low explanation",
intent:   &CommandIntent{Action: "logs", Resource: "pod"},
risk:     RiskLevelLow,
contains: "Low risk",
},
{
name:     "Medium explanation",
intent:   &CommandIntent{Action: "scale", Resource: "deployment"},
risk:     RiskLevelMedium,
contains: "Medium risk",
},
{
name:     "High explanation",
intent:   &CommandIntent{Action: "delete", Resource: "pod"},
risk:     RiskLevelHigh,
contains: "IRREVERSIBLE",
},
{
name:     "Critical explanation",
intent:   &CommandIntent{Action: "delete", Resource: "namespace", Target: "prod"},
risk:     RiskLevelCritical,
contains: "CRITICAL",
},
{
name:     "Unknown risk",
intent:   &CommandIntent{Action: "test"},
risk:     RiskLevel(99),
contains: "Unknown",
},
}

for _, tt := range tests {
t.Run(tt.name, func(t *testing.T) {
explanation := validator.explainRisk(tt.intent, tt.risk)
assert.Contains(t, explanation, tt.contains)
})
}
}

// TestCheckReversibility_AllCases tests all reversibility scenarios
func TestCheckReversibility_AllCases(t *testing.T) {
validator := NewIntentValidator()

tests := []struct {
name       string
intent     *CommandIntent
reversible bool
undoHas    string
}{
{
name:       "Delete not reversible",
intent:     &CommandIntent{Action: "delete", Resource: "pod"},
reversible: false,
undoHas:    "",
},
{
name:       "Scale reversible",
intent:     &CommandIntent{Action: "scale", Target: "myapp"},
reversible: true,
undoHas:    "scale",
},
{
name:       "Restart reversible",
intent:     &CommandIntent{Action: "restart"},
reversible: true,
undoHas:    "restart",
},
{
name:       "Update reversible",
intent:     &CommandIntent{Action: "update"},
reversible: true,
undoHas:    "rollback",
},
{
name:       "Patch reversible",
intent:     &CommandIntent{Action: "patch"},
reversible: true,
undoHas:    "rollback",
},
{
name:       "Get reversible",
intent:     &CommandIntent{Action: "get"},
reversible: true,
undoHas:    "read-only",
},
{
name:       "List reversible",
intent:     &CommandIntent{Action: "list"},
reversible: true,
undoHas:    "read-only",
},
{
name:       "Unknown action",
intent:     &CommandIntent{Action: "unknown"},
reversible: false,
undoHas:    "",
},
}

for _, tt := range tests {
t.Run(tt.name, func(t *testing.T) {
reversible, undo := validator.checkReversibility(tt.intent)
assert.Equal(t, tt.reversible, reversible)
if tt.undoHas != "" {
assert.Contains(t, undo, tt.undoHas)
}
})
}
}

// TestIsReadAction tests read action detection
func TestIsReadAction(t *testing.T) {
readActions := []string{"get", "list", "describe", "watch", "show", "view", "GET", "LIST"}
nonReadActions := []string{"delete", "create", "update", "patch", "apply"}

for _, action := range readActions {
assert.True(t, isReadAction(action), "Expected %s to be read action", action)
}

for _, action := range nonReadActions {
assert.False(t, isReadAction(action), "Expected %s NOT to be read action", action)
}
}

// TestTranslateCommand tests command translation
func TestTranslateCommand(t *testing.T) {
validator := NewIntentValidator()

tests := []struct {
name     string
intent   *CommandIntent
expected string
}{
{
name: "Simple command",
intent: &CommandIntent{
Action:   "get",
Resource: "pods",
},
expected: "get pods",
},
{
name: "With target",
intent: &CommandIntent{
Action:   "delete",
Resource: "pod",
Target:   "mypod",
},
expected: "delete pod mypod",
},
{
name: "With namespace",
intent: &CommandIntent{
Action:    "get",
Resource:  "pods",
Namespace: "kube-system",
},
expected: "get pods in namespace kube-system",
},
{
name: "Full command",
intent: &CommandIntent{
Action:    "scale",
Resource:  "deployment",
Target:    "myapp",
Namespace: "production",
},
expected: "scale deployment myapp in namespace production",
},
}

for _, tt := range tests {
t.Run(tt.name, func(t *testing.T) {
result := validator.translateCommand(tt.intent)
assert.Equal(t, tt.expected, result)
})
}
}

// TestValidateIntent_NilContext tests nil context error
func TestValidateIntent_NilContext(t *testing.T) {
validator := NewIntentValidator()
intent := &CommandIntent{Action: "get", Resource: "pods"}

_, err := validator.ValidateIntent(nil, intent)
assert.Error(t, err)
assert.Contains(t, err.Error(), "context cannot be nil")
}

// TestValidateIntent_NilIntent tests nil intent error
func TestValidateIntent_NilIntent(t *testing.T) {
validator := NewIntentValidator()
ctx := context.Background()

_, err := validator.ValidateIntent(ctx, nil)
assert.Error(t, err)
assert.Contains(t, err.Error(), "command intent cannot be nil")
}

// TestIsConfirmed_NonExistent tests non-existent token
func TestIsConfirmed_NonExistent(t *testing.T) {
validator := NewIntentValidator()
assert.False(t, validator.IsConfirmed("nonexistent"))
}

// TestIsConfirmed_ExpiredToken tests expired confirmed token
func TestIsConfirmed_ExpiredToken(t *testing.T) {
validator := NewIntentValidator()

token := &ConfirmationToken{
Token:       "expired",
ExpiresAt:   time.Now().Add(-1 * time.Hour),
Confirmed:   true,
ConfirmedAt: time.Now().Add(-2 * time.Hour),
}
validator.confirmations[token.Token] = token

assert.False(t, validator.IsConfirmed(token.Token))
}

// TestCalculateRisk_EdgeCases tests edge cases in risk calculation
func TestCalculateRisk_EdgeCases(t *testing.T) {
analyzer := NewRiskAnalyzer()

t.Run("Secret resource bumps risk", func(t *testing.T) {
intent := &CommandIntent{
Action:   "get",
Resource: "secret",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelMedium, risk)
})

t.Run("Namespace resource is sensitive", func(t *testing.T) {
intent := &CommandIntent{
Action:   "update",
Resource: "namespace",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelMedium, risk)
})

t.Run("System namespace escalates risk", func(t *testing.T) {
intent := &CommandIntent{
Action:    "update",
Resource:  "pod",
Namespace: "kube-system",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelHigh, risk)
})

t.Run("Kube-public namespace escalates risk", func(t *testing.T) {
intent := &CommandIntent{
Action:    "create",
Resource:  "configmap",
Namespace: "kube-public",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelHigh, risk)
})

t.Run("Wildcard escalates delete to critical", func(t *testing.T) {
intent := &CommandIntent{
Action:      "delete",
Resource:    "pod",
Target:      "all",
HasWildcard: true,
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelCritical, risk)
})

t.Run("Unknown action defaults to safe", func(t *testing.T) {
intent := &CommandIntent{
Action:   "unknown",
Resource: "pod",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelSafe, risk)
})

t.Run("Drop is high risk", func(t *testing.T) {
intent := &CommandIntent{
Action:   "drop",
Resource: "table",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelHigh, risk)
})

t.Run("Flush is high risk", func(t *testing.T) {
intent := &CommandIntent{
Action:   "flush",
Resource: "cache",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelHigh, risk)
})

t.Run("Truncate is high risk", func(t *testing.T) {
intent := &CommandIntent{
Action:   "truncate",
Resource: "logs",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelHigh, risk)
})

t.Run("Exec is low risk", func(t *testing.T) {
intent := &CommandIntent{
Action:   "exec",
Resource: "pod",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelLow, risk)
})

t.Run("Port-forward is low risk", func(t *testing.T) {
intent := &CommandIntent{
Action:   "port-forward",
Resource: "service",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelLow, risk)
})

t.Run("Apply is medium risk", func(t *testing.T) {
intent := &CommandIntent{
Action:   "apply",
Resource: "deployment",
}
risk := analyzer.CalculateRisk(intent)
assert.Equal(t, RiskLevelMedium, risk)
})
}

// TestGenerateWarnings_AllWarnings tests all warning types
func TestGenerateWarnings_AllWarnings(t *testing.T) {
validator := NewIntentValidator()

t.Run("Secret resource warning", func(t *testing.T) {
intent := &CommandIntent{
Action:   "get",
Resource: "secret",
}
warnings := validator.generateWarnings(intent, RiskLevelMedium)
found := false
for _, w := range warnings {
if strings.Contains(w, "SENSITIVE") {
found = true
break
}
}
assert.True(t, found)
})

t.Run("Target all warning", func(t *testing.T) {
intent := &CommandIntent{
Action:   "delete",
Resource: "pod",
Target:   "all",
}
warnings := validator.generateWarnings(intent, RiskLevelHigh)
found := false
for _, w := range warnings {
if strings.Contains(w, "MULTIPLE") {
found = true
break
}
}
assert.True(t, found)
})

t.Run("Kube-public namespace warning", func(t *testing.T) {
intent := &CommandIntent{
Action:    "update",
Namespace: "kube-public",
}
warnings := validator.generateWarnings(intent, RiskLevelMedium)
found := false
for _, w := range warnings {
if strings.Contains(w, "SYSTEM") {
found = true
break
}
}
assert.True(t, found)
})
}

// TestConfirmIntent_NotFound tests confirming non-existent token
func TestConfirmIntent_NotFound(t *testing.T) {
validator := NewIntentValidator()
ctx := context.Background()

err := validator.ConfirmIntent(ctx, "nonexistent", "user123")
assert.Error(t, err)
assert.Contains(t, err.Error(), "not found")
}

