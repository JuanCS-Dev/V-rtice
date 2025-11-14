package neuro

import "time"

// ============================================================================
// AUDITORY CORTEX TYPES
// ============================================================================

type AuditoryListenRequest struct {
	Source string
	Topic  string
	Follow bool
}

type AuditoryEvent struct {
	Timestamp   time.Time
	EventType   string
	Severity    int
	Description string
	Source      string
	Metadata    map[string]interface{}
}

// ============================================================================
// THALAMUS TYPES
// ============================================================================

type ThalamusRouteRequest struct {
	Input     string
	InputType string
}

type ThalamusRouteResult struct {
	Routes []ThalamusRoute
}

type ThalamusRoute struct {
	InputType    string
	TargetCortex string
	Priority     string
	Status       string
}

// ============================================================================
// MEMORY TYPES
// ============================================================================

type MemoryConsolidateRequest struct {
	Type string
}

type MemoryConsolidateResult struct {
	PatternsConsolidated int
	MemoryUsage          string
	Duration             string
}

// ============================================================================
// CORTEX (PREFRONTAL) TYPES
// ============================================================================

type CortexPlanRequest struct {
	Objective string
}

type CortexPlan struct {
	Objective     string
	Steps         []CortexPlanStep
	TotalDuration string
}

type CortexPlanStep struct {
	Description       string
	EstimatedDuration string
	Priority          string
	Dependencies      []string
}

// ============================================================================
// VISUAL CORTEX TYPES
// ============================================================================

type VisualAnalyzeRequest struct {
	ImageFeed string
}

type VisualAnalyzeResult struct {
	FeedID          string
	DetectedObjects []DetectedObject
	ThreatLevel     string
	Analysis        string
}

type DetectedObject struct {
	Label      string
	Confidence float64
	BoundingBox map[string]int
}

// ============================================================================
// SOMATOSENSORY TYPES
// ============================================================================

type SomatosensoryStatus struct {
	Sensors []SomatosensorySensor
}

type SomatosensorySensor struct {
	Name      string
	Status    string
	Value     string
	Threshold string
	Unit      string
}

// ============================================================================
// TEGUMENTAR TYPES
// ============================================================================

type TegumentarShieldRequest struct {
	Zone string
}

type TegumentarShieldResult struct {
	ProtectionLevel string
	ActiveBarriers  int
	Zone            string
}

// ============================================================================
// VESTIBULAR TYPES
// ============================================================================

type VestibularBalanceRequest struct {
	Action string
}

type VestibularBalanceResult struct {
	BalanceScore        float64
	TasksRedistributed int
	Status              string
}

// ============================================================================
// CHEMICAL SENSING TYPES
// ============================================================================

type ChemicalSenseRequest struct {
	Indicators string
}

type ChemicalSenseResult struct {
	Threats []ChemicalThreat
}

type ChemicalThreat struct {
	Type     string
	Severity int
	Location string
	Details  map[string]interface{}
}
