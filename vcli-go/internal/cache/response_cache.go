package cache

import (
	"sync"
	"time"
)

// MemoryCacheEntry represents a cached response with expiry
type MemoryCacheEntry struct {
	Data      []byte
	ExpiresAt time.Time
}

// ResponseCache is a simple in-memory cache with TTL
type ResponseCache struct {
	mu      sync.RWMutex
	entries map[string]*MemoryCacheEntry
	ttl     time.Duration
}

// NewResponseCache creates a new response cache
func NewResponseCache(ttl time.Duration) *ResponseCache {
	cache := &ResponseCache{
		entries: make(map[string]*MemoryCacheEntry),
		ttl:     ttl,
	}

	// Start background cleanup goroutine
	go cache.cleanup()

	return cache
}

// Get retrieves a cached entry if it exists and hasn't expired
func (c *ResponseCache) Get(key string) ([]byte, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	entry, exists := c.entries[key]
	if !exists {
		return nil, false
	}

	// Check if expired
	if time.Now().After(entry.ExpiresAt) {
		return nil, false
	}

	return entry.Data, true
}

// Set stores a response in the cache
func (c *ResponseCache) Set(key string, data []byte) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.entries[key] = &MemoryCacheEntry{
		Data:      data,
		ExpiresAt: time.Now().Add(c.ttl),
	}
}

// Delete removes an entry from the cache
func (c *ResponseCache) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	delete(c.entries, key)
}

// Clear removes all entries from the cache
func (c *ResponseCache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.entries = make(map[string]*MemoryCacheEntry)
}

// Size returns the number of entries in the cache
func (c *ResponseCache) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()

	return len(c.entries)
}

// cleanup periodically removes expired entries
func (c *ResponseCache) cleanup() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		c.mu.Lock()
		now := time.Now()
		for key, entry := range c.entries {
			if now.After(entry.ExpiresAt) {
				delete(c.entries, key)
			}
		}
		c.mu.Unlock()
	}
}
