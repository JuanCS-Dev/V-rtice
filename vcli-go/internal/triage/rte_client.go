package triage

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type RTEClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// Request/Response types
type RealTimeCommand struct {
	CommandName string                 `json:"command_name"`
	Parameters  map[string]interface{} `json:"parameters"`
	Priority    int                    `json:"priority"`
}

type CommandExecutionResponse struct {
	Status          string                 `json:"status"`
	Timestamp       string                 `json:"timestamp"`
	ExecutionResult map[string]interface{} `json:"execution_result"`
}

type DataStreamIngest struct {
	StreamID string                 `json:"stream_id"`
	Data     map[string]interface{} `json:"data"`
	DataType string                 `json:"data_type"`
}

type DataStreamResponse struct {
	Status           string                 `json:"status"`
	Timestamp        string                 `json:"timestamp"`
	FusedDataSummary map[string]interface{} `json:"fused_data_summary"`
	MLPrediction     map[string]interface{} `json:"ml_prediction"`
	HyperscanMatches interface{}            `json:"hyperscan_matches"`
	PlaybookAction   map[string]interface{} `json:"playbook_action"`
}

type HealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

func NewRTEClient(endpoint, authToken string) *RTEClient {
	return &RTEClient{
		baseURL:    endpoint,
		httpClient: &http.Client{Timeout: 120 * time.Second},
		authToken:  authToken,
	}
}

func (c *RTEClient) ExecuteCommand(cmd RealTimeCommand) (*CommandExecutionResponse, error) {
	body, err := json.Marshal(cmd)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal command: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/execute_realtime_command", c.baseURL), bytes.NewBuffer(body))
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

	var result CommandExecutionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *RTEClient) IngestDataStream(ingest DataStreamIngest) (*DataStreamResponse, error) {
	body, err := json.Marshal(ingest)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal ingest request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/ingest_data_stream", c.baseURL), bytes.NewBuffer(body))
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

	var result DataStreamResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return &result, nil
}

func (c *RTEClient) Health() (*HealthResponse, error) {
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
