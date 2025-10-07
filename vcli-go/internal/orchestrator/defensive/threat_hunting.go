package defensive

import (
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/internal/immunis"
	"github.com/verticedev/vcli-go/internal/investigation"
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/orchestrator"
)

// ThreatHuntingOptions configures the proactive threat hunting workflow
type ThreatHuntingOptions struct {
	Scope                string   // Scope: infrastructure, endpoints, network, all
	ThreatTypes          []string // Types to hunt: malware, apt, insider, lateral_movement
	EnableMLPrediction   bool     // Use ML to predict future threats
	EnableAntibodies     bool     // Generate preventive antibodies
	EnableAgentCloning   bool     // Clone specialized hunting agents
	InfrastructureTargets []string // Infrastructure to scan (IPs/CIDRs)
	MaxDuration          time.Duration
}

// ThreatHuntingResult contains comprehensive hunting results
type ThreatHuntingResult struct {
	HuntID                 string
	EmergingThreats        []interface{}
	PredictedThreats       *maximus.PredictionResponse
	InvestigationResults   []interface{}
	ReconResults           []interface{}
	PreventiveAntibodies   []string
	ClonedAgents           int
	AIInsights             *maximus.InsightResponse
	TotalThreatsFound      int
	TotalIOCsDiscovered    int
	RiskAssessment         float64
	Recommendations        []string
	TotalDuration          time.Duration
}

// NewThreatHuntingWorkflow creates a proactive threat hunting workflow
//
// This workflow combines 7 services for predictive threat detection:
// 1. Threat Intel Query - Fetch latest emerging threats
// 2. Maximus Predict - Predict future threats using ML
// 3. Autonomous Investigation - Investigate predicted IoCs
// 4. Network Recon - Scan infrastructure for predicted IoCs
// 5. Immunis B-Cell - Generate preventive antibodies
// 6. Maximus Eureka - Generate threat trend insights
// 7. Lymphnode - Clone specialized hunting agents (optional)
//
// Pipeline:
// Threat Intel → ML Prediction → Investigation → Infrastructure Scan → Antibodies → Insights → Cloning
func NewThreatHuntingWorkflow(options ThreatHuntingOptions) orchestrator.Workflow {
	if options.MaxDuration == 0 {
		options.MaxDuration = 60 * time.Minute
	}

	if len(options.ThreatTypes) == 0 {
		options.ThreatTypes = []string{"malware", "apt", "lateral_movement"}
	}

	if options.Scope == "" {
		options.Scope = "infrastructure"
	}

	workflow := orchestrator.Workflow{
		Name:        "Proactive Threat Hunting",
		Description: fmt.Sprintf("Hunt for %v threats in %s scope", options.ThreatTypes, options.Scope),
		Category:    "defensive",
		Timeout:     options.MaxDuration,
		Metadata: map[string]interface{}{
			"scope":               options.Scope,
			"threat_types":        options.ThreatTypes,
			"ml_prediction":       options.EnableMLPrediction,
			"preventive_antibodies": options.EnableAntibodies,
			"hunt_started":        time.Now().Format(time.RFC3339),
		},
		Steps: []orchestrator.WorkflowStep{},
	}

	// Step 1: Query Threat Intelligence for Latest Threats
	for _, threatType := range options.ThreatTypes {
		stepName := fmt.Sprintf("query_threat_intel_%s", threatType)

		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        stepName,
			Description: fmt.Sprintf("Query latest %s threats", threatType),
			Service:     "threat_intel",
			Operation:   "QueryThreatIntel",
			Input: map[string]interface{}{
				"indicator":      threatType,
				"indicator_type": "threat_category",
				"context": map[string]interface{}{
					"latest":        true,
					"emerging_only": true,
					"timeframe":     "7d",
				},
			},
			OnError:    orchestrator.ErrorContinue, // Continue hunting even if query fails
			Timeout:    5 * time.Minute,
			Retries:    2,
			RetryDelay: 10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				if ctx.CurrentStep == 1 {
					ctx.SetVariable("hunt_start_time", time.Now())
				}
				return nil
			},
		})
	}

	// Step 2: ML-Powered Threat Prediction (if enabled)
	if options.EnableMLPrediction {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "predict_future_threats",
			Description: "Use ML to predict future threat emergence",
			Service:     "maximus_predict",
			Operation:   "Predict",
			Input:       nil, // Will aggregate threat intel results
			OnError:     orchestrator.ErrorContinue,
			Timeout:     5 * time.Minute,
			Retries:     2,
			RetryDelay:  10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Aggregate all threat intel results for ML prediction
				aggregatedThreats := make([]interface{}, 0)
				for _, threatType := range options.ThreatTypes {
					stepName := fmt.Sprintf("query_threat_intel_%s", threatType)
					if result, ok := ctx.GetResult(stepName); ok {
						aggregatedThreats = append(aggregatedThreats, result)
					}
				}

				predictionInput := map[string]interface{}{
					"threat_data":     aggregatedThreats,
					"scope":           options.Scope,
					"prediction_type": "emerging_threats",
					"timeframe":       "30d",
				}

				ctx.SetVariable("prediction_input", predictionInput)
				return nil
			},
		})
	}

	// Step 3: Initiate Autonomous Investigation for Predicted Threats
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "investigate_predicted_threats",
		Description: "Launch autonomous investigation for predicted IoCs",
		Service:     "autonomous_investigation",
		Operation:   "InitiateInvestigation",
		Input:       nil, // Will use prediction results or threat intel
		OnError:     orchestrator.ErrorContinue,
		Timeout:     10 * time.Minute,
		Retries:     2,
		RetryDelay:  15 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Use ML predictions if available, otherwise use threat intel
			var investigationTarget string
			var investigationScope string

			if options.EnableMLPrediction {
				if predResult, ok := ctx.GetResult("predict_future_threats"); ok {
					investigationTarget = "predicted_threats"
					investigationScope = "comprehensive"
					ctx.SetVariable("prediction_result", predResult)
				}
			} else {
				investigationTarget = "latest_threats"
				investigationScope = "targeted"
			}

			ctx.SetVariable("investigation_target", investigationTarget)
			ctx.SetVariable("investigation_scope", investigationScope)
			return nil
		},
	})

	// Step 4-N: Infrastructure Scanning for Each Target
	if len(options.InfrastructureTargets) > 0 {
		for i, target := range options.InfrastructureTargets {
			stepName := fmt.Sprintf("scan_infrastructure_%d_%s", i+1, target)

			workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
				Name:        stepName,
				Description: fmt.Sprintf("Scan infrastructure target: %s for predicted IoCs", target),
				Service:     "network_recon",
				Operation:   "StartRecon",
				Input: investigation.StartReconRequest{
					Target:   target,
					ScanType: "deep", // Deep scan for threat hunting
				},
				OnError:    orchestrator.ErrorContinue, // Continue scanning other targets
				Timeout:    15 * time.Minute,
				Retries:    1,
				RetryDelay: 30 * time.Second,
			})

			// Get scan results
			workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
				Name:        fmt.Sprintf("get_scan_results_%d", i+1),
				Description: fmt.Sprintf("Retrieve scan results for %s", target),
				Service:     "network_recon",
				Operation:   "GetReconResults",
				Input:       nil, // Will use recon ID from previous step
				OnError:     orchestrator.ErrorContinue,
				Timeout:     5 * time.Minute,
				Retries:     3,
				RetryDelay:  20 * time.Second,
				Transform: func(ctx *orchestrator.ExecutionContext) error {
					scanStepName := fmt.Sprintf("scan_infrastructure_%d_%s", i+1, target)
					if scanResult, ok := ctx.GetResult(scanStepName); ok {
						ctx.SetVariable(fmt.Sprintf("scan_result_%d", i+1), scanResult)
					}
					return nil
				},
			})
		}
	}

	// Step N+1: Generate Preventive Antibodies (if enabled)
	if options.EnableAntibodies {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "generate_preventive_antibodies",
			Description: "Generate YARA signatures for predicted threats",
			Service:     "bcell",
			Operation:   "Process",
			Input:       nil, // Will use investigation and scan results
			OnError:     orchestrator.ErrorContinue,
			Timeout:     5 * time.Minute,
			Retries:     2,
			RetryDelay:  10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Aggregate all investigation and scan results
				antibodyInput := map[string]interface{}{
					"investigation":  ctx.Results["investigate_predicted_threats"],
					"threat_intel":   make([]interface{}, 0),
					"scan_results":   make([]interface{}, 0),
					"preventive":     true,
				}

				// Add all threat intel results
				for _, threatType := range options.ThreatTypes {
					stepName := fmt.Sprintf("query_threat_intel_%s", threatType)
					if result, ok := ctx.GetResult(stepName); ok {
						threatIntel := antibodyInput["threat_intel"].([]interface{})
						antibodyInput["threat_intel"] = append(threatIntel, result)
					}
				}

				// Add all scan results
				for i := range options.InfrastructureTargets {
					resultName := fmt.Sprintf("get_scan_results_%d", i+1)
					if result, ok := ctx.GetResult(resultName); ok {
						scanResults := antibodyInput["scan_results"].([]interface{})
						antibodyInput["scan_results"] = append(scanResults, result)
					}
				}

				ctx.SetVariable("antibody_generation_input", antibodyInput)
				return nil
			},
		})
	}

	// Step N+2: Generate Threat Trend Insights (Maximus Eureka)
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "generate_threat_insights",
		Description: "Generate AI-powered insights on threat trends",
		Service:     "maximus_eureka",
		Operation:   "GenerateInsight",
		Input:       nil, // Will aggregate all hunting results
		OnError:     orchestrator.ErrorContinue,
		Timeout:     5 * time.Minute,
		Retries:     2,
		RetryDelay:  10 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Aggregate all hunting data for insight generation
			insightInput := map[string]interface{}{
				"scope":              options.Scope,
				"threat_types":       options.ThreatTypes,
				"threat_intel":       make([]interface{}, 0),
				"predictions":        ctx.Results["predict_future_threats"],
				"investigations":     ctx.Results["investigate_predicted_threats"],
				"antibodies":         ctx.Results["generate_preventive_antibodies"],
			}

			// Add threat intel
			for _, threatType := range options.ThreatTypes {
				stepName := fmt.Sprintf("query_threat_intel_%s", threatType)
				if result, ok := ctx.GetResult(stepName); ok {
					threatIntel := insightInput["threat_intel"].([]interface{})
					insightInput["threat_intel"] = append(threatIntel, result)
				}
			}

			ctx.SetVariable("insight_data", insightInput)
			return nil
		},
	})

	// Step N+3: Clone Specialized Hunting Agents (if enabled)
	if options.EnableAgentCloning {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "clone_hunting_agents",
			Description: "Clone specialized threat hunting agents",
			Service:     "lymphnode",
			Operation:   "CloneAgent",
			Input: immunis.CloneRequest{
				AgentID:      "threat_hunter",
				NumClones:    len(options.ThreatTypes) * 2, // 2 agents per threat type
				Mutate:       true,
				MutationRate: 0.15, // Higher mutation for diversity
			},
			OnError:    orchestrator.ErrorContinue,
			Timeout:    3 * time.Minute,
			Retries:    1,
			RetryDelay: 10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				huntStartTime, _ := ctx.GetVariable("hunt_start_time")
				if start, ok := huntStartTime.(time.Time); ok {
					duration := time.Since(start)
					ctx.SetVariable("total_hunt_duration", duration)
				}
				return nil
			},
		})
	}

	return workflow
}
