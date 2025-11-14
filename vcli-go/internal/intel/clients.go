package intel

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

type IntelClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewIntelClient(endpoint string) *IntelClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("intel")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &IntelClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *IntelClient) SearchGoogle(req *GoogleSearchRequest) (*GoogleSearchResult, error) {
	ctx := context.Background()

	var result GoogleSearchResult
	err := c.httpClient.PostJSONResponse(ctx, "/google/search", req, &result)
	if err != nil {
		return nil, fmt.Errorf("google search failed: %w", err)
	}

	return &result, nil
}

func (c *IntelClient) GoogleDork(req *GoogleDorkRequest) (*GoogleDorkResult, error) {
	ctx := context.Background()

	var result GoogleDorkResult
	err := c.httpClient.PostJSONResponse(ctx, "/google/dork", req, &result)
	if err != nil {
		return nil, fmt.Errorf("google dork failed: %w", err)
	}

	return &result, nil
}

func (c *IntelClient) LookupIP(req *IPLookupRequest) (*IPLookupResult, error) {
	ctx := context.Background()

	var result IPLookupResult
	err := c.httpClient.PostJSONResponse(ctx, "/ip/lookup", req, &result)
	if err != nil {
		return nil, fmt.Errorf("ip lookup failed: %w", err)
	}

	return &result, nil
}

func (c *IntelClient) GeolocationIP(req *IPGeoRequest) (*IPGeoResult, error) {
	ctx := context.Background()

	var result IPGeoResult
	err := c.httpClient.PostJSONResponse(ctx, "/ip/geo", req, &result)
	if err != nil {
		return nil, fmt.Errorf("ip geolocation failed: %w", err)
	}

	return &result, nil
}

func (c *IntelClient) SinespPlate(req *SinespPlateRequest) (*SinespPlateResult, error) {
	ctx := context.Background()

	var result SinespPlateResult
	err := c.httpClient.PostJSONResponse(ctx, "/sinesp/plate", req, &result)
	if err != nil {
		return nil, fmt.Errorf("sinesp plate lookup failed: %w", err)
	}

	return &result, nil
}

func (c *IntelClient) SinespDocument(req *SinespDocumentRequest) (*SinespDocumentResult, error) {
	ctx := context.Background()

	var result SinespDocumentResult
	err := c.httpClient.PostJSONResponse(ctx, "/sinesp/document", req, &result)
	if err != nil {
		return nil, fmt.Errorf("sinesp document lookup failed: %w", err)
	}

	return &result, nil
}

func (c *IntelClient) CheckSSL(req *SSLCheckRequest) (*SSLCheckResult, error) {
	ctx := context.Background()

	var result SSLCheckResult
	err := c.httpClient.PostJSONResponse(ctx, "/ssl/check", req, &result)
	if err != nil {
		return nil, fmt.Errorf("ssl check failed: %w", err)
	}

	return &result, nil
}

func (c *IntelClient) MonitorSSL(req *SSLMonitorRequest) (*SSLMonitorResult, error) {
	ctx := context.Background()

	var result SSLMonitorResult
	err := c.httpClient.PostJSONResponse(ctx, "/ssl/monitor", req, &result)
	if err != nil {
		return nil, fmt.Errorf("ssl monitor failed: %w", err)
	}

	return &result, nil
}

func (c *IntelClient) AnalyzeNarrative(req *NarrativeAnalyzeRequest) (*NarrativeAnalyzeResult, error) {
	ctx := context.Background()

	var result NarrativeAnalyzeResult
	err := c.httpClient.PostJSONResponse(ctx, "/narrative/analyze", req, &result)
	if err != nil {
		return nil, fmt.Errorf("narrative analysis failed: %w", err)
	}

	return &result, nil
}

func (c *IntelClient) DetectNarrative(req *NarrativeDetectRequest) (*NarrativeDetectResult, error) {
	ctx := context.Background()

	var result NarrativeDetectResult
	err := c.httpClient.PostJSONResponse(ctx, "/narrative/detect", req, &result)
	if err != nil {
		return nil, fmt.Errorf("narrative detection failed: %w", err)
	}

	return &result, nil
}
