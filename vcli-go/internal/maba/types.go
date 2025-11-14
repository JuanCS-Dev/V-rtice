package maba

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

// SessionRequest represents a request to create a browser session
type SessionRequest struct {
	Headless       bool    `json:"headless"`
	ViewportWidth  int     `json:"viewport_width"`
	ViewportHeight int     `json:"viewport_height"`
	UserAgent      *string `json:"user_agent,omitempty"`
}

// SessionResponse represents the response from creating a session
type SessionResponse struct {
	SessionID string `json:"session_id"`
	Status    string `json:"status"`
}

// ============================================================================
// NAVIGATION
// ============================================================================

// NavigateRequest represents a request to navigate to a URL
type NavigateRequest struct {
	URL       string `json:"url"`
	WaitUntil string `json:"wait_until"` // networkidle, load, domcontentloaded
	TimeoutMs int    `json:"timeout_ms"`
}

// NavigateResult represents the result of navigation
type NavigateResult struct {
	Status           string                 `json:"status"`
	Result           map[string]interface{} `json:"result,omitempty"`
	Error            *string                `json:"error,omitempty"`
	ExecutionTimeMs  float64                `json:"execution_time_ms"`
}

// ============================================================================
// BROWSER ACTIONS
// ============================================================================

// ClickRequest represents a request to click an element
type ClickRequest struct {
	Selector   string `json:"selector"`
	Button     string `json:"button"`      // left, right, middle
	ClickCount int    `json:"click_count"` // number of clicks
	TimeoutMs  int    `json:"timeout_ms"`
}

// TypeRequest represents a request to type text
type TypeRequest struct {
	Selector string `json:"selector"`
	Text     string `json:"text"`
	DelayMs  int    `json:"delay_ms"` // delay between keypresses
}

// ScreenshotRequest represents a request to take a screenshot
type ScreenshotRequest struct {
	FullPage bool    `json:"full_page"`
	Selector *string `json:"selector,omitempty"`
	Format   string  `json:"format"` // png, jpeg
}

// ActionResponse represents a generic browser action response
type ActionResponse struct {
	Status          string                 `json:"status"`
	Result          map[string]interface{} `json:"result,omitempty"`
	Error           *string                `json:"error,omitempty"`
	ExecutionTimeMs float64                `json:"execution_time_ms"`
}

// ============================================================================
// DATA EXTRACTION
// ============================================================================

// ExtractRequest represents a request to extract data from a page
type ExtractRequest struct {
	Selectors  map[string]string `json:"selectors"`   // field_name -> css_selector
	ExtractAll bool              `json:"extract_all"` // extract all matching elements
}

// ExtractResult represents the result of data extraction
type ExtractResult struct {
	Status          string                 `json:"status"`
	Result          map[string]interface{} `json:"result,omitempty"`
	Error           *string                `json:"error,omitempty"`
	ExecutionTimeMs float64                `json:"execution_time_ms"`
}

// ============================================================================
// COGNITIVE MAP
// ============================================================================

// CognitiveMapQueryRequest represents a query to the cognitive map
type CognitiveMapQueryRequest struct {
	QueryType  string                 `json:"query_type"` // find_element, get_path
	Parameters map[string]interface{} `json:"parameters"`
}

// CognitiveMapQueryResponse represents the cognitive map query response
type CognitiveMapQueryResponse struct {
	Found      bool                   `json:"found"`
	Result     map[string]interface{} `json:"result,omitempty"`
	Confidence float64                `json:"confidence"`
}

// ============================================================================
// STATS & HEALTH
// ============================================================================

// StatsResult represents MABA service statistics
type StatsResult struct {
	CognitiveMap   map[string]interface{} `json:"cognitive_map"`
	Browser        map[string]interface{} `json:"browser"`
	UptimeSeconds  float64                `json:"uptime_seconds"`
}
