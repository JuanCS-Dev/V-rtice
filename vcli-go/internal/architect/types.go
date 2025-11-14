package architect

type AnalyzeResult struct {
	TotalServices   int
	GapsFound       int
	Redundancies    int
	HealthScore     float64
	Recommendations []string
}

type BlueprintRequest struct {
	ServiceName string
	Format      string
}

type BlueprintResult struct {
	ServiceName string
	Blueprint   string
}

type StatusResult struct {
	Status            string
	AnalysesCompleted int
}
