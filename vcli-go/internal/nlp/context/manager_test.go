// Package context - Unit tests
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package context

import (
	"testing"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

func TestManager_CreateSession(t *testing.T) {
	manager := NewManager()

	ctx := manager.CreateSession()

	if ctx == nil {
		t.Fatal("CreateSession() returned nil")
	}

	if ctx.SessionID == "" {
		t.Error("SessionID should not be empty")
	}

	if ctx.CurrentNS != "default" {
		t.Errorf("CurrentNS = %v, want default", ctx.CurrentNS)
	}

	if ctx.History == nil {
		t.Error("History should be initialized")
	}

	if ctx.LastResources == nil {
		t.Error("LastResources should be initialized")
	}

	if ctx.Preferences == nil {
		t.Error("Preferences should be initialized")
	}
}

func TestManager_GetSession(t *testing.T) {
	manager := NewManager()

	// Create session
	ctx1 := manager.CreateSession()

	// Retrieve session
	ctx2, err := manager.GetSession(ctx1.SessionID)
	if err != nil {
		t.Fatalf("GetSession() error = %v", err)
	}

	if ctx2.SessionID != ctx1.SessionID {
		t.Errorf("Got wrong session: %v, want %v", ctx2.SessionID, ctx1.SessionID)
	}
}

func TestManager_GetSession_NotFound(t *testing.T) {
	manager := NewManager()

	_, err := manager.GetSession("nonexistent")
	if err == nil {
		t.Error("Expected error for nonexistent session")
	}
}

func TestManager_GetSession_Expired(t *testing.T) {
	manager := NewManagerWithOptions(50, 1*time.Millisecond)

	ctx := manager.CreateSession()

	// Wait for expiry
	time.Sleep(2 * time.Millisecond)

	_, err := manager.GetSession(ctx.SessionID)
	if err == nil {
		t.Error("Expected error for expired session")
	}
}

func TestManager_UpdateSession(t *testing.T) {
	manager := NewManager()

	ctx := manager.CreateSession()
	originalUpdated := ctx.Updated

	// Modify context
	ctx.CurrentNS = "production"

	// Wait a bit to ensure timestamp changes
	time.Sleep(1 * time.Millisecond)

	// Update session
	err := manager.UpdateSession(ctx)
	if err != nil {
		t.Fatalf("UpdateSession() error = %v", err)
	}

	// Retrieve and verify
	updated, _ := manager.GetSession(ctx.SessionID)
	if updated.CurrentNS != "production" {
		t.Errorf("CurrentNS not updated: got %v", updated.CurrentNS)
	}

	if !updated.Updated.After(originalUpdated) {
		t.Error("Updated timestamp should be newer")
	}
}

func TestManager_UpdateSession_NotFound(t *testing.T) {
	manager := NewManager()

	ctx := &nlp.Context{SessionID: "nonexistent"}
	err := manager.UpdateSession(ctx)
	if err == nil {
		t.Error("Expected error for nonexistent session")
	}
}

func TestManager_DeleteSession(t *testing.T) {
	manager := NewManager()

	ctx := manager.CreateSession()

	// Delete session
	err := manager.DeleteSession(ctx.SessionID)
	if err != nil {
		t.Fatalf("DeleteSession() error = %v", err)
	}

	// Verify deleted
	_, err = manager.GetSession(ctx.SessionID)
	if err == nil {
		t.Error("Session should be deleted")
	}
}

func TestManager_DeleteSession_NotFound(t *testing.T) {
	manager := NewManager()

	err := manager.DeleteSession("nonexistent")
	if err == nil {
		t.Error("Expected error when deleting nonexistent session")
	}
}

func TestManager_AddToHistory(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	entry := nlp.HistoryEntry{
		Input:   "mostra os pods",
		Success: true,
	}

	err := manager.AddToHistory(ctx.SessionID, entry)
	if err != nil {
		t.Fatalf("AddToHistory() error = %v", err)
	}

	// Retrieve and verify
	history, err := manager.GetHistory(ctx.SessionID, 0)
	if err != nil {
		t.Fatalf("GetHistory() error = %v", err)
	}

	if len(history) != 1 {
		t.Errorf("History length = %d, want 1", len(history))
	}

	if history[0].Input != "mostra os pods" {
		t.Errorf("History[0].Input = %v, want 'mostra os pods'", history[0].Input)
	}

	if history[0].Timestamp.IsZero() {
		t.Error("Timestamp should be set")
	}
}

func TestManager_AddToHistory_TrimOldEntries(t *testing.T) {
	manager := NewManagerWithOptions(5, 24*time.Hour)
	ctx := manager.CreateSession()

	// Add 10 entries (more than max)
	for i := 0; i < 10; i++ {
		entry := nlp.HistoryEntry{
			Input:   "command" + string(rune('0'+i)),
			Success: true,
		}
		_ = manager.AddToHistory(ctx.SessionID, entry)
	}

	// Verify only last 5 remain
	history, _ := manager.GetHistory(ctx.SessionID, 0)
	if len(history) != 5 {
		t.Errorf("History length = %d, want 5", len(history))
	}
}

func TestManager_GetHistory_WithLimit(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	// Add 5 entries
	for i := 0; i < 5; i++ {
		entry := nlp.HistoryEntry{Input: "cmd"}
		_ = manager.AddToHistory(ctx.SessionID, entry)
	}

	// Get last 3
	history, err := manager.GetHistory(ctx.SessionID, 3)
	if err != nil {
		t.Fatalf("GetHistory() error = %v", err)
	}

	if len(history) != 3 {
		t.Errorf("History length = %d, want 3", len(history))
	}
}

func TestManager_SetCurrentNamespace(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	err := manager.SetCurrentNamespace(ctx.SessionID, "production")
	if err != nil {
		t.Fatalf("SetCurrentNamespace() error = %v", err)
	}

	updated, _ := manager.GetSession(ctx.SessionID)
	if updated.CurrentNS != "production" {
		t.Errorf("CurrentNS = %v, want production", updated.CurrentNS)
	}
}

func TestManager_SetCurrentResource(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	err := manager.SetCurrentResource(ctx.SessionID, "pods")
	if err != nil {
		t.Fatalf("SetCurrentResource() error = %v", err)
	}

	updated, _ := manager.GetSession(ctx.SessionID)
	if updated.CurrentResource != "pods" {
		t.Errorf("CurrentResource = %v, want pods", updated.CurrentResource)
	}
}

func TestManager_TrackResource(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	err := manager.TrackResource(ctx.SessionID, "pods", "nginx-pod")
	if err != nil {
		t.Fatalf("TrackResource() error = %v", err)
	}

	// Add more resources
	_ = manager.TrackResource(ctx.SessionID, "pods", "redis-pod")

	updated, _ := manager.GetSession(ctx.SessionID)
	resources := updated.LastResources["pods"]

	if len(resources) != 2 {
		t.Errorf("Resources length = %d, want 2", len(resources))
	}

	if resources[0] != "nginx-pod" {
		t.Errorf("First resource = %v, want nginx-pod", resources[0])
	}
}

func TestManager_TrackResource_TrimOld(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	// Add 15 resources (more than max 10)
	for i := 0; i < 15; i++ {
		_ = manager.TrackResource(ctx.SessionID, "pods", "pod-"+string(rune('a'+i)))
	}

	updated, _ := manager.GetSession(ctx.SessionID)
	resources := updated.LastResources["pods"]

	if len(resources) != 10 {
		t.Errorf("Resources length = %d, want 10", len(resources))
	}
}

func TestManager_GetLastResource(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	_ = manager.TrackResource(ctx.SessionID, "deployments", "nginx-deployment")
	_ = manager.TrackResource(ctx.SessionID, "deployments", "redis-deployment")

	resource, err := manager.GetLastResource(ctx.SessionID, "deployments")
	if err != nil {
		t.Fatalf("GetLastResource() error = %v", err)
	}

	if resource != "redis-deployment" {
		t.Errorf("GetLastResource() = %v, want redis-deployment", resource)
	}
}

func TestManager_GetLastResource_NotFound(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	_, err := manager.GetLastResource(ctx.SessionID, "services")
	if err == nil {
		t.Error("Expected error for missing resource type")
	}
}

func TestManager_SetPreference(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	err := manager.SetPreference(ctx.SessionID, "output_format", "json")
	if err != nil {
		t.Fatalf("SetPreference() error = %v", err)
	}

	value, exists := manager.GetPreference(ctx.SessionID, "output_format")
	if !exists {
		t.Error("Preference should exist")
	}

	if value != "json" {
		t.Errorf("Preference value = %v, want json", value)
	}
}

func TestManager_GetPreference_NotFound(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	_, exists := manager.GetPreference(ctx.SessionID, "nonexistent")
	if exists {
		t.Error("Preference should not exist")
	}
}

func TestManager_GetPreference_SessionNotFound(t *testing.T) {
	manager := NewManager()

	_, exists := manager.GetPreference("nonexistent", "key")
	if exists {
		t.Error("Should return false for nonexistent session")
	}
}

func TestManager_ResolveReference(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	// Add command to history
	entry := nlp.HistoryEntry{
		Input:   "show pods nginx",
		Success: true,
		Intent: &nlp.Intent{
			Target: "pods",
		},
	}
	_ = manager.AddToHistory(ctx.SessionID, entry)

	// Track resource
	_ = manager.TrackResource(ctx.SessionID, "pods", "nginx-pod")

	// Resolve reference
	resourceType, resourceName, err := manager.ResolveReference(ctx.SessionID, "it")
	if err != nil {
		t.Fatalf("ResolveReference() error = %v", err)
	}

	if resourceType != "pods" {
		t.Errorf("ResourceType = %v, want pods", resourceType)
	}

	if resourceName != "nginx-pod" {
		t.Errorf("ResourceName = %v, want nginx-pod", resourceName)
	}
}

func TestManager_ResolveReference_NoHistory(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	_, _, err := manager.ResolveReference(ctx.SessionID, "it")
	if err == nil {
		t.Error("Expected error when no history exists")
	}
}

func TestManager_ResolveReference_SessionNotFound(t *testing.T) {
	manager := NewManager()

	_, _, err := manager.ResolveReference("nonexistent", "it")
	if err == nil {
		t.Error("Expected error for nonexistent session")
	}
}

func TestManager_CleanupExpiredSessions(t *testing.T) {
	manager := NewManagerWithOptions(50, 10*time.Millisecond)

	// Create 3 sessions
	_ = manager.CreateSession()
	_ = manager.CreateSession()
	_ = manager.CreateSession()

	// Wait for expiry
	time.Sleep(15 * time.Millisecond)

	// Cleanup
	removed := manager.CleanupExpiredSessions()

	if removed != 3 {
		t.Errorf("CleanupExpiredSessions() removed %d, want 3", removed)
	}

	if manager.GetActiveSessionCount() != 0 {
		t.Errorf("Active sessions = %d, want 0", manager.GetActiveSessionCount())
	}
}

func TestManager_GetActiveSessionCount(t *testing.T) {
	manager := NewManager()

	if manager.GetActiveSessionCount() != 0 {
		t.Error("Initial count should be 0")
	}

	_ = manager.CreateSession()
	_ = manager.CreateSession()

	if manager.GetActiveSessionCount() != 2 {
		t.Errorf("Active sessions = %d, want 2", manager.GetActiveSessionCount())
	}
}

func TestManager_String(t *testing.T) {
	manager := NewManager()

	str := manager.String()
	if str == "" {
		t.Error("String() should not be empty")
	}

	if len(str) < 10 {
		t.Error("String() should contain meaningful information")
	}
}

func TestManager_ConcurrentAccess(t *testing.T) {
	manager := NewManager()
	ctx := manager.CreateSession()

	// Simulate concurrent access
	done := make(chan bool, 10)

	for i := 0; i < 10; i++ {
		go func(n int) {
			entry := nlp.HistoryEntry{Input: "concurrent"}
			_ = manager.AddToHistory(ctx.SessionID, entry)
			done <- true
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}

	// Verify history was safely updated
	history, _ := manager.GetHistory(ctx.SessionID, 0)
	if len(history) != 10 {
		t.Errorf("Concurrent updates resulted in %d entries, want 10", len(history))
	}
}

func TestManager_EdgeCases(t *testing.T) {
	manager := NewManager()

	t.Run("operations on deleted session", func(t *testing.T) {
		ctx := manager.CreateSession()
		_ = manager.DeleteSession(ctx.SessionID)

		err := manager.SetCurrentNamespace(ctx.SessionID, "test")
		if err == nil {
			t.Error("Expected error for deleted session")
		}
	})

	t.Run("empty history retrieval", func(t *testing.T) {
		ctx := manager.CreateSession()
		history, err := manager.GetHistory(ctx.SessionID, 0)
		if err != nil {
			t.Errorf("GetHistory() error = %v", err)
		}
		if len(history) != 0 {
			t.Error("Empty session should return empty history")
		}
	})
}

func BenchmarkManager_CreateSession(b *testing.B) {
	manager := NewManager()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = manager.CreateSession()
	}
}

func BenchmarkManager_AddToHistory(b *testing.B) {
	manager := NewManager()
	ctx := manager.CreateSession()

	entry := nlp.HistoryEntry{
		Input:   "test command",
		Success: true,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = manager.AddToHistory(ctx.SessionID, entry)
	}
}
