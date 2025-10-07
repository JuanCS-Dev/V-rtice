package governance

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// HTTPClient provides HTTP interface to Governance backend
type HTTPClient struct {
	baseURL    string
	client     *http.Client
	operatorID string
	sessionID  string
}

// NewHTTPClient creates a new HTTP client for Governance API
func NewHTTPClient(baseURL, operatorID string) *HTTPClient {
	return &HTTPClient{
		baseURL:    baseURL,
		operatorID: operatorID,
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// SetSessionID sets the active session ID for authenticated requests
func (c *HTTPClient) SetSessionID(sessionID string) {
	c.sessionID = sessionID
}

// ApproveDecision approves a pending decision
func (c *HTTPClient) ApproveDecision(ctx context.Context, decisionID, comment string) error {
	url := fmt.Sprintf("%s/api/v1/governance/decision/%s/approve", c.baseURL, decisionID)

	request := struct {
		SessionID string `json:"session_id"`
		Comment   string `json:"comment,omitempty"`
		Reasoning string `json:"reasoning,omitempty"`
	}{
		SessionID: c.sessionID,
		Comment:   comment,
	}

	body, err := json.Marshal(request)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Operator-ID", c.operatorID)

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("approval failed with status %d: %s", resp.StatusCode, string(respBody))
	}

	return nil
}

// RejectDecision rejects a pending decision
func (c *HTTPClient) RejectDecision(ctx context.Context, decisionID, reason string) error {
	url := fmt.Sprintf("%s/api/v1/governance/decision/%s/reject", c.baseURL, decisionID)

	request := struct {
		SessionID string `json:"session_id"`
		Reason    string `json:"reason"` // Required field
		Comment   string `json:"comment,omitempty"`
		Reasoning string `json:"reasoning,omitempty"`
	}{
		SessionID: c.sessionID,
		Reason:    reason,
		Comment:   reason, // Also set comment for compatibility
	}

	body, err := json.Marshal(request)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Operator-ID", c.operatorID)

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("rejection failed with status %d: %s", resp.StatusCode, string(respBody))
	}

	return nil
}

// EscalateDecision escalates a decision to senior operator
func (c *HTTPClient) EscalateDecision(ctx context.Context, decisionID, reason string) error {
	url := fmt.Sprintf("%s/api/v1/governance/decision/%s/escalate", c.baseURL, decisionID)

	request := struct {
		SessionID        string `json:"session_id"`
		EscalationReason string `json:"escalation_reason,omitempty"`
		Comment          string `json:"comment,omitempty"`
	}{
		SessionID:        c.sessionID,
		EscalationReason: reason,
	}

	body, err := json.Marshal(request)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Operator-ID", c.operatorID)

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusAccepted {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("escalation failed with status %d: %s", resp.StatusCode, string(respBody))
	}

	return nil
}

// GetDecision retrieves a specific decision by ID
func (c *HTTPClient) GetDecision(ctx context.Context, decisionID string) (*Decision, error) {
	url := fmt.Sprintf("%s/governance/decisions/%s", c.baseURL, decisionID)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("X-Operator-ID", c.operatorID)

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("unexpected status %d: %s", resp.StatusCode, string(body))
	}

	var decision Decision
	if err := json.NewDecoder(resp.Body).Decode(&decision); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &decision, nil
}

// ListDecisions lists pending decisions with optional filtering
func (c *HTTPClient) ListDecisions(ctx context.Context, filter *DecisionFilter) ([]*Decision, error) {
	url := fmt.Sprintf("%s/governance/decisions", c.baseURL)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("X-Operator-ID", c.operatorID)

	// Add query parameters from filter
	if filter != nil {
		q := req.URL.Query()

		if len(filter.Status) > 0 {
			for _, status := range filter.Status {
				q.Add("status", string(status))
			}
		}

		if len(filter.RiskLevel) > 0 {
			for _, risk := range filter.RiskLevel {
				q.Add("risk_level", string(risk))
			}
		}

		if filter.Limit > 0 {
			q.Set("limit", fmt.Sprintf("%d", filter.Limit))
		}

		if filter.Offset > 0 {
			q.Set("offset", fmt.Sprintf("%d", filter.Offset))
		}

		req.URL.RawQuery = q.Encode()
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("unexpected status %d: %s", resp.StatusCode, string(body))
	}

	var response struct {
		Decisions []*Decision `json:"decisions"`
		Total     int         `json:"total"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return response.Decisions, nil
}

// GetMetrics retrieves current decision queue metrics (session stats)
func (c *HTTPClient) GetMetrics(ctx context.Context) (*DecisionMetrics, error) {
	// Backend uses session stats endpoint for metrics
	url := fmt.Sprintf("%s/api/v1/governance/session/%s/stats", c.baseURL, c.operatorID)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("X-Operator-ID", c.operatorID)

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("unexpected status %d: %s", resp.StatusCode, string(body))
	}

	// Backend returns SessionStats, which we'll convert to DecisionMetrics
	var stats SessionStats
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Convert SessionStats to DecisionMetrics
	metrics := &DecisionMetrics{
		TotalApproved:   stats.Approved,
		TotalRejected:   stats.Rejected,
		TotalEscalated:  stats.Escalated,
		AvgResponseTime: stats.AvgResponseTime,
		Timestamp:       time.Now(),
	}

	return metrics, nil
}

// GetSessionStats retrieves detailed session statistics
func (c *HTTPClient) GetSessionStats(ctx context.Context) (*SessionStats, error) {
	url := fmt.Sprintf("%s/api/v1/governance/session/%s/stats", c.baseURL, c.operatorID)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("X-Operator-ID", c.operatorID)

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("unexpected status %d: %s", resp.StatusCode, string(body))
	}

	var stats SessionStats
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &stats, nil
}

// CreateSession creates a new operator session
func (c *HTTPClient) CreateSession(ctx context.Context, operatorName, operatorRole string) (*Session, error) {
	url := fmt.Sprintf("%s/api/v1/governance/session/create", c.baseURL)

	request := SessionCreateRequest{
		OperatorID:   c.operatorID,
		OperatorName: operatorName,
		OperatorRole: operatorRole,
	}

	body, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("session creation failed with status %d: %s", resp.StatusCode, string(respBody))
	}

	var session Session
	if err := json.NewDecoder(resp.Body).Decode(&session); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Store session ID for future requests
	c.sessionID = session.SessionID

	return &session, nil
}

// HealthCheck checks backend health status
func (c *HTTPClient) HealthCheck(ctx context.Context) (bool, error) {
	url := fmt.Sprintf("%s/api/v1/governance/health", c.baseURL)

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return false, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return false, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	return resp.StatusCode == http.StatusOK, nil
}

// PingServer sends a ping to verify backend connectivity
func (c *HTTPClient) PingServer(ctx context.Context) (time.Duration, error) {
	start := time.Now()

	healthy, err := c.HealthCheck(ctx)
	if err != nil {
		return 0, err
	}

	if !healthy {
		return 0, fmt.Errorf("backend unhealthy")
	}

	return time.Since(start), nil
}
