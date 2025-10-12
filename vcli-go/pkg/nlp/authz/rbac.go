// Package authz - RBAC (Role-Based Access Control) Engine
//
// Implements role-based authorization with predefined role hierarchies
// and permission sets aligned with Kubernetes RBAC principles.
package authz

import (
	"errors"
	"fmt"
)

// RBACEngine manages role-based access control.
type RBACEngine struct {
	rolePermissions map[Role][]Permission
	userRoles       map[string][]Role // userID -> roles
}

// NewRBACEngine creates a new RBAC engine with default role configurations.
func NewRBACEngine() *RBACEngine {
	engine := &RBACEngine{
		rolePermissions: make(map[Role][]Permission),
		userRoles:       make(map[string][]Role),
	}

	// Initialize default role permissions
	engine.initializeDefaultRoles()

	return engine
}

// initializeDefaultRoles sets up the standard role hierarchy.
func (r *RBACEngine) initializeDefaultRoles() {
	// Viewer: Read-only access
	r.rolePermissions[RoleViewer] = []Permission{
		{
			Resource: ResourcePod,
			Actions:  []Action{ActionGet, ActionList, ActionDescribe, ActionWatch},
		},
		{
			Resource: ResourceDeployment,
			Actions:  []Action{ActionGet, ActionList, ActionDescribe},
		},
		{
			Resource: ResourceService,
			Actions:  []Action{ActionGet, ActionList, ActionDescribe},
		},
		{
			Resource: ResourceConfigMap,
			Actions:  []Action{ActionGet, ActionList},
		},
		// Viewer CANNOT access secrets
	}

	// Operator: Viewer + operational commands
	r.rolePermissions[RoleOperator] = append(
		r.rolePermissions[RoleViewer],
		Permission{
			Resource: ResourcePod,
			Actions:  []Action{ActionRestart, ActionScale},
		},
		Permission{
			Resource: ResourceDeployment,
			Actions:  []Action{ActionScale, ActionRestart, ActionUpdate},
		},
		Permission{
			Resource: ResourceService,
			Actions:  []Action{ActionUpdate},
		},
	)

	// Admin: Operator + create/delete with confirmation
	r.rolePermissions[RoleAdmin] = append(
		r.rolePermissions[RoleOperator],
		Permission{
			Resource:             ResourcePod,
			Actions:              []Action{ActionCreate, ActionDelete, ActionExecute},
			RequiresConfirmation: true,
		},
		Permission{
			Resource:             ResourceDeployment,
			Actions:              []Action{ActionCreate, ActionDelete},
			RequiresConfirmation: true,
		},
		Permission{
			Resource:             ResourceService,
			Actions:              []Action{ActionCreate, ActionDelete},
			RequiresConfirmation: true,
		},
		Permission{
			Resource: ResourceSecret,
			Actions:  []Action{ActionGet, ActionList}, // Admin can READ secrets
		},
		Permission{
			Resource:             ResourceNamespace,
			Actions:              []Action{ActionCreate, ActionDelete},
			RequiresConfirmation: true,
		},
	)

	// Super-Admin: Full unrestricted access
	r.rolePermissions[RoleSuperAdmin] = append(
		r.rolePermissions[RoleAdmin],
		Permission{
			Resource: ResourceSecret,
			Actions:  []Action{ActionCreate, ActionUpdate, ActionDelete}, // Full secret access
		},
		Permission{
			Resource: ResourceNode,
			Actions:  []Action{ActionGet, ActionList, ActionUpdate, ActionDelete},
		},
		Permission{
			Resource: ResourceCluster,
			Actions:  []Action{ActionGet, ActionUpdate, ActionDelete},
		},
		Permission{
			Resource: ResourcePod,
			Actions:  []Action{ActionDebug, ActionProxy}, // Advanced debugging
		},
	)
}

// AssignRole assigns a role to a user.
func (r *RBACEngine) AssignRole(userID string, role Role) error {
	if userID == "" {
		return errors.New("userID cannot be empty")
	}

	// Validate role exists
	if _, exists := r.rolePermissions[role]; !exists {
		return fmt.Errorf("invalid role: %s", role)
	}

	// Add role if not already assigned
	if !r.hasRole(userID, role) {
		r.userRoles[userID] = append(r.userRoles[userID], role)
	}

	return nil
}

// RevokeRole removes a role from a user.
func (r *RBACEngine) RevokeRole(userID string, role Role) error {
	if userID == "" {
		return errors.New("userID cannot be empty")
	}

	roles := r.userRoles[userID]
	newRoles := []Role{}

	for _, r := range roles {
		if r != role {
			newRoles = append(newRoles, r)
		}
	}

	r.userRoles[userID] = newRoles
	return nil
}

// GetUserRoles returns all roles assigned to a user.
func (r *RBACEngine) GetUserRoles(userID string) []Role {
	return r.userRoles[userID]
}

// GetRolePermissions returns all permissions for a role.
func (r *RBACEngine) GetRolePermissions(role Role) []Permission {
	return r.rolePermissions[role]
}

// CheckPermission checks if a user has permission for an action on a resource.
func (r *RBACEngine) CheckPermission(userID string, resource Resource, action Action, namespace string) (bool, *Permission) {
	roles := r.GetUserRoles(userID)

	// Check each role
	for _, role := range roles {
		permissions := r.GetRolePermissions(role)

		for _, perm := range permissions {
			// Check if resource matches
			if perm.Resource != resource {
				continue
			}

			// Check if action is allowed
			if !perm.HasAction(action) {
				continue
			}

			// Check if namespace is allowed
			if !perm.HasNamespace(namespace) {
				continue
			}

			// Permission found
			return true, &perm
		}
	}

	return false, nil
}

// GetHighestRole returns the highest privilege role for a user.
func (r *RBACEngine) GetHighestRole(userID string) Role {
	roles := r.GetUserRoles(userID)

	roleHierarchy := map[Role]int{
		RoleViewer:     1,
		RoleOperator:   2,
		RoleAdmin:      3,
		RoleSuperAdmin: 4,
	}

	highestRole := RoleViewer
	highestLevel := 0

	for _, role := range roles {
		if level := roleHierarchy[role]; level > highestLevel {
			highestLevel = level
			highestRole = role
		}
	}

	return highestRole
}

// HasRole checks if a user has a specific role.
func (r *RBACEngine) hasRole(userID string, role Role) bool {
	roles := r.userRoles[userID]
	for _, r := range roles {
		if r == role {
			return true
		}
	}
	return false
}

// HasAnyRole checks if a user has any of the specified roles.
func (r *RBACEngine) HasAnyRole(userID string, roles ...Role) bool {
	userRoles := r.GetUserRoles(userID)
	for _, userRole := range userRoles {
		for _, role := range roles {
			if userRole == role {
				return true
			}
		}
	}
	return false
}

// IsAuthorized performs a complete authorization check.
// Returns whether authorized and the permission that granted it.
func (r *RBACEngine) IsAuthorized(userID string, resource Resource, action Action, namespace string) (*AuthzDecision, error) {
	if userID == "" {
		return &AuthzDecision{
			Allowed: false,
			Reason:  "userID is required",
		}, nil
	}

	// Check permission
	allowed, perm := r.CheckPermission(userID, resource, action, namespace)

	if !allowed {
		// Get user's highest role for better error message
		highestRole := r.GetHighestRole(userID)

		return &AuthzDecision{
			Allowed: false,
			Reason: fmt.Sprintf("Role '%s' does not have permission for action '%s' on resource '%s'",
				highestRole, action, resource),
			Suggestions: r.getSuggestions(highestRole, action, resource),
		}, nil
	}

	// Permission granted
	decision := &AuthzDecision{
		Allowed: true,
		Reason: fmt.Sprintf("Permission granted by role-based access control"),
	}

	// Add requirements if permission needs confirmation
	if perm.RequiresConfirmation {
		decision.Requirements = []Requirement{RequirementSignedCommand}
		decision.Reason += " (requires confirmation)"
	}

	return decision, nil
}

// getSuggestions provides helpful suggestions when access is denied.
func (r *RBACEngine) getSuggestions(currentRole Role, action Action, resource Resource) []string {
	suggestions := []string{}

	// Suggest role upgrade if needed
	if currentRole == RoleViewer {
		if action == ActionDelete || action == ActionCreate {
			suggestions = append(suggestions, "This action requires 'admin' role or higher")
		} else if action == ActionRestart || action == ActionScale {
			suggestions = append(suggestions, "This action requires 'operator' role or higher")
		}
	} else if currentRole == RoleOperator {
		if action == ActionDelete || action == ActionCreate {
			suggestions = append(suggestions, "This action requires 'admin' role or higher")
		}
	}

	// Suggest alternative actions
	if action == ActionDelete {
		suggestions = append(suggestions, "Consider using 'scale to 0' instead of delete")
	}

	return suggestions
}

// AddCustomPermission adds a custom permission to a role.
// Use with caution - modifies role definitions at runtime.
func (r *RBACEngine) AddCustomPermission(role Role, permission Permission) error {
	if _, exists := r.rolePermissions[role]; !exists {
		return fmt.Errorf("role does not exist: %s", role)
	}

	r.rolePermissions[role] = append(r.rolePermissions[role], permission)
	return nil
}

// RemoveCustomPermission removes a custom permission from a role.
func (r *RBACEngine) RemoveCustomPermission(role Role, resource Resource) error {
	if _, exists := r.rolePermissions[role]; !exists {
		return fmt.Errorf("role does not exist: %s", role)
	}

	permissions := r.rolePermissions[role]
	newPermissions := []Permission{}

	for _, perm := range permissions {
		if perm.Resource != resource {
			newPermissions = append(newPermissions, perm)
		}
	}

	r.rolePermissions[role] = newPermissions
	return nil
}

// ListAllRoles returns all available roles.
func (r *RBACEngine) ListAllRoles() []Role {
	roles := []Role{}
	for role := range r.rolePermissions {
		roles = append(roles, role)
	}
	return roles
}

// GetUserCount returns the number of users with roles assigned.
func (r *RBACEngine) GetUserCount() int {
	return len(r.userRoles)
}

// ExportRolePermissions exports role permissions for audit/documentation.
func (r *RBACEngine) ExportRolePermissions() map[Role][]Permission {
	// Return a copy to prevent external modifications
	exported := make(map[Role][]Permission)
	for role, perms := range r.rolePermissions {
		exported[role] = append([]Permission{}, perms...)
	}
	return exported
}
