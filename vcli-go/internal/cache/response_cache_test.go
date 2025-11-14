package cache

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewResponseCache verifies cache creation
func TestNewResponseCache(t *testing.T) {
	cache := NewResponseCache(5 * time.Minute)
	assert.NotNil(t, cache)
	assert.NotNil(t, cache.entries)
	assert.Equal(t, 5*time.Minute, cache.ttl)
}

// TestResponseCache_SetGet verifies basic set/get
func TestResponseCache_SetGet(t *testing.T) {
	cache := NewResponseCache(1 * time.Hour)

	data := []byte("test data")
	cache.Set("test:key", data)

	retrieved, exists := cache.Get("test:key")
	require.True(t, exists)
	assert.Equal(t, data, retrieved)
}

// TestResponseCache_GetNonExistent verifies missing key
func TestResponseCache_GetNonExistent(t *testing.T) {
	cache := NewResponseCache(1 * time.Hour)

	data, exists := cache.Get("nonexistent")
	assert.False(t, exists)
	assert.Nil(t, data)
}

// TestResponseCache_Expiry verifies TTL expiration
func TestResponseCache_Expiry(t *testing.T) {
	cache := NewResponseCache(100 * time.Millisecond)

	cache.Set("test:expiry", []byte("data"))

	// Immediate get works
	_, exists := cache.Get("test:expiry")
	assert.True(t, exists)

	// Wait for expiry
	time.Sleep(150 * time.Millisecond)

	// Should be expired
	_, exists = cache.Get("test:expiry")
	assert.False(t, exists)
}

// TestResponseCache_Delete verifies deletion
func TestResponseCache_Delete(t *testing.T) {
	cache := NewResponseCache(1 * time.Hour)

	cache.Set("test:delete", []byte("data"))
	_, exists := cache.Get("test:delete")
	require.True(t, exists)

	cache.Delete("test:delete")

	_, exists = cache.Get("test:delete")
	assert.False(t, exists)
}

// TestResponseCache_Clear verifies clearing all entries
func TestResponseCache_Clear(t *testing.T) {
	cache := NewResponseCache(1 * time.Hour)

	cache.Set("key1", []byte("data1"))
	cache.Set("key2", []byte("data2"))
	cache.Set("key3", []byte("data3"))

	assert.Equal(t, 3, cache.Size())

	cache.Clear()

	assert.Equal(t, 0, cache.Size())
}

// TestResponseCache_Size verifies size tracking
func TestResponseCache_Size(t *testing.T) {
	cache := NewResponseCache(1 * time.Hour)

	assert.Equal(t, 0, cache.Size())

	cache.Set("key1", []byte("data1"))
	assert.Equal(t, 1, cache.Size())

	cache.Set("key2", []byte("data2"))
	assert.Equal(t, 2, cache.Size())

	cache.Delete("key1")
	assert.Equal(t, 1, cache.Size())
}

// TestResponseCache_Overwrite verifies overwriting entries
func TestResponseCache_Overwrite(t *testing.T) {
	cache := NewResponseCache(1 * time.Hour)

	cache.Set("key", []byte("original"))
	cache.Set("key", []byte("updated"))

	data, exists := cache.Get("key")
	require.True(t, exists)
	assert.Equal(t, []byte("updated"), data)
}

// TestResponseCache_ConcurrentAccess verifies thread-safety
func TestResponseCache_ConcurrentAccess(t *testing.T) {
	cache := NewResponseCache(1 * time.Hour)

	done := make(chan bool)

	// Concurrent writes
	for i := 0; i < 10; i++ {
		go func(id int) {
			for j := 0; j < 100; j++ {
				cache.Set("key", []byte("data"))
			}
			done <- true
		}(i)
	}

	// Concurrent reads
	for i := 0; i < 10; i++ {
		go func() {
			for j := 0; j < 100; j++ {
				cache.Get("key")
			}
			done <- true
		}()
	}

	// Wait for all goroutines
	for i := 0; i < 20; i++ {
		<-done
	}
}

// BenchmarkResponseCache_Set measures Set performance
func BenchmarkResponseCache_Set(b *testing.B) {
	cache := NewResponseCache(1 * time.Hour)
	data := []byte("test data")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cache.Set("key", data)
	}
}

// BenchmarkResponseCache_Get measures Get performance
func BenchmarkResponseCache_Get(b *testing.B) {
	cache := NewResponseCache(1 * time.Hour)
	cache.Set("key", []byte("test data"))

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		cache.Get("key")
	}
}
