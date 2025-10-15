package generator

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/verticedev/vcli-go/pkg/nlp"
)

// ============================================================================
// 100% COVERAGE SURGICAL TEST - PADRÃO PAGANI ABSOLUTO
// ============================================================================
// This test targets the 1 uncovered block (2.4% remaining) to achieve 100%.
// Line 230-233: ExplainCommand with --field-selector flag

// TestExplainCommand_WithFieldSelector tests lines 230-233
// Coverage target: ExplainCommand explanation with field-selector filter
func TestExplainCommand_WithFieldSelector(t *testing.T) {
	g := NewGenerator()

	cmd := &nlp.Command{
		Path: []string{"k8s", "get", "pods"},
		Flags: map[string]string{
			"--field-selector": "status.phase!=Running",
		},
	}

	explanation := g.ExplainCommand(cmd)

	// Lines 230-233: "Show pods with status.phase!=Running"
	assert.Contains(t, explanation, "Show")
	assert.Contains(t, explanation, "pods")
	assert.Contains(t, explanation, "with")
	assert.Contains(t, explanation, "status.phase!=Running")
}
