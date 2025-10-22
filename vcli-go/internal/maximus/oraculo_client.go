package maximus

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

// OraculoClient provides access to Maximus Oraculo Service for predictions and code analysis
type OraculoClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// PredictionRequest represents a request for predictive analysis
type PredictionRequest struct {
	Data           map[string]interface{} `json:"data"`
	PredictionType string                 `json:"prediction_type"`
	TimeHorizon    string                 `json:"time_horizon"`
}

// PredictionResponse represents the response from prediction
type PredictionResponse struct {
	Status     string                 `json:"status"`
	Timestamp  string                 `json:"timestamp"`
	Prediction map[string]interface{} `json:"prediction"`
}

// CodeAnalysisRequest represents a request for code analysis
type CodeAnalysisRequest struct {
	Code         string `json:"code"`
	Language     string `json:"language"`
	AnalysisType string `json:"analysis_type"`
}

// CodeAnalysisResponse represents the response from code analysis
type CodeAnalysisResponse struct {
	Status         string                 `json:"status"`
	Timestamp      string                 `json:"timestamp"`
	AnalysisResult map[string]interface{} `json:"analysis_result"`
}

// ImplementationRequest represents a request for automated code implementation
type ImplementationRequest struct {
	TaskDescription string                 `json:"task_description"`
	Context         map[string]interface{} `json:"context,omitempty"`
	TargetLanguage  string                 `json:"target_language"`
}

// ImplementationResponse represents the response from auto-implementation
type ImplementationResponse struct {
	Status               string                 `json:"status"`
	Timestamp            string                 `json:"timestamp"`
	ImplementationResult map[string]interface{} `json:"implementation_result"`
}

// NewOraculoClient creates a new Oraculo service client
func NewOraculoClient(endpoint, authToken string) *OraculoClient {
	debug := os.Getenv("VCLI_DEBUG") == "true"

	// Check env var if endpoint not provided
	if endpoint == "" {
		endpoint = os.Getenv("VCLI_ORACULO_ENDPOINT")
		if endpoint == "" {
			endpoint = "http://localhost:8026" // default
		}
	}

	if debug {
		fmt.Fprintf(os.Stderr, "[DEBUG] Oraculo client initialized with endpoint: %s\n", endpoint)
	}

	return &OraculoClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 90 * time.Second, // Code generation can take longer
		},
		authToken: authToken,
	}
}

// Predict generates a predictive insight based on provided data
func (c *OraculoClient) Predict(data map[string]interface{}, predictionType, timeHorizon string) (*PredictionResponse, error) {
	req := PredictionRequest{
		Data:           data,
		PredictionType: predictionType,
		TimeHorizon:    timeHorizon,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/predict", c.baseURL), bytes.NewBuffer(body))
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

	var result PredictionResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// AnalyzeCode analyzes code for vulnerabilities, performance issues, or refactoring opportunities
func (c *OraculoClient) AnalyzeCode(code, language, analysisType string) (*CodeAnalysisResponse, error) {
	req := CodeAnalysisRequest{
		Code:         code,
		Language:     language,
		AnalysisType: analysisType,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/analyze_code", c.baseURL), bytes.NewBuffer(body))
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

	var result CodeAnalysisResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// AutoImplement requests automated code implementation based on task description
func (c *OraculoClient) AutoImplement(taskDesc, targetLang string, context map[string]interface{}) (*ImplementationResponse, error) {
	req := ImplementationRequest{
		TaskDescription: taskDesc,
		Context:         context,
		TargetLanguage:  targetLang,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/auto_implement", c.baseURL), bytes.NewBuffer(body))
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

	var result ImplementationResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Health performs a health check on the Oraculo service
func (c *OraculoClient) Health() (*HealthResponse, error) {
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
