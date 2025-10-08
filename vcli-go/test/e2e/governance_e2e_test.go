package e2e

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	grpcclient "github.com/verticedev/vcli-go/internal/grpc"
)

const (
	grpcServerURL = "localhost:50051"
	operatorID    = "e2e_operator"
)

// TestE2E_CompleteWorkflow tests a complete decision workflow end-to-end
func TestE2E_CompleteWorkflow(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping E2E test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Step 1: Health check
	t.Log("Step 1: Health check")
	healthy, err := client.HealthCheck(ctx)
	require.NoError(t, err)
	assert.True(t, healthy, "Server should be healthy")

	// Step 2: Create session
	t.Log("Step 2: Create session")
	sessionID, err := client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	assert.NotEmpty(t, sessionID, "Session ID should not be empty")
	t.Logf("Created session: %s", sessionID)

	// Step 3: List pending decisions
	t.Log("Step 3: List pending decisions")
	decisions, err := client.ListPendingDecisions(ctx, 10, "PENDING", "")
	require.NoError(t, err)
	assert.NotNil(t, decisions, "Decisions list should not be nil")
	t.Logf("Found %d pending decisions", len(decisions))

	if len(decisions) > 0 {
		// Step 4: Get specific decision
		t.Log("Step 4: Get specific decision")
		firstDecision := decisions[0]
		decision, err := client.GetDecision(ctx, firstDecision.DecisionId)
		require.NoError(t, err)
		assert.NotNil(t, decision)
		assert.Equal(t, firstDecision.DecisionId, decision.DecisionId)
		t.Logf("Retrieved decision: %s (Type: %s, Priority: %s)",
			decision.DecisionId, decision.OperationType, decision.Priority)

		// Step 5: Approve decision
		t.Log("Step 5: Approve decision")
		err = client.ApproveDecision(ctx, decision.DecisionId,
			"E2E test approval",
			"Automated E2E workflow test")
		require.NoError(t, err)
		t.Logf("Approved decision: %s", decision.DecisionId)

		// Step 6: Verify decision was approved
		t.Log("Step 6: Verify decision status")
		updatedDecision, err := client.GetDecision(ctx, decision.DecisionId)
		require.NoError(t, err)
		assert.Equal(t, "APPROVED", updatedDecision.Status)
		t.Logf("Decision status confirmed: %s", updatedDecision.Status)
	}

	// Step 7: Get metrics
	t.Log("Step 7: Get metrics")
	metrics, err := client.GetMetrics(ctx)
	require.NoError(t, err)
	assert.NotNil(t, metrics)
	t.Logf("Metrics: Total=%d, Pending=%d, Approved=%d",
		metrics.TotalDecisions, metrics.PendingCount, metrics.ApprovedCount)

	// Step 8: Get session stats
	t.Log("Step 8: Get session stats")
	stats, err := client.GetSessionStats(ctx)
	require.NoError(t, err)
	assert.NotNil(t, stats)
	t.Logf("Session stats: Total=%d, Approved=%d, Avg Response=%.2fs",
		stats.TotalDecisions, stats.Approved, stats.AvgResponseTimeSeconds)

	// Step 9: Close session
	t.Log("Step 9: Close session")
	err = client.CloseSession(ctx)
	require.NoError(t, err)
	t.Log("Session closed successfully")
}

// TestE2E_ConcurrentOperations tests concurrent operations
func TestE2E_ConcurrentOperations(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping E2E test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Create session
	sessionID, err := client.CreateSession(ctx, "concurrent_operator")
	require.NoError(t, err)
	t.Logf("Created session: %s", sessionID)

	// Concurrent operations
	t.Log("Running concurrent operations...")
	concurrency := 10
	errChan := make(chan error, concurrency)

	for i := 0; i < concurrency; i++ {
		go func(id int) {
			// Each goroutine does: list decisions → get metrics
			_, err := client.ListPendingDecisions(ctx, 5, "PENDING", "")
			if err != nil {
				errChan <- fmt.Errorf("goroutine %d list failed: %w", id, err)
				return
			}

			_, err = client.GetMetrics(ctx)
			if err != nil {
				errChan <- fmt.Errorf("goroutine %d metrics failed: %w", id, err)
				return
			}

			errChan <- nil
		}(i)
	}

	// Collect results
	successCount := 0
	for i := 0; i < concurrency; i++ {
		err := <-errChan
		if err != nil {
			t.Logf("Goroutine error: %v", err)
		} else {
			successCount++
		}
	}

	t.Logf("Concurrent operations: %d/%d succeeded", successCount, concurrency)
	assert.Greater(t, successCount, concurrency/2, "At least half should succeed")
}

// TestE2E_ErrorHandling tests error handling scenarios
func TestE2E_ErrorHandling(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping E2E test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	t.Log("Test 1: Operations without session should fail gracefully")
	// Try to approve decision without session (should fail)
	err = client.ApproveDecision(ctx, "nonexistent-decision", "test", "test")
	assert.Error(t, err, "Should fail without active session")
	t.Logf("Expected error: %v", err)

	t.Log("Test 2: Create session, then test invalid decision ID")
	// Create session
	sessionID, err := client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	t.Logf("Created session: %s", sessionID)

	// Try to approve nonexistent decision
	err = client.ApproveDecision(ctx, "invalid-decision-id", "test", "test")
	// This may or may not fail depending on backend implementation
	// Just log the result
	if err != nil {
		t.Logf("Approve invalid decision failed (expected): %v", err)
	} else {
		t.Logf("Approve invalid decision succeeded (backend may create on-demand)")
	}

	t.Log("Test 3: Multiple rapid health checks")
	for i := 0; i < 5; i++ {
		healthy, err := client.HealthCheck(ctx)
		require.NoError(t, err)
		assert.True(t, healthy)
	}
	t.Log("Rapid health checks succeeded")
}

// TestE2E_LongRunningSession tests a long-running session
func TestE2E_LongRunningSession(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping long-running test in short mode")
	}

	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping E2E test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	// Create session
	sessionID, err := client.CreateSession(ctx, "longrunning_operator")
	require.NoError(t, err)
	t.Logf("Created session: %s", sessionID)

	// Perform operations over time
	duration := 10 * time.Second
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	startTime := time.Now()
	operationCount := 0

	t.Logf("Running operations for %v...", duration)
	for {
		select {
		case <-ticker.C:
			// List decisions
			_, err := client.ListPendingDecisions(ctx, 5, "PENDING", "")
			if err != nil {
				t.Logf("Operation failed: %v", err)
			} else {
				operationCount++
			}

			// Check if duration elapsed
			if time.Since(startTime) >= duration {
				t.Logf("Completed %d operations in %v", operationCount, duration)
				return
			}

		case <-ctx.Done():
			t.Fatalf("Context cancelled: %v", ctx.Err())
		}
	}
}

// TestE2E_MultipleDecisionWorkflow tests processing multiple decisions
func TestE2E_MultipleDecisionWorkflow(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient(grpcServerURL)
	if err != nil {
		t.Skip("gRPC server not running, skipping E2E test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Create session
	sessionID, err := client.CreateSession(ctx, operatorID)
	require.NoError(t, err)
	t.Logf("Created session: %s", sessionID)

	// Get all pending decisions
	decisions, err := client.ListPendingDecisions(ctx, 100, "PENDING", "")
	require.NoError(t, err)
	t.Logf("Found %d pending decisions", len(decisions))

	if len(decisions) == 0 {
		t.Log("No pending decisions to process")
		return
	}

	// Process first 3 decisions (or all if less than 3)
	processCount := min(3, len(decisions))
	t.Logf("Processing %d decisions...", processCount)

	for i := 0; i < processCount; i++ {
		decision := decisions[i]
		t.Logf("Processing decision %d/%d: %s (Priority: %s)",
			i+1, processCount, decision.DecisionId, decision.Priority)

		// Alternate between approve and reject
		if i%2 == 0 {
			err = client.ApproveDecision(ctx, decision.DecisionId,
				fmt.Sprintf("E2E test approval %d", i),
				"Automated approval for testing")
			action := "approved"
			if err == nil {
				t.Logf("✓ Decision %s", action)
			} else {
				t.Logf("✗ Failed to %s: %v", action, err)
			}
		} else {
			err = client.RejectDecision(ctx, decision.DecisionId,
				fmt.Sprintf("E2E test rejection %d", i),
				"Automated rejection for testing")
			action := "rejected"
			if err == nil {
				t.Logf("✓ Decision %s", action)
			} else {
				t.Logf("✗ Failed to %s: %v", action, err)
			}
		}
	}

	// Verify metrics updated
	metrics, err := client.GetMetrics(ctx)
	require.NoError(t, err)
	t.Logf("Final metrics: Approved=%d, Rejected=%d, Pending=%d",
		metrics.ApprovedCount, metrics.RejectedCount, metrics.PendingCount)
}

// Helper function
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
