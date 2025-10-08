package immunis

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// CytotoxicTClient provides access to Immunis Cytotoxic T-Cell Service for threat elimination
type CytotoxicTClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// CytotoxicTHealthResponse represents health check response
type CytotoxicTHealthResponse struct {
	Status        string `json:"status"`
	Service       string `json:"service"`
	CoreAvailable bool   `json:"core_available"`
	Timestamp     string `json:"timestamp"`
}

// CytotoxicTStatusResponse represents status response
type CytotoxicTStatusResponse struct {
	Status    string `json:"status"`
	Service   string `json:"service"`
	Mode      string `json:"mode"`
	Timestamp string `json:"timestamp"`
}

// NewCytotoxicTClient creates a new Cytotoxic T-Cell service client
func NewCytotoxicTClient(endpoint, authToken string) *CytotoxicTClient {
	return &CytotoxicTClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		authToken: authToken,
	}
}

// Process sends data for Cytotoxic T-Cell processing (threat elimination)
func (c *CytotoxicTClient) Process(data, context map[string]interface{}) (*ProcessResponse, error) {
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
func (c *CytotoxicTClient) Health() (*CytotoxicTHealthResponse, error) {
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

	var result CytotoxicTHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetStatus retrieves detailed service status
func (c *CytotoxicTClient) GetStatus() (*CytotoxicTStatusResponse, error) {
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

	var result CytotoxicTStatusResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
