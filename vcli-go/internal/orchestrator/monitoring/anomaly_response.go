package monitoring

import (
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/internal/ethical"
	"github.com/verticedev/vcli-go/internal/hcl"
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/orchestrator"
	"github.com/verticedev/vcli-go/internal/triage"
)

// AnomalyResponseOptions configures the anomaly detection & response workflow
type AnomalyResponseOptions struct {
	DetectionThreshold  float64 // Anomaly score threshold (0-1)
	AutoExecute         bool    // Automatically execute remediation
	IncludeRootCause    bool    // Include root cause analysis
	IncludePrediction   bool    // Predict future impact
	EthicalContext      string  // Context for ethical logging
	MaxDuration         time.Duration
}

// AnomalyResponseResult contains anomaly detection and response results
type AnomalyResponseResult struct {
	AnomaliesDetected    []interface{}
	AnomalyCount         int
	HighestSeverity      float64
	RootCauseAnalysis    *maximus.InsightResponse
	ImpactPrediction     *maximus.PredictionResponse
	CorrectiveCommands   []interface{}
	RemediationPlan      interface{}
	RemediationExecuted  bool
	EthicalAudit         interface{}
	SystemStabilized     bool
	TotalDuration        time.Duration
	Recommendations      []string
}

// NewAnomalyResponseWorkflow creates an anomaly detection and response workflow
//
// This workflow combines 7 services for complete anomaly handling:
// 1. HCL Analyzer - Detect anomalies in system metrics
// 2. Maximus Eureka - Generate root cause insights
// 3. Maximus Predict - Predict future impact
// 4. RTE Execute Command - Execute immediate corrective actions
// 5. HCL Planner - Plan long-term remediation
// 6. HCL Executor - Execute remediation plan (if auto-execute enabled)
// 7. Ethical Audit - Log all automated actions
//
// Pipeline:
// Detection → Root Cause → Impact Prediction → Immediate Actions → Planning → Execution → Audit
func NewAnomalyResponseWorkflow(options AnomalyResponseOptions) orchestrator.Workflow {
	if options.MaxDuration == 0 {
		options.MaxDuration = 10 * time.Minute
	}

	if options.DetectionThreshold == 0 {
		options.DetectionThreshold = 0.7 // Default 70% threshold
	}

	workflow := orchestrator.Workflow{
		Name:        "Anomaly Detection & Response",
		Description: "Detect system anomalies and execute corrective actions",
		Category:    "monitoring",
		Timeout:     options.MaxDuration,
		Metadata: map[string]interface{}{
			"detection_threshold": options.DetectionThreshold,
			"auto_execute":        options.AutoExecute,
			"ethical_context":     options.EthicalContext,
			"detection_started":   time.Now().Format(time.RFC3339),
		},
		Steps: []orchestrator.WorkflowStep{},
	}

	// Step 1: Detect Anomalies via HCL Analyzer
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "detect_anomalies",
		Description: "Detect anomalies in system metrics and health",
		Service:     "hcl_analyzer",
		Operation:   "Analyze",
		Input:       nil, // Will use current system metrics
		OnError:     orchestrator.ErrorAbort, // Must detect to proceed
		Timeout:     2 * time.Minute,
		Retries:     2,
		RetryDelay:  10 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			ctx.SetVariable("detection_start", time.Now())
			ctx.SetVariable("threshold", options.DetectionThreshold)
			return nil
		},
		Validate: func(result interface{}) error {
			// Validate that we got analysis results
			analysis, ok := result.(*hcl.AnalysisResult)
			if !ok {
				return fmt.Errorf("invalid analysis result type")
			}

			// Check if any anomalies were detected above threshold
			hasAnomalies := false
			if len(analysis.Anomalies) > 0 {
				for _, anomaly := range analysis.Anomalies {
					if anomaly.Severity > options.DetectionThreshold {
						hasAnomalies = true
						break
					}
				}
			}

			if !hasAnomalies {
				return fmt.Errorf("no anomalies detected above threshold %.2f", options.DetectionThreshold)
			}

			return nil
		},
	})

	// Step 2: Root Cause Analysis (if enabled)
	if options.IncludeRootCause {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "root_cause_analysis",
			Description: "Generate AI-powered root cause insights",
			Service:     "maximus_eureka",
			Operation:   "GenerateInsight",
			Input:       nil, // Will use detection results
			OnError:     orchestrator.ErrorContinue, // Continue even without root cause
			Timeout:     3 * time.Minute,
			Retries:     2,
			RetryDelay:  10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				analysisResult, ok := ctx.GetResult("detect_anomalies")
				if ok {
					insightInput := map[string]interface{}{
						"analysis_results": analysisResult,
						"insight_type":     "root_cause",
						"focus":            "anomalies",
					}
					ctx.SetVariable("root_cause_input", insightInput)
				}
				return nil
			},
		})
	}

	// Step 3: Predict Future Impact (if enabled)
	if options.IncludePrediction {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "predict_impact",
			Description: "Predict future impact of detected anomalies",
			Service:     "maximus_predict",
			Operation:   "Predict",
			Input:       nil, // Will use detection + root cause results
			OnError:     orchestrator.ErrorContinue,
			Timeout:     2 * time.Minute,
			Retries:     2,
			RetryDelay:  10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				analysisResult, _ := ctx.GetResult("detect_anomalies")
				rootCause, _ := ctx.GetResult("root_cause_analysis")

				predictionInput := map[string]interface{}{
					"anomalies":       analysisResult,
					"root_cause":      rootCause,
					"prediction_type": "impact_forecast",
					"timeframe":       "6h",
				}

				ctx.SetVariable("prediction_input", predictionInput)
				return nil
			},
		})
	}

	// Step 4: Execute Immediate Corrective Actions (RTE)
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "execute_immediate_actions",
		Description: "Execute immediate corrective commands in real-time",
		Service:     "rte",
		Operation:   "ExecuteCommand",
		Input:       nil, // Will construct commands from detection results
		OnError:     orchestrator.ErrorContinue, // Log but don't abort
		Timeout:     3 * time.Minute,
		Retries:     1,
		RetryDelay:  10 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Construct immediate corrective commands based on anomalies
			analysisResult, ok := ctx.GetResult("detect_anomalies")
			if ok {
				analysis := analysisResult.(*hcl.AnalysisResult)

				// Determine appropriate commands
				var commandName string
				parameters := make(map[string]interface{})

				if len(analysis.Anomalies) > 0 {
					anomaly := analysis.Anomalies[0] // Handle highest priority anomaly

					switch anomaly.Type {
					case "high_cpu":
						commandName = "throttle_processes"
						parameters["target_cpu"] = 70.0
					case "high_memory":
						commandName = "clear_cache"
						parameters["aggressive"] = true
					case "disk_full":
						commandName = "cleanup_logs"
						parameters["retention_days"] = 7
					default:
						commandName = "health_check"
					}
				}

				rteCommand := triage.RealTimeCommand{
					CommandName: commandName,
					Parameters:  parameters,
					Priority:    9, // High priority for anomaly response
				}

				ctx.SetVariable("rte_command", rteCommand)
			}
			return nil
		},
	})

	// Step 5: Plan Long-Term Remediation
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "plan_remediation",
		Description: "Generate long-term remediation plan using fuzzy logic + RL",
		Service:     "hcl_planner",
		Operation:   "Generate",
		Input:       nil, // Will use all previous results
		OnError:     orchestrator.ErrorContinue,
		Timeout:     3 * time.Minute,
		Retries:     2,
		RetryDelay:  10 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Aggregate all analysis data for planning
			planningInput := map[string]interface{}{
				"anomalies":         ctx.Results["detect_anomalies"],
				"root_cause":        ctx.Results["root_cause_analysis"],
				"impact_prediction": ctx.Results["predict_impact"],
				"immediate_actions": ctx.Results["execute_immediate_actions"],
			}

			ctx.SetVariable("planning_input", planningInput)
			return nil
		},
	})

	// Step 6: Execute Remediation Plan (if auto-execute enabled)
	if options.AutoExecute {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "execute_remediation",
			Description: "Execute automated remediation plan",
			Service:     "hcl_executor",
			Operation:   "Execute",
			Input:       nil, // Will use remediation plan
			OnError:     orchestrator.ErrorContinue,
			Timeout:     5 * time.Minute,
			Retries:     1,
			RetryDelay:  20 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				remediationPlan, ok := ctx.GetResult("plan_remediation")
				if ok {
					ctx.SetVariable("remediation_plan", remediationPlan)
				}
				return nil
			},
			Condition: func(ctx *orchestrator.ExecutionContext) bool {
				// Only execute if we have a valid plan
				_, hasPlan := ctx.GetResult("plan_remediation")
				return hasPlan
			},
		})
	}

	// Step 7: Ethical Audit of Automated Actions
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "ethical_audit",
		Description: "Log all automated actions taken for compliance",
		Service:     "ethical_audit",
		Operation:   "LogDecision",
		Input: ethical.EthicalDecisionLog{
			DecisionID:             "",
			RequestID:              "",
			ServiceName:            "anomaly_response",
			DecisionType:           "automated_response",
			Context: map[string]interface{}{
				"detection_threshold": options.DetectionThreshold,
				"auto_executed":       options.AutoExecute,
			},
			KantianResult:          map[string]interface{}{},
			ConsequentialistResult: map[string]interface{}{},
			VirtueResult:           map[string]interface{}{},
			PrinciplismResult:      map[string]interface{}{},
			FinalDecision:          map[string]interface{}{},
		},
		OnError:    orchestrator.ErrorContinue,
		Timeout:    2 * time.Minute,
		Retries:    2,
		RetryDelay: 5 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Calculate total response time
			startTime, _ := ctx.GetVariable("detection_start")
			if start, ok := startTime.(time.Time); ok {
				duration := time.Since(start)
				ctx.SetVariable("total_response_time", duration)
			}

			// Aggregate anomaly data for audit
			analysisResult, ok := ctx.GetResult("detect_anomalies")
			if ok {
				ctx.SetVariable("audit_anomalies", analysisResult)
			}

			return nil
		},
	})

	return workflow
}
