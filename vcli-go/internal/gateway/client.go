package gateway

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

// GatewayClient provides a generic REST client for API Gateway
type GatewayClient struct {
	baseURL    string
	httpClient *http.Client
	token      string // JWT auth token
}

// NewGatewayClient creates a new API Gateway client
func NewGatewayClient(baseURL, token string) *GatewayClient {
	return &GatewayClient{
		baseURL: baseURL,
		token:   token,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
			},
		},
	}
}

// Query performs a GET request to a service endpoint
func (c *GatewayClient) Query(ctx context.Context, service, endpoint string, params map[string]string) (json.RawMessage, error) {
	// Build URL
	u, err := url.Parse(fmt.Sprintf("%s/%s%s", c.baseURL, service, endpoint))
	if err != nil {
		return nil, fmt.Errorf("invalid URL: %w", err)
	}

	// Add query parameters
	if len(params) > 0 {
		q := u.Query()
		for k, v := range params {
			q.Add(k, v)
		}
		u.RawQuery = q.Encode()
	}

	// Create request
	req, err := http.NewRequestWithContext(ctx, "GET", u.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add auth header
	if c.token != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.token))
	}
	req.Header.Set("Accept", "application/json")

	// Execute request
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Check status code
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(body))
	}

	return json.RawMessage(body), nil
}

// Post performs a POST request to a service endpoint
func (c *GatewayClient) Post(ctx context.Context, service, endpoint string, body interface{}) (json.RawMessage, error) {
	// Build URL
	u := fmt.Sprintf("%s/%s%s", c.baseURL, service, endpoint)

	// Marshal body
	var bodyReader io.Reader
	if body != nil {
		bodyBytes, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal body: %w", err)
		}
		bodyReader = bytes.NewReader(bodyBytes)
	}

	// Create request
	req, err := http.NewRequestWithContext(ctx, "POST", u, bodyReader)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add headers
	if c.token != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.token))
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	// Execute request
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Check status code
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(respBody))
	}

	return json.RawMessage(respBody), nil
}

// Put performs a PUT request to a service endpoint
func (c *GatewayClient) Put(ctx context.Context, service, endpoint string, body interface{}) (json.RawMessage, error) {
	// Build URL
	u := fmt.Sprintf("%s/%s%s", c.baseURL, service, endpoint)

	// Marshal body
	var bodyReader io.Reader
	if body != nil {
		bodyBytes, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal body: %w", err)
		}
		bodyReader = bytes.NewReader(bodyBytes)
	}

	// Create request
	req, err := http.NewRequestWithContext(ctx, "PUT", u, bodyReader)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add headers
	if c.token != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.token))
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	// Execute request
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// Check status code
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(respBody))
	}

	return json.RawMessage(respBody), nil
}

// Delete performs a DELETE request to a service endpoint
func (c *GatewayClient) Delete(ctx context.Context, service, endpoint string) error {
	// Build URL
	u := fmt.Sprintf("%s/%s%s", c.baseURL, service, endpoint)

	// Create request
	req, err := http.NewRequestWithContext(ctx, "DELETE", u, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	// Add auth header
	if c.token != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.token))
	}

	// Execute request
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read response for error details
	body, _ := io.ReadAll(resp.Body)

	// Check status code
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

// SetToken updates the JWT auth token
func (c *GatewayClient) SetToken(token string) {
	c.token = token
}

// SetTimeout updates the HTTP client timeout
func (c *GatewayClient) SetTimeout(timeout time.Duration) {
	c.httpClient.Timeout = timeout
}

// Close closes idle connections
func (c *GatewayClient) Close() {
	c.httpClient.CloseIdleConnections()
}

// ============================================================
// Service-Specific Helpers
// ============================================================

// EthicalAuditClient provides helpers for ethical audit service
type EthicalAuditClient struct {
	gateway *GatewayClient
}

// NewEthicalAuditClient creates a client for ethical audit service
func NewEthicalAuditClient(baseURL, token string) *EthicalAuditClient {
	return &EthicalAuditClient{
		gateway: NewGatewayClient(baseURL, token),
	}
}

// GetDecisions retrieves ethical decisions
func (c *EthicalAuditClient) GetDecisions(ctx context.Context, filters map[string]string) (json.RawMessage, error) {
	return c.gateway.Query(ctx, "ethical-audit", "/decisions", filters)
}

// AuditDecision audits a specific decision
func (c *EthicalAuditClient) AuditDecision(ctx context.Context, decisionID string, auditData interface{}) (json.RawMessage, error) {
	return c.gateway.Post(ctx, "ethical-audit", fmt.Sprintf("/decisions/%s/audit", decisionID), auditData)
}

// NarrativeFilterClient provides helpers for narrative manipulation filter
type NarrativeFilterClient struct {
	gateway *GatewayClient
}

// NewNarrativeFilterClient creates a client for narrative filter service
func NewNarrativeFilterClient(baseURL, token string) *NarrativeFilterClient {
	return &NarrativeFilterClient{
		gateway: NewGatewayClient(baseURL, token),
	}
}

// AnalyzeContent analyzes content for narrative manipulation
func (c *NarrativeFilterClient) AnalyzeContent(ctx context.Context, content interface{}) (json.RawMessage, error) {
	return c.gateway.Post(ctx, "narrative-filter", "/analyze", content)
}

// GetAnalysisHistory retrieves analysis history
func (c *NarrativeFilterClient) GetAnalysisHistory(ctx context.Context, filters map[string]string) (json.RawMessage, error) {
	return c.gateway.Query(ctx, "narrative-filter", "/history", filters)
}
