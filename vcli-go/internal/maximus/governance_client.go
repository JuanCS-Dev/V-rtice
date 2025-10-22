package maximus

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/internal/debug"
)

// GovernanceClient handles communication with MAXIMUS Core Governance API
type GovernanceClient struct {
	baseURL    string
	httpClient *http.Client
}

// NewGovernanceClient creates a new governance API client
func NewGovernanceClient(baseURL string) *GovernanceClient {
	source := "flag"
	if baseURL == "" {
		baseURL = os.Getenv("VCLI_MAXIMUS_ENDPOINT")
		if baseURL != "" {
			source = "env:VCLI_MAXIMUS_ENDPOINT"
		} else {
			baseURL = "http://localhost:8150"
			source = "default"
		}
	}

	debug.LogConnection("MAXIMUS Governance", baseURL, source)

	return &GovernanceClient{
		baseURL: strings.TrimSuffix(baseURL, "/"),
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// ==================== RESPONSE TYPES ====================

// GovernanceHealthResponse represents governance health check response
type GovernanceHealthResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
	Version   string `json:"version,omitempty"`
}

// PendingStatsResponse represents pending decisions statistics
type PendingStatsResponse struct {
	TotalPending      int                `json:"total_pending"`
	ByCategory        map[string]int     `json:"by_category"`
	BySeverity        map[string]int     `json:"by_severity"`
	OldestDecisionAge float64            `json:"oldest_decision_age_seconds,omitempty"`
	Metadata          map[string]interface{} `json:"metadata,omitempty"`
}

// SessionCreateRequest represents session creation request
type SessionCreateRequest struct {
	OperatorID   string                 `json:"operator_id"`
	OperatorName string                 `json:"operator_name,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// SessionCreateResponse represents session creation response
type SessionCreateResponse struct {
	SessionID  string    `json:"session_id"`
	OperatorID string    `json:"operator_id"`
	CreatedAt  time.Time `json:"created_at"`
	ExpiresAt  time.Time `json:"expires_at,omitempty"`
}

// OperatorStatsResponse represents operator statistics
type OperatorStatsResponse struct {
	OperatorID      string             `json:"operator_id"`
	TotalDecisions  int                `json:"total_decisions"`
	Approved        int                `json:"approved"`
	Rejected        int                `json:"rejected"`
	Escalated       int                `json:"escalated"`
	AvgResponseTime float64            `json:"avg_response_time_seconds,omitempty"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

// DecisionActionResponse represents decision action result
type DecisionActionResponse struct {
	Success       bool                   `json:"success"`
	DecisionID    string                 `json:"decision_id"`
	Action        string                 `json:"action"`
	Timestamp     string                 `json:"timestamp"`
	Message       string                 `json:"message,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// ==================== REQUEST TYPES ====================

// ApproveDecisionRequest represents decision approval request
type ApproveDecisionRequest struct {
	SessionID  string  `json:"session_id"`
	Reasoning  *string `json:"reasoning,omitempty"`
	Comment    *string `json:"comment,omitempty"`
}

// RejectDecisionRequest represents decision rejection request
type RejectDecisionRequest struct {
	SessionID  string  `json:"session_id"`
	Reasoning  *string `json:"reasoning,omitempty"`
	Comment    *string `json:"comment,omitempty"`
}

// EscalateDecisionRequest represents decision escalation request
type EscalateDecisionRequest struct {
	SessionID  string  `json:"session_id"`
	Reasoning  string  `json:"reasoning"`
	Comment    *string `json:"comment,omitempty"`
	ToLevel    *string `json:"to_level,omitempty"`
}

// TestDecisionRequest represents test decision for E2E testing
type TestDecisionRequest struct {
	DecisionID   string                 `json:"decision_id"`
	Category     string                 `json:"category"`
	Severity     string                 `json:"severity"`
	Description  string                 `json:"description"`
	Context      map[string]interface{} `json:"context,omitempty"`
	RequiresHITL bool                   `json:"requires_hitl"`
}

// ==================== API METHODS ====================

// Health checks if the governance API is reachable
func (c *GovernanceClient) Health() (*GovernanceHealthResponse, error) {
	url := fmt.Sprintf("%s/api/v1/governance/health", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to governance API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var health GovernanceHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &health, nil
}

// GetPendingStats retrieves statistics about pending decisions
func (c *GovernanceClient) GetPendingStats() (*PendingStatsResponse, error) {
	url := fmt.Sprintf("%s/api/v1/governance/pending", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to governance API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var stats PendingStatsResponse
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &stats, nil
}

// CreateSession creates a new operator session
func (c *GovernanceClient) CreateSession(req SessionCreateRequest) (*SessionCreateResponse, error) {
	url := fmt.Sprintf("%s/api/v1/governance/session/create", c.baseURL)

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to governance API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var session SessionCreateResponse
	if err := json.NewDecoder(resp.Body).Decode(&session); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &session, nil
}

// GetOperatorStats retrieves operator statistics
func (c *GovernanceClient) GetOperatorStats(operatorID string) (*OperatorStatsResponse, error) {
	url := fmt.Sprintf("%s/api/v1/governance/session/%s/stats", c.baseURL, operatorID)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to governance API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var stats OperatorStatsResponse
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &stats, nil
}

// ApproveDecision approves a pending decision
func (c *GovernanceClient) ApproveDecision(decisionID string, req ApproveDecisionRequest) (*DecisionActionResponse, error) {
	url := fmt.Sprintf("%s/api/v1/governance/decision/%s/approve", c.baseURL, decisionID)

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to governance API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var result DecisionActionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// RejectDecision rejects a pending decision
func (c *GovernanceClient) RejectDecision(decisionID string, req RejectDecisionRequest) (*DecisionActionResponse, error) {
	url := fmt.Sprintf("%s/api/v1/governance/decision/%s/reject", c.baseURL, decisionID)

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to governance API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var result DecisionActionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// EscalateDecision escalates a pending decision to higher authority
func (c *GovernanceClient) EscalateDecision(decisionID string, req EscalateDecisionRequest) (*DecisionActionResponse, error) {
	url := fmt.Sprintf("%s/api/v1/governance/decision/%s/escalate", c.baseURL, decisionID)

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to governance API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var result DecisionActionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// EnqueueTestDecision enqueues a test decision (for E2E testing only)
func (c *GovernanceClient) EnqueueTestDecision(decision map[string]interface{}) error {
	url := fmt.Sprintf("%s/api/v1/governance/test/enqueue", c.baseURL)

	body, err := json.Marshal(decision)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to connect to governance API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	return nil
}
