package narrative

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// NarrativeClient handles communication with Narrative Manipulation Filter API
type NarrativeClient struct {
	baseURL    string
	httpClient *http.Client
}

// NewNarrativeClient creates a new narrative filter API client
func NewNarrativeClient(baseURL string) *NarrativeClient {
	if baseURL == "" {
		baseURL = "http://localhost:8030"
	}

	return &NarrativeClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second, // Longer timeout for analysis
		},
	}
}

// ==================== RESPONSE TYPES ====================
// All types moved to types.go to avoid duplication

// CacheStats from /stats/cache
type CacheStats struct {
	Success bool                   `json:"success"`
	Stats   map[string]interface{} `json:"stats"`
}

// DatabaseStats from /stats/database
type DatabaseStats struct {
	Success     bool           `json:"success"`
	TableCounts map[string]int `json:"table_counts"`
}

// ServiceInfo from /info
type ServiceInfo struct {
	Service     string                 `json:"service"`
	Version     string                 `json:"version"`
	Environment string                 `json:"environment"`
	Config      map[string]interface{} `json:"config"`
}

// ==================== REQUEST TYPES ====================
// Moved to types.go

// ==================== API METHODS ====================

// Analyze analyzes text for narrative manipulation
func (c *NarrativeClient) Analyze(text string, sourceURL *string) (*CognitiveDefenseReport, error) {
	url := fmt.Sprintf("%s/api/analyze", c.baseURL)

	request := AnalysisRequest{
		Text:      text,
		SourceURL: sourceURL,
	}

	body, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to narrative API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var analysisResp AnalysisResponse
	if err := json.NewDecoder(resp.Body).Decode(&analysisResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !analysisResp.Success {
		errMsg := "unknown error"
		if analysisResp.Error != nil {
			errMsg = *analysisResp.Error
		}
		return nil, fmt.Errorf("analysis failed: %s", errMsg)
	}

	if analysisResp.Report == nil {
		return nil, fmt.Errorf("no report in response")
	}

	return analysisResp.Report, nil
}

// Health checks service health
func (c *NarrativeClient) Health() (*HealthCheckResponse, error) {
	url := fmt.Sprintf("%s/health", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("narrative API unreachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("narrative API unhealthy (status %d)", resp.StatusCode)
	}

	var health HealthCheckResponse
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		return nil, fmt.Errorf("failed to decode health response: %w", err)
	}

	return &health, nil
}

// GetCacheStats retrieves cache statistics
func (c *NarrativeClient) GetCacheStats() (*CacheStats, error) {
	url := fmt.Sprintf("%s/stats/cache", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to narrative API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var stats CacheStats
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &stats, nil
}

// GetDatabaseStats retrieves database statistics
func (c *NarrativeClient) GetDatabaseStats() (*DatabaseStats, error) {
	url := fmt.Sprintf("%s/stats/database", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to narrative API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var stats DatabaseStats
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &stats, nil
}

// GetServiceInfo retrieves service information
func (c *NarrativeClient) GetServiceInfo() (*ServiceInfo, error) {
	url := fmt.Sprintf("%s/info", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to narrative API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var info ServiceInfo
	if err := json.NewDecoder(resp.Body).Decode(&info); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &info, nil
}
