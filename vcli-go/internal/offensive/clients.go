package offensive

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// ============================================================================
// UNIFIED OFFENSIVE CLIENT
// ============================================================================

type OffensiveClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewOffensiveClient(endpoint string) *OffensiveClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("offensive")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &OffensiveClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

// ============================================================================
// TOOLS
// ============================================================================

func (c *OffensiveClient) ListTools(req *ToolsListRequest) (*ToolsListResult, error) {
	ctx := context.Background()

	var result ToolsListResult
	err := c.httpClient.PostJSONResponse(ctx, "/tools/list", req, &result)
	if err != nil {
		return nil, fmt.Errorf("list tools failed: %w", err)
	}

	return &result, nil
}

// ============================================================================
// C2 (COMMAND & CONTROL)
// ============================================================================

func (c *OffensiveClient) LaunchC2(req *C2LaunchRequest) (*C2LaunchResult, error) {
	ctx := context.Background()

	var result C2LaunchResult
	err := c.httpClient.PostJSONResponse(ctx, "/c2/launch", req, &result)
	if err != nil {
		return nil, fmt.Errorf("launch C2 failed: %w", err)
	}

	return &result, nil
}

// ============================================================================
// SOCIAL ENGINEERING
// ============================================================================

func (c *OffensiveClient) LaunchSocialEngCampaign(req *SocialEngCampaignRequest) (*SocialEngCampaignResult, error) {
	ctx := context.Background()

	var result SocialEngCampaignResult
	err := c.httpClient.PostJSONResponse(ctx, "/social/campaign", req, &result)
	if err != nil {
		return nil, fmt.Errorf("launch social engineering campaign failed: %w", err)
	}

	return &result, nil
}

// ============================================================================
// MALWARE ANALYSIS
// ============================================================================

func (c *OffensiveClient) AnalyzeMalware(req *MalwareAnalyzeRequest) (*MalwareAnalyzeResult, error) {
	ctx := context.Background()

	var result MalwareAnalyzeResult
	err := c.httpClient.PostJSONResponse(ctx, "/malware/analyze", req, &result)
	if err != nil {
		return nil, fmt.Errorf("analyze malware failed: %w", err)
	}

	return &result, nil
}

// ============================================================================
// WARGAMING
// ============================================================================

func (c *OffensiveClient) StartWargame(req *WargameStartRequest) (*WargameStartResult, error) {
	ctx := context.Background()

	var result WargameStartResult
	err := c.httpClient.PostJSONResponse(ctx, "/wargame/start", req, &result)
	if err != nil {
		return nil, fmt.Errorf("start wargame failed: %w", err)
	}

	return &result, nil
}

// ============================================================================
// GATEWAY STATUS
// ============================================================================

func (c *OffensiveClient) GetGatewayStatus() (*GatewayStatus, error) {
	ctx := context.Background()

	var result GatewayStatus
	err := c.httpClient.GetJSON(ctx, "/gateway/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get gateway status failed: %w", err)
	}

	return &result, nil
}

// ============================================================================
// ORCHESTRATOR
// ============================================================================

func (c *OffensiveClient) ExecuteWorkflow(req *OrchestratorWorkflowRequest) (*OrchestratorWorkflowResult, error) {
	ctx := context.Background()

	var result OrchestratorWorkflowResult
	err := c.httpClient.PostJSONResponse(ctx, "/orchestrator/workflow", req, &result)
	if err != nil {
		return nil, fmt.Errorf("execute workflow failed: %w", err)
	}

	return &result, nil
}
