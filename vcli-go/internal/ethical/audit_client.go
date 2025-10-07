package ethical

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// AuditClient provides access to Ethical Audit Service for ethical decision logging and analytics
type AuditClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// EthicalDecisionLog represents an ethical decision to be logged
type EthicalDecisionLog struct {
	DecisionID       string                 `json:"decision_id"`
	RequestID        string                 `json:"request_id"`
	ServiceName      string                 `json:"service_name"`
	DecisionType     string                 `json:"decision_type"`
	Context          map[string]interface{} `json:"context"`
	KantianResult    map[string]interface{} `json:"kantian_result"`
	ConsequentialistResult map[string]interface{} `json:"consequentialist_result"`
	VirtueResult     map[string]interface{} `json:"virtue_result"`
	PrinciplismResult map[string]interface{} `json:"principialism_result"`
	FinalDecision    map[string]interface{} `json:"final_decision"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

// DecisionHistoryQuery represents a query for decision history
type DecisionHistoryQuery struct {
	StartTime    string                 `json:"start_time,omitempty"`
	EndTime      string                 `json:"end_time,omitempty"`
	DecisionType string                 `json:"decision_type,omitempty"`
	ServiceName  string                 `json:"service_name,omitempty"`
	RiskLevel    string                 `json:"risk_level,omitempty"`
	Limit        int                    `json:"limit,omitempty"`
	Offset       int                    `json:"offset,omitempty"`
	Filters      map[string]interface{} `json:"filters,omitempty"`
}

// DecisionHistoryResponse represents the response from decision history query
type DecisionHistoryResponse struct {
	Total     int                      `json:"total"`
	Decisions []map[string]interface{} `json:"decisions"`
	Offset    int                      `json:"offset"`
	Limit     int                      `json:"limit"`
}

// HumanOverrideRequest represents a human override of an AI decision
type HumanOverrideRequest struct {
	DecisionID       string                 `json:"decision_id"`
	OverrideReason   string                 `json:"override_reason"`
	OverrideDecision map[string]interface{} `json:"override_decision"`
	Operator         string                 `json:"operator"`
	Justification    string                 `json:"justification,omitempty"`
}

// EthicalMetrics represents overall ethical metrics
type EthicalMetrics struct {
	TotalDecisions     int                      `json:"total_decisions"`
	DecisionsByType    map[string]int           `json:"decisions_by_type"`
	HighRiskCount      int                      `json:"high_risk_count"`
	OverrideRate       float64                  `json:"override_rate"`
	ComplianceRate     float64                  `json:"compliance_rate"`
	AverageDecisionTime float64                 `json:"average_decision_time"`
	Timestamp          string                   `json:"timestamp"`
	AdditionalMetrics  map[string]interface{}   `json:"additional_metrics,omitempty"`
}

// FrameworkPerformance represents performance metrics for ethical frameworks
type FrameworkPerformance struct {
	Framework         string  `json:"framework"`
	TotalEvaluations  int     `json:"total_evaluations"`
	ApprovalRate      float64 `json:"approval_rate"`
	AverageConfidence float64 `json:"average_confidence"`
	AverageLatency    float64 `json:"average_latency"`
}

// AuditHealthResponse represents health check response
type AuditHealthResponse struct {
	Status    string `json:"status"`
	Service   string `json:"service"`
	Timestamp string `json:"timestamp"`
	Database  string `json:"database"`
}

// AuditStatusResponse represents detailed status response
type AuditStatusResponse struct {
	Service   string                 `json:"service"`
	Status    string                 `json:"status"`
	Database  map[string]interface{} `json:"database"`
	Timestamp string                 `json:"timestamp"`
}

// NewAuditClient creates a new Ethical Audit service client
func NewAuditClient(endpoint, authToken string) *AuditClient {
	return &AuditClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		authToken: authToken,
	}
}

// LogDecision logs an ethical decision for audit purposes
//
// Parameters:
//   - decisionLog: Complete ethical decision log with all framework results
//
// Returns the logged decision with audit ID
func (c *AuditClient) LogDecision(decisionLog EthicalDecisionLog) (map[string]interface{}, error) {
	body, err := json.Marshal(decisionLog)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/audit/decision", c.baseURL), bytes.NewBuffer(body))
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

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// GetDecision retrieves a specific ethical decision by ID
//
// Parameters:
//   - decisionID: The ID of the decision to retrieve
//
// Returns the complete decision record
func (c *AuditClient) GetDecision(decisionID string) (map[string]interface{}, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/audit/decision/%s", c.baseURL, decisionID), nil)
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

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// QueryDecisions queries decision history with filtering and pagination
//
// Parameters:
//   - query: Query parameters for filtering decisions
//
// Returns paginated decision history
func (c *AuditClient) QueryDecisions(query DecisionHistoryQuery) (*DecisionHistoryResponse, error) {
	body, err := json.Marshal(query)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/audit/decisions/query", c.baseURL), bytes.NewBuffer(body))
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

	var result DecisionHistoryResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// LogOverride logs a human override of an AI ethical decision
//
// Parameters:
//   - override: Human override request with justification
//
// Returns the logged override record
func (c *AuditClient) LogOverride(override HumanOverrideRequest) (map[string]interface{}, error) {
	body, err := json.Marshal(override)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/audit/override", c.baseURL), bytes.NewBuffer(body))
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

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// GetMetrics retrieves overall ethical metrics
//
// Returns comprehensive ethical decision metrics
func (c *AuditClient) GetMetrics() (*EthicalMetrics, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/audit/metrics", c.baseURL), nil)
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

	var result EthicalMetrics
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetFrameworkMetrics retrieves performance metrics for each ethical framework
//
// Returns performance metrics for all frameworks
func (c *AuditClient) GetFrameworkMetrics() ([]FrameworkPerformance, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/audit/metrics/frameworks", c.baseURL), nil)
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

	var result []FrameworkPerformance
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// Health performs a health check on the Ethical Audit service
//
// Returns the health status of the service
func (c *AuditClient) Health() (*AuditHealthResponse, error) {
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

	var result AuditHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetStatus retrieves detailed service status with database stats
//
// Returns detailed status information
func (c *AuditClient) GetStatus() (*AuditStatusResponse, error) {
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

	var result AuditStatusResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
