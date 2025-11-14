package defensive

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/internal/orchestrator"
)

// TestNewThreatHuntingWorkflow tests threat hunting workflow creation
func TestNewThreatHuntingWorkflow(t *testing.T) {
	tests := []struct {
		name            string
		options         ThreatHuntingOptions
		validateWorkflow func(t *testing.T, workflow orchestrator.Workflow)
	}{
		{
			name: "creates workflow with full options",
			options: ThreatHuntingOptions{
				Scope:                  "all",
				ThreatTypes:            []string{"malware", "apt", "lateral_movement"},
				EnableMLPrediction:     true,
				EnableAntibodies:       true,
				EnableAgentCloning:     true,
				InfrastructureTargets:  []string{"192.168.1.0/24", "10.0.0.0/8"},
				MaxDuration:            60 * time.Minute,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, "Proactive Threat Hunting", workflow.Name)
				assert.Equal(t, "defensive", workflow.Category)
				assert.Equal(t, 60*time.Minute, workflow.Timeout)
				assert.Contains(t, workflow.Description, "malware")
				assert.Contains(t, workflow.Description, "apt")
				assert.Contains(t, workflow.Description, "all")

				// Check metadata
				assert.Equal(t, "all", workflow.Metadata["scope"])
				assert.Equal(t, true, workflow.Metadata["ml_prediction"])
				assert.Equal(t, true, workflow.Metadata["preventive_antibodies"])

				// Verify steps exist
				assert.Greater(t, len(workflow.Steps), 0)
			},
		},
		{
			name: "applies default max duration",
			options: ThreatHuntingOptions{
				Scope: "infrastructure",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, 60*time.Minute, workflow.Timeout)
			},
		},
		{
			name: "applies default threat types",
			options: ThreatHuntingOptions{
				Scope: "infrastructure",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should create threat intel query steps for default types
				threatIntelSteps := 0
				for _, step := range workflow.Steps {
					if step.Service == "threat_intel" {
						threatIntelSteps++
					}
				}
				assert.Equal(t, 3, threatIntelSteps) // Default: malware, apt, lateral_movement
			},
		},
		{
			name: "applies default scope",
			options: ThreatHuntingOptions{
				ThreatTypes: []string{"malware"},
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, "infrastructure", workflow.Metadata["scope"])
			},
		},
		{
			name: "creates workflow without ML prediction",
			options: ThreatHuntingOptions{
				Scope:              "infrastructure",
				ThreatTypes:        []string{"malware"},
				EnableMLPrediction: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include prediction step
				predictionSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "predict_future_threats" {
						predictionSteps++
					}
				}
				assert.Equal(t, 0, predictionSteps)
			},
		},
		{
			name: "includes ML prediction when enabled",
			options: ThreatHuntingOptions{
				Scope:              "infrastructure",
				ThreatTypes:        []string{"malware"},
				EnableMLPrediction: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include prediction step
				predictionSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "predict_future_threats" {
						predictionSteps++
					}
				}
				assert.Equal(t, 1, predictionSteps)
			},
		},
		{
			name: "creates infrastructure scanning steps",
			options: ThreatHuntingOptions{
				Scope:                 "infrastructure",
				ThreatTypes:           []string{"malware"},
				InfrastructureTargets: []string{"192.168.1.0/24", "10.0.0.1"},
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should create scan steps for each target (scan + get_results)
				scanSteps := 0
				for _, step := range workflow.Steps {
					if step.Service == "network_recon" {
						scanSteps++
					}
				}
				assert.Equal(t, 4, scanSteps) // 2 targets * 2 steps each (start + get results)
			},
		},
		{
			name: "creates workflow without antibody generation",
			options: ThreatHuntingOptions{
				Scope:            "infrastructure",
				ThreatTypes:      []string{"malware"},
				EnableAntibodies: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include antibody generation step
				antibodySteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "generate_preventive_antibodies" {
						antibodySteps++
					}
				}
				assert.Equal(t, 0, antibodySteps)
			},
		},
		{
			name: "includes antibody generation when enabled",
			options: ThreatHuntingOptions{
				Scope:            "infrastructure",
				ThreatTypes:      []string{"malware"},
				EnableAntibodies: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include antibody generation step
				antibodySteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "generate_preventive_antibodies" {
						antibodySteps++
					}
				}
				assert.Equal(t, 1, antibodySteps)
			},
		},
		{
			name: "creates workflow without agent cloning",
			options: ThreatHuntingOptions{
				Scope:              "infrastructure",
				ThreatTypes:        []string{"malware"},
				EnableAgentCloning: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include agent cloning step
				cloneSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "clone_hunting_agents" {
						cloneSteps++
					}
				}
				assert.Equal(t, 0, cloneSteps)
			},
		},
		{
			name: "includes agent cloning when enabled",
			options: ThreatHuntingOptions{
				Scope:              "infrastructure",
				ThreatTypes:        []string{"malware", "apt"},
				EnableAgentCloning: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include agent cloning step
				cloneSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "clone_hunting_agents" {
						cloneSteps++
					}
				}
				assert.Equal(t, 1, cloneSteps)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewThreatHuntingWorkflow(tt.options)
			require.NotNil(t, workflow)
			tt.validateWorkflow(t, workflow)
		})
	}
}

// TestThreatHuntingWorkflowSteps tests individual workflow steps
func TestThreatHuntingWorkflowSteps(t *testing.T) {
	tests := []struct {
		name         string
		options      ThreatHuntingOptions
		validateSteps func(t *testing.T, steps []orchestrator.WorkflowStep)
	}{
		{
			name: "threat intel query steps configured correctly",
			options: ThreatHuntingOptions{
				Scope:       "infrastructure",
				ThreatTypes: []string{"malware", "apt"},
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Should have 2 threat intel query steps
				threatIntelSteps := 0
				for _, step := range steps {
					if step.Service == "threat_intel" && step.Operation == "QueryThreatIntel" {
						threatIntelSteps++
						assert.Equal(t, orchestrator.ErrorContinue, step.OnError)
						assert.NotNil(t, step.Transform)
					}
				}
				assert.Equal(t, 2, threatIntelSteps)
			},
		},
		{
			name: "ML prediction step configured correctly",
			options: ThreatHuntingOptions{
				Scope:              "infrastructure",
				ThreatTypes:        []string{"malware"},
				EnableMLPrediction: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var predictStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "predict_future_threats" {
						predictStep = &step
						break
					}
				}

				require.NotNil(t, predictStep)
				assert.Equal(t, "maximus_predict", predictStep.Service)
				assert.Equal(t, "Predict", predictStep.Operation)
				assert.NotNil(t, predictStep.Transform)
			},
		},
		{
			name: "autonomous investigation step configured correctly",
			options: ThreatHuntingOptions{
				Scope:       "infrastructure",
				ThreatTypes: []string{"malware"},
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var investigationStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "investigate_predicted_threats" {
						investigationStep = &step
						break
					}
				}

				require.NotNil(t, investigationStep)
				assert.Equal(t, "autonomous_investigation", investigationStep.Service)
				assert.Equal(t, "InitiateInvestigation", investigationStep.Operation)
				assert.NotNil(t, investigationStep.Transform)
			},
		},
		{
			name: "infrastructure scan steps configured correctly",
			options: ThreatHuntingOptions{
				Scope:                 "infrastructure",
				ThreatTypes:           []string{"malware"},
				InfrastructureTargets: []string{"192.168.1.0/24"},
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var scanStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "scan_infrastructure_1_192.168.1.0/24" {
						scanStep = &step
						break
					}
				}

				require.NotNil(t, scanStep)
				assert.Equal(t, "network_recon", scanStep.Service)
				assert.Equal(t, "StartRecon", scanStep.Operation)
				assert.Equal(t, orchestrator.ErrorContinue, scanStep.OnError)
			},
		},
		{
			name: "antibody generation step configured correctly",
			options: ThreatHuntingOptions{
				Scope:            "infrastructure",
				ThreatTypes:      []string{"malware"},
				EnableAntibodies: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var antibodyStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "generate_preventive_antibodies" {
						antibodyStep = &step
						break
					}
				}

				require.NotNil(t, antibodyStep)
				assert.Equal(t, "bcell", antibodyStep.Service)
				assert.Equal(t, "Process", antibodyStep.Operation)
				assert.NotNil(t, antibodyStep.Transform)
			},
		},
		{
			name: "threat insights step configured correctly",
			options: ThreatHuntingOptions{
				Scope:       "infrastructure",
				ThreatTypes: []string{"malware"},
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var insightsStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "generate_threat_insights" {
						insightsStep = &step
						break
					}
				}

				require.NotNil(t, insightsStep)
				assert.Equal(t, "maximus_eureka", insightsStep.Service)
				assert.Equal(t, "GenerateInsight", insightsStep.Operation)
				assert.NotNil(t, insightsStep.Transform)
			},
		},
		{
			name: "agent cloning step configured correctly",
			options: ThreatHuntingOptions{
				Scope:              "infrastructure",
				ThreatTypes:        []string{"malware", "apt"},
				EnableAgentCloning: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var cloneStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "clone_hunting_agents" {
						cloneStep = &step
						break
					}
				}

				require.NotNil(t, cloneStep)
				assert.Equal(t, "lymphnode", cloneStep.Service)
				assert.Equal(t, "CloneAgent", cloneStep.Operation)
				assert.NotNil(t, cloneStep.Transform)

				// Verify clone count (2 agents per threat type)
				// Note: We can't directly access the input here without type assertions
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewThreatHuntingWorkflow(tt.options)
			require.NotNil(t, workflow)
			tt.validateSteps(t, workflow.Steps)
		})
	}
}

// TestThreatHuntingWorkflowStepTransforms tests step transform functions
func TestThreatHuntingWorkflowStepTransforms(t *testing.T) {
	tests := []struct {
		name          string
		stepName      string
		setupCtx      func() *orchestrator.ExecutionContext
		options       ThreatHuntingOptions
		validateCtx   func(t *testing.T, ctx *orchestrator.ExecutionContext)
	}{
		{
			name:     "first threat intel step sets hunt start time",
			stepName: "query_threat_intel_malware",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					CurrentStep: 1,
					Variables:   make(map[string]interface{}),
				}
			},
			options: ThreatHuntingOptions{
				Scope:       "infrastructure",
				ThreatTypes: []string{"malware"},
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				_, ok := ctx.GetVariable("hunt_start_time")
				assert.True(t, ok)
			},
		},
		{
			name:     "prediction transform aggregates threat intel",
			stepName: "predict_future_threats",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Results: map[string]interface{}{
						"query_threat_intel_malware": map[string]interface{}{"threats": []string{"threat1"}},
						"query_threat_intel_apt":     map[string]interface{}{"threats": []string{"threat2"}},
					},
					Variables: make(map[string]interface{}),
				}
			},
			options: ThreatHuntingOptions{
				Scope:              "infrastructure",
				ThreatTypes:        []string{"malware", "apt"},
				EnableMLPrediction: true,
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				predInput, ok := ctx.GetVariable("prediction_input")
				assert.True(t, ok)
				assert.NotNil(t, predInput)
			},
		},
		{
			name:     "investigation transform sets variables",
			stepName: "investigate_predicted_threats",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Results: map[string]interface{}{
						"predict_future_threats": map[string]interface{}{"predictions": []string{"pred1"}},
					},
					Variables: make(map[string]interface{}),
				}
			},
			options: ThreatHuntingOptions{
				Scope:              "infrastructure",
				ThreatTypes:        []string{"malware"},
				EnableMLPrediction: true,
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				target, ok := ctx.GetVariable("investigation_target")
				assert.True(t, ok)
				assert.Equal(t, "predicted_threats", target)

				scope, ok := ctx.GetVariable("investigation_scope")
				assert.True(t, ok)
				assert.Equal(t, "comprehensive", scope)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewThreatHuntingWorkflow(tt.options)

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

// TestThreatHuntingOptions tests the ThreatHuntingOptions structure
func TestThreatHuntingOptions(t *testing.T) {
	options := ThreatHuntingOptions{
		Scope:                  "all",
		ThreatTypes:            []string{"malware", "apt"},
		EnableMLPrediction:     true,
		EnableAntibodies:       true,
		EnableAgentCloning:     true,
		InfrastructureTargets:  []string{"192.168.1.0/24"},
		MaxDuration:            60 * time.Minute,
	}

	assert.Equal(t, "all", options.Scope)
	assert.Len(t, options.ThreatTypes, 2)
	assert.True(t, options.EnableMLPrediction)
	assert.True(t, options.EnableAntibodies)
	assert.True(t, options.EnableAgentCloning)
	assert.Len(t, options.InfrastructureTargets, 1)
	assert.Equal(t, 60*time.Minute, options.MaxDuration)
}

// TestThreatHuntingResult tests the ThreatHuntingResult structure
func TestThreatHuntingResult(t *testing.T) {
	result := ThreatHuntingResult{
		HuntID:              "hunt-123",
		EmergingThreats:     []interface{}{},
		PreventiveAntibodies: []string{"yara-rule-1", "yara-rule-2"},
		ClonedAgents:        4,
		TotalThreatsFound:   10,
		TotalIOCsDiscovered: 25,
		RiskAssessment:      7.5,
		Recommendations:     []string{"Update signatures", "Increase monitoring"},
		TotalDuration:       45 * time.Minute,
	}

	assert.Equal(t, "hunt-123", result.HuntID)
	assert.Len(t, result.PreventiveAntibodies, 2)
	assert.Equal(t, 4, result.ClonedAgents)
	assert.Equal(t, 10, result.TotalThreatsFound)
	assert.Equal(t, 7.5, result.RiskAssessment)
	assert.Len(t, result.Recommendations, 2)
}

// TestThreatHuntingWorkflowStepOrdering tests the order of steps
func TestThreatHuntingWorkflowStepOrdering(t *testing.T) {
	options := ThreatHuntingOptions{
		Scope:                 "infrastructure",
		ThreatTypes:           []string{"malware"},
		EnableMLPrediction:    true,
		EnableAntibodies:      true,
		EnableAgentCloning:    true,
		InfrastructureTargets: []string{"192.168.1.0/24"},
		MaxDuration:           60 * time.Minute,
	}

	workflow := NewThreatHuntingWorkflow(options)

	// Expected order:
	// 1. Threat intel queries (1 per threat type)
	// 2. ML prediction (if enabled)
	// 3. Autonomous investigation
	// 4. Infrastructure scans (2 per target: start + get results)
	// 5. Antibody generation (if enabled)
	// 6. Threat insights
	// 7. Agent cloning (if enabled)

	stepNames := make([]string, len(workflow.Steps))
	for i, step := range workflow.Steps {
		stepNames[i] = step.Name
	}

	// Verify key steps appear in order
	threatIntelIdx := -1
	predictionIdx := -1
	investigationIdx := -1
	insightsIdx := -1

	for i, name := range stepNames {
		if name == "query_threat_intel_malware" {
			threatIntelIdx = i
		}
		if name == "predict_future_threats" {
			predictionIdx = i
		}
		if name == "investigate_predicted_threats" {
			investigationIdx = i
		}
		if name == "generate_threat_insights" {
			insightsIdx = i
		}
	}

	assert.Greater(t, predictionIdx, threatIntelIdx, "Prediction should come after threat intel")
	assert.Greater(t, investigationIdx, predictionIdx, "Investigation should come after prediction")
	assert.Greater(t, insightsIdx, investigationIdx, "Insights should come after investigation")
}

// BenchmarkNewThreatHuntingWorkflow benchmarks workflow creation
func BenchmarkNewThreatHuntingWorkflow(b *testing.B) {
	options := ThreatHuntingOptions{
		Scope:                  "all",
		ThreatTypes:            []string{"malware", "apt", "lateral_movement"},
		EnableMLPrediction:     true,
		EnableAntibodies:       true,
		EnableAgentCloning:     true,
		InfrastructureTargets:  []string{"192.168.1.0/24", "10.0.0.0/8"},
		MaxDuration:            60 * time.Minute,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = NewThreatHuntingWorkflow(options)
	}
}
