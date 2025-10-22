package grpc

import (
	"context"
	"fmt"
	"io"
	"os"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "github.com/verticedev/vcli-go/api/grpc/governance"
)

// GovernanceClient wraps the gRPC client for Governance service
type GovernanceClient struct {
	conn   *grpc.ClientConn
	client pb.GovernanceServiceClient

	serverAddress string
	sessionID     string
	operatorID    string
}

// NewGovernanceClient creates a new Governance gRPC client
func NewGovernanceClient(serverAddress string) (*GovernanceClient, error) {
	debug := os.Getenv("VCLI_DEBUG") == "true"

	// Check env var if endpoint not provided
	if serverAddress == "" {
		serverAddress = os.Getenv("VCLI_GOVERNANCE_ENDPOINT")
		if serverAddress == "" {
			serverAddress = "localhost:50053" // default
		}
	}

	if debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] Governance gRPC client connecting to %s\n", serverAddress)
	}

	conn, err := grpc.NewClient(
		serverAddress,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Governance at %s: %w", serverAddress, err)
	}

	if debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] Governance gRPC connection established\n")
	}

	client := pb.NewGovernanceServiceClient(conn)

	return &GovernanceClient{
		conn:          conn,
		client:        client,
		serverAddress: serverAddress,
	}, nil
}

// Close closes the gRPC connection
func (c *GovernanceClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// HealthCheck performs a health check on the server
func (c *GovernanceClient) HealthCheck(ctx context.Context) (bool, error) {
	req := &pb.HealthCheckRequest{}

	resp, err := c.client.HealthCheck(ctx, req)
	if err != nil {
		return false, fmt.Errorf("health check failed: %w", err)
	}

	return resp.Healthy, nil
}

// CreateSession creates a new operator session
func (c *GovernanceClient) CreateSession(ctx context.Context, operatorID string) (string, error) {
	req := &pb.CreateSessionRequest{
		OperatorId: operatorID,
	}

	resp, err := c.client.CreateSession(ctx, req)
	if err != nil {
		return "", fmt.Errorf("failed to create session: %w", err)
	}

	c.sessionID = resp.SessionId
	c.operatorID = operatorID

	return resp.SessionId, nil
}

// CloseSession closes the current session
func (c *GovernanceClient) CloseSession(ctx context.Context) error {
	if c.sessionID == "" {
		return fmt.Errorf("no active session")
	}

	req := &pb.CloseSessionRequest{
		SessionId: c.sessionID,
	}

	resp, err := c.client.CloseSession(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to close session: %w", err)
	}

	if !resp.Success {
		return fmt.Errorf("session close failed")
	}

	c.sessionID = ""
	return nil
}

// ListPendingDecisions lists pending decisions
func (c *GovernanceClient) ListPendingDecisions(ctx context.Context, limit int32, status, priority string) ([]*pb.Decision, error) {
	if c.sessionID == "" {
		return nil, fmt.Errorf("no active session")
	}

	req := &pb.ListPendingDecisionsRequest{
		SessionId: c.sessionID,
		Limit:     limit,
		Status:    status,
		Priority:  priority,
	}

	resp, err := c.client.ListPendingDecisions(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to list decisions: %w", err)
	}

	return resp.Decisions, nil
}

// GetDecision gets a specific decision by ID
func (c *GovernanceClient) GetDecision(ctx context.Context, decisionID string) (*pb.Decision, error) {
	req := &pb.GetDecisionRequest{
		DecisionId: decisionID,
	}

	resp, err := c.client.GetDecision(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get decision: %w", err)
	}

	return resp.Decision, nil
}

// ApproveDecision approves a decision
func (c *GovernanceClient) ApproveDecision(ctx context.Context, decisionID, comment, reasoning string) error {
	if c.sessionID == "" {
		return fmt.Errorf("no active session")
	}

	req := &pb.ApproveDecisionRequest{
		SessionId:  c.sessionID,
		DecisionId: decisionID,
		Comment:    comment,
		Reasoning:  reasoning,
	}

	resp, err := c.client.ApproveDecision(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to approve decision: %w", err)
	}

	if !resp.Success {
		return fmt.Errorf("approval failed: %s", resp.Message)
	}

	return nil
}

// RejectDecision rejects a decision
func (c *GovernanceClient) RejectDecision(ctx context.Context, decisionID, comment, reasoning string) error {
	if c.sessionID == "" {
		return fmt.Errorf("no active session")
	}

	req := &pb.RejectDecisionRequest{
		SessionId:  c.sessionID,
		DecisionId: decisionID,
		Comment:    comment,
		Reasoning:  reasoning,
	}

	resp, err := c.client.RejectDecision(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to reject decision: %w", err)
	}

	if !resp.Success {
		return fmt.Errorf("rejection failed: %s", resp.Message)
	}

	return nil
}

// EscalateDecision escalates a decision
func (c *GovernanceClient) EscalateDecision(ctx context.Context, decisionID, reason, target string) error {
	if c.sessionID == "" {
		return fmt.Errorf("no active session")
	}

	req := &pb.EscalateDecisionRequest{
		SessionId:         c.sessionID,
		DecisionId:        decisionID,
		Reason:            reason,
		EscalationTarget:  target,
	}

	resp, err := c.client.EscalateDecision(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to escalate decision: %w", err)
	}

	if !resp.Success {
		return fmt.Errorf("escalation failed: %s", resp.Message)
	}

	return nil
}

// GetMetrics gets overall governance metrics
func (c *GovernanceClient) GetMetrics(ctx context.Context) (*pb.DecisionMetrics, error) {
	if c.sessionID == "" {
		return nil, fmt.Errorf("no active session")
	}

	req := &pb.GetMetricsRequest{
		SessionId: c.sessionID,
	}

	resp, err := c.client.GetMetrics(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get metrics: %w", err)
	}

	return resp.Metrics, nil
}

// GetSessionStats gets session-specific statistics
func (c *GovernanceClient) GetSessionStats(ctx context.Context) (*pb.GetSessionStatsResponse, error) {
	if c.operatorID == "" {
		return nil, fmt.Errorf("no operator ID set")
	}

	req := &pb.GetSessionStatsRequest{
		OperatorId: c.operatorID,
	}

	resp, err := c.client.GetSessionStats(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get session stats: %w", err)
	}

	return resp, nil
}

// StreamDecisions streams decision events in real-time
func (c *GovernanceClient) StreamDecisions(ctx context.Context, handler func(*pb.DecisionEvent) error) error {
	if c.sessionID == "" {
		return fmt.Errorf("no active session")
	}

	req := &pb.StreamDecisionsRequest{
		SessionId: c.sessionID,
	}

	stream, err := c.client.StreamDecisions(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to start decision stream: %w", err)
	}

	for {
		event, err := stream.Recv()
		if err == io.EOF {
			// Stream ended normally
			return nil
		}
		if err != nil {
			return fmt.Errorf("error receiving decision event: %w", err)
		}

		// Call handler with event
		if err := handler(event); err != nil {
			return fmt.Errorf("event handler error: %w", err)
		}
	}
}

// StreamEvents streams governance events in real-time
func (c *GovernanceClient) StreamEvents(ctx context.Context, handler func(*pb.GovernanceEvent) error) error {
	if c.sessionID == "" {
		return fmt.Errorf("no active session")
	}

	req := &pb.StreamEventsRequest{
		SessionId: c.sessionID,
	}

	stream, err := c.client.StreamEvents(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to start event stream: %w", err)
	}

	for {
		event, err := stream.Recv()
		if err == io.EOF {
			// Stream ended normally
			return nil
		}
		if err != nil {
			return fmt.Errorf("error receiving governance event: %w", err)
		}

		// Call handler with event
		if err := handler(event); err != nil {
			return fmt.Errorf("event handler error: %w", err)
		}
	}
}

// SessionID returns the current session ID
func (c *GovernanceClient) SessionID() string {
	return c.sessionID
}

// OperatorID returns the current operator ID
func (c *GovernanceClient) OperatorID() string {
	return c.operatorID
}

// ServerAddress returns the server address
func (c *GovernanceClient) ServerAddress() string {
	return c.serverAddress
}
