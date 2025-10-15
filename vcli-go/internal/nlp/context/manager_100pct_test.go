package context

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/verticedev/vcli-go/pkg/nlp"
)

// ============================================================================
// 100% COVERAGE SURGICAL TESTS - PADRÃO PAGANI ABSOLUTO
// ============================================================================
// These tests target the 9 uncovered lines (6.7% remaining) to achieve 100%.
// All tests focus on error paths with invalid session IDs.

// TestAddToHistory_InvalidSession tests line 118-120
// Error path: AddToHistory with non-existent session ID
func TestAddToHistory_InvalidSession(t *testing.T) {
	m := NewManager()

	entry := nlp.HistoryEntry{
		Input:   "get pods",
		Success: true,
	}

	err := m.AddToHistory("invalid-session-id", entry)

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "session not found")
}

// TestGetHistory_InvalidSession tests line 141-143
// Error path: GetHistory with non-existent session ID
func TestGetHistory_InvalidSession(t *testing.T) {
	m := NewManager()

	history, err := m.GetHistory("invalid-session-id", 10)

	assert.Error(t, err)
	assert.Nil(t, history)
	assert.Contains(t, err.Error(), "session not found")
}

// TestSetCurrentResource_InvalidSession tests line 174-176
// Error path: SetCurrentResource with non-existent session ID
func TestSetCurrentResource_InvalidSession(t *testing.T) {
	m := NewManager()

	err := m.SetCurrentResource("invalid-session-id", "pods")

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "session not found")
}

// TestTrackResource_InvalidSession tests line 189-191
// Error path: TrackResource with non-existent session ID
func TestTrackResource_InvalidSession(t *testing.T) {
	m := NewManager()

	err := m.TrackResource("invalid-session-id", "pod", "nginx-1234")

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "session not found")
}

// TestTrackResource_NilLastResources tests line 194-196
// Edge case: TrackResource with nil LastResources map initialization
func TestTrackResource_NilLastResources(t *testing.T) {
	m := NewManager()
	ctx := m.CreateSession()

	// Manually set LastResources to nil to trigger initialization
	ctx.LastResources = nil
	m.sessions[ctx.SessionID] = ctx

	err := m.TrackResource(ctx.SessionID, "pod", "nginx-1234")

	assert.NoError(t, err)
	assert.NotNil(t, ctx.LastResources)
	assert.Equal(t, 1, len(ctx.LastResources["pod"]))
	assert.Equal(t, "nginx-1234", ctx.LastResources["pod"][0])
}

// TestGetLastResource_InvalidSession tests line 216-218
// Error path: GetLastResource with non-existent session ID
func TestGetLastResource_InvalidSession(t *testing.T) {
	m := NewManager()

	resource, err := m.GetLastResource("invalid-session-id", "pod")

	assert.Error(t, err)
	assert.Empty(t, resource)
	assert.Contains(t, err.Error(), "session not found")
}

// TestSetPreference_InvalidSession tests line 234-236
// Error path: SetPreference with non-existent session ID
func TestSetPreference_InvalidSession(t *testing.T) {
	m := NewManager()

	err := m.SetPreference("invalid-session-id", "output", "yaml")

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "session not found")
}

// TestSetPreference_NilPreferences tests line 238-240
// Edge case: SetPreference with nil Preferences map initialization
func TestSetPreference_NilPreferences(t *testing.T) {
	m := NewManager()
	ctx := m.CreateSession()

	// Manually set Preferences to nil to trigger initialization
	ctx.Preferences = nil
	m.sessions[ctx.SessionID] = ctx

	err := m.SetPreference(ctx.SessionID, "output", "yaml")

	assert.NoError(t, err)
	assert.NotNil(t, ctx.Preferences)
	assert.Equal(t, "yaml", ctx.Preferences["output"])
}

// TestResolveReference_NoResourceName tests line 284
// Edge case: ResolveReference when intent has target but no tracked resources
func TestResolveReference_NoResourceName(t *testing.T) {
	m := NewManager()
	ctx := m.CreateSession()

	// Add history entry with intent but no tracked resources
	entry := nlp.HistoryEntry{
		Input:   "get pods",
		Success: true,
		Intent: &nlp.Intent{
			Verb:   "get",
			Target: "pod",
		},
	}

	// Manually add to history
	ctx.History = append(ctx.History, entry)
	m.sessions[ctx.SessionID] = ctx

	resourceType, resourceName, err := m.ResolveReference(ctx.SessionID, "it")

	assert.NoError(t, err)
	assert.Equal(t, "pod", resourceType)
	assert.Empty(t, resourceName) // Line 284: return resourceType, "", nil
}
