package hunting

// ============================================================================
// APT PREDICTION
// ============================================================================

type APTPredictRequest struct {
	Target     string
	Confidence float64
}

type APTPredictResult struct {
	Target       string
	PredictionID string
	Threats      []APTThreat
	OverallRisk  string
}

type APTThreat struct {
	Actor       string
	Campaign    string
	Probability float64
	Tactics     string
}

type APTProfileRequest struct {
	Actor string
}

type APTProfileResult struct {
	Actor            string
	Aliases          string
	Origin           string
	ActiveSince      string
	Sophistication   string
	KnownTactics     []MITRETactic
	TargetedSectors  []string
}

type MITRETactic struct {
	ID          string
	Description string
}

// ============================================================================
// THREAT HUNTING
// ============================================================================

type HuntStartRequest struct {
	Query     string
	Timerange string
	Scope     string
}

type HuntStartResult struct {
	HuntID          string
	Query           string
	Scope           string
	Status          string
	Progress        float64
	InitialFindings []Finding
}

type Finding struct {
	Description string
	Severity    int
}

type HuntResultsRequest struct {
	HuntID string
}

type HuntResultsResult struct {
	HuntID            string
	Status            string
	Findings          []DetailedFinding
	HighSeverityCount int
}

type DetailedFinding struct {
	Type        string
	Description string
	Severity    int
	Confidence  float64
}

// ============================================================================
// ANOMALY PREDICTION
// ============================================================================

type AnomalyPredictRequest struct {
	Target    string
	Timerange string
	Mode      string
}

type AnomalyPredictResult struct {
	Target             string
	PredictionHorizon  string
	ModelConfidence    float64
	Predictions        []AnomalyPrediction
}

type AnomalyPrediction struct {
	TimeWindow  string
	Type        string
	Probability float64
	Impact      string
}

// ============================================================================
// ATTACK SURFACE ANALYSIS
// ============================================================================

type SurfaceAnalyzeRequest struct {
	Target string
	Scope  string
}

type SurfaceAnalyzeResult struct {
	Target          string
	Scope           string
	TotalAssets     int
	ExposedServices int
	RiskScore       float64
	ExposurePoints  []ExposurePoint
	Recommendations []string
}

type ExposurePoint struct {
	Asset     string
	Type      string
	Exposure  string
	RiskLevel string
}

type SurfaceMapRequest struct {
	Target string
}

type SurfaceMapResult struct {
	MapID            string
	Nodes            int
	Edges            int
	CriticalPaths    int
	VisualizationURL string
}
