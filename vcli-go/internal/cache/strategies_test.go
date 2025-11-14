package cache

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewPrefetcher verifies prefetcher creation
func TestNewPrefetcher(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	prefetcher := NewPrefetcher(cache)
	assert.NotNil(t, prefetcher)
	assert.NotNil(t, prefetcher.cache)
	assert.Len(t, prefetcher.strategies, 3) // hot, warm, cold
}

// TestPrefetchStrategy_WithFetcher verifies strategy execution with fetcher
func TestPrefetchStrategy_WithFetcher(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	prefetcher := NewPrefetcher(cache)

	// Create custom strategy with fetcher
	strategy := PrefetchStrategy{
		Name:        "test",
		Description: "Test strategy",
		TTL:         1 * time.Minute,
		Keys: []CacheKey{
			{
				Key:      "test:key1",
				Category: "hot",
				Fetcher: func(ctx context.Context) (interface{}, error) {
					return "fetched value", nil
				},
			},
		},
	}

	err = prefetcher.PrefetchStrategy(context.Background(), strategy)
	require.NoError(t, err)

	// Verify data was cached
	var value string
	err = cache.Get("test:key1", &value)
	require.NoError(t, err)
	assert.Equal(t, "fetched value", value)
}

// TestPrefetchStrategy_NoFetcher verifies strategy skips keys without fetcher
func TestPrefetchStrategy_NoFetcher(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	prefetcher := NewPrefetcher(cache)

	strategy := PrefetchStrategy{
		Name: "test",
		TTL:  1 * 60,
		Keys: []CacheKey{
			{
				Key:      "test:no:fetcher",
				Category: "hot",
				Fetcher:  nil, // No fetcher
			},
		},
	}

	// Should not error, just skip
	err = prefetcher.PrefetchStrategy(context.Background(), strategy)
	require.NoError(t, err)

	// Verify nothing was cached
	var value string
	err = cache.Get("test:no:fetcher", &value)
	assert.ErrorIs(t, err, ErrCacheMiss)
}

// TestPrefetchStrategy_FetcherError verifies error handling
func TestPrefetchStrategy_FetcherError(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	prefetcher := NewPrefetcher(cache)

	strategy := PrefetchStrategy{
		Name: "test",
		TTL:  1 * 60,
		Keys: []CacheKey{
			{
				Key:      "test:error",
				Category: "hot",
				Fetcher: func(ctx context.Context) (interface{}, error) {
					return nil, fmt.Errorf("fetch error")
				},
			},
		},
	}

	// Should not propagate fetcher errors
	err = prefetcher.PrefetchStrategy(context.Background(), strategy)
	require.NoError(t, err)

	// Verify nothing was cached
	var value string
	err = cache.Get("test:error", &value)
	assert.ErrorIs(t, err, ErrCacheMiss)
}

// TestPrefetchAll verifies prefetching all strategies
func TestPrefetchAll(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	prefetcher := NewPrefetcher(cache)

	// Override strategies with test fetchers
	prefetcher.strategies = []PrefetchStrategy{
		{
			Name: "test1",
			TTL:  1 * time.Hour,
			Keys: []CacheKey{
				{
					Key:      "test:key1",
					Category: "hot",
					Fetcher: func(ctx context.Context) (interface{}, error) {
						return "value1", nil
					},
				},
			},
		},
		{
			Name: "test2",
			TTL:  1 * time.Hour,
			Keys: []CacheKey{
				{
					Key:      "test:key2",
					Category: "warm",
					Fetcher: func(ctx context.Context) (interface{}, error) {
						return "value2", nil
					},
				},
			},
		},
	}

	err = prefetcher.PrefetchAll(context.Background())
	require.NoError(t, err)

	// Verify both were cached
	var value1, value2 string
	require.NoError(t, cache.Get("test:key1", &value1))
	require.NoError(t, cache.Get("test:key2", &value2))
	assert.Equal(t, "value1", value1)
	assert.Equal(t, "value2", value2)
}

// TestBuildAgentListKey verifies agent list key building
func TestBuildAgentListKey(t *testing.T) {
	tests := []struct {
		name         string
		lymphnodeID  string
		agentType    string
		state        string
		expectedKey  string
	}{
		{"all defaults", "", "", "", "immune:agents:all:all:all"},
		{"specific lymphnode", "ln-1", "", "", "immune:agents:ln-1:all:all"},
		{"specific type", "", "cytotoxic", "", "immune:agents:all:cytotoxic:all"},
		{"specific state", "", "", "active", "immune:agents:all:all:active"},
		{"all specific", "ln-1", "helper", "idle", "immune:agents:ln-1:helper:idle"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			key := BuildAgentListKey(tt.lymphnodeID, tt.agentType, tt.state)
			assert.Equal(t, tt.expectedKey, key)
		})
	}
}

// TestBuildAgentKey verifies agent key building
func TestBuildAgentKey(t *testing.T) {
	key := BuildAgentKey("agent-123")
	assert.Equal(t, "immune:agent:agent-123", key)
}

// TestBuildLymphnodeListKey verifies lymphnode list key building
func TestBuildLymphnodeListKey(t *testing.T) {
	tests := []struct {
		zone     string
		expected string
	}{
		{"", "immune:lymphnodes:all"},
		{"zone-1", "immune:lymphnodes:zone-1"},
		{"production", "immune:lymphnodes:production"},
	}

	for _, tt := range tests {
		t.Run(tt.zone, func(t *testing.T) {
			key := BuildLymphnodeListKey(tt.zone)
			assert.Equal(t, tt.expected, key)
		})
	}
}

// TestBuildLymphnodeKey verifies lymphnode key building
func TestBuildLymphnodeKey(t *testing.T) {
	key := BuildLymphnodeKey("ln-456")
	assert.Equal(t, "immune:lymphnode:ln-456", key)
}

// TestBuildDecisionListKey verifies decision list key building
func TestBuildDecisionListKey(t *testing.T) {
	tests := []struct {
		status   string
		expected string
	}{
		{"", "maximus:decisions:all"},
		{"pending", "maximus:decisions:pending"},
		{"approved", "maximus:decisions:approved"},
	}

	for _, tt := range tests {
		t.Run(tt.status, func(t *testing.T) {
			key := BuildDecisionListKey(tt.status)
			assert.Equal(t, tt.expected, key)
		})
	}
}

// TestBuildDecisionKey verifies decision key building
func TestBuildDecisionKey(t *testing.T) {
	key := BuildDecisionKey("dec-789")
	assert.Equal(t, "maximus:decision:dec-789", key)
}

// TestBuildMetricsKey verifies metrics key building
func TestBuildMetricsKey(t *testing.T) {
	key := BuildMetricsKey("cpu_usage", "1h")
	assert.Equal(t, "metrics:cpu_usage:1h", key)
}

// TestBuildGatewayKey verifies gateway key building
func TestBuildGatewayKey(t *testing.T) {
	params := map[string]string{
		"id":   "123",
		"type": "query",
	}

	key := BuildGatewayKey("maximus", "/api/data", params)
	assert.Contains(t, key, "gateway:maximus:/api/data")
	assert.Contains(t, key, "id=123")
	assert.Contains(t, key, "type=query")
}

// TestBuildGatewayKey_NoParams verifies gateway key without params
func TestBuildGatewayKey_NoParams(t *testing.T) {
	key := BuildGatewayKey("service", "/endpoint", nil)
	assert.Equal(t, "gateway:service:/endpoint", key)
}

// TestInvalidatePattern_AllAgents verifies agent invalidation
func TestInvalidatePattern_AllAgents(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	// Set test data
	cache.Set("immune:agents:1", "agent1", 1*time.Hour)
	cache.Set("immune:agents:2", "agent2", 1*time.Hour)
	cache.Set("immune:lymphnodes:1", "ln1", 1*time.Hour)

	// Invalidate all agents
	err = cache.Invalidate(InvalidateAllAgents)
	require.NoError(t, err)

	// Verify agents are gone
	var value string
	assert.ErrorIs(t, cache.Get("immune:agents:1", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("immune:agents:2", &value), ErrCacheMiss)

	// Verify lymphnodes remain
	err = cache.Get("immune:lymphnodes:1", &value)
	require.NoError(t, err)
}

// TestInvalidatePattern_AllLymphnodes verifies lymphnode invalidation
func TestInvalidatePattern_AllLymphnodes(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	cache.Set("immune:lymphnodes:1", "ln1", 1*time.Hour)
	cache.Set("immune:lymphnodes:2", "ln2", 1*time.Hour)
	cache.Set("immune:agents:1", "agent1", 1*time.Hour)

	err = cache.Invalidate(InvalidateAllLymphnodes)
	require.NoError(t, err)

	var value string
	assert.ErrorIs(t, cache.Get("immune:lymphnodes:1", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("immune:lymphnodes:2", &value), ErrCacheMiss)

	// Verify agents remain
	err = cache.Get("immune:agents:1", &value)
	require.NoError(t, err)
}

// TestInvalidatePattern_AllDecisions verifies decision invalidation
func TestInvalidatePattern_AllDecisions(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	cache.Set("maximus:decisions:1", "dec1", 1*time.Hour)
	cache.Set("maximus:decisions:2", "dec2", 1*time.Hour)
	cache.Set("metrics:test", "metric", 1*time.Hour)

	err = cache.Invalidate(InvalidateAllDecisions)
	require.NoError(t, err)

	var value string
	assert.ErrorIs(t, cache.Get("maximus:decisions:1", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("maximus:decisions:2", &value), ErrCacheMiss)

	// Verify metrics remain
	err = cache.Get("metrics:test", &value)
	require.NoError(t, err)
}

// TestInvalidatePattern_AllMetrics verifies metrics invalidation
func TestInvalidatePattern_AllMetrics(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	cache.Set("metrics:cpu", "90%", 1*time.Hour)
	cache.Set("metrics:memory", "80%", 1*time.Hour)
	cache.Set("gateway:test", "data", 1*time.Hour)

	err = cache.Invalidate(InvalidateAllMetrics)
	require.NoError(t, err)

	var value string
	assert.ErrorIs(t, cache.Get("metrics:cpu", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("metrics:memory", &value), ErrCacheMiss)

	// Verify gateway remains
	err = cache.Get("gateway:test", &value)
	require.NoError(t, err)
}

// TestInvalidatePattern_AllGateway verifies gateway invalidation
func TestInvalidatePattern_AllGateway(t *testing.T) {
	tmpDir := t.TempDir()
	cache, err := NewCache(tmpDir)
	require.NoError(t, err)
	defer cache.Close()

	cache.Set("gateway:req1", "data1", 1*time.Hour)
	cache.Set("gateway:req2", "data2", 1*time.Hour)
	cache.Set("immune:agents:1", "agent", 1*time.Hour)

	err = cache.Invalidate(InvalidateAllGateway)
	require.NoError(t, err)

	var value string
	assert.ErrorIs(t, cache.Get("gateway:req1", &value), ErrCacheMiss)
	assert.ErrorIs(t, cache.Get("gateway:req2", &value), ErrCacheMiss)

	// Verify agents remain
	err = cache.Get("immune:agents:1", &value)
	require.NoError(t, err)
}

// TestHotDataStrategy verifies hot data strategy configuration
func TestHotDataStrategy(t *testing.T) {
	assert.Equal(t, "hot", HotDataStrategy.Name)
	assert.Equal(t, 5*time.Minute, HotDataStrategy.TTL)
	assert.NotEmpty(t, HotDataStrategy.Keys)
	assert.Contains(t, HotDataStrategy.Description, "5min TTL")
}

// TestWarmDataStrategy verifies warm data strategy configuration
func TestWarmDataStrategy(t *testing.T) {
	assert.Equal(t, "warm", WarmDataStrategy.Name)
	assert.Equal(t, 1*time.Hour, WarmDataStrategy.TTL)
	assert.NotEmpty(t, WarmDataStrategy.Keys)
	assert.Contains(t, WarmDataStrategy.Description, "1h TTL")
}

// TestColdDataStrategy verifies cold data strategy configuration
func TestColdDataStrategy(t *testing.T) {
	assert.Equal(t, "cold", ColdDataStrategy.Name)
	assert.Equal(t, 24*time.Hour, ColdDataStrategy.TTL)
	assert.NotEmpty(t, ColdDataStrategy.Keys)
	assert.Contains(t, ColdDataStrategy.Description, "24h TTL")
}

// BenchmarkBuildAgentListKey measures key building performance
func BenchmarkBuildAgentListKey(b *testing.B) {
	for i := 0; i < b.N; i++ {
		BuildAgentListKey("ln-1", "cytotoxic", "active")
	}
}

// BenchmarkBuildGatewayKey measures gateway key building
func BenchmarkBuildGatewayKey(b *testing.B) {
	params := map[string]string{
		"id":   "123",
		"type": "query",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		BuildGatewayKey("service", "/endpoint", params)
	}
}
