package maximus

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"github.com/verticedev/vcli-go/internal/debug"
)

// EurekaClient provides access to Maximus Eureka Service for insight generation
type EurekaClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// InsightRequest represents a request for insight generation
type InsightRequest struct {
	Data     map[string]interface{} `json:"data"`
	DataType string                 `json:"data_type"`
	Context  map[string]interface{} `json:"context,omitempty"`
}

// InsightResponse represents the response from insight generation
type InsightResponse struct {
	Status    string                 `json:"status"`
	Timestamp string                 `json:"timestamp"`
	Insights  map[string]interface{} `json:"insights"`
}

// PatternDetectionRequest represents a request for pattern detection
type PatternDetectionRequest struct {
	Data              map[string]interface{} `json:"data"`
	PatternDefinition map[string]interface{} `json:"pattern_definition"`
}

// PatternDetectionResponse represents the response from pattern detection
type PatternDetectionResponse struct {
	Status           string                   `json:"status"`
	Timestamp        string                   `json:"timestamp"`
	DetectedPatterns []map[string]interface{} `json:"detected_patterns"`
}

// IoCExtractionResponse represents the response from IoC extraction
type IoCExtractionResponse struct {
	Status        string                   `json:"status"`
	Timestamp     string                   `json:"timestamp"`
	ExtractedIoCs []map[string]interface{} `json:"extracted_iocs"`
}

// HealthResponse represents the health check response
type HealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// NewEurekaClient creates a new Eureka service client
func NewEurekaClient(endpoint, authToken string) *EurekaClient {
	source := "flag"
	if endpoint == "" {
		endpoint = os.Getenv("VCLI_EUREKA_ENDPOINT")
		if endpoint != "" {
			source = "env:VCLI_EUREKA_ENDPOINT"
		} else {
			endpoint = "http://localhost:8024"
			source = "default"
		}
	}

	debug.LogConnection("Eureka", endpoint, source)

	return &EurekaClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 60 * time.Second, // Insight generation can take time
		},
		authToken: authToken,
	}
}

// GenerateInsight generates novel insights from provided data
func (c *EurekaClient) GenerateInsight(data map[string]interface{}, dataType string, context map[string]interface{}) (*InsightResponse, error) {
	debug := os.Getenv("VCLI_DEBUG") == "true"
	if debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] Eureka GenerateInsight: connecting to %s\n", c.baseURL)
	}

	req := InsightRequest{
		Data:     data,
		DataType: dataType,
		Context:  context,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/generate_insight", c.baseURL), bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Eureka at %s: %w", c.baseURL, err)
	}
	defer resp.Body.Close()

	if debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] Eureka responded with status: %d\n", resp.StatusCode)
	}

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result InsightResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// DetectPattern detects specific patterns within provided data
func (c *EurekaClient) DetectPattern(data map[string]interface{}, patternDef map[string]interface{}) (*PatternDetectionResponse, error) {
	req := PatternDetectionRequest{
		Data:              data,
		PatternDefinition: patternDef,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/detect_pattern", c.baseURL), bytes.NewBuffer(body))
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

	var result PatternDetectionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// ExtractIoCs extracts Indicators of Compromise from provided data
func (c *EurekaClient) ExtractIoCs(data map[string]interface{}) (*IoCExtractionResponse, error) {
	body, err := json.Marshal(data)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/extract_iocs", c.baseURL), bytes.NewBuffer(body))
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

	var result IoCExtractionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Health performs a health check on the Eureka service
func (c *EurekaClient) Health() (*HealthResponse, error) {
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

	var result HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
