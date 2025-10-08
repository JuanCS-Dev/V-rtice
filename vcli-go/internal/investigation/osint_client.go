package investigation

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// OSINTClient provides access to OSINT Service for open-source intelligence gathering
type OSINTClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// StartInvestigationRequest represents a request to start an OSINT investigation
type StartInvestigationRequest struct {
	Query              string                 `json:"query"`
	InvestigationType  string                 `json:"investigation_type"`
	Parameters         map[string]interface{} `json:"parameters,omitempty"`
}

// StartInvestigationResponse represents the response from starting an investigation
type StartInvestigationResponse struct {
	InvestigationID string `json:"investigation_id"`
	Status          string `json:"status"`
	Timestamp       string `json:"timestamp"`
}

// InvestigationStatus represents the current status of an OSINT investigation
type InvestigationStatus struct {
	ID          string                 `json:"id"`
	Query       string                 `json:"query"`
	Type        string                 `json:"type"`
	Status      string                 `json:"status"`
	Progress    float64                `json:"progress"`
	StartTime   string                 `json:"start_time"`
	Results     map[string]interface{} `json:"results"`
	Parameters  map[string]interface{} `json:"parameters"`
	CurrentStep string                 `json:"current_step,omitempty"`
	Error       string                 `json:"error,omitempty"`
}

// InvestigationReport represents the final report of a completed investigation
type InvestigationReport struct {
	InvestigationID    string                 `json:"investigation_id"`
	Query              string                 `json:"query"`
	InvestigationType  string                 `json:"investigation_type"`
	Summary            string                 `json:"summary"`
	Findings           []map[string]interface{} `json:"findings"`
	CollectedData      []map[string]interface{} `json:"collected_data"`
	AnalysisResults    map[string]interface{} `json:"analysis_results"`
	Recommendations    []string               `json:"recommendations,omitempty"`
	Timestamp          string                 `json:"timestamp"`
	AdditionalMetadata map[string]interface{} `json:"additional_metadata,omitempty"`
}

// OSINTHealthResponse represents health check response
type OSINTHealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// NewOSINTClient creates a new OSINT service client
func NewOSINTClient(endpoint, authToken string) *OSINTClient {
	return &OSINTClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 120 * time.Second, // OSINT investigations can take time
		},
		authToken: authToken,
	}
}

// StartInvestigation initiates a new OSINT investigation
//
// Parameters:
//   - query: The primary query for the investigation (username, email, domain, etc.)
//   - investigationType: Type of investigation (e.g., 'person_recon', 'domain_analysis')
//   - parameters: Additional parameters for the investigation
//
// Returns the investigation ID and initial status
func (c *OSINTClient) StartInvestigation(query, investigationType string, parameters map[string]interface{}) (*StartInvestigationResponse, error) {
	req := StartInvestigationRequest{
		Query:              query,
		InvestigationType:  investigationType,
		Parameters:         parameters,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/start_investigation", c.baseURL), bytes.NewBuffer(body))
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

	var result StartInvestigationResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetInvestigationStatus retrieves the current status of an OSINT investigation
//
// Parameters:
//   - investigationID: The ID of the investigation
//
// Returns the current status, progress, and partial results
func (c *OSINTClient) GetInvestigationStatus(investigationID string) (*InvestigationStatus, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/investigation/%s/status", c.baseURL, investigationID), nil)
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

	var result InvestigationStatus
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetInvestigationReport retrieves the final report of a completed OSINT investigation
//
// Parameters:
//   - investigationID: The ID of the investigation
//
// Returns the complete investigation report with findings and analysis
func (c *OSINTClient) GetInvestigationReport(investigationID string) (*InvestigationReport, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/investigation/%s/report", c.baseURL, investigationID), nil)
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

	// The report endpoint returns the results field from the investigation status
	// We need to decode it as a generic map first, then convert to InvestigationReport
	var rawReport map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&rawReport); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Convert the raw map to InvestigationReport structure
	// Marshal back to JSON then unmarshal to struct for type safety
	reportJSON, err := json.Marshal(rawReport)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal report: %w", err)
	}

	var report InvestigationReport
	if err := json.Unmarshal(reportJSON, &report); err != nil {
		return nil, fmt.Errorf("failed to unmarshal report: %w", err)
	}

	return &report, nil
}

// Health performs a health check on the OSINT service
//
// Returns the health status of the service
func (c *OSINTClient) Health() (*OSINTHealthResponse, error) {
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

	var result OSINTHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
