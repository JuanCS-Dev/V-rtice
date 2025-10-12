// Package authz - Main Authorizer orchestrator
//
// The Authorizer orchestrates RBAC and Policy engines to make
// comprehensive authorization decisions considering multiple factors.
//
// "What can you do?" - Layer 2 of Guardian Zero Trust Security
package authz

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp/auth"
)

// Authorizer orchestrates all authorization components.
type Authorizer struct {
	rbac         *RBACEngine
	policyEngine *PolicyEngine
}

// AuthorizerConfig configures the authorizer behavior.
type AuthorizerConfig struct {
	// Enable/disable components
	EnableRBAC     bool
	EnablePolicies bool

	// Strictness
	DenyByDefault bool // If true, deny unless explicitly allowed
}

// NewAuthorizer creates a new authorizer with default configuration.
func NewAuthorizer() *Authorizer {
	return &Authorizer{
		rbac:         NewRBACEngine(),
		policyEngine: NewPolicyEngine(),
	}
}

// NewAuthorizerWithConfig creates an authorizer with custom configuration.
func NewAuthorizerWithConfig(config *AuthorizerConfig) (*Authorizer, error) {
	if config == nil {
		return nil, errors.New("config cannot be nil")
	}

	auth := &Authorizer{}

	if config.EnableRBAC {
		auth.rbac = NewRBACEngine()
	}

	if config.EnablePolicies {
		auth.policyEngine = NewPolicyEngine()
	}

	return auth, nil
}

// Authorize performs complete authorization check.
//
// Process:
// 1. Check RBAC permissions
// 2. Evaluate contextual policies
// 3. Combine results
// 4. Return decision
func (a *Authorizer) Authorize(ctx context.Context, authzCtx *AuthzContext) (*AuthzDecision, error) {
	if ctx == nil {
		return nil, errors.New("context cannot be nil")
	}
	if authzCtx == nil {
		return nil, errors.New("authz context cannot be nil")
	}
	if authzCtx.AuthContext == nil {
		return nil, errors.New("auth context is required")
	}

	// Step 1: Check RBAC permissions
	rbacDecision, err := a.rbac.IsAuthorized(
		authzCtx.AuthContext.UserID,
		authzCtx.Resource,
		authzCtx.Action,
		authzCtx.Namespace,
	)
	if err != nil {
		return nil, fmt.Errorf("RBAC check failed: %w", err)
	}

	// If RBAC denies, return immediately (unless policies can override)
	if !rbacDecision.Allowed {
		return rbacDecision, nil
	}

	// Step 2: Evaluate contextual policies
	policyDecision, err := a.policyEngine.EvaluatePolicies(
		authzCtx,
		authzCtx.Resource,
		authzCtx.Action,
	)
	if err != nil {
		return nil, fmt.Errorf("policy evaluation failed: %w", err)
	}

	// Step 3: Check if any policy denies
	if policyDecision.Denied {
		return &AuthzDecision{
			Allowed:         false,
			Reason:          policyDecision.DenyReason,
			MatchedPolicies: getPolicyNames(policyDecision.Policies),
		}, nil
	}

	// Step 4: Combine RBAC and policy requirements
	finalDecision := &AuthzDecision{
		Allowed:         true,
		Reason:          rbacDecision.Reason,
		Requirements:    combineRequirements(rbacDecision.Requirements, policyDecision.Requirements),
		MatchedPolicies: getPolicyNames(policyDecision.Policies),
	}

	// Update reason if there are policy requirements
	if len(policyDecision.Requirements) > 0 {
		finalDecision.Reason += fmt.Sprintf(" (with %d policy requirements)", len(policyDecision.Requirements))
	}

	return finalDecision, nil
}

// CheckPermission is a simplified authorization check.
// Returns whether the user has permission (without policy evaluation).
func (a *Authorizer) CheckPermission(userID string, resource Resource, action Action) (bool, error) {
	if userID == "" {
		return false, errors.New("userID is required")
	}

	allowed, _ := a.rbac.CheckPermission(userID, resource, action, "")
	return allowed, nil
}

// AssignRole assigns a role to a user.
func (a *Authorizer) AssignRole(userID string, role Role) error {
	return a.rbac.AssignRole(userID, role)
}

// RevokeRole removes a role from a user.
func (a *Authorizer) RevokeRole(userID string, role Role) error {
	return a.rbac.RevokeRole(userID, role)
}

// GetUserRoles returns all roles for a user.
func (a *Authorizer) GetUserRoles(userID string) []Role {
	return a.rbac.GetUserRoles(userID)
}

// AddPolicy adds a custom policy.
func (a *Authorizer) AddPolicy(policy *Policy) error {
	return a.policyEngine.AddPolicy(policy)
}

// RemovePolicy removes a policy by name.
func (a *Authorizer) RemovePolicy(name string) error {
	return a.policyEngine.RemovePolicy(name)
}

// BuildAuthzContext builds an authorization context from auth context.
// Helper to simplify context construction.
func (a *Authorizer) BuildAuthzContext(
	authCtx *auth.AuthContext,
	resource Resource,
	action Action,
	namespace string,
	environment Environment,
) *AuthzContext {
	return &AuthzContext{
		AuthContext:   authCtx,
		Resource:      resource,
		Action:        action,
		Namespace:     namespace,
		Environment:   environment,
		TimeOfDay:     time.Now(),
		DayOfWeek:     time.Now().Weekday(),
		DeviceTrusted: authCtx.DeviceTrusted,
		SourceIP:      authCtx.IPAddress,
		RecentActions: []ActionRecord{},
	}
}

// QuickAuthorize performs authorization with minimal context.
// Useful for simple checks where full context isn't available.
func (a *Authorizer) QuickAuthorize(
	authCtx *auth.AuthContext,
	resource Resource,
	action Action,
) (*AuthzDecision, error) {
	ctx := context.Background()
	authzCtx := a.BuildAuthzContext(
		authCtx,
		resource,
		action,
		"default",
		EnvProduction, // Assume production for safety
	)

	return a.Authorize(ctx, authzCtx)
}

// GetRBACEngine returns the RBAC engine (for advanced usage).
func (a *Authorizer) GetRBACEngine() *RBACEngine {
	return a.rbac
}

// GetPolicyEngine returns the policy engine (for advanced usage).
func (a *Authorizer) GetPolicyEngine() *PolicyEngine {
	return a.policyEngine
}

// ExportAuthorizationReport exports a report of all authorization rules.
// Useful for compliance and audit purposes.
func (a *Authorizer) ExportAuthorizationReport() *AuthorizationReport {
	return &AuthorizationReport{
		Roles:    a.rbac.ExportRolePermissions(),
		Policies: a.policyEngine.ListPolicies(),
		UserCount: a.rbac.GetUserCount(),
		PolicyCount: a.policyEngine.GetPolicyCount(),
		GeneratedAt: time.Now(),
	}
}

// AuthorizationReport contains a snapshot of authorization configuration.
type AuthorizationReport struct {
	Roles       map[Role][]Permission
	Policies    []*Policy
	UserCount   int
	PolicyCount int
	GeneratedAt time.Time
}

// Helper functions

func combineRequirements(r1, r2 []Requirement) []Requirement {
	combined := append([]Requirement{}, r1...)
	combined = append(combined, r2...)
	return uniqueRequirements(combined)
}

func getPolicyNames(policies []*Policy) []string {
	names := []string{}
	for _, policy := range policies {
		names = append(names, policy.Name)
	}
	return names
}
