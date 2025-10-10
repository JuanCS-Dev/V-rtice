package sensors

import (
	"context"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// ProcessMonitor monitors running processes for anomalies.
//
// Biological Analogy: Detects "foreign" processes (like immune system
// detecting non-self antigens). Anomalies trigger platelet activation.
type ProcessMonitor struct {
	logger         *logger.Logger
	metrics        *metrics.Collector
	anomalyScore   float64
	mu             sync.RWMutex
	knownProcesses map[string]bool
	ctx            context.Context
}

// NewProcessMonitor creates a new process monitoring sensor.
func NewProcessMonitor(log *logger.Logger, m *metrics.Collector) *ProcessMonitor {
	return &ProcessMonitor{
		logger:         log,
		metrics:        m,
		anomalyScore:   0.0,
		knownProcesses: make(map[string]bool),
	}
}

// Start begins process monitoring.
func (pm *ProcessMonitor) Start(ctx context.Context) error {
	pm.ctx = ctx
	
	// Build baseline of known processes
	pm.buildBaseline()
	
	// Start monitoring loop
	go pm.monitorLoop()
	
	pm.logger.Debug("process_monitor_started")
	return nil
}

// buildBaseline establishes initial process baseline.
//
// Phase 1: Simple implementation (just record current processes).
// Future: ML-based behavioral profiling.
func (pm *ProcessMonitor) buildBaseline() {
	// Read /proc to get process list (Linux-specific for Phase 1)
	entries, err := os.ReadDir("/proc")
	if err != nil {
		pm.logger.Warn("failed to read /proc", logger.Error(err))
		return
	}
	
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		
		// Try to read process command line
		cmdPath := fmt.Sprintf("/proc/%s/cmdline", entry.Name())
		cmdData, err := os.ReadFile(cmdPath)
		if err != nil {
			continue
		}
		
		cmd := string(cmdData)
		if cmd != "" {
			pm.knownProcesses[cmd] = true
		}
	}
	
	pm.logger.Debug("baseline_established",
		logger.Int("known_processes", len(pm.knownProcesses)),
	)
}

// monitorLoop continuously monitors for process anomalies.
func (pm *ProcessMonitor) monitorLoop() {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-pm.ctx.Done():
			return
		case <-ticker.C:
			pm.checkProcesses()
		}
	}
}

// checkProcesses scans current processes and updates anomaly score.
func (pm *ProcessMonitor) checkProcesses() {
	entries, err := os.ReadDir("/proc")
	if err != nil {
		return
	}
	
	anomalies := 0
	totalProcesses := 0
	
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		
		cmdPath := fmt.Sprintf("/proc/%s/cmdline", entry.Name())
		cmdData, err := os.ReadFile(cmdPath)
		if err != nil {
			continue
		}
		
		cmd := string(cmdData)
		if cmd == "" {
			continue
		}
		
		totalProcesses++
		
		// Simple heuristics for Phase 1
		if pm.isAnomalousProcess(cmd) {
			anomalies++
			
			pm.logger.Debug("anomalous_process_detected",
				logger.String("process", cmd[:min(len(cmd), 50)]),
			)
		}
	}
	
	// Update anomaly score
	if totalProcesses > 0 {
		score := float64(anomalies) / float64(totalProcesses)
		pm.mu.Lock()
		pm.anomalyScore = score
		pm.mu.Unlock()
	}
}

// isAnomalousProcess applies heuristics to detect suspicious processes.
//
// Phase 1: Simple keyword matching.
// Future: ML-based behavioral analysis, execution flow tracking.
func (pm *ProcessMonitor) isAnomalousProcess(cmd string) bool {
	// Unknown process (not in baseline)
	if !pm.knownProcesses[cmd] {
		// Add to baseline (learning phase)
		pm.knownProcesses[cmd] = true
		return false // Don't flag new legitimate processes
	}
	
	// Suspicious keywords (Phase 1 heuristics)
	suspiciousKeywords := []string{
		"nc -l", "ncat", "netcat",
		"/bin/bash -i",
		"powershell",
		"meterpreter",
		"reverse_shell",
		"cryptominer",
	}
	
	cmdLower := strings.ToLower(cmd)
	for _, keyword := range suspiciousKeywords {
		if strings.Contains(cmdLower, keyword) {
			return true
		}
	}
	
	return false
}

// GetAnomalyScore returns current anomaly score (0.0-1.0).
func (pm *ProcessMonitor) GetAnomalyScore() float64 {
	pm.mu.RLock()
	defer pm.mu.RUnlock()
	return pm.anomalyScore
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
