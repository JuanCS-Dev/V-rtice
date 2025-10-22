package grpc

import (
	"context"
	"fmt"
	"io"
	"os"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "github.com/verticedev/vcli-go/api/grpc/immune"
	"github.com/verticedev/vcli-go/internal/debug"
)

// ImmuneClient wraps the gRPC client for Active Immune Core service
type ImmuneClient struct {
	conn   *grpc.ClientConn
	client pb.ActiveImmuneCoreClient

	serverAddress string
}

// NewImmuneClient creates a new Active Immune Core gRPC client
func NewImmuneClient(serverAddress string) (*ImmuneClient, error) {
	// Determine endpoint source
	source := "flag"
	if serverAddress == "" {
		serverAddress = os.Getenv("VCLI_IMMUNE_ENDPOINT")
		if serverAddress != "" {
			source = "env:VCLI_IMMUNE_ENDPOINT"
		} else {
			serverAddress = "localhost:50052"
			source = "default"
		}
	}

	debug.LogConnection("ImmuneCore", serverAddress, source)

	conn, err := grpc.NewClient(
		serverAddress,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		debug.LogError("ImmuneCore", serverAddress, err)
		return nil, fmt.Errorf("failed to connect to Immune Core at %s: %w", serverAddress, err)
	}

	debug.LogSuccess("ImmuneCore", serverAddress)

	client := pb.NewActiveImmuneCoreClient(conn)

	return &ImmuneClient{
		conn:          conn,
		client:        client,
		serverAddress: serverAddress,
	}, nil
}

// Close closes the gRPC connection
func (c *ImmuneClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// ============================================================
// Agent Management
// ============================================================

// ListAgents lists agents with optional filters
func (c *ImmuneClient) ListAgents(
	ctx context.Context,
	lymphnodeID string,
	agentType pb.AgentType,
	state pb.AgentState,
	page, pageSize int32,
	includeMetrics bool,
) (*pb.ListAgentsResponse, error) {
	req := &pb.ListAgentsRequest{
		LymphnodeId:    lymphnodeID,
		AgentType:      agentType,
		State:          state,
		Page:           page,
		PageSize:       pageSize,
		IncludeMetrics: includeMetrics,
	}

	resp, err := c.client.ListAgents(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to list agents: %w", err)
	}

	return resp, nil
}

// GetAgent retrieves a specific agent by ID
func (c *ImmuneClient) GetAgent(
	ctx context.Context,
	agentID string,
	includeMetrics, includeHistory bool,
) (*pb.Agent, error) {
	req := &pb.GetAgentRequest{
		AgentId:        agentID,
		IncludeMetrics: includeMetrics,
		IncludeHistory: includeHistory,
	}

	resp, err := c.client.GetAgent(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get agent: %w", err)
	}

	return resp, nil
}

// CloneAgent clones an agent multiple times
func (c *ImmuneClient) CloneAgent(
	ctx context.Context,
	agentID string,
	cloneCount int32,
	lymphnodeID string,
) (*pb.CloneAgentResponse, error) {
	req := &pb.CloneAgentRequest{
		AgentId:     agentID,
		CloneCount:  cloneCount,
		LymphnodeId: lymphnodeID,
	}

	resp, err := c.client.CloneAgent(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to clone agent: %w", err)
	}

	return resp, nil
}

// TerminateAgent terminates an agent
func (c *ImmuneClient) TerminateAgent(
	ctx context.Context,
	agentID, reason string,
	graceful bool,
) (*pb.TerminateAgentResponse, error) {
	req := &pb.TerminateAgentRequest{
		AgentId:  agentID,
		Reason:   reason,
		Graceful: graceful,
	}

	resp, err := c.client.TerminateAgent(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to terminate agent: %w", err)
	}

	return resp, nil
}

// GetAgentMetrics retrieves agent performance metrics
func (c *ImmuneClient) GetAgentMetrics(
	ctx context.Context,
	agentID string,
) (*pb.AgentMetrics, error) {
	req := &pb.GetAgentMetricsRequest{
		AgentId: agentID,
	}

	resp, err := c.client.GetAgentMetrics(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get agent metrics: %w", err)
	}

	return resp, nil
}

// ============================================================
// Lymphnode Operations
// ============================================================

// ListLymphnodes lists all lymphnodes
func (c *ImmuneClient) ListLymphnodes(
	ctx context.Context,
	zone string,
	includeMetrics bool,
) (*pb.ListLymphnodesResponse, error) {
	req := &pb.ListLymphnodesRequest{
		Zone:           zone,
		IncludeMetrics: includeMetrics,
	}

	resp, err := c.client.ListLymphnodes(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to list lymphnodes: %w", err)
	}

	return resp, nil
}

// GetLymphnodeStatus retrieves detailed lymphnode status
func (c *ImmuneClient) GetLymphnodeStatus(
	ctx context.Context,
	lymphnodeID string,
) (*pb.LymphnodeStatus, error) {
	req := &pb.GetLymphnodeRequest{
		LymphnodeId: lymphnodeID,
	}

	resp, err := c.client.GetLymphnodeStatus(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get lymphnode status: %w", err)
	}

	return resp, nil
}

// GetLymphnodeMetrics retrieves lymphnode metrics
func (c *ImmuneClient) GetLymphnodeMetrics(
	ctx context.Context,
	lymphnodeID string,
) (*pb.LymphnodeMetrics, error) {
	req := &pb.GetLymphnodeRequest{
		LymphnodeId: lymphnodeID,
	}

	resp, err := c.client.GetLymphnodeMetrics(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get lymphnode metrics: %w", err)
	}

	return resp, nil
}

// ============================================================
// Cytokine Streaming
// ============================================================

// StreamCytokines streams cytokines in real-time
func (c *ImmuneClient) StreamCytokines(
	ctx context.Context,
	topics []string,
	lymphnodeID, eventType string,
	severityMin int32,
	handler func(*pb.Cytokine) error,
) error {
	req := &pb.StreamCytokinesRequest{
		Topics:      topics,
		LymphnodeId: lymphnodeID,
		EventType:   eventType,
		SeverityMin: severityMin,
	}

	stream, err := c.client.StreamCytokines(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to stream cytokines: %w", err)
	}

	for {
		cytokine, err := stream.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return fmt.Errorf("error receiving cytokine: %w", err)
		}

		if err := handler(cytokine); err != nil {
			return fmt.Errorf("cytokine handler error: %w", err)
		}
	}
}

// PublishCytokine publishes a cytokine event
func (c *ImmuneClient) PublishCytokine(
	ctx context.Context,
	emitterID, eventType string,
	severity int32,
	tags []string,
) (*pb.PublishCytokineResponse, error) {
	req := &pb.PublishCytokineRequest{
		EmitterId: emitterID,
		EventType: eventType,
		Severity:  severity,
		Tags:      tags,
	}

	resp, err := c.client.PublishCytokine(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to publish cytokine: %w", err)
	}

	return resp, nil
}

// ============================================================
// Hormone System
// ============================================================

// StreamHormones streams hormones in real-time
func (c *ImmuneClient) StreamHormones(
	ctx context.Context,
	hormoneTypes []string,
	zone string,
	handler func(*pb.Hormone) error,
) error {
	req := &pb.StreamHormonesRequest{
		HormoneTypes: hormoneTypes,
		Zone:         zone,
	}

	stream, err := c.client.StreamHormones(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to stream hormones: %w", err)
	}

	for {
		hormone, err := stream.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return fmt.Errorf("error receiving hormone: %w", err)
		}

		if err := handler(hormone); err != nil {
			return fmt.Errorf("hormone handler error: %w", err)
		}
	}
}

// PublishHormone publishes a hormone signal
func (c *ImmuneClient) PublishHormone(
	ctx context.Context,
	hormoneType, source string,
	nivel float64,
) (*pb.PublishHormoneResponse, error) {
	req := &pb.PublishHormoneRequest{
		Type:   hormoneType,
		Nivel:  nivel,
		Source: source,
	}

	resp, err := c.client.PublishHormone(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to publish hormone: %w", err)
	}

	return resp, nil
}

// ============================================================
// Coordination
// ============================================================

// TriggerMassResponse triggers a mass immune response
func (c *ImmuneClient) TriggerMassResponse(
	ctx context.Context,
	lymphnodeID, threatType string,
	agentCount int32,
	agentType pb.AgentType,
	reason string,
) (*pb.MassResponseResponse, error) {
	req := &pb.MassResponseRequest{
		LymphnodeId: lymphnodeID,
		ThreatType:  threatType,
		AgentCount:  agentCount,
		AgentType:   agentType,
		Reason:      reason,
	}

	resp, err := c.client.TriggerMassResponse(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to trigger mass response: %w", err)
	}

	return resp, nil
}

// GetSystemHealth retrieves overall immune system health
func (c *ImmuneClient) GetSystemHealth(
	ctx context.Context,
	includeAllLymphnodes, includeAgentStats bool,
) (*pb.SystemHealthResponse, error) {
	req := &pb.SystemHealthRequest{
		IncludeAllLymphnodes: includeAllLymphnodes,
		IncludeAgentStats:    includeAgentStats,
	}

	resp, err := c.client.GetSystemHealth(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get system health: %w", err)
	}

	return resp, nil
}

// ============================================================
// Utility Methods
// ============================================================

// ServerAddress returns the server address
func (c *ImmuneClient) ServerAddress() string {
	return c.serverAddress
}

// IsHealthy performs a simple health check
func (c *ImmuneClient) IsHealthy(ctx context.Context) bool {
	resp, err := c.GetSystemHealth(ctx, false, false)
	if err != nil {
		return false
	}
	return resp.Status == pb.SystemHealthResponse_HEALTHY
}
