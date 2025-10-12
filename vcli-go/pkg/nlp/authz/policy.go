// Package authz - Policy Engine for context-aware authorization
//
// Evaluates contextual policies that go beyond simple RBAC,
// considering environment, time, device trust, and other factors.
package authz

import (
	"errors"
	"fmt"
)

// PolicyEngine evaluates context-aware authorization policies.
type PolicyEngine struct {
	policies []*Policy
}

// NewPolicyEngine creates a new policy engine with default policies.
func NewPolicyEngine() *PolicyEngine {
	engine := &PolicyEngine{
		policies: []*Policy{},
	}

	// Initialize default policies
	engine.initializeDefaultPolicies()

	return engine
}

// initializeDefaultPolicies sets up standard security policies.
func (p *PolicyEngine) initializeDefaultPolicies() {
	// Policy: Production Delete Restriction
	p.policies = append(p.policies, &Policy{
		Name:        "production-delete-restriction",
		Description: "Deleting resources in production requires MFA and manager approval",
		Conditions: []Condition{
			{Type: ConditionEnvironment, Value: string(EnvProduction)},
		},
		Requirements: []Requirement{
			RequirementMFA,
			RequirementManagerApproval,
			RequirementChangeTicket,
		},
		Priority: 100,
	})

	// Policy: Night Operations Escalation
	p.policies = append(p.policies, &Policy{
		Name:        "night-operations-escalation",
		Description: "Operations during night hours require on-call confirmation",
		Conditions: []Condition{
			{Type: ConditionTimeOfDay, Value: "22:00-06:00"},
		},
		Requirements: []Requirement{
			RequirementOnCallConfirm,
			RequirementIncidentNumber,
		},
		Priority: 80,
	})

	// Policy: Weekend Production Changes
	p.policies = append(p.policies, &Policy{
		Name:        "weekend-production-restriction",
		Description: "Production changes on weekends require second approver",
		Conditions: []Condition{
			{Type: ConditionEnvironment, Value: string(EnvProduction)},
			{Type: ConditionDayOfWeek, Value: "weekend"},
		},
		Requirements: []Requirement{
			RequirementSecondApprover,
			RequirementChangeTicket,
		},
		Priority: 90,
	})

	// Policy: Untrusted Device Restrictions
	p.policies = append(p.policies, &Policy{
		Name:        "untrusted-device-restriction",
		Description: "Untrusted devices require additional MFA",
		Conditions: []Condition{
			{Type: ConditionDeviceTrust, Value: "untrusted"},
		},
		Requirements: []Requirement{
			RequirementMFA,
		},
		Priority: 70,
	})

	// Policy: Secret Access Restriction
	p.policies = append(p.policies, &Policy{
		Name:        "secret-access-policy",
		Description: "Accessing secrets requires MFA and signed command",
		Conditions:  []Condition{},
		Requirements: []Requirement{
			RequirementMFA,
			RequirementSignedCommand,
		},
		Priority: 110, // High priority
	})
}

// EvaluatePolicies evaluates all policies against the context.
// Returns aggregated policy decision with all matched policies.
func (p *PolicyEngine) EvaluatePolicies(ctx *AuthzContext, resource Resource, action Action) (*PolicyDecision, error) {
	if ctx == nil {
		return nil, errors.New("authz context cannot be nil")
	}

	decision := &PolicyDecision{
		Policies:     []*Policy{},
		Requirements: []Requirement{},
		Denied:       false,
	}

	// Check for secret access
	if resource == ResourceSecret {
		// Find secret access policy
		for _, policy := range p.policies {
			if policy.Name == "secret-access-policy" {
				decision.Policies = append(decision.Policies, policy)
				decision.Requirements = append(decision.Requirements, policy.Requirements...)
			}
		}
	}

	// Evaluate all policies by priority
	for _, policy := range p.policies {
		// Check if all conditions match
		if !p.policyMatches(policy, ctx) {
			continue
		}

		// Policy matches
		decision.Policies = append(decision.Policies, policy)

		// If it's a deny policy, deny immediately
		if policy.IsDenyPolicy {
			decision.Denied = true
			decision.DenyReason = policy.Description
			return decision, nil
		}

		// Add requirements
		decision.Requirements = append(decision.Requirements, policy.Requirements...)
	}

	// Remove duplicate requirements
	decision.Requirements = uniqueRequirements(decision.Requirements)

	return decision, nil
}

// policyMatches checks if all conditions of a policy match the context.
func (p *PolicyEngine) policyMatches(policy *Policy, ctx *AuthzContext) bool {
	// Empty conditions = always match
	if len(policy.Conditions) == 0 {
		return false // Don't match policies with no conditions (except when explicitly checked)
	}

	// All conditions must match
	for _, condition := range policy.Conditions {
		if !condition.Matches(ctx) {
			return false
		}
	}

	return true
}

// AddPolicy adds a custom policy to the engine.
func (p *PolicyEngine) AddPolicy(policy *Policy) error {
	if policy == nil {
		return errors.New("policy cannot be nil")
	}
	if policy.Name == "" {
		return errors.New("policy name is required")
	}

	p.policies = append(p.policies, policy)
	return nil
}

// RemovePolicy removes a policy by name.
func (p *PolicyEngine) RemovePolicy(name string) error {
	newPolicies := []*Policy{}
	found := false

	for _, policy := range p.policies {
		if policy.Name != name {
			newPolicies = append(newPolicies, policy)
		} else {
			found = true
		}
	}

	if !found {
		return fmt.Errorf("policy not found: %s", name)
	}

	p.policies = newPolicies
	return nil
}

// GetPolicy retrieves a policy by name.
func (p *PolicyEngine) GetPolicy(name string) (*Policy, error) {
	for _, policy := range p.policies {
		if policy.Name == name {
			return policy, nil
		}
	}
	return nil, fmt.Errorf("policy not found: %s", name)
}

// ListPolicies returns all policies.
func (p *PolicyEngine) ListPolicies() []*Policy {
	return p.policies
}

// GetPolicyCount returns the number of policies.
func (p *PolicyEngine) GetPolicyCount() int {
	return len(p.policies)
}

// Helper function to remove duplicate requirements
func uniqueRequirements(reqs []Requirement) []Requirement {
	seen := make(map[Requirement]bool)
	unique := []Requirement{}

	for _, req := range reqs {
		if !seen[req] {
			seen[req] = true
			unique = append(unique, req)
		}
	}

	return unique
}
