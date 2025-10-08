package hcl

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// ExecutorClient provides access to HCL Executor Service for plan execution
type ExecutorClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// ExecutePlanRequest represents a request to execute a resource alignment plan
type ExecutePlanRequest struct {
	PlanID   string                   `json:"plan_id"`
	Actions  []map[string]interface{} `json:"actions"`
	Priority int                      `json:"priority"`
}

// ExecutionResult represents the result of plan execution
type ExecutionResult struct {
	Timestamp     string                   `json:"timestamp"`
	PlanID        string                   `json:"plan_id"`
	Status        string                   `json:"status"`
	ActionResults []map[string]interface{} `json:"action_results"`
}

// K8sStatus represents Kubernetes cluster status
type K8sStatus struct {
	Nodes                int                    `json:"nodes,omitempty"`
	Pods                 int                    `json:"pods,omitempty"`
	Services             int                    `json:"services,omitempty"`
	ClusterHealth        string                 `json:"cluster_health,omitempty"`
	AdditionalInfo       map[string]interface{} `json:"additional_info,omitempty"`
}

// ExecutorHealthResponse represents health check response
type ExecutorHealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// NewExecutorClient creates a new HCL Executor service client
func NewExecutorClient(endpoint, authToken string) *ExecutorClient {
	return &ExecutorClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 120 * time.Second, // Plan execution can take time
		},
		authToken: authToken,
	}
}

// ExecutePlan receives and executes a resource alignment plan
//
// Parameters:
//   - planID: Unique identifier for the plan
//   - actions: List of actions to be executed
//   - priority: Priority of the plan execution (1-10, 10 being highest)
//
// Returns the execution results with status for each action
func (c *ExecutorClient) ExecutePlan(planID string, actions []map[string]interface{}, priority int) (*ExecutionResult, error) {
	req := ExecutePlanRequest{
		PlanID:   planID,
		Actions:  actions,
		Priority: priority,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/execute_plan", c.baseURL), bytes.NewBuffer(body))
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

	var result ExecutionResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetK8sStatus retrieves the current status of the Kubernetes cluster
//
// Returns the Kubernetes cluster status information
func (c *ExecutorClient) GetK8sStatus() (*K8sStatus, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/k8s_status", c.baseURL), nil)
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

	var result K8sStatus
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Health performs a health check on the HCL Executor service
//
// Returns the health status of the service
func (c *ExecutorClient) Health() (*ExecutorHealthResponse, error) {
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

	var result ExecutorHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
