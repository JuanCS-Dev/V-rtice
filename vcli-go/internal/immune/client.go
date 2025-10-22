package immune

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

// ImmuneClient handles communication with Active Immune Core API
type ImmuneClient struct {
	baseURL    string
	httpClient *http.Client
}

// NewImmuneClient creates a new Immune Core API client
//
// The baseURL should include the protocol (http:// or https://).
// For production environments, HTTPS is strongly recommended.
//
// Examples:
//   - Development: http://localhost:8200
//   - Production:  https://immune.vertice.ai:8200
func NewImmuneClient(baseURL string) *ImmuneClient {
	source := "flag"
	if baseURL == "" {
		baseURL = os.Getenv("VCLI_IMMUNE_ENDPOINT")
		if baseURL != "" {
			source = "env:VCLI_IMMUNE_ENDPOINT"
		} else {
			baseURL = "http://localhost:8200"
			source = "default"
		}
	}

	// Ensure URL has protocol
	if !strings.HasPrefix(baseURL, "http://") && !strings.HasPrefix(baseURL, "https://") {
		// If no protocol specified, use https for non-localhost, http for localhost
		if strings.HasPrefix(baseURL, "localhost") || strings.HasPrefix(baseURL, "127.0.0.1") {
			baseURL = "http://" + baseURL
		} else {
			baseURL = "https://" + baseURL
		}
	}

	debug.LogConnection("Active Immune Core", baseURL, source)

	return &ImmuneClient{
		baseURL: strings.TrimSuffix(baseURL, "/"),
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// ==================== RESPONSE TYPES ====================

// HealthResponse represents health check response
type HealthResponse struct {
	Status          string  `json:"status"`
	Timestamp       string  `json:"timestamp"`
	Version         string  `json:"version"`
	UptimeSeconds   float64 `json:"uptime_seconds"`
	AgentsActive    int     `json:"agents_active"`
	LymphnodesActive int    `json:"lymphnodes_active"`
}

// Agent represents an immune system agent
type Agent struct {
	AgentID       string                 `json:"agent_id"`
	AgentType     string                 `json:"agent_type"`
	State         string                 `json:"state"`
	LymphnodeID   string                 `json:"lymphnode_id"`
	CreatedAt     string                 `json:"created_at"`
	LastHeartbeat string                 `json:"last_heartbeat,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// AgentListResponse represents list agents response
type AgentListResponse struct {
	Agents     []Agent `json:"agents"`
	TotalCount int     `json:"total_count"`
	Page       int     `json:"page,omitempty"`
	PageSize   int     `json:"page_size,omitempty"`
}

// AgentDetailResponse represents single agent with details
type AgentDetailResponse struct {
	Agent
	Metrics  map[string]interface{} `json:"metrics,omitempty"`
	History  []interface{}          `json:"history,omitempty"`
}

// CloneAgentRequest represents clone agent request
type CloneAgentRequest struct {
	SourceAgentID string `json:"source_agent_id"`
	Count         int    `json:"count"`
	LymphnodeID   string `json:"lymphnode_id,omitempty"`
}

// CloneAgentResponse represents clone agent response
type CloneAgentResponse struct {
	Success   bool     `json:"success"`
	ClonedIDs []string `json:"cloned_ids"`
	Message   string   `json:"message,omitempty"`
}

// Lymphnode represents a lymphnode (agent cluster)
type Lymphnode struct {
	LymphnodeID string                 `json:"lymphnode_id"`
	Zone        string                 `json:"zone"`
	Status      string                 `json:"status"`
	AgentCount  int                    `json:"agent_count"`
	Capacity    int                    `json:"capacity"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// LymphnodeListResponse represents list lymphnodes response
type LymphnodeListResponse struct {
	Lymphnodes []Lymphnode `json:"lymphnodes"`
	TotalCount int         `json:"total_count"`
}

// HomeostasisResponse represents system homeostasis status
type HomeostasisResponse struct {
	Status         string                 `json:"status"`
	Balance        float64                `json:"balance"`
	AgentsActive   int                    `json:"agents_active"`
	AgentsIdle     int                    `json:"agents_idle"`
	TotalAgents    int                    `json:"total_agents"`
	Recommendations []string              `json:"recommendations,omitempty"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
}

// ==================== API METHODS ====================

// Health checks if the Immune Core API is reachable
func (c *ImmuneClient) Health() (*HealthResponse, error) {
	healthURL := fmt.Sprintf("%s/health", c.baseURL)

	resp, err := c.httpClient.Get(healthURL)
	if err != nil {
		// Return contextual connection error with suggestions
		return nil, vcli_errors.NewConnectionErrorBuilder("Active Immune Core", c.baseURL).
			WithOperation("health check").
			WithCause(err).
			Build()
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

// ListAgents retrieves all agents with optional filtering
func (c *ImmuneClient) ListAgents(lymphnodeID, agentType, state string, page, pageSize int) (*AgentListResponse, error) {
	u, _ := url.Parse(fmt.Sprintf("%s/agents", c.baseURL))
	q := u.Query()

	if lymphnodeID != "" {
		q.Set("lymphnode_id", lymphnodeID)
	}
	if agentType != "" {
		q.Set("agent_type", agentType)
	}
	if state != "" {
		q.Set("state", state)
	}
	if page > 0 {
		q.Set("page", fmt.Sprintf("%d", page))
	}
	if pageSize > 0 {
		q.Set("page_size", fmt.Sprintf("%d", pageSize))
	}

	u.RawQuery = q.Encode()

	resp, err := c.httpClient.Get(u.String())
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Immune Core API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var agents AgentListResponse
	if err := json.NewDecoder(resp.Body).Decode(&agents); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &agents, nil
}

// GetAgent retrieves details for a specific agent
func (c *ImmuneClient) GetAgent(agentID string, includeMetrics, includeHistory bool) (*AgentDetailResponse, error) {
	u, _ := url.Parse(fmt.Sprintf("%s/agents/%s", c.baseURL, agentID))
	q := u.Query()

	if includeMetrics {
		q.Set("include_metrics", "true")
	}
	if includeHistory {
		q.Set("include_history", "true")
	}

	u.RawQuery = q.Encode()

	resp, err := c.httpClient.Get(u.String())
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Immune Core API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var agent AgentDetailResponse
	if err := json.NewDecoder(resp.Body).Decode(&agent); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &agent, nil
}

// CloneAgent clones an existing agent
func (c *ImmuneClient) CloneAgent(req CloneAgentRequest) (*CloneAgentResponse, error) {
	url := fmt.Sprintf("%s/agents/clone", c.baseURL)

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Immune Core API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(respBody))
	}

	var result CloneAgentResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// ListLymphnodes retrieves all lymphnodes with optional filtering
func (c *ImmuneClient) ListLymphnodes(zone string, includeMetrics bool) (*LymphnodeListResponse, error) {
	u, _ := url.Parse(fmt.Sprintf("%s/lymphnodes", c.baseURL))
	q := u.Query()

	if zone != "" {
		q.Set("zone", zone)
	}
	if includeMetrics {
		q.Set("include_metrics", "true")
	}

	u.RawQuery = q.Encode()

	resp, err := c.httpClient.Get(u.String())
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Immune Core API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var lymphnodes LymphnodeListResponse
	if err := json.NewDecoder(resp.Body).Decode(&lymphnodes); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &lymphnodes, nil
}

// GetHomeostasis retrieves system homeostasis status
func (c *ImmuneClient) GetHomeostasis() (*HomeostasisResponse, error) {
	url := fmt.Sprintf("%s/homeostasis", c.baseURL)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Immune Core API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(body))
	}

	var homeostasis HomeostasisResponse
	if err := json.NewDecoder(resp.Body).Decode(&homeostasis); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &homeostasis, nil
}
