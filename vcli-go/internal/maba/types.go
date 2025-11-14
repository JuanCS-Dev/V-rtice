package maba

// Navigation
type NavigateRequest struct {
	URL    string
	Action string
	Wait   bool
}

type NavigateResult struct {
	URL           string
	Title         string
	LoadTime      int
	Status        string
	ExtractedData map[string]interface{}
}

// Extraction
type ExtractRequest struct {
	URL   string
	Query string
}

type ExtractResult struct {
	URL  string
	Data []map[string]interface{}
}

// Sessions
type SessionListResult struct {
	Sessions []BrowserSession
}

type BrowserSession struct {
	ID            string
	CurrentURL    string
	Duration      int
	ResourceUsage int
	Status        string
}

// Cognitive Map
type MapQueryRequest struct {
	Domain string
}

type MapQueryResult struct {
	Domain      string
	PageCount   int
	PathCount   int
	Confidence  float64
	CommonPaths []NavigationPath
}

type NavigationPath struct {
	Path  string
	Usage int
}

type MapStatsResult struct {
	TotalDomains      int
	TotalPages        int
	TotalPaths        int
	TotalInteractions int
	TopDomains        []DomainStats
}

type DomainStats struct {
	Domain string
	Visits int
}

// Tools
type ToolListResult struct {
	Tools []MABATool
}

type MABATool struct {
	Name        string
	Description string
	Status      string
	UsageCount  int
}

// Status
type StatusResult struct {
	Status          string
	ActiveSessions  int
	MapSize         int
	ResourceUsage   float64
	ToolsRegistered int
}
