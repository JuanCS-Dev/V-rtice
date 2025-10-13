package narrative

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type NarrativeFilterClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// All types are now in types.go to avoid duplication

type SimpleHealthResponse struct {
	Status string `json:"status"`
}

type CacheStatsResponse struct {
	Success bool                   `json:"success"`
	Stats   map[string]interface{} `json:"stats"`
}

type DatabaseStatsResponse struct {
	Success     bool           `json:"success"`
	TableCounts map[string]int `json:"table_counts"`
}

type ServiceInfoResponse struct {
	Service     string                 `json:"service"`
	Version     string                 `json:"version"`
	Environment string                 `json:"environment"`
	Config      map[string]interface{} `json:"config"`
}

func NewNarrativeFilterClient(endpoint, authToken string) *NarrativeFilterClient {
	return &NarrativeFilterClient{
		baseURL:    endpoint,
		httpClient: &http.Client{Timeout: 90 * time.Second},
		authToken:  authToken,
	}
}

func (c *NarrativeFilterClient) AnalyzeContent(req AnalysisRequest) (*AnalysisResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal analysis request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/api/analyze", c.baseURL), bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result AnalysisResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *NarrativeFilterClient) Health() (*HealthCheckResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/health", c.baseURL), nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result HealthCheckResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *NarrativeFilterClient) SimpleHealth() (*SimpleHealthResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/health/simple", c.baseURL), nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result SimpleHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *NarrativeFilterClient) GetCacheStats() (*CacheStatsResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/stats/cache", c.baseURL), nil)
	if err != nil {
		return nil, err
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result CacheStatsResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *NarrativeFilterClient) GetDatabaseStats() (*DatabaseStatsResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/stats/database", c.baseURL), nil)
	if err != nil {
		return nil, err
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result DatabaseStatsResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *NarrativeFilterClient) GetServiceInfo() (*ServiceInfoResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/info", c.baseURL), nil)
	if err != nil {
		return nil, err
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result ServiceInfoResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}
