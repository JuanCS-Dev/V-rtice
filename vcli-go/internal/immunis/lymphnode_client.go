package immunis

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// LymphnodeClient provides access to Lymphnode coordination operations
type LymphnodeClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// CloneRequest represents a request to clone an agent (clonal expansion)
type CloneRequest struct {
	AgentID        string  `json:"agent_id"`
	Especializacao *string `json:"especializacao,omitempty"`
	NumClones      int     `json:"num_clones"`
	Mutate         bool    `json:"mutate"`
	MutationRate   float64 `json:"mutation_rate"`
}

// CloneResponse represents the response from clone creation
type CloneResponse struct {
	ParentID       string   `json:"parent_id"`
	CloneIDs       []string `json:"clone_ids"`
	NumClones      int      `json:"num_clones"`
	Especializacao *string  `json:"especializacao,omitempty"`
	CreatedAt      string   `json:"created_at"`
}

// LymphnodeMetrics represents lymphnode operational metrics
type LymphnodeMetrics struct {
	LymphnodeID            string  `json:"lymphnode_id"`
	Nivel                  string  `json:"nivel"`
	AreaResponsabilidade   string  `json:"area_responsabilidade"`
	HomeostaticState       string  `json:"homeostatic_state"`
	TemperaturaRegional    float64 `json:"temperatura_regional"`
	AgentesAtivos          int     `json:"agentes_ativos"`
	AgentesDormindo        int     `json:"agentes_dormindo"`
	TotalAmeacasDetectadas int     `json:"total_ameacas_detectadas"`
	TotalNeutralizacoes    int     `json:"total_neutralizacoes"`
	TotalClonesCriados     int     `json:"total_clones_criados"`
	TotalClonesDestruidos  int     `json:"total_clones_destruidos"`
}

// HomeostaticStateResponse represents the current homeostatic state
type HomeostaticStateResponse struct {
	HomeostaticState    string  `json:"homeostatic_state"`
	TemperaturaRegional float64 `json:"temperatura_regional"`
	Description         string  `json:"description"`
	RecommendedAction   string  `json:"recommended_action"`
}

// DestroyResponse represents the response from clone destruction
type DestroyResponse struct {
	Especializacao string `json:"especializacao"`
	NumDestroyed   int    `json:"num_destroyed"`
	Message        string `json:"message"`
}

// NewLymphnodeClient creates a new Lymphnode service client
func NewLymphnodeClient(endpoint, authToken string) *LymphnodeClient {
	return &LymphnodeClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		authToken: authToken,
	}
}

// CloneAgent creates clones of an agent with optional specialization (clonal expansion)
//
// This mimics the biological immune system's clonal expansion - creating multiple
// specialized copies of a high-performing agent to respond to specific threats.
//
// Parameters:
//   - req: Clone request parameters
//
// Returns clone creation result with clone IDs
func (c *LymphnodeClient) CloneAgent(req CloneRequest) (*CloneResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/clone", c.baseURL), bytes.NewBuffer(body))
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

	if resp.StatusCode != http.StatusCreated {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result CloneResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// DestroyClones triggers programmed cell death (apoptosis) for clones with a specific specialization
//
// This is useful for cleanup after threat neutralization, removing specialized
// clones that are no longer needed.
//
// Parameters:
//   - especializacao: Specialization identifier
//
// Returns the number of clones destroyed
func (c *LymphnodeClient) DestroyClones(especializacao string) (*DestroyResponse, error) {
	httpReq, err := http.NewRequest("DELETE", fmt.Sprintf("%s/clones/%s", c.baseURL, especializacao), nil)
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

	var result DestroyResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetMetrics retrieves lymphnode operational metrics and statistics
//
// Returns metrics including agent counts, threats, clones, homeostatic state, etc.
func (c *LymphnodeClient) GetMetrics() (*LymphnodeMetrics, error) {
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

	var result LymphnodeMetrics
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetHomeostaticState retrieves the current homeostatic state
//
// The homeostatic state represents the system's stress level:
//   - REPOUSO: System at rest
//   - VIGILÂNCIA: Low-level monitoring
//   - ATENÇÃO: Moderate alert
//   - ATIVAÇÃO: Significant stress
//   - INFLAMAÇÃO: Critical stress
//
// Returns the state with description and recommended actions
func (c *LymphnodeClient) GetHomeostaticState() (*HomeostaticStateResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/homeostatic-state", c.baseURL), nil)
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

	var result HomeostaticStateResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
