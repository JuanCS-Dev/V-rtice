package ethical

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// HSASClient provides access to HSAS Service for human-system alignment
type HSASClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

// HumanFeedback represents human feedback on AI actions/decisions
type HumanFeedback struct {
	FeedbackType    string                 `json:"feedback_type"`
	Context         map[string]interface{} `json:"context"`
	FeedbackDetails string                 `json:"feedback_details"`
	Rating          *int                   `json:"rating,omitempty"`
}

// ExplanationRequest represents a request for AI decision explanation
type ExplanationRequest struct {
	DecisionID string                 `json:"decision_id"`
	Context    map[string]interface{} `json:"context,omitempty"`
}

// FeedbackResponse represents the response from feedback submission
type FeedbackResponse struct {
	Status    string `json:"status"`
	Message   string `json:"message"`
	Timestamp string `json:"timestamp"`
}

// ExplanationResponse represents the AI explanation response
type ExplanationResponse struct {
	Status      string                 `json:"status"`
	DecisionID  string                 `json:"decision_id"`
	Explanation map[string]interface{} `json:"explanation"`
	Timestamp   string                 `json:"timestamp"`
}

// AlignmentStatus represents the current human-system alignment status
type AlignmentStatus struct {
	OverallScore       float64                `json:"overall_score,omitempty"`
	ValueAlignment     float64                `json:"value_alignment,omitempty"`
	IntentAlignment    float64                `json:"intent_alignment,omitempty"`
	EthicalCompliance  float64                `json:"ethical_compliance,omitempty"`
	FeedbackIncorporated int                  `json:"feedback_incorporated,omitempty"`
	LastUpdate         string                 `json:"last_update,omitempty"`
	AdditionalMetrics  map[string]interface{} `json:"additional_metrics,omitempty"`
}

// HSASHealthResponse represents health check response
type HSASHealthResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// NewHSASClient creates a new HSAS service client
func NewHSASClient(endpoint, authToken string) *HSASClient {
	return &HSASClient{
		baseURL: endpoint,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		authToken: authToken,
	}
}

// SubmitFeedback submits human feedback to the HSAS for processing and learning
//
// Parameters:
//   - feedback: Human feedback on AI actions or decisions
//
// Returns confirmation of feedback submission
func (c *HSASClient) SubmitFeedback(feedback HumanFeedback) (*FeedbackResponse, error) {
	body, err := json.Marshal(feedback)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/submit_feedback", c.baseURL), bytes.NewBuffer(body))
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

	var result FeedbackResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// RequestExplanation requests an explanation for a specific AI decision or action
//
// Parameters:
//   - decisionID: The ID of the AI decision to explain
//   - context: Additional context for the explanation request
//
// Returns the AI's explanation
func (c *HSASClient) RequestExplanation(decisionID string, context map[string]interface{}) (*ExplanationResponse, error) {
	req := ExplanationRequest{
		DecisionID: decisionID,
		Context:    context,
	}

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", fmt.Sprintf("%s/request_explanation", c.baseURL), bytes.NewBuffer(body))
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

	var result ExplanationResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetAlignmentStatus retrieves the current human-system alignment status
//
// Returns a summary of the AI's alignment with human values
func (c *HSASClient) GetAlignmentStatus() (*AlignmentStatus, error) {
	httpReq, err := http.NewRequest("GET", fmt.Sprintf("%s/alignment_status", c.baseURL), nil)
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

	var result AlignmentStatus
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// Health performs a health check on the HSAS service
//
// Returns the health status of the service
func (c *HSASClient) Health() (*HSASHealthResponse, error) {
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

	var result HSASHealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
