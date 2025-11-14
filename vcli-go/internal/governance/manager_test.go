package governance

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// MOCK CLIENT FOR TESTING
// ============================================================================

// mockClient implements the Client interface for testing
type mockClient struct {
	// Session Management
	createSessionFunc func(ctx context.Context, operatorName, operatorRole string) (*Session, error)
	setSessionIDFunc  func(sessionID string)

	// Decision Operations
	approveDecisionFunc  func(ctx context.Context, decisionID, comment string) error
	rejectDecisionFunc   func(ctx context.Context, decisionID, reason string) error
	escalateDecisionFunc func(ctx context.Context, decisionID, reason string) error
	getDecisionFunc      func(ctx context.Context, decisionID string) (*Decision, error)
	listDecisionsFunc    func(ctx context.Context, filter *DecisionFilter) ([]*Decision, error)

	// Metrics & Health
	getMetricsFunc     func(ctx context.Context) (*DecisionMetrics, error)
	getSessionStatsFunc func(ctx context.Context) (*SessionStats, error)
	healthCheckFunc    func(ctx context.Context) (bool, error)
	pingServerFunc     func(ctx context.Context) (time.Duration, error)

	// Lifecycle
	closeFunc func() error

	// State tracking
	sessionID string
	closed    bool
}

func newMockClient() *mockClient {
	return &mockClient{}
}

func (m *mockClient) CreateSession(ctx context.Context, operatorName, operatorRole string) (*Session, error) {
	if m.createSessionFunc != nil {
		return m.createSessionFunc(ctx, operatorName, operatorRole)
	}
	return &Session{
		SessionID:    "session-123",
		OperatorID:   "operator-1",
		OperatorName: operatorName,
		OperatorRole: operatorRole,
		CreatedAt:    time.Now(),
		Active:       true,
	}, nil
}

func (m *mockClient) SetSessionID(sessionID string) {
	m.sessionID = sessionID
	if m.setSessionIDFunc != nil {
		m.setSessionIDFunc(sessionID)
	}
}

func (m *mockClient) ApproveDecision(ctx context.Context, decisionID, comment string) error {
	if m.approveDecisionFunc != nil {
		return m.approveDecisionFunc(ctx, decisionID, comment)
	}
	return nil
}

func (m *mockClient) RejectDecision(ctx context.Context, decisionID, reason string) error {
	if m.rejectDecisionFunc != nil {
		return m.rejectDecisionFunc(ctx, decisionID, reason)
	}
	return nil
}

func (m *mockClient) EscalateDecision(ctx context.Context, decisionID, reason string) error {
	if m.escalateDecisionFunc != nil {
		return m.escalateDecisionFunc(ctx, decisionID, reason)
	}
	return nil
}

func (m *mockClient) GetDecision(ctx context.Context, decisionID string) (*Decision, error) {
	if m.getDecisionFunc != nil {
		return m.getDecisionFunc(ctx, decisionID)
	}
	return &Decision{DecisionID: decisionID}, nil
}

func (m *mockClient) ListDecisions(ctx context.Context, filter *DecisionFilter) ([]*Decision, error) {
	if m.listDecisionsFunc != nil {
		return m.listDecisionsFunc(ctx, filter)
	}
	return []*Decision{}, nil
}

func (m *mockClient) GetMetrics(ctx context.Context) (*DecisionMetrics, error) {
	if m.getMetricsFunc != nil {
		return m.getMetricsFunc(ctx)
	}
	return &DecisionMetrics{
		TotalPending:  5,
		TotalApproved: 10,
		Timestamp:     time.Now(),
	}, nil
}

func (m *mockClient) GetSessionStats(ctx context.Context) (*SessionStats, error) {
	if m.getSessionStatsFunc != nil {
		return m.getSessionStatsFunc(ctx)
	}
	return &SessionStats{}, nil
}

func (m *mockClient) HealthCheck(ctx context.Context) (bool, error) {
	if m.healthCheckFunc != nil {
		return m.healthCheckFunc(ctx)
	}
	return true, nil
}

func (m *mockClient) PingServer(ctx context.Context) (time.Duration, error) {
	if m.pingServerFunc != nil {
		return m.pingServerFunc(ctx)
	}
	return time.Millisecond * 10, nil
}

func (m *mockClient) Close() error {
	m.closed = true
	if m.closeFunc != nil {
		return m.closeFunc()
	}
	return nil
}

// ============================================================================
// MANAGER CONSTRUCTOR TESTS
// ============================================================================

func TestNewManager(t *testing.T) {
	t.Run("creates manager with default HTTP backend", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		require.NotNil(t, mgr)
		assert.Equal(t, "http://localhost:8080", mgr.serverURL)
		assert.Equal(t, "operator-1", mgr.operatorID)
		assert.Equal(t, "session-123", mgr.sessionID)
		assert.Equal(t, BackendHTTP, mgr.backendType)
		assert.NotNil(t, mgr.pendingDecisions)
		assert.NotNil(t, mgr.resolvedDecisions)
		assert.NotNil(t, mgr.decisionCh)
		assert.NotNil(t, mgr.eventCh)
		assert.NotNil(t, mgr.errorCh)
		assert.NotNil(t, mgr.stopCh)
		assert.False(t, mgr.running)
	})
}

func TestNewManagerWithBackend(t *testing.T) {
	t.Run("creates manager with HTTP backend", func(t *testing.T) {
		mgr := NewManagerWithBackend("http://localhost:8080", "operator-1", "session-123", BackendHTTP)

		require.NotNil(t, mgr)
		assert.Equal(t, BackendHTTP, mgr.backendType)
	})

	t.Run("creates manager with gRPC backend", func(t *testing.T) {
		mgr := NewManagerWithBackend("localhost:50051", "operator-1", "session-123", BackendGRPC)

		require.NotNil(t, mgr)
		assert.Equal(t, BackendGRPC, mgr.backendType)
	})
}

// ============================================================================
// MANAGER LIFECYCLE TESTS
// ============================================================================

func TestManagerStop(t *testing.T) {
	t.Run("stops non-running manager without error", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		err := mgr.Stop(context.Background())

		require.NoError(t, err)
	})

	t.Run("stops running manager", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mgr.running = true

		err := mgr.Stop(context.Background())

		require.NoError(t, err)
		assert.False(t, mgr.running)
	})
}

// ============================================================================
// DECISION OPERATION TESTS
// ============================================================================

func TestManagerApproveDecision(t *testing.T) {
	t.Run("approves pending decision successfully", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mgr.client = newMockClient()

		// Add pending decision
		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusPending,
			ActionType: "block_ip",
			Target:     "192.168.1.1",
		}
		mgr.pendingDecisions[decision.DecisionID] = decision

		err := mgr.ApproveDecision(context.Background(), "decision-123", "Looks good")

		require.NoError(t, err)
		assert.Equal(t, DecisionStatusApproved, decision.Status)
		assert.Equal(t, "operator-1", decision.OperatorID)
		assert.Equal(t, "approve", decision.OperatorDecision)
		assert.Equal(t, "Looks good", decision.OperatorNotes)
		assert.NotNil(t, decision.ResolvedAt)
	})

	t.Run("error when decision not found", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mgr.client = newMockClient()

		err := mgr.ApproveDecision(context.Background(), "nonexistent", "comment")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "decision not found")
	})

	t.Run("error when decision not pending", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mgr.client = newMockClient()

		// Add already-approved decision
		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusApproved,
		}
		mgr.pendingDecisions[decision.DecisionID] = decision

		err := mgr.ApproveDecision(context.Background(), "decision-123", "comment")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "decision not pending")
	})

	t.Run("error when backend approval fails", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mock := newMockClient()
		mock.approveDecisionFunc = func(ctx context.Context, decisionID, comment string) error {
			return errors.New("backend error")
		}
		mgr.client = mock

		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusPending,
		}
		mgr.pendingDecisions[decision.DecisionID] = decision

		err := mgr.ApproveDecision(context.Background(), "decision-123", "comment")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to approve decision")
		assert.Contains(t, err.Error(), "backend error")
	})
}

func TestManagerRejectDecision(t *testing.T) {
	t.Run("rejects pending decision successfully", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mgr.client = newMockClient()

		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusPending,
			ActionType: "block_ip",
		}
		mgr.pendingDecisions[decision.DecisionID] = decision

		err := mgr.RejectDecision(context.Background(), "decision-123", "False positive")

		require.NoError(t, err)
		assert.Equal(t, DecisionStatusRejected, decision.Status)
		assert.Equal(t, "operator-1", decision.OperatorID)
		assert.Equal(t, "reject", decision.OperatorDecision)
		assert.Equal(t, "False positive", decision.OperatorNotes)
		assert.NotNil(t, decision.ResolvedAt)
	})

	t.Run("error when decision not found", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mgr.client = newMockClient()

		err := mgr.RejectDecision(context.Background(), "nonexistent", "reason")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "decision not found")
	})

	t.Run("error when decision not pending", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mgr.client = newMockClient()

		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusRejected,
		}
		mgr.pendingDecisions[decision.DecisionID] = decision

		err := mgr.RejectDecision(context.Background(), "decision-123", "reason")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "decision not pending")
	})

	t.Run("error when backend rejection fails", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mock := newMockClient()
		mock.rejectDecisionFunc = func(ctx context.Context, decisionID, reason string) error {
			return errors.New("backend error")
		}
		mgr.client = mock

		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusPending,
		}
		mgr.pendingDecisions[decision.DecisionID] = decision

		err := mgr.RejectDecision(context.Background(), "decision-123", "reason")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to reject decision")
	})
}

func TestManagerEscalateDecision(t *testing.T) {
	t.Run("escalates decision successfully", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mgr.client = newMockClient()

		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusPending,
		}
		mgr.pendingDecisions[decision.DecisionID] = decision

		// Capture emitted event
		go func() {
			<-mgr.eventCh // Consume the event
		}()

		err := mgr.EscalateDecision(context.Background(), "decision-123", "Need senior review")

		require.NoError(t, err)
		assert.Equal(t, DecisionStatusEscalated, decision.Status)
		assert.Equal(t, "operator-1", decision.OperatorID)
		assert.Equal(t, "escalate", decision.OperatorDecision)
		assert.Equal(t, "Need senior review", decision.OperatorNotes)
	})

	t.Run("error when decision not found", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mgr.client = newMockClient()

		err := mgr.EscalateDecision(context.Background(), "nonexistent", "reason")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "decision not found")
	})

	t.Run("error when backend escalation fails", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")
		mock := newMockClient()
		mock.escalateDecisionFunc = func(ctx context.Context, decisionID, reason string) error {
			return errors.New("backend error")
		}
		mgr.client = mock

		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusPending,
		}
		mgr.pendingDecisions[decision.DecisionID] = decision

		err := mgr.EscalateDecision(context.Background(), "decision-123", "reason")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to escalate decision")
	})
}

// ============================================================================
// DECISION QUERY TESTS
// ============================================================================

func TestManagerGetPendingDecisions(t *testing.T) {
	t.Run("returns empty list when no decisions", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		decisions := mgr.GetPendingDecisions()

		require.NotNil(t, decisions)
		assert.Len(t, decisions, 0)
	})

	t.Run("returns all pending decisions", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		mgr.pendingDecisions["decision-1"] = &Decision{DecisionID: "decision-1"}
		mgr.pendingDecisions["decision-2"] = &Decision{DecisionID: "decision-2"}
		mgr.pendingDecisions["decision-3"] = &Decision{DecisionID: "decision-3"}

		decisions := mgr.GetPendingDecisions()

		require.Len(t, decisions, 3)
	})
}

func TestManagerGetDecision(t *testing.T) {
	t.Run("retrieves pending decision", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		expected := &Decision{
			DecisionID: "decision-123",
			ActionType: "block_ip",
			Target:     "192.168.1.1",
		}
		mgr.pendingDecisions["decision-123"] = expected

		decision, err := mgr.GetDecision("decision-123")

		require.NoError(t, err)
		assert.Equal(t, expected, decision)
	})

	t.Run("retrieves resolved decision", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		expected := &Decision{
			DecisionID: "decision-456",
			Status:     DecisionStatusApproved,
		}
		mgr.resolvedDecisions["decision-456"] = expected

		decision, err := mgr.GetDecision("decision-456")

		require.NoError(t, err)
		assert.Equal(t, expected, decision)
	})

	t.Run("error when decision not found", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		decision, err := mgr.GetDecision("nonexistent")

		require.Error(t, err)
		assert.Nil(t, decision)
		assert.Contains(t, err.Error(), "decision not found")
	})

	t.Run("prefers pending over resolved when both exist", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		pending := &Decision{DecisionID: "decision-123", Status: DecisionStatusPending}
		resolved := &Decision{DecisionID: "decision-123", Status: DecisionStatusApproved}

		mgr.pendingDecisions["decision-123"] = pending
		mgr.resolvedDecisions["decision-123"] = resolved

		decision, err := mgr.GetDecision("decision-123")

		require.NoError(t, err)
		assert.Equal(t, DecisionStatusPending, decision.Status)
	})
}

// ============================================================================
// METRICS AND STATUS TESTS
// ============================================================================

func TestManagerGetMetrics(t *testing.T) {
	t.Run("returns current metrics", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		mgr.metrics = DecisionMetrics{
			TotalPending:  5,
			TotalApproved: 10,
			TotalRejected: 2,
		}

		metrics := mgr.GetMetrics()

		assert.Equal(t, 5, metrics.TotalPending)
		assert.Equal(t, 10, metrics.TotalApproved)
		assert.Equal(t, 2, metrics.TotalRejected)
	})
}

func TestManagerGetConnectionStatus(t *testing.T) {
	t.Run("returns disconnected when no SSE client", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		status := mgr.GetConnectionStatus()

		assert.False(t, status.Connected)
		assert.Equal(t, "http://localhost:8080", status.ServerURL)
	})
}

// ============================================================================
// CHANNEL ACCESSOR TESTS
// ============================================================================

func TestManagerChannels(t *testing.T) {
	t.Run("Decisions returns decision channel", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		ch := mgr.Decisions()

		require.NotNil(t, ch)
	})

	t.Run("Events returns event channel", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		ch := mgr.Events()

		require.NotNil(t, ch)
	})

	t.Run("Errors returns error channel", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		ch := mgr.Errors()

		require.NotNil(t, ch)
	})
}

// ============================================================================
// INTERNAL METHOD TESTS
// ============================================================================

func TestManagerAddPendingDecision(t *testing.T) {
	t.Run("adds decision to pending queue", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		decision := &Decision{
			DecisionID: "decision-123",
			ActionType: "block_ip",
		}

		// Consume channels
		go func() {
			<-mgr.decisionCh
			<-mgr.eventCh
		}()

		mgr.addPendingDecision(decision)

		assert.Len(t, mgr.pendingDecisions, 1)
		assert.Equal(t, decision, mgr.pendingDecisions["decision-123"])
	})

	t.Run("emits decision to channel", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		decision := &Decision{DecisionID: "decision-123"}

		// Consume event channel
		go func() {
			<-mgr.eventCh
		}()

		go mgr.addPendingDecision(decision)

		received := <-mgr.decisionCh
		assert.Equal(t, decision, received)
	})

	t.Run("emits event", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		decision := &Decision{DecisionID: "decision-123"}

		// Consume decision channel
		go func() {
			<-mgr.decisionCh
		}()

		go mgr.addPendingDecision(decision)

		event := <-mgr.eventCh
		assert.Equal(t, EventDecisionAdded, event.Type)
		assert.Equal(t, decision, event.Decision)
	})
}

func TestManagerResolveDecision(t *testing.T) {
	t.Run("moves decision from pending to resolved", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusApproved,
		}
		mgr.pendingDecisions["decision-123"] = decision

		// Consume event
		go func() {
			<-mgr.eventCh
		}()

		mgr.resolveDecision(decision)

		assert.Len(t, mgr.pendingDecisions, 0)
		assert.Len(t, mgr.resolvedDecisions, 1)
		assert.Equal(t, decision, mgr.resolvedDecisions["decision-123"])
	})

	t.Run("emits resolution event", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		decision := &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusApproved,
		}
		mgr.pendingDecisions["decision-123"] = decision

		go mgr.resolveDecision(decision)

		event := <-mgr.eventCh
		assert.Equal(t, EventDecisionResolved, event.Type)
		assert.Equal(t, decision, event.Decision)
	})

	t.Run("limits resolved cache size", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		// Consume events
		go func() {
			for i := 0; i < 1002; i++ {
				<-mgr.eventCh
			}
		}()

		// Fill resolved cache to exactly 1000
		for i := 0; i < 1000; i++ {
			decision := &Decision{
				DecisionID: string(rune(i)),
				Status:     DecisionStatusApproved,
			}
			mgr.resolvedDecisions[decision.DecisionID] = decision
		}

		// Add one more to trigger eviction (1000 + 1 = 1001, then removes 1 = 1000)
		decision := &Decision{
			DecisionID: "decision-final",
			Status:     DecisionStatusApproved,
		}
		mgr.pendingDecisions[decision.DecisionID] = decision

		mgr.resolveDecision(decision)

		// After adding to 1001 and removing 1, should have 1000
		assert.Equal(t, 1000, len(mgr.resolvedDecisions))
	})
}

func TestManagerEmitEvent(t *testing.T) {
	t.Run("emits event to channel", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		event := ManagerEvent{
			Type:      EventConnectionEstablished,
			Timestamp: time.Now(),
		}

		go mgr.emitEvent(event)

		received := <-mgr.eventCh
		assert.Equal(t, EventConnectionEstablished, received.Type)
	})

	t.Run("drops event when channel full", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		// Fill channel
		for i := 0; i < 100; i++ {
			mgr.eventCh <- ManagerEvent{Type: EventMetricsUpdated}
		}

		// Should not block
		mgr.emitEvent(ManagerEvent{Type: EventConnectionEstablished})
	})
}

func TestManagerEmitError(t *testing.T) {
	t.Run("emits error to error channel", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		testErr := errors.New("test error")

		go mgr.emitError(testErr)

		received := <-mgr.errorCh
		assert.Equal(t, testErr, received)
	})

	t.Run("emits error as event when error channel full", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		// Fill error channel
		for i := 0; i < 10; i++ {
			mgr.errorCh <- errors.New("filler")
		}

		testErr := errors.New("test error")

		go mgr.emitError(testErr)

		// Should receive as event instead
		event := <-mgr.eventCh
		assert.Equal(t, EventError, event.Type)
		assert.Equal(t, testErr, event.Error)
	})

	t.Run("drops error when both channels full", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		// Fill both channels
		for i := 0; i < 10; i++ {
			mgr.errorCh <- errors.New("filler")
		}
		for i := 0; i < 100; i++ {
			mgr.eventCh <- ManagerEvent{Type: EventMetricsUpdated}
		}

		// Should not block
		mgr.emitError(errors.New("dropped error"))
	})
}

// ============================================================================
// SSE EVENT HANDLING TESTS
// ============================================================================

func TestManagerHandleSSEEvent(t *testing.T) {
	t.Run("handles decision_pending event", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		// Consume channels
		go func() {
			<-mgr.decisionCh
			<-mgr.eventCh
		}()

		event := &SSEEvent{
			EventType: "decision_pending",
			EventID:   "event-123",
			Data: map[string]interface{}{
				"decision_id": "decision-123",
				"action_type": "block_ip",
				"status":      "PENDING",
				"created_at":  time.Now().Format(time.RFC3339),
			},
		}

		mgr.handleSSEEvent(event)

		// Give it time to process
		time.Sleep(10 * time.Millisecond)

		assert.Len(t, mgr.pendingDecisions, 1)
	})

	t.Run("handles decision_resolved event", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		// Add pending decision first
		mgr.pendingDecisions["decision-123"] = &Decision{
			DecisionID: "decision-123",
			Status:     DecisionStatusPending,
		}

		// Consume event
		go func() {
			<-mgr.eventCh
		}()

		event := &SSEEvent{
			EventType: "decision_resolved",
			EventID:   "event-456",
			Data: map[string]interface{}{
				"decision_id": "decision-123",
				"status":      "APPROVED",
				"created_at":  time.Now().Format(time.RFC3339),
			},
		}

		mgr.handleSSEEvent(event)

		// Give it time to process
		time.Sleep(10 * time.Millisecond)

		assert.Len(t, mgr.pendingDecisions, 0)
		assert.Len(t, mgr.resolvedDecisions, 1)
	})

	t.Run("handles heartbeat event", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		event := &SSEEvent{
			EventType: "heartbeat",
			EventID:   "heartbeat-1",
		}

		// Should not error
		mgr.handleSSEEvent(event)
	})

	t.Run("handles unknown event type", func(t *testing.T) {
		mgr := NewManager("http://localhost:8080", "operator-1", "session-123")

		// Consume error
		go func() {
			<-mgr.errorCh
		}()

		event := &SSEEvent{
			EventType: "unknown_event",
			EventID:   "unknown-1",
		}

		mgr.handleSSEEvent(event)

		// Give it time to process
		time.Sleep(10 * time.Millisecond)
	})
}

// ============================================================================
// MANAGER EVENT TYPE TESTS
// ============================================================================

func TestManagerEventType(t *testing.T) {
	t.Run("event type constants are correct", func(t *testing.T) {
		assert.Equal(t, ManagerEventType("decision_added"), EventDecisionAdded)
		assert.Equal(t, ManagerEventType("decision_resolved"), EventDecisionResolved)
		assert.Equal(t, ManagerEventType("decision_escalated"), EventDecisionEscalated)
		assert.Equal(t, ManagerEventType("decision_expired"), EventDecisionExpired)
		assert.Equal(t, ManagerEventType("metrics_updated"), EventMetricsUpdated)
		assert.Equal(t, ManagerEventType("connection_established"), EventConnectionEstablished)
		assert.Equal(t, ManagerEventType("connection_lost"), EventConnectionLost)
		assert.Equal(t, ManagerEventType("error"), EventError)
	})
}
