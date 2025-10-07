package governance

import (
	"context"
	"fmt"
	"time"

	grpcclient "github.com/verticedev/vcli-go/internal/grpc"
)

// Client defines the common interface for Governance clients (HTTP or gRPC)
type Client interface {
	// Session Management
	CreateSession(ctx context.Context, operatorName, operatorRole string) (*Session, error)
	SetSessionID(sessionID string)

	// Decision Operations
	ApproveDecision(ctx context.Context, decisionID, comment string) error
	RejectDecision(ctx context.Context, decisionID, reason string) error
	EscalateDecision(ctx context.Context, decisionID, reason string) error
	GetDecision(ctx context.Context, decisionID string) (*Decision, error)
	ListDecisions(ctx context.Context, filter *DecisionFilter) ([]*Decision, error)

	// Metrics & Health
	GetMetrics(ctx context.Context) (*DecisionMetrics, error)
	GetSessionStats(ctx context.Context) (*SessionStats, error)
	HealthCheck(ctx context.Context) (bool, error)
	PingServer(ctx context.Context) (time.Duration, error)

	// Lifecycle
	Close() error
}

// BackendType specifies the backend communication protocol
type BackendType string

const (
	BackendHTTP BackendType = "http"
	BackendGRPC BackendType = "grpc"
)

// ClientConfig holds configuration for client creation
type ClientConfig struct {
	BackendType BackendType
	ServerURL   string
	OperatorID  string
}

// NewClient creates a new Governance client based on backend type
func NewClient(config ClientConfig) (Client, error) {
	switch config.BackendType {
	case BackendHTTP:
		return NewHTTPClient(config.ServerURL, config.OperatorID), nil

	case BackendGRPC:
		return NewGRPCClientWrapper(config.ServerURL, config.OperatorID)

	default:
		return nil, fmt.Errorf("unsupported backend type: %s", config.BackendType)
	}
}

// GRPCClientWrapper adapts the gRPC client to the Client interface
type GRPCClientWrapper struct {
	client     *grpcclient.GovernanceClient
	operatorID string
	sessionID  string
}

// NewGRPCClientWrapper creates a new gRPC client wrapper
func NewGRPCClientWrapper(serverAddress, operatorID string) (*GRPCClientWrapper, error) {
	client, err := grpcclient.NewGovernanceClient(serverAddress)
	if err != nil {
		return nil, fmt.Errorf("failed to create gRPC client: %w", err)
	}

	return &GRPCClientWrapper{
		client:     client,
		operatorID: operatorID,
	}, nil
}

// CreateSession creates a new operator session (gRPC)
func (w *GRPCClientWrapper) CreateSession(ctx context.Context, operatorName, operatorRole string) (*Session, error) {
	// gRPC CreateSession only needs operator ID
	sessionID, err := w.client.CreateSession(ctx, w.operatorID)
	if err != nil {
		return nil, err
	}

	w.sessionID = sessionID

	// Convert to common Session type
	return &Session{
		SessionID:    sessionID,
		OperatorID:   w.operatorID,
		OperatorName: operatorName,
		OperatorRole: operatorRole,
		CreatedAt:    time.Now(),
		Active:       true,
	}, nil
}

// SetSessionID sets the active session ID
func (w *GRPCClientWrapper) SetSessionID(sessionID string) {
	w.sessionID = sessionID
}

// ApproveDecision approves a decision (gRPC)
func (w *GRPCClientWrapper) ApproveDecision(ctx context.Context, decisionID, comment string) error {
	return w.client.ApproveDecision(ctx, decisionID, comment, "")
}

// RejectDecision rejects a decision (gRPC)
func (w *GRPCClientWrapper) RejectDecision(ctx context.Context, decisionID, reason string) error {
	return w.client.RejectDecision(ctx, decisionID, reason, "")
}

// EscalateDecision escalates a decision (gRPC)
func (w *GRPCClientWrapper) EscalateDecision(ctx context.Context, decisionID, reason string) error {
	return w.client.EscalateDecision(ctx, decisionID, reason, "senior_operator")
}

// GetDecision gets a specific decision (gRPC)
func (w *GRPCClientWrapper) GetDecision(ctx context.Context, decisionID string) (*Decision, error) {
	pbDecision, err := w.client.GetDecision(ctx, decisionID)
	if err != nil {
		return nil, err
	}

	// Convert protobuf Decision to internal Decision type
	decision := &Decision{
		DecisionID:       pbDecision.DecisionId,
		ActionType:       pbDecision.OperationType,
		Status:           DecisionStatus(pbDecision.Status),
		Context:          make(map[string]interface{}),
		RecommendedActio: pbDecision.OperationType,
		CreatedAt:        pbDecision.CreatedAt.AsTime(),
	}

	// Convert context map
	for k, v := range pbDecision.Context {
		decision.Context[k] = v
	}

	// Convert risk assessment
	if pbDecision.RiskAssessment != nil {
		decision.RiskLevel = RiskLevel(pbDecision.RiskAssessment.Level)
		decision.ThreatScore = pbDecision.RiskAssessment.Score
	}

	return decision, nil
}

// ListDecisions lists decisions (gRPC)
func (w *GRPCClientWrapper) ListDecisions(ctx context.Context, filter *DecisionFilter) ([]*Decision, error) {
	// Convert filter to gRPC parameters
	limit := int32(50)
	status := "PENDING"
	priority := ""

	if filter != nil {
		if filter.Limit > 0 {
			limit = int32(filter.Limit)
		}
		if len(filter.Status) > 0 {
			status = string(filter.Status[0])
		}
	}

	pbDecisions, err := w.client.ListPendingDecisions(ctx, limit, status, priority)
	if err != nil {
		return nil, err
	}

	// Convert protobuf decisions to internal Decision type
	decisions := make([]*Decision, len(pbDecisions))
	for i, pbDec := range pbDecisions {
		decisions[i] = &Decision{
			DecisionID:       pbDec.DecisionId,
			ActionType:       pbDec.OperationType,
			Status:           DecisionStatus(pbDec.Status),
			Context:          make(map[string]interface{}),
			RecommendedActio: pbDec.OperationType,
			CreatedAt:        pbDec.CreatedAt.AsTime(),
		}

		// Convert context
		for k, v := range pbDec.Context {
			decisions[i].Context[k] = v
		}

		// Convert risk
		if pbDec.RiskAssessment != nil {
			decisions[i].RiskLevel = RiskLevel(pbDec.RiskAssessment.Level)
			decisions[i].ThreatScore = pbDec.RiskAssessment.Score
		}
	}

	return decisions, nil
}

// GetMetrics gets decision metrics (gRPC)
func (w *GRPCClientWrapper) GetMetrics(ctx context.Context) (*DecisionMetrics, error) {
	pbMetrics, err := w.client.GetMetrics(ctx)
	if err != nil {
		return nil, err
	}

	return &DecisionMetrics{
		TotalPending:    int(pbMetrics.PendingCount),
		TotalApproved:   int(pbMetrics.ApprovedCount),
		TotalRejected:   int(pbMetrics.RejectedCount),
		TotalEscalated:  int(pbMetrics.EscalatedCount),
		PendingCritical: int(pbMetrics.CriticalCount),
		PendingHigh:     int(pbMetrics.HighPriorityCount),
		AvgResponseTime: pbMetrics.AvgResponseTimeSeconds,
		Timestamp:       time.Now(),
	}, nil
}

// GetSessionStats gets session statistics (gRPC)
func (w *GRPCClientWrapper) GetSessionStats(ctx context.Context) (*SessionStats, error) {
	pbStats, err := w.client.GetSessionStats(ctx)
	if err != nil {
		return nil, err
	}

	return &SessionStats{
		TotalDecisions:  int(pbStats.TotalDecisions),
		Approved:        int(pbStats.Approved),
		Rejected:        int(pbStats.Rejected),
		Escalated:       int(pbStats.Escalated),
		AvgResponseTime: pbStats.AvgResponseTimeSeconds,
	}, nil
}

// HealthCheck checks backend health (gRPC)
func (w *GRPCClientWrapper) HealthCheck(ctx context.Context) (bool, error) {
	return w.client.HealthCheck(ctx)
}

// PingServer pings the backend (gRPC)
func (w *GRPCClientWrapper) PingServer(ctx context.Context) (time.Duration, error) {
	start := time.Now()
	healthy, err := w.client.HealthCheck(ctx)
	if err != nil {
		return 0, err
	}
	if !healthy {
		return 0, fmt.Errorf("backend unhealthy")
	}
	return time.Since(start), nil
}

// Close closes the gRPC connection
func (w *GRPCClientWrapper) Close() error {
	return w.client.Close()
}
