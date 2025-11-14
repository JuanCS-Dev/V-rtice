package rte

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

type RTEClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewRTEClient(endpoint string) *RTEClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("rte")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &RTEClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *RTEClient) Triage(req *TriageRequest) (*TriageResult, error) {
	ctx := context.Background()

	var result TriageResult
	err := c.httpClient.PostJSONResponse(ctx, "/triage", req, &result)
	if err != nil {
		return nil, fmt.Errorf("triage failed: %w", err)
	}

	return &result, nil
}

func (c *RTEClient) Correlate(req *FusionRequest) (*FusionResult, error) {
	ctx := context.Background()

	var result FusionResult
	err := c.httpClient.PostJSONResponse(ctx, "/fusion/correlate", req, &result)
	if err != nil {
		return nil, fmt.Errorf("correlate failed: %w", err)
	}

	return &result, nil
}

func (c *RTEClient) Predict(req *PredictRequest) (*PredictResult, error) {
	ctx := context.Background()

	var result PredictResult
	err := c.httpClient.PostJSONResponse(ctx, "/predict", req, &result)
	if err != nil {
		return nil, fmt.Errorf("predict failed: %w", err)
	}

	return &result, nil
}

func (c *RTEClient) Match(req *MatchRequest) (*MatchResult, error) {
	ctx := context.Background()

	var result MatchResult
	err := c.httpClient.PostJSONResponse(ctx, "/match", req, &result)
	if err != nil {
		return nil, fmt.Errorf("match failed: %w", err)
	}

	return &result, nil
}

func (c *RTEClient) ListPlaybooks() (*PlaybooksResult, error) {
	ctx := context.Background()

	var result PlaybooksResult
	err := c.httpClient.GetJSON(ctx, "/playbooks", &result)
	if err != nil {
		return nil, fmt.Errorf("list playbooks failed: %w", err)
	}

	return &result, nil
}

func (c *RTEClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/health", &result)
	if err != nil {
		return nil, fmt.Errorf("get status failed: %w", err)
	}

	return &result, nil
}
