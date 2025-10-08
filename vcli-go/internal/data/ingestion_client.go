package data

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type IngestionClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// Enums
type JobStatus string

const (
	JobStatusPending   JobStatus = "pending"
	JobStatusRunning   JobStatus = "running"
	JobStatusCompleted JobStatus = "completed"
	JobStatusFailed    JobStatus = "failed"
	JobStatusCancelled JobStatus = "cancelled"
)

type DataSource string

const (
	DataSourceSinesp        DataSource = "sinesp"
	DataSourcePrisional     DataSource = "prisional"
	DataSourceAntecedentes  DataSource = "antecedentes"
	DataSourceANPR          DataSource = "anpr"
	DataSourceManual        DataSource = "manual"
)

type EntityType string

const (
	EntityTypePessoa     EntityType = "pessoa"
	EntityTypeVeiculo    EntityType = "veiculo"
	EntityTypeEndereco   EntityType = "endereco"
	EntityTypeOcorrencia EntityType = "ocorrencia"
)

// Request/Response types
type IngestJobRequest struct {
	Source         DataSource             `json:"source"`
	EntityType     *EntityType            `json:"entity_type,omitempty"`
	Filters        map[string]interface{} `json:"filters"`
	LoadToPostgres bool                   `json:"load_to_postgres"`
	LoadToNeo4j    bool                   `json:"load_to_neo4j"`
	Metadata       map[string]interface{} `json:"metadata"`
}

type IngestJobResponse struct {
	JobID     string     `json:"job_id"`
	Status    JobStatus  `json:"status"`
	Source    DataSource `json:"source"`
	CreatedAt string     `json:"created_at"`
	Message   string     `json:"message"`
}

type IngestJobStatus struct {
	JobID            string                 `json:"job_id"`
	Status           JobStatus              `json:"status"`
	Source           DataSource             `json:"source"`
	CreatedAt        string                 `json:"created_at"`
	StartedAt        *string                `json:"started_at,omitempty"`
	CompletedAt      *string                `json:"completed_at,omitempty"`
	RecordsProcessed int                    `json:"records_processed"`
	RecordsFailed    int                    `json:"records_failed"`
	ErrorMessage     *string                `json:"error_message,omitempty"`
	Metadata         map[string]interface{} `json:"metadata"`
}

type TriggerIngestRequest struct {
	Source     DataSource             `json:"source"`
	EntityType *EntityType            `json:"entity_type,omitempty"`
	Filters    map[string]interface{} `json:"filters"`
}

type HealthResponse struct {
	Status          string `json:"status"`
	Service         string `json:"service"`
	Version         string `json:"version"`
	PostgresHealthy bool   `json:"postgres_healthy"`
	Neo4jHealthy    bool   `json:"neo4j_healthy"`
	ActiveJobs      int    `json:"active_jobs"`
}

type DataSourceInfo struct {
	Enabled     bool     `json:"enabled"`
	Description string   `json:"description"`
	Entities    []string `json:"entities"`
	URL         string   `json:"url,omitempty"`
	Status      string   `json:"status,omitempty"`
}

type SourcesResponse struct {
	Sources map[string]DataSourceInfo `json:"sources"`
	Total   int                       `json:"total"`
	Enabled int                       `json:"enabled"`
}

type EntityInfo struct {
	Description   string   `json:"description"`
	Fields        []string `json:"fields"`
	PrimaryKey    string   `json:"primary_key"`
	Relationships []string `json:"relationships"`
}

type EntitiesResponse struct {
	Entities map[string]EntityInfo `json:"entities"`
	Total    int                   `json:"total"`
}

type StatisticsResponse struct {
	TotalJobs        int                `json:"total_jobs"`
	ByStatus         map[string]int     `json:"by_status"`
	BySource         map[string]int     `json:"by_source"`
	RecordsProcessed int                `json:"records_processed"`
	RecordsFailed    int                `json:"records_failed"`
	ActiveJobs       int                `json:"active_jobs"`
}

type CancelJobResponse struct {
	JobID   string `json:"job_id"`
	Status  string `json:"status"`
	Message string `json:"message"`
}

func NewIngestionClient(endpoint, authToken string) *IngestionClient {
	return &IngestionClient{
		baseURL:    endpoint,
		httpClient: &http.Client{Timeout: 120 * time.Second},
		authToken:  authToken,
	}
}

func (c *IngestionClient) CreateJob(req IngestJobRequest) (*IngestJobResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal job request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/jobs", c.baseURL), bytes.NewBuffer(body))
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

	var result IngestJobResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *IngestionClient) GetJobStatus(jobID string) (*IngestJobStatus, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/jobs/%s", c.baseURL, jobID), nil)
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

	var result IngestJobStatus
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *IngestionClient) ListJobs(status *JobStatus, limit int) ([]IngestJobStatus, error) {
	url := fmt.Sprintf("%s/jobs?limit=%d", c.baseURL, limit)
	if status != nil {
		url = fmt.Sprintf("%s&status=%s", url, *status)
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

	var result []IngestJobStatus
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result, nil
}

func (c *IngestionClient) TriggerIngestion(req TriggerIngestRequest) (*IngestJobResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal trigger request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/ingest/trigger", c.baseURL), bytes.NewBuffer(body))
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

	var result IngestJobResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *IngestionClient) ListSources() (*SourcesResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/sources", c.baseURL), nil)
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

	var result SourcesResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *IngestionClient) ListEntityTypes() (*EntitiesResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/entities", c.baseURL), nil)
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

	var result EntitiesResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *IngestionClient) GetStatistics() (*StatisticsResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/stats", c.baseURL), nil)
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

func (c *IngestionClient) CancelJob(jobID string) (*CancelJobResponse, error) {
	httpReq, err := http.NewRequest("DELETE", fmt.Sprintf("%s/jobs/%s", c.baseURL, jobID), nil)
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

	var result CancelJobResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *IngestionClient) Health() (*HealthResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/health", c.baseURL), nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}
