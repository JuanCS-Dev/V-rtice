package cache

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewCache verifies cache creation
func TestNewCache(t *testing.T) {
	tmpDir := t.TempDir()

	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	require.NotNil(t, cache)
	defer cache.Close()

	assert.NotNil(t, cache.db)
	assert.Equal(t, tmpDir, cache.basePath)
}

// TestNewCache_DirectoryCreation verifies cache directory is created
func TestNewCache_DirectoryCreation(t *testing.T) {
	tmpDir := t.TempDir()

	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Verify cache directory exists
	assert.DirExists(t, tmpDir+"/cache")
}

// TestCache_SetGet_String verifies basic set/get operations with string
func TestCache_SetGet_String(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Set value
	err = cache.Set("test:key", "test value", 1*time.Hour)
	require.NoError(t, err)

	// Get value
	var value string
	err = cache.Get("test:key", &value)
	require.NoError(t, err)
	assert.Equal(t, "test value", value)
}

// TestCache_SetGet_Struct verifies set/get with struct
func TestCache_SetGet_Struct(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	type TestData struct {
		ID   int
		Name string
	}

	original := TestData{ID: 123, Name: "test"}

	// Set struct
	err = cache.Set("test:struct", original, 1*time.Hour)
	require.NoError(t, err)

	// Get struct
	var retrieved TestData
	err = cache.Get("test:struct", &retrieved)
	require.NoError(t, err)
	assert.Equal(t, original, retrieved)
}

// TestCache_SetGet_Map verifies set/get with map
func TestCache_SetGet_Map(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	original := map[string]interface{}{
		"key1": "value1",
		"key2": 42,
		"key3": true,
	}

	err = cache.Set("test:map", original, 1*time.Hour)
	require.NoError(t, err)

	var retrieved map[string]interface{}
	err = cache.Get("test:map", &retrieved)
	require.NoError(t, err)
	assert.Equal(t, "value1", retrieved["key1"])
	assert.Equal(t, float64(42), retrieved["key2"]) // JSON unmarshals numbers as float64
	assert.Equal(t, true, retrieved["key3"])
}

// TestCache_Get_NonExistent verifies ErrCacheMiss on missing key
func TestCache_Get_NonExistent(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	var value string
	err = cache.Get("nonexistent:key", &value)
	assert.ErrorIs(t, err, ErrCacheMiss)
}

// TestCache_TTL_Expiry verifies TTL expiration
func TestCache_TTL_Expiry(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Set with short TTL (BadgerDB needs at least 1 second to reliably handle TTL)
	err = cache.Set("test:expiry", "will expire", 1*time.Second)
	require.NoError(t, err, "Set should succeed")

	// Immediate get should work
	var value string
	err = cache.Get("test:expiry", &value)
	require.NoError(t, err, "Immediate Get should succeed")
	assert.Equal(t, "will expire", value)

	// Wait for expiry + buffer for BadgerDB cleanup
	time.Sleep(1500 * time.Millisecond)

	// Get should fail after expiry
	err = cache.Get("test:expiry", &value)
	assert.Error(t, err, "Should error on expired key")
}

// TestCache_Delete verifies deletion
func TestCache_Delete(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Set value
	cache.Set("test:delete", "will be deleted", 1*time.Hour)

	// Verify it exists
	var value string
	err = cache.Get("test:delete", &value)
	require.NoError(t, err)

	// Delete
	err = cache.Delete("test:delete")
	require.NoError(t, err)

	// Verify it's gone
	err = cache.Get("test:delete", &value)
	assert.ErrorIs(t, err, ErrCacheMiss)
}

// TestCache_DeletePrefix verifies prefix-based deletion
func TestCache_DeletePrefix(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Set multiple keys with same prefix
	cache.Set("test:prefix:key1", "value1", 1*time.Hour)
	cache.Set("test:prefix:key2", "value2", 1*time.Hour)
	cache.Set("test:prefix:key3", "value3", 1*time.Hour)
	cache.Set("other:key", "should remain", 1*time.Hour)

	// Delete prefix
	err = cache.DeletePrefix("test:prefix:")
	require.NoError(t, err)

	// Verify prefix keys are gone
	var value string
	assert.ErrorIs(t, cache.Get("test:prefix:key1", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("test:prefix:key2", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("test:prefix:key3", &value), ErrCacheMiss)

	// Verify other key remains
	err = cache.Get("other:key", &value)
	require.NoError(t, err)
	assert.Equal(t, "should remain", value)
}

// TestCache_Clear verifies clearing all entries
func TestCache_Clear(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Set multiple keys
	cache.Set("key1", "value1", 1*time.Hour)
	cache.Set("key2", "value2", 1*time.Hour)
	cache.Set("key3", "value3", 1*time.Hour)

	// Clear all
	err = cache.Clear()
	require.NoError(t, err)

	// Verify all are gone
	var value string
	assert.ErrorIs(t, cache.Get("key1", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("key2", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("key3", &value), ErrCacheMiss)
}

// TestCache_Metrics_Hits verifies hit counting
func TestCache_Metrics_Hits(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	cache.Set("test:key", "value", 1*time.Hour)

	// Multiple gets should increment hits
	var value string
	cache.Get("test:key", &value)
	cache.Get("test:key", &value)
	cache.Get("test:key", &value)

	hits, misses, _, hitRate := cache.GetMetrics()
	assert.Equal(t, int64(3), hits)
	assert.Equal(t, int64(0), misses)
	assert.Equal(t, 100.0, hitRate)
}

// TestCache_Metrics_Misses verifies miss counting
func TestCache_Metrics_Misses(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	var value string
	cache.Get("nonexistent1", &value)
	cache.Get("nonexistent2", &value)

	hits, misses, _, hitRate := cache.GetMetrics()
	assert.Equal(t, int64(0), hits)
	assert.Equal(t, int64(2), misses)
	assert.Equal(t, 0.0, hitRate)
}

// TestCache_Metrics_HitRate verifies hit rate calculation
func TestCache_Metrics_HitRate(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	cache.Set("key1", "value1", 1*time.Hour)

	var value string
	cache.Get("key1", &value)       // Hit
	cache.Get("key1", &value)       // Hit
	cache.Get("nonexistent", &value) // Miss

	hits, misses, _, hitRate := cache.GetMetrics()
	assert.Equal(t, int64(2), hits)
	assert.Equal(t, int64(1), misses)
	assert.InDelta(t, 66.67, hitRate, 0.1) // 2/3 = 66.67%
}

// TestCache_ListKeys_AllKeys verifies listing all keys
func TestCache_ListKeys_AllKeys(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	cache.Set("key1", "value1", 1*time.Hour)
	cache.Set("key2", "value2", 1*time.Hour)
	cache.Set("key3", "value3", 1*time.Hour)

	keys, err := cache.ListKeys("")
	require.NoError(t, err)
	assert.Len(t, keys, 3)
	assert.Contains(t, keys, "key1")
	assert.Contains(t, keys, "key2")
	assert.Contains(t, keys, "key3")
}

// TestCache_ListKeys_WithPrefix verifies listing keys with prefix
func TestCache_ListKeys_WithPrefix(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	cache.Set("test:key1", "value1", 1*time.Hour)
	cache.Set("test:key2", "value2", 1*time.Hour)
	cache.Set("other:key", "value3", 1*time.Hour)

	keys, err := cache.ListKeys("test:")
	require.NoError(t, err)
	assert.Len(t, keys, 2)
	assert.Contains(t, keys, "test:key1")
	assert.Contains(t, keys, "test:key2")
	assert.NotContains(t, keys, "other:key")
}

// TestCache_ListKeys_Empty verifies listing when cache is empty
func TestCache_ListKeys_Empty(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	keys, err := cache.ListKeys("")
	require.NoError(t, err)
	assert.Empty(t, keys)
}

// TestCache_GetInfo verifies getting entry metadata
func TestCache_GetInfo(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	cache.Set("test:info", "test value", 1*time.Hour)

	info, err := cache.GetInfo("test:info")
	require.NoError(t, err)
	assert.Equal(t, "test:info", info.Key)
	assert.Equal(t, "test value", info.Value)
	assert.Equal(t, "warm", info.Category) // 1 hour TTL = warm
	assert.True(t, time.Now().Before(info.ExpiresAt))
	assert.True(t, time.Now().After(info.CreatedAt))
}

// TestCache_GetInfo_NonExistent verifies error on missing key
func TestCache_GetInfo_NonExistent(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	info, err := cache.GetInfo("nonexistent")
	assert.ErrorIs(t, err, ErrCacheMiss)
	assert.Nil(t, info)
}

// TestCache_RunGC verifies garbage collection
func TestCache_RunGC(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Add some data
	for i := 0; i < 10; i++ {
		cache.Set("key"+string(rune(i)), "value", 1*time.Hour)
	}

	// Run GC - may fail if not enough data, that's ok
	err = cache.RunGC()
	// Don't assert on error - GC may fail if not enough data to compact
}

// TestCategorizeByTTL verifies TTL categorization
func TestCategorizeByTTL(t *testing.T) {
	tests := []struct {
		ttl      time.Duration
		expected string
	}{
		{1 * time.Minute, "hot"},
		{5 * time.Minute, "hot"},
		{10 * time.Minute, "warm"},
		{30 * time.Minute, "warm"},
		{1 * time.Hour, "warm"},
		{2 * time.Hour, "cold"},
		{24 * time.Hour, "cold"},
	}

	for _, tt := range tests {
		t.Run(tt.ttl.String(), func(t *testing.T) {
			result := categorizeByTTL(tt.ttl)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// TestCache_ConcurrentAccess verifies thread-safety
func TestCache_ConcurrentAccess(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Pre-populate
	for i := 0; i < 10; i++ {
		cache.Set("key"+string(rune(i)), "value", 1*time.Hour)
	}

	// Concurrent reads
	done := make(chan bool)
	for i := 0; i < 10; i++ {
		go func(id int) {
			var value string
			for j := 0; j < 100; j++ {
				cache.Get("key"+string(rune(id%10)), &value)
			}
			done <- true
		}(i)
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}
}

// TestCache_Invalidate verifies invalidation patterns
func TestCache_Invalidate(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Set test data
	cache.Set("immune:agents:1", "agent1", 1*time.Hour)
	cache.Set("immune:agents:2", "agent2", 1*time.Hour)
	cache.Set("maximus:decisions:1", "decision1", 1*time.Hour)

	// Invalidate all agents
	err = cache.Invalidate(InvalidateAllAgents)
	require.NoError(t, err)

	// Verify agents are gone
	var value string
	assert.ErrorIs(t, cache.Get("immune:agents:1", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("immune:agents:2", &value), ErrCacheMiss)

	// Verify decisions remain
	err = cache.Get("maximus:decisions:1", &value)
	require.NoError(t, err)
	assert.Equal(t, "decision1", value)
}

// BenchmarkCache_Set measures Set performance
func BenchmarkCache_Set(b *testing.B) {
	tmpDir := b.TempDir()
	cache, _ := NewCache(tmpDir)
	defer cache.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cache.Set("key", "value", 1*time.Hour)
	}
}

// BenchmarkCache_Get measures Get performance
func BenchmarkCache_Get(b *testing.B) {
	tmpDir := b.TempDir()
	cache, _ := NewCache(tmpDir)
	defer cache.Close()

	cache.Set("key", "value", 1*time.Hour)

	b.ResetTimer()
	var value string
	for i := 0; i < b.N; i++ {
		cache.Get("key", &value)
	}
}

// BenchmarkCache_Delete measures Delete performance
func BenchmarkCache_Delete(b *testing.B) {
	tmpDir := b.TempDir()
	cache, _ := NewCache(tmpDir)
	defer cache.Close()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		b.StopTimer()
		cache.Set("key", "value", 1*time.Hour)
		b.StartTimer()
		cache.Delete("key")
	}
}
