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

// ============================================================================
// NEW TESTS - Coverage Improvement to 90%+
// ============================================================================

func TestNewAuthorizerWithConfig(t *testing.T) {
	t.Run("ValidConfig", func(t *testing.T) {
		config := &AuthorizerConfig{
			EnableRBAC:     true,
			EnablePolicies: true,
			DenyByDefault:  true,
		}
		auth, err := NewAuthorizerWithConfig(config)
		require.NoError(t, err)
		assert.NotNil(t, auth)
		assert.NotNil(t, auth.rbac)
		assert.NotNil(t, auth.policyEngine)
	})

	t.Run("NilConfig", func(t *testing.T) {
		auth, err := NewAuthorizerWithConfig(nil)
		assert.Error(t, err)
		assert.Nil(t, auth)
		assert.Contains(t, err.Error(), "config cannot be nil")
	})

	t.Run("OnlyRBAC", func(t *testing.T) {
		config := &AuthorizerConfig{
			EnableRBAC:     true,
			EnablePolicies: false,
		}
		auth, err := NewAuthorizerWithConfig(config)
		require.NoError(t, err)
		assert.NotNil(t, auth.rbac)
		assert.Nil(t, auth.policyEngine)
	})

	t.Run("OnlyPolicies", func(t *testing.T) {
		config := &AuthorizerConfig{
			EnableRBAC:     false,
			EnablePolicies: true,
		}
		auth, err := NewAuthorizerWithConfig(config)
		require.NoError(t, err)
		assert.Nil(t, auth.rbac)
		assert.NotNil(t, auth.policyEngine)
	})
}

func TestAuthorize_ErrorCases(t *testing.T) {
	authorizer, authCtx := setupAuthorizerTest(t)

	t.Run("NilContext", func(t *testing.T) {
		authzCtx := authorizer.BuildAuthzContext(
			authCtx, ResourcePod, ActionGet, "default", EnvDevelopment,
		)
		decision, err := authorizer.Authorize(nil, authzCtx)
		assert.Error(t, err)
		assert.Nil(t, decision)
		assert.Contains(t, err.Error(), "context cannot be nil")
	})

	t.Run("NilAuthzContext", func(t *testing.T) {
		ctx := context.Background()
		decision, err := authorizer.Authorize(ctx, nil)
		assert.Error(t, err)
		assert.Nil(t, decision)
		assert.Contains(t, err.Error(), "authz context cannot be nil")
	})

	t.Run("NilAuthContext", func(t *testing.T) {
		ctx := context.Background()
		authzCtx := &AuthzContext{
			AuthContext: nil,
			Resource:    ResourcePod,
			Action:      ActionGet,
		}
		decision, err := authorizer.Authorize(ctx, authzCtx)
		assert.Error(t, err)
		assert.Nil(t, decision)
		assert.Contains(t, err.Error(), "auth context is required")
	})
}

func TestCheckPermission(t *testing.T) {
	authorizer, _ := setupAuthorizerTest(t)

	t.Run("WithPermission", func(t *testing.T) {
		authorizer.AssignRole("testuser", RoleViewer)
		allowed, err := authorizer.CheckPermission("testuser", ResourcePod, ActionGet)
		require.NoError(t, err)
		assert.True(t, allowed)
	})

	t.Run("WithoutPermission", func(t *testing.T) {
		authorizer.AssignRole("testuser", RoleViewer)
		allowed, err := authorizer.CheckPermission("testuser", ResourcePod, ActionDelete)
		require.NoError(t, err)
		assert.False(t, allowed)
	})

	t.Run("EmptyUserID", func(t *testing.T) {
		allowed, err := authorizer.CheckPermission("", ResourcePod, ActionGet)
		assert.Error(t, err)
		assert.False(t, allowed)
		assert.Contains(t, err.Error(), "userID is required")
	})
}

func TestRoleManagement(t *testing.T) {
	authorizer, _ := setupAuthorizerTest(t)

	t.Run("AssignRole", func(t *testing.T) {
		err := authorizer.AssignRole("testuser", RoleViewer)
		assert.NoError(t, err)
		
		roles := authorizer.GetUserRoles("testuser")
		assert.Len(t, roles, 1)
		assert.Equal(t, RoleViewer, roles[0])
	})

	t.Run("RevokeRole", func(t *testing.T) {
		authorizer.AssignRole("testuser", RoleViewer)
		authorizer.AssignRole("testuser", RoleOperator)
		
		err := authorizer.RevokeRole("testuser", RoleViewer)
		assert.NoError(t, err)
		
		roles := authorizer.GetUserRoles("testuser")
		assert.Len(t, roles, 1)
		assert.Equal(t, RoleOperator, roles[0])
	})

	t.Run("GetUserRoles_NoRoles", func(t *testing.T) {
		roles := authorizer.GetUserRoles("newuser")
		assert.Empty(t, roles)
	})
}

func TestPolicyManagement(t *testing.T) {
	authorizer, _ := setupAuthorizerTest(t)

	t.Run("AddPolicy", func(t *testing.T) {
		policy := &Policy{
			Name:        "test-policy",
			Description: "Test policy",
			Conditions:  []Condition{{Type: ConditionEnvironment, Value: "test"}},
			Requirements: []Requirement{RequirementMFA},
		}
		
		err := authorizer.AddPolicy(policy)
		assert.NoError(t, err)
		
		// Verify policy was added
		engine := authorizer.GetPolicyEngine()
		retrievedPolicy, err := engine.GetPolicy("test-policy")
		require.NoError(t, err)
		assert.Equal(t, "test-policy", retrievedPolicy.Name)
	})

	t.Run("RemovePolicy", func(t *testing.T) {
		policy := &Policy{
			Name:        "temp-policy",
			Description: "Temporary test policy",
		}
		authorizer.AddPolicy(policy)
		
		err := authorizer.RemovePolicy("temp-policy")
		assert.NoError(t, err)
		
		// Verify policy was removed
		engine := authorizer.GetPolicyEngine()
		_, err = engine.GetPolicy("temp-policy")
		assert.Error(t, err)
	})
}

func TestGetEngines(t *testing.T) {
	authorizer, _ := setupAuthorizerTest(t)

	t.Run("GetRBACEngine", func(t *testing.T) {
		rbac := authorizer.GetRBACEngine()
		assert.NotNil(t, rbac)
		assert.IsType(t, &RBACEngine{}, rbac)
	})

	t.Run("GetPolicyEngine", func(t *testing.T) {
		policyEngine := authorizer.GetPolicyEngine()
		assert.NotNil(t, policyEngine)
		assert.IsType(t, &PolicyEngine{}, policyEngine)
	})
}

func TestAuthorize_PolicyDenial(t *testing.T) {
	authorizer, authCtx := setupAuthorizerTest(t)
	authorizer.AssignRole("testuser", RoleAdmin)

	// Add a deny policy
	denyPolicy := &Policy{
		Name:          "test-deny-policy",
		Description:   "Test deny policy",
		IsDenyPolicy:  true,
		Conditions: []Condition{
			{Type: ConditionEnvironment, Value: string(EnvDevelopment)},
		},
	}
	authorizer.AddPolicy(denyPolicy)

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
	assert.Contains(t, decision.MatchedPolicies, "test-deny-policy")
}

func TestAuthorize_SecretAccess(t *testing.T) {
	authorizer, authCtx := setupAuthorizerTest(t)
	authorizer.AssignRole("testuser", RoleAdmin)

	ctx := context.Background()
	authzCtx := authorizer.BuildAuthzContext(
		authCtx,
		ResourceSecret, // Secret resource
		ActionGet,
		"default",
		EnvDevelopment,
	)

	decision, err := authorizer.Authorize(ctx, authzCtx)
	require.NoError(t, err)
	assert.True(t, decision.Allowed)
	assert.Contains(t, decision.Requirements, RequirementMFA)
	assert.Contains(t, decision.Requirements, RequirementSignedCommand)
	assert.Contains(t, decision.MatchedPolicies, "secret-access-policy")
}

func TestAuthorize_PolicyRequirements(t *testing.T) {
	authorizer, authCtx := setupAuthorizerTest(t)
	authorizer.AssignRole("testuser", RoleAdmin)
	authCtx.DeviceTrusted = false // Untrusted device

	// Add untrusted device policy
	ctx := context.Background()
	authzCtx := &AuthzContext{
		AuthContext:   authCtx,
		Resource:      ResourcePod,
		Action:        ActionDelete,
		Namespace:     "default",
		Environment:   EnvDevelopment,
		DeviceTrusted: false,
	}

	decision, err := authorizer.Authorize(ctx, authzCtx)
	require.NoError(t, err)
	assert.True(t, decision.Allowed)
	// Should have MFA requirement from untrusted device policy
	assert.Contains(t, decision.Requirements, RequirementMFA)
}
