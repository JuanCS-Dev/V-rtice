package vulnscan

import (
	"context"
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// VULNERABILITY SCANNER CLIENT
// ============================================================================

type VulnScanClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewVulnScanClient(endpoint string) *VulnScanClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("vulnscan")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	clientConfig.Timeout = 120 * time.Second // Vulnerability scans may take longer
	return &VulnScanClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *VulnScanClient) Scan(req *ScanRequest) (*ScanResult, error) {
	ctx := context.Background()

	var result ScanResult
	err := c.httpClient.PostJSONResponse(ctx, "/scan", req, &result)
	if err != nil {
		return nil, fmt.Errorf("vulnerability scan failed: %w", err)
	}

	return &result, nil
}

func (c *VulnScanClient) GetReport(req *ReportRequest) (*ReportResult, error) {
	ctx := context.Background()

	var result ReportResult
	err := c.httpClient.PostJSONResponse(ctx, "/scan/report", req, &result)
	if err != nil {
		return nil, fmt.Errorf("get scan report failed: %w", err)
	}

	return &result, nil
}

func (c *VulnScanClient) GetStatus() (*StatusResult, error) {
	ctx := context.Background()

	var result StatusResult
	err := c.httpClient.GetJSON(ctx, "/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get vulnscan status failed: %w", err)
	}

	return &result, nil
}
