// +build integration

package chaos

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	grpcclient "github.com/verticedev/vcli-go/internal/grpc"
)

const (
	grpcServerURL = "localhost:50051"
	operatorID    = "chaos_operator"
)

// TestChaos_NetworkLatency tests behavior under network latency
func TestChaos_NetworkLatency(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping chaos test")
		return
	}
	defer client.Close()

	t.Log("Testing behavior under simulated network latency...")

	// Create session
	ctx := context.Background()
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	// Test with varying timeouts to simulate latency
	latencies := []time.Duration{
		100 * time.Millisecond,
		500 * time.Millisecond,
		1 * time.Second,
		2 * time.Second,
	}

	for _, latency := range latencies {
		ctx, cancel := context.WithTimeout(context.Background(), latency)

		start := time.Now()
		_, err := client.HealthCheck(ctx)
		elapsed := time.Since(start)

		cancel()

		if err != nil {
			t.Logf("Latency %v: Failed after %v (expected for short timeouts)", latency, elapsed)
		} else {
			t.Logf("Latency %v: Success in %v", latency, elapsed)
			assert.Less(t, elapsed, latency, "Operation should complete within timeout")
		}
	}

	t.Log("✓ Client handles varying network conditions gracefully")
}

// TestChaos_TimeoutRecovery tests recovery from timeout scenarios
func TestChaos_TimeoutRecovery(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping chaos test")
		return
	}
	defer client.Close()

	t.Log("Testing timeout recovery...")

	// Create session
	ctx := context.Background()
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	// Test series: timeout → success → timeout → success
	scenarios := []struct {
		name    string
		timeout time.Duration
		expectSuccess bool
	}{
		{"Very short timeout", 1 * time.Nanosecond, false},
		{"Normal operation", 5 * time.Second, true},
		{"Short timeout", 1 * time.Millisecond, false},
		{"Recovery", 5 * time.Second, true},
		{"Another short timeout", 500 * time.Microsecond, false},
		{"Final recovery", 5 * time.Second, true},
	}

	successCount := 0
	for _, scenario := range scenarios {
		ctx, cancel := context.WithTimeout(context.Background(), scenario.timeout)

		_, err := client.HealthCheck(ctx)
		cancel()

		if err == nil {
			successCount++
			t.Logf("✓ %s: Success", scenario.name)
			if !scenario.expectSuccess {
				t.Logf("  (Unexpectedly succeeded with timeout %v)", scenario.timeout)
			}
		} else {
			t.Logf("✗ %s: Failed (%v)", scenario.name, err)
			if scenario.expectSuccess {
				t.Errorf("  Expected success but got error: %v", err)
			}
		}
	}

	t.Logf("Recovery test complete: %d/%d scenarios succeeded", successCount, len(scenarios))
	assert.Greater(t, successCount, 0, "At least some operations should succeed")
}

// TestChaos_ConcurrentFailures tests behavior when multiple concurrent ops fail
func TestChaos_ConcurrentFailures(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping chaos test")
		return
	}
	defer client.Close()

	t.Log("Testing concurrent operation failures...")

	// Create session
	ctx := context.Background()
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	// Run concurrent operations with varying timeouts (some will fail)
	concurrency := 20
	var successful atomic.Int64
	var failed atomic.Int64

	var wg sync.WaitGroup

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			// Alternate between very short and normal timeouts
			var timeout time.Duration
			if id%2 == 0 {
				timeout = 1 * time.Nanosecond // Will likely fail
			} else {
				timeout = 5 * time.Second // Should succeed
			}

			ctx, cancel := context.WithTimeout(context.Background(), timeout)
			defer cancel()

			_, err := client.HealthCheck(ctx)
			if err != nil {
				failed.Add(1)
			} else {
				successful.Add(1)
			}
		}(i)
	}

	wg.Wait()

	t.Logf("Concurrent failures test: %d successful, %d failed", successful.Load(), failed.Load())

	// Both should have some results
	assert.Greater(t, successful.Load(), int64(0), "Some operations should succeed")
	assert.Greater(t, failed.Load(), int64(0), "Some operations should fail (as designed)")

	t.Log("✓ Client handles concurrent failures gracefully")
}

// TestChaos_RapidReconnection tests rapid connection/disconnection
func TestChaos_RapidReconnection(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	t.Log("Testing rapid connection/disconnection...")

	numCycles := 10

	for i := 0; i < numCycles; i++ {
		// Create client
		client, err := grpcclient.NewGovernanceClient(grpcServerURL)
		if err != nil {
			t.Fatalf("Failed to create client on cycle %d: %v", i, err)
		}

		// Quick operation
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		_, err = client.HealthCheck(ctx)
		cancel()

		if err != nil {
			t.Logf("Cycle %d: Health check failed: %v", i, err)
		}

		// Close immediately
		err = client.Close()
		if err != nil {
			t.Logf("Cycle %d: Close failed: %v", i, err)
		}

		// Small delay before next cycle
		time.Sleep(10 * time.Millisecond)
	}

	t.Logf("✓ Completed %d rapid reconnection cycles", numCycles)
}

// TestChaos_SessionWithoutHealthCheck tests session operations without health check
func TestChaos_SessionWithoutHealthCheck(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping chaos test")
		return
	}
	defer client.Close()

	t.Log("Testing session operations without prior health check...")

	ctx := context.Background()

	// Create session immediately without health check
	sessionID, err := client.CreateSession(ctx, operatorID)
	if err != nil {
		t.Fatalf("Failed to create session without health check: %v", err)
	}

	t.Logf("✓ Created session without health check: %s", sessionID)

	// Perform operations
	_, err = client.ListPendingDecisions(ctx, 10, "PENDING", "")
	assert.NoError(t, err, "List decisions should work")

	_, err = client.GetMetrics(ctx)
	assert.NoError(t, err, "Get metrics should work")

	// Close session
	err = client.CloseSession(ctx)
	assert.NoError(t, err, "Close session should work")

	t.Log("✓ Session lifecycle works without health check")
}

// TestChaos_InvalidOperationSequence tests invalid operation sequences
func TestChaos_InvalidOperationSequence(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping chaos test")
		return
	}
	defer client.Close()

	ctx := context.Background()

	t.Log("Testing invalid operation sequences...")

	// Try to list decisions without session (should fail gracefully)
	t.Log("Test 1: List decisions without session")
	_, err = client.ListPendingDecisions(ctx, 10, "PENDING", "")
	assert.Error(t, err, "Should fail without active session")
	t.Logf("✓ Correctly rejected: %v", err)

	// Try to approve decision without session
	t.Log("Test 2: Approve decision without session")
	err = client.ApproveDecision(ctx, "dec-001", "test", "test")
	assert.Error(t, err, "Should fail without active session")
	t.Logf("✓ Correctly rejected: %v", err)

	// Create session
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)

	// Try to create another session (might succeed or fail depending on implementation)
	t.Log("Test 3: Create second session")
	sessionID2, err := client.CreateSession(ctx, operatorID+"_2")
	if err != nil {
		t.Logf("✓ Correctly rejected duplicate session: %v", err)
	} else {
		t.Logf("⚠️  Allowed second session: %s (implementation allows overwrite)", sessionID2)
	}

	// Close session
	err = client.CloseSession(ctx)
	require.NoError(t, err)

	// Try to use session after closing
	t.Log("Test 4: Operations after session close")
	_, err = client.ListPendingDecisions(ctx, 10, "PENDING", "")
	assert.Error(t, err, "Should fail after session closed")
	t.Logf("✓ Correctly rejected: %v", err)

	t.Log("✓ All invalid sequences handled correctly")
}

// TestChaos_HighErrorRate tests behavior under high error rate
func TestChaos_HighErrorRate(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping chaos test")
		return
	}
	defer client.Close()

	t.Log("Testing behavior under high error rate...")

	// Create session
	ctx := context.Background()
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	// Generate high error rate by requesting invalid decisions
	numRequests := 100
	var errors atomic.Int64
	var successes atomic.Int64

	var wg sync.WaitGroup

	for i := 0; i < numRequests; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()

			// Request invalid decision ID (should fail or return empty)
			decisionID := fmt.Sprintf("invalid-decision-%d", id)
			_, err := client.GetDecision(ctx, decisionID)

			if err != nil {
				errors.Add(1)
			} else {
				successes.Add(1)
			}
		}(i)
	}

	wg.Wait()

	errorRate := float64(errors.Load()) / float64(numRequests) * 100

	t.Logf("High error rate test: %d errors, %d successes (%.2f%% error rate)",
		errors.Load(), successes.Load(), errorRate)

	// Client should handle errors gracefully without crashing
	t.Log("✓ Client handled high error rate without crashing")

	// Verify client still works after high error rate
	healthy, err := client.HealthCheck(context.Background())
	assert.NoError(t, err, "Client should still be functional")
	assert.True(t, healthy, "Server should still be healthy")

	t.Log("✓ Client recovered and remains functional after error storm")
}

// TestChaos_ResourceExhaustion tests behavior under resource exhaustion
func TestChaos_ResourceExhaustion(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping chaos test")
		return
	}
	defer client.Close()

	t.Log("Testing behavior under resource exhaustion...")

	// Create session
	ctx := context.Background()
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	// Simulate resource exhaustion by making many large requests concurrently
	concurrency := 100
	requestsPerGoroutine := 50

	var wg sync.WaitGroup
	var totalOps atomic.Int64
	var failedOps atomic.Int64

	startTime := time.Now()

	for i := 0; i < concurrency; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			for j := 0; j < requestsPerGoroutine; j++ {
				ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)

				// Make a request
				_, err := client.ListPendingDecisions(ctx, 100, "PENDING", "")

				cancel()

				totalOps.Add(1)
				if err != nil {
					failedOps.Add(1)
				}
			}
		}()
	}

	wg.Wait()
	duration := time.Since(startTime)

	total := totalOps.Load()
	failed := failedOps.Load()
	successRate := float64(total-failed) / float64(total) * 100

	t.Logf("Resource exhaustion test:")
	t.Logf("  Total operations: %d", total)
	t.Logf("  Failed: %d", failed)
	t.Logf("  Success rate: %.2f%%", successRate)
	t.Logf("  Duration: %v", duration)
	t.Logf("  Throughput: %.2f ops/s", float64(total)/duration.Seconds())

	// Should maintain reasonable success rate even under stress
	assert.Greater(t, successRate, 80.0, "Success rate should be > 80% even under stress")

	t.Log("✓ Client maintained stability under resource exhaustion")
}

// TestChaos_PartialServiceDegradation tests graceful degradation
func TestChaos_PartialServiceDegradation(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping chaos test")
		return
	}
	defer client.Close()

	t.Log("Testing graceful degradation under partial service failure...")

	ctx := context.Background()

	// Create session
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	// Test that core operations still work even if some fail
	operations := []struct {
		name string
		fn   func() error
	}{
		{"HealthCheck", func() error { _, err := client.HealthCheck(ctx); return err }},
		{"ListDecisions", func() error { _, err := client.ListPendingDecisions(ctx, 10, "PENDING", ""); return err }},
		{"GetMetrics", func() error { _, err := client.GetMetrics(ctx); return err }},
		{"GetSessionStats", func() error { _, err := client.GetSessionStats(ctx); return err }},
		{"ApproveInvalidDecision", func() error { return client.ApproveDecision(ctx, "nonexistent", "test", "test") }},
	}

	successCount := 0
	for _, op := range operations {
		err := op.fn()
		if err != nil {
			t.Logf("✗ %s: %v", op.name, err)
		} else {
			t.Logf("✓ %s: Success", op.name)
			successCount++
		}
	}

	// At least core operations should work
	assert.Greater(t, successCount, len(operations)/2, "At least half of operations should succeed")

	t.Logf("✓ Service degraded gracefully: %d/%d operations succeeded", successCount, len(operations))
}

// TestChaos_StressRecovery tests recovery after stress
func TestChaos_StressRecovery(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping chaos test in short mode")
	}

	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping chaos test")
		return
	}
	defer client.Close()

	t.Log("Testing recovery after stress period...")

	ctx := context.Background()
	_, err = client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	defer client.CloseSession(ctx)

	// Stress phase
	t.Log("Phase 1: Applying stress (100 rapid operations)...")
	for i := 0; i < 100; i++ {
		client.HealthCheck(ctx)
	}

	// Recovery phase
	t.Log("Phase 2: Recovery period (5 seconds)...")
	time.Sleep(5 * time.Second)

	// Validation phase
	t.Log("Phase 3: Validating recovery...")
	successCount := 0
	for i := 0; i < 10; i++ {
		_, err := client.HealthCheck(ctx)
		if err == nil {
			successCount++
		}
		time.Sleep(100 * time.Millisecond)
	}

	recoveryRate := float64(successCount) / 10.0 * 100
	t.Logf("Recovery rate: %.2f%% (%d/10 operations succeeded)", recoveryRate, successCount)

	assert.Greater(t, recoveryRate, 90.0, "Should recover to > 90% success rate")

	t.Log("✓ Client recovered successfully after stress")
}
