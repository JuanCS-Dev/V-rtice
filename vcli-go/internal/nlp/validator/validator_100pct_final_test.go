package validator

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/verticedev/vcli-go/pkg/nlp"
)

// ============================================================================
// FINAL 100% COVERAGE - LINE 182-184 - PADRÃO PAGANI ABSOLUTO
// ============================================================================
// This test targets the ACTUAL uncovered line 182-184: the hasVerb detection break

// TestSuggest_HasVerb_DetectionBreak tests lines 182-184
// Coverage target: The `break` statement when detecting a VERB token in the hasVerb loop
func TestSuggest_HasVerb_DetectionBreak(t *testing.T) {
	v := NewValidator()

	// Multiple tokens with at least one VERB
	// This will trigger lines 182-184 (hasVerb = true; break)
	tokens := []nlp.Token{
		{
			Type:       nlp.TokenTypeVERB,
			Raw:        "show",
			Normalized: "show",
		},
		{
			Type:       nlp.TokenTypeNOUN,
			Raw:        "pods",
			Normalized: "pods",
		},
	}

	suggestions := v.Suggest("show pods", tokens)

	// This input has both a verb and resource, so it won't match the
	// "only verb" or "resource without verb" conditions.
	// It should return empty suggestions since it's complete enough.
	assert.Empty(t, suggestions, "Complete input should not generate suggestions")
}
