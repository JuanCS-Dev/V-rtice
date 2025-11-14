package streaming

import (
	"context"
	"net"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"google.golang.org/grpc/test/bufconn"
	"google.golang.org/protobuf/types/known/timestamppb"

	pb "github.com/verticedev/vcli-go/api/grpc/kafka"
)

const bufSize = 1024 * 1024

// mockKafkaProxyServer implements pb.KafkaProxyServer for testing
type mockKafkaProxyServer struct {
	pb.UnimplementedKafkaProxyServer

	// Configuration for different test scenarios
	streamTopicMessages  []*pb.KafkaMessage
	streamTopicsMessages []*pb.KafkaMessage
	publishError         error
	getTopicInfoError    error
	listTopicsError      error
	streamTopicError     error
	streamTopicsError    error
}

// StreamTopic implements server-side streaming for single topic
func (m *mockKafkaProxyServer) StreamTopic(
	req *pb.StreamTopicRequest,
	stream grpc.ServerStreamingServer[pb.KafkaMessage],
) error {
	if m.streamTopicError != nil {
		return m.streamTopicError
	}

	// Send configured messages
	for _, msg := range m.streamTopicMessages {
		if err := stream.Send(msg); err != nil {
			return err
		}
	}

	return nil
}

// StreamTopics implements server-side streaming for multiple topics
func (m *mockKafkaProxyServer) StreamTopics(
	req *pb.StreamTopicsRequest,
	stream grpc.ServerStreamingServer[pb.KafkaMessage],
) error {
	if m.streamTopicsError != nil {
		return m.streamTopicsError
	}

	// Send configured messages
	for _, msg := range m.streamTopicsMessages {
		if err := stream.Send(msg); err != nil {
			return err
		}
	}

	return nil
}

// PublishMessage implements message publishing
func (m *mockKafkaProxyServer) PublishMessage(
	ctx context.Context,
	req *pb.PublishMessageRequest,
) (*pb.PublishMessageResponse, error) {
	if m.publishError != nil {
		return nil, m.publishError
	}

	return &pb.PublishMessageResponse{
		Success:   true,
		Partition: 0,
		Offset:    12345,
	}, nil
}

// GetTopicInfo implements topic metadata retrieval
func (m *mockKafkaProxyServer) GetTopicInfo(
	ctx context.Context,
	req *pb.GetTopicInfoRequest,
) (*pb.TopicInfo, error) {
	if m.getTopicInfoError != nil {
		return nil, m.getTopicInfoError
	}

	return &pb.TopicInfo{
		Topic:             req.Topic,
		NumPartitions:     3,
		ReplicationFactor: 2,
		Config: map[string]string{
			"retention.ms": "604800000",
		},
	}, nil
}

// ListTopics implements topic listing
func (m *mockKafkaProxyServer) ListTopics(
	ctx context.Context,
	req *pb.ListTopicsRequest,
) (*pb.ListTopicsResponse, error) {
	if m.listTopicsError != nil {
		return nil, m.listTopicsError
	}

	topics := []string{"topic1", "topic2", "topic3"}

	// Filter internal topics if requested
	if !req.IncludeInternal {
		topics = []string{"topic1", "topic2"}
	}

	return &pb.ListTopicsResponse{
		Topics: topics,
	}, nil
}

// setupTestServer creates an in-memory gRPC server for testing
func setupTestServer(t *testing.T, mockServer *mockKafkaProxyServer) (*grpc.Server, *bufconn.Listener) {
	lis := bufconn.Listen(bufSize)

	server := grpc.NewServer()
	pb.RegisterKafkaProxyServer(server, mockServer)

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

// createTestClient creates a KafkaClient connected to the test server
func createTestClient(t *testing.T, lis *bufconn.Listener) *KafkaClient {
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

	return &KafkaClient{
		conn:          conn,
		client:        pb.NewKafkaProxyClient(conn),
		serverAddress: "bufnet",
	}
}

// ============================================================
// Constructor Tests
// ============================================================

func TestNewKafkaClient(t *testing.T) {
	t.Run("successful connection", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)

		client := createTestClient(t, lis)

		assert.NotNil(t, client)
		assert.NotNil(t, client.conn)
		assert.NotNil(t, client.client)
		assert.Equal(t, "bufnet", client.serverAddress)
	})

	t.Run("connection error - invalid address", func(t *testing.T) {
		// This will fail during actual dial, not during client creation
		// since grpc.NewClient doesn't connect immediately
		client, err := NewKafkaClient("invalid:99999")

		// NewClient succeeds, but connection will fail on first RPC
		require.NoError(t, err)
		assert.NotNil(t, client)

		// Cleanup
		if client != nil {
			client.Close()
		}
	})
}

// ============================================================
// StreamTopic Tests
// ============================================================

func TestKafkaClient_StreamTopic(t *testing.T) {
	t.Run("successful streaming", func(t *testing.T) {
		// Setup mock messages
		mockMessages := []*pb.KafkaMessage{
			{
				Topic:     "test-topic",
				Partition: 0,
				Offset:    1,
				Key:       "key1",
				Timestamp: timestamppb.Now(),
			},
			{
				Topic:     "test-topic",
				Partition: 0,
				Offset:    2,
				Key:       "key2",
				Timestamp: timestamppb.Now(),
			},
		}

		mockServer := &mockKafkaProxyServer{
			streamTopicMessages: mockMessages,
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		// Track received messages
		var received []*pb.KafkaMessage
		handler := func(msg *pb.KafkaMessage) error {
			received = append(received, msg)
			return nil
		}

		ctx := context.Background()
		err := client.StreamTopic(
			ctx,
			"test-topic",
			"test-group",
			-1, // latest offset
			-1, // all partitions
			[]string{"event1", "event2"},
			1, // severity min
			map[string]string{"field1": "value1"},
			handler,
		)

		require.NoError(t, err)
		assert.Len(t, received, 2)
		assert.Equal(t, "key1", received[0].Key)
		assert.Equal(t, "key2", received[1].Key)
	})

	t.Run("handler error stops streaming", func(t *testing.T) {
		mockMessages := []*pb.KafkaMessage{
			{Topic: "test-topic", Offset: 1},
			{Topic: "test-topic", Offset: 2},
		}

		mockServer := &mockKafkaProxyServer{
			streamTopicMessages: mockMessages,
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		// Handler that fails on first message
		handlerCalled := 0
		handler := func(msg *pb.KafkaMessage) error {
			handlerCalled++
			return assert.AnError
		}

		ctx := context.Background()
		err := client.StreamTopic(
			ctx,
			"test-topic",
			"test-group",
			0,
			0,
			nil,
			0,
			nil,
			handler,
		)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "handler error")
		assert.Equal(t, 1, handlerCalled)
	})

	t.Run("stream error", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{
			streamTopicError: status.Error(codes.Internal, "kafka error"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		handler := func(msg *pb.KafkaMessage) error {
			return nil
		}

		ctx := context.Background()
		err := client.StreamTopic(
			ctx,
			"test-topic",
			"test-group",
			0,
			0,
			nil,
			0,
			nil,
			handler,
		)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "kafka error")
	})

	t.Run("context cancellation", func(t *testing.T) {
		// Create a mock that sends messages slowly
		mockServer := &mockKafkaProxyServer{
			streamTopicMessages: []*pb.KafkaMessage{
				{Topic: "test", Offset: 1},
			},
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx, cancel := context.WithCancel(context.Background())
		cancel() // Cancel immediately

		handler := func(msg *pb.KafkaMessage) error {
			return nil
		}

		err := client.StreamTopic(
			ctx,
			"test-topic",
			"test-group",
			0,
			0,
			nil,
			0,
			nil,
			handler,
		)

		// Should get an error due to cancelled context
		require.Error(t, err)
	})
}

// ============================================================
// StreamTopics Tests
// ============================================================

func TestKafkaClient_StreamTopics(t *testing.T) {
	t.Run("successful multi-topic streaming", func(t *testing.T) {
		mockMessages := []*pb.KafkaMessage{
			{Topic: "topic1", Partition: 0, Offset: 1, Key: "key1"},
			{Topic: "topic2", Partition: 0, Offset: 1, Key: "key2"},
			{Topic: "topic1", Partition: 0, Offset: 2, Key: "key3"},
		}

		mockServer := &mockKafkaProxyServer{
			streamTopicsMessages: mockMessages,
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		var received []*pb.KafkaMessage
		handler := func(msg *pb.KafkaMessage) error {
			received = append(received, msg)
			return nil
		}

		ctx := context.Background()
		err := client.StreamTopics(
			ctx,
			[]string{"topic1", "topic2"},
			"test-group",
			-1,
			[]string{"event1"},
			1,
			map[string]string{"filter": "value"},
			handler,
		)

		require.NoError(t, err)
		assert.Len(t, received, 3)

		// Verify topics
		topics := make(map[string]int)
		for _, msg := range received {
			topics[msg.Topic]++
		}
		assert.Equal(t, 2, topics["topic1"])
		assert.Equal(t, 1, topics["topic2"])
	})

	t.Run("handler error in multi-topic stream", func(t *testing.T) {
		mockMessages := []*pb.KafkaMessage{
			{Topic: "topic1", Offset: 1},
			{Topic: "topic2", Offset: 1},
		}

		mockServer := &mockKafkaProxyServer{
			streamTopicsMessages: mockMessages,
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		handler := func(msg *pb.KafkaMessage) error {
			return assert.AnError
		}

		ctx := context.Background()
		err := client.StreamTopics(
			ctx,
			[]string{"topic1", "topic2"},
			"test-group",
			0,
			nil,
			0,
			nil,
			handler,
		)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "handler error")
	})

	t.Run("stream error", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{
			streamTopicsError: status.Error(codes.Unavailable, "kafka unavailable"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		handler := func(msg *pb.KafkaMessage) error {
			return nil
		}

		ctx := context.Background()
		err := client.StreamTopics(
			ctx,
			[]string{"topic1"},
			"test-group",
			0,
			nil,
			0,
			nil,
			handler,
		)

		require.Error(t, err)
		// Error can be either from initial call or from stream.Recv()
		assert.True(t,
			assert.ObjectsAreEqual(err.Error(), "failed to stream topics: rpc error: code = Unavailable desc = kafka unavailable") ||
			assert.ObjectsAreEqual(err.Error(), "error receiving message: rpc error: code = Unavailable desc = kafka unavailable"),
		)
	})
}

// ============================================================
// PublishMessage Tests
// ============================================================

func TestKafkaClient_PublishMessage(t *testing.T) {
	t.Run("successful publish", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		payload := map[string]interface{}{
			"message": "test message",
			"count":   float64(42),
			"active":  true,
		}

		resp, err := client.PublishMessage(
			ctx,
			"test-topic",
			"test-key",
			payload,
			map[string]string{
				"header1": "value1",
				"header2": "value2",
			},
		)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.True(t, resp.Success)
		assert.Equal(t, int32(0), resp.Partition)
		assert.Equal(t, int64(12345), resp.Offset)
	})

	t.Run("publish with empty payload", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		payload := map[string]interface{}{}

		resp, err := client.PublishMessage(
			ctx,
			"test-topic",
			"test-key",
			payload,
			nil,
		)

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.True(t, resp.Success)
	})

	t.Run("publish error", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{
			publishError: status.Error(codes.Internal, "publish failed"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		payload := map[string]interface{}{
			"test": "data",
		}

		_, err := client.PublishMessage(
			ctx,
			"test-topic",
			"test-key",
			payload,
			nil,
		)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to publish message")
	})

	t.Run("invalid payload conversion", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()

		// Create invalid payload with unsupported type
		payload := map[string]interface{}{
			"invalid": make(chan int), // channels can't be converted to protobuf
		}

		_, err := client.PublishMessage(
			ctx,
			"test-topic",
			"test-key",
			payload,
			nil,
		)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to convert payload")
	})
}

// ============================================================
// GetTopicInfo Tests
// ============================================================

func TestKafkaClient_GetTopicInfo(t *testing.T) {
	t.Run("successful get topic info", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.GetTopicInfo(ctx, "test-topic")

		require.NoError(t, err)
		assert.NotNil(t, resp)
		assert.Equal(t, "test-topic", resp.Topic)
		assert.Equal(t, int32(3), resp.NumPartitions)
		assert.Equal(t, int32(2), resp.ReplicationFactor)
		assert.Contains(t, resp.Config, "retention.ms")
	})

	t.Run("topic not found error", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{
			getTopicInfoError: status.Error(codes.NotFound, "topic not found"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.GetTopicInfo(ctx, "nonexistent-topic")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get topic info")
	})

	t.Run("get topic info with empty name", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		resp, err := client.GetTopicInfo(ctx, "")

		// Should still work, server handles validation
		require.NoError(t, err)
		assert.NotNil(t, resp)
	})
}

// ============================================================
// ListTopics Tests
// ============================================================

func TestKafkaClient_ListTopics(t *testing.T) {
	t.Run("list topics - exclude internal", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		topics, err := client.ListTopics(ctx, "", false)

		require.NoError(t, err)
		assert.Len(t, topics, 2)
		assert.Contains(t, topics, "topic1")
		assert.Contains(t, topics, "topic2")
	})

	t.Run("list topics - include internal", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		topics, err := client.ListTopics(ctx, "", true)

		require.NoError(t, err)
		assert.Len(t, topics, 3)
	})

	t.Run("list topics with pattern", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		topics, err := client.ListTopics(ctx, "topic*", false)

		require.NoError(t, err)
		assert.NotEmpty(t, topics)
	})

	t.Run("list topics error", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{
			listTopicsError: status.Error(codes.Internal, "kafka error"),
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()
		_, err := client.ListTopics(ctx, "", false)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to list topics")
	})
}

// ============================================================
// Utility Methods Tests
// ============================================================

func TestKafkaClient_ServerAddress(t *testing.T) {
	t.Run("returns correct server address", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		assert.Equal(t, "bufnet", client.ServerAddress())
	})
}

func TestKafkaClient_Close(t *testing.T) {
	t.Run("close valid connection", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		err := client.Close()
		assert.NoError(t, err)
	})

	t.Run("close nil connection", func(t *testing.T) {
		client := &KafkaClient{
			conn: nil,
		}

		err := client.Close()
		assert.NoError(t, err)
	})

	t.Run("close idempotent", func(t *testing.T) {
		mockServer := &mockKafkaProxyServer{}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		err := client.Close()
		assert.NoError(t, err)

		// Close again should not panic
		err = client.Close()
		// May return error on double close, but should not panic
		_ = err
	})
}

// ============================================================
// Helper Function Tests
// ============================================================

func TestToStruct(t *testing.T) {
	t.Run("convert simple map", func(t *testing.T) {
		input := map[string]interface{}{
			"string": "value",
			"number": float64(42),
			"bool":   true,
		}

		result, err := toStruct(input)

		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "value", result.Fields["string"].GetStringValue())
		assert.Equal(t, float64(42), result.Fields["number"].GetNumberValue())
		assert.True(t, result.Fields["bool"].GetBoolValue())
	})

	t.Run("convert nested map", func(t *testing.T) {
		input := map[string]interface{}{
			"nested": map[string]interface{}{
				"key": "value",
			},
		}

		result, err := toStruct(input)

		require.NoError(t, err)
		assert.NotNil(t, result)
		nested := result.Fields["nested"].GetStructValue()
		assert.NotNil(t, nested)
		assert.Equal(t, "value", nested.Fields["key"].GetStringValue())
	})

	t.Run("convert array", func(t *testing.T) {
		input := map[string]interface{}{
			"array": []interface{}{"a", "b", "c"},
		}

		result, err := toStruct(input)

		require.NoError(t, err)
		assert.NotNil(t, result)
		list := result.Fields["array"].GetListValue()
		assert.NotNil(t, list)
		assert.Len(t, list.Values, 3)
	})

	t.Run("convert empty map", func(t *testing.T) {
		input := map[string]interface{}{}

		result, err := toStruct(input)

		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Empty(t, result.Fields)
	})

	t.Run("error on invalid type", func(t *testing.T) {
		input := map[string]interface{}{
			"invalid": make(chan int),
		}

		_, err := toStruct(input)

		require.Error(t, err)
	})
}

// ============================================================
// Integration-style Tests
// ============================================================

func TestKafkaClient_Integration(t *testing.T) {
	t.Run("complete workflow - publish and stream", func(t *testing.T) {
		mockMessages := []*pb.KafkaMessage{
			{
				Topic:     "test-topic",
				Partition: 0,
				Offset:    1,
				Key:       "published-key",
				Timestamp: timestamppb.Now(),
			},
		}

		mockServer := &mockKafkaProxyServer{
			streamTopicMessages: mockMessages,
		}
		_, lis := setupTestServer(t, mockServer)
		client := createTestClient(t, lis)

		ctx := context.Background()

		// 1. Publish a message
		publishResp, err := client.PublishMessage(
			ctx,
			"test-topic",
			"published-key",
			map[string]interface{}{
				"data": "test",
			},
			nil,
		)
		require.NoError(t, err)
		assert.True(t, publishResp.Success)

		// 2. Stream messages
		var received []*pb.KafkaMessage
		handler := func(msg *pb.KafkaMessage) error {
			received = append(received, msg)
			return nil
		}

		err = client.StreamTopic(
			ctx,
			"test-topic",
			"test-group",
			0,
			0,
			nil,
			0,
			nil,
			handler,
		)
		require.NoError(t, err)
		assert.Len(t, received, 1)
		assert.Equal(t, "published-key", received[0].Key)

		// 3. Get topic info
		topicInfo, err := client.GetTopicInfo(ctx, "test-topic")
		require.NoError(t, err)
		assert.Equal(t, "test-topic", topicInfo.Topic)

		// 4. List topics
		topics, err := client.ListTopics(ctx, "", false)
		require.NoError(t, err)
		assert.NotEmpty(t, topics)

		// 5. Close client
		err = client.Close()
		assert.NoError(t, err)
	})
}
