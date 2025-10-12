package authz

import (
"context"
"testing"

"github.com/stretchr/testify/assert"
"github.com/stretchr/testify/require"
"github.com/verticedev/vcli-go/pkg/nlp/auth"
)

func setupAuthorizerTest(t *testing.T) (*Authorizer, *auth.AuthContext) {
authorizer := NewAuthorizer()

authCtx := &auth.AuthContext{
UserID:        "testuser",
Username:      "testuser",
Verified:      true,
DeviceTrusted: true,
IPAddress:     "192.168.1.100",
}

return authorizer, authCtx
}

func TestNewAuthorizer(t *testing.T) {
auth := NewAuthorizer()
assert.NotNil(t, auth)
assert.NotNil(t, auth.rbac)
assert.NotNil(t, auth.policyEngine)
}

func TestAuthorize_ViewerCanRead(t *testing.T) {
authorizer, authCtx := setupAuthorizerTest(t)
authorizer.AssignRole("testuser", RoleViewer)

ctx := context.Background()
authzCtx := authorizer.BuildAuthzContext(
authCtx,
ResourcePod,
ActionGet,
"default",
EnvDevelopment,
)

decision, err := authorizer.Authorize(ctx, authzCtx)
require.NoError(t, err)
assert.True(t, decision.Allowed)
}

func TestAuthorize_ViewerCannotDelete(t *testing.T) {
authorizer, authCtx := setupAuthorizerTest(t)
authorizer.AssignRole("testuser", RoleViewer)

ctx := context.Background()
authzCtx := authorizer.BuildAuthzContext(
authCtx,
ResourcePod,
ActionDelete,
"default",
EnvDevelopment,
)

decision, err := authorizer.Authorize(ctx, authzCtx)
require.NoError(t, err)
assert.False(t, decision.Allowed)
}

func TestAuthorize_ProductionRequiresMFA(t *testing.T) {
authorizer, authCtx := setupAuthorizerTest(t)
authorizer.AssignRole("testuser", RoleAdmin)

ctx := context.Background()
authzCtx := authorizer.BuildAuthzContext(
authCtx,
ResourcePod,
ActionDelete,
"default",
EnvProduction, // Production environment
)

decision, err := authorizer.Authorize(ctx, authzCtx)
require.NoError(t, err)

// Should be allowed but with requirements
assert.True(t, decision.Allowed)
assert.NotEmpty(t, decision.Requirements)
assert.Contains(t, decision.MatchedPolicies, "production-delete-restriction")
}

func TestQuickAuthorize(t *testing.T) {
authorizer, authCtx := setupAuthorizerTest(t)
authorizer.AssignRole("testuser", RoleViewer)

decision, err := authorizer.QuickAuthorize(authCtx, ResourcePod, ActionGet)
require.NoError(t, err)
assert.True(t, decision.Allowed)
}

func TestBuildAuthzContext(t *testing.T) {
authorizer, authCtx := setupAuthorizerTest(t)

ctx := authorizer.BuildAuthzContext(
authCtx,
ResourcePod,
ActionGet,
"default",
EnvProduction,
)

assert.NotNil(t, ctx)
assert.Equal(t, ResourcePod, ctx.Resource)
assert.Equal(t, ActionGet, ctx.Action)
assert.Equal(t, EnvProduction, ctx.Environment)
assert.True(t, ctx.DeviceTrusted)
}

func TestExportAuthorizationReport(t *testing.T) {
authorizer, _ := setupAuthorizerTest(t)
authorizer.AssignRole("user1", RoleViewer)
authorizer.AssignRole("user2", RoleAdmin)

report := authorizer.ExportAuthorizationReport()
assert.NotNil(t, report)
assert.NotEmpty(t, report.Roles)
assert.NotEmpty(t, report.Policies)
assert.Equal(t, 2, report.UserCount)
}
