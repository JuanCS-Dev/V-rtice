package investigation

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// InvestigationClient handles communication with Autonomous Investigation API
type InvestigationClient struct {
	baseURL    string
	httpClient *http.Client
}

// NewInvestigationClient creates a new investigation API client
func NewInvestigationClient(baseURL string) *InvestigationClient {
	if baseURL == "" {
		baseURL = "http://localhost:8042"
	}

	return &InvestigationClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 60 * time.Second, // Longer timeout for investigations
		},
	}
}

// ==================== REQUEST TYPES ====================

// ThreatActorRegistrationRequest for registering threat actors
type ThreatActorRegistrationRequest struct {
	ActorID              string   `json:"actor_id"`
	ActorName            string   `json:"actor_name"`
	KnownTTPs            []string `json:"known_ttps"`
	KnownInfrastructure  []string `json:"known_infrastructure,omitempty"`
	SophisticationScore  float64  `json:"sophistication_score"`
}

// SecurityIncidentRequest for ingesting incidents
type SecurityIncidentRequest struct {
	IncidentID      string            `json:"incident_id"`
	Timestamp       *string           `json:"timestamp,omitempty"`
	IncidentType    string            `json:"incident_type"`
	AffectedAssets  []string          `json:"affected_assets"`
	IOCs            []string          `json:"iocs"`
	TTPsObserved    []string          `json:"ttps_observed"`
	Severity        float64           `json:"severity"`
	RawEvidence     map[string]interface{} `json:"raw_evidence,omitempty"`
}

// ==================== RESPONSE TYPES ====================

// ThreatActorProfileResponse from /actor/{id}
type ThreatActorProfileResponse struct {
	ActorID              string   `json:"actor_id"`
	ActorName            string   `json:"actor_name"`
	TTPs                 []string `json:"ttps"`
	Infrastructure       []string `json:"infrastructure"`
	MalwareFamilies      []string `json:"malware_families"`
	Targets              []string `json:"targets"`
	SophisticationScore  float64  `json:"sophistication_score"`
	ActivityCount        int      `json:"activity_count"`
	AttributionConfidence float64 `json:"attribution_confidence"`
}

// AttributionResponse from /incident/attribute
type AttributionResponse struct {
	IncidentID          string   `json:"incident_id"`
	AttributedActorID   *string  `json:"attributed_actor_id"`
	AttributedActorName *string  `json:"attributed_actor_name"`
	ConfidenceScore     float64  `json:"confidence_score"`
	MatchingTTPs        []string `json:"matching_ttps"`
	Timestamp           string   `json:"timestamp"`
}

// CampaignResponse from /campaign endpoints
type CampaignResponse struct {
	CampaignID       string   `json:"campaign_id"`
	CampaignName     string   `json:"campaign_name"`
	Incidents        []string `json:"incidents"`
	AttributedActor  *string  `json:"attributed_actor"`
	StartDate        string   `json:"start_date"`
	LastActivity     string   `json:"last_activity"`
	TTPs             []string `json:"ttps"`
	Targets          []string `json:"targets"`
	ConfidenceScore  float64  `json:"confidence_score"`
	CampaignPattern  string   `json:"campaign_pattern"`
	Timestamp        string   `json:"timestamp"`
}

// InvestigationResponse from /investigation endpoints
type InvestigationResponse struct {
	InvestigationID    string   `json:"investigation_id"`
	IncidentID         string   `json:"incident_id"`
	Status             string   `json:"status"`
	Findings           []string `json:"findings"`
	EvidenceCount      int      `json:"evidence_count"`
	AttributedActor    *string  `json:"attributed_actor"`
	RelatedCampaigns   []string `json:"related_campaigns"`
	ConfidenceScore    float64  `json:"confidence_score"`
	PlaybookUsed       string   `json:"playbook_used"`
	DurationSeconds    *float64 `json:"duration_seconds"`
	Recommendations    []string `json:"recommendations"`
}

// StatusResponse from /status
type StatusResponse struct {
	Service    string                            `json:"service"`
	Status     string                            `json:"status"`
	Components map[string]map[string]interface{} `json:"components"`
	Timestamp  string                            `json:"timestamp"`
}

// ==================== API METHODS ====================

// RegisterThreatActor registers a new threat actor
func (c *InvestigationClient) RegisterThreatActor(req ThreatActorRegistrationRequest) (map[string]interface{}, error) {
	url := fmt.Sprintf("%s/actor/register", c.baseURL)

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// GetActorProfile retrieves threat actor profile
func (c *InvestigationClient) GetActorProfile(actorID string) (*ThreatActorProfileResponse, error) {
	url := fmt.Sprintf("%s/actor/%s", c.baseURL, actorID)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("threat actor not found: %s", actorID)
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var profile ThreatActorProfileResponse
	if err := json.NewDecoder(resp.Body).Decode(&profile); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &profile, nil
}

// ListThreatActors lists all registered threat actors
func (c *InvestigationClient) ListThreatActors() ([]ThreatActorProfileResponse, error) {
	url := fmt.Sprintf("%s/actor", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var actors []ThreatActorProfileResponse
	if err := json.NewDecoder(resp.Body).Decode(&actors); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return actors, nil
}

// IngestIncident ingests security incident
func (c *InvestigationClient) IngestIncident(req SecurityIncidentRequest) (map[string]interface{}, error) {
	url := fmt.Sprintf("%s/incident/ingest", c.baseURL)

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// AttributeIncident attributes incident to threat actor
func (c *InvestigationClient) AttributeIncident(incidentID string) (*AttributionResponse, error) {
	url := fmt.Sprintf("%s/incident/attribute", c.baseURL)

	reqBody := map[string]string{"incident_id": incidentID}
	body, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var result AttributionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// CorrelateCampaigns correlates incidents into campaigns
func (c *InvestigationClient) CorrelateCampaigns() ([]CampaignResponse, error) {
	url := fmt.Sprintf("%s/campaign/correlate", c.baseURL)

	resp, err := c.httpClient.Post(url, "application/json", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var campaigns []CampaignResponse
	if err := json.NewDecoder(resp.Body).Decode(&campaigns); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return campaigns, nil
}

// GetCampaign retrieves campaign details
func (c *InvestigationClient) GetCampaign(campaignID string) (*CampaignResponse, error) {
	url := fmt.Sprintf("%s/campaign/%s", c.baseURL, campaignID)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("campaign not found: %s", campaignID)
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var campaign CampaignResponse
	if err := json.NewDecoder(resp.Body).Decode(&campaign); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &campaign, nil
}

// ListCampaigns lists all campaigns
func (c *InvestigationClient) ListCampaigns() ([]CampaignResponse, error) {
	url := fmt.Sprintf("%s/campaign", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var campaigns []CampaignResponse
	if err := json.NewDecoder(resp.Body).Decode(&campaigns); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return campaigns, nil
}

// InitiateInvestigation starts autonomous investigation
func (c *InvestigationClient) InitiateInvestigation(incidentID string) (*InvestigationResponse, error) {
	url := fmt.Sprintf("%s/investigation/initiate", c.baseURL)

	reqBody := map[string]string{"incident_id": incidentID}
	body, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
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

// GetInvestigation retrieves investigation status
func (c *InvestigationClient) GetInvestigation(investigationID string) (*InvestigationResponse, error) {
	url := fmt.Sprintf("%s/investigation/%s", c.baseURL, investigationID)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("investigation not found: %s", investigationID)
	}

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var investigation InvestigationResponse
	if err := json.NewDecoder(resp.Body).Decode(&investigation); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &investigation, nil
}

// Health checks service health
func (c *InvestigationClient) Health() error {
	url := fmt.Sprintf("%s/health", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return fmt.Errorf("investigation API unreachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("investigation API unhealthy (status %d)", resp.StatusCode)
	}

	return nil
}

// GetStatus retrieves service status
func (c *InvestigationClient) GetStatus() (*StatusResponse, error) {
	url := fmt.Sprintf("%s/status", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

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

// GetStats retrieves service statistics
func (c *InvestigationClient) GetStats() (map[string]interface{}, error) {
	url := fmt.Sprintf("%s/stats", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to investigation API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var stats map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return stats, nil
}
