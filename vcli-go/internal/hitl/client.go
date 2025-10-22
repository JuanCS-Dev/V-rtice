package hitl

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/internal/debug"
	vcli_errors "github.com/verticedev/vcli-go/internal/errors"
)

// Client provides access to HITL Console API
type Client struct {
	baseURL     string
	httpClient  *http.Client
	accessToken string
}

// ============================================================================
// REQUEST/RESPONSE MODELS
// ============================================================================

// LoginRequest represents authentication request
type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// LoginResponse represents authentication response
type LoginResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
}

// Decision represents a HITL decision
type Decision struct {
	DecisionID         string    `json:"decision_id"`
	AnalysisID         string    `json:"analysis_id"`
	IncidentID         string    `json:"incident_id"`
	ThreatLevel        string    `json:"threat_level"`
	SourceIP           string    `json:"source_ip"`
	AttributedActor    string    `json:"attributed_actor"`
	Confidence         float64   `json:"confidence"`
	IOCs               []string  `json:"iocs"`
	TTPs               []string  `json:"ttps"`
	RecommendedActions []string  `json:"recommended_actions"`
	ForensicSummary    string    `json:"forensic_summary"`
	Priority           string    `json:"priority"`
	Status             string    `json:"status"`
	CreatedAt          time.Time `json:"created_at"`
	UpdatedAt          time.Time `json:"updated_at"`
}

// DecisionResponse represents decision response with human input
type DecisionResponse struct {
	DecisionID      string    `json:"decision_id"`
	AnalysisID      string    `json:"analysis_id"`
	Status          string    `json:"status"`
	ApprovedActions []string  `json:"approved_actions"`
	Notes           string    `json:"notes"`
	DecidedBy       string    `json:"decided_by"`
	DecidedAt       time.Time `json:"decided_at"`
}

// DecisionCreate represents decision creation request
type DecisionCreate struct {
	Status          string   `json:"status"`
	ApprovedActions []string `json:"approved_actions"`
	Notes           string   `json:"notes"`
}

// EscalateRequest represents escalation request
type EscalateRequest struct {
	Reason string `json:"reason"`
}

// SystemStatus represents HITL system status
type SystemStatus struct {
	Status             string `json:"status"`
	PendingDecisions   int    `json:"pending_decisions"`
	CriticalPending    int    `json:"critical_pending"`
	InReviewDecisions  int    `json:"in_review_decisions"`
	TotalDecisionsToday int   `json:"total_decisions_today"`
}

// DecisionStats represents decision statistics
type DecisionStats struct {
	TotalPending            int     `json:"total_pending"`
	CriticalPending         int     `json:"critical_pending"`
	HighPending             int     `json:"high_pending"`
	MediumPending           int     `json:"medium_pending"`
	LowPending              int     `json:"low_pending"`
	TotalApproved           int     `json:"total_approved"`
	TotalRejected           int     `json:"total_rejected"`
	TotalEscalated          int     `json:"total_escalated"`
	ApprovalRate            float64 `json:"approval_rate"`
	AvgResponseTimeMinutes  float64 `json:"avg_response_time_minutes"`
	OldestPendingMinutes    float64 `json:"oldest_pending_minutes"`
}

// HealthResponse represents health check response
type HealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// ============================================================================
// CLIENT METHODS
// ============================================================================

// NewClient creates a new HITL API client
func NewClient(baseURL string) *Client {
	source := "flag"
	if baseURL == "" {
		baseURL = os.Getenv("VCLI_HITL_ENDPOINT")
		if baseURL != "" {
			source = "env:VCLI_HITL_ENDPOINT"
		} else {
			baseURL = "http://localhost:8000/api"
			source = "default"
		}
	}

	// Ensure URL has protocol - HTTPS auto-detection
	if !strings.HasPrefix(baseURL, "http://") && !strings.HasPrefix(baseURL, "https://") {
		// If no protocol specified, use https for non-localhost, http for localhost
		if strings.HasPrefix(baseURL, "localhost") || strings.HasPrefix(baseURL, "127.0.0.1") {
			baseURL = "http://" + baseURL
		} else {
			baseURL = "https://" + baseURL
		}
	}

	debug.LogConnection("HITL Console", baseURL, source)

	return &Client{
		baseURL: strings.TrimSuffix(baseURL, "/"),
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Login authenticates and obtains access token
func (c *Client) Login(username, password string) error {
	// Use form data for OAuth2 password flow
	data := url.Values{}
	data.Set("username", username)
	data.Set("password", password)

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/auth/login", c.baseURL), bytes.NewBufferString(data.Encode()))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return vcli_errors.NewConnectionErrorBuilder("HITL Console", c.baseURL).
			WithOperation("login").
			WithCause(err).
			Build()
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusUnauthorized || resp.StatusCode == http.StatusForbidden {
		bodyBytes, _ := io.ReadAll(resp.Body)
		baseErr := vcli_errors.NewAuthError("HITL Console", "Invalid credentials")
		baseErr = baseErr.WithDetails(string(bodyBytes))
		ctx := vcli_errors.ErrorContext{
			Endpoint:    c.baseURL,
			Operation:   "login",
			Suggestions: vcli_errors.GetSuggestionsFor(vcli_errors.ErrorTypeAuth, "HITL Console", c.baseURL),
			HelpCommand: "vcli troubleshoot hitl",
		}
		return vcli_errors.NewContextualError(baseErr, ctx)
	} else if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("login failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result LoginResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return fmt.Errorf("failed to decode response: %w", err)
	}

	c.accessToken = result.AccessToken
	return nil
}

// SetToken sets the access token directly (for testing or when token is already available)
func (c *Client) SetToken(token string) {
	c.accessToken = token
}

// BaseURL returns the base URL
func (c *Client) BaseURL() string {
	return c.baseURL
}

// GetStatus retrieves HITL system status
func (c *Client) GetStatus() (*SystemStatus, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/status", c.baseURL), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	c.setAuthHeader(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result SystemStatus
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// ListPendingDecisions retrieves all pending decisions
func (c *Client) ListPendingDecisions(priority string) ([]Decision, error) {
	endpoint := fmt.Sprintf("%s/decisions/pending", c.baseURL)

	// Add priority filter if specified
	if priority != "" {
		endpoint = fmt.Sprintf("%s?priority=%s", endpoint, priority)
	}

	httpReq, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	c.setAuthHeader(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result []Decision
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// GetDecision retrieves specific decision by analysis ID
func (c *Client) GetDecision(analysisID string) (*Decision, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/decisions/%s", c.baseURL, analysisID), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	c.setAuthHeader(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, fmt.Errorf("decision not found: %s", analysisID)
	}

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result Decision
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetDecisionResponse retrieves decision response if available
func (c *Client) GetDecisionResponse(analysisID string) (*DecisionResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/decisions/%s/response", c.baseURL, analysisID), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	c.setAuthHeader(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil // Decision not yet made
	}

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result DecisionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// MakeDecision submits decision (approve/reject)
func (c *Client) MakeDecision(analysisID string, decision DecisionCreate) (*DecisionResponse, error) {
	body, err := json.Marshal(decision)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/decisions/%s/decide", c.baseURL, analysisID), bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	c.setAuthHeader(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result DecisionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// EscalateDecision escalates decision to higher authority
func (c *Client) EscalateDecision(analysisID string, reason string) (*DecisionResponse, error) {
	req := EscalateRequest{Reason: reason}
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/decisions/%s/escalate", c.baseURL, analysisID), bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	c.setAuthHeader(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result DecisionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetStats retrieves decision statistics
func (c *Client) GetStats() (*DecisionStats, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/decisions/stats/summary", c.baseURL), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	c.setAuthHeader(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result DecisionStats
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Health performs health check
func (c *Client) Health() (*HealthResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/health", c.baseURL), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
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

// ============================================================================
// HELPER METHODS
// ============================================================================

func (c *Client) setAuthHeader(req *http.Request) {
	if c.accessToken != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.accessToken))
	}
}
