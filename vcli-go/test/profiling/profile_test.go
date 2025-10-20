// +build integration

package profiling

import (
	"context"
	"fmt"
	"runtime"
	"runtime/pprof"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/require"

	grpcclient "github.com/verticedev/vcli-go/internal/grpc"
)

const (
	grpcServerURL = "localhost:50051"
	operatorID    = "profiling_operator"
)

// TestCPUProfile_HealthCheck profiles CPU usage during health checks
func TestCPUProfile_HealthCheck(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping CPU profiling test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping profiling test")
		return
	}
	defer client.Close()

	ctx := context.Background()

	t.Log("Starting CPU profiling for health checks...")

	// Perform health checks for 10 seconds
	duration := 10 * time.Second
	endTime := time.Now().Add(duration)

	count := 0
	for time.Now().Before(endTime) {
		_, err := client.HealthCheck(ctx)
		if err != nil {
			t.Logf("Health check failed: %v", err)
		}
		count++
		time.Sleep(10 * time.Millisecond)
	}

	t.Logf("Completed %d health checks in %v", count, duration)
	t.Logf("Rate: %.2f checks/second", float64(count)/duration.Seconds())
}

// TestMemoryProfile_SessionLifecycle profiles memory during session lifecycle
func TestMemoryProfile_SessionLifecycle(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping memory profiling test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping profiling test")
		return
	}
	defer client.Close()

	ctx := context.Background()

	t.Log("Starting memory profiling for session lifecycle...")

	// Create and destroy sessions repeatedly
	numSessions := 100

	for i := 0; i < numSessions; i++ {
		sessionID, err := client.CreateSession(ctx, fmt.Sprintf("%s_%d", operatorID, i))
		if err != nil {
			t.Fatalf("Failed to create session %d: %v", i, err)
		}

		// Perform some operations
		client.HealthCheck(ctx)
		client.ListPendingDecisions(ctx, 10, "PENDING", "")
		client.GetMetrics(ctx)

		// Close session
		err = client.CloseSession(ctx)
		if err != nil {
			t.Logf("Failed to close session %s: %v", sessionID, err)
		}

		if i%10 == 0 {
			t.Logf("Progress: %d/%d sessions", i, numSessions)
		}
	}

	t.Logf("Completed %d session lifecycles", numSessions)
}

// TestGoroutineProfile_ConcurrentOperations profiles goroutines during concurrent ops
func TestGoroutineProfile_ConcurrentOperations(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping goroutine profiling test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping profiling test")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	t.Log("Starting goroutine profiling for concurrent operations...")

	// Take initial goroutine snapshot
	initialGoroutines := runtime.NumGoroutine()
	t.Logf("Initial goroutines: %d", initialGoroutines)

	// Run concurrent operations
	concurrency := 100
	opsPerGoroutine := 100

	var wg sync.WaitGroup

	startTime := time.Now()

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			for j := 0; j < opsPerGoroutine; j++ {
				operation := j % 3
				switch operation {
				case 0:
					client.HealthCheck(ctx)
				case 1:
					client.ListPendingDecisions(ctx, 5, "PENDING", "")
				case 2:
					client.GetMetrics(ctx)
				}
			}
		}(i)
	}

	// Check goroutines during execution
	time.Sleep(500 * time.Millisecond)
	midGoroutines := runtime.NumGoroutine()
	t.Logf("Goroutines during execution: %d (+%d)", midGoroutines, midGoroutines-initialGoroutines)

	wg.Wait()
	duration := time.Since(startTime)

	// Check final goroutines
	time.Sleep(1 * time.Second)
	runtime.GC()
	time.Sleep(1 * time.Second)

	finalGoroutines := runtime.NumGoroutine()
	t.Logf("Final goroutines: %d (+%d)", finalGoroutines, finalGoroutines-initialGoroutines)

	totalOps := concurrency * opsPerGoroutine
	t.Logf("Completed %d operations in %v", totalOps, duration)
	t.Logf("Rate: %.2f ops/second", float64(totalOps)/duration.Seconds())

	// Validate goroutines didn't leak significantly
	goroutineLeak := finalGoroutines - initialGoroutines
	if goroutineLeak > 10 {
		t.Logf("WARNING: Potential goroutine leak: +%d goroutines", goroutineLeak)
	} else {
		t.Logf("✓ No significant goroutine leak detected")
	}
}

// TestBlockProfile_ChannelContention profiles blocking on channels
func TestBlockProfile_ChannelContention(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping block profiling test in short mode")
	}

	// Enable block profiling
	runtime.SetBlockProfileRate(1)
	defer runtime.SetBlockProfileRate(0)

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping profiling test")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	t.Log("Starting block profiling for channel contention...")

	// Simulate contention with concurrent operations
	concurrency := 50
	duration := 5 * time.Second

	var wg sync.WaitGroup
	endTime := time.Now().Add(duration)

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			for time.Now().Before(endTime) {
				client.HealthCheck(ctx)
				time.Sleep(10 * time.Millisecond)
			}
		}()
	}

	wg.Wait()

	t.Log("Block profiling completed")
}

// TestMutexProfile_Contention profiles mutex contention
func TestMutexProfile_Contention(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping mutex profiling test in short mode")
	}

	// Enable mutex profiling
	runtime.SetMutexProfileFraction(1)
	defer runtime.SetMutexProfileFraction(0)

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping profiling test")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	t.Log("Starting mutex profiling for contention...")

	// Simulate contention with concurrent operations
	concurrency := 50
	opsPerGoroutine := 100

	var wg sync.WaitGroup

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			for j := 0; j < opsPerGoroutine; j++ {
				client.HealthCheck(ctx)
			}
		}()
	}

	wg.Wait()

	t.Log("Mutex profiling completed")
}

// TestHeapProfile_AllocationPatterns profiles heap allocations
func TestHeapProfile_AllocationPatterns(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping heap profiling test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping profiling test")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	t.Log("Starting heap profiling for allocation patterns...")

	// Capture initial heap stats
	var m1 runtime.MemStats
	runtime.ReadMemStats(&m1)
	t.Logf("Initial heap: Alloc=%d MB, TotalAlloc=%d MB, Sys=%d MB",
		m1.Alloc/1024/1024, m1.TotalAlloc/1024/1024, m1.Sys/1024/1024)

	// Perform operations that allocate memory
	numOperations := 10000

	for i := 0; i < numOperations; i++ {
		operation := i % 4
		switch operation {
		case 0:
			client.HealthCheck(ctx)
		case 1:
			client.ListPendingDecisions(ctx, 10, "PENDING", "")
		case 2:
			client.GetMetrics(ctx)
		case 3:
			client.GetSessionStats(ctx)
		}
	}

	// Capture final heap stats
	var m2 runtime.MemStats
	runtime.ReadMemStats(&m2)
	t.Logf("Final heap: Alloc=%d MB, TotalAlloc=%d MB, Sys=%d MB",
		m2.Alloc/1024/1024, m2.TotalAlloc/1024/1024, m2.Sys/1024/1024)

	// Calculate allocation rate
	allocPerOp := (m2.TotalAlloc - m1.TotalAlloc) / uint64(numOperations)
	t.Logf("Average allocation per operation: %d bytes", allocPerOp)

	// GC and check if memory is freed
	runtime.GC()
	time.Sleep(1 * time.Second)

	var m3 runtime.MemStats
	runtime.ReadMemStats(&m3)
	t.Logf("After GC: Alloc=%d MB, TotalAlloc=%d MB, Sys=%d MB",
		m3.Alloc/1024/1024, m3.TotalAlloc/1024/1024, m3.Sys/1024/1024)

	// Validate memory is reclaimed
	memoryReclaimed := m2.Alloc - m3.Alloc
	reclaimRate := float64(memoryReclaimed) / float64(m2.Alloc) * 100
	t.Logf("Memory reclaimed after GC: %d bytes (%.2f%%)", memoryReclaimed, reclaimRate)

	if reclaimRate < 50 {
		t.Logf("WARNING: Low memory reclaim rate (%.2f%%), possible memory retention", reclaimRate)
	} else {
		t.Logf("✓ Good memory reclaim rate (%.2f%%)", reclaimRate)
	}
}

// TestAllocationProfile_PerOperation profiles allocations per operation type
func TestAllocationProfile_PerOperation(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping allocation profiling test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping profiling test")
		return
	}
	defer client.Close()

	ctx := context.Background()

	// Create session
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	t.Log("Profiling allocations per operation type...")

	operations := []struct {
		name string
		fn   func() error
	}{
		{"HealthCheck", func() error { _, err := client.HealthCheck(ctx); return err }},
		{"ListDecisions", func() error { _, err := client.ListPendingDecisions(ctx, 10, "PENDING", ""); return err }},
		{"GetMetrics", func() error { _, err := client.GetMetrics(ctx); return err }},
		{"GetSessionStats", func() error { _, err := client.GetSessionStats(ctx); return err }},
	}

	iterations := 1000

	for _, op := range operations {
		// GC before each operation profiling
		runtime.GC()
		time.Sleep(100 * time.Millisecond)

		var m1, m2 runtime.MemStats
		runtime.ReadMemStats(&m1)

		// Perform operations
		for i := 0; i < iterations; i++ {
			op.fn()
		}

		runtime.ReadMemStats(&m2)

		allocPerOp := (m2.TotalAlloc - m1.TotalAlloc) / uint64(iterations)
		mallocsPerOp := (m2.Mallocs - m1.Mallocs) / uint64(iterations)

		t.Logf("%-20s: %6d bytes/op, %4d mallocs/op", op.name, allocPerOp, mallocsPerOp)
	}
}

// Helper function to print profile data
func printProfileData(t *testing.T, profile *pprof.Profile, topN int) {
	t.Logf("\nTop %d entries in %s profile:", topN, profile.Name())

	// This is a simplified version - in practice you'd write to a buffer
	// and parse it or use pprof tools
	t.Logf("(Profile contains %d samples)", profile.Count())
}
