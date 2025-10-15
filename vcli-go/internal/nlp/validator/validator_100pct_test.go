package validator

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/verticedev/vcli-go/pkg/nlp"
)

// ============================================================================
// 100% COVERAGE SURGICAL TESTS - PADRÃO PAGANI ABSOLUTO
// ============================================================================
// These tests target the 3 uncovered blocks (2.7% remaining) to achieve 100%.

// TestValidateCommand_UnknownSubsystem_WithSuggestion tests lines 63-65
// Coverage target: findClosestMatch returns non-empty suggestion (distance ≤ 2)
func TestValidateCommand_UnknownSubsystem_WithSuggestion(t *testing.T) {
	v := NewValidator()

	// Use subsystem "k8" which has edit distance 1 from "k8s"
	cmd := &nlp.Command{
		Path: []string{"k8"}, // Distance 1 from "k8s"
	}

	result, err := v.ValidateCommand(cmd)

	assert.NoError(t, err)
	assert.False(t, result.Valid)
	assert.Contains(t, result.Error, "Unknown subsystem: k8")
	// Lines 63-65: closest != "" → suggests "k8s"
	assert.NotEmpty(t, result.Suggestions)
	assert.Contains(t, result.Suggestions[0], "k8s")
}

// TestSuggest_ResourceWithoutVerb tests lines 182-184
// Coverage target: Resource-only input (no verb detected), executes break statement
func TestSuggest_ResourceWithoutVerb(t *testing.T) {
	v := NewValidator()

	// Tokens with NOUN but no VERB - this will trigger the break statement at line 78
	// The loop finds a NOUN token, adds suggestions, then breaks
	tokens := []nlp.Token{
		{
			Type:       nlp.TokenTypeNOUN,
			Raw:        "pods",
			Normalized: "pods",
		},
	}

	suggestions := v.Suggest("pods", tokens)

	// Lines 66-78: hasVerb == false, finds NOUN, adds "show <resource>" + "describe <resource>", then breaks
	assert.Len(t, suggestions, 2, "Should have exactly 2 suggestions (show and describe)")
	assert.Contains(t, suggestions[0].Text, "show pods")
	assert.Contains(t, suggestions[0].Description, "List pods")
	assert.Equal(t, 0.9, suggestions[0].Confidence)
	assert.Contains(t, suggestions[1].Text, "describe pods")
	assert.Contains(t, suggestions[1].Description, "Describe pods details")
	assert.Equal(t, 0.85, suggestions[1].Confidence)
}

// TestCheckRequiredFlags_ShortPath tests lines 244-246
// Coverage target: Early return when cmd.Path length < 2
func TestCheckRequiredFlags_ShortPath(t *testing.T) {
	v := NewValidator()

	// Command with only subsystem (no verb)
	cmd := &nlp.Command{
		Path: []string{"k8s"},
	}

	result := &ValidationResult{
		Valid:       true,
		Warnings:    make([]string, 0),
		Suggestions: make([]string, 0),
	}

	// Lines 244-246: len(cmd.Path) < 2 → early return
	v.checkRequiredFlags(cmd, result)

	// No warnings or errors should be added
	assert.Empty(t, result.Warnings)
	assert.Empty(t, result.Suggestions)
	assert.True(t, result.Valid)
}
