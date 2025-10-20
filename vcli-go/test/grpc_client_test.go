// +build integration

package test

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	grpcclient "github.com/verticedev/vcli-go/internal/grpc"
)

func TestGovernanceGRPCClient_HealthCheck(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient("localhost:50051")
	if err != nil {
		t.Skip("gRPC server not running, skipping test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Test health check
	healthy, err := client.HealthCheck(ctx)
	require.NoError(t, err)
	assert.True(t, healthy, "Server should be healthy")
}

func TestGovernanceGRPCClient_SessionLifecycle(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient("localhost:50051")
	if err != nil {
		t.Skip("gRPC server not running, skipping test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Create session
	sessionID, err := client.CreateSession(ctx, "test_operator")
	require.NoError(t, err)
	assert.NotEmpty(t, sessionID, "Session ID should not be empty")

	// Verify session ID is stored
	assert.Equal(t, sessionID, client.SessionID())
	assert.Equal(t, "test_operator", client.OperatorID())

	// Close session
	err = client.CloseSession(ctx)
	require.NoError(t, err)
}

func TestGovernanceGRPCClient_ListPendingDecisions(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient("localhost:50051")
	if err != nil {
		t.Skip("gRPC server not running, skipping test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Create session first
	_, err = client.CreateSession(ctx, "test_operator")
	require.NoError(t, err)

	// List pending decisions
	decisions, err := client.ListPendingDecisions(ctx, 10, "PENDING", "")
	require.NoError(t, err)
	assert.NotNil(t, decisions, "Decisions list should not be nil")

	// POC server should have mock decisions
	if len(decisions) > 0 {
		t.Logf("Found %d pending decisions", len(decisions))
		for i, decision := range decisions {
			t.Logf("Decision %d: ID=%s, Type=%s, Priority=%s, Status=%s",
				i+1, decision.DecisionId, decision.OperationType, decision.Priority, decision.Status)
		}
	}
}

func TestGovernanceGRPCClient_GetDecision(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient("localhost:50051")
	if err != nil {
		t.Skip("gRPC server not running, skipping test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Get a known POC decision
	decision, err := client.GetDecision(ctx, "dec-001")
	require.NoError(t, err)
	assert.NotNil(t, decision, "Decision should not be nil")
	assert.Equal(t, "dec-001", decision.DecisionId)
	t.Logf("Retrieved decision: %s (Type: %s, Priority: %s)",
		decision.DecisionId, decision.OperationType, decision.Priority)
}

func TestGovernanceGRPCClient_ApproveDecision(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient("localhost:50051")
	if err != nil {
		t.Skip("gRPC server not running, skipping test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Create session first
	_, err = client.CreateSession(ctx, "test_operator")
	require.NoError(t, err)

	// Approve a decision
	err = client.ApproveDecision(ctx, "dec-002",
		"Approved for testing",
		"Test case validation")
	require.NoError(t, err)

	// Verify decision was updated
	decision, err := client.GetDecision(ctx, "dec-002")
	require.NoError(t, err)
	assert.Equal(t, "APPROVED", decision.Status)
	t.Logf("Decision dec-002 successfully approved")
}

func TestGovernanceGRPCClient_GetMetrics(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient("localhost:50051")
	if err != nil {
		t.Skip("gRPC server not running, skipping test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Create session first
	_, err = client.CreateSession(ctx, "test_operator")
	require.NoError(t, err)

	// Get metrics
	metrics, err := client.GetMetrics(ctx)
	require.NoError(t, err)
	assert.NotNil(t, metrics, "Metrics should not be nil")

	t.Logf("Governance Metrics:")
	t.Logf("  Total Decisions: %d", metrics.TotalDecisions)
	t.Logf("  Pending: %d", metrics.PendingCount)
	t.Logf("  Approved: %d", metrics.ApprovedCount)
	t.Logf("  Rejected: %d", metrics.RejectedCount)
	t.Logf("  Escalated: %d", metrics.EscalatedCount)
	t.Logf("  Critical: %d", metrics.CriticalCount)
	t.Logf("  High Priority: %d", metrics.HighPriorityCount)
	t.Logf("  Avg Response Time: %.2fs", metrics.AvgResponseTimeSeconds)
	t.Logf("  Approval Rate: %.2f%%", metrics.ApprovalRate)
	t.Logf("  SLA Violations: %d", metrics.SlaViolations)
}

func TestGovernanceGRPCClient_GetSessionStats(t *testing.T) {
	// Skip if server not running
	client, err := grpcclient.NewGovernanceClient("localhost:50051")
	if err != nil {
		t.Skip("gRPC server not running, skipping test")
		return
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Create session first
	_, err = client.CreateSession(ctx, "test_operator")
	require.NoError(t, err)

	// Get session stats
	stats, err := client.GetSessionStats(ctx)
	require.NoError(t, err)
	assert.NotNil(t, stats, "Stats should not be nil")

	t.Logf("Session Stats for test_operator:")
	t.Logf("  Total Decisions: %d", stats.TotalDecisions)
	t.Logf("  Approved: %d", stats.Approved)
	t.Logf("  Rejected: %d", stats.Rejected)
	t.Logf("  Escalated: %d", stats.Escalated)
	t.Logf("  Avg Response Time: %.2fs", stats.AvgResponseTimeSeconds)
}
