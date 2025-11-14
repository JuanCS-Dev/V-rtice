package osint

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/internal/investigation"
	"github.com/verticedev/vcli-go/internal/orchestrator"
)

// TestNewDeepInvestigationWorkflow tests deep investigation workflow creation
func TestNewDeepInvestigationWorkflow(t *testing.T) {
	tests := []struct {
		name            string
		options         DeepInvestigationOptions
		validateWorkflow func(t *testing.T, workflow orchestrator.Workflow)
	}{
		{
			name: "creates workflow with full options",
			options: DeepInvestigationOptions{
				Subject:             "example.com",
				SubjectType:         "domain",
				Sources:             []string{"whois", "dns", "ssl", "social"},
				EnableDataIngestion: true,
				EnableGraphAnalysis: true,
				EnableNarrative:     true,
				MaxDepth:            3,
				MaxDuration:         30 * time.Minute,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, "Deep Investigation", workflow.Name)
				assert.Equal(t, "osint", workflow.Category)
				assert.Equal(t, 30*time.Minute, workflow.Timeout)
				assert.Contains(t, workflow.Description, "example.com")
				assert.Contains(t, workflow.Description, "domain")

				// Check metadata
				assert.Equal(t, "example.com", workflow.Metadata["subject"])
				assert.Equal(t, "domain", workflow.Metadata["subject_type"])
				assert.Equal(t, 3, workflow.Metadata["graph_depth"])

				// Verify steps exist
				assert.Greater(t, len(workflow.Steps), 0)
			},
		},
		{
			name: "applies default max duration",
			options: DeepInvestigationOptions{
				Subject:     "test.com",
				SubjectType: "domain",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, 30*time.Minute, workflow.Timeout)
			},
		},
		{
			name: "applies default sources",
			options: DeepInvestigationOptions{
				Subject:     "test.com",
				SubjectType: "domain",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should use default sources: whois, dns, ssl, social, news
				osintSteps := 0
				for _, step := range workflow.Steps {
					if step.Service == "osint" && step.Operation == "StartInvestigation" {
						osintSteps++
					}
				}
				assert.Equal(t, 5, osintSteps) // 5 default sources
			},
		},
		{
			name: "applies default max depth",
			options: DeepInvestigationOptions{
				Subject:     "test.com",
				SubjectType: "domain",
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				assert.Equal(t, 3, workflow.Metadata["graph_depth"])
			},
		},
		{
			name: "creates workflow without data ingestion",
			options: DeepInvestigationOptions{
				Subject:             "test.com",
				SubjectType:         "domain",
				EnableDataIngestion: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include ingestion steps
				ingestionSteps := 0
				for _, step := range workflow.Steps {
					if step.Service == "tataca_ingestion" {
						ingestionSteps++
					}
				}
				assert.Equal(t, 0, ingestionSteps)
			},
		},
		{
			name: "includes data ingestion when enabled for person",
			options: DeepInvestigationOptions{
				Subject:             "John Doe",
				SubjectType:         "person",
				EnableDataIngestion: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include ingestion steps for person
				ingestionSteps := 0
				for _, step := range workflow.Steps {
					if step.Service == "tataca_ingestion" {
						ingestionSteps++
					}
				}
				assert.Equal(t, 2, ingestionSteps) // trigger + status
			},
		},
		{
			name: "includes data ingestion for organization",
			options: DeepInvestigationOptions{
				Subject:             "ACME Corp",
				SubjectType:         "organization",
				EnableDataIngestion: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				ingestionSteps := 0
				for _, step := range workflow.Steps {
					if step.Service == "tataca_ingestion" {
						ingestionSteps++
					}
				}
				assert.Equal(t, 2, ingestionSteps) // trigger + status
			},
		},
		{
			name: "skips data ingestion for domain subject type",
			options: DeepInvestigationOptions{
				Subject:             "example.com",
				SubjectType:         "domain",
				EnableDataIngestion: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				ingestionSteps := 0
				for _, step := range workflow.Steps {
					if step.Service == "tataca_ingestion" {
						ingestionSteps++
					}
				}
				assert.Equal(t, 0, ingestionSteps) // No ingestion for domain
			},
		},
		{
			name: "creates workflow without graph analysis",
			options: DeepInvestigationOptions{
				Subject:             "test.com",
				SubjectType:         "domain",
				EnableGraphAnalysis: false,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should not include graph analysis steps
				graphSteps := 0
				for _, step := range workflow.Steps {
					if step.Service == "seriema_graph" {
						graphSteps++
					}
				}
				assert.Equal(t, 0, graphSteps)
			},
		},
		{
			name: "includes graph analysis when enabled",
			options: DeepInvestigationOptions{
				Subject:             "test.com",
				SubjectType:         "domain",
				EnableGraphAnalysis: true,
			},
			validateWorkflow: func(t *testing.T, workflow orchestrator.Workflow) {
				// Should include graph steps: build, centrality, circular
				graphSteps := 0
				for _, step := range workflow.Steps {
					if step.Service == "seriema_graph" {
						graphSteps++
					}
				}
				assert.Equal(t, 3, graphSteps)
			},
		},
		{
			name: "creates workflow without narrative analysis",
			options: DeepInvestigationOptions{
				Subject:         "test.com",
				SubjectType:     "domain",
				EnableNarrative: false,
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
			options: DeepInvestigationOptions{
				Subject:         "test.com",
				SubjectType:     "domain",
				EnableNarrative: true,
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
			workflow := NewDeepInvestigationWorkflow(tt.options)
			require.NotNil(t, workflow)
			tt.validateWorkflow(t, workflow)
		})
	}
}

// TestDeepInvestigationWorkflowSteps tests individual workflow steps
func TestDeepInvestigationWorkflowSteps(t *testing.T) {
	tests := []struct {
		name         string
		options      DeepInvestigationOptions
		validateSteps func(t *testing.T, steps []orchestrator.WorkflowStep)
	}{
		{
			name: "OSINT collection steps configured correctly",
			options: DeepInvestigationOptions{
				Subject:     "test.com",
				SubjectType: "domain",
				Sources:     []string{"whois", "dns"},
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				// Should have 2 OSINT start steps + 2 get results steps = 4 total
				osintSteps := 0
				for _, step := range steps {
					if step.Service == "osint" {
						osintSteps++
					}
				}
				assert.Equal(t, 4, osintSteps)

				// Check first OSINT step
				var firstOSINTStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "osint_source_1_whois" {
						firstOSINTStep = &step
						break
					}
				}

				require.NotNil(t, firstOSINTStep)
				assert.Equal(t, "osint", firstOSINTStep.Service)
				assert.Equal(t, "StartInvestigation", firstOSINTStep.Operation)
				assert.Equal(t, orchestrator.ErrorContinue, firstOSINTStep.OnError)
				assert.NotNil(t, firstOSINTStep.Transform)
			},
		},
		{
			name: "autonomous enrichment step configured correctly",
			options: DeepInvestigationOptions{
				Subject:     "test.com",
				SubjectType: "domain",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var enrichmentStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "autonomous_enrichment" {
						enrichmentStep = &step
						break
					}
				}

				require.NotNil(t, enrichmentStep)
				assert.Equal(t, "autonomous_investigation", enrichmentStep.Service)
				assert.Equal(t, "InitiateInvestigation", enrichmentStep.Operation)
				assert.NotNil(t, enrichmentStep.Transform)
			},
		},
		{
			name: "data ingestion steps configured correctly",
			options: DeepInvestigationOptions{
				Subject:             "John Doe",
				SubjectType:         "person",
				EnableDataIngestion: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var triggerStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "ingest_sinesp_data" {
						triggerStep = &step
						break
					}
				}

				require.NotNil(t, triggerStep)
				assert.Equal(t, "tataca_ingestion", triggerStep.Service)
				assert.Equal(t, "TriggerIngestion", triggerStep.Operation)
			},
		},
		{
			name: "graph building step configured correctly",
			options: DeepInvestigationOptions{
				Subject:             "test.com",
				SubjectType:         "domain",
				EnableGraphAnalysis: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var graphStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "build_knowledge_graph" {
						graphStep = &step
						break
					}
				}

				require.NotNil(t, graphStep)
				assert.Equal(t, "seriema_graph", graphStep.Service)
				assert.Equal(t, "StoreFramework", graphStep.Operation)
				assert.NotNil(t, graphStep.Transform)
			},
		},
		{
			name: "centrality analysis step configured correctly",
			options: DeepInvestigationOptions{
				Subject:             "test.com",
				SubjectType:         "domain",
				EnableGraphAnalysis: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var centralityStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "centrality_analysis" {
						centralityStep = &step
						break
					}
				}

				require.NotNil(t, centralityStep)
				assert.Equal(t, "seriema_graph", centralityStep.Service)
				assert.Equal(t, "GetCentrality", centralityStep.Operation)
				assert.NotNil(t, centralityStep.Transform)
			},
		},
		{
			name: "circular pattern detection step configured correctly",
			options: DeepInvestigationOptions{
				Subject:             "test.com",
				SubjectType:         "domain",
				EnableGraphAnalysis: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var circularStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "detect_circular_patterns" {
						circularStep = &step
						break
					}
				}

				require.NotNil(t, circularStep)
				assert.Equal(t, "seriema_graph", circularStep.Service)
				assert.Equal(t, "GetCircularArguments", circularStep.Operation)
			},
		},
		{
			name: "narrative analysis step configured correctly",
			options: DeepInvestigationOptions{
				Subject:         "test.com",
				SubjectType:     "domain",
				EnableNarrative: true,
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var narrativeStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "narrative_analysis" {
						narrativeStep = &step
						break
					}
				}

				require.NotNil(t, narrativeStep)
				assert.Equal(t, "narrative_filter", narrativeStep.Service)
				assert.Equal(t, "AnalyzeContent", narrativeStep.Operation)
				assert.NotNil(t, narrativeStep.Transform)
			},
		},
		{
			name: "insights generation step configured correctly",
			options: DeepInvestigationOptions{
				Subject:     "test.com",
				SubjectType: "domain",
			},
			validateSteps: func(t *testing.T, steps []orchestrator.WorkflowStep) {
				var insightsStep *orchestrator.WorkflowStep
				for _, step := range steps {
					if step.Name == "generate_insights" {
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
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewDeepInvestigationWorkflow(tt.options)
			require.NotNil(t, workflow)
			tt.validateSteps(t, workflow.Steps)
		})
	}
}

// TestDeepInvestigationWorkflowStepTransforms tests step transform functions
func TestDeepInvestigationWorkflowStepTransforms(t *testing.T) {
	tests := []struct {
		name          string
		stepName      string
		setupCtx      func() *orchestrator.ExecutionContext
		options       DeepInvestigationOptions
		validateCtx   func(t *testing.T, ctx *orchestrator.ExecutionContext)
	}{
		{
			name:     "first OSINT step sets investigation start",
			stepName: "osint_source_1_whois",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Variables: make(map[string]interface{}),
				}
			},
			options: DeepInvestigationOptions{
				Subject:     "test.com",
				SubjectType: "domain",
				Sources:     []string{"whois"},
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				_, ok := ctx.GetVariable("investigation_start")
				assert.True(t, ok)

				subject, ok := ctx.GetVariable("subject")
				assert.True(t, ok)
				assert.Equal(t, "test.com", subject)
			},
		},
		{
			name:     "autonomous enrichment aggregates OSINT data",
			stepName: "autonomous_enrichment",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Results: map[string]interface{}{
						"get_osint_results_whois": map[string]interface{}{"data": "whois_data"},
						"get_osint_results_dns":   map[string]interface{}{"data": "dns_data"},
					},
					Variables: make(map[string]interface{}),
				}
			},
			options: DeepInvestigationOptions{
				Subject:     "test.com",
				SubjectType: "domain",
				Sources:     []string{"whois", "dns"},
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				aggregated, ok := ctx.GetVariable("aggregated_osint")
				assert.True(t, ok)
				assert.NotNil(t, aggregated)

				// Should have 2 entries
				osintData := aggregated.([]interface{})
				assert.Len(t, osintData, 2)
			},
		},
		{
			name:     "graph building creates framework structure",
			stepName: "build_knowledge_graph",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Results: map[string]interface{}{
						"get_osint_results_whois": map[string]interface{}{"data": "whois_data"},
					},
					Variables: make(map[string]interface{}),
				}
			},
			options: DeepInvestigationOptions{
				Subject:             "test.com",
				SubjectType:         "domain",
				Sources:             []string{"whois"},
				EnableGraphAnalysis: true,
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				framework, ok := ctx.GetVariable("knowledge_graph")
				assert.True(t, ok)
				assert.NotNil(t, framework)
			},
		},
		{
			name:     "insights generation aggregates all results",
			stepName: "generate_insights",
			setupCtx: func() *orchestrator.ExecutionContext {
				return &orchestrator.ExecutionContext{
					Results: map[string]interface{}{
						"get_osint_results_whois": map[string]interface{}{"data": "whois_data"},
						"autonomous_enrichment":   map[string]interface{}{"enriched": true},
					},
					Variables: map[string]interface{}{
						"investigation_start": time.Now(),
					},
				}
			},
			options: DeepInvestigationOptions{
				Subject:     "test.com",
				SubjectType: "domain",
				Sources:     []string{"whois"},
			},
			validateCtx: func(t *testing.T, ctx *orchestrator.ExecutionContext) {
				insightInput, ok := ctx.GetVariable("insight_input")
				assert.True(t, ok)
				assert.NotNil(t, insightInput)

				_, ok = ctx.GetVariable("investigation_duration")
				assert.True(t, ok)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workflow := NewDeepInvestigationWorkflow(tt.options)

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

// TestDeepInvestigationOptions tests the DeepInvestigationOptions structure
func TestDeepInvestigationOptions(t *testing.T) {
	options := DeepInvestigationOptions{
		Subject:             "example.com",
		SubjectType:         "domain",
		Sources:             []string{"whois", "dns", "ssl"},
		EnableDataIngestion: true,
		EnableGraphAnalysis: true,
		EnableNarrative:     true,
		MaxDepth:            3,
		MaxDuration:         30 * time.Minute,
	}

	assert.Equal(t, "example.com", options.Subject)
	assert.Equal(t, "domain", options.SubjectType)
	assert.Len(t, options.Sources, 3)
	assert.True(t, options.EnableDataIngestion)
	assert.True(t, options.EnableGraphAnalysis)
	assert.True(t, options.EnableNarrative)
	assert.Equal(t, 3, options.MaxDepth)
	assert.Equal(t, 30*time.Minute, options.MaxDuration)
}

// TestDeepInvestigationResult tests the DeepInvestigationResult structure
func TestDeepInvestigationResult(t *testing.T) {
	result := DeepInvestigationResult{
		Subject:             "example.com",
		OSINTResults:        []*investigation.InvestigationReport{},
		CircularityDetected: true,
		TotalDataPoints:     150,
		TotalRelationships:  75,
		KeyEntities:         []string{"entity1", "entity2"},
		SuspiciousPatterns:  []string{"pattern1"},
		Recommendations:     []string{"Further investigation needed"},
		TotalDuration:       25 * time.Minute,
	}

	assert.Equal(t, "example.com", result.Subject)
	assert.True(t, result.CircularityDetected)
	assert.Equal(t, 150, result.TotalDataPoints)
	assert.Equal(t, 75, result.TotalRelationships)
	assert.Len(t, result.KeyEntities, 2)
	assert.Len(t, result.SuspiciousPatterns, 1)
	assert.Len(t, result.Recommendations, 1)
}

// TestDeepInvestigationWorkflowStepOrdering tests the order of steps
func TestDeepInvestigationWorkflowStepOrdering(t *testing.T) {
	options := DeepInvestigationOptions{
		Subject:             "example.com",
		SubjectType:         "domain",
		Sources:             []string{"whois"},
		EnableDataIngestion: false,
		EnableGraphAnalysis: true,
		EnableNarrative:     true,
		MaxDepth:            3,
		MaxDuration:         30 * time.Minute,
	}

	workflow := NewDeepInvestigationWorkflow(options)

	// Expected order:
	// 1. OSINT collection (start + get results per source)
	// 2. Autonomous enrichment
	// 3. Graph building
	// 4. Centrality analysis
	// 5. Circular pattern detection
	// 6. Narrative analysis
	// 7. Insights generation

	stepNames := make([]string, len(workflow.Steps))
	for i, step := range workflow.Steps {
		stepNames[i] = step.Name
	}

	// Verify key steps appear in order
	enrichmentIdx := -1
	graphIdx := -1
	narrativeIdx := -1
	insightsIdx := -1

	for i, name := range stepNames {
		if name == "autonomous_enrichment" {
			enrichmentIdx = i
		}
		if name == "build_knowledge_graph" {
			graphIdx = i
		}
		if name == "narrative_analysis" {
			narrativeIdx = i
		}
		if name == "generate_insights" {
			insightsIdx = i
		}
	}

	assert.Greater(t, graphIdx, enrichmentIdx, "Graph building should come after enrichment")
	assert.Greater(t, narrativeIdx, graphIdx, "Narrative should come after graph")
	assert.Greater(t, insightsIdx, narrativeIdx, "Insights should come after narrative")
}

// BenchmarkNewDeepInvestigationWorkflow benchmarks workflow creation
func BenchmarkNewDeepInvestigationWorkflow(b *testing.B) {
	options := DeepInvestigationOptions{
		Subject:             "example.com",
		SubjectType:         "domain",
		Sources:             []string{"whois", "dns", "ssl", "social", "news"},
		EnableDataIngestion: true,
		EnableGraphAnalysis: true,
		EnableNarrative:     true,
		MaxDepth:            3,
		MaxDuration:         30 * time.Minute,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = NewDeepInvestigationWorkflow(options)
	}
}
