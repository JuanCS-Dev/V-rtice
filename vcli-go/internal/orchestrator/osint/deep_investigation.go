package osint

import (
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/internal/data"
	"github.com/verticedev/vcli-go/internal/graph"
	"github.com/verticedev/vcli-go/internal/investigation"
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/narrative"
	"github.com/verticedev/vcli-go/internal/orchestrator"
)

// DeepInvestigationOptions configures the deep investigation workflow
type DeepInvestigationOptions struct {
	Subject            string   // Subject to investigate (person, domain, organization)
	SubjectType        string   // Type: person, domain, organization, network
	Sources            []string // OSINT sources to use
	EnableDataIngestion bool     // Ingest structured data (SINESP, etc.)
	EnableGraphAnalysis bool     // Build knowledge graph
	EnableNarrative    bool     // Analyze narrative manipulation
	MaxDepth           int      // Graph traversal depth
	MaxDuration        time.Duration
}

// DeepInvestigationResult contains comprehensive investigation results
type DeepInvestigationResult struct {
	Subject              string
	OSINTResults         []*investigation.InvestigationReport
	AutonomousInvestResults interface{}
	IngestionResults     []interface{}
	KnowledgeGraph       *graph.FrameworkResponse
	CentralityAnalysis   *graph.CentralityResponse
	CircularityDetected  bool
	NarrativeAnalysis    *narrative.AnalysisResponse
	AIInsights           *maximus.InsightResponse
	TotalDataPoints      int
	TotalRelationships   int
	KeyEntities          []string
	SuspiciousPatterns   []string
	Recommendations      []string
	TotalDuration        time.Duration
}

// NewDeepInvestigationWorkflow creates a comprehensive multi-layer OSINT investigation
//
// This workflow combines 8 services for deep intelligence gathering:
// 1. OSINT Investigation - Collect open-source intelligence
// 2. Autonomous Investigation - Enrich with threat intelligence
// 3. Tatacá Ingestion - Ingest structured data (SINESP, criminal records)
// 4. Seriema Graph Store - Build knowledge graph
// 5. Seriema Centrality - Identify key entities
// 6. Seriema Circular - Detect circular arguments/fraud patterns
// 7. Narrative Filter - Analyze manipulation narratives
// 8. Maximus Eureka - Generate investigative insights
//
// Pipeline:
// OSINT → Enrichment → Data Ingestion → Graph Building → Centrality → Circularity → Narrative → Insights
func NewDeepInvestigationWorkflow(options DeepInvestigationOptions) orchestrator.Workflow {
	if options.MaxDuration == 0 {
		options.MaxDuration = 30 * time.Minute
	}

	if len(options.Sources) == 0 {
		options.Sources = []string{"whois", "dns", "ssl", "social", "news"}
	}

	if options.MaxDepth == 0 {
		options.MaxDepth = 3
	}

	workflow := orchestrator.Workflow{
		Name:        "Deep Investigation",
		Description: fmt.Sprintf("Multi-layer OSINT investigation of %s (%s)", options.Subject, options.SubjectType),
		Category:    "osint",
		Timeout:     options.MaxDuration,
		Metadata: map[string]interface{}{
			"subject":         options.Subject,
			"subject_type":    options.SubjectType,
			"sources":         options.Sources,
			"graph_depth":     options.MaxDepth,
			"investigation_started": time.Now().Format(time.RFC3339),
		},
		Steps: []orchestrator.WorkflowStep{},
	}

	// Step 1-N: OSINT Collection from Multiple Sources
	for i, source := range options.Sources {
		stepName := fmt.Sprintf("osint_source_%d_%s", i+1, source)

		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        stepName,
			Description: fmt.Sprintf("Collect OSINT from %s", source),
			Service:     "osint",
			Operation:   "StartInvestigation",
			Input: investigation.StartInvestigationRequest{
				Query:             options.Subject,
				InvestigationType: options.SubjectType,
				Parameters: map[string]interface{}{
					"sources": []string{source},
				},
			},
			OnError:    orchestrator.ErrorContinue, // Continue even if one source fails
			Timeout:    10 * time.Minute,
			Retries:    2,
			RetryDelay: 15 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				if i == 0 {
					ctx.SetVariable("investigation_start", time.Now())
					ctx.SetVariable("subject", options.Subject)
				}
				return nil
			},
		})

		// Get OSINT results for this source
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        fmt.Sprintf("get_osint_results_%s", source),
			Description: fmt.Sprintf("Retrieve OSINT results from %s", source),
			Service:     "osint",
			Operation:   "GetInvestigationReport",
			Input:       nil, // Will use investigation ID from previous step
			OnError:     orchestrator.ErrorContinue,
			Timeout:     5 * time.Minute,
			Retries:     3,
			RetryDelay:  10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				sourceStepName := fmt.Sprintf("osint_source_%d_%s", i+1, source)
				if result, ok := ctx.GetResult(sourceStepName); ok {
					ctx.SetVariable(fmt.Sprintf("osint_result_%s", source), result)
				}
				return nil
			},
		})
	}

	// Step N+1: Enrich with Autonomous Investigation
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "autonomous_enrichment",
		Description: "Enrich OSINT data with threat intelligence correlation",
		Service:     "autonomous_investigation",
		Operation:   "InitiateInvestigation",
		Input:       nil, // Will use aggregated OSINT results
		OnError:     orchestrator.ErrorContinue,
		Timeout:     10 * time.Minute,
		Retries:     2,
		RetryDelay:  15 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Aggregate all OSINT results for enrichment
			osintData := make([]interface{}, 0)
			for _, source := range options.Sources {
				resultKey := fmt.Sprintf("get_osint_results_%s", source)
				if result, ok := ctx.GetResult(resultKey); ok {
					osintData = append(osintData, result)
				}
			}
			ctx.SetVariable("aggregated_osint", osintData)
			return nil
		},
	})

	// Step N+2: Ingest Structured Data (if enabled)
	if options.EnableDataIngestion {
		// Example: SINESP vehicle data
		if options.SubjectType == "person" || options.SubjectType == "organization" {
			workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
				Name:        "ingest_sinesp_data",
				Description: "Ingest structured data from SINESP and other sources",
				Service:     "tataca_ingestion",
				Operation:   "TriggerIngestion",
				Input: data.TriggerIngestRequest{
					Source: data.DataSourceSinesp,
					Filters: map[string]interface{}{
						"subject": options.Subject,
					},
				},
				OnError:    orchestrator.ErrorContinue,
				Timeout:    10 * time.Minute,
				Retries:    2,
				RetryDelay: 20 * time.Second,
			})

			// Wait for ingestion completion
			workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
				Name:        "get_ingestion_status",
				Description: "Wait for data ingestion to complete",
				Service:     "tataca_ingestion",
				Operation:   "GetJobStatus",
				Input:       nil, // Will use job ID from trigger
				OnError:     orchestrator.ErrorContinue,
				Timeout:     5 * time.Minute,
				Retries:     5,
				RetryDelay:  30 * time.Second,
				Transform: func(ctx *orchestrator.ExecutionContext) error {
					triggerResult, ok := ctx.GetResult("ingest_sinesp_data")
					if ok {
						ctx.SetVariable("ingestion_trigger", triggerResult)
					}
					return nil
				},
			})
		}
	}

	// Step N+3: Build Knowledge Graph (if enabled)
	if options.EnableGraphAnalysis {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "build_knowledge_graph",
			Description: "Construct knowledge graph from investigation data",
			Service:     "seriema_graph",
			Operation:   "StoreFramework",
			Input:       nil, // Will construct graph from all collected data
			OnError:     orchestrator.ErrorContinue,
			Timeout:     5 * time.Minute,
			Retries:     2,
			RetryDelay:  10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Build graph structure from OSINT and investigation results
				arguments := make([]graph.Argument, 0)
				attacks := make([]graph.Attack, 0)

				// Add subject as root node
				arguments = append(arguments, graph.Argument{
					ID:   "subject_root",
					Text: options.Subject,
					Type: options.SubjectType,
				})

				// Extract entities from OSINT results and create edges
				for _, source := range options.Sources {
					resultKey := fmt.Sprintf("get_osint_results_%s", source)
					if _, ok := ctx.GetResult(resultKey); ok {
						// Parse result and extract entities
						arguments = append(arguments, graph.Argument{
							ID:   fmt.Sprintf("%s_data", source),
							Text: fmt.Sprintf("Data from %s", source),
							Type: "evidence",
						})
						attacks = append(attacks, graph.Attack{
							From: "subject_root",
							To:   fmt.Sprintf("%s_data", source),
							Type: "sourced_from",
						})
					}
				}

				framework := graph.Framework{
					Name:      fmt.Sprintf("Investigation: %s", options.Subject),
					Arguments: arguments,
					Attacks:   attacks,
					Metadata: map[string]interface{}{
						"subject":      options.Subject,
						"subject_type": options.SubjectType,
						"created_at":   time.Now().Format(time.RFC3339),
					},
				}

				ctx.SetVariable("knowledge_graph", framework)
				return nil
			},
		})

		// Step N+4: Centrality Analysis
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "centrality_analysis",
			Description: "Identify key entities using centrality metrics",
			Service:     "seriema_graph",
			Operation:   "GetCentrality",
			Input:       nil, // Will use framework ID from graph building
			OnError:     orchestrator.ErrorContinue,
			Timeout:     3 * time.Minute,
			Retries:     2,
			RetryDelay:  10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				graphResult, ok := ctx.GetResult("build_knowledge_graph")
				if ok {
					ctx.SetVariable("framework_id", graphResult)
				}
				return nil
			},
		})

		// Step N+5: Detect Circular Arguments (Fraud Patterns)
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "detect_circular_patterns",
			Description: "Detect circular arguments and potential fraud patterns",
			Service:     "seriema_graph",
			Operation:   "GetCircularArguments",
			Input:       nil, // Will use framework ID
			OnError:     orchestrator.ErrorContinue,
			Timeout:     3 * time.Minute,
			Retries:     2,
			RetryDelay:  10 * time.Second,
		})
	}

	// Step N+6: Narrative Analysis (if enabled)
	if options.EnableNarrative {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "narrative_analysis",
			Description: "Analyze narrative manipulation patterns",
			Service:     "narrative_filter",
			Operation:   "AnalyzeContent",
			Input:       nil, // Will extract text from OSINT results
			OnError:     orchestrator.ErrorContinue,
			Timeout:     10 * time.Minute,
			Retries:     2,
			RetryDelay:  15 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Extract text content from OSINT results for narrative analysis
				narrativeText := fmt.Sprintf("Investigation subject: %s\n", options.Subject)

				// Append text from various sources
				for _, source := range options.Sources {
					resultKey := fmt.Sprintf("get_osint_results_%s", source)
					if result, ok := ctx.GetResult(resultKey); ok {
						narrativeText += fmt.Sprintf("\nSource: %s\nData: %v\n", source, result)
					}
				}

				analysisRequest := narrative.AnalysisRequest{
					Text:        narrativeText,
					EnableTier2: true,
					Priority:    5,
					Metadata: map[string]interface{}{
						"subject":      options.Subject,
						"investigation_type": options.SubjectType,
					},
				}

				ctx.SetVariable("narrative_input", analysisRequest)
				return nil
			},
		})
	}

	// Step N+7: Generate Investigative Insights
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "generate_insights",
		Description: "Generate AI-powered investigative insights",
		Service:     "maximus_eureka",
		Operation:   "GenerateInsight",
		Input:       nil, // Will aggregate all investigation data
		OnError:     orchestrator.ErrorContinue,
		Timeout:     5 * time.Minute,
		Retries:     2,
		RetryDelay:  10 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Aggregate all investigation results
			insightData := map[string]interface{}{
				"subject":              options.Subject,
				"subject_type":         options.SubjectType,
				"osint_sources":        options.Sources,
				"osint_results":        make([]interface{}, 0),
				"autonomous_investigation": ctx.Results["autonomous_enrichment"],
				"ingestion_results":    ctx.Results["get_ingestion_status"],
				"knowledge_graph":      ctx.Results["build_knowledge_graph"],
				"centrality":           ctx.Results["centrality_analysis"],
				"circular_patterns":    ctx.Results["detect_circular_patterns"],
				"narrative_analysis":   ctx.Results["narrative_analysis"],
			}

			// Add all OSINT results
			for _, source := range options.Sources {
				resultKey := fmt.Sprintf("get_osint_results_%s", source)
				if result, ok := ctx.GetResult(resultKey); ok {
					osintResults := insightData["osint_results"].([]interface{})
					insightData["osint_results"] = append(osintResults, result)
				}
			}

			ctx.SetVariable("insight_input", insightData)

			// Calculate total duration
			startTime, _ := ctx.GetVariable("investigation_start")
			if start, ok := startTime.(time.Time); ok {
				duration := time.Since(start)
				ctx.SetVariable("investigation_duration", duration)
			}

			return nil
		},
	})

	return workflow
}
