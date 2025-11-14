package nis

// Narratives
type NarrativeRequest struct {
	Service string
	Type    string
	Focus   string
}

type NarrativeResult struct {
	Service         string
	Type            string
	Narrative       string
	KeyInsights     []string
	Recommendations []string
	Cost            float64
	GenerationTime  int
}

type NarrativeListResult struct {
	Narratives []NarrativeSummary
}

type NarrativeSummary struct {
	Service   string
	Type      string
	Timestamp string
	Cost      float64
	Preview   string
}

// Anomaly Detection
type AnomalyRequest struct {
	Service   string
	Metric    string
	Threshold float64
}

type AnomalyResult struct {
	Service   string
	Baseline  float64
	StdDev    float64
	Anomalies []Anomaly
}

type Anomaly struct {
	Timestamp string
	Metric    string
	Value     float64
	ZScore    float64
	Severity  string
}

type BaselineRequest struct {
	Service string
	Metric  string
}

type BaselineResult struct {
	Service   string
	Baselines []BaselineStats
}

type BaselineStats struct {
	Metric     string
	Mean       float64
	StdDev     float64
	WindowSize int
	LastUpdate string
}

// Cost Management
type CostStatusResult struct {
	DailySpent    float64
	DailyLimit    float64
	MonthlySpent  float64
	MonthlyLimit  float64
	TotalRequests int
	AvgCost       float64
}

type CostHistoryResult struct {
	History []CostEntry
}

type CostEntry struct {
	Date       string
	Requests   int
	TotalCost  float64
	AvgCost    float64
}

// Rate Limiting
type RateLimitResult struct {
	HourlyUsed    int
	HourlyLimit   int
	DailyUsed     int
	DailyLimit    int
	MinInterval   int
	NextAvailable int
}

// Status
type StatusResult struct {
	Status              string
	Health              float64
	NarrativesGenerated int
	AnomaliesDetected   int
	TotalCost           float64
}
