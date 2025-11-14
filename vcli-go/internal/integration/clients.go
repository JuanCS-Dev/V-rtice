package integration

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// INTEGRATION CLIENT
// ============================================================================

type IntegrationClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewIntegrationClient(endpoint string) *IntegrationClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("integration")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &IntegrationClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *IntegrationClient) List() (*ListResult, error) {
	ctx := context.Background()

	var result ListResult
	err := c.httpClient.GetJSON(ctx, "/integrations", &result)
	if err != nil {
		return nil, fmt.Errorf("list integrations failed: %w", err)
	}

	return &result, nil
}

func (c *IntegrationClient) Test(req *TestRequest) (*TestResult, error) {
	ctx := context.Background()

	var result TestResult
	err := c.httpClient.PostJSONResponse(ctx, "/integrations/test", req, &result)
	if err != nil {
		return nil, fmt.Errorf("test integration failed: %w", err)
	}

	return &result, nil
}

func (c *IntegrationClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get integration status failed: %w", err)
	}

	return &result, nil
}
