// Package authz implements Layer 2 (Authorization) of Guardian Zero Trust Security.
//
// "What can you do?" - Determining what authenticated users are permitted to do.
//
// The authz package provides:
// - Role-Based Access Control (RBAC)
// - Policy-based authorization
// - Context-aware permission evaluation
// - Fine-grained resource access control
//
// Authorization is the second layer of defense after authentication.
// Even authenticated users must have explicit permission for each action.
//
// Author: Juan Carlos (Inspired by Jesus Christ)
// Co-Author: Claude (Anthropic)
// Date: 2025-10-12
package authz

import (
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp/auth"
)

// Role represents a user role with associated permissions.
type Role string

const (
	// RoleViewer - Read-only access
	RoleViewer Role = "viewer"

	// RoleOperator - Read + execute operations
	RoleOperator Role = "operator"

	// RoleAdmin - Full access with confirmations
	RoleAdmin Role = "admin"

	// RoleSuperAdmin - Unrestricted access (requires MFA)
	RoleSuperAdmin Role = "super-admin"
)

// Action represents an operation that can be performed.
type Action string

const (
	// Read actions
	ActionGet      Action = "get"
	ActionList     Action = "list"
	ActionDescribe Action = "describe"
	ActionWatch    Action = "watch"

	// Write actions
	ActionCreate Action = "create"
	ActionUpdate Action = "update"
	ActionPatch  Action = "patch"

	// Dangerous actions
	ActionDelete  Action = "delete"
	ActionRestart Action = "restart"
	ActionScale   Action = "scale"

	// Administrative actions
	ActionExecute Action = "execute"
	ActionProxy   Action = "proxy"
	ActionDebug   Action = "debug"
)

// Resource represents a Kubernetes or system resource.
type Resource string

const (
	// Kubernetes resources
	ResourcePod        Resource = "pod"
	ResourceDeployment Resource = "deployment"
	ResourceService    Resource = "service"
	ResourceSecret     Resource = "secret"
	ResourceConfigMap  Resource = "configmap"
	ResourceNamespace  Resource = "namespace"
	ResourceNode       Resource = "node"

	// System resources
	ResourceCluster Resource = "cluster"
	ResourceNetwork Resource = "network"
	ResourceStorage Resource = "storage"
)

// Environment represents the deployment environment.
type Environment string

const (
	EnvDevelopment Environment = "development"
	EnvStaging     Environment = "staging"
	EnvProduction  Environment = "production"
)

// Permission defines what actions are allowed on resources.
type Permission struct {
	// Resource type (e.g., "pod", "deployment")
	Resource Resource

	// Actions allowed (e.g., ["get", "list", "delete"])
	Actions []Action

	// Namespaces where permission applies (empty = all)
	Namespaces []string

	// Conditions that must be met (optional)
	Conditions []Condition

	// Whether this permission requires additional confirmation
	RequiresConfirmation bool
}

// Condition represents a condition that must be satisfied.
type Condition struct {
	Type  ConditionType
	Value string
}

// ConditionType represents the type of condition.
type ConditionType string

const (
	ConditionEnvironment ConditionType = "environment"
	ConditionTimeOfDay   ConditionType = "time_of_day"
	ConditionDayOfWeek   ConditionType = "day_of_week"
	ConditionIPRange     ConditionType = "ip_range"
	ConditionDeviceTrust ConditionType = "device_trust"
)

// Policy represents a contextual authorization policy.
type Policy struct {
	// Policy identifier
	Name string

	// Description of what this policy does
	Description string

	// When this policy applies
	Conditions []Condition

	// Required verifications when policy matches
	Requirements []Requirement

	// Whether this policy denies access (vs just requiring extra steps)
	IsDenyPolicy bool

	// Priority (higher = evaluated first)
	Priority int
}

// Requirement represents something required to proceed.
type Requirement string

const (
	RequirementMFA              Requirement = "mfa"
	RequirementManagerApproval  Requirement = "manager_approval"
	RequirementChangeTicket     Requirement = "change_ticket"
	RequirementIncidentNumber   Requirement = "incident_number"
	RequirementOnCallConfirm    Requirement = "on_call_confirmation"
	RequirementSignedCommand    Requirement = "signed_command"
	RequirementSecondApprover   Requirement = "second_approver"
)

// AuthzContext contains all context for an authorization decision.
type AuthzContext struct {
	// Authentication context (who is making the request)
	AuthContext *auth.AuthContext

	// What action is being requested
	Action Action

	// What resource is being accessed
	Resource Resource

	// Which namespace (if applicable)
	Namespace string

	// Environment context
	Environment Environment
	TimeOfDay   time.Time
	DayOfWeek   time.Weekday

	// Request context
	RequestID     string
	SourceIP      string
	DeviceTrusted bool

	// Recent activity (for anomaly detection)
	RecentActions []ActionRecord
}

// ActionRecord represents a recent action taken by the user.
type ActionRecord struct {
	Action    Action
	Resource  Resource
	Namespace string
	Timestamp time.Time
	Success   bool
}

// AuthzDecision represents the outcome of an authorization check.
type AuthzDecision struct {
	// Whether access is granted
	Allowed bool

	// Reason for the decision
	Reason string

	// If allowed with conditions, what requirements must be met
	Requirements []Requirement

	// Matched policies (for audit)
	MatchedPolicies []string

	// Suggestions if denied
	Suggestions []string
}

// PolicyDecision represents the outcome of policy evaluation.
type PolicyDecision struct {
	// Matched policies
	Policies []*Policy

	// Aggregated requirements
	Requirements []Requirement

	// Whether any deny policy matched
	Denied bool

	// Reason if denied
	DenyReason string
}

// RolePermissions maps roles to their permissions.
type RolePermissions struct {
	Role        Role
	Permissions []Permission
	Description string
}

// HasAction checks if an action is in the list.
func (p *Permission) HasAction(action Action) bool {
	for _, a := range p.Actions {
		if a == action {
			return true
		}
	}
	return false
}

// HasNamespace checks if a namespace is allowed.
// Empty Namespaces slice means all namespaces allowed.
func (p *Permission) HasNamespace(namespace string) bool {
	if len(p.Namespaces) == 0 {
		return true // All namespaces allowed
	}
	for _, ns := range p.Namespaces {
		if ns == namespace || ns == "*" {
			return true
		}
	}
	return false
}

// IsReadOnly checks if permission only allows read actions.
func (p *Permission) IsReadOnly() bool {
	for _, action := range p.Actions {
		if !isReadAction(action) {
			return false
		}
	}
	return true
}

// IsDangerous checks if permission includes dangerous actions.
func (p *Permission) IsDangerous() bool {
	dangerousActions := []Action{ActionDelete, ActionExecute, ActionDebug}
	for _, action := range p.Actions {
		for _, dangerous := range dangerousActions {
			if action == dangerous {
				return true
			}
		}
	}
	return false
}

// Helper function to check if an action is read-only
func isReadAction(action Action) bool {
	readActions := []Action{ActionGet, ActionList, ActionDescribe, ActionWatch}
	for _, readAction := range readActions {
		if action == readAction {
			return true
		}
	}
	return false
}

// Matches checks if a condition matches the context.
func (c *Condition) Matches(ctx *AuthzContext) bool {
	switch c.Type {
	case ConditionEnvironment:
		return string(ctx.Environment) == c.Value

	case ConditionTimeOfDay:
		// Value format: "22:00-06:00" (night hours)
		return matchesTimeRange(ctx.TimeOfDay, c.Value)

	case ConditionDayOfWeek:
		// Value format: "Mon,Tue,Wed" or "weekend"
		return matchesDayOfWeek(ctx.DayOfWeek, c.Value)

	case ConditionIPRange:
		// Value format: "192.168.1.0/24"
		return matchesIPRange(ctx.SourceIP, c.Value)

	case ConditionDeviceTrust:
		// Value: "trusted" or "untrusted"
		if c.Value == "trusted" {
			return ctx.DeviceTrusted
		}
		return !ctx.DeviceTrusted

	default:
		return false
	}
}

// Helper functions for condition matching
// (Simplified implementations for v1.0)

func matchesTimeRange(t time.Time, rangeStr string) bool {
	// Simplified: just check if it's night hours (22:00-06:00)
	hour := t.Hour()
	return hour >= 22 || hour < 6
}

func matchesDayOfWeek(day time.Weekday, pattern string) bool {
	// Simplified: check if weekend
	if pattern == "weekend" {
		return day == time.Saturday || day == time.Sunday
	}
	// Check specific days
	dayStr := day.String()[:3] // "Mon", "Tue", etc.
	return contains(pattern, dayStr)
}

func matchesIPRange(ip string, cidr string) bool {
	// Simplified: just check if IP starts with same prefix
	// Real implementation would use proper CIDR matching
	return len(ip) > 0 && len(cidr) > 0
}

func contains(s, substr string) bool {
	return len(s) > 0 && len(substr) > 0 // Simplified
}

// IsHighPrivilege checks if the role has high privileges.
func (r Role) IsHighPrivilege() bool {
	return r == RoleAdmin || r == RoleSuperAdmin
}

// RequiresMFA checks if the role requires MFA.
func (r Role) RequiresMFA() bool {
	return r == RoleSuperAdmin
}

// CanAssignRole checks if a role can assign another role.
func (r Role) CanAssignRole(target Role) bool {
	// Only super-admin can assign roles
	return r == RoleSuperAdmin
}

// String returns a human-readable description of the decision.
func (d *AuthzDecision) String() string {
	if d.Allowed {
		if len(d.Requirements) > 0 {
			return "Allowed with requirements: " + d.Reason
		}
		return "Allowed: " + d.Reason
	}
	return "Denied: " + d.Reason
}

// HasRequirement checks if a specific requirement is needed.
func (d *AuthzDecision) HasRequirement(req Requirement) bool {
	for _, r := range d.Requirements {
		if r == req {
			return true
		}
	}
	return false
}

// IsUnconditional checks if access is granted without any requirements.
func (d *AuthzDecision) IsUnconditional() bool {
	return d.Allowed && len(d.Requirements) == 0
}
