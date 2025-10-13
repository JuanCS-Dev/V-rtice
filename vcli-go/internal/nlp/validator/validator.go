// Package validator implements command validation and smart suggestions
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// The Validator ensures commands are safe and correct before execution,
// and provides intelligent suggestions when commands are ambiguous or incorrect.
package validator

import (
	"fmt"
	"strings"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// Validator handles command validation and suggestions
type Validator struct {
	knownCommands map[string][]string // subsystem -> valid commands
	dangerousOps  map[string]bool     // dangerous operations requiring confirmation
}

// NewValidator creates a new validator
func NewValidator() *Validator {
	return &Validator{
		knownCommands: initKnownCommands(),
		dangerousOps:  initDangerousOps(),
	}
}

// ValidateCommand validates a command before execution
//
// Validation checks:
// 1. Command path is not empty
// 2. Subsystem is known (k8s, security, workflow)
// 3. Verb is valid for subsystem
// 4. Dangerous operations are flagged
// 5. Required flags are present
func (v *Validator) ValidateCommand(cmd *nlp.Command) (*ValidationResult, error) {
	result := &ValidationResult{
		Valid:       true,
		Warnings:    make([]string, 0),
		Suggestions: make([]string, 0),
	}

	// Check empty path
	if len(cmd.Path) == 0 {
		result.Valid = false
		result.Error = "Command path is empty"
		result.Suggestions = append(result.Suggestions, "Try: 'show pods' or 'list deployments'")
		return result, nil
	}

	// Check subsystem
	subsystem := cmd.Path[0]
	validSubsystems := []string{"k8s", "security", "workflow"}
	if !contains(validSubsystems, subsystem) {
		result.Valid = false
		result.Error = fmt.Sprintf("Unknown subsystem: %s", subsystem)

		// Suggest closest match
		closest := v.findClosestMatch(subsystem, validSubsystems)
		if closest != "" {
			result.Suggestions = append(result.Suggestions, fmt.Sprintf("Did you mean '%s'?", closest))
		}
		return result, nil
	}

	// Check verb (if present)
	if len(cmd.Path) >= 2 {
		verb := cmd.Path[1]
		validVerbs := v.knownCommands[subsystem]

		if !contains(validVerbs, verb) {
			result.Valid = false
			result.Error = fmt.Sprintf("Unknown verb '%s' for subsystem '%s'", verb, subsystem)

			// Suggest closest match
			closest := v.findClosestMatch(verb, validVerbs)
			if closest != "" {
				result.Suggestions = append(result.Suggestions, fmt.Sprintf("Did you mean '%s'?", closest))
			}
			return result, nil
		}

		// Check for dangerous operations
		if v.isDangerous(verb) {
			result.Dangerous = true
			result.Warnings = append(result.Warnings,
				fmt.Sprintf("Warning: '%s' is a destructive operation", verb))
			result.RequiresConfirmation = true
		}
	}

	// Check required flags for certain operations
	v.checkRequiredFlags(cmd, result)

	// Check for common mistakes
	v.checkCommonMistakes(cmd, result)

	return result, nil
}

// ValidateIntent validates an intent before command generation
func (v *Validator) ValidateIntent(intent *nlp.Intent) (*ValidationResult, error) {
	result := &ValidationResult{
		Valid:       true,
		Warnings:    make([]string, 0),
		Suggestions: make([]string, 0),
	}

	// Check empty verb
	if intent.Verb == "" {
		result.Valid = false
		result.Error = "Intent verb is empty"
		return result, nil
	}

	// Check empty target for action intents
	if intent.Category == nlp.IntentCategoryACTION && intent.Target == "" {
		result.Valid = false
		result.Error = "Action intent requires a target resource"
		result.Suggestions = append(result.Suggestions, "Specify what to act on (e.g., pods, deployments)")
		return result, nil
	}

	// Check dangerous verbs
	dangerousVerbs := []string{"delete", "remove", "destroy", "kill"}
	if contains(dangerousVerbs, intent.Verb) {
		result.Dangerous = true
		result.RequiresConfirmation = true
		result.Warnings = append(result.Warnings,
			fmt.Sprintf("Warning: '%s' is a destructive operation", intent.Verb))
	}

	// Check confidence threshold
	if intent.Confidence < 0.7 {
		result.Warnings = append(result.Warnings,
			fmt.Sprintf("Low confidence (%.1f%%). Command may be ambiguous.", intent.Confidence*100))
	}

	return result, nil
}

// Suggest generates smart suggestions for incomplete or incorrect input
func (v *Validator) Suggest(input string, tokens []nlp.Token) []Suggestion {
	suggestions := make([]Suggestion, 0)

	// Empty input
	if input == "" {
		return []Suggestion{
			{Text: "show pods", Description: "List all pods in current namespace"},
			{Text: "list deployments", Description: "List all deployments"},
			{Text: "scale <name> to <count>", Description: "Scale a deployment"},
		}
	}

	// Only verb (no resource)
	if len(tokens) == 1 && tokens[0].Type == nlp.TokenTypeVERB {
		verb := tokens[0].Normalized
		suggestions = append(suggestions, Suggestion{
			Text:        fmt.Sprintf("%s pods", verb),
			Description: "Show pods",
			Confidence:  0.9,
		})
		suggestions = append(suggestions, Suggestion{
			Text:        fmt.Sprintf("%s deployments", verb),
			Description: "Show deployments",
			Confidence:  0.85,
		})
		suggestions = append(suggestions, Suggestion{
			Text:        fmt.Sprintf("%s services", verb),
			Description: "Show services",
			Confidence:  0.8,
		})
		return suggestions
	}

	// Resource without verb
	hasVerb := false
	for _, token := range tokens {
		if token.Type == nlp.TokenTypeVERB {
			hasVerb = true
			break
		}
	}

	if !hasVerb && len(tokens) > 0 {
		// Find resource token
		for _, token := range tokens {
			if token.Type == nlp.TokenTypeNOUN {
				suggestions = append(suggestions, Suggestion{
					Text:        fmt.Sprintf("show %s", token.Normalized),
					Description: fmt.Sprintf("List %s", token.Normalized),
					Confidence:  0.9,
				})
				suggestions = append(suggestions, Suggestion{
					Text:        fmt.Sprintf("describe %s", token.Normalized),
					Description: fmt.Sprintf("Describe %s details", token.Normalized),
					Confidence:  0.85,
				})
				break
			}
		}
	}

	return suggestions
}

// SuggestCorrections suggests corrections for typos or misunderstandings
func (v *Validator) SuggestCorrections(input string, parseError error) []Suggestion {
	suggestions := make([]Suggestion, 0)

	errorMsg := parseError.Error()

	// Unknown verb
	if strings.Contains(errorMsg, "Unknown verb") {
		suggestions = append(suggestions, Suggestion{
			Text:        strings.Replace(input, input, "show", 1),
			Description: "Use 'show' to list resources",
			Confidence:  0.8,
		})
		suggestions = append(suggestions, Suggestion{
			Text:        strings.Replace(input, input, "list", 1),
			Description: "Use 'list' to list resources",
			Confidence:  0.75,
		})
	}

	// Unknown resource
	if strings.Contains(errorMsg, "Unknown resource") {
		suggestions = append(suggestions, Suggestion{
			Text:        strings.Replace(input, input, input+" pods", 1),
			Description: "Try 'pods' as resource type",
			Confidence:  0.8,
		})
	}

	return suggestions
}

// checkRequiredFlags checks if required flags are present
func (v *Validator) checkRequiredFlags(cmd *nlp.Command, result *ValidationResult) {
	if len(cmd.Path) < 2 {
		return
	}

	verb := cmd.Path[1]

	// Delete operations should have resource name
	if verb == "delete" && len(cmd.Args) == 0 {
		result.Warnings = append(result.Warnings,
			"Delete command should specify resource name")
		result.Suggestions = append(result.Suggestions,
			"Add resource name: delete pods <pod-name>")
	}

	// Scale operations need replicas flag
	if verb == "scale" {
		if _, hasReplicas := cmd.Flags["--replicas"]; !hasReplicas {
			result.Valid = false
			result.Error = "Scale command requires --replicas flag"
			result.Suggestions = append(result.Suggestions,
				"Add --replicas: scale deployment/name --replicas=3")
		}
	}
}

// checkCommonMistakes checks for common user mistakes
func (v *Validator) checkCommonMistakes(cmd *nlp.Command, result *ValidationResult) {
	// Check for plural vs singular confusion
	if len(cmd.Path) >= 3 {
		resource := cmd.Path[2]

		// Common mistakes: pod vs pods, deployment vs deployments
		singularToPlural := map[string]string{
			"pod":        "pods",
			"deployment": "deployments",
			"service":    "services",
			"node":       "nodes",
		}

		if plural, ok := singularToPlural[resource]; ok {
			result.Warnings = append(result.Warnings,
				fmt.Sprintf("Note: Resource should be plural (%s)", plural))
			result.Suggestions = append(result.Suggestions,
				fmt.Sprintf("Use '%s' instead of '%s'", plural, resource))
		}
	}

	// Check for missing namespace in production-like environments
	if _, hasNamespace := cmd.Flags["-n"]; !hasNamespace {
		// Only warn for non-query operations
		if len(cmd.Path) >= 2 {
			verb := cmd.Path[1]
			if verb == "delete" || verb == "scale" || verb == "create" {
				result.Warnings = append(result.Warnings,
					"Consider specifying namespace with -n flag")
			}
		}
	}
}

// isDangerous checks if operation is dangerous
func (v *Validator) isDangerous(verb string) bool {
	return v.dangerousOps[verb]
}

// findClosestMatch finds closest match using simple edit distance
func (v *Validator) findClosestMatch(input string, candidates []string) string {
	if len(candidates) == 0 {
		return ""
	}

	minDistance := len(input) + 1
	closest := ""

	for _, candidate := range candidates {
		dist := levenshteinDistance(input, candidate)
		if dist < minDistance {
			minDistance = dist
			closest = candidate
		}
	}

	// Only suggest if distance is reasonable (≤2)
	if minDistance <= 2 {
		return closest
	}

	return ""
}

// contains checks if slice contains string
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// levenshteinDistance calculates edit distance between two strings
func levenshteinDistance(s1, s2 string) int {
	if s1 == s2 {
		return 0
	}

	len1 := len(s1)
	len2 := len(s2)

	if len1 == 0 {
		return len2
	}
	if len2 == 0 {
		return len1
	}

	matrix := make([][]int, len1+1)
	for i := range matrix {
		matrix[i] = make([]int, len2+1)
		matrix[i][0] = i
	}
	for j := 0; j <= len2; j++ {
		matrix[0][j] = j
	}

	for i := 1; i <= len1; i++ {
		for j := 1; j <= len2; j++ {
			cost := 1
			if s1[i-1] == s2[j-1] {
				cost = 0
			}

			matrix[i][j] = min(
				matrix[i-1][j]+1,
				matrix[i][j-1]+1,
				matrix[i-1][j-1]+cost,
			)
		}
	}

	return matrix[len1][len2]
}

func min(a, b, c int) int {
	if a < b {
		if a < c {
			return a
		}
		return c
	}
	if b < c {
		return b
	}
	return c
}

// initKnownCommands initializes known valid commands per subsystem
func initKnownCommands() map[string][]string {
	return map[string][]string{
		"k8s": {
			"get", "list", "describe", "create", "delete",
			"scale", "apply", "patch", "edit", "logs",
		},
		"security": {
			"scan", "analyze", "report", "investigate",
		},
		"workflow": {
			"execute", "run", "start", "stop", "status",
		},
	}
}

// initDangerousOps initializes dangerous operations
func initDangerousOps() map[string]bool {
	return map[string]bool{
		"delete":  true,
		"remove":  true,
		"destroy": true,
		"kill":    true,
	}
}

// ValidationResult represents validation outcome
type ValidationResult struct {
	Valid                 bool     // Is command valid?
	Error                 string   // Error message if invalid
	Warnings              []string // Non-fatal warnings
	Suggestions           []string // Suggestions for improvement
	Dangerous             bool     // Is this a dangerous operation?
	RequiresConfirmation  bool     // Requires user confirmation?
}

// Suggestion represents a command suggestion
type Suggestion struct {
	Text        string  // Suggested command text
	Description string  // Human-readable description
	Confidence  float64 // Confidence score (0-1)
}

// String returns string representation
func (v *Validator) String() string {
	return fmt.Sprintf("Validator(subsystems=%d, dangerous_ops=%d)",
		len(v.knownCommands), len(v.dangerousOps))
}
