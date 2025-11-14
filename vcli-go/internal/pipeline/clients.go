package pipeline

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// PIPELINE CLIENT
// ============================================================================

type PipelineClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewPipelineClient(endpoint string) *PipelineClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("pipeline")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &PipelineClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *PipelineClient) Ingest(req *IngestRequest) (*IngestResult, error) {
	ctx := context.Background()

	var result IngestResult
	err := c.httpClient.PostJSONResponse(ctx, "/tataca/ingest", req, &result)
	if err != nil {
		return nil, fmt.Errorf("ingest data failed: %w", err)
	}

	return &result, nil
}

func (c *PipelineClient) GraphQuery(req *GraphQueryRequest) (*GraphQueryResult, error) {
	ctx := context.Background()

	var result GraphQueryResult
	err := c.httpClient.PostJSONResponse(ctx, "/seriema/query", req, &result)
	if err != nil {
		return nil, fmt.Errorf("graph query failed: %w", err)
	}

	return &result, nil
}

func (c *PipelineClient) Visualize(req *VisualizeRequest) (*VisualizeResult, error) {
	ctx := context.Background()

	var result VisualizeResult
	err := c.httpClient.PostJSONResponse(ctx, "/seriema/visualize", req, &result)
	if err != nil {
		return nil, fmt.Errorf("visualize graph failed: %w", err)
	}

	return &result, nil
}

func (c *PipelineClient) PublishCommand(req *CommandRequest) (*CommandResult, error) {
	ctx := context.Background()

	var result CommandResult
	err := c.httpClient.PostJSONResponse(ctx, "/command_bus/publish", req, &result)
	if err != nil {
		return nil, fmt.Errorf("publish command failed: %w", err)
	}

	return &result, nil
}

func (c *PipelineClient) ListTopics() (*TopicListResult, error) {
	ctx := context.Background()

	var result TopicListResult
	err := c.httpClient.GetJSON(ctx, "/command_bus/topics", &result)
	if err != nil {
		return nil, fmt.Errorf("list topics failed: %w", err)
	}

	return &result, nil
}

func (c *PipelineClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get pipeline status failed: %w", err)
	}

	return &result, nil
}
