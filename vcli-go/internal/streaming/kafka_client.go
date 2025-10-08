package streaming

import (
	"context"
	"fmt"
	"io"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/types/known/structpb"

	pb "github.com/verticedev/vcli-go/api/grpc/kafka"
)

// KafkaClient wraps the gRPC Kafka Proxy client
type KafkaClient struct {
	conn   *grpc.ClientConn
	client pb.KafkaProxyClient

	serverAddress string
}

// NewKafkaClient creates a new Kafka Proxy gRPC client
func NewKafkaClient(serverAddress string) (*KafkaClient, error) {
	conn, err := grpc.NewClient(
		serverAddress,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Kafka Proxy server: %w", err)
	}

	client := pb.NewKafkaProxyClient(conn)

	return &KafkaClient{
		conn:          conn,
		client:        client,
		serverAddress: serverAddress,
	}, nil
}

// Close closes the gRPC connection
func (c *KafkaClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

// ============================================================
// Streaming Operations
// ============================================================

// StreamTopic streams messages from a single Kafka topic
func (c *KafkaClient) StreamTopic(
	ctx context.Context,
	topic string,
	consumerGroup string,
	offset int64,
	partition int32,
	eventTypes []string,
	severityMin int32,
	fieldFilters map[string]string,
	handler func(*pb.KafkaMessage) error,
) error {
	req := &pb.StreamTopicRequest{
		Topic:         topic,
		ConsumerGroup: consumerGroup,
		Offset:        offset,
		Partition:     partition,
		EventTypes:    eventTypes,
		SeverityMin:   severityMin,
		FieldFilters:  fieldFilters,
	}

	stream, err := c.client.StreamTopic(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to stream topic: %w", err)
	}

	for {
		msg, err := stream.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return fmt.Errorf("error receiving message: %w", err)
		}

		if err := handler(msg); err != nil {
			return fmt.Errorf("handler error: %w", err)
		}
	}
}

// StreamTopics streams messages from multiple Kafka topics
func (c *KafkaClient) StreamTopics(
	ctx context.Context,
	topics []string,
	consumerGroup string,
	offset int64,
	eventTypes []string,
	severityMin int32,
	fieldFilters map[string]string,
	handler func(*pb.KafkaMessage) error,
) error {
	req := &pb.StreamTopicsRequest{
		Topics:        topics,
		ConsumerGroup: consumerGroup,
		Offset:        offset,
		EventTypes:    eventTypes,
		SeverityMin:   severityMin,
		FieldFilters:  fieldFilters,
	}

	stream, err := c.client.StreamTopics(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to stream topics: %w", err)
	}

	for {
		msg, err := stream.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return fmt.Errorf("error receiving message: %w", err)
		}

		if err := handler(msg); err != nil {
			return fmt.Errorf("handler error: %w", err)
		}
	}
}

// ============================================================
// Publishing Operations
// ============================================================

// PublishMessage publishes a message to a Kafka topic
func (c *KafkaClient) PublishMessage(
	ctx context.Context,
	topic, key string,
	payload map[string]interface{},
	headers map[string]string,
) (*pb.PublishMessageResponse, error) {
	// Convert payload to protobuf Struct
	payloadStruct, err := toStruct(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to convert payload: %w", err)
	}

	req := &pb.PublishMessageRequest{
		Topic:   topic,
		Key:     key,
		Payload: payloadStruct,
		Headers: headers,
	}

	resp, err := c.client.PublishMessage(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to publish message: %w", err)
	}

	return resp, nil
}

// ============================================================
// Metadata Operations
// ============================================================

// GetTopicInfo retrieves metadata for a specific topic
func (c *KafkaClient) GetTopicInfo(ctx context.Context, topic string) (*pb.TopicInfo, error) {
	req := &pb.GetTopicInfoRequest{
		Topic: topic,
	}

	resp, err := c.client.GetTopicInfo(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to get topic info: %w", err)
	}

	return resp, nil
}

// ListTopics lists all available Kafka topics
func (c *KafkaClient) ListTopics(ctx context.Context, pattern string, includeInternal bool) ([]string, error) {
	req := &pb.ListTopicsRequest{
		Pattern:         pattern,
		IncludeInternal: includeInternal,
	}

	resp, err := c.client.ListTopics(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to list topics: %w", err)
	}

	return resp.Topics, nil
}

// ============================================================
// Utility Functions
// ============================================================

// ServerAddress returns the server address
func (c *KafkaClient) ServerAddress() string {
	return c.serverAddress
}

// Helper function to convert map to protobuf Struct
func toStruct(m map[string]interface{}) (*structpb.Struct, error) {
	// Use protobuf's built-in conversion
	return structpb.NewStruct(m)
}
