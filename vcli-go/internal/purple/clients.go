package purple

import (
	"context"
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// PURPLE TEAM CLIENT
// ============================================================================

type PurpleClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewPurpleClient(endpoint string) *PurpleClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("purple")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	clientConfig.Timeout = 60 * time.Second // Purple team exercises may take longer
	return &PurpleClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *PurpleClient) RunExercise(req *ExerciseRequest) (*ExerciseResult, error) {
	ctx := context.Background()

	var result ExerciseResult
	err := c.httpClient.PostJSONResponse(ctx, "/exercise/run", req, &result)
	if err != nil {
		return nil, fmt.Errorf("run purple team exercise failed: %w", err)
	}

	return &result, nil
}

func (c *PurpleClient) GetReport(req *ReportRequest) (*ReportResult, error) {
	ctx := context.Background()

	var result ReportResult
	err := c.httpClient.PostJSONResponse(ctx, "/exercise/report", req, &result)
	if err != nil {
		return nil, fmt.Errorf("get exercise report failed: %w", err)
	}

	return &result, nil
}

func (c *PurpleClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get purple team status failed: %w", err)
	}

	return &result, nil
}
