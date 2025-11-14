package rte

// Triage
type TriageRequest struct {
	AlertID  string
	Playbook string
	Auto     bool
}

type TriageResult struct {
	AlertID       string
	Verdict       string
	Confidence    float64
	ExecutionTime int
	PlaybookUsed  string
	Actions       []ActionResult
	Reasoning     string
}

type ActionResult struct {
	Action string
	Status string
}

// Fusion Engine
type FusionRequest struct {
	EventID string
}

type FusionResult struct {
	EventID           string
	CorrelatedSources []CorrelatedSource
	CorrelationScore  float64
	Insights          []string
}

type CorrelatedSource struct {
	Name       string
	EventCount int
	Relevance  float64
}

// Fast ML
type PredictRequest struct {
	Data string
}

type PredictResult struct {
	Prediction    string
	Confidence    float64
	InferenceTime int
	Features      []FeatureImportance
}

type FeatureImportance struct {
	Name       string
	Importance float64
}

// Hyperscan
type MatchRequest struct {
	Pattern string
}

type MatchResult struct {
	Pattern  string
	Matches  []PatternMatch
	ScanTime int
}

type PatternMatch struct {
	Position int
	Context  string
}

// Playbooks
type PlaybooksResult struct {
	Playbooks []Playbook
}

type Playbook struct {
	Name        string
	Description string
	AvgExecTime int
	UsageCount  int
}

// Status
type StatusResult struct {
	Status            string
	AvgResponseTime   float64
	TriagesExecuted   int
	ActivePlaybooks   int
	ComponentHealth   []ComponentHealth
}

type ComponentHealth struct {
	Name   string
	Status string
}
