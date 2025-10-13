// Package learning - Unit tests
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package learning

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

func TestNewEngine(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")

	engine, err := NewEngine(dbPath, 100)
	if err != nil {
		t.Fatalf("NewEngine() error = %v", err)
	}
	defer engine.Close()

	if engine.db == nil {
		t.Error("Engine DB should not be nil")
	}

	if engine.maxCacheSize != 100 {
		t.Errorf("maxCacheSize = %d, want 100", engine.maxCacheSize)
	}

	if !engine.statsEnabled {
		t.Error("Stats should be enabled by default")
	}
}

func TestEngine_LearnPattern(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{
		Verb:   "show",
		Target: "pods",
	}

	command := &nlp.Command{
		Path: []string{"k8s", "get", "pods"},
	}

	err := engine.LearnPattern("show pods", intent, command)
	if err != nil {
		t.Fatalf("LearnPattern() error = %v", err)
	}

	// Verify pattern was stored
	pattern, err := engine.GetPattern("show pods")
	if err != nil {
		t.Fatalf("GetPattern() error = %v", err)
	}

	if pattern.Input != "show pods" {
		t.Errorf("Pattern input = %s, want 'show pods'", pattern.Input)
	}

	if pattern.Frequency != 1 {
		t.Errorf("Pattern frequency = %d, want 1", pattern.Frequency)
	}
}

func TestEngine_LearnPattern_UpdateExisting(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{
		Verb:   "show",
		Target: "pods",
	}

	command := &nlp.Command{
		Path: []string{"k8s", "get", "pods"},
	}

	// Learn pattern twice
	engine.LearnPattern("show pods", intent, command)
	engine.LearnPattern("show pods", intent, command)

	pattern, _ := engine.GetPattern("show pods")

	if pattern.Frequency != 2 {
		t.Errorf("Pattern frequency = %d, want 2", pattern.Frequency)
	}
}

func TestEngine_GetPattern_NotFound(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	_, err := engine.GetPattern("nonexistent")
	if err == nil {
		t.Error("GetPattern() should return error for nonexistent pattern")
	}
}

func TestEngine_GetPattern_CacheHit(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	engine.LearnPattern("show pods", intent, command)

	// First call - cache miss
	engine.GetPattern("show pods")

	// Second call - should be cache hit
	engine.stats.cacheHits = 0
	engine.stats.cacheMisses = 0

	engine.GetPattern("show pods")

	if engine.stats.cacheHits != 1 {
		t.Errorf("Cache hits = %d, want 1", engine.stats.cacheHits)
	}

	if engine.stats.cacheMisses != 0 {
		t.Errorf("Cache misses = %d, want 0", engine.stats.cacheMisses)
	}
}

func TestEngine_FindSimilarPatterns(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	// Learn multiple patterns
	patterns := []string{
		"show pods in production",
		"show deployments",
		"list services",
	}

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	for _, p := range patterns {
		engine.LearnPattern(p, intent, command)
	}

	// Find similar to "show"
	similar, err := engine.FindSimilarPatterns("show pods", 10)
	if err != nil {
		t.Fatalf("FindSimilarPatterns() error = %v", err)
	}

	if len(similar) == 0 {
		t.Error("Should find at least one similar pattern")
	}
}

func TestEngine_RecordFeedback(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	engine.LearnPattern("show pods", intent, command)

	patternID := generatePatternID("show pods")

	feedback := &Feedback{
		PatternID: patternID,
		Input:     "show pods",
		Command:   "k8s get pods",
		Success:   true,
		Accepted:  true,
		Timestamp: time.Now(),
	}

	err := engine.RecordFeedback(feedback)
	if err != nil {
		t.Fatalf("RecordFeedback() error = %v", err)
	}

	if engine.stats.TotalFeedback != 1 {
		t.Errorf("TotalFeedback = %d, want 1", engine.stats.TotalFeedback)
	}
}

func TestEngine_RecordFeedback_UpdatesSuccessRate(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	engine.LearnPattern("show pods", intent, command)

	patternID := generatePatternID("show pods")

	// Record successful feedback
	feedback := &Feedback{
		PatternID: patternID,
		Success:   true,
		Timestamp: time.Now(),
	}
	engine.RecordFeedback(feedback)

	// Record failed feedback
	feedback.Success = false
	engine.RecordFeedback(feedback)

	pattern, _ := engine.GetPattern("show pods")

	// Success rate should be between 0 and 1
	if pattern.SuccessRate < 0 || pattern.SuccessRate > 1 {
		t.Errorf("SuccessRate = %f, want between 0 and 1", pattern.SuccessRate)
	}
}

func TestEngine_GetPopularPatterns(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	// Learn patterns with different frequencies
	engine.LearnPattern("pattern1", intent, command)

	engine.LearnPattern("pattern2", intent, command)
	engine.LearnPattern("pattern2", intent, command)

	engine.LearnPattern("pattern3", intent, command)
	engine.LearnPattern("pattern3", intent, command)
	engine.LearnPattern("pattern3", intent, command)

	popular, err := engine.GetPopularPatterns(3)
	if err != nil {
		t.Fatalf("GetPopularPatterns() error = %v", err)
	}

	if len(popular) != 3 {
		t.Errorf("GetPopularPatterns() returned %d patterns, want 3", len(popular))
	}

	// Should be sorted by frequency (descending)
	if popular[0].Frequency < popular[1].Frequency {
		t.Error("Patterns should be sorted by frequency (descending)")
	}
}

func TestEngine_GetPopularPatterns_Limit(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	// Learn 5 patterns
	for i := 0; i < 5; i++ {
		engine.LearnPattern("pattern"+string(rune(i)), intent, command)
	}

	popular, _ := engine.GetPopularPatterns(2)

	if len(popular) != 2 {
		t.Errorf("GetPopularPatterns(2) returned %d patterns, want 2", len(popular))
	}
}

func TestEngine_GetStats(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	stats := engine.GetStats()

	if stats == nil {
		t.Fatal("GetStats() should not return nil")
	}

	if stats.TotalPatterns != 0 {
		t.Errorf("Initial TotalPatterns = %d, want 0", stats.TotalPatterns)
	}

	// Learn a pattern
	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}
	engine.LearnPattern("show pods", intent, command)

	stats = engine.GetStats()

	if stats.TotalPatterns != 1 {
		t.Errorf("TotalPatterns = %d, want 1", stats.TotalPatterns)
	}
}

func TestEngine_GetStats_CacheHitRate(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	engine.LearnPattern("show pods", intent, command)

	// Clear cache to ensure first call is a miss
	engine.ClearCache()

	// Reset stats
	engine.stats.cacheHits = 0
	engine.stats.cacheMisses = 0

	// First call - miss (not in cache, will load from DB)
	engine.GetPattern("show pods")

	// Second call - hit (now in cache)
	engine.GetPattern("show pods")

	stats := engine.GetStats()

	if stats.CacheHitRate != 0.5 {
		t.Errorf("CacheHitRate = %f, want 0.5 (1 hit, 1 miss)", stats.CacheHitRate)
	}
}

func TestEngine_ClearCache(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	engine.LearnPattern("show pods", intent, command)

	// Get pattern to add to cache
	engine.GetPattern("show pods")

	if len(engine.patternCache) == 0 {
		t.Error("Cache should have at least one entry")
	}

	engine.ClearCache()

	if len(engine.patternCache) != 0 {
		t.Errorf("Cache size = %d after ClearCache(), want 0", len(engine.patternCache))
	}
}

func TestEngine_CacheLRUEviction(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 2) // Small cache
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	// Learn 3 patterns (exceeds cache size)
	engine.LearnPattern("pattern1", intent, command)
	time.Sleep(10 * time.Millisecond)

	engine.LearnPattern("pattern2", intent, command)
	time.Sleep(10 * time.Millisecond)

	engine.LearnPattern("pattern3", intent, command)

	// Cache should have max 2 entries
	if len(engine.patternCache) > 2 {
		t.Errorf("Cache size = %d, want <= 2", len(engine.patternCache))
	}
}

func TestEngine_Close(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)

	err := engine.Close()
	if err != nil {
		t.Errorf("Close() error = %v", err)
	}

	// Verify DB is closed by attempting operation
	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	err = engine.LearnPattern("test", intent, command)
	if err == nil {
		t.Error("Operations after Close() should fail")
	}
}

func TestPattern_Fields(t *testing.T) {
	pattern := &Pattern{
		ID:          "test123",
		Input:       "show pods",
		Intent:      "show:pods",
		Command:     "k8s get pods",
		Frequency:   5,
		SuccessRate: 0.9,
		LastUsed:    time.Now(),
		CreatedAt:   time.Now(),
		UserID:      "user123",
	}

	if pattern.ID != "test123" {
		t.Errorf("ID = %s, want 'test123'", pattern.ID)
	}

	if pattern.Frequency != 5 {
		t.Errorf("Frequency = %d, want 5", pattern.Frequency)
	}

	if pattern.SuccessRate != 0.9 {
		t.Errorf("SuccessRate = %f, want 0.9", pattern.SuccessRate)
	}
}

func TestFeedback_Fields(t *testing.T) {
	feedback := &Feedback{
		PatternID:  "pattern123",
		Input:      "show pods",
		Command:    "k8s get pods",
		Success:    true,
		Accepted:   true,
		Correction: "",
		Timestamp:  time.Now(),
		UserID:     "user123",
	}

	if feedback.PatternID != "pattern123" {
		t.Errorf("PatternID = %s, want 'pattern123'", feedback.PatternID)
	}

	if !feedback.Success {
		t.Error("Success should be true")
	}

	if !feedback.Accepted {
		t.Error("Accepted should be true")
	}
}

func TestGeneratePatternID(t *testing.T) {
	id1 := generatePatternID("show pods")
	id2 := generatePatternID("show pods")
	id3 := generatePatternID("list deployments")

	if id1 != id2 {
		t.Error("Same input should generate same ID")
	}

	if id1 == id3 {
		t.Error("Different inputs should generate different IDs")
	}
}

func TestFormatCommand(t *testing.T) {
	command := &nlp.Command{
		Path:  []string{"k8s", "get", "pods"},
		Args:  []string{"nginx-pod"},
		Flags: map[string]string{"-n": "prod"},
	}

	formatted := formatCommand(command)

	if formatted == "" {
		t.Error("formatCommand() should not return empty string")
	}

	// Should contain all parts
	if !contains(formatted, "k8s") || !contains(formatted, "get") || !contains(formatted, "pods") {
		t.Error("formatCommand() should contain all path elements")
	}
}

func TestIsSimilar(t *testing.T) {
	tests := []struct {
		input1   string
		input2   string
		expected bool
	}{
		{"show pods", "show deployments", true},     // Same prefix (4 chars)
		{"list pods", "get pods", true},             // Same suffix "pods" (one >= 8 chars)
		{"show", "list", false},                     // Too short
		{"pods in production", "services in production", true}, // Same suffix (both >=8 chars)
		{"list deployments", "list services", true}, // Same prefix
		{"abc", "xyz", false},                       // Too short
		{"pods", "services", false},                 // Different, too short for any match
	}

	for _, tt := range tests {
		result := isSimilar(tt.input1, tt.input2)
		if result != tt.expected {
			t.Errorf("isSimilar(%q, %q) = %v, want %v",
				tt.input1, tt.input2, result, tt.expected)
		}
	}
}

func TestEngine_String(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	str := engine.String()

	if str == "" {
		t.Error("String() should not be empty")
	}

	if !contains(str, "LearningEngine") {
		t.Error("String() should contain 'LearningEngine'")
	}
}

func TestEngine_Persistence(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")

	// Create engine and learn pattern
	engine1, _ := NewEngine(dbPath, 100)
	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}
	engine1.LearnPattern("show pods", intent, command)
	engine1.Close()

	// Reopen engine and verify pattern persisted
	engine2, _ := NewEngine(dbPath, 100)
	defer engine2.Close()

	pattern, err := engine2.GetPattern("show pods")
	if err != nil {
		t.Fatalf("Pattern should persist after restart, got error: %v", err)
	}

	if pattern.Input != "show pods" {
		t.Error("Persisted pattern has incorrect data")
	}
}

func TestEngine_ConcurrentAccess(t *testing.T) {
	dbPath := filepath.Join(t.TempDir(), "test_db")
	engine, _ := NewEngine(dbPath, 100)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	done := make(chan bool, 10)

	// Concurrent writes
	for i := 0; i < 10; i++ {
		go func(n int) {
			pattern := "pattern" + string(rune(n))
			engine.LearnPattern(pattern, intent, command)
			done <- true
		}(i)
	}

	// Wait for all writes
	for i := 0; i < 10; i++ {
		<-done
	}

	// Verify all patterns stored
	stats := engine.GetStats()
	if stats.TotalPatterns < 10 {
		t.Errorf("Expected at least 10 patterns, got %d", stats.TotalPatterns)
	}
}

// Helper function
func contains(s, substr string) bool {
	return len(s) >= len(substr) && s[:len(substr)] == substr ||
	       len(s) > len(substr) && findSubstr(s, substr)
}

func findSubstr(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

func BenchmarkEngine_LearnPattern(b *testing.B) {
	dbPath := filepath.Join(os.TempDir(), "bench_db")
	defer os.RemoveAll(dbPath)

	engine, _ := NewEngine(dbPath, 1000)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		engine.LearnPattern("show pods", intent, command)
	}
}

func BenchmarkEngine_GetPattern(b *testing.B) {
	dbPath := filepath.Join(os.TempDir(), "bench_db")
	defer os.RemoveAll(dbPath)

	engine, _ := NewEngine(dbPath, 1000)
	defer engine.Close()

	intent := &nlp.Intent{Verb: "show", Target: "pods"}
	command := &nlp.Command{Path: []string{"k8s", "get", "pods"}}
	engine.LearnPattern("show pods", intent, command)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		engine.GetPattern("show pods")
	}
}
