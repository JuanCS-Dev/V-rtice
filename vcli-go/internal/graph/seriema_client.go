package graph

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type SeriemaClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// Request/Response types for framework operations
type Framework struct {
	Name      string              `json:"name"`
	Arguments []Argument          `json:"arguments"`
	Attacks   []Attack            `json:"attacks"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

type Argument struct {
	ID          string                 `json:"id"`
	Text        string                 `json:"text"`
	Type        string                 `json:"type,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

type Attack struct {
	From string `json:"from"`
	To   string `json:"to"`
	Type string `json:"type,omitempty"`
}

type FrameworkResponse struct {
	FrameworkID string `json:"framework_id"`
	Message     string `json:"message"`
	NodeCount   int    `json:"node_count"`
	EdgeCount   int    `json:"edge_count"`
}

type CentralityResponse struct {
	FrameworkID        string             `json:"framework_id"`
	DegreeCentrality   map[string]float64 `json:"degree_centrality"`
	BetweennessCentrality map[string]float64 `json:"betweenness_centrality"`
	ClosenessCentrality map[string]float64 `json:"closeness_centrality"`
	MostCentral        []string           `json:"most_central"`
}

type PathsRequest struct {
	Source      string `json:"source"`
	Target      string `json:"target"`
	MaxPaths    int    `json:"max_paths,omitempty"`
	CutoffDepth int    `json:"cutoff_depth,omitempty"`
}

type PathsResponse struct {
	FrameworkID string     `json:"framework_id"`
	Source      string     `json:"source"`
	Target      string     `json:"target"`
	Paths       [][]string `json:"paths"`
	PathCount   int        `json:"path_count"`
}

type NeighborhoodResponse struct {
	FrameworkID  string   `json:"framework_id"`
	ArgumentID   string   `json:"argument_id"`
	Predecessors []string `json:"predecessors"`
	Successors   []string `json:"successors"`
	Distance     int      `json:"distance,omitempty"`
}

type CircularArgumentsResponse struct {
	FrameworkID    string     `json:"framework_id"`
	Cycles         [][]string `json:"cycles"`
	CycleCount     int        `json:"cycle_count"`
	HasCircularity bool       `json:"has_circularity"`
}

type StatisticsResponse struct {
	FrameworkID         string             `json:"framework_id"`
	NodeCount           int                `json:"node_count"`
	EdgeCount           int                `json:"edge_count"`
	Density             float64            `json:"density"`
	AveragePathLength   float64            `json:"average_path_length"`
	Diameter            int                `json:"diameter"`
	IsDirected          bool               `json:"is_directed"`
	IsAcyclic           bool               `json:"is_acyclic"`
	StronglyConnectedComponents int        `json:"strongly_connected_components"`
	AdditionalMetrics   map[string]interface{} `json:"additional_metrics,omitempty"`
}

func NewSeriemaClient(endpoint, authToken string) *SeriemaClient {
	return &SeriemaClient{
		baseURL:    endpoint,
		httpClient: &http.Client{Timeout: 60 * time.Second},
		authToken:  authToken,
	}
}

func (c *SeriemaClient) StoreFramework(framework Framework) (*FrameworkResponse, error) {
	body, err := json.Marshal(framework)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal framework: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/framework/store", c.baseURL), bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result FrameworkResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *SeriemaClient) GetFramework(frameworkID string) (*Framework, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/framework/%s", c.baseURL, frameworkID), nil)
	if err != nil {
		return nil, err
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result Framework
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *SeriemaClient) GetCentrality(frameworkID string) (*CentralityResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/framework/%s/centrality", c.baseURL, frameworkID), nil)
	if err != nil {
		return nil, err
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result CentralityResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *SeriemaClient) FindPaths(frameworkID string, pathsReq PathsRequest) (*PathsResponse, error) {
	body, err := json.Marshal(pathsReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal paths request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/framework/%s/paths", c.baseURL, frameworkID), bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result PathsResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *SeriemaClient) GetNeighborhood(frameworkID, argumentID string, distance int) (*NeighborhoodResponse, error) {
	url := fmt.Sprintf("%s/framework/%s/neighborhood/%s", c.baseURL, frameworkID, argumentID)
	if distance > 0 {
		url = fmt.Sprintf("%s?distance=%d", url, distance)
	}

	httpReq, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result NeighborhoodResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *SeriemaClient) GetCircularArguments(frameworkID string) (*CircularArgumentsResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/framework/%s/circular-arguments", c.baseURL, frameworkID), nil)
	if err != nil {
		return nil, err
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result CircularArgumentsResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *SeriemaClient) GetStatistics(frameworkID string) (*StatisticsResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/framework/%s/statistics", c.baseURL, frameworkID), nil)
	if err != nil {
		return nil, err
	}

	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var result StatisticsResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *SeriemaClient) Health() (map[string]string, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/health", c.baseURL), nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]string
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result, nil
}
