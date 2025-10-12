package authz

import (
"testing"
"time"

"github.com/stretchr/testify/assert"
"github.com/verticedev/vcli-go/pkg/nlp/auth"
)

func TestPermission_HasNamespace(t *testing.T) {
	t.Run("EmptyNamespaces", func(t *testing.T) {
		perm := Permission{
			Resource:   ResourcePod,
			Actions:    []Action{ActionGet},
			Namespaces: []string{}, // Empty = all allowed
		}
		assert.True(t, perm.HasNamespace("any-namespace"))
	})

	t.Run("SpecificNamespaceAllowed", func(t *testing.T) {
		perm := Permission{
			Resource:   ResourcePod,
			Actions:    []Action{ActionGet},
			Namespaces: []string{"production", "staging"},
		}
		assert.True(t, perm.HasNamespace("production"))
		assert.True(t, perm.HasNamespace("staging"))
	})

	t.Run("NamespaceNotAllowed", func(t *testing.T) {
		perm := Permission{
			Resource:   ResourcePod,
			Actions:    []Action{ActionGet},
			Namespaces: []string{"production"},
		}
		assert.False(t, perm.HasNamespace("development"))
	})
}

func TestPermission_IsReadOnly(t *testing.T) {
t.Run("OnlyReadActions", func(t *testing.T) {
perm := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionGet, ActionList, ActionDescribe},
}
assert.True(t, perm.IsReadOnly())
})

t.Run("HasWriteActions", func(t *testing.T) {
perm := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionGet, ActionCreate},
}
assert.False(t, perm.IsReadOnly())
})

t.Run("HasDeleteAction", func(t *testing.T) {
perm := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionGet, ActionDelete},
}
assert.False(t, perm.IsReadOnly())
})
}

func TestPermission_IsDangerous(t *testing.T) {
t.Run("SafeActions", func(t *testing.T) {
perm := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionGet, ActionList},
}
assert.False(t, perm.IsDangerous())
})

t.Run("DeleteAction", func(t *testing.T) {
perm := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionDelete},
}
assert.True(t, perm.IsDangerous())
})

t.Run("ExecuteAction", func(t *testing.T) {
perm := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionExecute},
}
assert.True(t, perm.IsDangerous())
})

t.Run("DebugAction", func(t *testing.T) {
perm := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionDebug},
}
assert.True(t, perm.IsDangerous())
})
}

func TestCondition_Matches(t *testing.T) {
t.Run("EnvironmentMatch", func(t *testing.T) {
cond := Condition{
Type:  ConditionEnvironment,
Value: string(EnvProduction),
}
ctx := &AuthzContext{
Environment: EnvProduction,
}
assert.True(t, cond.Matches(ctx))
})

t.Run("EnvironmentMismatch", func(t *testing.T) {
cond := Condition{
Type:  ConditionEnvironment,
Value: string(EnvProduction),
}
ctx := &AuthzContext{
Environment: EnvDevelopment,
}
assert.False(t, cond.Matches(ctx))
})

t.Run("DeviceTrustMatch", func(t *testing.T) {
cond := Condition{
Type:  ConditionDeviceTrust,
Value: "untrusted",
}
ctx := &AuthzContext{
DeviceTrusted: false,
}
assert.True(t, cond.Matches(ctx))
})

t.Run("DayOfWeekWeekend", func(t *testing.T) {
cond := Condition{
Type:  ConditionDayOfWeek,
Value: "weekend",
}
ctxSaturday := &AuthzContext{
DayOfWeek: time.Saturday,
}
ctxSunday := &AuthzContext{
DayOfWeek: time.Sunday,
}
assert.True(t, cond.Matches(ctxSaturday))
assert.True(t, cond.Matches(ctxSunday))

ctxMonday := &AuthzContext{
DayOfWeek: time.Monday,
}
assert.False(t, cond.Matches(ctxMonday))
})

t.Run("DayOfWeekWeekday", func(t *testing.T) {
cond := Condition{
Type:  ConditionDayOfWeek,
Value: "weekday",
}
ctxMonday := &AuthzContext{
DayOfWeek: time.Monday,
}
assert.True(t, cond.Matches(ctxMonday))

ctxSaturday := &AuthzContext{
DayOfWeek: time.Saturday,
}
assert.False(t, cond.Matches(ctxSaturday))
})
}

func TestRole_IsHighPrivilege(t *testing.T) {
assert.False(t, RoleViewer.IsHighPrivilege())
assert.False(t, RoleOperator.IsHighPrivilege())
assert.True(t, RoleAdmin.IsHighPrivilege())
assert.True(t, RoleSuperAdmin.IsHighPrivilege())
}

func TestRole_RequiresMFA(t *testing.T) {
assert.False(t, RoleViewer.RequiresMFA())
assert.False(t, RoleOperator.RequiresMFA())
assert.False(t, RoleAdmin.RequiresMFA()) // Optional
assert.True(t, RoleSuperAdmin.RequiresMFA()) // Always
}

func TestRole_CanAssignRole(t *testing.T) {
	// Only super-admin can assign roles
	assert.False(t, RoleViewer.CanAssignRole(RoleViewer))
	assert.False(t, RoleOperator.CanAssignRole(RoleOperator))
	assert.False(t, RoleAdmin.CanAssignRole(RoleAdmin))
	assert.True(t, RoleSuperAdmin.CanAssignRole(RoleAdmin))
	assert.True(t, RoleSuperAdmin.CanAssignRole(RoleSuperAdmin))
}

func TestPolicy_HasRequirement(t *testing.T) {
		}
		str := decision.String()
		assert.Contains(t, str, "Allowed")
	})

	t.Run("AllowedWithRequirements", func(t *testing.T) {
		decision := &AuthzDecision{
			Allowed:      true,
			Reason:       "Permission granted",
			Requirements: []Requirement{RequirementMFA},
		}
		str := decision.String()
		assert.Contains(t, str, "Allowed with requirements")
	})

	t.Run("Denied", func(t *testing.T) {
		decision := &AuthzDecision{
			Allowed: false,
			Reason:  "Insufficient permissions",
		}
		str := decision.String()
		assert.Contains(t, str, "Denied")
	})
}

func TestAuthzDecision_IsUnconditional(t *testing.T) {
	t.Run("AllowedWithoutRequirements", func(t *testing.T) {
		decision := &AuthzDecision{
			Allowed:      true,
			Requirements: []Requirement{},
		}
		assert.True(t, decision.IsUnconditional())
	})

	t.Run("AllowedWithRequirements", func(t *testing.T) {
		decision := &AuthzDecision{
			Allowed:      true,
			Requirements: []Requirement{RequirementMFA},
		}
		assert.False(t, decision.IsUnconditional())
	})

	t.Run("Denied", func(t *testing.T) {
		decision := &AuthzDecision{
			Allowed: false,
		}
		assert.False(t, decision.IsUnconditional())
	})
}

func TestAuthzDecision_HasRequirement(t *testing.T) {
	decision := &AuthzDecision{
		Allowed: true,
		Requirements: []Requirement{
			RequirementMFA,
			RequirementSignedCommand,
		},
	}

	assert.True(t, decision.HasRequirement(RequirementMFA))
	assert.True(t, decision.HasRequirement(RequirementSignedCommand))
	assert.False(t, decision.HasRequirement(RequirementManagerApproval))
}

func TestAuthzDecision_AllowedWithRequirements(t *testing.T) {
decision := &AuthzDecision{
Allowed:      true,
Requirements: []Requirement{RequirementMFA},
}

// Decision is allowed but has additional requirements
assert.True(t, decision.Allowed)
assert.NotEmpty(t, decision.Requirements)
}

func TestAuthzContext_Complete(t *testing.T) {
authCtx := &auth.AuthContext{
UserID:        "testuser",
Username:      "testuser",
DeviceTrusted: true,
IPAddress:     "192.168.1.100",
}

authzCtx := &AuthzContext{
AuthContext:   authCtx,
Resource:      ResourcePod,
Action:        ActionGet,
Namespace:     "default",
Environment:   EnvProduction,
TimeOfDay:     time.Now(),
DayOfWeek:     time.Monday,
DeviceTrusted: true,
SourceIP:      "192.168.1.100",
RecentActions: []ActionRecord{},
}

assert.NotNil(t, authzCtx.AuthContext)
assert.Equal(t, ResourcePod, authzCtx.Resource)
assert.Equal(t, ActionGet, authzCtx.Action)
assert.Equal(t, "default", authzCtx.Namespace)
assert.Equal(t, EnvProduction, authzCtx.Environment)
}

func TestActionRecord(t *testing.T) {
record := ActionRecord{
Action:    ActionDelete,
Resource:  ResourcePod,
Timestamp: time.Now(),
Success:   true,
}

assert.Equal(t, ActionDelete, record.Action)
assert.Equal(t, ResourcePod, record.Resource)
assert.True(t, record.Success)
}

func TestRequirements(t *testing.T) {
// Test all requirement constants exist
assert.NotEmpty(t, RequirementMFA)
assert.NotEmpty(t, RequirementSignedCommand)
assert.NotEmpty(t, RequirementManagerApproval)
assert.NotEmpty(t, RequirementChangeTicket)
assert.NotEmpty(t, RequirementOnCallConfirm)
assert.NotEmpty(t, RequirementIncidentNumber)
assert.NotEmpty(t, RequirementSecondApprover)
}

func TestConditionTypes(t *testing.T) {
// Test all condition type constants exist
assert.NotEmpty(t, ConditionEnvironment)
assert.NotEmpty(t, ConditionTimeOfDay)
assert.NotEmpty(t, ConditionDayOfWeek)
assert.NotEmpty(t, ConditionDeviceTrust)
}
