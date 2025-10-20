// Package authz - Layer 2: Authorization
//
// Implements role-based access control (RBAC) for NLP commands
package authz

import (
	"context"
	"fmt"
)

// AuthzLayer handles authorization decisions
type AuthzLayer interface {
	// Authorize checks if user has permission to execute command
	Authorize(ctx context.Context, userID string, roles []string, action string, resource string) (*AuthzDecision, error)
}

// AuthzDecision represents authorization result
type AuthzDecision struct {
	Allowed bool
	Reason  string
	Role    string // Role that granted permission
}

// Permission represents a role-action-resource mapping
type Permission struct {
	Role     string
	Action   string   // read, write, delete, execute
	Resource string   // pods, services, configmaps, *
	Scopes   []string // namespace restrictions
}

type authzLayer struct {
	permissions map[string][]Permission // role -> permissions
}

// NewAuthzLayer creates authorization layer
func NewAuthzLayer() AuthzLayer {
	return &authzLayer{
		permissions: initDefaultPermissions(),
	}
}

// Authorize implements AuthzLayer
func (a *authzLayer) Authorize(ctx context.Context, userID string, roles []string, action string, resource string) (*AuthzDecision, error) {
	// Check each role
	for _, role := range roles {
		perms, exists := a.permissions[role]
		if !exists {
			continue
		}

		for _, perm := range perms {
			// Check action match
			if perm.Action != "*" && perm.Action != action {
				continue
			}

			// Check resource match
			if perm.Resource != "*" && perm.Resource != resource {
				continue
			}

			return &AuthzDecision{
				Allowed: true,
				Reason:  fmt.Sprintf("Granted by role: %s", role),
				Role:    role,
			}, nil
		}
	}

	return &AuthzDecision{
		Allowed: false,
		Reason:  fmt.Sprintf("No permission for action '%s' on resource '%s'", action, resource),
	}, nil
}

// initDefaultPermissions sets up RBAC
func initDefaultPermissions() map[string][]Permission {
	return map[string][]Permission{
		"admin": {
			{Role: "admin", Action: "*", Resource: "*"},
		},
		"operator": {
			{Role: "operator", Action: "read", Resource: "*"},
			{Role: "operator", Action: "write", Resource: "pods"},
			{Role: "operator", Action: "write", Resource: "services"},
			{Role: "operator", Action: "execute", Resource: "deployments"},
		},
		"viewer": {
			{Role: "viewer", Action: "read", Resource: "*"},
		},
	}
}

