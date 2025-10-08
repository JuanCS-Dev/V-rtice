package offensive

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type WebAttackClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

type AttackRequest struct {
	TargetURL    string                 `json:"target_url"`
	AttackType   string                 `json:"attack_type"`
	Parameters   map[string]interface{} `json:"parameters,omitempty"`
	Intensity    string                 `json:"intensity,omitempty"`
}

type AttackResponse struct {
	AttackID       string                 `json:"attack_id"`
	Status         string                 `json:"status"`
	Vulnerabilities []string              `json:"vulnerabilities"`
	Findings       map[string]interface{} `json:"findings"`
	Timestamp      string                 `json:"timestamp"`
}

func NewWebAttackClient(endpoint, authToken string) *WebAttackClient {
	return &WebAttackClient{
		baseURL:    endpoint,
		httpClient: &http.Client{Timeout: 120 * time.Second},
		authToken:  authToken,
	}
}

func (c *WebAttackClient) LaunchAttack(targetURL, attackType string, parameters map[string]interface{}) (*AttackResponse, error) {
	req := AttackRequest{TargetURL: targetURL, AttackType: attackType, Parameters: parameters}
	body, _ := json.Marshal(req)

	httpReq, _ := http.NewRequest("POST", fmt.Sprintf("%s/launch_attack", c.baseURL), bytes.NewBuffer(body))
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

	var result AttackResponse
	json.NewDecoder(resp.Body).Decode(&result)
	return &result, nil
}

func (c *WebAttackClient) GetAttackStatus(attackID string) (*AttackResponse, error) {
	httpReq, _ := http.NewRequest("GET", fmt.Sprintf("%s/attack_status/%s", c.baseURL, attackID), nil)
	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result AttackResponse
	json.NewDecoder(resp.Body).Decode(&result)
	return &result, nil
}

func (c *WebAttackClient) Health() (map[string]string, error) {
	httpReq, _ := http.NewRequest("GET", fmt.Sprintf("%s/health", c.baseURL), nil)
	resp, _ := c.httpClient.Do(httpReq)
	defer resp.Body.Close()

	var result map[string]string
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}
