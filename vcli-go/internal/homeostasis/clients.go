package homeostasis

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// HOMEOSTASIS CLIENT
// ============================================================================

type HomeostasisClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewHomeostasisClient(endpoint string) *HomeostasisClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("homeostasis")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &HomeostasisClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *HomeostasisClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get homeostasis status failed: %w", err)
	}

	return &result, nil
}

func (c *HomeostasisClient) Adjust(req *AdjustRequest) (*AdjustResult, error) {
	ctx := context.Background()

	var result AdjustResult
	err := c.httpClient.PostJSONResponse(ctx, "/adjust", req, &result)
	if err != nil {
		return nil, fmt.Errorf("adjust homeostasis failed: %w", err)
	}

	return &result, nil
}
