package governance

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Manager coordinates Governance decision queue and backend communication
type Manager struct {
	// Backend clients
	sseClient  *SSEClient
	httpClient *HTTPClient

	// Local decision queue (synchronized with backend)
	mu               sync.RWMutex
	pendingDecisions map[string]*Decision // decision_id -> Decision
	resolvedDecisions map[string]*Decision // Recently resolved decisions (limited cache)

	// Metrics
	metrics DecisionMetrics

	// Event broadcasting
	decisionCh chan *Decision
	eventCh    chan ManagerEvent
	errorCh    chan error

	// Configuration
	serverURL  string
	operatorID string
	sessionID  string

	// State
	running bool
	stopCh  chan struct{}
}

// ManagerEvent represents high-level events from the manager
type ManagerEvent struct {
	Type      ManagerEventType
	Decision  *Decision
	Metrics   *DecisionMetrics
	Error     error
	Timestamp time.Time
}

// ManagerEventType represents the type of manager event
type ManagerEventType string

const (
	EventDecisionAdded      ManagerEventType = "decision_added"
	EventDecisionResolved   ManagerEventType = "decision_resolved"
	EventDecisionEscalated  ManagerEventType = "decision_escalated"
	EventDecisionExpired    ManagerEventType = "decision_expired"
	EventMetricsUpdated     ManagerEventType = "metrics_updated"
	EventConnectionEstablished ManagerEventType = "connection_established"
	EventConnectionLost     ManagerEventType = "connection_lost"
	EventError              ManagerEventType = "error"
)

// NewManager creates a new Governance manager
func NewManager(serverURL, operatorID, sessionID string) *Manager {
	return &Manager{
		serverURL:         serverURL,
		operatorID:        operatorID,
		sessionID:         sessionID,
		pendingDecisions:  make(map[string]*Decision),
		resolvedDecisions: make(map[string]*Decision),
		decisionCh:        make(chan *Decision, 100),
		eventCh:           make(chan ManagerEvent, 100),
		errorCh:           make(chan error, 10),
		stopCh:            make(chan struct{}),
	}
}

// Start starts the governance manager and establishes backend connection
func (m *Manager) Start(ctx context.Context) error {
	m.mu.Lock()
	if m.running {
		m.mu.Unlock()
		return fmt.Errorf("manager already running")
	}
	m.running = true
	m.mu.Unlock()

	// Create HTTP client
	m.httpClient = NewHTTPClient(m.serverURL, m.operatorID)

	// Health check before starting
	healthy, err := m.httpClient.HealthCheck(ctx)
	if err != nil || !healthy {
		return fmt.Errorf("backend health check failed: %w", err)
	}

	// Create operator session
	session, err := m.httpClient.CreateSession(ctx, m.operatorID, "soc_operator")
	if err != nil {
		return fmt.Errorf("failed to create session: %w", err)
	}

	// Store session ID
	m.mu.Lock()
	m.sessionID = session.SessionID
	m.mu.Unlock()

	// Create SSE client with session ID
	m.sseClient = NewSSEClient(m.serverURL, m.operatorID, m.sessionID)

	// Connect SSE stream
	if err := m.sseClient.Connect(ctx); err != nil {
		return fmt.Errorf("failed to connect SSE: %w", err)
	}

	// Start event processing
	go m.processEvents(ctx)
	go m.metricsUpdateLoop(ctx)

	// Load initial pending decisions
	if err := m.syncPendingDecisions(ctx); err != nil {
		m.emitError(fmt.Errorf("failed to sync initial decisions: %w", err))
	}

	m.emitEvent(ManagerEvent{
		Type:      EventConnectionEstablished,
		Timestamp: time.Now(),
	})

	return nil
}

// Stop stops the governance manager
func (m *Manager) Stop(ctx context.Context) error {
	m.mu.Lock()
	if !m.running {
		m.mu.Unlock()
		return nil
	}
	m.running = false
	m.mu.Unlock()

	close(m.stopCh)

	if m.sseClient != nil {
		m.sseClient.Close()
	}

	return nil
}

// Decisions returns channel for receiving pending decisions
func (m *Manager) Decisions() <-chan *Decision {
	return m.decisionCh
}

// Events returns channel for manager events
func (m *Manager) Events() <-chan ManagerEvent {
	return m.eventCh
}

// Errors returns channel for errors
func (m *Manager) Errors() <-chan error {
	return m.errorCh
}

// ApproveDecision approves a pending decision
func (m *Manager) ApproveDecision(ctx context.Context, decisionID, comment string) error {
	// Verify decision exists and is pending
	m.mu.RLock()
	decision, exists := m.pendingDecisions[decisionID]
	m.mu.RUnlock()

	if !exists {
		return fmt.Errorf("decision not found: %s", decisionID)
	}

	if decision.Status != DecisionStatusPending {
		return fmt.Errorf("decision not pending: %s (status: %s)", decisionID, decision.Status)
	}

	// Submit approval to backend
	if err := m.httpClient.ApproveDecision(ctx, decisionID, comment); err != nil {
		return fmt.Errorf("failed to approve decision: %w", err)
	}

	// Update local state (will be confirmed via SSE event)
	m.mu.Lock()
	decision.Status = DecisionStatusApproved
	decision.OperatorID = m.operatorID
	decision.OperatorDecision = "approve"
	decision.OperatorNotes = comment
	now := time.Now()
	decision.ResolvedAt = &now
	m.mu.Unlock()

	return nil
}

// RejectDecision rejects a pending decision
func (m *Manager) RejectDecision(ctx context.Context, decisionID, comment string) error {
	m.mu.RLock()
	decision, exists := m.pendingDecisions[decisionID]
	m.mu.RUnlock()

	if !exists {
		return fmt.Errorf("decision not found: %s", decisionID)
	}

	if decision.Status != DecisionStatusPending {
		return fmt.Errorf("decision not pending: %s", decisionID)
	}

	if err := m.httpClient.RejectDecision(ctx, decisionID, comment); err != nil {
		return fmt.Errorf("failed to reject decision: %w", err)
	}

	m.mu.Lock()
	decision.Status = DecisionStatusRejected
	decision.OperatorID = m.operatorID
	decision.OperatorDecision = "reject"
	decision.OperatorNotes = comment
	now := time.Now()
	decision.ResolvedAt = &now
	m.mu.Unlock()

	return nil
}

// EscalateDecision escalates a decision to senior operator
func (m *Manager) EscalateDecision(ctx context.Context, decisionID, reason string) error {
	m.mu.RLock()
	decision, exists := m.pendingDecisions[decisionID]
	m.mu.RUnlock()

	if !exists {
		return fmt.Errorf("decision not found: %s", decisionID)
	}

	if err := m.httpClient.EscalateDecision(ctx, decisionID, reason); err != nil {
		return fmt.Errorf("failed to escalate decision: %w", err)
	}

	m.mu.Lock()
	decision.Status = DecisionStatusEscalated
	decision.OperatorID = m.operatorID
	decision.OperatorDecision = "escalate"
	decision.OperatorNotes = reason
	m.mu.Unlock()

	m.emitEvent(ManagerEvent{
		Type:      EventDecisionEscalated,
		Decision:  decision,
		Timestamp: time.Now(),
	})

	return nil
}

// GetPendingDecisions returns all pending decisions
func (m *Manager) GetPendingDecisions() []*Decision {
	m.mu.RLock()
	defer m.mu.RUnlock()

	decisions := make([]*Decision, 0, len(m.pendingDecisions))
	for _, decision := range m.pendingDecisions {
		decisions = append(decisions, decision)
	}

	return decisions
}

// GetDecision retrieves a specific decision by ID (pending or resolved)
func (m *Manager) GetDecision(decisionID string) (*Decision, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if decision, exists := m.pendingDecisions[decisionID]; exists {
		return decision, nil
	}

	if decision, exists := m.resolvedDecisions[decisionID]; exists {
		return decision, nil
	}

	return nil, fmt.Errorf("decision not found: %s", decisionID)
}

// GetMetrics returns current decision queue metrics
func (m *Manager) GetMetrics() DecisionMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.metrics
}

// GetConnectionStatus returns current SSE connection status
func (m *Manager) GetConnectionStatus() ConnectionStatus {
	if m.sseClient == nil {
		return ConnectionStatus{
			Connected: false,
			ServerURL: m.serverURL,
		}
	}
	return m.sseClient.Status()
}

// processEvents processes incoming SSE events
func (m *Manager) processEvents(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-m.stopCh:
			return
		case event := <-m.sseClient.Events():
			m.handleSSEEvent(event)
		case err := <-m.sseClient.Errors():
			m.emitError(err)
		}
	}
}

// handleSSEEvent handles a single SSE event
func (m *Manager) handleSSEEvent(event *SSEEvent) {
	switch event.EventType {
	case "decision_pending":
		decision, err := ParseDecisionEvent(event)
		if err != nil {
			m.emitError(fmt.Errorf("failed to parse decision event: %w", err))
			return
		}

		m.addPendingDecision(decision)

	case "decision_resolved":
		decision, err := ParseDecisionEvent(event)
		if err != nil {
			m.emitError(fmt.Errorf("failed to parse resolved decision event: %w", err))
			return
		}

		m.resolveDecision(decision)

	case "heartbeat":
		// Heartbeat received, connection is healthy
		// No action needed, SSE client tracks this

	default:
		// Unknown event type
		m.emitError(fmt.Errorf("unknown SSE event type: %s", event.EventType))
	}
}

// addPendingDecision adds a new pending decision to the queue
func (m *Manager) addPendingDecision(decision *Decision) {
	m.mu.Lock()
	m.pendingDecisions[decision.DecisionID] = decision
	m.mu.Unlock()

	// Emit to decision channel (non-blocking)
	select {
	case m.decisionCh <- decision:
	default:
		m.emitError(fmt.Errorf("decision channel full, dropping decision: %s", decision.DecisionID))
	}

	m.emitEvent(ManagerEvent{
		Type:      EventDecisionAdded,
		Decision:  decision,
		Timestamp: time.Now(),
	})
}

// resolveDecision marks a decision as resolved
func (m *Manager) resolveDecision(decision *Decision) {
	m.mu.Lock()
	delete(m.pendingDecisions, decision.DecisionID)
	m.resolvedDecisions[decision.DecisionID] = decision

	// Limit resolved cache size
	if len(m.resolvedDecisions) > 1000 {
		// Simple eviction: remove oldest (would need ordered map for proper LRU)
		for id := range m.resolvedDecisions {
			delete(m.resolvedDecisions, id)
			break
		}
	}
	m.mu.Unlock()

	m.emitEvent(ManagerEvent{
		Type:      EventDecisionResolved,
		Decision:  decision,
		Timestamp: time.Now(),
	})
}

// syncPendingDecisions synchronizes pending decisions from backend
func (m *Manager) syncPendingDecisions(ctx context.Context) error {
	filter := &DecisionFilter{
		Status: []DecisionStatus{DecisionStatusPending},
		Limit:  100,
	}

	decisions, err := m.httpClient.ListDecisions(ctx, filter)
	if err != nil {
		return fmt.Errorf("failed to list decisions: %w", err)
	}

	m.mu.Lock()
	for _, decision := range decisions {
		m.pendingDecisions[decision.DecisionID] = decision
	}
	m.mu.Unlock()

	return nil
}

// metricsUpdateLoop periodically updates metrics from backend
func (m *Manager) metricsUpdateLoop(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-m.stopCh:
			return
		case <-ticker.C:
			m.updateMetrics(ctx)
		}
	}
}

// updateMetrics fetches and updates metrics from backend
func (m *Manager) updateMetrics(ctx context.Context) {
	metrics, err := m.httpClient.GetMetrics(ctx)
	if err != nil {
		m.emitError(fmt.Errorf("failed to fetch metrics: %w", err))
		return
	}

	m.mu.Lock()
	m.metrics = *metrics
	m.mu.Unlock()

	m.emitEvent(ManagerEvent{
		Type:      EventMetricsUpdated,
		Metrics:   metrics,
		Timestamp: time.Now(),
	})
}

// emitEvent emits a manager event (non-blocking)
func (m *Manager) emitEvent(event ManagerEvent) {
	select {
	case m.eventCh <- event:
	default:
		// Event channel full, drop event
	}
}

// emitError emits an error (non-blocking)
func (m *Manager) emitError(err error) {
	select {
	case m.errorCh <- err:
	case m.eventCh <- ManagerEvent{
		Type:      EventError,
		Error:     err,
		Timestamp: time.Now(),
	}:
	default:
		// Both channels full, drop error
	}
}
