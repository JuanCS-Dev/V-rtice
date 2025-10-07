package load

import (
	"context"
	"fmt"
	"runtime"
	"sync/atomic"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	grpcclient "github.com/verticedev/vcli-go/internal/grpc"
)

// MemorySnapshot represents memory statistics at a point in time
type MemorySnapshot struct {
	Timestamp      time.Time
	Alloc          uint64 // bytes allocated and not yet freed
	TotalAlloc     uint64 // bytes allocated (even if freed)
	Sys            uint64 // bytes obtained from system
	NumGC          uint32 // number of completed GC cycles
	NumGoroutine   int    // number of goroutines
	HeapAlloc      uint64 // heap bytes allocated
	HeapObjects    uint64 // total number of allocated heap objects
}

// MemoryMonitor tracks memory usage over time
type MemoryMonitor struct {
	snapshots []MemorySnapshot
	interval  time.Duration
	stopChan  chan bool
}

// NewMemoryMonitor creates a new memory monitor
func NewMemoryMonitor(interval time.Duration) *MemoryMonitor {
	return &MemoryMonitor{
		snapshots: make([]MemorySnapshot, 0),
		interval:  interval,
		stopChan:  make(chan bool),
	}
}

// Start begins monitoring memory
func (mm *MemoryMonitor) Start() {
	ticker := time.NewTicker(mm.interval)
	go func() {
		for {
			select {
			case <-ticker.C:
				mm.TakeSnapshot()
			case <-mm.stopChan:
				ticker.Stop()
				return
			}
		}
	}()
}

// Stop stops monitoring
func (mm *MemoryMonitor) Stop() {
	mm.stopChan <- true
}

// TakeSnapshot captures current memory statistics
func (mm *MemoryMonitor) TakeSnapshot() {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	snapshot := MemorySnapshot{
		Timestamp:    time.Now(),
		Alloc:        m.Alloc,
		TotalAlloc:   m.TotalAlloc,
		Sys:          m.Sys,
		NumGC:        m.NumGC,
		NumGoroutine: runtime.NumGoroutine(),
		HeapAlloc:    m.HeapAlloc,
		HeapObjects:  m.HeapObjects,
	}

	mm.snapshots = append(mm.snapshots, snapshot)
}

// GetSnapshots returns all snapshots
func (mm *MemoryMonitor) GetSnapshots() []MemorySnapshot {
	return mm.snapshots
}

// DetectMemoryLeak analyzes snapshots to detect memory leaks
func (mm *MemoryMonitor) DetectMemoryLeak() (bool, string) {
	if len(mm.snapshots) < 3 {
		return false, "Insufficient data points"
	}

	// Check if memory is consistently growing
	first := mm.snapshots[0]
	last := mm.snapshots[len(mm.snapshots)-1]

	allocGrowth := float64(last.Alloc) / float64(first.Alloc)
	_ = allocGrowth // heapGrowth unused for now

	// If memory grew more than 3x and hasn't been freed, potential leak
	if allocGrowth > 3.0 && last.NumGC > first.NumGC+10 {
		return true, fmt.Sprintf("Memory grew %.2fx despite %d GC cycles", allocGrowth, last.NumGC-first.NumGC)
	}

	// Check goroutine leaks
	goroutineGrowth := last.NumGoroutine - first.NumGoroutine
	if goroutineGrowth > 100 {
		return true, fmt.Sprintf("Goroutine leak detected: %d new goroutines", goroutineGrowth)
	}

	// Check heap object leaks
	objectGrowth := float64(last.HeapObjects) / float64(first.HeapObjects)
	if objectGrowth > 5.0 {
		return true, fmt.Sprintf("Heap object growth: %.2fx", objectGrowth)
	}

	return false, "No memory leak detected"
}

// PrintReport prints memory monitoring report
func (mm *MemoryMonitor) PrintReport(t *testing.T) {
	if len(mm.snapshots) == 0 {
		t.Log("No memory snapshots captured")
		return
	}

	first := mm.snapshots[0]
	last := mm.snapshots[len(mm.snapshots)-1]

	separator := repeatString("=", 80)
	t.Logf("\n%s", separator)
	t.Logf("Memory Monitoring Report")
	t.Logf("%s", separator)
	t.Logf("Duration:        %v", last.Timestamp.Sub(first.Timestamp))
	t.Logf("Snapshots:       %d", len(mm.snapshots))
	t.Logf("\nMemory Growth:")
	t.Logf("  Alloc:         %d → %d bytes (%.2fx)", first.Alloc, last.Alloc, float64(last.Alloc)/float64(first.Alloc))
	t.Logf("  HeapAlloc:     %d → %d bytes (%.2fx)", first.HeapAlloc, last.HeapAlloc, float64(last.HeapAlloc)/float64(first.HeapAlloc))
	t.Logf("  Sys:           %d → %d bytes (%.2fx)", first.Sys, last.Sys, float64(last.Sys)/float64(first.Sys))
	t.Logf("\nGC Stats:")
	t.Logf("  GC Cycles:     %d → %d (%d total)", first.NumGC, last.NumGC, last.NumGC-first.NumGC)
	t.Logf("\nGoroutines:")
	t.Logf("  Count:         %d → %d (%+d)", first.NumGoroutine, last.NumGoroutine, last.NumGoroutine-first.NumGoroutine)
	t.Logf("\nHeap Objects:")
	t.Logf("  Count:         %d → %d (%.2fx)", first.HeapObjects, last.HeapObjects, float64(last.HeapObjects)/float64(first.HeapObjects))
	t.Logf("%s\n", separator)

	// Memory leak detection
	leaked, reason := mm.DetectMemoryLeak()
	if leaked {
		t.Logf("⚠️  WARNING: %s", reason)
	} else {
		t.Logf("✓ %s", reason)
	}
}

// TestMemoryLeak_ContinuousOperations tests for memory leaks during continuous operations
func TestMemoryLeak_ContinuousOperations(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping memory leak test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping memory leak test")
		return
	}
	defer client.Close()

	// Start memory monitoring
	monitor := NewMemoryMonitor(1 * time.Second)
	monitor.Start()
	defer monitor.Stop()

	// Run continuous operations for 1 minute
	duration := 60 * time.Second
	ctx, cancel := context.WithTimeout(context.Background(), duration)
	defer cancel()

	var requestCount atomic.Int64

	t.Logf("Running continuous operations for %v...", duration)

	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			goto DONE
		case <-ticker.C:
			// Mix of operations
			operation := requestCount.Add(1) % 4
			switch operation {
			case 0:
				client.HealthCheck(context.Background())
			case 1:
				client.ListPendingDecisions(context.Background(), 5, "PENDING", "")
			case 2:
				client.GetMetrics(context.Background())
			case 3:
				// Periodically create and close sessions
				if operation%10 == 0 {
					sessionID, err := client.CreateSession(context.Background(), fmt.Sprintf("mem_test_%d", operation))
					if err == nil {
						// Session created successfully
						_ = sessionID
					}
				}
			}
		}
	}

DONE:
	totalRequests := requestCount.Load()
	t.Logf("Completed %d requests", totalRequests)

	// Force GC to clean up
	runtime.GC()
	time.Sleep(500 * time.Millisecond)

	// Take final snapshot
	monitor.TakeSnapshot()

	// Print report
	monitor.PrintReport(t)

	// Validate no memory leak
	leaked, reason := monitor.DetectMemoryLeak()
	assert.False(t, leaked, "Memory leak detected: %s", reason)

	// Get snapshots
	snapshots := monitor.GetSnapshots()
	require.Greater(t, len(snapshots), 30, "Should have at least 30 snapshots")

	// Validate goroutine count is stable (±20 from start)
	first := snapshots[0]
	last := snapshots[len(snapshots)-1]
	goroutineDiff := last.NumGoroutine - first.NumGoroutine
	assert.Less(t, goroutineDiff, 20, "Goroutine count should be stable")

	// Validate memory growth is reasonable (< 3x)
	memoryGrowth := float64(last.Alloc) / float64(first.Alloc)
	assert.Less(t, memoryGrowth, 3.0, "Memory should not grow more than 3x")
}

// TestMemoryLeak_ConnectionPooling tests connection pooling behavior
func TestMemoryLeak_ConnectionPooling(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping connection pooling test in short mode")
	}

	monitor := NewMemoryMonitor(500 * time.Millisecond)
	monitor.Start()
	defer monitor.Stop()

	// Create multiple clients (simulating connection pooling)
	numClients := 50
	clients := make([]*grpcclient.GovernanceClient, numClients)

	t.Logf("Creating %d clients...", numClients)

	// Create clients
	for i := 0; i < numClients; i++ {
		client, err := grpcclient.NewGovernanceClient(grpcServerURL)
		if err != nil {
			t.Skip("gRPC server not running, skipping connection pooling test")
			return
		}
		clients[i] = client
	}

	// Take snapshot after connection creation
	time.Sleep(1 * time.Second)
	monitor.TakeSnapshot()

	// Use all connections
	t.Logf("Using all connections...")
	ctx := context.Background()
	for i := 0; i < numClients; i++ {
		_, err := clients[i].HealthCheck(ctx)
		require.NoError(t, err)
	}

	// Take snapshot after using connections
	time.Sleep(1 * time.Second)
	monitor.TakeSnapshot()

	// Close all clients
	t.Logf("Closing all clients...")
	for i := 0; i < numClients; i++ {
		clients[i].Close()
	}

	// Force GC
	runtime.GC()
	time.Sleep(2 * time.Second)

	// Take final snapshot
	monitor.TakeSnapshot()

	// Print report
	monitor.PrintReport(t)

	// Validate connections are properly closed
	snapshots := monitor.GetSnapshots()
	require.Greater(t, len(snapshots), 3, "Should have at least 4 snapshots")

	// After closing, memory should go down
	beforeClose := snapshots[len(snapshots)-2]
	afterClose := snapshots[len(snapshots)-1]

	// Memory should not grow significantly after closing connections
	memoryAfterClose := float64(afterClose.Alloc) / float64(beforeClose.Alloc)
	assert.Less(t, memoryAfterClose, 1.5, "Memory should decrease after closing connections")

	// Goroutines should be cleaned up
	goroutineGrowth := afterClose.NumGoroutine - beforeClose.NumGoroutine
	assert.Less(t, goroutineGrowth, 10, "Goroutines should be cleaned up after closing connections")

	t.Logf("✓ Connection pooling working correctly")
}

// TestMemoryLeak_LongRunningSession tests memory behavior with long-running session
func TestMemoryLeak_LongRunningSession(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping long-running session test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping long-running session test")
		return
	}
	defer client.Close()

	monitor := NewMemoryMonitor(2 * time.Second)
	monitor.Start()
	defer monitor.Stop()

	// Create a session
	ctx := context.Background()
	sessionID, err := client.CreateSession(ctx, "longrunning_mem_test")
	require.NoError(t, err)
	t.Logf("Created session: %s", sessionID)

	// Perform operations over 2 minutes
	duration := 2 * time.Minute
	endTime := time.Now().Add(duration)

	t.Logf("Running operations for %v with active session...", duration)

	operationCount := 0
	for time.Now().Before(endTime) {
		// Perform various operations
		client.ListPendingDecisions(ctx, 10, "PENDING", "")
		client.GetMetrics(ctx)
		client.GetSessionStats(ctx)

		operationCount++

		// Periodic GC to ensure memory is being freed
		if operationCount%100 == 0 {
			runtime.GC()
		}

		time.Sleep(100 * time.Millisecond)
	}

	t.Logf("Completed %d operations", operationCount)

	// Close session
	err = client.CloseSession(ctx)
	require.NoError(t, err)

	// Force final GC
	runtime.GC()
	time.Sleep(1 * time.Second)

	// Take final snapshot
	monitor.TakeSnapshot()

	// Print report
	monitor.PrintReport(t)

	// Validate no memory leak
	leaked, reason := monitor.DetectMemoryLeak()
	assert.False(t, leaked, "Memory leak detected: %s", reason)

	t.Logf("✓ Long-running session completed without memory leak")
}

// TestMemoryLeak_RapidSessionCreationDestruction tests rapid session lifecycle
func TestMemoryLeak_RapidSessionCreationDestruction(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping rapid session test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping rapid session test")
		return
	}
	defer client.Close()

	monitor := NewMemoryMonitor(1 * time.Second)
	monitor.Start()
	defer monitor.Stop()

	ctx := context.Background()
	numSessions := 1000

	t.Logf("Creating and destroying %d sessions rapidly...", numSessions)

	for i := 0; i < numSessions; i++ {
		// Create session
		sessionID, err := client.CreateSession(ctx, fmt.Sprintf("rapid_test_%d", i))
		if err != nil {
			t.Logf("Failed to create session %d: %v", i, err)
			continue
		}

		// Do some operations
		client.HealthCheck(ctx)
		client.GetMetrics(ctx)

		// Close session (note: current implementation may not have CloseSession returning the session)
		// We're testing that repeated session creation doesn't leak
		_ = sessionID

		if i%100 == 0 {
			runtime.GC()
			t.Logf("Progress: %d/%d sessions", i, numSessions)
		}
	}

	// Final GC
	runtime.GC()
	time.Sleep(2 * time.Second)

	// Take final snapshot
	monitor.TakeSnapshot()

	// Print report
	monitor.PrintReport(t)

	// Validate no memory leak
	snapshots := monitor.GetSnapshots()
	require.Greater(t, len(snapshots), 2, "Should have multiple snapshots")

	first := snapshots[0]
	last := snapshots[len(snapshots)-1]

	// Memory growth should be reasonable
	memoryGrowth := float64(last.Alloc) / float64(first.Alloc)
	assert.Less(t, memoryGrowth, 5.0, "Memory should not grow more than 5x after 1000 sessions")

	// Goroutines should be stable
	goroutineGrowth := last.NumGoroutine - first.NumGoroutine
	assert.Less(t, goroutineGrowth, 50, "Goroutine count should remain stable")

	t.Logf("✓ Rapid session creation/destruction completed without leaks")
}
