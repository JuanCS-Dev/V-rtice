package investigation

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// ReconClient provides access to Network Reconnaissance Service for active network scanning
type ReconClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// ReconStatus represents the status of a reconnaissance task
type ReconStatus string

const (
	ReconStatusPending   ReconStatus = "pending"
	ReconStatusRunning   ReconStatus = "running"
	ReconStatusCompleted ReconStatus = "completed"
	ReconStatusFailed    ReconStatus = "failed"
	ReconStatusCancelled ReconStatus = "cancelled"
)

// StartReconRequest represents a request to start network reconnaissance
type StartReconRequest struct {
	Target     string                 `json:"target"`
	ScanType   string                 `json:"scan_type"`
	Parameters map[string]interface{} `json:"parameters,omitempty"`
}

// ReconTask represents a network reconnaissance task
type ReconTask struct {
	ID         string                 `json:"id"`
	Target     string                 `json:"target"`
	ScanType   string                 `json:"scan_type"`
	Parameters map[string]interface{} `json:"parameters"`
	StartTime  string                 `json:"start_time"`
	EndTime    string                 `json:"end_time,omitempty"`
	Status     ReconStatus            `json:"status"`
}

// ReconResult represents the detailed results of a reconnaissance task
type ReconResult struct {
	TaskID    string                 `json:"task_id"`
	Status    string                 `json:"status"`
	Output    map[string]interface{} `json:"output"`
	Timestamp string                 `json:"timestamp"`
}

// ReconMetrics represents operational metrics for the recon service
type ReconMetrics struct {
	TotalScans       int                    `json:"total_scans"`
	ActiveScans      int                    `json:"active_scans"`
	CompletedScans   int                    `json:"completed_scans"`
	FailedScans      int                    `json:"failed_scans"`
	AverageDuration  float64                `json:"average_duration_seconds"`
	ScansByType      map[string]int         `json:"scans_by_type"`
	AdditionalMetrics map[string]interface{} `json:"additional_metrics,omitempty"`
}

// ReconHealthResponse represents health check response
type ReconHealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// NewReconClient creates a new Network Reconnaissance service client
func NewReconClient(endpoint, authToken string) *ReconClient {
	return &ReconClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 120 * time.Second, // Network scans can take time
		},
		authToken: authToken,
	}
}

// StartRecon initiates a new network reconnaissance task
//
// Parameters:
//   - target: The target for reconnaissance (IP address, CIDR range, domain)
//   - scanType: Type of scan (e.g., 'nmap_full', 'masscan_ports')
//   - parameters: Additional parameters for the scan (e.g., 'ports' for masscan)
//
// Returns the initiated reconnaissance task details
func (c *ReconClient) StartRecon(target, scanType string, parameters map[string]interface{}) (*ReconTask, error) {
	req := StartReconRequest{
		Target:     target,
		ScanType:   scanType,
		Parameters: parameters,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/start_recon", c.baseURL), bytes.NewBuffer(body))
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

	var result ReconTask
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetReconStatus retrieves the current status of a reconnaissance task
//
// Parameters:
//   - taskID: The ID of the reconnaissance task
//
// Returns the current task status and details
func (c *ReconClient) GetReconStatus(taskID string) (*ReconTask, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/recon_task/%s/status", c.baseURL, taskID), nil)
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

	var result ReconTask
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetReconResults retrieves the results of a completed reconnaissance task
//
// Parameters:
//   - taskID: The ID of the reconnaissance task
//
// Returns the detailed reconnaissance results
func (c *ReconClient) GetReconResults(taskID string) (*ReconResult, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/recon_task/%s/results", c.baseURL, taskID), nil)
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

	var result ReconResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetMetrics retrieves overall operational metrics for the reconnaissance service
//
// Returns service metrics including scan counts, durations, and statistics
func (c *ReconClient) GetMetrics() (*ReconMetrics, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/metrics", c.baseURL), nil)
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

	var result ReconMetrics
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Health performs a health check on the reconnaissance service
//
// Returns the health status of the service
func (c *ReconClient) Health() (*ReconHealthResponse, error) {
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

	var result ReconHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
