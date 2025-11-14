package maba

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

type MABAClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewMABAClient(endpoint string) *MABAClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("maba")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &MABAClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *MABAClient) Navigate(req *NavigateRequest) (*NavigateResult, error) {
	ctx := context.Background()

	var result NavigateResult
	err := c.httpClient.PostJSONResponse(ctx, "/navigate", req, &result)
	if err != nil {
		return nil, fmt.Errorf("navigate failed: %w", err)
	}

	return &result, nil
}

func (c *MABAClient) Extract(req *ExtractRequest) (*ExtractResult, error) {
	ctx := context.Background()

	var result ExtractResult
	err := c.httpClient.PostJSONResponse(ctx, "/extract", req, &result)
	if err != nil {
		return nil, fmt.Errorf("extract failed: %w", err)
	}

	return &result, nil
}

func (c *MABAClient) ListSessions() (*SessionListResult, error) {
	ctx := context.Background()

	var result SessionListResult
	err := c.httpClient.GetJSON(ctx, "/sessions", &result)
	if err != nil {
		return nil, fmt.Errorf("list sessions failed: %w", err)
	}

	return &result, nil
}

func (c *MABAClient) QueryMap(req *MapQueryRequest) (*MapQueryResult, error) {
	ctx := context.Background()

	var result MapQueryResult
	err := c.httpClient.PostJSONResponse(ctx, "/cognitive-map/query", req, &result)
	if err != nil {
		return nil, fmt.Errorf("query map failed: %w", err)
	}

	return &result, nil
}

func (c *MABAClient) MapStats() (*MapStatsResult, error) {
	ctx := context.Background()

	var result MapStatsResult
	err := c.httpClient.GetJSON(ctx, "/cognitive-map/stats", &result)
	if err != nil {
		return nil, fmt.Errorf("map stats failed: %w", err)
	}

	return &result, nil
}

func (c *MABAClient) ListTools() (*ToolListResult, error) {
	ctx := context.Background()

	var result ToolListResult
	err := c.httpClient.GetJSON(ctx, "/tools", &result)
	if err != nil {
		return nil, fmt.Errorf("list tools failed: %w", err)
	}

	return &result, nil
}

func (c *MABAClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/health", &result)
	if err != nil {
		return nil, fmt.Errorf("get status failed: %w", err)
	}

	return &result, nil
}
