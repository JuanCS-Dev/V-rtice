package regulation

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/verticedev/coagulation/pkg/eventbus"
	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// ProteinSService acts as cofactor for Protein C.
//
// Biological Analogy: Protein S amplifies Protein C activity by 10-20x.
// It doesn't have activity alone, but dramatically enhances Protein C's
// anti-coagulant function.
//
// Digital Function: Accelerates and enhances health checking performed
// by Protein C. Provides caching, parallel execution, and result aggregation
// to make health checks faster and more comprehensive.
type ProteinSService struct {
	logger   *logger.Logger
	metrics  *metrics.Collector
	eventBus *eventbus.Client

	// Cached health results
	healthCache      map[string]*CachedHealthResult
	cacheTTL         time.Duration
	mu               sync.RWMutex

	// Performance optimization
	parallelChecks   int           // Number of parallel health checks
	checkTimeout     time.Duration // Per-check timeout
	batchSize        int           // Batch size for bulk checks

	ctx        context.Context
	cancelFunc context.CancelFunc
}

// CachedHealthResult represents cached health check.
type CachedHealthResult struct {
	SegmentID   string
	Result      *HealthStatus
	CachedAt    time.Time
	ExpiresAt   time.Time
	HitCount    int
}

// HealthCheckRequest represents async health check request.
type HealthCheckRequest struct {
	SegmentID   string
	Priority    int
	Callback    chan *HealthStatus
	Timeout     time.Duration
}

// BatchHealthCheckResult aggregates multiple checks.
type BatchHealthCheckResult struct {
	Results     map[string]*HealthStatus
	Duration    time.Duration
	CacheHits   int
	CacheMisses int
}

// NewProteinSService creates Protein C cofactor service.
func NewProteinSService(
	logger *logger.Logger,
	metrics *metrics.Collector,
	eventBus *eventbus.Client,
) *ProteinSService {
	ctx, cancel := context.WithCancel(context.Background())

	return &ProteinSService{
		logger:   logger,
		metrics:  metrics,
		eventBus: eventBus,

		healthCache:    make(map[string]*CachedHealthResult),
		cacheTTL:       60 * time.Second, // 1 minute cache
		
		parallelChecks: 10,                // 10 concurrent checks
		checkTimeout:   5 * time.Second,   // 5s per check
		batchSize:      50,                // 50 segments per batch

		ctx:        ctx,
		cancelFunc: cancel,
	}
}

// Start begins cofactor service.
func (p *ProteinSService) Start() error {
	p.logger.Info("Starting Protein S Service (Health Check Cofactor)")

	// Start cache maintenance
	go p.cacheMaintenanceLoop()

	p.logger.Info("Protein S Service active - accelerating health checks")
	return nil
}

// Stop gracefully stops the service.
func (p *ProteinSService) Stop() error {
	p.logger.Info("Stopping Protein S Service")
	p.cancelFunc()
	return nil
}

// AccelerateHealthCheck performs optimized health check with caching.
//
// CRITICAL FUNCTION: This method provides 10-20x speedup for health checks
// by utilizing caching and parallelization, allowing Protein C to evaluate
// more segments faster during quarantine expansion decisions.
func (p *ProteinSService) AccelerateHealthCheck(
	segmentID string,
	proteinC *ProteinCService,
) (*HealthStatus, error) {
	start := time.Now()

	// Check cache first
	if cached := p.getFromCache(segmentID); cached != nil {
		duration := time.Since(start).Seconds()
		p.metrics.RecordHistogram("health_check_duration_seconds", duration, map[string]string{
			"source": "cache",
		})
		p.metrics.IncrementCounter("health_check_cache_hits_total", map[string]string{
			"segment": segmentID,
		})

		p.logger.Debug("Health check cache HIT",
			"segment", segmentID,
			"age_seconds", time.Since(cached.CachedAt).Seconds(),
		)

		return cached.Result, nil
	}

	// Cache miss - perform check
	p.metrics.IncrementCounter("health_check_cache_misses_total", map[string]string{
		"segment": segmentID,
	})

	segment := &NetworkSegment{
		ID:       segmentID,
		Name:     fmt.Sprintf("Segment %s", segmentID),
		IPRanges: []string{"10.0.0.0/24"},
	}

	health := proteinC.CheckHealth(segment)

	// Cache result
	p.cacheHealthResult(segmentID, health)

	duration := time.Since(start).Seconds()
	p.metrics.RecordHistogram("health_check_duration_seconds", duration, map[string]string{
		"source": "live",
	})

	return health, nil
}

// BatchHealthCheck performs parallel health checks on multiple segments.
//
// Amplification Effect: Instead of checking N segments serially (N * check_time),
// performs parallel checks (check_time * ceil(N/parallelism)).
func (p *ProteinSService) BatchHealthCheck(
	segmentIDs []string,
	proteinC *ProteinCService,
) *BatchHealthCheckResult {
	start := time.Now()
	
	result := &BatchHealthCheckResult{
		Results: make(map[string]*HealthStatus),
	}

	// Check cache for all segments
	uncached := []string{}
	for _, segID := range segmentIDs {
		if cached := p.getFromCache(segID); cached != nil {
			result.Results[segID] = cached.Result
			result.CacheHits++
		} else {
			uncached = append(uncached, segID)
			result.CacheMisses++
		}
	}

	if len(uncached) == 0 {
		result.Duration = time.Since(start)
		p.logger.Info("Batch health check complete - all from cache",
			"segments", len(segmentIDs),
			"duration_ms", result.Duration.Milliseconds(),
		)
		return result
	}

	// Parallel checks for uncached segments
	var wg sync.WaitGroup
	resultChan := make(chan struct {
		segmentID string
		health    *HealthStatus
	}, len(uncached))

	// Semaphore for parallel execution
	sem := make(chan struct{}, p.parallelChecks)

	for _, segID := range uncached {
		wg.Add(1)
		go func(id string) {
			defer wg.Done()
			
			// Acquire semaphore
			sem <- struct{}{}
			defer func() { <-sem }()

			segment := &NetworkSegment{
				ID:       id,
				Name:     fmt.Sprintf("Segment %s", id),
				IPRanges: []string{"10.0.0.0/24"},
			}

			health := proteinC.CheckHealth(segment)
			p.cacheHealthResult(id, health)

			resultChan <- struct {
				segmentID string
				health    *HealthStatus
			}{id, health}
		}(segID)
	}

	// Wait for completion
	go func() {
		wg.Wait()
		close(resultChan)
	}()

	// Collect results
	for res := range resultChan {
		result.Results[res.segmentID] = res.health
	}

	result.Duration = time.Since(start)

	p.logger.Info("Batch health check complete",
		"total_segments", len(segmentIDs),
		"cache_hits", result.CacheHits,
		"cache_misses", result.CacheMisses,
		"duration_ms", result.Duration.Milliseconds(),
		"segments_per_second", float64(len(segmentIDs))/result.Duration.Seconds(),
	)

	// Metrics
	p.metrics.RecordHistogram("batch_health_check_duration_seconds", result.Duration.Seconds(), map[string]string{
		"batch_size": fmt.Sprintf("%d", len(segmentIDs)),
	})

	return result
}

// getFromCache retrieves cached health result if valid.
func (p *ProteinSService) getFromCache(segmentID string) *CachedHealthResult {
	p.mu.RLock()
	defer p.mu.RUnlock()

	cached, exists := p.healthCache[segmentID]
	if !exists {
		return nil
	}

	// Check expiration
	if time.Now().After(cached.ExpiresAt) {
		return nil
	}

	// Update hit count
	cached.HitCount++
	return cached
}

// cacheHealthResult stores health check result.
func (p *ProteinSService) cacheHealthResult(segmentID string, health *HealthStatus) {
	p.mu.Lock()
	defer p.mu.Unlock()

	cached := &CachedHealthResult{
		SegmentID: segmentID,
		Result:    health,
		CachedAt:  time.Now(),
		ExpiresAt: time.Now().Add(p.cacheTTL),
		HitCount:  0,
	}

	p.healthCache[segmentID] = cached

	p.logger.Debug("Cached health result",
		"segment", segmentID,
		"ttl_seconds", p.cacheTTL.Seconds(),
	)
}

// cacheMaintenanceLoop removes expired cache entries.
func (p *ProteinSService) cacheMaintenanceLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			p.cleanupExpiredCache()
		case <-p.ctx.Done():
			return
		}
	}
}

// cleanupExpiredCache removes stale entries.
func (p *ProteinSService) cleanupExpiredCache() {
	p.mu.Lock()
	defer p.mu.Unlock()

	now := time.Now()
	expired := []string{}

	for segID, cached := range p.healthCache {
		if now.After(cached.ExpiresAt) {
			expired = append(expired, segID)
		}
	}

	for _, segID := range expired {
		delete(p.healthCache, segID)
	}

	if len(expired) > 0 {
		p.logger.Debug("Cleaned up expired health cache entries", "count", len(expired))
	}

	// Metrics
	p.metrics.RecordGauge("health_cache_size", float64(len(p.healthCache)), nil)
}

// InvalidateCache clears cache for segment (force refresh).
func (p *ProteinSService) InvalidateCache(segmentID string) {
	p.mu.Lock()
	defer p.mu.Unlock()

	delete(p.healthCache, segmentID)
	
	p.logger.Debug("Invalidated health cache", "segment", segmentID)
}

// GetCacheStats returns cache performance statistics.
func (p *ProteinSService) GetCacheStats() map[string]interface{} {
	p.mu.RLock()
	defer p.mu.RUnlock()

	totalHits := 0
	for _, cached := range p.healthCache {
		totalHits += cached.HitCount
	}

	return map[string]interface{}{
		"cache_size":   len(p.healthCache),
		"total_hits":   totalHits,
		"cache_ttl_s":  p.cacheTTL.Seconds(),
	}
}

// SetCacheTTL updates cache time-to-live.
func (p *ProteinSService) SetCacheTTL(ttl time.Duration) {
	p.mu.Lock()
	defer p.mu.Unlock()

	p.cacheTTL = ttl
	p.logger.Info("Updated health cache TTL", "ttl_seconds", ttl.Seconds())
}
