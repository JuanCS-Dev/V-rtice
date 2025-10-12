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
assert.Equal(t, "SAFE", RiskLevelSafe.String())
assert.Equal(t, "CRITICAL", RiskLevelCritical.String())
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
assert.Contains(t, result.Warnings, "🚨 CRITICAL")
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
