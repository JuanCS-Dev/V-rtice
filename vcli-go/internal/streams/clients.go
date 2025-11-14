package streams

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// STREAMS (KAFKA) CLIENT
// ============================================================================

type StreamsClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewStreamsClient(endpoint string) *StreamsClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("streams")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &StreamsClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

// ============================================================================
// TOPIC OPERATIONS
// ============================================================================

func (c *StreamsClient) ListTopics() (*TopicListResult, error) {
	ctx := context.Background()

	var result TopicListResult
	err := c.httpClient.GetJSON(ctx, "/topics", &result)
	if err != nil {
		return nil, fmt.Errorf("list topics failed: %w", err)
	}

	return &result, nil
}

func (c *StreamsClient) CreateTopic(req *TopicCreateRequest) (*TopicCreateResult, error) {
	ctx := context.Background()

	var result TopicCreateResult
	err := c.httpClient.PostJSONResponse(ctx, "/topics/create", req, &result)
	if err != nil {
		return nil, fmt.Errorf("create topic failed: %w", err)
	}

	return &result, nil
}

func (c *StreamsClient) DescribeTopic(req *TopicDescribeRequest) (*TopicDescribeResult, error) {
	ctx := context.Background()

	var result TopicDescribeResult
	err := c.httpClient.PostJSONResponse(ctx, "/topics/describe", req, &result)
	if err != nil {
		return nil, fmt.Errorf("describe topic failed: %w", err)
	}

	return &result, nil
}

// ============================================================================
// PRODUCE / CONSUME
// ============================================================================

func (c *StreamsClient) Produce(req *ProduceRequest) (*ProduceResult, error) {
	ctx := context.Background()

	var result ProduceResult
	err := c.httpClient.PostJSONResponse(ctx, "/produce", req, &result)
	if err != nil {
		return nil, fmt.Errorf("produce message failed: %w", err)
	}

	return &result, nil
}

func (c *StreamsClient) Consume(req *ConsumeRequest) (*ConsumeResult, error) {
	ctx := context.Background()

	var result ConsumeResult
	err := c.httpClient.PostJSONResponse(ctx, "/consume", req, &result)
	if err != nil {
		return nil, fmt.Errorf("consume messages failed: %w", err)
	}

	return &result, nil
}

// ============================================================================
// CONSUMER GROUPS
// ============================================================================

func (c *StreamsClient) ListConsumers() (*ConsumerListResult, error) {
	ctx := context.Background()

	var result ConsumerListResult
	err := c.httpClient.GetJSON(ctx, "/consumers", &result)
	if err != nil {
		return nil, fmt.Errorf("list consumers failed: %w", err)
	}

	return &result, nil
}

func (c *StreamsClient) GetConsumerLag(req *ConsumerLagRequest) (*ConsumerLagResult, error) {
	ctx := context.Background()

	var result ConsumerLagResult
	err := c.httpClient.PostJSONResponse(ctx, "/consumers/lag", req, &result)
	if err != nil {
		return nil, fmt.Errorf("get consumer lag failed: %w", err)
	}

	return &result, nil
}
