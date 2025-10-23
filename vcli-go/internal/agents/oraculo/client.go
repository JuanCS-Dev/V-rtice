package oraculo

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Client represents an HTTP client for MAXIMUS Oraculo Service
type Client struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// NewClient creates a new Oraculo API client
func NewClient(baseURL, authToken string) *Client {
	return &Client{
		baseURL:   baseURL,
		authToken: authToken,
		httpClient: &http.Client{
			Timeout: 60 * time.Second, // AI code generation can take time
		},
	}
}

// ImplementationRequest represents a request to auto-implement code
type ImplementationRequest struct {
	TaskDescription string                 `json:"task_description"`
	Context         map[string]interface{} `json:"context,omitempty"`
	TargetLanguage  string                 `json:"target_language"`
}

// ImplementationResponse represents the response from auto-implement endpoint
type ImplementationResponse struct {
	Status    string    `json:"status"`
	Timestamp string    `json:"timestamp"`
	Result    ImplResult `json:"implementation_result"`
}

// ImplResult contains the generated code and implementation details
type ImplResult struct {
	GeneratedCode string        `json:"generated_code"`
	Details       ImplDetails   `json:"details"`
}

// ImplDetails contains metadata about the implementation
type ImplDetails struct {
	Status      string                 `json:"status"`
	Message     string                 `json:"message"`
	Language    string                 `json:"language"`
	ContextUsed map[string]interface{} `json:"context_used,omitempty"`
}

// AutoImplement requests code implementation from Oraculo
func (c *Client) AutoImplement(ctx context.Context, req ImplementationRequest) (*ImplementationResponse, error) {
	// Build request body
	reqBody, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	httpReq, err := http.NewRequestWithContext(
		ctx,
		http.MethodPost,
		fmt.Sprintf("%s/auto_implement", c.baseURL),
		bytes.NewReader(reqBody),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	httpReq.Header.Set("Content-Type", "application/json")
	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	// Execute request
	httpResp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer httpResp.Body.Close()

	// Read response body
	respBody, err := io.ReadAll(httpResp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Check status code
	if httpResp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("oraculo returned error status %d: %s", httpResp.StatusCode, string(respBody))
	}

	// Parse response
	var resp ImplementationResponse
	if err := json.Unmarshal(respBody, &resp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &resp, nil
}

// HealthCheck checks if Oraculo service is healthy
func (c *Client) HealthCheck(ctx context.Context) error {
	httpReq, err := http.NewRequestWithContext(
		ctx,
		http.MethodGet,
		fmt.Sprintf("%s/health", c.baseURL),
		nil,
	)
	if err != nil {
		return fmt.Errorf("failed to create health check request: %w", err)
	}

	httpResp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}
	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		return fmt.Errorf("health check returned status %d", httpResp.StatusCode)
	}

	return nil
}
