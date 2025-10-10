package sensors

import (
	"context"
	"os"
	"strings"
	"sync"
	"time"

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
	
	// Network baseline
	knownConnections map[string]*ConnectionProfile
	suspiciousIPs    map[string]bool
}

// ConnectionProfile represents normal connection behavior.
type ConnectionProfile struct {
	RemoteAddr string
	Port       int
	FirstSeen  time.Time
	Count      int
}

// NewNetworkMonitor creates a new network monitoring sensor.
func NewNetworkMonitor(log *logger.Logger, m *metrics.Collector) *NetworkMonitor {
	return &NetworkMonitor{
		logger:           log,
		metrics:          m,
		anomalyScore:     0.0,
		knownConnections: make(map[string]*ConnectionProfile),
		suspiciousIPs:    initSuspiciousIPs(),
	}
}

// initSuspiciousIPs returns known malicious IP patterns.
//
// Phase 1: Simple hardcoded list.
// Future: Threat intelligence feed integration.
func initSuspiciousIPs() map[string]bool {
	return map[string]bool{
		"10.0.0.666": true, // Example malicious IP
		"192.168.1.666": true,
		// Phase 1: Placeholder IPs
	}
}

// Start begins network monitoring.
func (nm *NetworkMonitor) Start(ctx context.Context) error {
	nm.ctx = ctx
	nm.logger.Debug("network_monitor_started")
	
	// Build initial baseline
	nm.buildBaseline()
	
	// Start monitoring loop
	go nm.monitorLoop()
	
	return nil
}

// buildBaseline establishes network connection baseline.
func (nm *NetworkMonitor) buildBaseline() {
	// Parse /proc/net/tcp for established connections (Linux-specific)
	data, err := os.ReadFile("/proc/net/tcp")
	if err != nil {
		nm.logger.Warn("failed to read /proc/net/tcp", logger.Error(err))
		return
	}
	
	lines := strings.Split(string(data), "\n")
	for _, line := range lines[1:] { // Skip header
		if line == "" {
			continue
		}
		
		fields := strings.Fields(line)
		if len(fields) < 3 {
			continue
		}
		
		// Parse remote address
		remoteAddr := nm.parseHexAddr(fields[2])
		if remoteAddr != "" {
			nm.knownConnections[remoteAddr] = &ConnectionProfile{
				RemoteAddr: remoteAddr,
				FirstSeen:  time.Now(),
				Count:      1,
			}
		}
	}
	
	nm.logger.Debug("network_baseline_established",
		logger.Int("known_connections", len(nm.knownConnections)),
	)
}

// parseHexAddr converts hex address from /proc/net/tcp to IP:port.
func (nm *NetworkMonitor) parseHexAddr(hexAddr string) string {
	// Phase 1: Simplified parsing
	// Format: "0100007F:0050" = 127.0.0.1:80
	parts := strings.Split(hexAddr, ":")
	if len(parts) != 2 {
		return ""
	}
	
	// Parse IP (hex to decimal)
	// Phase 1: Return hex as-is (future: proper conversion)
	return hexAddr
}

// monitorLoop continuously monitors network connections.
func (nm *NetworkMonitor) monitorLoop() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-nm.ctx.Done():
			return
		case <-ticker.C:
			nm.checkConnections()
		}
	}
}

// checkConnections scans current connections for anomalies.
func (nm *NetworkMonitor) checkConnections() {
	data, err := os.ReadFile("/proc/net/tcp")
	if err != nil {
		return
	}
	
	anomalies := 0
	totalConns := 0
	
	lines := strings.Split(string(data), "\n")
	for _, line := range lines[1:] {
		if line == "" {
			continue
		}
		
		fields := strings.Fields(line)
		if len(fields) < 3 {
			continue
		}
		
		remoteAddr := nm.parseHexAddr(fields[2])
		if remoteAddr == "" {
			continue
		}
		
		totalConns++
		
		// Check for anomalies
		if nm.isAnomalousConnection(remoteAddr) {
			anomalies++
			
			nm.logger.Debug("anomalous_connection_detected",
				logger.String("remote_addr", remoteAddr),
			)
		}
	}
	
	// Update anomaly score
	if totalConns > 0 {
		score := float64(anomalies) / float64(totalConns)
		nm.mu.Lock()
		nm.anomalyScore = score
		nm.mu.Unlock()
	}
}

// isAnomalousConnection checks if connection is suspicious.
func (nm *NetworkMonitor) isAnomalousConnection(remoteAddr string) bool {
	// Check against suspicious IP list
	if nm.suspiciousIPs[remoteAddr] {
		return true
	}
	
	// Check for unknown connections (not in baseline)
	if _, known := nm.knownConnections[remoteAddr]; !known {
		// Add to baseline (learning phase)
		nm.knownConnections[remoteAddr] = &ConnectionProfile{
			RemoteAddr: remoteAddr,
			FirstSeen:  time.Now(),
			Count:      1,
		}
		return false // Don't flag new legitimate connections
	}
	
	// Phase 1: Additional heuristics could go here
	// Future: ML-based flow analysis, bandwidth anomalies
	
	return false
}

// GetAnomalyScore returns current network anomaly score.
func (nm *NetworkMonitor) GetAnomalyScore() float64 {
	nm.mu.RLock()
	defer nm.mu.RUnlock()
	return nm.anomalyScore
}

// GetConnectionStats returns network statistics for testing.
func (nm *NetworkMonitor) GetConnectionStats() (int, int) {
	nm.mu.RLock()
	defer nm.mu.RUnlock()
	return len(nm.knownConnections), len(nm.suspiciousIPs)
}
