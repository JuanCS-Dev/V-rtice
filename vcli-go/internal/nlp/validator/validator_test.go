// Package validator - Unit tests
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package validator

import (
	"fmt"
	"strings"
	"testing"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

func TestValidator_ValidateCommand_ValidK8s(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path: []string{"k8s", "get", "pods"},
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	if !result.Valid {
		t.Errorf("Command should be valid, got error: %s", result.Error)
	}

	if result.Dangerous {
		t.Error("Get command should not be dangerous")
	}
}

func TestValidator_ValidateCommand_EmptyPath(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path: []string{},
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	if result.Valid {
		t.Error("Empty path should be invalid")
	}

	if result.Error == "" {
		t.Error("Should have error message")
	}

	if len(result.Suggestions) == 0 {
		t.Error("Should have suggestions for empty path")
	}
}

func TestValidator_ValidateCommand_UnknownSubsystem(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path: []string{"unknown", "get"},
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	if result.Valid {
		t.Error("Unknown subsystem should be invalid")
	}

	if result.Error == "" {
		t.Error("Should have error for unknown subsystem")
	}
}

func TestValidator_ValidateCommand_UnknownVerb(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path: []string{"k8s", "gte", "pods"}, // Close to "get"
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	if result.Valid {
		t.Error("Unknown verb should be invalid")
	}

	// Should suggest closest match
	if len(result.Suggestions) == 0 {
		t.Error("Should have at least one suggestion for unknown verb")
	}
}

func TestValidator_ValidateCommand_DangerousOperation(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path: []string{"k8s", "delete", "pods"},
		Args: []string{"nginx-pod"},
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	if !result.Valid {
		t.Errorf("Delete command should be valid, got error: %s", result.Error)
	}

	if !result.Dangerous {
		t.Error("Delete should be marked as dangerous")
	}

	if !result.RequiresConfirmation {
		t.Error("Delete should require confirmation")
	}

	if len(result.Warnings) == 0 {
		t.Error("Should have warning for dangerous operation")
	}
}

func TestValidator_ValidateCommand_ScaleWithoutReplicas(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path:  []string{"k8s", "scale", "deployments"},
		Args:  []string{"deployment/nginx"},
		Flags: map[string]string{}, // Missing --replicas
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	if result.Valid {
		t.Error("Scale without --replicas should be invalid")
	}

	if result.Error == "" {
		t.Error("Should have error for missing --replicas")
	}
}

func TestValidator_ValidateCommand_ScaleWithReplicas(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path:  []string{"k8s", "scale", "deployments"},
		Args:  []string{"deployment/nginx"},
		Flags: map[string]string{"--replicas": "5"},
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	if !result.Valid {
		t.Errorf("Scale with --replicas should be valid, got error: %s", result.Error)
	}
}

func TestValidator_ValidateCommand_DeleteWithoutName(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path: []string{"k8s", "delete", "pods"},
		Args: []string{}, // No pod name
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	// Should still be valid but have warning
	if !result.Valid {
		t.Error("Delete without name should technically be valid (deletes all)")
	}

	if len(result.Warnings) == 0 {
		t.Error("Should have warning about missing resource name")
	}
}

func TestValidator_ValidateCommand_SingularResource(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path: []string{"k8s", "get", "pod"}, // Singular instead of plural
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	// Should have warning about plural
	if len(result.Warnings) == 0 {
		t.Error("Should have warning about using plural form")
	}

	if len(result.Suggestions) == 0 {
		t.Error("Should suggest plural form")
	}
}

func TestValidator_ValidateCommand_ActionWithoutNamespace(t *testing.T) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path:  []string{"k8s", "delete", "pods"},
		Args:  []string{"nginx-pod"},
		Flags: map[string]string{}, // No namespace
	}

	result, err := validator.ValidateCommand(cmd)
	if err != nil {
		t.Fatalf("ValidateCommand() error = %v", err)
	}

	// Should have warning about namespace
	foundNamespaceWarning := false
	for _, warning := range result.Warnings {
		if strings.Contains(warning, "namespace") {
			foundNamespaceWarning = true
			break
		}
	}

	if !foundNamespaceWarning {
		t.Error("Should have warning about missing namespace for destructive operation")
	}
}

func TestValidator_ValidateIntent_ValidQuery(t *testing.T) {
	validator := NewValidator()

	intent := &nlp.Intent{
		Verb:       "show",
		Target:     "pods",
		Category:   nlp.IntentCategoryQUERY,
		Confidence: 0.95,
	}

	result, err := validator.ValidateIntent(intent)
	if err != nil {
		t.Fatalf("ValidateIntent() error = %v", err)
	}

	if !result.Valid {
		t.Errorf("Valid intent should pass validation, got error: %s", result.Error)
	}

	if result.Dangerous {
		t.Error("Query intent should not be dangerous")
	}
}

func TestValidator_ValidateIntent_EmptyVerb(t *testing.T) {
	validator := NewValidator()

	intent := &nlp.Intent{
		Verb:     "", // Empty
		Target:   "pods",
		Category: nlp.IntentCategoryQUERY,
	}

	result, err := validator.ValidateIntent(intent)
	if err != nil {
		t.Fatalf("ValidateIntent() error = %v", err)
	}

	if result.Valid {
		t.Error("Intent with empty verb should be invalid")
	}
}

func TestValidator_ValidateIntent_ActionWithoutTarget(t *testing.T) {
	validator := NewValidator()

	intent := &nlp.Intent{
		Verb:     "delete",
		Target:   "", // Empty target
		Category: nlp.IntentCategoryACTION,
	}

	result, err := validator.ValidateIntent(intent)
	if err != nil {
		t.Fatalf("ValidateIntent() error = %v", err)
	}

	if result.Valid {
		t.Error("Action intent without target should be invalid")
	}

	if len(result.Suggestions) == 0 {
		t.Error("Should have suggestions for missing target")
	}
}

func TestValidator_ValidateIntent_DangerousVerb(t *testing.T) {
	validator := NewValidator()

	dangerousVerbs := []string{"delete", "remove", "destroy", "kill"}

	for _, verb := range dangerousVerbs {
		t.Run(verb, func(t *testing.T) {
			intent := &nlp.Intent{
				Verb:       verb,
				Target:     "pods",
				Category:   nlp.IntentCategoryACTION,
				Confidence: 0.95,
			}

			result, err := validator.ValidateIntent(intent)
			if err != nil {
				t.Fatalf("ValidateIntent() error = %v", err)
			}

			if !result.Dangerous {
				t.Errorf("Verb '%s' should be marked as dangerous", verb)
			}

			if !result.RequiresConfirmation {
				t.Errorf("Verb '%s' should require confirmation", verb)
			}
		})
	}
}

func TestValidator_ValidateIntent_LowConfidence(t *testing.T) {
	validator := NewValidator()

	intent := &nlp.Intent{
		Verb:       "show",
		Target:     "pods",
		Category:   nlp.IntentCategoryQUERY,
		Confidence: 0.5, // Low confidence
	}

	result, err := validator.ValidateIntent(intent)
	if err != nil {
		t.Fatalf("ValidateIntent() error = %v", err)
	}

	if len(result.Warnings) == 0 {
		t.Error("Should have warning for low confidence")
	}
}

func TestValidator_Suggest_EmptyInput(t *testing.T) {
	validator := NewValidator()

	suggestions := validator.Suggest("", []nlp.Token{})

	if len(suggestions) == 0 {
		t.Error("Should have suggestions for empty input")
	}

	// Should suggest common commands
	foundPods := false
	for _, sug := range suggestions {
		if strings.Contains(sug.Text, "pods") {
			foundPods = true
			break
		}
	}

	if !foundPods {
		t.Error("Should suggest pods-related command")
	}
}

func TestValidator_Suggest_VerbOnly(t *testing.T) {
	validator := NewValidator()

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
	}

	suggestions := validator.Suggest("show", tokens)

	if len(suggestions) == 0 {
		t.Error("Should have suggestions for verb-only input")
	}

	// Should suggest resources
	foundResource := false
	for _, sug := range suggestions {
		if strings.Contains(sug.Text, "pods") ||
			strings.Contains(sug.Text, "deployments") ||
			strings.Contains(sug.Text, "services") {
			foundResource = true
			break
		}
	}

	if !foundResource {
		t.Error("Should suggest resource types")
	}
}

func TestValidator_Suggest_ResourceWithoutVerb(t *testing.T) {
	validator := NewValidator()

	tokens := []nlp.Token{
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
	}

	suggestions := validator.Suggest("pods", tokens)

	if len(suggestions) == 0 {
		t.Error("Should have suggestions for resource-only input")
	}

	// Should suggest verbs
	foundVerb := false
	for _, sug := range suggestions {
		if strings.Contains(sug.Text, "show") ||
			strings.Contains(sug.Text, "describe") {
			foundVerb = true
			break
		}
	}

	if !foundVerb {
		t.Error("Should suggest verbs for resource")
	}
}

func TestValidator_SuggestCorrections_UnknownVerb(t *testing.T) {
	validator := NewValidator()

	input := "lst pods"
	parseError := fmt.Errorf("Unknown verb: lst")

	suggestions := validator.SuggestCorrections(input, parseError)

	if len(suggestions) == 0 {
		t.Error("Should have corrections for unknown verb")
	}
}

func TestValidator_SuggestCorrections_UnknownResource(t *testing.T) {
	validator := NewValidator()

	input := "show unknown"
	parseError := fmt.Errorf("Unknown resource: unknown")

	suggestions := validator.SuggestCorrections(input, parseError)

	if len(suggestions) == 0 {
		t.Error("Should have corrections for unknown resource")
	}
}

func TestValidator_FindClosestMatch(t *testing.T) {
	validator := NewValidator()

	tests := []struct {
		input      string
		candidates []string
		expected   string
	}{
		{"lst", []string{"list", "get", "show"}, "list"},
		{"gte", []string{"get", "list", "show"}, "get"},
		{"k8", []string{"k8s", "security", "workflow"}, "k8s"},
		{"xyz", []string{"abc", "def", "ghi"}, ""}, // Too different
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result := validator.findClosestMatch(tt.input, tt.candidates)
			if result != tt.expected {
				t.Errorf("findClosestMatch(%q, %v) = %q, want %q",
					tt.input, tt.candidates, result, tt.expected)
			}
		})
	}
}

func TestValidator_FindClosestMatch_EmptyCandidates(t *testing.T) {
	validator := NewValidator()

	result := validator.findClosestMatch("test", []string{})
	if result != "" {
		t.Errorf("findClosestMatch with empty candidates should return empty string, got %q", result)
	}
}

func TestValidator_IsDangerous(t *testing.T) {
	validator := NewValidator()

	dangerousOps := []string{"delete", "remove", "destroy", "kill"}
	for _, op := range dangerousOps {
		if !validator.isDangerous(op) {
			t.Errorf("Operation '%s' should be dangerous", op)
		}
	}

	safeOps := []string{"get", "list", "show", "describe"}
	for _, op := range safeOps {
		if validator.isDangerous(op) {
			t.Errorf("Operation '%s' should not be dangerous", op)
		}
	}
}

func TestValidator_LevenshteinDistance(t *testing.T) {
	tests := []struct {
		s1       string
		s2       string
		expected int
	}{
		{"", "", 0},
		{"a", "", 1},
		{"", "a", 1},
		{"abc", "abc", 0},
		{"abc", "abd", 1},
		{"list", "lst", 1},
		{"kitten", "sitting", 3},
	}

	for _, tt := range tests {
		t.Run(tt.s1+"_"+tt.s2, func(t *testing.T) {
			dist := levenshteinDistance(tt.s1, tt.s2)
			if dist != tt.expected {
				t.Errorf("levenshteinDistance(%q, %q) = %d, want %d",
					tt.s1, tt.s2, dist, tt.expected)
			}
		})
	}
}

func TestValidator_String(t *testing.T) {
	validator := NewValidator()

	str := validator.String()
	if str == "" {
		t.Error("String() should not be empty")
	}

	if !strings.Contains(str, "Validator") {
		t.Error("String() should contain 'Validator'")
	}
}

func TestValidator_AllSubsystems(t *testing.T) {
	validator := NewValidator()

	subsystems := []string{"k8s", "security", "workflow"}

	for _, subsystem := range subsystems {
		t.Run(subsystem, func(t *testing.T) {
			cmd := &nlp.Command{
				Path: []string{subsystem, "get"},
			}

			// Adjust verb for non-k8s subsystems
			if subsystem == "security" {
				cmd.Path[1] = "scan"
			} else if subsystem == "workflow" {
				cmd.Path[1] = "execute"
			}

			result, err := validator.ValidateCommand(cmd)
			if err != nil {
				t.Fatalf("ValidateCommand() error = %v", err)
			}

			if !result.Valid {
				t.Errorf("Valid %s command should pass, got error: %s",
					subsystem, result.Error)
			}
		})
	}
}

func TestValidator_ValidationResult_AllFields(t *testing.T) {
	result := &ValidationResult{
		Valid:                true,
		Error:                "test error",
		Warnings:             []string{"warning1", "warning2"},
		Suggestions:          []string{"suggestion1"},
		Dangerous:            true,
		RequiresConfirmation: true,
	}

	if !result.Valid {
		t.Error("Valid field not set correctly")
	}

	if result.Error != "test error" {
		t.Error("Error field not set correctly")
	}

	if len(result.Warnings) != 2 {
		t.Error("Warnings not set correctly")
	}

	if len(result.Suggestions) != 1 {
		t.Error("Suggestions not set correctly")
	}

	if !result.Dangerous {
		t.Error("Dangerous field not set correctly")
	}

	if !result.RequiresConfirmation {
		t.Error("RequiresConfirmation field not set correctly")
	}
}

func TestValidator_Suggestion_AllFields(t *testing.T) {
	sug := Suggestion{
		Text:        "show pods",
		Description: "List all pods",
		Confidence:  0.95,
	}

	if sug.Text != "show pods" {
		t.Error("Text field not set correctly")
	}

	if sug.Description != "List all pods" {
		t.Error("Description field not set correctly")
	}

	if sug.Confidence != 0.95 {
		t.Error("Confidence field not set correctly")
	}
}

func BenchmarkValidator_ValidateCommand(b *testing.B) {
	validator := NewValidator()

	cmd := &nlp.Command{
		Path: []string{"k8s", "get", "pods"},
		Flags: map[string]string{
			"-n": "prod",
		},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = validator.ValidateCommand(cmd)
	}
}

func BenchmarkValidator_ValidateIntent(b *testing.B) {
	validator := NewValidator()

	intent := &nlp.Intent{
		Verb:       "show",
		Target:     "pods",
		Category:   nlp.IntentCategoryQUERY,
		Confidence: 0.95,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = validator.ValidateIntent(intent)
	}
}
