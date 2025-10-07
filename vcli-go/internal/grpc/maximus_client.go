package grpc

import (
	"context"
	"fmt"
	"io"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/types/known/timestamppb"

	pb "github.com/verticedev/vcli-go/api/grpc/maximus"
)

// MaximusClient wraps the gRPC client for MAXIMUS Orchestrator service
type MaximusClient struct {
	conn   *grpc.ClientConn
	client pb.MaximusOrchestratorClient

	serverAddress string
}

// NewMaximusClient creates a new MAXIMUS gRPC client
func NewMaximusClient(serverAddress string) (*MaximusClient, error) {
	conn, err := grpc.NewClient(
		serverAddress,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to MAXIMUS server: %w", err)
	}

	client := pb.NewMaximusOrchestratorClient(conn)

	return &MaximusClient{
		conn:          conn,
		client:        client,
		serverAddress: serverAddress,
	}, nil
}

// Close closes the gRPC connection
func (c *MaximusClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// ============================================================
// Decision Management
// ============================================================

// SubmitDecision submits a new decision for approval
func (c *MaximusClient) SubmitDecision(
	ctx context.Context,
	decisionType, title, description, context string,
	priority string,
	tags []string,
	requesterID string,
) (*pb.SubmitDecisionResponse, error) {
	req := &pb.SubmitDecisionRequest{
		DecisionType: decisionType,
		Title:        title,
		Description:  description,
		Context:      context,
		Priority:     priority,
		Tags:         tags,
		RequesterId:  requesterID,
	}

	resp, err := c.client.SubmitDecision(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to submit decision: %w", err)
	}

	return resp, nil
}

// GetDecision retrieves a decision by ID
func (c *MaximusClient) GetDecision(ctx context.Context, decisionID string) (*pb.Decision, error) {
	req := &pb.GetDecisionRequest{
		DecisionId: decisionID,
	}

	resp, err := c.client.GetDecision(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get decision: %w", err)
	}

	return resp, nil
}

// ListDecisions lists decisions with optional filters
func (c *MaximusClient) ListDecisions(
	ctx context.Context,
	status, decisionType, contextFilter string,
	tags []string,
	page, pageSize int32,
	sortBy, sortOrder string,
	startTime, endTime *time.Time,
) (*pb.ListDecisionsResponse, error) {
	req := &pb.ListDecisionsRequest{
		Status:       status,
		DecisionType: decisionType,
		Context:      contextFilter,
		Tags:         tags,
		Page:         page,
		PageSize:     pageSize,
		SortBy:       sortBy,
		SortOrder:    sortOrder,
	}

	if startTime != nil {
		req.StartTime = timestamppb.New(*startTime)
	}
	if endTime != nil {
		req.EndTime = timestamppb.New(*endTime)
	}

	resp, err := c.client.ListDecisions(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to list decisions: %w", err)
	}

	return resp, nil
}

// UpdateDecisionStatus updates the status of a decision
func (c *MaximusClient) UpdateDecisionStatus(
	ctx context.Context,
	decisionID, newStatus, reason, updatedBy string,
) (*pb.Decision, error) {
	req := &pb.UpdateDecisionStatusRequest{
		DecisionId: decisionID,
		NewStatus:  newStatus,
		Reason:     reason,
		UpdatedBy:  updatedBy,
	}

	resp, err := c.client.UpdateDecisionStatus(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to update decision status: %w", err)
	}

	return resp, nil
}

// DeleteDecision deletes a decision
func (c *MaximusClient) DeleteDecision(ctx context.Context, decisionID, reason string) error {
	req := &pb.DeleteDecisionRequest{
		DecisionId: decisionID,
		Reason:     reason,
	}

	resp, err := c.client.DeleteDecision(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to delete decision: %w", err)
	}

	if !resp.Success {
		return fmt.Errorf("delete failed: %s", resp.Message)
	}

	return nil
}

// ============================================================
// Real-time Event Streaming
// ============================================================

// WatchDecision watches a specific decision for updates in real-time
func (c *MaximusClient) WatchDecision(
	ctx context.Context,
	decisionID string,
	handler func(*pb.DecisionEvent) error,
) error {
	req := &pb.WatchDecisionRequest{
		DecisionId: decisionID,
	}

	stream, err := c.client.WatchDecision(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to watch decision: %w", err)
	}

	for {
		event, err := stream.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return fmt.Errorf("error receiving decision event: %w", err)
		}

		if err := handler(event); err != nil {
			return fmt.Errorf("event handler error: %w", err)
		}
	}
}

// StreamAllEvents streams all decision events with optional filters
func (c *MaximusClient) StreamAllEvents(
	ctx context.Context,
	decisionTypes, statuses []string,
	contextFilter string,
	handler func(*pb.DecisionEvent) error,
) error {
	req := &pb.StreamEventsRequest{
		DecisionTypes: decisionTypes,
		Statuses:      statuses,
		Context:       contextFilter,
	}

	stream, err := c.client.StreamAllEvents(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to stream events: %w", err)
	}

	for {
		event, err := stream.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return fmt.Errorf("error receiving event: %w", err)
		}

		if err := handler(event); err != nil {
			return fmt.Errorf("event handler error: %w", err)
		}
	}
}

// ============================================================
// Governance Metrics
// ============================================================

// GetGovernanceMetrics retrieves governance metrics
func (c *MaximusClient) GetGovernanceMetrics(
	ctx context.Context,
	startTime, endTime *time.Time,
	contextFilter string,
	decisionTypes []string,
) (*pb.GovernanceMetrics, error) {
	req := &pb.GetMetricsRequest{
		Context:       contextFilter,
		DecisionTypes: decisionTypes,
	}

	if startTime != nil {
		req.StartTime = timestamppb.New(*startTime)
	}
	if endTime != nil {
		req.EndTime = timestamppb.New(*endTime)
	}

	resp, err := c.client.GetGovernanceMetrics(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get governance metrics: %w", err)
	}

	return resp, nil
}

// GetServiceHealth checks MAXIMUS service health
func (c *MaximusClient) GetServiceHealth(ctx context.Context, serviceName string) (*pb.HealthCheckResponse, error) {
	req := &pb.HealthCheckRequest{
		Service: serviceName,
	}

	resp, err := c.client.GetServiceHealth(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("health check failed: %w", err)
	}

	return resp, nil
}

// ============================================================
// Batch Operations
// ============================================================

// BatchSubmitDecisions submits multiple decisions in batch
func (c *MaximusClient) BatchSubmitDecisions(
	ctx context.Context,
	decisions []*pb.SubmitDecisionRequest,
) (*pb.BatchSubmitResponse, error) {
	req := &pb.BatchSubmitRequest{
		Decisions: decisions,
	}

	resp, err := c.client.BatchSubmitDecisions(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("batch submit failed: %w", err)
	}

	return resp, nil
}

// ============================================================
// Utility Methods
// ============================================================

// ServerAddress returns the server address
func (c *MaximusClient) ServerAddress() string {
	return c.serverAddress
}

// IsHealthy performs a simple health check and returns true if healthy
func (c *MaximusClient) IsHealthy(ctx context.Context) bool {
	resp, err := c.GetServiceHealth(ctx, "")
	if err != nil {
		return false
	}
	return resp.Status == pb.HealthCheckResponse_SERVING
}
