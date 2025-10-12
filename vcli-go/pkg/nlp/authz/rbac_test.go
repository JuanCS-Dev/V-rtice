package authz

import (
"testing"

"github.com/stretchr/testify/assert"
"github.com/stretchr/testify/require"
)

func TestNewRBACEngine(t *testing.T) {
engine := NewRBACEngine()
assert.NotNil(t, engine)
assert.NotEmpty(t, engine.rolePermissions)
}

func TestAssignRole(t *testing.T) {
engine := NewRBACEngine()

err := engine.AssignRole("user1", RoleViewer)
require.NoError(t, err)

roles := engine.GetUserRoles("user1")
assert.Contains(t, roles, RoleViewer)
}

func TestRevokeRole(t *testing.T) {
engine := NewRBACEngine()
engine.AssignRole("user1", RoleViewer)

err := engine.RevokeRole("user1", RoleViewer)
require.NoError(t, err)

roles := engine.GetUserRoles("user1")
assert.NotContains(t, roles, RoleViewer)
}

func TestViewerPermissions(t *testing.T) {
engine := NewRBACEngine()
engine.AssignRole("viewer", RoleViewer)

// Viewer can read pods
allowed, _ := engine.CheckPermission("viewer", ResourcePod, ActionGet, "default")
assert.True(t, allowed)

// Viewer cannot delete pods
allowed, _ = engine.CheckPermission("viewer", ResourcePod, ActionDelete, "default")
assert.False(t, allowed)

// Viewer cannot access secrets
allowed, _ = engine.CheckPermission("viewer", ResourceSecret, ActionGet, "default")
assert.False(t, allowed)
}

func TestAdminPermissions(t *testing.T) {
engine := NewRBACEngine()
engine.AssignRole("admin", RoleAdmin)

// Admin can read
allowed, _ := engine.CheckPermission("admin", ResourcePod, ActionGet, "default")
assert.True(t, allowed)

// Admin can delete (with confirmation)
allowed, perm := engine.CheckPermission("admin", ResourcePod, ActionDelete, "default")
assert.True(t, allowed)
assert.True(t, perm.RequiresConfirmation)

// Admin can read secrets
allowed, _ = engine.CheckPermission("admin", ResourceSecret, ActionGet, "default")
assert.True(t, allowed)
}

func TestSuperAdminPermissions(t *testing.T) {
engine := NewRBACEngine()
engine.AssignRole("superadmin", RoleSuperAdmin)

// Super admin can do everything
allowed, _ := engine.CheckPermission("superadmin", ResourceSecret, ActionDelete, "default")
assert.True(t, allowed)

allowed, _ = engine.CheckPermission("superadmin", ResourceNode, ActionDelete, "default")
assert.True(t, allowed)
}

func TestGetHighestRole(t *testing.T) {
engine := NewRBACEngine()
engine.AssignRole("user1", RoleViewer)
engine.AssignRole("user1", RoleAdmin)

highest := engine.GetHighestRole("user1")
assert.Equal(t, RoleAdmin, highest)
}

func TestIsAuthorized(t *testing.T) {
engine := NewRBACEngine()
engine.AssignRole("viewer", RoleViewer)

// Allowed action
decision, err := engine.IsAuthorized("viewer", ResourcePod, ActionGet, "default")
require.NoError(t, err)
assert.True(t, decision.Allowed)

// Denied action
decision, err = engine.IsAuthorized("viewer", ResourcePod, ActionDelete, "default")
require.NoError(t, err)
assert.False(t, decision.Allowed)
assert.NotEmpty(t, decision.Suggestions)
}

// ============================================================================
// NEW TESTS - Coverage Improvement to 90%+
// ============================================================================

func TestAssignRole_ErrorCases(t *testing.T) {
	engine := NewRBACEngine()

	t.Run("EmptyUserID", func(t *testing.T) {
		err := engine.AssignRole("", RoleViewer)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "userID cannot be empty")
	})

	t.Run("InvalidRole", func(t *testing.T) {
		err := engine.AssignRole("user1", Role("invalid-role"))
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "invalid role")
	})

	t.Run("DuplicateRole", func(t *testing.T) {
		engine.AssignRole("user1", RoleViewer)
		// Assigning same role again should not error
		err := engine.AssignRole("user1", RoleViewer)
		assert.NoError(t, err)
		
		// But user should still have only one instance
		roles := engine.GetUserRoles("user1")
		count := 0
		for _, r := range roles {
			if r == RoleViewer {
				count++
			}
		}
		assert.Equal(t, 1, count)
	})
}

func TestRevokeRole_ErrorCases(t *testing.T) {
	engine := NewRBACEngine()

	t.Run("EmptyUserID", func(t *testing.T) {
		err := engine.RevokeRole("", RoleViewer)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "userID cannot be empty")
	})

	t.Run("RevokeNonExistentRole", func(t *testing.T) {
		engine.AssignRole("user1", RoleViewer)
		err := engine.RevokeRole("user1", RoleAdmin)
		assert.NoError(t, err) // Should not error, just no-op
	})
}

func TestHasAnyRole(t *testing.T) {
	engine := NewRBACEngine()

	t.Run("UserHasOneOfRoles", func(t *testing.T) {
		engine.AssignRole("user1", RoleOperator)
		
		hasAny := engine.HasAnyRole("user1", RoleViewer, RoleOperator, RoleAdmin)
		assert.True(t, hasAny)
	})

	t.Run("UserHasNoneOfRoles", func(t *testing.T) {
		engine.AssignRole("user1", RoleViewer)
		
		hasAny := engine.HasAnyRole("user1", RoleAdmin, RoleSuperAdmin)
		assert.False(t, hasAny)
	})

	t.Run("UserNoRoles", func(t *testing.T) {
		hasAny := engine.HasAnyRole("newuser", RoleViewer, RoleAdmin)
		assert.False(t, hasAny)
	})
}

func TestGetHighestRole_EdgeCases(t *testing.T) {
	engine := NewRBACEngine()

	t.Run("NoRoles", func(t *testing.T) {
		highest := engine.GetHighestRole("newuser")
		assert.Equal(t, RoleViewer, highest) // Default to lowest
	})

	t.Run("SuperAdmin", func(t *testing.T) {
		engine.AssignRole("superuser", RoleViewer)
		engine.AssignRole("superuser", RoleOperator)
		engine.AssignRole("superuser", RoleSuperAdmin)
		
		highest := engine.GetHighestRole("superuser")
		assert.Equal(t, RoleSuperAdmin, highest)
	})
}

func TestIsAuthorized_EmptyUserID(t *testing.T) {
	engine := NewRBACEngine()

	decision, err := engine.IsAuthorized("", ResourcePod, ActionGet, "default")
	assert.NoError(t, err)
	assert.False(t, decision.Allowed)
	assert.Contains(t, decision.Reason, "userID is required")
}

func TestGetSuggestions(t *testing.T) {
	engine := NewRBACEngine()

	t.Run("ViewerTryingDelete", func(t *testing.T) {
		engine.AssignRole("viewer", RoleViewer)
		decision, _ := engine.IsAuthorized("viewer", ResourcePod, ActionDelete, "default")
		
		assert.False(t, decision.Allowed)
		assert.NotEmpty(t, decision.Suggestions)
		// Should suggest admin role
		suggestionsStr := ""
		for _, s := range decision.Suggestions {
			suggestionsStr += s
		}
		assert.Contains(t, suggestionsStr, "admin")
	})

	t.Run("ViewerTryingRestart", func(t *testing.T) {
		engine.AssignRole("viewer", RoleViewer)
		decision, _ := engine.IsAuthorized("viewer", ResourcePod, ActionRestart, "default")
		
		assert.False(t, decision.Allowed)
		assert.NotEmpty(t, decision.Suggestions)
		// Should suggest operator role
		suggestionsStr := ""
		for _, s := range decision.Suggestions {
			suggestionsStr += s
		}
		assert.Contains(t, suggestionsStr, "operator")
	})

	t.Run("OperatorTryingDelete", func(t *testing.T) {
		engine.AssignRole("operator", RoleOperator)
		decision, _ := engine.IsAuthorized("operator", ResourcePod, ActionDelete, "default")
		
		assert.False(t, decision.Allowed)
		assert.NotEmpty(t, decision.Suggestions)
		// Should suggest admin role
		suggestionsStr := ""
		for _, s := range decision.Suggestions {
			suggestionsStr += s
		}
		assert.Contains(t, suggestionsStr, "admin")
	})

	t.Run("DeleteSuggestion", func(t *testing.T) {
		engine.AssignRole("viewer", RoleViewer)
		decision, _ := engine.IsAuthorized("viewer", ResourceDeployment, ActionDelete, "default")
		
		assert.False(t, decision.Allowed)
		// Should suggest scale to 0 as alternative
		suggestionsStr := ""
		for _, s := range decision.Suggestions {
			suggestionsStr += s
		}
		assert.Contains(t, suggestionsStr, "scale to 0")
	})
}

func TestOperatorPermissions(t *testing.T) {
	engine := NewRBACEngine()
	engine.AssignRole("operator", RoleOperator)

	t.Run("CanRead", func(t *testing.T) {
		allowed, _ := engine.CheckPermission("operator", ResourcePod, ActionGet, "default")
		assert.True(t, allowed)
	})

	t.Run("CanRestart", func(t *testing.T) {
		allowed, _ := engine.CheckPermission("operator", ResourcePod, ActionRestart, "default")
		assert.True(t, allowed)
	})

	t.Run("CanScale", func(t *testing.T) {
		allowed, _ := engine.CheckPermission("operator", ResourceDeployment, ActionScale, "default")
		assert.True(t, allowed)
	})

	t.Run("CannotDelete", func(t *testing.T) {
		allowed, _ := engine.CheckPermission("operator", ResourcePod, ActionDelete, "default")
		assert.False(t, allowed)
	})

	t.Run("CannotAccessSecrets", func(t *testing.T) {
		allowed, _ := engine.CheckPermission("operator", ResourceSecret, ActionGet, "default")
		assert.False(t, allowed)
	})
}

func TestCustomPermissions(t *testing.T) {
	engine := NewRBACEngine()

	t.Run("AddCustomPermission", func(t *testing.T) {
		customPerm := Permission{
			Resource: Resource("custom-resource"),
			Actions:  []Action{ActionGet, ActionList},
		}
		
		err := engine.AddCustomPermission(RoleViewer, customPerm)
		assert.NoError(t, err)
		
		// Verify permission was added
		perms := engine.GetRolePermissions(RoleViewer)
		found := false
		for _, p := range perms {
			if p.Resource == "custom-resource" {
				found = true
				break
			}
		}
		assert.True(t, found)
	})

	t.Run("AddCustomPermission_InvalidRole", func(t *testing.T) {
		customPerm := Permission{
			Resource: Resource("custom-resource"),
			Actions:  []Action{ActionGet},
		}
		
		err := engine.AddCustomPermission(Role("invalid-role"), customPerm)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "role does not exist")
	})

	t.Run("RemoveCustomPermission", func(t *testing.T) {
		// Add first
		customPerm := Permission{
			Resource: Resource("temp-resource"),
			Actions:  []Action{ActionGet},
		}
		engine.AddCustomPermission(RoleViewer, customPerm)
		
		// Remove
		err := engine.RemoveCustomPermission(RoleViewer, Resource("temp-resource"))
		assert.NoError(t, err)
		
		// Verify it's gone
		perms := engine.GetRolePermissions(RoleViewer)
		for _, p := range perms {
			assert.NotEqual(t, Resource("temp-resource"), p.Resource)
		}
	})

	t.Run("RemoveCustomPermission_InvalidRole", func(t *testing.T) {
		err := engine.RemoveCustomPermission(Role("invalid-role"), ResourcePod)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "role does not exist")
	})
}

func TestListAllRoles(t *testing.T) {
	engine := NewRBACEngine()

	roles := engine.ListAllRoles()
	assert.NotEmpty(t, roles)
	assert.Contains(t, roles, RoleViewer)
	assert.Contains(t, roles, RoleOperator)
	assert.Contains(t, roles, RoleAdmin)
	assert.Contains(t, roles, RoleSuperAdmin)
}

func TestGetUserCount(t *testing.T) {
	engine := NewRBACEngine()

	// Initially no users
	assert.Equal(t, 0, engine.GetUserCount())

	// Add users
	engine.AssignRole("user1", RoleViewer)
	assert.Equal(t, 1, engine.GetUserCount())

	engine.AssignRole("user2", RoleAdmin)
	assert.Equal(t, 2, engine.GetUserCount())

	engine.AssignRole("user3", RoleOperator)
	assert.Equal(t, 3, engine.GetUserCount())
}

func TestExportRolePermissions(t *testing.T) {
	engine := NewRBACEngine()

	exported := engine.ExportRolePermissions()
	assert.NotEmpty(t, exported)

	// Verify all default roles are present
	assert.Contains(t, exported, RoleViewer)
	assert.Contains(t, exported, RoleOperator)
	assert.Contains(t, exported, RoleAdmin)
	assert.Contains(t, exported, RoleSuperAdmin)

	// Verify it's a copy (modifying it doesn't affect engine)
	exported[RoleViewer] = []Permission{}
	enginePerms := engine.GetRolePermissions(RoleViewer)
	assert.NotEmpty(t, enginePerms) // Should still have permissions
}

func TestCheckPermission_Namespace(t *testing.T) {
	engine := NewRBACEngine()
	engine.AssignRole("user1", RoleViewer)

	t.Run("DefaultNamespace", func(t *testing.T) {
		allowed, _ := engine.CheckPermission("user1", ResourcePod, ActionGet, "default")
		assert.True(t, allowed)
	})

	t.Run("OtherNamespace", func(t *testing.T) {
		// Permissions don't restrict by namespace in default config
		allowed, _ := engine.CheckPermission("user1", ResourcePod, ActionGet, "production")
		assert.True(t, allowed)
	})
}

func TestAdminRequiresConfirmation(t *testing.T) {
	engine := NewRBACEngine()
	engine.AssignRole("admin", RoleAdmin)

	// Delete actions require confirmation
	decision, err := engine.IsAuthorized("admin", ResourcePod, ActionDelete, "default")
	require.NoError(t, err)
	assert.True(t, decision.Allowed)
	assert.Contains(t, decision.Requirements, RequirementSignedCommand)
	assert.Contains(t, decision.Reason, "requires confirmation")
}
