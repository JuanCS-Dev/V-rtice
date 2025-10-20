package threat

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type VulnClient struct {
	baseURL    string
	httpClient *http.Client
	authToken  string
}

type VulnQuery struct {
	CVE     string                 `json:"cve,omitempty"`
	Product string                 `json:"product,omitempty"`
	Version string                 `json:"version,omitempty"`
	Context map[string]interface{} `json:"context,omitempty"`
}

type VulnResponse struct {
	CVE         string   `json:"cve"`
	Severity    string   `json:"severity"`
	Score       float64  `json:"score"`
	Description string   `json:"description"`
	Affected    []string `json:"affected"`
	References  []string `json:"references"`
}

func NewVulnClient(endpoint, authToken string) *VulnClient {
	return &VulnClient{
		baseURL:    endpoint,
		httpClient: &http.Client{Timeout: 60 * time.Second},
		authToken:  authToken,
	}
}

func (c *VulnClient) QueryVulnerability(cve, product, version string, context map[string]interface{}) (*VulnResponse, error) {
	req := VulnQuery{CVE: cve, Product: product, Version: version, Context: context}
	body, _ := json.Marshal(req)

	httpReq, _ := http.NewRequest("POST", fmt.Sprintf("%s/query_vulnerability", c.baseURL), bytes.NewBuffer(body))
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

	var result VulnResponse
	json.NewDecoder(resp.Body).Decode(&result)
	return &result, nil
}

func (c *VulnClient) Health() (map[string]string, error) {
	httpReq, _ := http.NewRequest("GET", fmt.Sprintf("%s/health", c.baseURL), nil)
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
