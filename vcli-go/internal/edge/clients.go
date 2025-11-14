package edge

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// EDGE CLIENT
// ============================================================================

type EdgeClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewEdgeClient(endpoint string) *EdgeClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("edge")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &EdgeClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *EdgeClient) Deploy(req *DeployRequest) (*DeployResult, error) {
	ctx := context.Background()

	var result DeployResult
	err := c.httpClient.PostJSONResponse(ctx, "/agents/deploy", req, &result)
	if err != nil {
		return nil, fmt.Errorf("deploy edge agent failed: %w", err)
	}

	return &result, nil
}

func (c *EdgeClient) List() (*ListResult, error) {
	ctx := context.Background()

	var result ListResult
	err := c.httpClient.GetJSON(ctx, "/agents", &result)
	if err != nil {
		return nil, fmt.Errorf("list edge agents failed: %w", err)
	}

	return &result, nil
}

func (c *EdgeClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get edge status failed: %w", err)
	}

	return &result, nil
}
