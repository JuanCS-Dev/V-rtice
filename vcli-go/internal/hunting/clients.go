package hunting

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

type HuntingClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewHuntingClient(endpoint string) *HuntingClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("hunting")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &HuntingClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *HuntingClient) PredictAPT(req *APTPredictRequest) (*APTPredictResult, error) {
	ctx := context.Background()

	var result APTPredictResult
	err := c.httpClient.PostJSONResponse(ctx, "/apt/predict", req, &result)
	if err != nil {
		return nil, fmt.Errorf("predict APT failed: %w", err)
	}

	return &result, nil
}

func (c *HuntingClient) ProfileAPT(req *APTProfileRequest) (*APTProfileResult, error) {
	ctx := context.Background()

	var result APTProfileResult
	err := c.httpClient.PostJSONResponse(ctx, "/apt/profile", req, &result)
	if err != nil {
		return nil, fmt.Errorf("profile APT failed: %w", err)
	}

	return &result, nil
}

func (c *HuntingClient) StartHunt(req *HuntStartRequest) (*HuntStartResult, error) {
	ctx := context.Background()

	var result HuntStartResult
	err := c.httpClient.PostJSONResponse(ctx, "/hunt/start", req, &result)
	if err != nil {
		return nil, fmt.Errorf("start hunt failed: %w", err)
	}

	return &result, nil
}

func (c *HuntingClient) GetHuntResults(huntID string) (*HuntResultsResult, error) {
	ctx := context.Background()

	var result HuntResultsResult
	err := c.httpClient.GetJSON(ctx, fmt.Sprintf("/hunt/results/%s", huntID), &result)
	if err != nil {
		return nil, fmt.Errorf("get hunt results failed: %w", err)
	}

	return &result, nil
}

func (c *HuntingClient) PredictAnomaly(req *AnomalyPredictRequest) (*AnomalyPredictResult, error) {
	ctx := context.Background()

	var result AnomalyPredictResult
	err := c.httpClient.PostJSONResponse(ctx, "/predict/anomaly", req, &result)
	if err != nil {
		return nil, fmt.Errorf("predict anomaly failed: %w", err)
	}

	return &result, nil
}

func (c *HuntingClient) AnalyzeSurface(req *SurfaceAnalyzeRequest) (*SurfaceAnalyzeResult, error) {
	ctx := context.Background()

	var result SurfaceAnalyzeResult
	err := c.httpClient.PostJSONResponse(ctx, "/surface/analyze", req, &result)
	if err != nil {
		return nil, fmt.Errorf("analyze surface failed: %w", err)
	}

	return &result, nil
}

func (c *HuntingClient) MapSurface(req *SurfaceMapRequest) (*SurfaceMapResult, error) {
	ctx := context.Background()

	var result SurfaceMapResult
	err := c.httpClient.PostJSONResponse(ctx, "/surface/map", req, &result)
	if err != nil {
		return nil, fmt.Errorf("map surface failed: %w", err)
	}

	return &result, nil
}
