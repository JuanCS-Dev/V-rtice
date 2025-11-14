package offensive

// ============================================================================
// TOOLS TYPES
// ============================================================================

type ToolsListRequest struct {
	Phase string
}

type ToolsListResult struct {
	Tools []OffensiveTool
}

type OffensiveTool struct {
	Name         string
	Phase        string
	Category     string
	RequiresAuth bool
	Description  string
}

// ============================================================================
// C2 TYPES
// ============================================================================

type C2LaunchRequest struct {
	Target string
	Config string
}

type C2LaunchResult struct {
	ServerURL       string
	ActiveListeners int
	AccessToken     string
	Status          string
}

// ============================================================================
// SOCIAL ENGINEERING TYPES
// ============================================================================

type SocialEngCampaignRequest struct {
	Template string
	Config   string
}

type SocialEngCampaignResult struct {
	CampaignID  string
	Template    string
	TargetCount int
	Duration    string
	Status      string
}

// ============================================================================
// MALWARE ANALYSIS TYPES
// ============================================================================

type MalwareAnalyzeRequest struct {
	SamplePath string
	Mode       string
}

type MalwareAnalyzeResult struct {
	SampleHash  string
	ThreatLevel string
	Family      string
	IOCs        []string
	Behaviors   []string
	Report      string
}

// ============================================================================
// WARGAMING TYPES
// ============================================================================

type WargameStartRequest struct {
	Scenario string
}

type WargameStartResult struct {
	GameID            string
	ScenarioName      string
	Phases            []WargamePhase
	EstimatedDuration string
	Status            string
}

type WargamePhase struct {
	Name     string
	Duration string
	Status   string
}

// ============================================================================
// GATEWAY TYPES
// ============================================================================

type GatewayStatus struct {
	Components []GatewayComponent
	OverallStatus string
}

type GatewayComponent struct {
	Name      string
	Status    string
	Uptime    string
	ActiveOps int
}

// ============================================================================
// ORCHESTRATOR TYPES
// ============================================================================

type OrchestratorWorkflowRequest struct {
	Playbook string
	Config   string
}

type OrchestratorWorkflowResult struct {
	WorkflowID   string
	PlaybookName string
	TotalPhases  int
	CurrentPhase string
	Status       string
}
