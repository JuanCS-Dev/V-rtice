package hcl

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// AnalyzerClient provides access to HCL Analyzer Service for system health analysis
type AnalyzerClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// AnomalyType represents the type of anomaly detected
type AnomalyType string

const (
	AnomalyTypeSpike   AnomalyType = "spike"
	AnomalyTypeDrop    AnomalyType = "drop"
	AnomalyTypeTrend   AnomalyType = "trend"
	AnomalyTypeOutlier AnomalyType = "outlier"
)

// Anomaly represents a detected anomaly in system metrics
type Anomaly struct {
	Type         AnomalyType `json:"type"`
	MetricName   string      `json:"metric_name"`
	CurrentValue float64     `json:"current_value"`
	Severity     float64     `json:"severity"`
	Description  string      `json:"description"`
}

// SystemMetrics represents a snapshot of system metrics
type SystemMetrics struct {
	Timestamp       string            `json:"timestamp"`
	CPUUsage        float64           `json:"cpu_usage"`
	MemoryUsage     float64           `json:"memory_usage"`
	DiskIORate      float64           `json:"disk_io_rate"`
	NetworkIORate   float64           `json:"network_io_rate"`
	AvgLatencyMs    float64           `json:"avg_latency_ms"`
	ErrorRate       float64           `json:"error_rate"`
	ServiceStatus   map[string]string `json:"service_status"`
}

// AnalysisResult represents the comprehensive analysis of system health
type AnalysisResult struct {
	Timestamp            string                 `json:"timestamp"`
	OverallHealthScore   float64                `json:"overall_health_score"`
	Anomalies            []Anomaly              `json:"anomalies"`
	Trends               map[string]interface{} `json:"trends"`
	Recommendations      []string               `json:"recommendations"`
	RequiresIntervention bool                   `json:"requires_intervention"`
}

// AnalyzeMetricsRequest represents a request to analyze system metrics
type AnalyzeMetricsRequest struct {
	CurrentMetrics SystemMetrics `json:"current_metrics"`
}

// AnalyzerHealthResponse represents health check response
type AnalyzerHealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// NewAnalyzerClient creates a new HCL Analyzer service client
func NewAnalyzerClient(endpoint, authToken string) *AnalyzerClient {
	return &AnalyzerClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		authToken: authToken,
	}
}

// AnalyzeMetrics submits system metrics for analysis to detect anomalies and assess health
//
// Parameters:
//   - metrics: Current system metrics snapshot
//
// Returns comprehensive analysis result with anomalies, trends, and recommendations
func (c *AnalyzerClient) AnalyzeMetrics(metrics SystemMetrics) (*AnalysisResult, error) {
	req := AnalyzeMetricsRequest{
		CurrentMetrics: metrics,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/analyze_metrics", c.baseURL), bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result AnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetAnalysisHistory retrieves a history of past analysis results
//
// Parameters:
//   - limit: Maximum number of historical results to retrieve
//
// Returns a list of past analysis results
func (c *AnalyzerClient) GetAnalysisHistory(limit int) ([]AnalysisResult, error) {
	url := fmt.Sprintf("%s/analysis_history?limit=%d", c.baseURL, limit)
	httpReq, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result []AnalysisResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// Health performs a health check on the HCL Analyzer service
//
// Returns the health status of the service
func (c *AnalyzerClient) Health() (*AnalyzerHealthResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/health", c.baseURL), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result AnalyzerHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
