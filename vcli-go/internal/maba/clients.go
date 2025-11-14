package maba

import (
	"context"
	"fmt"
	"net/url"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

// MABAClient is a production-ready client for the MABA (MAXIMUS Browser Agent) service
// Implements Anthropic patterns: conservative defaults, proper error handling, session management
type MABAClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

// NewMABAClient creates a new MABA client with the given endpoint
// If endpoint is empty, uses the configured default from config
//
// Anthropic Pattern: Conservative constructor with sensible defaults
func NewMABAClient(endpoint string) *MABAClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("maba")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &MABAClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

// CreateSession creates a new browser session
//
// Anthropic Pattern: Explicit session management, fail-fast on errors
func (c *MABAClient) CreateSession(ctx context.Context, req *SessionRequest) (*SessionResponse, error) {
	// Validate request
	if req == nil {
		return nil, fmt.Errorf("session request cannot be nil")
	}

	// Set conservative defaults if not provided
	if req.ViewportWidth == 0 {
		req.ViewportWidth = 1920
	}
	if req.ViewportHeight == 0 {
		req.ViewportHeight = 1080
	}

	var result SessionResponse
	err := c.httpClient.PostJSONResponse(ctx, "/sessions", req, &result)
	if err != nil {
		return nil, fmt.Errorf("create session failed: %w", err)
	}

	return &result, nil
}

// CloseSession closes an existing browser session
//
// Anthropic Pattern: Explicit cleanup, graceful error handling
func (c *MABAClient) CloseSession(ctx context.Context, sessionID string) error {
	if sessionID == "" {
		return fmt.Errorf("session_id cannot be empty")
	}

	// DELETE /sessions/{session_id}
	endpoint := fmt.Sprintf("/sessions/%s", url.PathEscape(sessionID))

	// Use Delete method
	_, err := c.httpClient.Delete(ctx, endpoint)
	if err != nil {
		return fmt.Errorf("close session failed: %w", err)
	}

	return nil
}

// ============================================================================
// NAVIGATION
// ============================================================================

// Navigate navigates to a URL in the specified session
//
// Anthropic Pattern: Context-aware, timeout handling via context
func (c *MABAClient) Navigate(ctx context.Context, sessionID string, req *NavigateRequest) (*NavigateResult, error) {
	if sessionID == "" {
		return nil, fmt.Errorf("session_id cannot be empty")
	}
	if req == nil {
		return nil, fmt.Errorf("navigate request cannot be nil")
	}
	if req.URL == "" {
		return nil, fmt.Errorf("URL cannot be empty")
	}

	// Set conservative defaults
	if req.WaitUntil == "" {
		req.WaitUntil = "networkidle"
	}
	if req.TimeoutMs == 0 {
		req.TimeoutMs = 30000 // 30 seconds default
	}

	// Backend expects session_id as query parameter
	endpoint := fmt.Sprintf("/navigate?session_id=%s", url.QueryEscape(sessionID))

	var result NavigateResult
	err := c.httpClient.PostJSONResponse(ctx, endpoint, req, &result)
	if err != nil {
		return nil, fmt.Errorf("navigate failed: %w", err)
	}

	// Check for application-level errors
	if result.Error != nil && *result.Error != "" {
		return &result, fmt.Errorf("navigation error: %s", *result.Error)
	}

	return &result, nil
}

// ============================================================================
// BROWSER ACTIONS
// ============================================================================

// Click clicks an element in the specified session
//
// Anthropic Pattern: Explicit parameters, clear error messages
func (c *MABAClient) Click(ctx context.Context, sessionID string, req *ClickRequest) (*ActionResponse, error) {
	if sessionID == "" {
		return nil, fmt.Errorf("session_id cannot be empty")
	}
	if req == nil {
		return nil, fmt.Errorf("click request cannot be nil")
	}
	if req.Selector == "" {
		return nil, fmt.Errorf("selector cannot be empty")
	}

	// Set conservative defaults
	if req.Button == "" {
		req.Button = "left"
	}
	if req.ClickCount == 0 {
		req.ClickCount = 1
	}
	if req.TimeoutMs == 0 {
		req.TimeoutMs = 30000
	}

	endpoint := fmt.Sprintf("/click?session_id=%s", url.QueryEscape(sessionID))

	var result ActionResponse
	err := c.httpClient.PostJSONResponse(ctx, endpoint, req, &result)
	if err != nil {
		return nil, fmt.Errorf("click failed: %w", err)
	}

	if result.Error != nil && *result.Error != "" {
		return &result, fmt.Errorf("click error: %s", *result.Error)
	}

	return &result, nil
}

// Type types text into an element in the specified session
func (c *MABAClient) Type(ctx context.Context, sessionID string, req *TypeRequest) (*ActionResponse, error) {
	if sessionID == "" {
		return nil, fmt.Errorf("session_id cannot be empty")
	}
	if req == nil {
		return nil, fmt.Errorf("type request cannot be nil")
	}
	if req.Selector == "" {
		return nil, fmt.Errorf("selector cannot be empty")
	}

	// DelayMs default is 0 (no delay between keystrokes)

	endpoint := fmt.Sprintf("/type?session_id=%s", url.QueryEscape(sessionID))

	var result ActionResponse
	err := c.httpClient.PostJSONResponse(ctx, endpoint, req, &result)
	if err != nil {
		return nil, fmt.Errorf("type failed: %w", err)
	}

	if result.Error != nil && *result.Error != "" {
		return &result, fmt.Errorf("type error: %s", *result.Error)
	}

	return &result, nil
}

// Screenshot takes a screenshot in the specified session
func (c *MABAClient) Screenshot(ctx context.Context, sessionID string, req *ScreenshotRequest) (*ActionResponse, error) {
	if sessionID == "" {
		return nil, fmt.Errorf("session_id cannot be empty")
	}
	if req == nil {
		return nil, fmt.Errorf("screenshot request cannot be nil")
	}

	// Set default format
	if req.Format == "" {
		req.Format = "png"
	}

	endpoint := fmt.Sprintf("/screenshot?session_id=%s", url.QueryEscape(sessionID))

	var result ActionResponse
	err := c.httpClient.PostJSONResponse(ctx, endpoint, req, &result)
	if err != nil {
		return nil, fmt.Errorf("screenshot failed: %w", err)
	}

	if result.Error != nil && *result.Error != "" {
		return &result, fmt.Errorf("screenshot error: %s", *result.Error)
	}

	return &result, nil
}

// ============================================================================
// DATA EXTRACTION
// ============================================================================

// Extract extracts data from the current page in the specified session
//
// Anthropic Pattern: Defensive validation, clear error messages
func (c *MABAClient) Extract(ctx context.Context, sessionID string, req *ExtractRequest) (*ExtractResult, error) {
	if sessionID == "" {
		return nil, fmt.Errorf("session_id cannot be empty")
	}
	if req == nil {
		return nil, fmt.Errorf("extract request cannot be nil")
	}
	if len(req.Selectors) == 0 {
		return nil, fmt.Errorf("selectors cannot be empty")
	}

	endpoint := fmt.Sprintf("/extract?session_id=%s", url.QueryEscape(sessionID))

	var result ExtractResult
	err := c.httpClient.PostJSONResponse(ctx, endpoint, req, &result)
	if err != nil {
		return nil, fmt.Errorf("extract failed: %w", err)
	}

	if result.Error != nil && *result.Error != "" {
		return &result, fmt.Errorf("extract error: %s", *result.Error)
	}

	return &result, nil
}

// ============================================================================
// COGNITIVE MAP
// ============================================================================

// QueryCognitiveMap queries the cognitive map for learned patterns
//
// Anthropic Pattern: Domain-specific knowledge encapsulation
func (c *MABAClient) QueryCognitiveMap(ctx context.Context, req *CognitiveMapQueryRequest) (*CognitiveMapQueryResponse, error) {
	if req == nil {
		return nil, fmt.Errorf("cognitive map query request cannot be nil")
	}
	if req.QueryType == "" {
		return nil, fmt.Errorf("query_type cannot be empty")
	}

	// Validate query type
	validTypes := map[string]bool{
		"find_element": true,
		"get_path":     true,
	}
	if !validTypes[req.QueryType] {
		return nil, fmt.Errorf("invalid query_type: %s (must be find_element or get_path)", req.QueryType)
	}

	var result CognitiveMapQueryResponse
	err := c.httpClient.PostJSONResponse(ctx, "/cognitive-map/query", req, &result)
	if err != nil {
		return nil, fmt.Errorf("cognitive map query failed: %w", err)
	}

	return &result, nil
}

// ============================================================================
// STATS & HEALTH
// ============================================================================

// GetStats retrieves service statistics
//
// Anthropic Pattern: Observable services, health monitoring
func (c *MABAClient) GetStats(ctx context.Context) (*StatsResult, error) {
	var result StatsResult
	err := c.httpClient.GetJSON(ctx, "/stats", &result)
	if err != nil {
		return nil, fmt.Errorf("get stats failed: %w", err)
	}

	return &result, nil
}
