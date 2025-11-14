package grpc

import (
	"context"
	"net"
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"google.golang.org/grpc/test/bufconn"

	pb "github.com/verticedev/vcli-go/api/grpc/immune"
)

const bufSize = 1024 * 1024

// mockActiveImmuneCoreServer implements pb.ActiveImmuneCoreServer for testing
type mockActiveImmuneCoreServer struct {
	pb.UnimplementedActiveImmuneCoreServer

	// Mock data
	agents     []*pb.Agent
	lymphnodes []*pb.Lymphnode
	cytokines  []*pb.Cytokine
	hormones   []*pb.Hormone

	// Error configuration for different methods
	listAgentsError          error
	getAgentError            error
	cloneAgentError          error
	terminateAgentError      error
	getAgentMetricsError     error
	listLymphnodesError      error
	getLymphnodeStatusError  error
	getLymphnodeMetricsError error
	streamCytokinesError     error
	publishCytokineError     error
	streamHormonesError      error
	publishHormoneError      error
	triggerMassResponseError error
	getSystemHealthError     error
}

// ListAgents implements agent listing
func (m *mockActiveImmuneCoreServer) ListAgents(
	ctx context.Context,
	req *pb.ListAgentsRequest,
) (*pb.ListAgentsResponse, error) {
	if m.listAgentsError != nil {
		return nil, m.listAgentsError
	}

	return &pb.ListAgentsResponse{
		Agents:     m.agents,
		TotalCount: int32(len(m.agents)),
		Page:       req.Page,
		PageSize:   req.PageSize,
	}, nil
}

// GetAgent implements agent retrieval
func (m *mockActiveImmuneCoreServer) GetAgent(
	ctx context.Context,
	req *pb.GetAgentRequest,
) (*pb.Agent, error) {
	if m.getAgentError != nil {
		return nil, m.getAgentError
	}

	return &pb.Agent{
		AgentId:     req.AgentId,
		Type:        pb.AgentType_MACROPHAGE,
		State:       pb.AgentState_ACTIVE,
		LymphnodeId: "lymph-1",
	}, nil
}

// CloneAgent implements agent cloning
func (m *mockActiveImmuneCoreServer) CloneAgent(
	ctx context.Context,
	req *pb.CloneAgentRequest,
) (*pb.CloneAgentResponse, error) {
	if m.cloneAgentError != nil {
		return nil, m.cloneAgentError
	}

	clonedAgentIds := make([]string, req.CloneCount)
	for i := range clonedAgentIds {
		clonedAgentIds[i] = req.AgentId + "-clone-" + string(rune(i))
	}

	return &pb.CloneAgentResponse{
		ClonedAgentIds: clonedAgentIds,
		SuccessCount:   req.CloneCount,
		FailureCount:   0,
	}, nil
}

// TerminateAgent implements agent termination
func (m *mockActiveImmuneCoreServer) TerminateAgent(
	ctx context.Context,
	req *pb.TerminateAgentRequest,
) (*pb.TerminateAgentResponse, error) {
	if m.terminateAgentError != nil {
		return nil, m.terminateAgentError
	}

	return &pb.TerminateAgentResponse{
		Success: true,
		Message: "agent terminated: " + req.AgentId,
	}, nil
}

// GetAgentMetrics implements agent metrics retrieval
func (m *mockActiveImmuneCoreServer) GetAgentMetrics(
	ctx context.Context,
	req *pb.GetAgentMetricsRequest,
) (*pb.AgentMetrics, error) {
	if m.getAgentMetricsError != nil {
		return nil, m.getAgentMetricsError
	}

	return &pb.AgentMetrics{
		AgentId:           req.AgentId,
		AvgResponseTimeMs: 125.5,
		TotalActions:      100,
		SuccessRate:       0.98,
		AvgCpuPercent:     45.5,
		AvgMemoryMb:       512.0,
	}, nil
}

// ListLymphnodes implements lymphnode listing
func (m *mockActiveImmuneCoreServer) ListLymphnodes(
	ctx context.Context,
	req *pb.ListLymphnodesRequest,
) (*pb.ListLymphnodesResponse, error) {
	if m.listLymphnodesError != nil {
		return nil, m.listLymphnodesError
	}

	return &pb.ListLymphnodesResponse{
		Lymphnodes: m.lymphnodes,
		TotalCount: int32(len(m.lymphnodes)),
	}, nil
}

// GetLymphnodeStatus implements lymphnode status retrieval
func (m *mockActiveImmuneCoreServer) GetLymphnodeStatus(
	ctx context.Context,
	req *pb.GetLymphnodeRequest,
) (*pb.LymphnodeStatus, error) {
	if m.getLymphnodeStatusError != nil {
		return nil, m.getLymphnodeStatusError
	}

	return &pb.LymphnodeStatus{
		Lymphnode: &pb.Lymphnode{
			LymphnodeId: req.LymphnodeId,
			Zone:        "zone-a",
			TotalAgents: 10,
			IsHealthy:   true,
		},
		CpuPercent: 60.0,
		MemoryMb:   2048.0,
	}, nil
}

// GetLymphnodeMetrics implements lymphnode metrics retrieval
func (m *mockActiveImmuneCoreServer) GetLymphnodeMetrics(
	ctx context.Context,
	req *pb.GetLymphnodeRequest,
) (*pb.LymphnodeMetrics, error) {
	if m.getLymphnodeMetricsError != nil {
		return nil, m.getLymphnodeMetricsError
	}

	return &pb.LymphnodeMetrics{
		LymphnodeId:  req.LymphnodeId,
		TotalAgents:  100,
		ActiveAgents: 85,
	}, nil
}

// StreamCytokines implements cytokine streaming
func (m *mockActiveImmuneCoreServer) StreamCytokines(
	req *pb.StreamCytokinesRequest,
	stream grpc.ServerStreamingServer[pb.Cytokine],
) error {
	if m.streamCytokinesError != nil {
		return m.streamCytokinesError
	}

	for _, cytokine := range m.cytokines {
		if err := stream.Send(cytokine); err != nil {
			return err
		}
	}

	return nil
}

// PublishCytokine implements cytokine publishing
func (m *mockActiveImmuneCoreServer) PublishCytokine(
	ctx context.Context,
	req *pb.PublishCytokineRequest,
) (*pb.PublishCytokineResponse, error) {
	if m.publishCytokineError != nil {
		return nil, m.publishCytokineError
	}

	return &pb.PublishCytokineResponse{
		Success:    true,
		CytokineId: "cyt-123",
	}, nil
}

// StreamHormones implements hormone streaming
func (m *mockActiveImmuneCoreServer) StreamHormones(
	req *pb.StreamHormonesRequest,
	stream grpc.ServerStreamingServer[pb.Hormone],
) error {
	if m.streamHormonesError != nil {
		return m.streamHormonesError
	}

	for _, hormone := range m.hormones {
		if err := stream.Send(hormone); err != nil {
			return err
		}
	}

	return nil
}

// PublishHormone implements hormone publishing
func (m *mockActiveImmuneCoreServer) PublishHormone(
	ctx context.Context,
	req *pb.PublishHormoneRequest,
) (*pb.PublishHormoneResponse, error) {
	if m.publishHormoneError != nil {
		return nil, m.publishHormoneError
	}

	return &pb.PublishHormoneResponse{
		Success:   true,
		HormoneId: "horm-456",
	}, nil
}

// TriggerMassResponse implements mass response triggering
func (m *mockActiveImmuneCoreServer) TriggerMassResponse(
	ctx context.Context,
	req *pb.MassResponseRequest,
) (*pb.MassResponseResponse, error) {
	if m.triggerMassResponseError != nil {
		return nil, m.triggerMassResponseError
	}

	return &pb.MassResponseResponse{
		Success:      true,
		AgentsCloned: req.AgentCount,
		Message:      "mass response triggered",
	}, nil
}

// GetSystemHealth implements system health retrieval
func (m *mockActiveImmuneCoreServer) GetSystemHealth(
	ctx context.Context,
	req *pb.SystemHealthRequest,
) (*pb.SystemHealthResponse, error) {
	if m.getSystemHealthError != nil {
		return nil, m.getSystemHealthError
	}

	return &pb.SystemHealthResponse{
		Status:           pb.SystemHealthResponse_HEALTHY,
		TotalLymphnodes:  5,
		HealthyLymphnodes: 5,
		TotalAgents:      500,
		ActiveAgents:     450,
	}, nil
}

// setupTestServer creates an in-memory gRPC server for testing
func setupTestServer(t *testing.T, mockServer *mockActiveImmuneCoreServer) (*grpc.Server, *bufconn.Listener) {
	lis := bufconn.Listen(bufSize)

	server := grpc.NewServer()
	pb.RegisterActiveImmuneCoreServer(server, mockServer)

	go func() {
		if err := server.Serve(lis); err != nil {
			// Server stopped
		}
	}()

	t.Cleanup(func() {
		server.Stop()
		lis.Close()
	})

	return server, lis
}

// createTestClient creates an ImmuneClient connected to the test server
func createTestClient(t *testing.T, lis *bufconn.Listener) *ImmuneClient {
	ctx := context.Background()

	conn, err := grpc.DialContext(
		ctx,
		"bufnet",
		grpc.WithContextDialer(func(context.Context, string) (net.Conn, error) {
			return lis.Dial()
		}),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	require.NoError(t, err)

	t.Cleanup(func() {
		conn.Close()
	})

	return &ImmuneClient{
		conn:          conn,
		client:        pb.NewActiveImmuneCoreClient(conn),
		serverAddress: "bufnet",
	}
}

// ============================================================
// Constructor Tests
// ============================================================

func TestNewImmuneClient(t *testing.T) {
	t.Run("with explicit server address", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)

		client := createTestClient(t, lis)

		assert.NotNil(t, client)
		assert.NotNil(t, client.conn)
		assert.NotNil(t, client.client)
		assert.Equal(t, "bufnet", client.serverAddress)
	})

	t.Run("with environment variable", func(t *testing.T) {
		os.Setenv("VCLI_IMMUNE_ENDPOINT", "test-endpoint:50052")
		defer os.Unsetenv("VCLI_IMMUNE_ENDPOINT")

		// This will fail to connect, but we're testing the endpoint resolution
		client, err := NewImmuneClient("")

		// Connection will fail, but client should be created with env var endpoint
		if client != nil {
			assert.Equal(t, "test-endpoint:50052", client.serverAddress)
			client.Close()
		} else {
			// If client creation fails, that's expected for invalid endpoint
			assert.Error(t, err)
		}
	})

	t.Run("with default endpoint", func(t *testing.T) {
		os.Unsetenv("VCLI_IMMUNE_ENDPOINT")

		// This will fail to connect to default localhost:50052
		client, err := NewImmuneClient("")

		// Connection will fail, but client should be created with default endpoint
		if client != nil {
			assert.Equal(t, "localhost:50052", client.serverAddress)
			client.Close()
		} else {
			// If client creation fails, that's expected for unreachable endpoint
			assert.Error(t, err)
		}
	})
}

// ============================================================
// Agent Management Tests
// ============================================================

func TestImmuneClient_ListAgents(t *testing.T) {
	t.Run("successful list", func(t *testing.T) {
		mockAgents := []*pb.Agent{
			{
				AgentId: "agent-1",
				Type:    pb.AgentType_MACROPHAGE,
				State:   pb.AgentState_ACTIVE,
			},
			{
				AgentId: "agent-2",
				Type:    pb.AgentType_T_CELL,
				State:   pb.AgentState_INACTIVE,
			},
		}

		mockServer := &mockActiveImmuneCoreServer{agents: mockAgents}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.ListAgents(
			ctx,
			"lymph-1",
			pb.AgentType_AGENT_TYPE_UNSPECIFIED,
			pb.AgentState_STATE_UNSPECIFIED,
			1,
			10,
			true,
		)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.Len(t, resp.Agents, 2)
		assert.Equal(t, int32(2), resp.TotalCount)
		assert.Equal(t, "agent-1", resp.Agents[0].AgentId)
	})

	t.Run("list agents error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			listAgentsError: status.Error(codes.Internal, "database error"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.ListAgents(ctx, "", pb.AgentType_AGENT_TYPE_UNSPECIFIED, pb.AgentState_STATE_UNSPECIFIED, 1, 10, false)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to list agents")
	})

	t.Run("list with filters", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{agents: []*pb.Agent{}}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.ListAgents(
			ctx,
			"lymph-1",
			pb.AgentType_MACROPHAGE,
			pb.AgentState_ACTIVE,
			1,
			10,
			true,
		)

		require.NoError(t, err)
		assert.NotNil(t, resp)
	})
}

func TestImmuneClient_GetAgent(t *testing.T) {
	t.Run("successful get", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		agent, err := client.GetAgent(ctx, "agent-1", true, true)

		require.NoError(t, err)
		assert.NotNil(t, agent)
		assert.Equal(t, "agent-1", agent.AgentId)
		assert.Equal(t, pb.AgentType_MACROPHAGE, agent.Type)
		assert.Equal(t, pb.AgentState_ACTIVE, agent.State)
	})

	t.Run("agent not found", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			getAgentError: status.Error(codes.NotFound, "agent not found"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.GetAgent(ctx, "nonexistent", false, false)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get agent")
	})

	t.Run("get with options", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		agent, err := client.GetAgent(ctx, "agent-1", true, false)

		require.NoError(t, err)
		assert.NotNil(t, agent)
	})
}

func TestImmuneClient_CloneAgent(t *testing.T) {
	t.Run("successful clone", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.CloneAgent(ctx, "agent-1", 3, "lymph-1")

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.Equal(t, int32(3), resp.SuccessCount)
		assert.Len(t, resp.ClonedAgentIds, 3)
	})

	t.Run("clone error - insufficient resources", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			cloneAgentError: status.Error(codes.ResourceExhausted, "insufficient resources"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.CloneAgent(ctx, "agent-1", 1000, "lymph-1")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to clone agent")
	})

	t.Run("clone with zero count", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.CloneAgent(ctx, "agent-1", 0, "lymph-1")

		require.NoError(t, err)
		assert.NotNil(t, resp)
	})
}

func TestImmuneClient_TerminateAgent(t *testing.T) {
	t.Run("graceful termination", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.TerminateAgent(ctx, "agent-1", "test completed", true)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.True(t, resp.Success)
		assert.Contains(t, resp.Message, "agent-1")
	})

	t.Run("forced termination", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.TerminateAgent(ctx, "agent-1", "error detected", false)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.True(t, resp.Success)
	})

	t.Run("terminate error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			terminateAgentError: status.Error(codes.FailedPrecondition, "agent busy"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.TerminateAgent(ctx, "agent-1", "test", true)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to terminate agent")
	})
}

func TestImmuneClient_GetAgentMetrics(t *testing.T) {
	t.Run("successful get metrics", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		metrics, err := client.GetAgentMetrics(ctx, "agent-1")

		require.NoError(t, err)
		assert.NotNil(t, metrics)
		assert.Equal(t, "agent-1", metrics.AgentId)
		assert.Equal(t, float64(45.5), metrics.AvgCpuPercent)
		assert.Equal(t, float64(512.0), metrics.AvgMemoryMb)
		assert.Equal(t, int64(100), metrics.TotalActions)
	})

	t.Run("metrics error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			getAgentMetricsError: status.Error(codes.NotFound, "agent not found"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.GetAgentMetrics(ctx, "nonexistent")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get agent metrics")
	})
}

// ============================================================
// Lymphnode Operations Tests
// ============================================================

func TestImmuneClient_ListLymphnodes(t *testing.T) {
	t.Run("successful list", func(t *testing.T) {
		mockLymphnodes := []*pb.Lymphnode{
			{LymphnodeId: "lymph-1", Zone: "zone-a"},
			{LymphnodeId: "lymph-2", Zone: "zone-b"},
		}

		mockServer := &mockActiveImmuneCoreServer{lymphnodes: mockLymphnodes}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.ListLymphnodes(ctx, "zone-a", true)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.Len(t, resp.Lymphnodes, 2)
		assert.Equal(t, int32(2), resp.TotalCount)
	})

	t.Run("list error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			listLymphnodesError: status.Error(codes.Internal, "database error"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.ListLymphnodes(ctx, "", false)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to list lymphnodes")
	})
}

func TestImmuneClient_GetLymphnodeStatus(t *testing.T) {
	t.Run("successful get status", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		status, err := client.GetLymphnodeStatus(ctx, "lymph-1")

		require.NoError(t, err)
		assert.NotNil(t, status)
		assert.NotNil(t, status.Lymphnode)
		assert.Equal(t, "lymph-1", status.Lymphnode.LymphnodeId)
		assert.True(t, status.Lymphnode.IsHealthy)
		assert.Equal(t, int32(10), status.Lymphnode.TotalAgents)
	})

	t.Run("status error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			getLymphnodeStatusError: status.Error(codes.NotFound, "lymphnode not found"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.GetLymphnodeStatus(ctx, "nonexistent")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get lymphnode status")
	})
}

func TestImmuneClient_GetLymphnodeMetrics(t *testing.T) {
	t.Run("successful get metrics", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		metrics, err := client.GetLymphnodeMetrics(ctx, "lymph-1")

		require.NoError(t, err)
		assert.NotNil(t, metrics)
		assert.Equal(t, "lymph-1", metrics.LymphnodeId)
		assert.Equal(t, int32(100), metrics.TotalAgents)
		assert.Equal(t, int32(85), metrics.ActiveAgents)
	})

	t.Run("metrics error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			getLymphnodeMetricsError: status.Error(codes.Unavailable, "service unavailable"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.GetLymphnodeMetrics(ctx, "lymph-1")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get lymphnode metrics")
	})
}

// ============================================================
// Cytokine Streaming Tests
// ============================================================

func TestImmuneClient_StreamCytokines(t *testing.T) {
	t.Run("successful streaming", func(t *testing.T) {
		mockCytokines := []*pb.Cytokine{
			{CytokineId: "cyt-1", EventType: "alert", Severity: 3},
			{CytokineId: "cyt-2", EventType: "warning", Severity: 2},
		}

		mockServer := &mockActiveImmuneCoreServer{cytokines: mockCytokines}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		var received []*pb.Cytokine
		handler := func(cyt *pb.Cytokine) error {
			received = append(received, cyt)
			return nil
		}

		ctx := context.Background()
		err := client.StreamCytokines(
			ctx,
			[]string{"topic1", "topic2"},
			"lymph-1",
			"alert",
			2,
			handler,
		)

		require.NoError(t, err)
		assert.Len(t, received, 2)
		assert.Equal(t, "cyt-1", received[0].CytokineId)
	})

	t.Run("handler error", func(t *testing.T) {
		mockCytokines := []*pb.Cytokine{{CytokineId: "cyt-1"}}

		mockServer := &mockActiveImmuneCoreServer{cytokines: mockCytokines}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		handler := func(cyt *pb.Cytokine) error {
			return assert.AnError
		}

		ctx := context.Background()
		err := client.StreamCytokines(ctx, nil, "", "", 0, handler)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "cytokine handler error")
	})

	t.Run("stream error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			streamCytokinesError: status.Error(codes.Internal, "stream error"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		handler := func(cyt *pb.Cytokine) error {
			return nil
		}

		ctx := context.Background()
		err := client.StreamCytokines(ctx, nil, "", "", 0, handler)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "stream error")
	})
}

func TestImmuneClient_PublishCytokine(t *testing.T) {
	t.Run("successful publish", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.PublishCytokine(
			ctx,
			"agent-1",
			"alert",
			3,
			[]string{"tag1", "tag2"},
		)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.True(t, resp.Success)
		assert.Equal(t, "cyt-123", resp.CytokineId)
	})

	t.Run("publish error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			publishCytokineError: status.Error(codes.InvalidArgument, "invalid severity"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.PublishCytokine(ctx, "agent-1", "alert", -1, nil)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to publish cytokine")
	})
}

// ============================================================
// Hormone System Tests
// ============================================================

func TestImmuneClient_StreamHormones(t *testing.T) {
	t.Run("successful streaming", func(t *testing.T) {
		mockHormones := []*pb.Hormone{
			{HormoneId: "horm-1", Type: "cortisol", Nivel: 0.8},
			{HormoneId: "horm-2", Type: "adrenaline", Nivel: 0.6},
		}

		mockServer := &mockActiveImmuneCoreServer{hormones: mockHormones}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		var received []*pb.Hormone
		handler := func(h *pb.Hormone) error {
			received = append(received, h)
			return nil
		}

		ctx := context.Background()
		err := client.StreamHormones(
			ctx,
			[]string{"cortisol", "adrenaline"},
			"zone-a",
			handler,
		)

		require.NoError(t, err)
		assert.Len(t, received, 2)
		assert.Equal(t, "cortisol", received[0].Type)
	})

	t.Run("handler error", func(t *testing.T) {
		mockHormones := []*pb.Hormone{{HormoneId: "horm-1"}}

		mockServer := &mockActiveImmuneCoreServer{hormones: mockHormones}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		handler := func(h *pb.Hormone) error {
			return assert.AnError
		}

		ctx := context.Background()
		err := client.StreamHormones(ctx, nil, "", handler)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "hormone handler error")
	})

	t.Run("stream error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			streamHormonesError: status.Error(codes.Unavailable, "service down"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		handler := func(h *pb.Hormone) error {
			return nil
		}

		ctx := context.Background()
		err := client.StreamHormones(ctx, nil, "", handler)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "service down")
	})
}

func TestImmuneClient_PublishHormone(t *testing.T) {
	t.Run("successful publish", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.PublishHormone(ctx, "cortisol", "lymph-1", 0.75)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.True(t, resp.Success)
		assert.Equal(t, "horm-456", resp.HormoneId)
	})

	t.Run("publish error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			publishHormoneError: status.Error(codes.OutOfRange, "invalid nivel"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.PublishHormone(ctx, "cortisol", "lymph-1", 1.5)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to publish hormone")
	})
}

// ============================================================
// Coordination Tests
// ============================================================

func TestImmuneClient_TriggerMassResponse(t *testing.T) {
	t.Run("successful trigger", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.TriggerMassResponse(
			ctx,
			"lymph-1",
			"ddos-attack",
			10,
			pb.AgentType_MACROPHAGE,
			"critical threat detected",
		)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.True(t, resp.Success)
		assert.Equal(t, int32(10), resp.AgentsCloned)
	})

	t.Run("trigger error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			triggerMassResponseError: status.Error(codes.ResourceExhausted, "capacity exceeded"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.TriggerMassResponse(
			ctx,
			"lymph-1",
			"attack",
			1000,
			pb.AgentType_MACROPHAGE,
			"test",
		)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to trigger mass response")
	})
}

func TestImmuneClient_GetSystemHealth(t *testing.T) {
	t.Run("successful get health", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.GetSystemHealth(ctx, true, true)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.Equal(t, pb.SystemHealthResponse_HEALTHY, resp.Status)
		assert.Equal(t, int32(5), resp.TotalLymphnodes)
		assert.Equal(t, int32(500), resp.TotalAgents)
	})

	t.Run("health error", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			getSystemHealthError: status.Error(codes.Unavailable, "system unavailable"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.GetSystemHealth(ctx, false, false)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get system health")
	})

	t.Run("health with options", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.GetSystemHealth(ctx, false, true)

		require.NoError(t, err)
		assert.NotNil(t, resp)
	})
}

// ============================================================
// Utility Methods Tests
// ============================================================

func TestImmuneClient_ServerAddress(t *testing.T) {
	t.Run("returns correct server address", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		assert.Equal(t, "bufnet", client.ServerAddress())
	})
}

func TestImmuneClient_IsHealthy(t *testing.T) {
	t.Run("system is healthy", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		healthy := client.IsHealthy(ctx)

		assert.True(t, healthy)
	})

	t.Run("system is unhealthy", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			getSystemHealthError: status.Error(codes.Unavailable, "system down"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		healthy := client.IsHealthy(ctx)

		assert.False(t, healthy)
	})
}

func TestImmuneClient_Close(t *testing.T) {
	t.Run("close valid connection", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		err := client.Close()
		assert.NoError(t, err)
	})

	t.Run("close nil connection", func(t *testing.T) {
		client := &ImmuneClient{conn: nil}

		err := client.Close()
		assert.NoError(t, err)
	})

	t.Run("close idempotent", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		err := client.Close()
		assert.NoError(t, err)

		// Close again should not panic
		err = client.Close()
		_ = err
	})
}

// ============================================================
// Integration-style Tests
// ============================================================

func TestImmuneClient_Integration(t *testing.T) {
	t.Run("complete workflow", func(t *testing.T) {
		mockServer := &mockActiveImmuneCoreServer{
			agents: []*pb.Agent{
				{AgentId: "agent-1", Type: pb.AgentType_MACROPHAGE},
			},
			lymphnodes: []*pb.Lymphnode{
				{LymphnodeId: "lymph-1", Zone: "zone-a"},
			},
			cytokines: []*pb.Cytokine{
				{CytokineId: "cyt-1", EventType: "alert"},
			},
			hormones: []*pb.Hormone{
				{HormoneId: "horm-1", Type: "cortisol"},
			},
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()

		// 1. Check system health
		health, err := client.GetSystemHealth(ctx, true, true)
		require.NoError(t, err)
		assert.Equal(t, pb.SystemHealthResponse_HEALTHY, health.Status)

		// 2. List agents
		agents, err := client.ListAgents(ctx, "", pb.AgentType_AGENT_TYPE_UNSPECIFIED, pb.AgentState_STATE_UNSPECIFIED, 1, 10, false)
		require.NoError(t, err)
		assert.Len(t, agents.Agents, 1)

		// 3. Get agent details
		agent, err := client.GetAgent(ctx, "agent-1", false, false)
		require.NoError(t, err)
		assert.Equal(t, "agent-1", agent.AgentId)

		// 4. Get agent metrics
		metrics, err := client.GetAgentMetrics(ctx, "agent-1")
		require.NoError(t, err)
		assert.NotNil(t, metrics)

		// 5. List lymphnodes
		lymphs, err := client.ListLymphnodes(ctx, "", false)
		require.NoError(t, err)
		assert.Len(t, lymphs.Lymphnodes, 1)

		// 6. Publish cytokine
		cytResp, err := client.PublishCytokine(ctx, "agent-1", "alert", 3, nil)
		require.NoError(t, err)
		assert.True(t, cytResp.Success)

		// 7. Publish hormone
		hormResp, err := client.PublishHormone(ctx, "cortisol", "lymph-1", 0.5)
		require.NoError(t, err)
		assert.True(t, hormResp.Success)

		// 8. Trigger mass response
		massResp, err := client.TriggerMassResponse(ctx, "lymph-1", "threat", 5, pb.AgentType_MACROPHAGE, "test")
		require.NoError(t, err)
		assert.True(t, massResp.Success)

		// 9. Clone agent
		cloneResp, err := client.CloneAgent(ctx, "agent-1", 2, "lymph-1")
		require.NoError(t, err)
		assert.Len(t, cloneResp.ClonedAgentIds, 2)

		// 10. Terminate agent
		termResp, err := client.TerminateAgent(ctx, "agent-1", "test complete", true)
		require.NoError(t, err)
		assert.True(t, termResp.Success)

		// 11. Close client
		err = client.Close()
		assert.NoError(t, err)
	})
}
