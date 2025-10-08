package immunis

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// BCellClient provides access to Immunis B-Cell Service for antibody generation
type BCellClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// ProcessRequest represents a generic processing request
type ProcessRequest struct {
	Data    map[string]interface{} `json:"data"`
	Context map[string]interface{} `json:"context,omitempty"`
}

// ProcessResponse represents a generic processing response
type ProcessResponse struct {
	Status    string                 `json:"status"`
	Service   string                 `json:"service"`
	Results   map[string]interface{} `json:"results"`
	Timestamp string                 `json:"timestamp"`
}

// BCellHealthResponse represents health check response
type BCellHealthResponse struct {
	Status        string `json:"status"`
	Service       string `json:"service"`
	CoreAvailable bool   `json:"core_available"`
	Timestamp     string `json:"timestamp"`
}

// BCellStatusResponse represents status response
type BCellStatusResponse struct {
	Status    string `json:"status"`
	Service   string `json:"service"`
	Mode      string `json:"mode"`
	Timestamp string `json:"timestamp"`
}

// NewBCellClient creates a new B-Cell service client
func NewBCellClient(endpoint, authToken string) *BCellClient {
	return &BCellClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		authToken: authToken,
	}
}

// Process sends data for B-Cell processing (antibody generation)
func (c *BCellClient) Process(data, context map[string]interface{}) (*ProcessResponse, error) {
	req := ProcessRequest{
		Data:    data,
		Context: context,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/process", c.baseURL), bytes.NewBuffer(body))
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

	var result ProcessResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Health performs health check
func (c *BCellClient) Health() (*BCellHealthResponse, error) {
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

	var result BCellHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetStatus retrieves detailed service status
func (c *BCellClient) GetStatus() (*BCellStatusResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/status", c.baseURL), nil)
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

	var result BCellStatusResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
