package cache

import (
	"context"
	"fmt"
	"time"
)

// PrefetchStrategy defines a cache prefetch strategy
type PrefetchStrategy struct {
	Name        string
	Description string
	TTL         time.Duration
	Keys        []CacheKey
}

// CacheKey represents a key to be prefetched
type CacheKey struct {
	Key      string
	Fetcher  func(context.Context) (interface{}, error)
	Category string
}

// Predefined strategies
var (
	// HotDataStrategy caches frequently accessed data (5min TTL)
	HotDataStrategy = PrefetchStrategy{
		Name:        "hot",
		Description: "Frequently accessed data (5min TTL)",
		TTL:         5 * time.Minute,
		Keys: []CacheKey{
			{
				Key:      "immune:agents:active",
				Category: "hot",
			},
			{
				Key:      "immune:lymphnodes:status",
				Category: "hot",
			},
			{
				Key:      "maximus:decisions:pending",
				Category: "hot",
			},
		},
	}

	// WarmDataStrategy caches moderately accessed data (1h TTL)
	WarmDataStrategy = PrefetchStrategy{
		Name:        "warm",
		Description: "Moderately accessed data (1h TTL)",
		TTL:         1 * time.Hour,
		Keys: []CacheKey{
			{
				Key:      "immune:agents:all",
				Category: "warm",
			},
			{
				Key:      "maximus:decisions:history",
				Category: "warm",
			},
			{
				Key:      "metrics:system:summary",
				Category: "warm",
			},
		},
	}

	// ColdDataStrategy caches rarely accessed data (24h TTL)
	ColdDataStrategy = PrefetchStrategy{
		Name:        "cold",
		Description: "Rarely accessed data (24h TTL)",
		TTL:         24 * time.Hour,
		Keys: []CacheKey{
			{
				Key:      "config:services",
				Category: "cold",
			},
			{
				Key:      "config:endpoints",
				Category: "cold",
			},
		},
	}
)

// Prefetcher manages cache prefetching
type Prefetcher struct {
	cache      *Cache
	strategies []PrefetchStrategy
}

// NewPrefetcher creates a new cache prefetcher
func NewPrefetcher(cache *Cache) *Prefetcher {
	return &Prefetcher{
		cache: cache,
		strategies: []PrefetchStrategy{
			HotDataStrategy,
			WarmDataStrategy,
			ColdDataStrategy,
		},
	}
}

// PrefetchAll executes all prefetch strategies
func (p *Prefetcher) PrefetchAll(ctx context.Context) error {
	for _, strategy := range p.strategies {
		if err := p.PrefetchStrategy(ctx, strategy); err != nil {
			return fmt.Errorf("failed to prefetch %s: %w", strategy.Name, err)
		}
	}
	return nil
}

// PrefetchStrategy executes a single prefetch strategy
func (p *Prefetcher) PrefetchStrategy(ctx context.Context, strategy PrefetchStrategy) error {
	for _, key := range strategy.Keys {
		// Skip if no fetcher defined
		if key.Fetcher == nil {
			continue
		}

		// Fetch data
		data, err := key.Fetcher(ctx)
		if err != nil {
			// Log error but continue with other keys
			continue
		}

		// Cache data
		if err := p.cache.Set(key.Key, data, strategy.TTL); err != nil {
			return fmt.Errorf("failed to cache %s: %w", key.Key, err)
		}
	}

	return nil
}

// ============================================================
// Cache Key Builders
// ============================================================

// BuildAgentListKey creates a cache key for agent list
func BuildAgentListKey(lymphnodeID, agentType, state string) string {
	if lymphnodeID == "" {
		lymphnodeID = "all"
	}
	if agentType == "" {
		agentType = "all"
	}
	if state == "" {
		state = "all"
	}
	return fmt.Sprintf("immune:agents:%s:%s:%s", lymphnodeID, agentType, state)
}

// BuildAgentKey creates a cache key for a specific agent
func BuildAgentKey(agentID string) string {
	return fmt.Sprintf("immune:agent:%s", agentID)
}

// BuildLymphnodeListKey creates a cache key for lymphnode list
func BuildLymphnodeListKey(zone string) string {
	if zone == "" {
		zone = "all"
	}
	return fmt.Sprintf("immune:lymphnodes:%s", zone)
}

// BuildLymphnodeKey creates a cache key for a specific lymphnode
func BuildLymphnodeKey(lymphnodeID string) string {
	return fmt.Sprintf("immune:lymphnode:%s", lymphnodeID)
}

// BuildDecisionListKey creates a cache key for decision list
func BuildDecisionListKey(status string) string {
	if status == "" {
		status = "all"
	}
	return fmt.Sprintf("maximus:decisions:%s", status)
}

// BuildDecisionKey creates a cache key for a specific decision
func BuildDecisionKey(decisionID string) string {
	return fmt.Sprintf("maximus:decision:%s", decisionID)
}

// BuildMetricsKey creates a cache key for metrics query
func BuildMetricsKey(query, timeRange string) string {
	return fmt.Sprintf("metrics:%s:%s", query, timeRange)
}

// BuildGatewayKey creates a cache key for gateway requests
func BuildGatewayKey(service, endpoint string, params map[string]string) string {
	// Simple key builder - could be more sophisticated
	key := fmt.Sprintf("gateway:%s:%s", service, endpoint)
	for k, v := range params {
		key += fmt.Sprintf(":%s=%s", k, v)
	}
	return key
}

// ============================================================
// Cache Invalidation Patterns
// ============================================================

// InvalidatePattern defines common invalidation patterns
type InvalidatePattern string

const (
	InvalidateAllAgents     InvalidatePattern = "immune:agents:"
	InvalidateAllLymphnodes InvalidatePattern = "immune:lymphnodes:"
	InvalidateAllDecisions  InvalidatePattern = "maximus:decisions:"
	InvalidateAllMetrics    InvalidatePattern = "metrics:"
	InvalidateAllGateway    InvalidatePattern = "gateway:"
)

// Invalidate removes all cache entries matching a pattern
func (c *Cache) Invalidate(pattern InvalidatePattern) error {
	return c.DeletePrefix(string(pattern))
}
