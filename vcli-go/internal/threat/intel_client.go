package threat

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type IntelClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

type ThreatIntelQuery struct {
	Indicator     string                 `json:"indicator"`
	IndicatorType string                 `json:"indicator_type"`
	Context       map[string]interface{} `json:"context,omitempty"`
}

type ThreatIntelResponse struct {
	Indicator      string                 `json:"indicator"`
	ThreatScore    float64                `json:"threat_score"`
	Classification string                 `json:"classification"`
	Sources        []string               `json:"sources"`
	TTPs           []string               `json:"ttps,omitempty"`
	AdditionalInfo map[string]interface{} `json:"additional_info,omitempty"`
}

func NewIntelClient(endpoint, authToken string) *IntelClient {
	return &IntelClient{
		baseURL:    endpoint,
		httpClient: &http.Client{Timeout: 60 * time.Second},
		authToken:  authToken,
	}
}

func (c *IntelClient) QueryThreatIntel(indicator, indicatorType string, context map[string]interface{}) (*ThreatIntelResponse, error) {
	req := ThreatIntelQuery{Indicator: indicator, IndicatorType: indicatorType, Context: context}
	body, _ := json.Marshal(req)

	httpReq, _ := http.NewRequest("POST", fmt.Sprintf("%s/query_threat_intel", c.baseURL), bytes.NewBuffer(body))
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

	var result ThreatIntelResponse
	json.NewDecoder(resp.Body).Decode(&result)
	return &result, nil
}

func (c *IntelClient) GetStatus() (map[string]interface{}, error) {
	httpReq, _ := http.NewRequest("GET", fmt.Sprintf("%s/threat_intel_status", c.baseURL), nil)
	if c.authToken != "" {
		httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authToken))
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}

func (c *IntelClient) Health() (map[string]string, error) {
	httpReq, _ := http.NewRequest("GET", fmt.Sprintf("%s/health", c.baseURL), nil)
	resp, _ := c.httpClient.Do(httpReq)
	defer resp.Body.Close()

	var result map[string]string
	json.NewDecoder(resp.Body).Decode(&result)
	return result, nil
}
