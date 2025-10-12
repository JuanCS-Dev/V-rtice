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
