package authz

import (
"testing"
"time"

"github.com/stretchr/testify/assert"
"github.com/verticedev/vcli-go/pkg/nlp/auth"
)

func TestPermission_HasNamespace(t *testing.T) {
perm := Permission{
Resource:   ResourcePod,
Actions:    []Action{ActionGet},
Namespaces: []string{},
}
assert.True(t, perm.HasNamespace("any-namespace"))

perm2 := Permission{
Resource:   ResourcePod,
Actions:    []Action{ActionGet},
Namespaces: []string{"production"},
}
assert.True(t, perm2.HasNamespace("production"))
assert.False(t, perm2.HasNamespace("dev"))
}

func TestPermission_IsReadOnly(t *testing.T) {
perm := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionGet, ActionList},
}
assert.True(t, perm.IsReadOnly())

perm2 := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionGet, ActionCreate},
}
assert.False(t, perm2.IsReadOnly())
}

func TestPermission_IsDangerous(t *testing.T) {
perm := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionGet, ActionList},
}
assert.False(t, perm.IsDangerous())

perm2 := Permission{
Resource: ResourcePod,
Actions:  []Action{ActionDelete},
}
assert.True(t, perm2.IsDangerous())
}

func TestCondition_Matches(t *testing.T) {
cond := Condition{
Type:  ConditionEnvironment,
Value: string(EnvProduction),
}
ctx := &AuthzContext{
Environment: EnvProduction,
}
assert.True(t, cond.Matches(ctx))

ctx2 := &AuthzContext{
Environment: EnvDevelopment,
}
assert.False(t, cond.Matches(ctx2))
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
assert.False(t, RoleAdmin.RequiresMFA())
assert.True(t, RoleSuperAdmin.RequiresMFA())
}

func TestRole_CanAssignRole(t *testing.T) {
assert.False(t, RoleViewer.CanAssignRole(RoleViewer))
assert.False(t, RoleOperator.CanAssignRole(RoleOperator))
assert.False(t, RoleAdmin.CanAssignRole(RoleAdmin))
assert.True(t, RoleSuperAdmin.CanAssignRole(RoleAdmin))
}

func TestAuthzDecision_String(t *testing.T) {
decision := &AuthzDecision{
Allowed: true,
Reason:  "OK",
}
str := decision.String()
assert.Contains(t, str, "Allowed")

decision2 := &AuthzDecision{
Allowed: false,
Reason:  "Not allowed",
}
str2 := decision2.String()
assert.Contains(t, str2, "Denied")
}

func TestAuthzDecision_HasRequirement(t *testing.T) {
decision := &AuthzDecision{
Allowed: true,
Requirements: []Requirement{RequirementMFA},
}
assert.True(t, decision.HasRequirement(RequirementMFA))
assert.False(t, decision.HasRequirement(RequirementManagerApproval))
}

func TestAuthzDecision_IsUnconditional(t *testing.T) {
decision := &AuthzDecision{
Allowed:      true,
Requirements: []Requirement{},
}
assert.True(t, decision.IsUnconditional())

decision2 := &AuthzDecision{
Allowed:      true,
Requirements: []Requirement{RequirementMFA},
}
assert.False(t, decision2.IsUnconditional())
}

func TestAuthzContext_Complete(t *testing.T) {
authCtx := &auth.AuthContext{
UserID:        "testuser",
Username:      "testuser",
DeviceTrusted: true,
IPAddress:     "192.168.1.100",
}

authzCtx := &AuthzContext{
AuthContext: authCtx,
Resource:    ResourcePod,
Action:      ActionGet,
Namespace:   "default",
Environment: EnvProduction,
TimeOfDay:   time.Now(),
DayOfWeek:   time.Monday,
}

assert.NotNil(t, authzCtx.AuthContext)
assert.Equal(t, ResourcePod, authzCtx.Resource)
assert.Equal(t, ActionGet, authzCtx.Action)
}

func TestRequirementsAndConditions(t *testing.T) {
assert.NotEmpty(t, RequirementMFA)
assert.NotEmpty(t, RequirementSignedCommand)
assert.NotEmpty(t, ConditionEnvironment)
assert.NotEmpty(t, ConditionTimeOfDay)
}
