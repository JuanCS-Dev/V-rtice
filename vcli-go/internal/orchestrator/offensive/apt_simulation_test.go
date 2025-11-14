package offensive

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/internal/orchestrator"
)

// TestNewAPTSimulationWorkflow tests APT simulation workflow creation
func TestNewAPTSimulationWorkflow(t *testing.T) {
	tests := []struct {
		name            string
		options         APTSimulationOptions
		validateWorkflow func(t *testing.T, workflow orchestrator.Workflow)
	}{
		{
			name: "creates workflow with full options",
			options: APTSimulationOptions{
				ActorName:        "APT28",
				TargetDomain:     "example.com",
				SimulationPhases: []string{"reconnaissance", "weaponization", "delivery"},
				EnableNarrative:  true,
				NarrativeContext: "Test narrative context",
				EthicalContext:   "Authorized red team exercise",
				MaxDuration:      90 * time.Minute,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, "APT Simulation", workflow.Name)
				assert.Equal(t, "offensive", workflow.Category)
				assert.Equal(t, 90*time.Minute, workflow.Timeout)
				assert.Contains(t, workflow.Description, "APT28")
				assert.Contains(t, workflow.Description, "example.com")

				// Check metadata
				assert.Equal(t, "APT28", workflow.Metadata["actor"])
				assert.Equal(t, "example.com", workflow.Metadata["target"])
				assert.Equal(t, "Authorized red team exercise", workflow.Metadata["ethical_context"])
				assert.Equal(t, "red_team_simulation", workflow.Metadata["operation_type"])

				// Verify step count: 1 actor profile + 1 threat intel + 1 prediction +
				// 3 phases * 2 (execute + dwell) - 1 (no dwell after last) +
				// 1 narrative + 1 insights + 1 audit = 11 steps
				expectedSteps := 1 + 1 + 1 + (3*2 - 1) + 1 + 1 + 1
				assert.Equal(t, expectedSteps, len(workflow.Steps))
			},
		},
		{
			name: "applies default max duration when not specified",
			options: APTSimulationOptions{
				ActorName:      "Lazarus",
				TargetDomain:   "test.com",
				EthicalContext: "Test",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, 90*time.Minute, workflow.Timeout)
			},
		},
		{
			name: "applies default simulation phases when not specified",
			options: APTSimulationOptions{
				ActorName:      "APT29",
				TargetDomain:   "target.com",
				EthicalContext: "Test",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Default phases: reconnaissance, weaponization, delivery, exploitation
				// Steps: 1 actor + 1 threat intel + 1 prediction + (4*2-1) attack phases + 1 insights + 1 audit = 11
				expectedSteps := 1 + 1 + 1 + (4*2 - 1) + 1 + 1
				assert.GreaterOrEqual(t, len(workflow.Steps), expectedSteps)
			},
		},
		{
			name: "creates workflow without narrative analysis",
			options: APTSimulationOptions{
				ActorName:       "APT28",
				TargetDomain:    "test.com",
				EnableNarrative: false,
				EthicalContext:  "Test",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include narrative analysis step
				narrativeSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "narrative_analysis" {
						narrativeSteps++
					}
				}
				assert.Equal(t, 0, narrativeSteps)
			},
		},
		{
			name: "includes narrative analysis when enabled",
			options: APTSimulationOptions{
				ActorName:        "APT28",
				TargetDomain:     "test.com",
				EnableNarrative:  true,
				NarrativeContext: "Test context",
				EthicalContext:   "Test",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include narrative analysis step
				narrativeSteps := 0
				for _, step := range workflow.Steps {
					if step.Name == "narrative_analysis" {
						narrativeSteps++
					}
				}
				assert.Equal(t, 1, narrativeSteps)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewAPTSimulationWorkflow(tt.options)
			require.NotNil(t, workflow)
			tt.validateWorkflow(t, workflow)
		})
	}
}

// TestAPTSimulationWorkflowSteps tests individual workflow steps
func TestAPTSimulationWorkflowSteps(t *testing.T) {
	tests := []struct {
		name         string
		options      APTSimulationOptions
		validateSteps func(t *testing.T, steps []orchestrator.WorkflowStep)
	}{
		{
			name: "actor profile step configured correctly",
			options: APTSimulationOptions{
				ActorName:      "APT28",
				TargetDomain:   "test.com",
				EthicalContext: "Test",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// First step should be load_actor_profile
				require.Greater(t, len(steps), 0)
				actorStep := steps[0]

				assert.Equal(t, "load_actor_profile", actorStep.Name)
				assert.Equal(t, "autonomous_investigation", actorStep.Service)
				assert.Equal(t, "GetActor", actorStep.Operation)
				assert.Equal(t, orchestrator.ErrorAbort, actorStep.OnError)
				assert.Equal(t, 2, actorStep.Retries)
				assert.NotNil(t, actorStep.Transform)
				assert.NotNil(t, actorStep.Validate)
			},
		},
		{
			name: "threat intel step configured correctly",
			options: APTSimulationOptions{
				ActorName:      "APT28",
				TargetDomain:   "test.com",
				EthicalContext: "Test",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Second step should be query_threat_intel
				require.Greater(t, len(steps), 1)
				threatIntelStep := steps[1]

				assert.Equal(t, "query_threat_intel", threatIntelStep.Name)
				assert.Equal(t, "threat_intel", threatIntelStep.Service)
				assert.Equal(t, "QueryThreatIntel", threatIntelStep.Operation)
				assert.Equal(t, orchestrator.ErrorContinue, threatIntelStep.OnError)
			},
		},
		{
			name: "prediction step configured correctly",
			options: APTSimulationOptions{
				ActorName:      "APT28",
				TargetDomain:   "test.com",
				EthicalContext: "Test",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Third step should be predict_attack_phases
				require.Greater(t, len(steps), 2)
				predictStep := steps[2]

				assert.Equal(t, "predict_attack_phases", predictStep.Name)
				assert.Equal(t, "maximus_oraculo", predictStep.Service)
				assert.Equal(t, "Predict", predictStep.Operation)
				assert.NotNil(t, predictStep.Transform)
			},
		},
		{
			name: "attack phase steps created for each phase",
			options: APTSimulationOptions{
				ActorName:        "APT28",
				TargetDomain:     "test.com",
				SimulationPhases: []string{"reconnaissance", "delivery"},
				EthicalContext:   "Test",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Count attack phase steps
				phaseSteps := 0
				for _, step := range steps {
					if step.Service == "web_attack" && step.Operation == "LaunchAttack" {
						phaseSteps++
					}
				}
				assert.Equal(t, 2, phaseSteps)
			},
		},
		{
			name: "dwell time steps created between phases",
			options: APTSimulationOptions{
				ActorName:        "APT28",
				TargetDomain:     "test.com",
				SimulationPhases: []string{"reconnaissance", "delivery", "exploitation"},
				EthicalContext:   "Test",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Count dwell time steps (should be num_phases - 1)
				dwellSteps := 0
				for _, step := range steps {
					if step.Name[:10] == "dwell_time" {
						dwellSteps++
					}
				}
				assert.Equal(t, 2, dwellSteps) // 3 phases - 1 = 2 dwell steps
			},
		},
		{
			name: "campaign insights step configured correctly",
			options: APTSimulationOptions{
				ActorName:      "APT28",
				TargetDomain:   "test.com",
				EthicalContext: "Test",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Find campaign_insights step
				var insightsStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "campaign_insights" {
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
			name: "ethical audit step configured correctly",
			options: APTSimulationOptions{
				ActorName:      "APT28",
				TargetDomain:   "test.com",
				EthicalContext: "Authorized test",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Last step should be ethical_audit
				require.Greater(t, len(steps), 0)
				auditStep := steps[len(steps)-1]

				assert.Equal(t, "ethical_audit", auditStep.Name)
				assert.Equal(t, "ethical_audit", auditStep.Service)
				assert.Equal(t, "LogDecision", auditStep.Operation)
				assert.NotNil(t, auditStep.Transform)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewAPTSimulationWorkflow(tt.options)
			require.NotNil(t, workflow)
			tt.validateSteps(t, workflow.Steps)
		})
	}
}

// TestAPTSimulationWorkflowStepTransforms tests step transform functions
func TestAPTSimulationWorkflowStepTransforms(t *testing.T) {
	tests := []struct {
		name          string
		stepName      string
		setupCtx      func() *orchestrator.ExecutionContext
		options       APTSimulationOptions
		validateCtx   func(t *testing.T, ctx *orchestrator.ExecutionContext)
	}{
		{
			name:     "actor profile transform sets variables",
			stepName: "load_actor_profile",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Variables: make(map[string]interface{}),
				}
			},
			options: APTSimulationOptions{
				ActorName:      "APT28",
				TargetDomain:   "test.com",
				EthicalContext: "Test",
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				_, ok := ctx.GetVariable("simulation_start")
				assert.True(t, ok)

				actorName, ok := ctx.GetVariable("actor_name")
				assert.True(t, ok)
				assert.Equal(t, "APT28", actorName)
			},
		},
		{
			name:     "prediction transform aggregates results",
			stepName: "predict_attack_phases",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Results: map[string]interface{}{
						"load_actor_profile": map[string]interface{}{"actor": "APT28"},
						"query_threat_intel": map[string]interface{}{"ttps": []string{"T1566"}},
					},
					Variables: make(map[string]interface{}),
				}
			},
			options: APTSimulationOptions{
				ActorName:        "APT28",
				TargetDomain:     "test.com",
				SimulationPhases: []string{"reconnaissance"},
				EthicalContext:   "Test",
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				predInput, ok := ctx.GetVariable("prediction_input")
				assert.True(t, ok)
				assert.NotNil(t, predInput)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewAPTSimulationWorkflow(tt.options)

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

// TestAPTSimulationWorkflowStepValidation tests step validation functions
func TestAPTSimulationWorkflowStepValidation(t *testing.T) {
	tests := []struct {
		name      string
		stepName  string
		result    interface{}
		expectErr bool
	}{
		{
			name:      "actor profile validation passes with valid result",
			stepName:  "load_actor_profile",
			result:    map[string]interface{}{"actor": "APT28"},
			expectErr: false,
		},
		{
			name:      "actor profile validation fails with nil result",
			stepName:  "load_actor_profile",
			result:    nil,
			expectErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			options := APTSimulationOptions{
				ActorName:      "APT28",
				TargetDomain:   "test.com",
				EthicalContext: "Test",
			}

			workflow := NewAPTSimulationWorkflow(options)

			// Find the step with the specified name
			var targetStep *orchestrator.WorkflowStep
			for _, step := range workflow.Steps {
				if step.Name == tt.stepName {
					targetStep = &step
					break
				}
			}

			require.NotNil(t, targetStep, "Step %s not found", tt.stepName)
			require.NotNil(t, targetStep.Validate, "Validate not found for step %s", tt.stepName)

			err := targetStep.Validate(tt.result)

			if tt.expectErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

// TestAPTSimulationWorkflowAttackTypes tests attack type mapping
func TestAPTSimulationWorkflowAttackTypes(t *testing.T) {
	tests := []struct {
		name          string
		phases        []string
		expectedTypes map[string]string
	}{
		{
			name:   "reconnaissance maps to scan",
			phases: []string{"reconnaissance"},
			expectedTypes: map[string]string{
				"reconnaissance": "scan",
			},
		},
		{
			name:   "weaponization maps to xss",
			phases: []string{"weaponization"},
			expectedTypes: map[string]string{
				"weaponization": "xss",
			},
		},
		{
			name:   "delivery maps to sqli",
			phases: []string{"delivery"},
			expectedTypes: map[string]string{
				"delivery": "sqli",
			},
		},
		{
			name:   "exploitation maps to scan",
			phases: []string{"exploitation"},
			expectedTypes: map[string]string{
				"exploitation": "scan",
			},
		},
		{
			name:   "all phases map correctly",
			phases: []string{"reconnaissance", "weaponization", "delivery", "exploitation"},
			expectedTypes: map[string]string{
				"reconnaissance": "scan",
				"weaponization":  "xss",
				"delivery":       "sqli",
				"exploitation":   "scan",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			options := APTSimulationOptions{
				ActorName:        "APT28",
				TargetDomain:     "test.com",
				SimulationPhases: tt.phases,
				EthicalContext:   "Test",
			}

			workflow := NewAPTSimulationWorkflow(options)

			// Find attack execution steps and verify attack types
			for i, phase := range tt.phases {
				stepName := "execute_phase_" + string(rune(i+1)) + "_" + phase

				var attackStep *orchestrator.WorkflowStep
				for _, step := range workflow.Steps {
					if step.Name == stepName {
						attackStep = &step
						break
					}
				}

				require.NotNil(t, attackStep, "Attack step for phase %s not found", phase)

				input, ok := attackStep.Input.(map[string]interface{})
				require.True(t, ok, "Input should be map[string]interface{}")

				attackType, ok := input["attack_type"].(string)
				require.True(t, ok, "attack_type should be string")

				expectedType := tt.expectedTypes[phase]
				assert.Equal(t, expectedType, attackType, "Attack type mismatch for phase %s", phase)
			}
		})
	}
}

// TestAPTSimulationOptions tests the APTSimulationOptions structure
func TestAPTSimulationOptions(t *testing.T) {
	options := APTSimulationOptions{
		ActorName:        "APT28",
		TargetDomain:     "example.com",
		SimulationPhases: []string{"reconnaissance", "delivery"},
		EnableNarrative:  true,
		NarrativeContext: "Test context",
		EthicalContext:   "Authorized",
		MaxDuration:      60 * time.Minute,
	}

	assert.Equal(t, "APT28", options.ActorName)
	assert.Equal(t, "example.com", options.TargetDomain)
	assert.Len(t, options.SimulationPhases, 2)
	assert.True(t, options.EnableNarrative)
	assert.Equal(t, 60*time.Minute, options.MaxDuration)
}

// TestAPTSimulationResult tests the APTSimulationResult structure
func TestAPTSimulationResult(t *testing.T) {
	result := APTSimulationResult{
		ActorName:         "APT28",
		ExecutedPhases:    []string{"reconnaissance", "delivery"},
		PhasesCompleted:   2,
		SimulationSuccess: true,
		TotalDuration:     30 * time.Minute,
		Recommendations:   []string{"Update detection rules", "Enhance monitoring"},
	}

	assert.Equal(t, "APT28", result.ActorName)
	assert.Len(t, result.ExecutedPhases, 2)
	assert.Equal(t, 2, result.PhasesCompleted)
	assert.True(t, result.SimulationSuccess)
	assert.Len(t, result.Recommendations, 2)
}

// BenchmarkNewAPTSimulationWorkflow benchmarks workflow creation
func BenchmarkNewAPTSimulationWorkflow(b *testing.B) {
	options := APTSimulationOptions{
		ActorName:        "APT28",
		TargetDomain:     "test.com",
		SimulationPhases: []string{"reconnaissance", "weaponization", "delivery", "exploitation"},
		EnableNarrative:  true,
		NarrativeContext: "Test",
		EthicalContext:   "Authorized",
		MaxDuration:      90 * time.Minute,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = NewAPTSimulationWorkflow(options)
	}
}
