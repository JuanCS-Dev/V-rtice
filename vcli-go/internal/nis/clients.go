package nis

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

type NISClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewNISClient(endpoint string) *NISClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("nis")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &NISClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *NISClient) GenerateNarrative(req *NarrativeRequest) (*NarrativeResult, error) {
	ctx := context.Background()

	var result NarrativeResult
	err := c.httpClient.PostJSONResponse(ctx, "/narrative/generate", req, &result)
	if err != nil {
		return nil, fmt.Errorf("generate narrative failed: %w", err)
	}

	return &result, nil
}

func (c *NISClient) ListNarratives() (*NarrativeListResult, error) {
	ctx := context.Background()

	var result NarrativeListResult
	err := c.httpClient.GetJSON(ctx, "/narrative/list", &result)
	if err != nil {
		return nil, fmt.Errorf("list narratives failed: %w", err)
	}

	return &result, nil
}

func (c *NISClient) DetectAnomalies(req *AnomalyRequest) (*AnomalyResult, error) {
	ctx := context.Background()

	var result AnomalyResult
	err := c.httpClient.PostJSONResponse(ctx, "/anomaly/detect", req, &result)
	if err != nil {
		return nil, fmt.Errorf("detect anomalies failed: %w", err)
	}

	return &result, nil
}

func (c *NISClient) GetBaseline(req *BaselineRequest) (*BaselineResult, error) {
	ctx := context.Background()

	var result BaselineResult
	err := c.httpClient.PostJSONResponse(ctx, "/anomaly/baseline", req, &result)
	if err != nil {
		return nil, fmt.Errorf("get baseline failed: %w", err)
	}

	return &result, nil
}

func (c *NISClient) GetCostStatus() (*CostStatusResult, error) {
	ctx := context.Background()

	var result CostStatusResult
	err := c.httpClient.GetJSON(ctx, "/cost/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get cost status failed: %w", err)
	}

	return &result, nil
}

func (c *NISClient) GetCostHistory() (*CostHistoryResult, error) {
	ctx := context.Background()

	var result CostHistoryResult
	err := c.httpClient.GetJSON(ctx, "/cost/history", &result)
	if err != nil {
		return nil, fmt.Errorf("get cost history failed: %w", err)
	}

	return &result, nil
}

func (c *NISClient) GetRateLimit() (*RateLimitResult, error) {
	ctx := context.Background()

	var result RateLimitResult
	err := c.httpClient.GetJSON(ctx, "/ratelimit", &result)
	if err != nil {
		return nil, fmt.Errorf("get rate limit failed: %w", err)
	}

	return &result, nil
}

func (c *NISClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/health", &result)
	if err != nil {
		return nil, fmt.Errorf("get status failed: %w", err)
	}

	return &result, nil
}
