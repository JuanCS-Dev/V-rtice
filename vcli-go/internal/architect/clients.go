package architect

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// ARCHITECT CLIENT
// ============================================================================

type ArchitectClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewArchitectClient(endpoint string) *ArchitectClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("architect")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &ArchitectClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *ArchitectClient) Analyze() (*AnalyzeResult, error) {
	ctx := context.Background()

	var result AnalyzeResult
	err := c.httpClient.GetJSON(ctx, "/analyze", &result)
	if err != nil {
		return nil, fmt.Errorf("analyze system failed: %w", err)
	}

	return &result, nil
}

func (c *ArchitectClient) Blueprint(req *BlueprintRequest) (*BlueprintResult, error) {
	ctx := context.Background()

	var result BlueprintResult
	err := c.httpClient.PostJSONResponse(ctx, "/blueprint", req, &result)
	if err != nil {
		return nil, fmt.Errorf("generate blueprint failed: %w", err)
	}

	return &result, nil
}

func (c *ArchitectClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get architect status failed: %w", err)
	}

	return &result, nil
}
