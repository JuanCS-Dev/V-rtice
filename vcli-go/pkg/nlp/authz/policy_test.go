package authz

import (
"testing"
"time"

"github.com/stretchr/testify/assert"
"github.com/stretchr/testify/require"
)

func TestPolicyEngine_AddPolicy(t *testing.T) {
engine := NewPolicyEngine()

t.Run("ValidPolicy", func(t *testing.T) {
policy := &Policy{
Name:        "test-add-policy",
Description: "Test adding policy",
Conditions: []Condition{
{Type: ConditionEnvironment, Value: "test"},
},
}
err := engine.AddPolicy(policy)
assert.NoError(t, err)
})

t.Run("NilPolicy", func(t *testing.T) {
err := engine.AddPolicy(nil)
assert.Error(t, err)
assert.Contains(t, err.Error(), "policy cannot be nil")
})

t.Run("EmptyName", func(t *testing.T) {
policy := &Policy{
Name:        "",
Description: "Policy without name",
}
err := engine.AddPolicy(policy)
assert.Error(t, err)
assert.Contains(t, err.Error(), "policy name is required")
})
}

func TestPolicyEngine_RemovePolicy(t *testing.T) {
engine := NewPolicyEngine()

t.Run("ExistingPolicy", func(t *testing.T) {
// Add a policy first
policy := &Policy{
Name:        "test-remove-policy",
Description: "Test removing policy",
}
engine.AddPolicy(policy)

// Remove it
err := engine.RemovePolicy("test-remove-policy")
assert.NoError(t, err)

// Verify it's gone
_, err = engine.GetPolicy("test-remove-policy")
assert.Error(t, err)
})

t.Run("NonExistingPolicy", func(t *testing.T) {
err := engine.RemovePolicy("non-existing-policy")
assert.Error(t, err)
assert.Contains(t, err.Error(), "policy not found")
})

t.Run("RemoveDefaultPolicy", func(t *testing.T) {
err := engine.RemovePolicy("production-delete-restriction")
assert.NoError(t, err)

// Verify it's removed
_, err = engine.GetPolicy("production-delete-restriction")
assert.Error(t, err)
})
}

func TestPolicyEngine_GetPolicy(t *testing.T) {
engine := NewPolicyEngine()

t.Run("ExistingDefaultPolicy", func(t *testing.T) {
policy, err := engine.GetPolicy("production-delete-restriction")
require.NoError(t, err)
assert.NotNil(t, policy)
assert.Equal(t, "production-delete-restriction", policy.Name)
})

t.Run("NonExistingPolicy", func(t *testing.T) {
policy, err := engine.GetPolicy("non-existing-policy")
assert.Error(t, err)
assert.Nil(t, policy)
assert.Contains(t, err.Error(), "policy not found")
})

t.Run("AddedPolicy", func(t *testing.T) {
newPolicy := &Policy{
Name:        "test-get-policy",
Description: "Test getting policy",
}
engine.AddPolicy(newPolicy)

policy, err := engine.GetPolicy("test-get-policy")
require.NoError(t, err)
assert.Equal(t, "test-get-policy", policy.Name)
})
}

func TestPolicyEngine_EvaluatePolicies_EdgeCases(t *testing.T) {
engine := NewPolicyEngine()

t.Run("NilContext", func(t *testing.T) {
decision, err := engine.EvaluatePolicies(nil, ResourcePod, ActionGet)
assert.Error(t, err)
assert.Nil(t, decision)
assert.Contains(t, err.Error(), "authz context cannot be nil")
})

t.Run("DenyPolicy", func(t *testing.T) {
// Add a deny policy
denyPolicy := &Policy{
Name:          "test-deny",
Description:   "Test deny policy",
IsDenyPolicy:  true,
Conditions: []Condition{
{Type: ConditionEnvironment, Value: "test-env"},
},
}
engine.AddPolicy(denyPolicy)

ctx := &AuthzContext{
Environment:   "test-env",
DeviceTrusted: true,
TimeOfDay:     time.Now(),
DayOfWeek:     time.Monday,
}

decision, err := engine.EvaluatePolicies(ctx, ResourcePod, ActionGet)
require.NoError(t, err)
assert.True(t, decision.Denied)
assert.Equal(t, "Test deny policy", decision.DenyReason)
})

t.Run("MultipleMatchingPolicies", func(t *testing.T) {
engine := NewPolicyEngine()

// Add multiple policies
policy1 := &Policy{
Name: "policy1",
Conditions: []Condition{
{Type: ConditionEnvironment, Value: "staging"},
},
Requirements: []Requirement{RequirementMFA},
Priority:     100,
}
policy2 := &Policy{
Name: "policy2",
Conditions: []Condition{
{Type: ConditionEnvironment, Value: "staging"},
},
Requirements: []Requirement{RequirementSignedCommand},
Priority:     90,
}
engine.AddPolicy(policy1)
engine.AddPolicy(policy2)

ctx := &AuthzContext{
Environment:   "staging",
DeviceTrusted: true,
TimeOfDay:     time.Now(),
DayOfWeek:     time.Monday,
}

decision, err := engine.EvaluatePolicies(ctx, ResourcePod, ActionGet)
require.NoError(t, err)
assert.False(t, decision.Denied)
assert.Len(t, decision.Policies, 2)
// Both requirements should be present (and unique)
assert.Contains(t, decision.Requirements, RequirementMFA)
assert.Contains(t, decision.Requirements, RequirementSignedCommand)
})
}

func TestPolicyEngine_ListPolicies(t *testing.T) {
engine := NewPolicyEngine()

policies := engine.ListPolicies()
assert.NotEmpty(t, policies)

// Should have default policies
policyNames := make([]string, len(policies))
for i, p := range policies {
policyNames[i] = p.Name
}
assert.Contains(t, policyNames, "production-delete-restriction")
assert.Contains(t, policyNames, "secret-access-policy")
}

func TestPolicyEngine_GetPolicyCount(t *testing.T) {
engine := NewPolicyEngine()

initialCount := engine.GetPolicyCount()
assert.Greater(t, initialCount, 0) // Should have default policies

// Add a policy
engine.AddPolicy(&Policy{
Name:        "test-count-policy",
Description: "Test policy count",
})

newCount := engine.GetPolicyCount()
assert.Equal(t, initialCount+1, newCount)

// Remove a policy
engine.RemovePolicy("test-count-policy")
finalCount := engine.GetPolicyCount()
assert.Equal(t, initialCount, finalCount)
}

func TestPolicyMatching_AllConditions(t *testing.T) {
engine := NewPolicyEngine()

t.Run("ProductionDeleteRestriction", func(t *testing.T) {
ctx := &AuthzContext{
Environment:   EnvProduction,
DeviceTrusted: true,
TimeOfDay:     time.Now(),
DayOfWeek:     time.Wednesday,
}

decision, err := engine.EvaluatePolicies(ctx, ResourcePod, ActionDelete)
require.NoError(t, err)
assert.False(t, decision.Denied)

// Should match production-delete-restriction
policyNames := []string{}
for _, p := range decision.Policies {
policyNames = append(policyNames, p.Name)
}
assert.Contains(t, policyNames, "production-delete-restriction")
assert.Contains(t, decision.Requirements, RequirementMFA)
assert.Contains(t, decision.Requirements, RequirementManagerApproval)
})

t.Run("NightOperationsEscalation", func(t *testing.T) {
// Create a time at night (e.g., 23:00)
night := time.Date(2025, 1, 1, 23, 0, 0, 0, time.UTC)

ctx := &AuthzContext{
Environment:   EnvProduction,
DeviceTrusted: true,
TimeOfDay:     night,
DayOfWeek:     time.Wednesday,
}

decision, err := engine.EvaluatePolicies(ctx, ResourcePod, ActionRestart)
require.NoError(t, err)
assert.False(t, decision.Denied)

// Should match night-operations-escalation
policyNames := []string{}
for _, p := range decision.Policies {
policyNames = append(policyNames, p.Name)
}
assert.Contains(t, policyNames, "night-operations-escalation")
assert.Contains(t, decision.Requirements, RequirementOnCallConfirm)
})

t.Run("UntrustedDeviceRestriction", func(t *testing.T) {
ctx := &AuthzContext{
Environment:   EnvDevelopment,
DeviceTrusted: false, // Untrusted device
TimeOfDay:     time.Now(),
DayOfWeek:     time.Monday,
}

decision, err := engine.EvaluatePolicies(ctx, ResourcePod, ActionGet)
require.NoError(t, err)
assert.False(t, decision.Denied)

// Should match untrusted-device-restriction
policyNames := []string{}
for _, p := range decision.Policies {
policyNames = append(policyNames, p.Name)
}
assert.Contains(t, policyNames, "untrusted-device-restriction")
assert.Contains(t, decision.Requirements, RequirementMFA)
})
}

func TestSecretAccessPolicy(t *testing.T) {
engine := NewPolicyEngine()

ctx := &AuthzContext{
Environment:   EnvDevelopment,
DeviceTrusted: true,
TimeOfDay:     time.Now(),
DayOfWeek:     time.Monday,
}

decision, err := engine.EvaluatePolicies(ctx, ResourceSecret, ActionGet)
require.NoError(t, err)
assert.False(t, decision.Denied)

// Secret access always requires MFA and signed command
assert.Contains(t, decision.Requirements, RequirementMFA)
assert.Contains(t, decision.Requirements, RequirementSignedCommand)

policyNames := []string{}
for _, p := range decision.Policies {
policyNames = append(policyNames, p.Name)
}
assert.Contains(t, policyNames, "secret-access-policy")
}

func TestUniqueRequirements(t *testing.T) {
// Test the uniqueRequirements helper
reqs := []Requirement{
RequirementMFA,
RequirementSignedCommand,
RequirementMFA, // Duplicate
RequirementManagerApproval,
RequirementSignedCommand, // Duplicate
}

unique := uniqueRequirements(reqs)
assert.Len(t, unique, 3)
assert.Contains(t, unique, RequirementMFA)
assert.Contains(t, unique, RequirementSignedCommand)
assert.Contains(t, unique, RequirementManagerApproval)
}
