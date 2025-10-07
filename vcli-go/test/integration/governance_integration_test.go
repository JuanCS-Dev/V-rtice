package integration

import (
	"context"
	"fmt"
	"testing"
	"time"

	gov "github.com/verticedev/vcli-go/internal/governance"
)

const (
	testServerURL  = "http://localhost:8001"
	testOperatorID = "integration_test_operator"
	testSessionID  = "integration_test_session"
)

// TestGovernanceBackendHealth tests basic connectivity to Python backend
func TestGovernanceBackendHealth(t *testing.T) {
	ctx := context.Background()
	client := gov.NewHTTPClient(testServerURL, testOperatorID)

	healthy, err := client.HealthCheck(ctx)
	if err != nil {
		t.Fatalf("Health check failed: %v", err)
	}

	if !healthy {
		t.Fatal("Backend is not healthy")
	}

	t.Log("✅ Backend health check passed")
}

// TestGovernanceBackendPing tests latency to Python backend
func TestGovernanceBackendPing(t *testing.T) {
	ctx := context.Background()
	client := gov.NewHTTPClient(testServerURL, testOperatorID)

	latency, err := client.PingServer(ctx)
	if err != nil {
		t.Fatalf("Ping failed: %v", err)
	}

	t.Logf("✅ Backend ping: %v", latency)

	if latency > 100*time.Millisecond {
		t.Logf("⚠️  High latency detected: %v (expected < 100ms)", latency)
	}
}

// TestGovernanceMetrics tests metrics retrieval
func TestGovernanceMetrics(t *testing.T) {
	ctx := context.Background()
	client := gov.NewHTTPClient(testServerURL, testOperatorID)

	metrics, err := client.GetMetrics(ctx)
	if err != nil {
		t.Fatalf("Failed to get metrics: %v", err)
	}

	t.Logf("✅ Metrics retrieved:")
	t.Logf("   Total Pending: %d", metrics.TotalPending)
	t.Logf("   Critical: %d", metrics.PendingCritical)
	t.Logf("   High: %d", metrics.PendingHigh)
	t.Logf("   Medium: %d", metrics.PendingMedium)
	t.Logf("   Low: %d", metrics.PendingLow)
	t.Logf("   Nearing SLA: %d", metrics.NearingSLA)
	t.Logf("   Breached SLA: %d", metrics.BreachedSLA)
}

// TestGovernanceListDecisions tests listing pending decisions
func TestGovernanceListDecisions(t *testing.T) {
	ctx := context.Background()
	client := gov.NewHTTPClient(testServerURL, testOperatorID)

	filter := &gov.DecisionFilter{
		Status: []gov.DecisionStatus{gov.DecisionStatusPending},
		Limit:  10,
	}

	decisions, err := client.ListDecisions(ctx, filter)
	if err != nil {
		t.Fatalf("Failed to list decisions: %v", err)
	}

	t.Logf("✅ Retrieved %d pending decisions", len(decisions))

	for i, decision := range decisions {
		t.Logf("   [%d] %s: %s → %s (risk: %s, confidence: %.2f%%)",
			i+1,
			decision.DecisionID,
			decision.ActionType,
			decision.Target,
			decision.RiskLevel,
			decision.Confidence*100)
	}
}

// TestGovernanceSSEConnection tests SSE client connection
func TestGovernanceSSEConnection(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	sseClient := gov.NewSSEClient(testServerURL, testOperatorID, testSessionID)

	// Connect to SSE stream
	if err := sseClient.Connect(ctx); err != nil {
		t.Fatalf("Failed to connect SSE: %v", err)
	}
	defer sseClient.Close()

	// Wait for connection to establish
	time.Sleep(2 * time.Second)

	status := sseClient.Status()

	if !status.Connected {
		t.Fatal("SSE client not connected")
	}

	t.Logf("✅ SSE connection established")
	t.Logf("   Server URL: %s", status.ServerURL)
	t.Logf("   Events received: %d", status.EventsReceived)
	t.Logf("   Bytes received: %d", status.BytesReceived)

	// Listen for events for a few seconds
	eventCount := 0
	timeout := time.After(5 * time.Second)

eventLoop:
	for {
		select {
		case event := <-sseClient.Events():
			eventCount++
			t.Logf("   Received event: %s (id: %s)", event.EventType, event.EventID)

		case err := <-sseClient.Errors():
			t.Logf("   SSE error: %v", err)

		case <-timeout:
			break eventLoop
		}
	}

	t.Logf("✅ Received %d events in 5 seconds", eventCount)
}

// TestGovernanceManagerIntegration tests full Manager integration
func TestGovernanceManagerIntegration(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	manager := gov.NewManager(testServerURL, testOperatorID, testSessionID)

	// Start manager
	if err := manager.Start(ctx); err != nil {
		t.Fatalf("Failed to start manager: %v", err)
	}
	defer manager.Stop(ctx)

	t.Log("✅ Manager started successfully")

	// Wait for initial sync
	time.Sleep(2 * time.Second)

	// Check connection status
	connStatus := manager.GetConnectionStatus()
	if !connStatus.Connected {
		t.Fatal("Manager not connected to backend")
	}

	t.Logf("✅ Manager connected:")
	t.Logf("   Events received: %d", connStatus.EventsReceived)
	t.Logf("   Last heartbeat: %v ago", time.Since(connStatus.LastHeartbeat))

	// Get pending decisions
	decisions := manager.GetPendingDecisions()
	t.Logf("✅ Pending decisions: %d", len(decisions))

	// Get metrics
	metrics := manager.GetMetrics()
	t.Logf("✅ Queue metrics:")
	t.Logf("   Total pending: %d", metrics.TotalPending)
	t.Logf("   Critical: %d", metrics.PendingCritical)
	t.Logf("   High: %d", metrics.PendingHigh)

	// Monitor events for a few seconds
	eventCount := 0
	decisionCount := 0
	timeout := time.After(5 * time.Second)

monitorLoop:
	for {
		select {
		case decision := <-manager.Decisions():
			decisionCount++
			t.Logf("   New decision: %s (%s)", decision.DecisionID, decision.RiskLevel)

		case event := <-manager.Events():
			eventCount++
			t.Logf("   Manager event: %s", event.Type)

		case err := <-manager.Errors():
			t.Logf("   Manager error: %v", err)

		case <-timeout:
			break monitorLoop
		}
	}

	t.Logf("✅ Monitoring complete:")
	t.Logf("   Events: %d", eventCount)
	t.Logf("   Decisions: %d", decisionCount)
}

// TestGovernanceE2EWorkflow tests end-to-end workflow
func TestGovernanceE2EWorkflow(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	manager := gov.NewManager(testServerURL, testOperatorID, testSessionID)

	if err := manager.Start(ctx); err != nil {
		t.Fatalf("Failed to start manager: %v", err)
	}
	defer manager.Stop(ctx)

	t.Log("✅ E2E test started")

	// Wait for initial sync
	time.Sleep(3 * time.Second)

	// Get pending decisions
	decisions := manager.GetPendingDecisions()

	if len(decisions) == 0 {
		t.Log("⚠️  No pending decisions to test with")
		t.Log("   You can create test decisions via the Python backend API")
		return
	}

	// Test approving first decision
	decision := decisions[0]
	t.Logf("📋 Testing approval of decision: %s", decision.DecisionID)
	t.Logf("   Action: %s → %s", decision.ActionType, decision.Target)
	t.Logf("   Risk: %s", decision.RiskLevel)
	t.Logf("   Confidence: %.2f%%", decision.Confidence*100)

	// Approve decision
	if err := manager.ApproveDecision(ctx, decision.DecisionID, "Approved via integration test"); err != nil {
		t.Fatalf("Failed to approve decision: %v", err)
	}

	t.Logf("✅ Decision approved successfully")

	// Wait for SSE confirmation
	timeout := time.After(5 * time.Second)
	resolved := false

confirmLoop:
	for {
		select {
		case event := <-manager.Events():
			if event.Type == gov.EventDecisionResolved {
				if event.Decision != nil && event.Decision.DecisionID == decision.DecisionID {
					resolved = true
					t.Logf("✅ SSE confirmation received: decision resolved")
					break confirmLoop
				}
			}

		case <-timeout:
			t.Log("⚠️  Timeout waiting for SSE confirmation")
			break confirmLoop
		}
	}

	if !resolved {
		t.Log("⚠️  SSE confirmation not received (may be timing issue)")
	}

	// Verify decision is no longer pending
	updatedDecisions := manager.GetPendingDecisions()
	found := false
	for _, d := range updatedDecisions {
		if d.DecisionID == decision.DecisionID {
			found = true
			break
		}
	}

	if found {
		t.Error("❌ Decision still in pending queue after approval")
	} else {
		t.Log("✅ Decision removed from pending queue")
	}

	t.Log("✅ E2E workflow test complete")
}
