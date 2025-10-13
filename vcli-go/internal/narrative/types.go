package narrative

// ============================================================================
// SHARED TYPES FOR NARRATIVE FILTER SERVICE
// Consolidated to avoid duplications across clients
// ============================================================================

// ManipulationSeverity enum
type ManipulationSeverity string

const (
	SeverityCritical ManipulationSeverity = "CRITICAL"
	SeverityHigh     ManipulationSeverity = "HIGH"
	SeverityMedium   ManipulationSeverity = "MEDIUM"
	SeverityLow      ManipulationSeverity = "LOW"
	SeverityMinimal  ManipulationSeverity = "MINIMAL"
)

// CognitiveDefenseAction enum
type CognitiveDefenseAction string

const (
	ActionBlock    CognitiveDefenseAction = "BLOCK"
	ActionWarn     CognitiveDefenseAction = "WARN"
	ActionFlag     CognitiveDefenseAction = "FLAG"
	ActionMonitor  CognitiveDefenseAction = "MONITOR"
	ActionAllow    CognitiveDefenseAction = "ALLOW"
)

// ============================================================================
// REQUEST/RESPONSE TYPES
// ============================================================================

// AnalysisRequest for narrative analysis
type AnalysisRequest struct {
	Text        string                 `json:"text"`
	SourceURL   *string                `json:"source_url,omitempty"`
	EnableTier2 bool                   `json:"enable_tier2"`
	Priority    int                    `json:"priority"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// AnalysisResponse from /api/analyze endpoint
type AnalysisResponse struct {
	Success bool                    `json:"success"`
	Report  *CognitiveDefenseReport `json:"report,omitempty"`
	Error   *string                 `json:"error,omitempty"`
}

// HealthCheckResponse from /health endpoint
type HealthCheckResponse struct {
	Status       string            `json:"status"` // healthy, degraded, unhealthy
	Version      string            `json:"version"`
	Timestamp    string            `json:"timestamp"`
	Services     map[string]bool   `json:"services"`
	ModelsLoaded []string          `json:"models_loaded"`
}

// ============================================================================
// COGNITIVE DEFENSE REPORT (UNIFIED)
// ============================================================================

// CognitiveDefenseReport complete analysis report
type CognitiveDefenseReport struct {
	AnalysisID        string                 `json:"analysis_id"`
	Timestamp         string                 `json:"timestamp"`
	Version           string                 `json:"version"`
	Text              string                 `json:"text"`
	SourceURL         *string                `json:"source_url,omitempty"`
	ThreatScore       float64                `json:"threat_score"`
	Severity          string                 `json:"severity"`
	RecommendedAction string                 `json:"recommended_action"`
	Confidence        float64                `json:"confidence"`
	Reasoning         string                 `json:"reasoning"`
	Evidence          []string               `json:"evidence"`
	ProcessingTimeMs  float64                `json:"processing_time_ms"`
	ModelsUsed        []string               `json:"models_used"`
	
	// Detailed analysis results (flexible schema)
	CredibilityResult map[string]interface{} `json:"credibility_result"`
	EmotionalResult   map[string]interface{} `json:"emotional_result"`
	LogicalResult     map[string]interface{} `json:"logical_result"`
	RealityResult     map[string]interface{} `json:"reality_result"`
}

// Helper methods for type-safe access to nested fields

// GetCredibilityScore extracts credibility score from flexible schema
func (r *CognitiveDefenseReport) GetCredibilityScore() float64 {
	if r.CredibilityResult == nil {
		return 0.0
	}
	if score, ok := r.CredibilityResult["credibility_score"].(float64); ok {
		return score
	}
	return 0.0
}

// GetCredibilityRating extracts rating from flexible schema
func (r *CognitiveDefenseReport) GetCredibilityRating() string {
	if r.CredibilityResult == nil {
		return "UNKNOWN"
	}
	if rating, ok := r.CredibilityResult["rating"].(string); ok {
		return rating
	}
	return "UNKNOWN"
}

// GetDomain extracts domain from flexible schema
func (r *CognitiveDefenseReport) GetDomain() string {
	if r.CredibilityResult == nil {
		return ""
	}
	if domain, ok := r.CredibilityResult["domain"].(string); ok {
		return domain
	}
	return ""
}
