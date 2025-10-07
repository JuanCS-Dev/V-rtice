package observability

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

// PrometheusClient provides access to Prometheus HTTP API
type PrometheusClient struct {
	baseURL    string
	httpClient *http.Client
}

// NewPrometheusClient creates a new Prometheus client
func NewPrometheusClient(baseURL string) *PrometheusClient {
	return &PrometheusClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// ============================================================
// Query API
// ============================================================

// QueryResult represents a Prometheus query result
type QueryResult struct {
	Status string      `json:"status"`
	Data   QueryData   `json:"data"`
	Error  string      `json:"error,omitempty"`
	ErrorType string   `json:"errorType,omitempty"`
}

// QueryData contains the actual query results
type QueryData struct {
	ResultType string        `json:"resultType"`
	Result     []MetricValue `json:"result"`
}

// MetricValue represents a single metric value
type MetricValue struct {
	Metric map[string]string `json:"metric"`
	Value  []interface{}     `json:"value,omitempty"`   // [timestamp, value]
	Values [][]interface{}   `json:"values,omitempty"`  // [[timestamp, value], ...]
}

// QueryInstant performs an instant query at a single point in time
func (c *PrometheusClient) QueryInstant(ctx context.Context, query string, timestamp *time.Time) (*QueryResult, error) {
	// Build URL
	u, err := url.Parse(fmt.Sprintf("%s/api/v1/query", c.baseURL))
	if err != nil {
		return nil, fmt.Errorf("invalid base URL: %w", err)
	}

	// Add query parameters
	q := u.Query()
	q.Set("query", query)
	if timestamp != nil {
		q.Set("time", fmt.Sprintf("%d", timestamp.Unix()))
	}
	u.RawQuery = q.Encode()

	// Execute request
	req, err := http.NewRequestWithContext(ctx, "GET", u.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Parse response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	var result QueryResult
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	if result.Status != "success" {
		return nil, fmt.Errorf("query failed: %s - %s", result.ErrorType, result.Error)
	}

	return &result, nil
}

// QueryRange performs a range query over a time period
func (c *PrometheusClient) QueryRange(ctx context.Context, query string, start, end time.Time, step string) (*QueryResult, error) {
	// Build URL
	u, err := url.Parse(fmt.Sprintf("%s/api/v1/query_range", c.baseURL))
	if err != nil {
		return nil, fmt.Errorf("invalid base URL: %w", err)
	}

	// Add query parameters
	q := u.Query()
	q.Set("query", query)
	q.Set("start", fmt.Sprintf("%d", start.Unix()))
	q.Set("end", fmt.Sprintf("%d", end.Unix()))
	q.Set("step", step)
	u.RawQuery = q.Encode()

	// Execute request
	req, err := http.NewRequestWithContext(ctx, "GET", u.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Parse response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	var result QueryResult
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	if result.Status != "success" {
		return nil, fmt.Errorf("query failed: %s - %s", result.ErrorType, result.Error)
	}

	return &result, nil
}

// ============================================================
// Metadata API
// ============================================================

// LabelValues represents label values response
type LabelValues struct {
	Status string   `json:"status"`
	Data   []string `json:"data"`
}

// SeriesResult represents series metadata
type SeriesResult struct {
	Status string              `json:"status"`
	Data   []map[string]string `json:"data"`
}

// GetLabelValues retrieves all values for a specific label
func (c *PrometheusClient) GetLabelValues(ctx context.Context, labelName string) ([]string, error) {
	// Build URL
	u := fmt.Sprintf("%s/api/v1/label/%s/values", c.baseURL, url.PathEscape(labelName))

	// Execute request
	req, err := http.NewRequestWithContext(ctx, "GET", u, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Parse response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	var result LabelValues
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	if result.Status != "success" {
		return nil, fmt.Errorf("query failed")
	}

	return result.Data, nil
}

// GetSeries retrieves time series matching label selectors
func (c *PrometheusClient) GetSeries(ctx context.Context, matches []string, start, end *time.Time) ([]map[string]string, error) {
	// Build URL
	u, err := url.Parse(fmt.Sprintf("%s/api/v1/series", c.baseURL))
	if err != nil {
		return nil, fmt.Errorf("invalid base URL: %w", err)
	}

	// Add query parameters
	q := u.Query()
	for _, match := range matches {
		q.Add("match[]", match)
	}
	if start != nil {
		q.Set("start", fmt.Sprintf("%d", start.Unix()))
	}
	if end != nil {
		q.Set("end", fmt.Sprintf("%d", end.Unix()))
	}
	u.RawQuery = q.Encode()

	// Execute request
	req, err := http.NewRequestWithContext(ctx, "GET", u.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Parse response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	var result SeriesResult
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	if result.Status != "success" {
		return nil, fmt.Errorf("query failed")
	}

	return result.Data, nil
}

// ============================================================
// Health & Status
// ============================================================

// TargetsResult represents targets API response
type TargetsResult struct {
	Status string       `json:"status"`
	Data   TargetsData  `json:"data"`
}

// TargetsData contains active and dropped targets
type TargetsData struct {
	ActiveTargets  []Target `json:"activeTargets"`
	DroppedTargets []Target `json:"droppedTargets"`
}

// Target represents a single scrape target
type Target struct {
	DiscoveredLabels map[string]string `json:"discoveredLabels"`
	Labels           map[string]string `json:"labels"`
	ScrapePool       string            `json:"scrapePool"`
	ScrapeURL        string            `json:"scrapeUrl"`
	Health           string            `json:"health"`
	LastError        string            `json:"lastError,omitempty"`
	LastScrape       time.Time         `json:"lastScrape"`
	LastScrapeDuration float64         `json:"lastScrapeDuration"`
}

// GetTargets retrieves scrape targets
func (c *PrometheusClient) GetTargets(ctx context.Context, state string) (*TargetsData, error) {
	// Build URL
	u, err := url.Parse(fmt.Sprintf("%s/api/v1/targets", c.baseURL))
	if err != nil {
		return nil, fmt.Errorf("invalid base URL: %w", err)
	}

	// Add state filter if specified
	if state != "" {
		q := u.Query()
		q.Set("state", state)
		u.RawQuery = q.Encode()
	}

	// Execute request
	req, err := http.NewRequestWithContext(ctx, "GET", u.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Parse response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	var result TargetsResult
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	if result.Status != "success" {
		return nil, fmt.Errorf("query failed")
	}

	return &result.Data, nil
}

// ============================================================
// Utility Methods
// ============================================================

// SetTimeout updates the HTTP client timeout
func (c *PrometheusClient) SetTimeout(timeout time.Duration) {
	c.httpClient.Timeout = timeout
}

// Close closes idle connections
func (c *PrometheusClient) Close() {
	c.httpClient.CloseIdleConnections()
}
