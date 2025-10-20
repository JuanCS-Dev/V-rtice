// Package sandbox - Layer 3: Sandboxing
//
// Enforces namespace and resource scope boundaries
package sandbox

import (
	"context"
	"fmt"
	"strings"
)

// SandboxLayer enforces execution boundaries
type SandboxLayer interface {
	// ValidateScope checks if command is within allowed scope
	ValidateScope(ctx context.Context, userID string, namespace string, resource string) (*ScopeDecision, error)
}

// ScopeDecision represents sandbox validation result
type ScopeDecision struct {
	Allowed   bool
	Reason    string
	Namespace string // Effective namespace (may be rewritten)
}

// SandboxRule defines allowed scopes
type SandboxRule struct {
	UserID             string
	AllowedNamespaces  []string // Empty means all
	ForbiddenResources []string // Blacklist
}

type sandboxLayer struct {
	rules map[string]*SandboxRule // userID -> rule
}

// NewSandboxLayer creates sandbox layer
func NewSandboxLayer() SandboxLayer {
	return &sandboxLayer{
		rules: make(map[string]*SandboxRule),
	}
}

// ValidateScope implements SandboxLayer
func (s *sandboxLayer) ValidateScope(ctx context.Context, userID string, namespace string, resource string) (*ScopeDecision, error) {
	rule, exists := s.rules[userID]
	if !exists {
		// No specific rule = default allow
		return &ScopeDecision{
			Allowed:   true,
			Reason:    "No sandbox restrictions",
			Namespace: namespace,
		}, nil
	}

	// Check forbidden resources
	for _, forbidden := range rule.ForbiddenResources {
		if strings.EqualFold(forbidden, resource) {
			return &ScopeDecision{
				Allowed: false,
				Reason:  fmt.Sprintf("Resource '%s' is forbidden", resource),
			}, nil
		}
	}

	// Check namespace restrictions
	if len(rule.AllowedNamespaces) > 0 {
		allowed := false
		for _, ns := range rule.AllowedNamespaces {
			if ns == namespace || ns == "*" {
				allowed = true
				break
			}
		}

		if !allowed {
			return &ScopeDecision{
				Allowed: false,
				Reason:  fmt.Sprintf("Namespace '%s' not in allowed list", namespace),
			}, nil
		}
	}

	return &ScopeDecision{
		Allowed:   true,
		Reason:    "Within sandbox scope",
		Namespace: namespace,
	}, nil
}

// SetRule configures sandbox for user
func (s *sandboxLayer) SetRule(userID string, rule *SandboxRule) {
	s.rules[userID] = rule
}

