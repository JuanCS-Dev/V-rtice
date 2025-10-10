package sensors

import (
	"context"
	"sync"

	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// NetworkMonitor monitors network activity for anomalies.
//
// Biological Analogy: Detects abnormal "flow" patterns (like sensing
// turbulent blood flow that indicates vessel damage).
type NetworkMonitor struct {
	logger       *logger.Logger
	metrics      *metrics.Collector
	anomalyScore float64
	mu           sync.RWMutex
	ctx          context.Context
}

// NewNetworkMonitor creates a new network monitoring sensor.
func NewNetworkMonitor(log *logger.Logger, m *metrics.Collector) *NetworkMonitor {
	return &NetworkMonitor{
		logger:       log,
		metrics:      m,
		anomalyScore: 0.0,
	}
}

// Start begins network monitoring.
//
// Phase 1: Placeholder implementation.
// Future: eBPF-based packet inspection, flow analysis.
func (nm *NetworkMonitor) Start(ctx context.Context) error {
	nm.ctx = ctx
	nm.logger.Debug("network_monitor_started (placeholder)")
	
	// Phase 1: Return low anomaly score (not implemented yet)
	nm.mu.Lock()
	nm.anomalyScore = 0.0
	nm.mu.Unlock()
	
	return nil
}

// GetAnomalyScore returns current network anomaly score.
//
// Phase 1: Always 0.0 (placeholder).
// Future: Real-time network anomaly detection via eBPF.
func (nm *NetworkMonitor) GetAnomalyScore() float64 {
	nm.mu.RLock()
	defer nm.mu.RUnlock()
	return nm.anomalyScore
}
