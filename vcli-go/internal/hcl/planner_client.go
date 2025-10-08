package hcl

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// PlannerClient provides access to HCL Planner Service for resource planning
type PlannerClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// PlanRequest represents a request to generate a resource alignment plan
type PlanRequest struct {
	AnalysisResult   map[string]interface{} `json:"analysis_result"`
	CurrentState     map[string]interface{} `json:"current_state"`
	OperationalGoals map[string]interface{} `json:"operational_goals"`
}

// PlanResponse represents the generated resource alignment plan
type PlanResponse struct {
	Timestamp       string                   `json:"timestamp"`
	PlanID          string                   `json:"plan_id"`
	Status          string                   `json:"status"`
	PlanDetails     string                   `json:"plan_details"`
	Actions         []map[string]interface{} `json:"actions"`
	EstimatedImpact map[string]interface{}   `json:"estimated_impact"`
}

// PlannerStatus represents the status of planning components
type PlannerStatus struct {
	Status                 string                 `json:"status"`
	FuzzyControllerStatus  map[string]interface{} `json:"fuzzy_controller_status"`
	RLAgentStatus          map[string]interface{} `json:"rl_agent_status"`
}

// PlannerHealthResponse represents health check response
type PlannerHealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// NewPlannerClient creates a new HCL Planner service client
func NewPlannerClient(endpoint, authToken string) *PlannerClient {
	return &PlannerClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		authToken: authToken,
	}
}

// GeneratePlan generates a resource alignment plan based on analysis results and operational goals
//
// Parameters:
//   - analysisResult: Analysis result from the HCL Analyzer Service
//   - currentState: Current system state
//   - operationalGoals: Operational goals (e.g., 'high_performance', 'cost_efficiency')
//
// Returns the generated resource plan with actions and estimated impact
func (c *PlannerClient) GeneratePlan(analysisResult, currentState, operationalGoals map[string]interface{}) (*PlanResponse, error) {
	req := PlanRequest{
		AnalysisResult:   analysisResult,
		CurrentState:     currentState,
		OperationalGoals: operationalGoals,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/generate_plan", c.baseURL), bytes.NewBuffer(body))
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

	var result PlanResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetPlannerStatus retrieves the current status of the HCL Planner Service
//
// Returns the status of planning components (fuzzy controller, RL agent)
func (c *PlannerClient) GetPlannerStatus() (*PlannerStatus, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/planner_status", c.baseURL), nil)
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

	var result PlannerStatus
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Health performs a health check on the HCL Planner service
//
// Returns the health status of the service
func (c *PlannerClient) Health() (*PlannerHealthResponse, error) {
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

	var result PlannerHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
