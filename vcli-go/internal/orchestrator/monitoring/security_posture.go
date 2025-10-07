package monitoring

import (
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/internal/hcl"
	"github.com/verticedev/vcli-go/internal/immunis"
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/orchestrator"
)

// SecurityPostureOptions configures the security posture monitoring workflow
type SecurityPostureOptions struct {
	IncludeML              bool // Include ML-based predictions
	IncludeImmuneStatus    bool // Check all immune system components
	IncludeEthicalMetrics  bool // Include ethical compliance metrics
	IncludeAlignmentCheck  bool // Check human-system alignment
	PredictionTimeframe    string // Timeframe for predictions (1h, 24h, 7d)
	MaxDuration            time.Duration
}

// SecurityPostureResult contains comprehensive security posture assessment
type SecurityPostureResult struct {
	Timestamp            time.Time
	HCLAnalysis          *hcl.AnalysisResult
	MLPredictions        *maximus.PredictionResponse
	HomeostaticState     *immunis.HomeostaticStateResponse
	ImmuneMetrics        map[string]interface{}
	EthicalMetrics       interface{}
	AlignmentStatus      interface{}
	OverallHealthScore   float64
	RequiresIntervention bool
	Anomalies            []string
	Recommendations      []string
	TotalDuration        time.Duration
}

// NewSecurityPostureWorkflow creates a comprehensive security posture monitoring workflow
//
// This workflow combines 9 services for complete posture assessment:
// 1. HCL Analyzer - Analyze system health metrics
// 2. Maximus Predict - Predict resource degradation (if enabled)
// 3. Lymphnode Homeostatic - Check homeostatic state (REPOUSO → ATIVAÇÃO)
// 4. Macrophage Status - Check phagocytosis operations
// 5. B-Cell Status - Check antibody generation status
// 6. Helper-T Status - Check immune coordination
// 7. Cytotoxic-T Status - Check threat elimination status
// 8. Ethical Audit Metrics - Get compliance metrics (if enabled)
// 9. HSAS Alignment - Check human-system alignment (if enabled)
//
// Pipeline:
// HCL Analysis → ML Prediction → Homeostatic Check → Immune Status (all cells) → Ethics → Alignment
func NewSecurityPostureWorkflow(options SecurityPostureOptions) orchestrator.Workflow {
	if options.MaxDuration == 0 {
		options.MaxDuration = 5 * time.Minute // Quick check
	}

	if options.PredictionTimeframe == "" {
		options.PredictionTimeframe = "24h"
	}

	workflow := orchestrator.Workflow{
		Name:        "Security Posture Check",
		Description: "Comprehensive security posture and health monitoring",
		Category:    "monitoring",
		Timeout:     options.MaxDuration,
		Metadata: map[string]interface{}{
			"check_started": time.Now().Format(time.RFC3339),
			"ml_enabled":    options.IncludeML,
			"immune_check":  options.IncludeImmuneStatus,
		},
		Steps: []orchestrator.WorkflowStep{},
	}

	// Step 1: HCL Analysis - Analyze Current System Metrics
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "hcl_analysis",
		Description: "Analyze current system health and metrics",
		Service:     "hcl_analyzer",
		Operation:   "Analyze",
		Input:       nil, // Will use current system metrics
		OnError:     orchestrator.ErrorContinue, // Continue even if analysis fails
		Timeout:     2 * time.Minute,
		Retries:     2,
		RetryDelay:  10 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			ctx.SetVariable("check_start_time", time.Now())
			return nil
		},
	})

	// Step 2: ML-Based Prediction (if enabled)
	if options.IncludeML {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "ml_prediction",
			Description: fmt.Sprintf("Predict resource degradation for next %s", options.PredictionTimeframe),
			Service:     "maximus_predict",
			Operation:   "Predict",
			Input:       nil, // Will use HCL analysis results
			OnError:     orchestrator.ErrorContinue,
			Timeout:     2 * time.Minute,
			Retries:     2,
			RetryDelay:  10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				hclResult, ok := ctx.GetResult("hcl_analysis")
				if ok {
					predictionInput := map[string]interface{}{
						"current_metrics":  hclResult,
						"prediction_type":  "resource_degradation",
						"timeframe":        options.PredictionTimeframe,
					}
					ctx.SetVariable("prediction_input", predictionInput)
				}
				return nil
			},
		})
	}

	// Step 3: Check Homeostatic State
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "homeostatic_state",
		Description: "Check system homeostatic state (REPOUSO/VIGILÂNCIA/ATENÇÃO/ATIVAÇÃO/INFLAMAÇÃO)",
		Service:     "lymphnode",
		Operation:   "GetHomeostaticState",
		Input:       nil,
		OnError:     orchestrator.ErrorContinue,
		Timeout:     1 * time.Minute,
		Retries:     2,
		RetryDelay:  5 * time.Second,
	})

	// Steps 4-7: Immune System Status Checks (if enabled)
	if options.IncludeImmuneStatus {
		// Step 4: Macrophage Status
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "macrophage_status",
			Description: "Check macrophage phagocytosis status",
			Service:     "macrophage",
			Operation:   "GetStatus",
			Input:       nil,
			OnError:     orchestrator.ErrorContinue,
			Timeout:     1 * time.Minute,
			Retries:     1,
			RetryDelay:  5 * time.Second,
		})

		// Step 5: B-Cell Status
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "bcell_status",
			Description: "Check B-cell antibody generation status",
			Service:     "bcell",
			Operation:   "GetStatus",
			Input:       nil,
			OnError:     orchestrator.ErrorContinue,
			Timeout:     1 * time.Minute,
			Retries:     1,
			RetryDelay:  5 * time.Second,
		})

		// Step 6: Helper-T Status
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "helper_t_status",
			Description: "Check helper T-cell coordination status",
			Service:     "helper_t",
			Operation:   "GetStatus",
			Input:       nil,
			OnError:     orchestrator.ErrorContinue,
			Timeout:     1 * time.Minute,
			Retries:     1,
			RetryDelay:  5 * time.Second,
		})

		// Step 7: Cytotoxic-T Status
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "cytotoxic_t_status",
			Description: "Check cytotoxic T-cell elimination status",
			Service:     "cytotoxic_t",
			Operation:   "GetStatus",
			Input:       nil,
			OnError:     orchestrator.ErrorContinue,
			Timeout:     1 * time.Minute,
			Retries:     1,
			RetryDelay:  5 * time.Second,
		})

		// Step 8: Lymphnode Metrics
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "lymphnode_metrics",
			Description: "Get lymphnode coordination metrics",
			Service:     "lymphnode",
			Operation:   "GetMetrics",
			Input:       nil,
			OnError:     orchestrator.ErrorContinue,
			Timeout:     1 * time.Minute,
			Retries:     1,
			RetryDelay:  5 * time.Second,
		})
	}

	// Step N+1: Ethical Compliance Metrics (if enabled)
	if options.IncludeEthicalMetrics {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "ethical_metrics",
			Description: "Get ethical compliance metrics",
			Service:     "ethical_audit",
			Operation:   "GetMetrics",
			Input:       nil,
			OnError:     orchestrator.ErrorContinue,
			Timeout:     1 * time.Minute,
			Retries:     2,
			RetryDelay:  5 * time.Second,
		})

		// Framework-specific metrics
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "framework_metrics",
			Description: "Get ethical framework metrics (Kantian, Consequentialist, etc.)",
			Service:     "ethical_audit",
			Operation:   "GetFrameworkMetrics",
			Input:       nil,
			OnError:     orchestrator.ErrorContinue,
			Timeout:     1 * time.Minute,
			Retries:     2,
			RetryDelay:  5 * time.Second,
		})
	}

	// Step N+2: Human-System Alignment Check (if enabled)
	if options.IncludeAlignmentCheck {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "alignment_status",
			Description: "Check human-system alignment status",
			Service:     "hsas",
			Operation:   "GetAlignmentStatus",
			Input:       nil,
			OnError:     orchestrator.ErrorContinue,
			Timeout:     1 * time.Minute,
			Retries:     2,
			RetryDelay:  5 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Calculate total check duration
				startTime, _ := ctx.GetVariable("check_start_time")
				if start, ok := startTime.(time.Time); ok {
					duration := time.Since(start)
					ctx.SetVariable("total_check_duration", duration)
				}
				return nil
			},
		})
	}

	return workflow
}
