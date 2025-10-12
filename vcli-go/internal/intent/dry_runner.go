// Package intent - Dry Runner
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// Executes commands in simulation mode to preview impact
// without actually making changes.
package intent

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// DryRunner executes commands in simulation mode
//
// Purpose: Before actually executing a destructive command,
// we simulate it to show user what would happen. This is
// similar to kubectl's --dry-run flag.
type DryRunner struct {
	// TODO: Add kubectl client for actual dry-run
}

// NewDryRunner creates a new dry runner
func NewDryRunner() *DryRunner {
	return &DryRunner{}
}

// DryRunResult represents result of dry-run execution
//
// Dry-run simulates command execution without actually
// making changes. This allows user to preview what
// would happen.
type DryRunResult struct {
	// Did dry-run succeed?
	Success bool

	// Output from dry-run
	Output string

	// Any errors that would occur
	Errors []string

	// List of resources that would be changed
	ResourcesChanged []string

	// Changes that would be made
	Changes []Change
}

// Change represents a specific change that would be made
type Change struct {
	Resource string
	Field    string
	OldValue string
	NewValue string
}

// Execute runs command in dry-run mode
//
// This simulates command execution without making actual changes.
// Returns detailed information about what would happen.
func (dr *DryRunner) Execute(ctx context.Context, cmd *nlp.Command) (*DryRunResult, error) {
	// TODO: Implement actual dry-run execution with kubectl
	// For now, return simulated result

	result := &DryRunResult{
		Success:          true,
		Output:           "Dry-run simulation",
		Errors:           []string{},
		ResourcesChanged: dr.extractResourceNames(cmd),
		Changes:          []Change{},
	}

	return result, nil
}

// Estimate calculates impact without running command
//
// This is faster than Execute() - it just analyzes the command
// structure to estimate impact, without actually talking to K8s.
func (dr *DryRunner) Estimate(ctx context.Context, cmd *nlp.Command) (*Impact, error) {
	// Extract resource count
	resourceCount := dr.countResources(cmd)

	// Extract namespaces
	namespaces := dr.extractNamespaces(cmd)

	// Determine if reversible
	reversible := dr.isReversible(cmd)

	// Calculate risk score
	riskScore := dr.calculateRisk(cmd, resourceCount)

	// Estimate duration
	duration := dr.estimateDuration(cmd, resourceCount)

	// Build description
	description := dr.buildDescription(cmd, resourceCount, namespaces)

	impact := &Impact{
		AffectedResources: dr.extractResourceNames(cmd),
		Severity:          dr.getSeverityLevel(riskScore),
		Reversible:        reversible,
		EstimatedTime:     duration,
		Dependencies:      []string{},
		Description:       description,
		RiskScore:         riskScore,
	}

	return impact, nil
}

// countResources counts how many resources will be affected
func (dr *DryRunner) countResources(cmd *nlp.Command) int {
	// If specific resources are named, count them
	if len(cmd.Args) > 0 {
		return len(cmd.Args)
	}

	// If using selectors or --all, estimate higher
	if _, exists := cmd.Flags["--all"]; exists {
		return 10 // Conservative estimate
	}
	if _, exists := cmd.Flags["-l"]; exists {
		return 5 // Conservative estimate
	}
	if _, exists := cmd.Flags["--selector"]; exists {
		return 5 // Conservative estimate
	}

	// Default to 1 resource
	return 1
}

// extractNamespaces gets affected namespaces
func (dr *DryRunner) extractNamespaces(cmd *nlp.Command) []string {
	// Check -n or --namespace flag
	if ns, exists := cmd.Flags["-n"]; exists && ns != "" {
		return []string{ns}
	}
	if ns, exists := cmd.Flags["--namespace"]; exists && ns != "" {
		return []string{ns}
	}

	// Check for --all-namespaces
	if _, exists := cmd.Flags["--all-namespaces"]; exists {
		return []string{"ALL"}
	}
	if _, exists := cmd.Flags["-A"]; exists {
		return []string{"ALL"}
	}

	return []string{"default"}
}

// isReversible determines if action can be undone
func (dr *DryRunner) isReversible(cmd *nlp.Command) bool {
	verb := dr.extractVerb(cmd)

	// Delete operations
	if verb == "delete" || verb == "remove" {
		// Check if resource has controller (reversible)
		// For now, assume pods with controllers are reversible
		resource := dr.extractResource(cmd)
		if resource == "pod" || resource == "pods" {
			return true // Pods are recreated by controllers
		}
		return false
	}

	// Scale operations are reversible
	if verb == "scale" {
		return true
	}

	// Apply/patch are reversible (can re-apply previous state)
	if verb == "apply" || verb == "patch" {
		return true
	}

	// Default to not reversible (be conservative)
	return false
}

// calculateRisk computes risk score (0.0 - 1.0)
func (dr *DryRunner) calculateRisk(cmd *nlp.Command, resourceCount int) float64 {
	verb := dr.extractVerb(cmd)

	// Base risk by verb
	baseRisk := 0.0
	switch verb {
	case "delete", "remove":
		baseRisk = 0.8
	case "scale":
		baseRisk = 0.5
	case "patch", "apply":
		baseRisk = 0.4
	case "create":
		baseRisk = 0.2
	default:
		baseRisk = 0.1
	}

	// Increase risk for multiple resources
	if resourceCount > 5 {
		baseRisk += 0.1
	}
	if resourceCount > 10 {
		baseRisk += 0.1
	}

	// Increase risk for production namespace
	namespaces := dr.extractNamespaces(cmd)
	for _, ns := range namespaces {
		if ns == "production" || ns == "prod" || ns == "ALL" {
			baseRisk += 0.2
		}
	}

	// Cap at 1.0
	if baseRisk > 1.0 {
		baseRisk = 1.0
	}

	return baseRisk
}

// estimateDuration estimates how long command will take
func (dr *DryRunner) estimateDuration(cmd *nlp.Command, resourceCount int) string {
	verb := dr.extractVerb(cmd)

	// Base duration by verb
	baseDuration := time.Second
	switch verb {
	case "delete":
		baseDuration = 5 * time.Second
	case "scale":
		baseDuration = 10 * time.Second
	case "apply":
		baseDuration = 3 * time.Second
	case "get", "list":
		baseDuration = 1 * time.Second
	}

	// Scale by resource count
	totalDuration := baseDuration * time.Duration(resourceCount)

	// Format nicely
	if totalDuration < time.Minute {
		return fmt.Sprintf("%d segundos", int(totalDuration.Seconds()))
	}
	return fmt.Sprintf("%d minutos", int(totalDuration.Minutes()))
}

// buildDescription creates human-readable impact description
func (dr *DryRunner) buildDescription(cmd *nlp.Command, resourceCount int, namespaces []string) string {
	verb := dr.extractVerb(cmd)
	resource := dr.extractResource(cmd)

	var desc strings.Builder

	desc.WriteString(fmt.Sprintf("Esta ação irá %s ", verb))
	if resourceCount > 1 {
		desc.WriteString(fmt.Sprintf("%d %s", resourceCount, resource))
	} else {
		desc.WriteString(fmt.Sprintf("1 %s", resource))
	}

	if len(namespaces) > 0 && namespaces[0] != "default" {
		desc.WriteString(fmt.Sprintf(" no namespace %s", namespaces[0]))
	}

	desc.WriteString(".")

	return desc.String()
}

// getSeverityLevel converts risk score to severity string
func (dr *DryRunner) getSeverityLevel(riskScore float64) string {
	if riskScore >= 0.8 {
		return "critical"
	}
	if riskScore >= 0.6 {
		return "high"
	}
	if riskScore >= 0.3 {
		return "medium"
	}
	return "low"
}

// extractVerb gets action verb from command
func (dr *DryRunner) extractVerb(cmd *nlp.Command) string {
	if len(cmd.Path) >= 2 && cmd.Path[0] == "kubectl" {
		return cmd.Path[1]
	}
	if len(cmd.Path) > 0 {
		return cmd.Path[0]
	}
	return "execute"
}

// extractResource gets resource type from command
func (dr *DryRunner) extractResource(cmd *nlp.Command) string {
	if len(cmd.Path) >= 3 && cmd.Path[0] == "kubectl" {
		return cmd.Path[2]
	}
	if resource, exists := cmd.Flags["--resource"]; exists {
		return resource
	}
	if resource, exists := cmd.Flags["-r"]; exists {
		return resource
	}
	return "resource"
}

// extractResourceNames gets names of specific resources
func (dr *DryRunner) extractResourceNames(cmd *nlp.Command) []string {
	return cmd.Args
}
