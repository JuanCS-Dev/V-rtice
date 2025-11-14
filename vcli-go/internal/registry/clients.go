package registry

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// REGISTRY CLIENT
// ============================================================================

type RegistryClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewRegistryClient(endpoint string) *RegistryClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("registry")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &RegistryClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *RegistryClient) List() (*ListResult, error) {
	ctx := context.Background()

	var result ListResult
	err := c.httpClient.GetJSON(ctx, "/services", &result)
	if err != nil {
		return nil, fmt.Errorf("list services failed: %w", err)
	}

	return &result, nil
}

func (c *RegistryClient) Health(req *HealthRequest) (*HealthResult, error) {
	ctx := context.Background()

	var result HealthResult
	err := c.httpClient.PostJSONResponse(ctx, "/services/health", req, &result)
	if err != nil {
		return nil, fmt.Errorf("check service health failed: %w", err)
	}

	return &result, nil
}

func (c *RegistryClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get registry status failed: %w", err)
	}

	return &result, nil
}
