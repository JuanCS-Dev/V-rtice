package authz

import (
	"context"
	"sync"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewAuthzLayer(t *testing.T) {
	t.Run("creates layer with default permissions", func(t *testing.T) {
		layer := NewAuthzLayer()
		assert.NotNil(t, layer)

		// Verify layer is usable
		ctx := context.Background()
		decision, err := layer.Authorize(ctx, "user1", []string{"admin"}, "read", "pods")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
	})

	t.Run("initializes default permissions correctly", func(t *testing.T) {
		layer := NewAuthzLayer().(*authzLayer)

		// Verify all default roles exist
		assert.Contains(t, layer.permissions, "admin")
		assert.Contains(t, layer.permissions, "operator")
		assert.Contains(t, layer.permissions, "viewer")

		// Verify admin has wildcard permissions
		adminPerms := layer.permissions["admin"]
		assert.Len(t, adminPerms, 1)
		assert.Equal(t, "*", adminPerms[0].Action)
		assert.Equal(t, "*", adminPerms[0].Resource)
	})
}

func TestAuthzLayer_Authorize_AdminRole(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("admin can perform any action on any resource", func(t *testing.T) {
		testCases := []struct {
			action   string
			resource string
		}{
			{"read", "pods"},
			{"write", "deployments"},
			{"delete", "services"},
			{"execute", "jobs"},
			{"create", "configmaps"},
			{"*", "*"},
		}

		for _, tc := range testCases {
			decision, err := layer.Authorize(ctx, "admin-user", []string{"admin"}, tc.action, tc.resource)
			require.NoError(t, err)
			assert.True(t, decision.Allowed, "admin should be allowed %s on %s", tc.action, tc.resource)
			assert.Equal(t, "admin", decision.Role)
			assert.Contains(t, decision.Reason, "admin")
		}
	})

	t.Run("admin with multiple roles still grants access", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"viewer", "admin", "operator"}, "delete", "everything")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "admin", decision.Role)
	})
}

func TestAuthzLayer_Authorize_OperatorRole(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("operator can read any resource", func(t *testing.T) {
		resources := []string{"pods", "services", "deployments", "configmaps", "secrets"}

		for _, resource := range resources {
			decision, err := layer.Authorize(ctx, "operator-user", []string{"operator"}, "read", resource)
			require.NoError(t, err)
			assert.True(t, decision.Allowed, "operator should read %s", resource)
			assert.Equal(t, "operator", decision.Role)
		}
	})

	t.Run("operator can write pods", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "operator-user", []string{"operator"}, "write", "pods")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "operator", decision.Role)
	})

	t.Run("operator can write services", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "operator-user", []string{"operator"}, "write", "services")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "operator", decision.Role)
	})

	t.Run("operator can execute deployments", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "operator-user", []string{"operator"}, "execute", "deployments")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "operator", decision.Role)
	})

	t.Run("operator cannot delete pods", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "operator-user", []string{"operator"}, "delete", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
		assert.Contains(t, decision.Reason, "No permission")
		assert.Contains(t, decision.Reason, "delete")
	})

	t.Run("operator cannot write deployments", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "operator-user", []string{"operator"}, "write", "deployments")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
		assert.Contains(t, decision.Reason, "No permission")
	})

	t.Run("operator cannot write configmaps", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "operator-user", []string{"operator"}, "write", "configmaps")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
	})
}

func TestAuthzLayer_Authorize_ViewerRole(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("viewer can read any resource", func(t *testing.T) {
		resources := []string{"pods", "services", "deployments", "configmaps", "secrets", "nodes"}

		for _, resource := range resources {
			decision, err := layer.Authorize(ctx, "viewer-user", []string{"viewer"}, "read", resource)
			require.NoError(t, err)
			assert.True(t, decision.Allowed, "viewer should read %s", resource)
			assert.Equal(t, "viewer", decision.Role)
			assert.Contains(t, decision.Reason, "viewer")
		}
	})

	t.Run("viewer cannot write any resource", func(t *testing.T) {
		resources := []string{"pods", "services", "deployments"}

		for _, resource := range resources {
			decision, err := layer.Authorize(ctx, "viewer-user", []string{"viewer"}, "write", resource)
			require.NoError(t, err)
			assert.False(t, decision.Allowed, "viewer should not write %s", resource)
			assert.Contains(t, decision.Reason, "No permission")
		}
	})

	t.Run("viewer cannot delete any resource", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "viewer-user", []string{"viewer"}, "delete", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
	})

	t.Run("viewer cannot execute commands", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "viewer-user", []string{"viewer"}, "execute", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
	})
}

func TestAuthzLayer_Authorize_MultipleRoles(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("grants access if any role permits", func(t *testing.T) {
		// User has both viewer and operator roles
		decision, err := layer.Authorize(ctx, "user", []string{"viewer", "operator"}, "write", "pods")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "operator", decision.Role) // operator role granted permission
	})

	t.Run("denies if no role permits", func(t *testing.T) {
		// User has only viewer role
		decision, err := layer.Authorize(ctx, "user", []string{"viewer"}, "delete", "deployments")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
	})

	t.Run("first matching role is returned", func(t *testing.T) {
		// Both viewer and operator can read
		decision, err := layer.Authorize(ctx, "user", []string{"viewer", "operator"}, "read", "pods")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "viewer", decision.Role) // viewer is first in list
	})
}

func TestAuthzLayer_Authorize_NoRoles(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("denies access with empty role list", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{}, "read", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
		assert.Contains(t, decision.Reason, "No permission")
	})

	t.Run("denies access with nil role list", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", nil, "read", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
	})
}

func TestAuthzLayer_Authorize_UnknownRole(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("denies access for unknown role", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"unknown-role"}, "read", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
		assert.Contains(t, decision.Reason, "No permission")
	})

	t.Run("denies access for invalid role", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"hacker"}, "delete", "*")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
	})

	t.Run("grants access if one role is valid", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"unknown", "viewer"}, "read", "pods")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "viewer", decision.Role)
	})
}

func TestAuthzLayer_Authorize_WildcardMatching(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("wildcard action matches any action", func(t *testing.T) {
		// Admin has * action
		decision, err := layer.Authorize(ctx, "user", []string{"admin"}, "custom-action", "resource")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
	})

	t.Run("wildcard resource matches any resource", func(t *testing.T) {
		// Admin has * resource
		decision, err := layer.Authorize(ctx, "user", []string{"admin"}, "action", "custom-resource")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
	})

	t.Run("specific action does not match wildcard request", func(t *testing.T) {
		// Viewer has read action, requesting *
		decision, err := layer.Authorize(ctx, "user", []string{"viewer"}, "*", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
	})
}

func TestAuthzLayer_Authorize_CaseSensitivity(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("roles are case-sensitive", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"Admin"}, "read", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed) // "Admin" != "admin"
	})

	t.Run("actions are case-sensitive", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"operator"}, "Read", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed) // "Read" != "read"
	})

	t.Run("resources are case-sensitive", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"operator"}, "write", "Pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed) // "Pods" != "pods"
	})
}

func TestAuthzLayer_Authorize_ConcurrentAccess(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("thread-safe concurrent authorization checks", func(t *testing.T) {
		var wg sync.WaitGroup
		numGoroutines := 50
		checksPerGoroutine := 20

		for i := 0; i < numGoroutines; i++ {
			wg.Add(1)
			go func(id int) {
				defer wg.Done()
				for j := 0; j < checksPerGoroutine; j++ {
					roles := []string{"viewer", "operator", "admin"}
					role := roles[j%3]
					layer.Authorize(ctx, "user", []string{role}, "read", "pods")
				}
			}(i)
		}

		wg.Wait()
	})
}

func TestAuthzLayer_Authorize_EdgeCases(t *testing.T) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	t.Run("empty action string", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"admin"}, "", "pods")
		require.NoError(t, err)
		assert.True(t, decision.Allowed) // admin wildcard matches empty action
	})

	t.Run("empty resource string", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"admin"}, "read", "")
		require.NoError(t, err)
		assert.True(t, decision.Allowed) // admin wildcard matches empty resource
	})

	t.Run("empty user ID", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "", []string{"viewer"}, "read", "pods")
		require.NoError(t, err)
		assert.True(t, decision.Allowed) // userID not used in authorization logic
	})

	t.Run("special characters in resource name", func(t *testing.T) {
		decision, err := layer.Authorize(ctx, "user", []string{"admin"}, "read", "pod/nginx-deployment-abc123")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
	})
}

func TestAuthzDecision_Structure(t *testing.T) {
	t.Run("decision contains all required fields", func(t *testing.T) {
		decision := &AuthzDecision{
			Allowed: true,
			Reason:  "test reason",
			Role:    "test-role",
		}

		assert.True(t, decision.Allowed)
		assert.Equal(t, "test reason", decision.Reason)
		assert.Equal(t, "test-role", decision.Role)
	})

	t.Run("denied decision has empty role", func(t *testing.T) {
		layer := NewAuthzLayer()
		ctx := context.Background()

		decision, err := layer.Authorize(ctx, "user", []string{"viewer"}, "delete", "pods")
		require.NoError(t, err)

		assert.False(t, decision.Allowed)
		assert.Empty(t, decision.Role) // No role granted permission
		assert.NotEmpty(t, decision.Reason)
	})
}

func TestPermission_Structure(t *testing.T) {
	t.Run("default permissions have expected structure", func(t *testing.T) {
		perms := initDefaultPermissions()

		// Test admin permissions
		assert.Len(t, perms["admin"], 1)
		assert.Equal(t, "admin", perms["admin"][0].Role)
		assert.Equal(t, "*", perms["admin"][0].Action)
		assert.Equal(t, "*", perms["admin"][0].Resource)

		// Test operator permissions
		assert.Len(t, perms["operator"], 4)
		operatorPerms := perms["operator"]

		// Verify operator can read all
		readPerm := operatorPerms[0]
		assert.Equal(t, "operator", readPerm.Role)
		assert.Equal(t, "read", readPerm.Action)
		assert.Equal(t, "*", readPerm.Resource)

		// Test viewer permissions
		assert.Len(t, perms["viewer"], 1)
		assert.Equal(t, "viewer", perms["viewer"][0].Role)
		assert.Equal(t, "read", perms["viewer"][0].Action)
		assert.Equal(t, "*", perms["viewer"][0].Resource)
	})
}

func TestAuthzLayer_Integration(t *testing.T) {
	t.Run("realistic RBAC scenario", func(t *testing.T) {
		layer := NewAuthzLayer()
		ctx := context.Background()

		// Admin performs dangerous operation
		decision, err := layer.Authorize(ctx, "admin-user", []string{"admin"}, "delete", "deployment/production")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "admin", decision.Role)

		// Operator reads pod logs
		decision, err = layer.Authorize(ctx, "ops-user", []string{"operator"}, "read", "pods/logs")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)

		// Operator restarts pods
		decision, err = layer.Authorize(ctx, "ops-user", []string{"operator"}, "write", "pods")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)

		// Operator tries to delete deployment (denied)
		decision, err = layer.Authorize(ctx, "ops-user", []string{"operator"}, "delete", "deployment/app")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
		assert.Contains(t, decision.Reason, "No permission")

		// Viewer reads cluster state
		decision, err = layer.Authorize(ctx, "viewer-user", []string{"viewer"}, "read", "nodes")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)

		// Viewer tries to modify (denied)
		decision, err = layer.Authorize(ctx, "viewer-user", []string{"viewer"}, "write", "configmap")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)

		// User with no roles (denied)
		decision, err = layer.Authorize(ctx, "anonymous", []string{}, "read", "secrets")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)
	})

	t.Run("role escalation scenario", func(t *testing.T) {
		layer := NewAuthzLayer()
		ctx := context.Background()

		// User starts as viewer
		decision, err := layer.Authorize(ctx, "user1", []string{"viewer"}, "delete", "pods")
		require.NoError(t, err)
		assert.False(t, decision.Allowed)

		// User gets promoted to operator
		decision, err = layer.Authorize(ctx, "user1", []string{"viewer", "operator"}, "write", "pods")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "operator", decision.Role)

		// User gets promoted to admin
		decision, err = layer.Authorize(ctx, "user1", []string{"admin"}, "delete", "*")
		require.NoError(t, err)
		assert.True(t, decision.Allowed)
		assert.Equal(t, "admin", decision.Role)
	})
}

func BenchmarkAuthzLayer_Authorize(b *testing.B) {
	layer := NewAuthzLayer()
	ctx := context.Background()

	b.Run("admin authorization", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			layer.Authorize(ctx, "user", []string{"admin"}, "read", "pods")
		}
	})

	b.Run("viewer authorization", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			layer.Authorize(ctx, "user", []string{"viewer"}, "read", "pods")
		}
	})

	b.Run("denied authorization", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			layer.Authorize(ctx, "user", []string{"viewer"}, "delete", "pods")
		}
	})

	b.Run("multiple roles", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			layer.Authorize(ctx, "user", []string{"viewer", "operator", "admin"}, "write", "services")
		}
	})
}
