package cache

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/dgraph-io/badger/v4"
)

// Cache provides persistent caching with BadgerDB
type Cache struct {
	db       *badger.DB
	basePath string

	// Metrics
	hits   int64
	misses int64
	size   int64
}

// CacheEntry represents a cached value with metadata
type CacheEntry struct {
	Key       string      `json:"key"`
	Value     interface{} `json:"value"`
	ExpiresAt time.Time   `json:"expires_at"`
	CreatedAt time.Time   `json:"created_at"`
	Category  string      `json:"category"` // hot, warm, cold
}

// NewCache creates a new BadgerDB cache
func NewCache(basePath string) (*Cache, error) {
	// Create cache directory
	cachePath := filepath.Join(basePath, "cache")
	if err := os.MkdirAll(cachePath, 0755); err != nil {
		return nil, fmt.Errorf("failed to create cache directory: %w", err)
	}

	// Open BadgerDB
	opts := badger.DefaultOptions(cachePath)
	opts.Logger = nil // Disable BadgerDB logging

	db, err := badger.Open(opts)
	if err != nil {
		return nil, fmt.Errorf("failed to open cache database: %w", err)
	}

	return &Cache{
		db:       db,
		basePath: basePath,
	}, nil
}

// Close closes the cache database
func (c *Cache) Close() error {
	return c.db.Close()
}

// Set stores a value in the cache with TTL
func (c *Cache) Set(key string, value interface{}, ttl time.Duration) error {
	entry := CacheEntry{
		Key:       key,
		Value:     value,
		ExpiresAt: time.Now().Add(ttl),
		CreatedAt: time.Now(),
		Category:  categorizeByTTL(ttl),
	}

	data, err := json.Marshal(entry)
	if err != nil {
		return fmt.Errorf("failed to marshal entry: %w", err)
	}

	err = c.db.Update(func(txn *badger.Txn) error {
		e := badger.NewEntry([]byte(key), data).WithTTL(ttl)
		return txn.SetEntry(e)
	})

	if err != nil {
		return fmt.Errorf("failed to set cache entry: %w", err)
	}

	c.size++
	return nil
}

// Get retrieves a value from the cache
func (c *Cache) Get(key string, dest interface{}) error {
	var entry CacheEntry

	err := c.db.View(func(txn *badger.Txn) error {
		item, err := txn.Get([]byte(key))
		if err != nil {
			return err
		}

		return item.Value(func(val []byte) error {
			return json.Unmarshal(val, &entry)
		})
	})

	if err == badger.ErrKeyNotFound {
		c.misses++
		return ErrCacheMiss
	}
	if err != nil {
		c.misses++
		return fmt.Errorf("failed to get cache entry: %w", err)
	}

	// Check if expired (double-check, BadgerDB should handle this)
	if time.Now().After(entry.ExpiresAt) {
		c.misses++
		return ErrCacheExpired
	}

	// Unmarshal value into destination
	valueJSON, err := json.Marshal(entry.Value)
	if err != nil {
		return fmt.Errorf("failed to marshal value: %w", err)
	}

	if err := json.Unmarshal(valueJSON, dest); err != nil {
		return fmt.Errorf("failed to unmarshal into destination: %w", err)
	}

	c.hits++
	return nil
}

// Delete removes a key from the cache
func (c *Cache) Delete(key string) error {
	err := c.db.Update(func(txn *badger.Txn) error {
		return txn.Delete([]byte(key))
	})

	if err != nil {
		return fmt.Errorf("failed to delete cache entry: %w", err)
	}

	c.size--
	return nil
}

// DeletePrefix removes all keys with a given prefix
func (c *Cache) DeletePrefix(prefix string) error {
	var keys []string

	// Collect keys to delete
	err := c.db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.PrefetchValues = false
		it := txn.NewIterator(opts)
		defer it.Close()

		prefixBytes := []byte(prefix)
		for it.Seek(prefixBytes); it.ValidForPrefix(prefixBytes); it.Next() {
			key := string(it.Item().Key())
			keys = append(keys, key)
		}
		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to scan cache: %w", err)
	}

	// Delete collected keys
	for _, key := range keys {
		if err := c.Delete(key); err != nil {
			return err
		}
	}

	return nil
}

// Clear removes all entries from the cache
func (c *Cache) Clear() error {
	return c.db.DropAll()
}

// GetMetrics returns cache hit/miss metrics
func (c *Cache) GetMetrics() (hits, misses, size int64, hitRate float64) {
	total := c.hits + c.misses
	if total > 0 {
		hitRate = float64(c.hits) / float64(total) * 100
	}
	return c.hits, c.misses, c.size, hitRate
}

// ListKeys returns all keys in the cache
func (c *Cache) ListKeys(prefix string) ([]string, error) {
	var keys []string

	err := c.db.View(func(txn *badger.Txn) error {
		opts := badger.DefaultIteratorOptions
		opts.PrefetchValues = false
		it := txn.NewIterator(opts)
		defer it.Close()

		if prefix != "" {
			prefixBytes := []byte(prefix)
			for it.Seek(prefixBytes); it.ValidForPrefix(prefixBytes); it.Next() {
				keys = append(keys, string(it.Item().Key()))
			}
		} else {
			for it.Rewind(); it.Valid(); it.Next() {
				keys = append(keys, string(it.Item().Key()))
			}
		}
		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to list keys: %w", err)
	}

	return keys, nil
}

// GetInfo returns detailed info about a cached entry
func (c *Cache) GetInfo(key string) (*CacheEntry, error) {
	var entry CacheEntry

	err := c.db.View(func(txn *badger.Txn) error {
		item, err := txn.Get([]byte(key))
		if err != nil {
			return err
		}

		return item.Value(func(val []byte) error {
			return json.Unmarshal(val, &entry)
		})
	})

	if err == badger.ErrKeyNotFound {
		return nil, ErrCacheMiss
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get cache info: %w", err)
	}

	return &entry, nil
}

// RunGC runs garbage collection on the cache
func (c *Cache) RunGC() error {
	return c.db.RunValueLogGC(0.5)
}

// ============================================================
// Helper Functions
// ============================================================

func categorizeByTTL(ttl time.Duration) string {
	switch {
	case ttl <= 5*time.Minute:
		return "hot" // 5min TTL
	case ttl <= 1*time.Hour:
		return "warm" // 1h TTL
	default:
		return "cold" // 24h+ TTL
	}
}

// Common cache errors
var (
	ErrCacheMiss    = fmt.Errorf("cache miss")
	ErrCacheExpired = fmt.Errorf("cache entry expired")
)
