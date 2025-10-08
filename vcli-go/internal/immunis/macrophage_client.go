package immunis

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

// MacrophageClient provides access to Immunis Macrophage Service for malware phagocytosis
type MacrophageClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// PhagocytoseResponse represents the response from phagocytose endpoint
type PhagocytoseResponse struct {
	Status    string                 `json:"status"`
	Artifact  map[string]interface{} `json:"artifact"`
	Timestamp string                 `json:"timestamp"`
}

// PresentAntigenRequest represents antigen presentation request
type PresentAntigenRequest struct {
	Artifact map[string]interface{} `json:"artifact"`
}

// PresentAntigenResponse represents antigen presentation response
type PresentAntigenResponse struct {
	Status    string `json:"status"`
	Message   string `json:"message"`
	Timestamp string `json:"timestamp"`
}

// CleanupResponse represents cleanup response
type CleanupResponse struct {
	Status           string `json:"status"`
	ArtifactsRemoved int    `json:"artifacts_removed"`
	Timestamp        string `json:"timestamp"`
}

// StatusResponse represents detailed status response
type StatusResponse struct {
	CuckooEnabled           bool   `json:"cuckoo_enabled"`
	KafkaEnabled            bool   `json:"kafka_enabled"`
	ProcessedArtifactsCount int    `json:"processed_artifacts_count"`
	GeneratedSignaturesCount int   `json:"generated_signatures_count"`
	Timestamp               string `json:"timestamp"`
}

// HealthResponse represents health check response
type HealthResponse struct {
	Status          string `json:"status"`
	Service         string `json:"service"`
	CuckooEnabled   bool   `json:"cuckoo_enabled"`
	KafkaEnabled    bool   `json:"kafka_enabled"`
	ArtifactsCount  int    `json:"artifacts_count"`
	SignaturesCount int    `json:"signatures_count"`
	Timestamp       string `json:"timestamp"`
}

// ArtifactsResponse represents artifacts list response
type ArtifactsResponse struct {
	Status    string                   `json:"status"`
	Artifacts []map[string]interface{} `json:"artifacts"`
	Count     int                      `json:"count"`
	Timestamp string                   `json:"timestamp"`
}

// SignaturesResponse represents signatures list response
type SignaturesResponse struct {
	Status     string                   `json:"status"`
	Signatures []map[string]interface{} `json:"signatures"`
	Count      int                      `json:"count"`
	Timestamp  string                   `json:"timestamp"`
}

// NewMacrophageClient creates a new Macrophage service client
func NewMacrophageClient(endpoint, authToken string) *MacrophageClient {
	return &MacrophageClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 120 * time.Second, // Malware analysis can take time
		},
		authToken: authToken,
	}
}

// Phagocytose uploads and analyzes malware sample
func (c *MacrophageClient) Phagocytose(filePath, malwareFamily string) (*PhagocytoseResponse, error) {
	// Open file
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	// Create multipart form
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add file
	part, err := writer.CreateFormFile("file", filepath.Base(filePath))
	if err != nil {
		return nil, fmt.Errorf("failed to create form file: %w", err)
	}

	if _, err := io.Copy(part, file); err != nil {
		return nil, fmt.Errorf("failed to copy file: %w", err)
	}

	// Add malware_family field
	if err := writer.WriteField("malware_family", malwareFamily); err != nil {
		return nil, fmt.Errorf("failed to write field: %w", err)
	}

	if err := writer.Close(); err != nil {
		return nil, fmt.Errorf("failed to close writer: %w", err)
	}

	// Create request
	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/phagocytose", c.baseURL), body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", writer.FormDataContentType())
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

	var result PhagocytoseResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// PresentAntigen presents antigen to Dendritic Cells
func (c *MacrophageClient) PresentAntigen(artifact map[string]interface{}) (*PresentAntigenResponse, error) {
	req := PresentAntigenRequest{
		Artifact: artifact,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/present_antigen", c.baseURL), bytes.NewBuffer(body))
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

	var result PresentAntigenResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Cleanup removes old artifacts
func (c *MacrophageClient) Cleanup() (*CleanupResponse, error) {
	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/cleanup", c.baseURL), nil)
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

	var result CleanupResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetStatus retrieves detailed service status
func (c *MacrophageClient) GetStatus() (*StatusResponse, error) {
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
func (c *MacrophageClient) Health() (*HealthResponse, error) {
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

// GetArtifacts retrieves list of processed artifacts
func (c *MacrophageClient) GetArtifacts() (*ArtifactsResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/artifacts", c.baseURL), nil)
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

	var result ArtifactsResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetSignatures retrieves list of generated YARA signatures
func (c *MacrophageClient) GetSignatures() (*SignaturesResponse, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/signatures", c.baseURL), nil)
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

	var result SignaturesResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
