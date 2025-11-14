package monitoring

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/internal/orchestrator"
)

// TestNewSecurityPostureWorkflow tests security posture workflow creation
func TestNewSecurityPostureWorkflow(t *testing.T) {
	tests := []struct {
		name            string
		options         SecurityPostureOptions
		validateWorkflow func(t *testing.T, workflow orchestrator.Workflow)
	}{
		{
			name: "creates workflow with full options",
			options: SecurityPostureOptions{
				IncludeML:             true,
				IncludeImmuneStatus:   true,
				IncludeEthicalMetrics: true,
				IncludeAlignmentCheck: true,
				PredictionTimeframe:   "24h",
				MaxDuration:           5 * time.Minute,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, "Security Posture Check", workflow.Name)
				assert.Equal(t, "monitoring", workflow.Category)
				assert.Equal(t, 5*time.Minute, workflow.Timeout)
				assert.Contains(t, workflow.Description, "security posture")

				// Check metadata
				assert.Equal(t, true, workflow.Metadata["ml_enabled"])
				assert.Equal(t, true, workflow.Metadata["immune_check"])

				// Verify steps exist
				assert.Greater(t, len(workflow.Steps), 0)
			},
		},
		{
			name: "applies default max duration",
			options: SecurityPostureOptions{
				IncludeML: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, 5*time.Minute, workflow.Timeout)
			},
		},
		{
			name: "applies default prediction timeframe",
			options: SecurityPostureOptions{
				IncludeML: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Check prediction step uses default timeframe
				var predictionStep *orchestrator.WorkflowStep
				for _, step := range workflow.Steps {
					if step.Name == "ml_prediction" {
						predictionStep = &step
						break
					}
				}

				require.NotNil(t, predictionStep)
				assert.Contains(t, predictionStep.Description, "24h")
			},
		},
		{
			name: "creates workflow without ML prediction",
			options: SecurityPostureOptions{
				IncludeML: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include ML prediction step
				mlSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "ml_prediction" {
						mlSteps++
					}
				}
				assert.Equal(t, 0, mlSteps)
			},
		},
		{
			name: "includes ML prediction when enabled",
			options: SecurityPostureOptions{
				IncludeML:           true,
				PredictionTimeframe: "7d",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include ML prediction step
				mlSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "ml_prediction" {
						mlSteps++
					}
				}
				assert.Equal(t, 1, mlSteps)
			},
		},
		{
			name: "creates workflow without immune status checks",
			options: SecurityPostureOptions{
				IncludeImmuneStatus: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include immune cell status steps
				immuneSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "macrophage_status" ||
						step.Name == "bcell_status" ||
						step.Name == "helper_t_status" ||
						step.Name == "cytotoxic_t_status" {
						immuneSteps++
					}
				}
				assert.Equal(t, 0, immuneSteps)
			},
		},
		{
			name: "includes immune status checks when enabled",
			options: SecurityPostureOptions{
				IncludeImmuneStatus: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include all immune cell status steps
				immuneSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "macrophage_status" ||
						step.Name == "bcell_status" ||
						step.Name == "helper_t_status" ||
						step.Name == "cytotoxic_t_status" ||
						step.Name == "lymphnode_metrics" {
						immuneSteps++
					}
				}
				assert.Equal(t, 5, immuneSteps) // 4 cell types + lymphnode metrics
			},
		},
		{
			name: "creates workflow without ethical metrics",
			options: SecurityPostureOptions{
				IncludeEthicalMetrics: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include ethical metrics steps
				ethicalSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "ethical_metrics" || step.Name == "framework_metrics" {
						ethicalSteps++
					}
				}
				assert.Equal(t, 0, ethicalSteps)
			},
		},
		{
			name: "includes ethical metrics when enabled",
			options: SecurityPostureOptions{
				IncludeEthicalMetrics: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include ethical metrics steps
				ethicalSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "ethical_metrics" || step.Name == "framework_metrics" {
						ethicalSteps++
					}
				}
				assert.Equal(t, 2, ethicalSteps)
			},
		},
		{
			name: "creates workflow without alignment check",
			options: SecurityPostureOptions{
				IncludeAlignmentCheck: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include alignment status step
				alignmentSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "alignment_status" {
						alignmentSteps++
					}
				}
				assert.Equal(t, 0, alignmentSteps)
			},
		},
		{
			name: "includes alignment check when enabled",
			options: SecurityPostureOptions{
				IncludeAlignmentCheck: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include alignment status step
				alignmentSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "alignment_status" {
						alignmentSteps++
					}
				}
				assert.Equal(t, 1, alignmentSteps)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewSecurityPostureWorkflow(tt.options)
			require.NotNil(t, workflow)
			tt.validateWorkflow(t, workflow)
		})
	}
}

// TestSecurityPostureWorkflowSteps tests individual workflow steps
func TestSecurityPostureWorkflowSteps(t *testing.T) {
	tests := []struct {
		name         string
		options      SecurityPostureOptions
		validateSteps func(t *testing.T, steps []orchestrator.WorkflowStep)
	}{
		{
			name: "HCL analysis step configured correctly",
			options: SecurityPostureOptions{
				IncludeML: false,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// First step should always be HCL analysis
				require.Greater(t, len(steps), 0)
				hclStep := steps[0]

				assert.Equal(t, "hcl_analysis", hclStep.Name)
				assert.Equal(t, "hcl_analyzer", hclStep.Service)
				assert.Equal(t, "Analyze", hclStep.Operation)
				assert.Equal(t, orchestrator.ErrorContinue, hclStep.OnError)
				assert.NotNil(t, hclStep.Transform)
			},
		},
		{
			name: "ML prediction step configured correctly",
			options: SecurityPostureOptions{
				IncludeML:           true,
				PredictionTimeframe: "7d",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var predictionStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "ml_prediction" {
						predictionStep = &step
						break
					}
				}

				require.NotNil(t, predictionStep)
				assert.Equal(t, "maximus_predict", predictionStep.Service)
				assert.Equal(t, "Predict", predictionStep.Operation)
				assert.Contains(t, predictionStep.Description, "7d")
				assert.NotNil(t, predictionStep.Transform)
			},
		},
		{
			name: "homeostatic state step configured correctly",
			options: SecurityPostureOptions{
				IncludeML: false,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var homeostaticStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "homeostatic_state" {
						homeostaticStep = &step
						break
					}
				}

				require.NotNil(t, homeostaticStep)
				assert.Equal(t, "lymphnode", homeostaticStep.Service)
				assert.Equal(t, "GetHomeostaticState", homeostaticStep.Operation)
				assert.Contains(t, homeostaticStep.Description, "REPOUSO")
			},
		},
		{
			name: "immune system status steps configured correctly",
			options: SecurityPostureOptions{
				IncludeImmuneStatus: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Check macrophage step
				var macrophageStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "macrophage_status" {
						macrophageStep = &step
						break
					}
				}
				require.NotNil(t, macrophageStep)
				assert.Equal(t, "macrophage", macrophageStep.Service)
				assert.Equal(t, "GetStatus", macrophageStep.Operation)

				// Check B-cell step
				var bcellStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "bcell_status" {
						bcellStep = &step
						break
					}
				}
				require.NotNil(t, bcellStep)
				assert.Equal(t, "bcell", bcellStep.Service)

				// Check Helper-T step
				var helperTStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "helper_t_status" {
						helperTStep = &step
						break
					}
				}
				require.NotNil(t, helperTStep)
				assert.Equal(t, "helper_t", helperTStep.Service)

				// Check Cytotoxic-T step
				var cytotoxicTStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "cytotoxic_t_status" {
						cytotoxicTStep = &step
						break
					}
				}
				require.NotNil(t, cytotoxicTStep)
				assert.Equal(t, "cytotoxic_t", cytotoxicTStep.Service)

				// Check lymphnode metrics step
				var lymphnodeStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "lymphnode_metrics" {
						lymphnodeStep = &step
						break
					}
				}
				require.NotNil(t, lymphnodeStep)
				assert.Equal(t, "lymphnode", lymphnodeStep.Service)
				assert.Equal(t, "GetMetrics", lymphnodeStep.Operation)
			},
		},
		{
			name: "ethical metrics steps configured correctly",
			options: SecurityPostureOptions{
				IncludeEthicalMetrics: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Check ethical metrics step
				var ethicalStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "ethical_metrics" {
						ethicalStep = &step
						break
					}
				}
				require.NotNil(t, ethicalStep)
				assert.Equal(t, "ethical_audit", ethicalStep.Service)
				assert.Equal(t, "GetMetrics", ethicalStep.Operation)

				// Check framework metrics step
				var frameworkStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "framework_metrics" {
						frameworkStep = &step
						break
					}
				}
				require.NotNil(t, frameworkStep)
				assert.Equal(t, "ethical_audit", frameworkStep.Service)
				assert.Equal(t, "GetFrameworkMetrics", frameworkStep.Operation)
			},
		},
		{
			name: "alignment status step configured correctly",
			options: SecurityPostureOptions{
				IncludeAlignmentCheck: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var alignmentStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "alignment_status" {
						alignmentStep = &step
						break
					}
				}

				require.NotNil(t, alignmentStep)
				assert.Equal(t, "hsas", alignmentStep.Service)
				assert.Equal(t, "GetAlignmentStatus", alignmentStep.Operation)
				assert.NotNil(t, alignmentStep.Transform)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewSecurityPostureWorkflow(tt.options)
			require.NotNil(t, workflow)
			tt.validateSteps(t, workflow.Steps)
		})
	}
}

// TestSecurityPostureWorkflowStepTransforms tests step transform functions
func TestSecurityPostureWorkflowStepTransforms(t *testing.T) {
	tests := []struct {
		name          string
		stepName      string
		setupCtx      func() *orchestrator.ExecutionContext
		options       SecurityPostureOptions
		validateCtx   func(t *testing.T, ctx *orchestrator.ExecutionContext)
	}{
		{
			name:     "HCL analysis sets check start time",
			stepName: "hcl_analysis",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Variables: make(map[string]interface{}),
				}
			},
			options: SecurityPostureOptions{
				IncludeML: false,
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				_, ok := ctx.GetVariable("check_start_time")
				assert.True(t, ok)
			},
		},
		{
			name:     "ML prediction uses HCL results",
			stepName: "ml_prediction",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Results: map[string]interface{}{
						"hcl_analysis": map[string]interface{}{
							"cpu_usage":    80,
							"memory_usage": 75,
						},
					},
					Variables: make(map[string]interface{}),
				}
			},
			options: SecurityPostureOptions{
				IncludeML:           true,
				PredictionTimeframe: "24h",
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				predInput, ok := ctx.GetVariable("prediction_input")
				assert.True(t, ok)
				assert.NotNil(t, predInput)

				input := predInput.(map[string]interface{})
				assert.Equal(t, "resource_degradation", input["prediction_type"])
				assert.Equal(t, "24h", input["timeframe"])
			},
		},
		{
			name:     "alignment status calculates total duration",
			stepName: "alignment_status",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Variables: map[string]interface{}{
						"check_start_time": time.Now().Add(-2 * time.Minute),
					},
				}
			},
			options: SecurityPostureOptions{
				IncludeAlignmentCheck: true,
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				duration, ok := ctx.GetVariable("total_check_duration")
				assert.True(t, ok)
				assert.NotNil(t, duration)

				dur := duration.(time.Duration)
				assert.Greater(t, dur, time.Duration(0))
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewSecurityPostureWorkflow(tt.options)

			// Find the step with the specified name
			var targetStep *orchestrator.WorkflowStep
			for _, step := range workflow.Steps {
				if step.Name == tt.stepName {
					targetStep = &step
					break
				}
			}

			require.NotNil(t, targetStep, "Step %s not found", tt.stepName)
			require.NotNil(t, targetStep.Transform, "Transform not found for step %s", tt.stepName)

			ctx := tt.setupCtx()
			err := targetStep.Transform(ctx)
			require.NoError(t, err)

			tt.validateCtx(t, ctx)
		})
	}
}

// TestSecurityPostureOptions tests the SecurityPostureOptions structure
func TestSecurityPostureOptions(t *testing.T) {
	options := SecurityPostureOptions{
		IncludeML:             true,
		IncludeImmuneStatus:   true,
		IncludeEthicalMetrics: true,
		IncludeAlignmentCheck: true,
		PredictionTimeframe:   "7d",
		MaxDuration:           5 * time.Minute,
	}

	assert.True(t, options.IncludeML)
	assert.True(t, options.IncludeImmuneStatus)
	assert.True(t, options.IncludeEthicalMetrics)
	assert.True(t, options.IncludeAlignmentCheck)
	assert.Equal(t, "7d", options.PredictionTimeframe)
	assert.Equal(t, 5*time.Minute, options.MaxDuration)
}

// TestSecurityPostureResult tests the SecurityPostureResult structure
func TestSecurityPostureResult(t *testing.T) {
	result := SecurityPostureResult{
		Timestamp:            time.Now(),
		OverallHealthScore:   85.5,
		RequiresIntervention: false,
		Anomalies:            []string{"High CPU usage detected"},
		Recommendations:      []string{"Scale up resources", "Optimize queries"},
		TotalDuration:        3 * time.Minute,
	}

	assert.Equal(t, 85.5, result.OverallHealthScore)
	assert.False(t, result.RequiresIntervention)
	assert.Len(t, result.Anomalies, 1)
	assert.Len(t, result.Recommendations, 2)
	assert.Equal(t, 3*time.Minute, result.TotalDuration)
}

// TestSecurityPostureWorkflowStepOrdering tests the order of steps
func TestSecurityPostureWorkflowStepOrdering(t *testing.T) {
	options := SecurityPostureOptions{
		IncludeML:             true,
		IncludeImmuneStatus:   true,
		IncludeEthicalMetrics: true,
		IncludeAlignmentCheck: true,
		PredictionTimeframe:   "24h",
		MaxDuration:           5 * time.Minute,
	}

	workflow := NewSecurityPostureWorkflow(options)

	// Expected order:
	// 1. HCL analysis
	// 2. ML prediction (if enabled)
	// 3. Homeostatic state
	// 4. Immune system checks (if enabled)
	// 5. Ethical metrics (if enabled)
	// 6. Alignment check (if enabled)

	stepNames := make([]string, len(workflow.Steps))
	for i, step := range workflow.Steps {
		stepNames[i] = step.Name
	}

	// Verify key steps appear in order
	hclIdx := -1
	mlIdx := -1
	homeostaticIdx := -1
	ethicalIdx := -1
	alignmentIdx := -1

	for i, name := range stepNames {
		if name == "hcl_analysis" {
			hclIdx = i
		}
		if name == "ml_prediction" {
			mlIdx = i
		}
		if name == "homeostatic_state" {
			homeostaticIdx = i
		}
		if name == "ethical_metrics" {
			ethicalIdx = i
		}
		if name == "alignment_status" {
			alignmentIdx = i
		}
	}

	assert.Equal(t, 0, hclIdx, "HCL analysis should be first step")
	assert.Greater(t, mlIdx, hclIdx, "ML prediction should come after HCL")
	assert.Greater(t, homeostaticIdx, mlIdx, "Homeostatic check should come after ML")
	assert.Greater(t, alignmentIdx, ethicalIdx, "Alignment should come after ethical metrics")
}

// TestSecurityPostureWorkflowMinimalConfiguration tests minimal configuration
func TestSecurityPostureWorkflowMinimalConfiguration(t *testing.T) {
	options := SecurityPostureOptions{
		IncludeML:             false,
		IncludeImmuneStatus:   false,
		IncludeEthicalMetrics: false,
		IncludeAlignmentCheck: false,
	}

	workflow := NewSecurityPostureWorkflow(options)

	// Should still have HCL analysis and homeostatic state as minimum
	assert.GreaterOrEqual(t, len(workflow.Steps), 2)

	// First step should be HCL analysis
	assert.Equal(t, "hcl_analysis", workflow.Steps[0].Name)

	// Should have homeostatic state
	hasHomeostatic := false
	for _, step := range workflow.Steps {
		if step.Name == "homeostatic_state" {
			hasHomeostatic = true
			break
		}
	}
	assert.True(t, hasHomeostatic, "Should always include homeostatic state check")
}

// TestSecurityPostureWorkflowMaximalConfiguration tests maximal configuration
func TestSecurityPostureWorkflowMaximalConfiguration(t *testing.T) {
	options := SecurityPostureOptions{
		IncludeML:             true,
		IncludeImmuneStatus:   true,
		IncludeEthicalMetrics: true,
		IncludeAlignmentCheck: true,
		PredictionTimeframe:   "7d",
		MaxDuration:           10 * time.Minute,
	}

	workflow := NewSecurityPostureWorkflow(options)

	// Count steps:
	// 1. HCL analysis
	// 2. ML prediction
	// 3. Homeostatic state
	// 4-8. Immune system (macrophage, bcell, helper_t, cytotoxic_t, lymphnode_metrics) = 5
	// 9-10. Ethical metrics (ethical_metrics, framework_metrics) = 2
	// 11. Alignment status
	// Total = 11 steps

	assert.Equal(t, 11, len(workflow.Steps))

	// Verify all expected steps are present
	expectedSteps := []string{
		"hcl_analysis",
		"ml_prediction",
		"homeostatic_state",
		"macrophage_status",
		"bcell_status",
		"helper_t_status",
		"cytotoxic_t_status",
		"lymphnode_metrics",
		"ethical_metrics",
		"framework_metrics",
		"alignment_status",
	}

	for _, expected := range expectedSteps {
		found := false
		for _, step := range workflow.Steps {
			if step.Name == expected {
				found = true
				break
			}
		}
		assert.True(t, found, "Expected step %s not found", expected)
	}
}

// BenchmarkNewSecurityPostureWorkflow benchmarks workflow creation
func BenchmarkNewSecurityPostureWorkflow(b *testing.B) {
	options := SecurityPostureOptions{
		IncludeML:             true,
		IncludeImmuneStatus:   true,
		IncludeEthicalMetrics: true,
		IncludeAlignmentCheck: true,
		PredictionTimeframe:   "24h",
		MaxDuration:           5 * time.Minute,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = NewSecurityPostureWorkflow(options)
	}
}
