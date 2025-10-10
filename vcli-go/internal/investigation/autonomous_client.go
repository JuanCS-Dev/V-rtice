package investigation

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// AutonomousClient provides access to Autonomous Investigation Service
type AutonomousClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// ThreatActorProfile represents a threat actor profile
type ThreatActorProfile struct {
	ActorID              string                 `json:"actor_id"`
	ActorName            string                 `json:"actor_name"`
	KnownTTPs            []string               `json:"known_ttps"`
	KnownInfrastructure  []string               `json:"known_infrastructure"`
	SophisticationScore  float64                `json:"sophistication_score"`
	ObservedIncidents    int                    `json:"observed_incidents,omitempty"`
	FirstSeen            string                 `json:"first_seen,omitempty"`
	LastSeen             string                 `json:"last_seen,omitempty"`
	AdditionalAttributes map[string]interface{} `json:"additional_attributes,omitempty"`
}

// AttributionResponse represents attribution analysis response
type AttributionResponse struct {
	PrimaryAttribution string                       `json:"primary_attribution"`
	Confidence         float64                      `json:"confidence"`
	AlternativeActors  []map[string]interface{}     `json:"alternative_actors"`
	Reasoning          string                       `json:"reasoning"`
	MatchedIndicators  map[string][]string          `json:"matched_indicators"`
	Timestamp          string                       `json:"timestamp"`
}

// CampaignResponse represents a campaign
type CampaignResponse struct {
	CampaignID   string                 `json:"campaign_id"`
	Name         string                 `json:"name"`
	FirstSeen    string                 `json:"first_seen"`
	LastSeen     string                 `json:"last_seen"`
	Incidents    []string               `json:"incidents"`
	Actors       []string               `json:"actors"`
	SharedTTPs   []string               `json:"shared_ttps"`
	Confidence   float64                `json:"confidence"`
	Description  string                 `json:"description,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// InvestigationResponse represents an investigation
type InvestigationResponse struct {
	InvestigationID string                 `json:"investigation_id"`
	Status          string                 `json:"status"`
	StartedAt       string                 `json:"started_at"`
	CompletedAt     string                 `json:"completed_at,omitempty"`
	Findings        map[string]interface{} `json:"findings,omitempty"`
	Recommendations []string               `json:"recommendations,omitempty"`
}

// StatusResponse represents service status
type StatusResponse struct {
	Status           string `json:"status"`
	ThreatActors     int    `json:"threat_actors"`
	Incidents        int    `json:"incidents"`
	Campaigns        int    `json:"campaigns"`
	Investigations   int    `json:"investigations"`
	Timestamp        string `json:"timestamp"`
}

// HealthResponse represents health check
type HealthResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
}

// NewAutonomousClient creates a new Autonomous Investigation client
func NewAutonomousClient(endpoint, authToken string) *AutonomousClient {
	return &AutonomousClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 120 * time.Second, // Investigations can take time
		},
		authToken: authToken,
	}
}

// RegisterActor registers a new threat actor profile
func (c *AutonomousClient) RegisterActor(profile ThreatActorProfile) (*ThreatActorProfile, error) {
	body, err := json.Marshal(profile)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/actor/register", c.baseURL), bytes.NewBuffer(body))
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

	var result ThreatActorProfile
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetActor retrieves a threat actor profile by ID
func (c *AutonomousClient) GetActor(actorID string) (*ThreatActorProfile, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/actor/%s", c.baseURL, actorID), nil)
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

	var result ThreatActorProfile
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// ListActors lists all threat actors
func (c *AutonomousClient) ListActors() ([]ThreatActorProfile, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/actor", c.baseURL), nil)
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

	var result []ThreatActorProfile
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// IngestIncident ingests a security incident
func (c *AutonomousClient) IngestIncident(incident map[string]interface{}) (map[string]interface{}, error) {
	body, err := json.Marshal(incident)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/incident/ingest", c.baseURL), bytes.NewBuffer(body))
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

// AttributeIncident performs attribution analysis on an incident
func (c *AutonomousClient) AttributeIncident(incidentID string) (*AttributionResponse, error) {
	reqBody := map[string]string{"incident_id": incidentID}
	body, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/incident/attribute", c.baseURL), bytes.NewBuffer(body))
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

	var result AttributionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// CorrelateCampaigns correlates incidents into campaigns
func (c *AutonomousClient) CorrelateCampaigns() ([]CampaignResponse, error) {
	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/campaign/correlate", c.baseURL), nil)
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

	var result []CampaignResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// GetCampaign retrieves a campaign by ID
func (c *AutonomousClient) GetCampaign(campaignID string) (*CampaignResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/campaign/%s", c.baseURL, campaignID), nil)
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

	var result CampaignResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// ListCampaigns lists all campaigns
func (c *AutonomousClient) ListCampaigns() ([]CampaignResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/campaign", c.baseURL), nil)
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

	var result []CampaignResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// InitiateInvestigation initiates a new investigation
func (c *AutonomousClient) InitiateInvestigation(target string, scope string) (*InvestigationResponse, error) {
	reqBody := map[string]string{
		"target": target,
		"scope":  scope,
	}
	body, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/investigation/initiate", c.baseURL), bytes.NewBuffer(body))
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

	var result InvestigationResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetInvestigation retrieves an investigation by ID
func (c *AutonomousClient) GetInvestigation(investigationID string) (*InvestigationResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/investigation/%s", c.baseURL, investigationID), nil)
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

	var result InvestigationResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetStatus retrieves service status
func (c *AutonomousClient) GetStatus() (*StatusResponse, error) {
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

	var result StatusResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Health performs health check
func (c *AutonomousClient) Health() (*HealthResponse, error) {
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

	var result HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
