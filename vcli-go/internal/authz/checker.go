// Package authz implements authorization checking (Layer 2)
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is CAMADA 2 of the "Guardian of Intent" v2.0:
// "AUTORIZAÇÃO - O que você pode fazer?"
//
// Provides:
// - RBAC (Role-Based Access Control)
// - Context-aware policies (IP, time, state)
// - Permission checking
package authz

import (
	"context"
	"net"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp"
	"github.com/verticedev/vcli-go/pkg/security"
)

// Checker handles authorization checks
type Checker struct {
	roleStore   RoleStore
	policyStore PolicyStore
}

// NewChecker creates a new authorization checker
func NewChecker(roleStore RoleStore, policyStore PolicyStore) *Checker {
	return &Checker{
		roleStore:   roleStore,
		policyStore: policyStore,
	}
}

// RoleStore interface for role persistence
type RoleStore interface {
	GetRole(ctx context.Context, name string) (*security.Role, error)
	GetUserRoles(ctx context.Context, userID string) ([]security.Role, error)
}

// PolicyStore interface for policy persistence
type PolicyStore interface {
	GetPolicies(ctx context.Context) ([]security.Policy, error)
}

// PreCheck performs early authorization check before parsing
//
// This is a lightweight check that can reject obvious violations
// before we invest time in parsing. Checks:
// - User has at least one role
// - Input doesn't contain obvious forbidden patterns
func (c *Checker) PreCheck(ctx context.Context, user *security.User, input string) error {
	if len(user.Roles) == 0 {
		return &security.SecurityError{
			Layer:     "authz",
			Type:      security.ErrorTypeAuthz,
			Message:   "User has no assigned roles",
			Timestamp: time.Now(),
			UserID:    user.ID,
			SessionID: user.SessionID,
		}
	}
	
	// Check for obvious forbidden patterns
	forbidden := []string{
		"delete namespaces production",
		"delete all",
		"rm -rf",
		"kubectl delete --all",
	}
	
	lowerInput := strings.ToLower(input)
	for _, pattern := range forbidden {
		if strings.Contains(lowerInput, pattern) {
			return &security.SecurityError{
				Layer:     "authz",
				Type:      security.ErrorTypeAuthz,
				Message:   "Input contains forbidden pattern",
				Details:   map[string]interface{}{"pattern": pattern},
				Timestamp: time.Now(),
				UserID:    user.ID,
				SessionID: user.SessionID,
			}
		}
	}
	
	return nil
}

// CheckCommand performs full authorization check on a parsed command
//
// This is the main authorization function. It checks:
// 1. User has permission for the resource/verb combination
// 2. Context-aware policies allow the action
// 3. Risk-based restrictions (e.g., production access)
func (c *Checker) CheckCommand(ctx context.Context, secCtx *security.SecurityContext, cmd *nlp.Command) error {
	startTime := time.Now()
	
	// Get user roles
	roles, err := c.roleStore.GetUserRoles(ctx, secCtx.User.ID)
	if err != nil {
		return err
	}
	
	// Extract resource and verb from command
	resource, verb := c.extractResourceAndVerb(cmd)
	namespace := c.extractNamespace(cmd)
	
	// Check RBAC permissions
	hasPermission := false
	for _, role := range roles {
		if c.roleHasPermission(role, resource, verb, namespace) {
			hasPermission = true
			
			// Check if MFA is required for this role
			if role.RequireMFA && !secCtx.User.MFAVerified {
				return &security.SecurityError{
					Layer:     "authz",
					Type:      security.ErrorTypeAuthz,
					Message:   "MFA required for this operation",
					Details:   map[string]interface{}{"role": role.Name},
					Timestamp: time.Now(),
					UserID:    secCtx.User.ID,
					SessionID: secCtx.User.SessionID,
				}
			}
			
			// Check time restrictions
			if !c.checkTimeRestriction(role.TimeRestrictions) {
				return &security.SecurityError{
					Layer:     "authz",
					Type:      security.ErrorTypeAuthz,
					Message:   "Operation not allowed at this time",
					Details:   map[string]interface{}{
						"role":        role.Name,
						"current_hour": time.Now().Hour(),
					},
					Timestamp: time.Now(),
					UserID:    secCtx.User.ID,
					SessionID: secCtx.User.SessionID,
				}
			}
			
			break
		}
	}
	
	if !hasPermission {
		return &security.SecurityError{
			Layer:     "authz",
			Type:      security.ErrorTypeAuthz,
			Message:   "Permission denied",
			Details: map[string]interface{}{
				"resource":  resource,
				"verb":      verb,
				"namespace": namespace,
			},
			Timestamp: time.Now(),
			UserID:    secCtx.User.ID,
			SessionID: secCtx.User.SessionID,
		}
	}
	
	// Evaluate context-aware policies
	policies, err := c.policyStore.GetPolicies(ctx)
	if err != nil {
		return err
	}
	
	for _, policy := range policies {
		effect, err := c.evaluatePolicy(policy, secCtx, cmd)
		if err != nil {
			continue // Skip policies with evaluation errors
		}
		
		if effect == security.PolicyEffectDENY {
			return &security.SecurityError{
				Layer:     "authz",
				Type:      security.ErrorTypeAuthz,
				Message:   "Denied by policy",
				Details: map[string]interface{}{
					"policy": policy.Name,
					"reason": policy.Description,
				},
				Timestamp: time.Now(),
				UserID:    secCtx.User.ID,
				SessionID: secCtx.User.SessionID,
			}
		}
	}
	
	// Check succeeded
	// Duration tracking: Implement when Prometheus metrics are wired
	// duration := time.Since(startTime)
	// authzCheckDuration.Observe(duration.Seconds())
	_ = startTime
	return nil
}

// roleHasPermission checks if a role has permission for resource/verb/namespace
func (c *Checker) roleHasPermission(role security.Role, resource, verb, namespace string) bool {
	for _, perm := range role.Permissions {
		// Check resource match
		if perm.Resource != "*" && perm.Resource != resource {
			continue
		}
		
		// Check verb match
		verbMatches := false
		for _, v := range perm.Verbs {
			if v == "*" || v == verb {
				verbMatches = true
				break
			}
		}
		if !verbMatches {
			continue
		}
		
		// Check namespace match
		if perm.Namespace != "*" && perm.Namespace != namespace {
			continue
		}
		
		// All checks passed
		return true
	}
	
	return false
}

// checkTimeRestriction checks if current time satisfies restrictions
func (c *Checker) checkTimeRestriction(tr security.TimeRestriction) bool {
	now := time.Now()
	
	// Check hour restriction
	if len(tr.AllowedHours) > 0 {
		currentHour := now.Hour()
		hourAllowed := false
		for _, h := range tr.AllowedHours {
			if h == currentHour {
				hourAllowed = true
				break
			}
		}
		if !hourAllowed {
			return false
		}
	}
	
	// Check day restriction
	if len(tr.AllowedDays) > 0 {
		currentDay := int(now.Weekday())
		dayAllowed := false
		for _, d := range tr.AllowedDays {
			if d == currentDay {
				dayAllowed = true
				break
			}
		}
		if !dayAllowed {
			return false
		}
	}
	
	return true
}

// evaluatePolicy evaluates a context-aware policy
func (c *Checker) evaluatePolicy(policy security.Policy, secCtx *security.SecurityContext, cmd *nlp.Command) (security.PolicyEffect, error) {
	// All conditions must be satisfied for policy to apply
	for _, condition := range policy.Conditions {
		satisfied, err := c.evaluateCondition(condition, secCtx, cmd)
		if err != nil {
			return "", err
		}
		if !satisfied {
			// Condition not met, policy doesn't apply
			return "", nil
		}
	}
	
	// All conditions satisfied, return policy effect
	return policy.Effect, nil
}

// evaluateCondition evaluates a single policy condition
func (c *Checker) evaluateCondition(cond security.Condition, secCtx *security.SecurityContext, cmd *nlp.Command) (bool, error) {
	switch cond.Type {
	case security.ConditionTypeIP:
		return c.evalIPCondition(cond, secCtx)
	case security.ConditionTypeTime:
		return c.evalTimeCondition(cond)
	case security.ConditionTypeDay:
		return c.evalDayCondition(cond)
	case security.ConditionTypeNamespace:
		return c.evalNamespaceCondition(cond, cmd)
	case security.ConditionTypeRiskScore:
		return c.evalRiskScoreCondition(cond, secCtx)
	default:
		return false, nil
	}
}

// evalIPCondition evaluates IP-based conditions
func (c *Checker) evalIPCondition(cond security.Condition, secCtx *security.SecurityContext) (bool, error) {
	userIP := net.ParseIP(secCtx.IP)
	if userIP == nil {
		return false, nil
	}
	
	switch cond.Operator {
	case security.OperatorEquals:
		allowedIP := net.ParseIP(cond.Value.(string))
		return userIP.Equal(allowedIP), nil
		
	case security.OperatorIn:
		// Value should be a CIDR range
		_, ipNet, err := net.ParseCIDR(cond.Value.(string))
		if err != nil {
			return false, err
		}
		return ipNet.Contains(userIP), nil
		
	default:
		return false, nil
	}
}

// evalTimeCondition evaluates time-based conditions
func (c *Checker) evalTimeCondition(cond security.Condition) (bool, error) {
	currentHour := time.Now().Hour()
	targetHour := cond.Value.(int)
	
	switch cond.Operator {
	case security.OperatorEquals:
		return currentHour == targetHour, nil
	case security.OperatorGreaterThan:
		return currentHour > targetHour, nil
	case security.OperatorLessThan:
		return currentHour < targetHour, nil
	default:
		return false, nil
	}
}

// evalDayCondition evaluates day-based conditions
func (c *Checker) evalDayCondition(cond security.Condition) (bool, error) {
	currentDay := int(time.Now().Weekday())
	
	switch cond.Operator {
	case security.OperatorIn:
		allowedDays := cond.Value.([]int)
		for _, day := range allowedDays {
			if day == currentDay {
				return true, nil
			}
		}
		return false, nil
	default:
		return false, nil
	}
}

// evalNamespaceCondition evaluates namespace-based conditions
func (c *Checker) evalNamespaceCondition(cond security.Condition, cmd *nlp.Command) (bool, error) {
	cmdNamespace := c.extractNamespace(cmd)
	targetNamespace := cond.Value.(string)
	
	switch cond.Operator {
	case security.OperatorEquals:
		return cmdNamespace == targetNamespace, nil
	case security.OperatorNotEquals:
		return cmdNamespace != targetNamespace, nil
	case security.OperatorContains:
		return strings.Contains(cmdNamespace, targetNamespace), nil
	default:
		return false, nil
	}
}

// evalRiskScoreCondition evaluates risk score conditions
func (c *Checker) evalRiskScoreCondition(cond security.Condition, secCtx *security.SecurityContext) (bool, error) {
	threshold := cond.Value.(int)
	
	switch cond.Operator {
	case security.OperatorGreaterThan:
		return secCtx.RiskScore > threshold, nil
	case security.OperatorLessThan:
		return secCtx.RiskScore < threshold, nil
	default:
		return false, nil
	}
}

// extractResourceAndVerb extracts resource type and verb from command
func (c *Checker) extractResourceAndVerb(cmd *nlp.Command) (string, string) {
	if len(cmd.Path) < 2 {
		return "unknown", "unknown"
	}
	
	// Path typically: ["kubectl", "get", "pods"]
	verb := cmd.Path[1]       // "get", "delete", etc.
	resource := cmd.Path[2]   // "pods", "deployments", etc.
	
	return resource, verb
}

// extractNamespace extracts namespace from command
func (c *Checker) extractNamespace(cmd *nlp.Command) string {
	// Check flags for namespace
	if ns, ok := cmd.Flags["-n"]; ok {
		return ns
	}
	if ns, ok := cmd.Flags["--namespace"]; ok {
		return ns
	}
	
	// Default namespace
	return "default"
}
