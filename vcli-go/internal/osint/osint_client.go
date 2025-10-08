package osint

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// OSINTClient handles communication with OSINT Service API
type OSINTClient struct {
	baseURL    string
	httpClient *http.Client
}

// NewOSINTClient creates a new OSINT API client
func NewOSINTClient(baseURL string) *OSINTClient {
	if baseURL == "" {
		baseURL = "http://localhost:8050"
	}

	return &OSINTClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 120 * time.Second, // OSINT can take longer
		},
	}
}

// ==================== REQUEST TYPES ====================

// StartInvestigationRequest for initiating OSINT investigations
type StartInvestigationRequest struct {
	Query              string                 `json:"query"`
	InvestigationType  string                 `json:"investigation_type"`
	Parameters         map[string]interface{} `json:"parameters,omitempty"`
}

// ==================== RESPONSE TYPES ====================

// InvestigationResponse from /start_investigation
type InvestigationResponse struct {
	InvestigationID string `json:"investigation_id"`
	Status          string `json:"status"`
	Message         string `json:"message,omitempty"`
}

// StatusResponse from /investigation/{id}/status
type StatusResponse struct {
	InvestigationID string                 `json:"investigation_id"`
	Status          string                 `json:"status"`
	Progress        float64                `json:"progress,omitempty"`
	CurrentPhase    string                 `json:"current_phase,omitempty"`
	Message         string                 `json:"message,omitempty"`
	Details         map[string]interface{} `json:"details,omitempty"`
}

// ReportResponse from /investigation/{id}/report
type ReportResponse struct {
	InvestigationID   string                 `json:"investigation_id"`
	Query             string                 `json:"query"`
	InvestigationType string                 `json:"investigation_type"`
	Status            string                 `json:"status"`
	StartedAt         string                 `json:"started_at"`
	CompletedAt       string                 `json:"completed_at,omitempty"`
	Findings          []Finding              `json:"findings,omitempty"`
	Summary           string                 `json:"summary,omitempty"`
	RiskScore         float64                `json:"risk_score,omitempty"`
	Metadata          map[string]interface{} `json:"metadata,omitempty"`
}

// Finding represents an OSINT finding
type Finding struct {
	Source      string                 `json:"source"`
	Category    string                 `json:"category"`
	Severity    string                 `json:"severity,omitempty"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	URL         string                 `json:"url,omitempty"`
	Timestamp   string                 `json:"timestamp,omitempty"`
	Data        map[string]interface{} `json:"data,omitempty"`
}

// HealthResponse from /health
type HealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// ==================== API METHODS ====================

// StartInvestigation initiates a new OSINT investigation
func (c *OSINTClient) StartInvestigation(req StartInvestigationRequest) (*InvestigationResponse, error) {
	url := fmt.Sprintf("%s/start_investigation", c.baseURL)

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to OSINT API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var result InvestigationResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetStatus retrieves investigation status
func (c *OSINTClient) GetStatus(investigationID string) (*StatusResponse, error) {
	url := fmt.Sprintf("%s/investigation/%s/status", c.baseURL, investigationID)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to OSINT API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("investigation not found: %s", investigationID)
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var status StatusResponse
	if err := json.NewDecoder(resp.Body).Decode(&status); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &status, nil
}

// GetReport retrieves investigation report
func (c *OSINTClient) GetReport(investigationID string) (*ReportResponse, error) {
	url := fmt.Sprintf("%s/investigation/%s/report", c.baseURL, investigationID)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to OSINT API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("investigation not found: %s", investigationID)
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var report ReportResponse
	if err := json.NewDecoder(resp.Body).Decode(&report); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &report, nil
}

// Health checks service health
func (c *OSINTClient) Health() error {
	url := fmt.Sprintf("%s/health", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return fmt.Errorf("OSINT API unreachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("OSINT API unhealthy (status %d)", resp.StatusCode)
	}

	return nil
}

// GetHealthDetails retrieves detailed health information
func (c *OSINTClient) GetHealthDetails() (*HealthResponse, error) {
	url := fmt.Sprintf("%s/health", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to OSINT API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var health HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &health, nil
}
