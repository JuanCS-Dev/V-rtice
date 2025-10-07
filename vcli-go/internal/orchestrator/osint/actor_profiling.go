package osint

import (
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/internal/data"
	"github.com/verticedev/vcli-go/internal/graph"
	"github.com/verticedev/vcli-go/internal/investigation"
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/orchestrator"
	"github.com/verticedev/vcli-go/internal/threat"
)

// ActorProfilingOptions configures the threat actor profiling workflow
type ActorProfilingOptions struct {
	ActorID           string   // Actor identifier (APT28, Lazarus, etc.)
	ActorName         string   // Actor name (if different from ID)
	IncludeOSINT      bool     // Include OSINT on actor infrastructure
	IncludeAttribution bool     // Include incident attribution
	IncludeCampaigns  bool     // Correlate campaigns
	BuildInfraGraph   bool     // Build infrastructure relationship graph
	IngestProfile     bool     // Store profile in Tatacá
	MaxDuration       time.Duration
}

// ActorProfilingResult contains comprehensive actor profile
type ActorProfilingResult struct {
	ActorID              string
	ActorName            string
	ThreatIntel          *threat.ThreatIntelResponse
	OSINTResults         *investigation.InvestigationReport
	ActorProfile         interface{}
	AttributedIncidents  []interface{}
	CorrelatedCampaigns  []interface{}
	InfrastructureGraph  *graph.FrameworkResponse
	AIInsights           *maximus.InsightResponse
	ProfileStored        bool
	KnownTTPs            []string
	KnownInfrastructure  []string
	SophisticationScore  float64
	ActiveCampaigns      int
	Recommendations      []string
	TotalDuration        time.Duration
}

// NewActorProfilingWorkflow creates a comprehensive threat actor profiling workflow
//
// This workflow combines 7 services for complete actor intelligence:
// 1. Threat Intel Query - Fetch actor threat intelligence
// 2. OSINT Investigation - Collect OSINT on actor infrastructure
// 3. Autonomous Investigation GetActor - Retrieve detailed actor profile
// 4. Autonomous Investigation AttributeIncident - Attribute incidents to actor
// 5. Autonomous Investigation CorrelateCampaigns - Correlate actor campaigns
// 6. Seriema Graph - Map infrastructure relationships (C2s, domains, IPs)
// 7. Maximus Eureka - Generate insights on motivation, TTPs, and attribution confidence
// 8. Tatacá Ingestion - Store comprehensive profile (optional)
//
// Pipeline:
// Threat Intel → OSINT → Actor Profile → Attribution → Correlation → Infrastructure Graph → Insights → Storage
func NewActorProfilingWorkflow(options ActorProfilingOptions) orchestrator.Workflow {
	if options.MaxDuration == 0 {
		options.MaxDuration = 40 * time.Minute
	}

	if options.ActorName == "" {
		options.ActorName = options.ActorID
	}

	workflow := orchestrator.Workflow{
		Name:        "Threat Actor Profiling",
		Description: fmt.Sprintf("Comprehensive profiling of threat actor: %s", options.ActorName),
		Category:    "osint",
		Timeout:     options.MaxDuration,
		Metadata: map[string]interface{}{
			"actor_id":        options.ActorID,
			"actor_name":      options.ActorName,
			"profiling_started": time.Now().Format(time.RFC3339),
		},
		Steps: []orchestrator.WorkflowStep{},
	}

	// Step 1: Query Threat Intelligence for Actor
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "query_threat_intel",
		Description: fmt.Sprintf("Query threat intelligence for %s", options.ActorName),
		Service:     "threat_intel",
		Operation:   "QueryThreatIntel",
		Input: map[string]interface{}{
			"indicator":      options.ActorID,
			"indicator_type": "threat_actor",
			"context": map[string]interface{}{
				"enrich_ttps":           true,
				"enrich_infrastructure": true,
				"include_campaigns":     true,
			},
		},
		OnError:    orchestrator.ErrorAbort, // Must have threat intel to proceed
		Timeout:    5 * time.Minute,
		Retries:    2,
		RetryDelay: 15 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			ctx.SetVariable("profiling_start", time.Now())
			ctx.SetVariable("actor_id", options.ActorID)
			return nil
		},
		Validate: func(result interface{}) error {
			if result == nil {
				return fmt.Errorf("no threat intelligence found for actor %s", options.ActorID)
			}
			return nil
		},
	})

	// Step 2: OSINT on Actor Infrastructure (if enabled)
	if options.IncludeOSINT {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "osint_infrastructure",
			Description: "Collect OSINT on actor's known infrastructure",
			Service:     "osint",
			Operation:   "StartInvestigation",
			Input:       nil, // Will extract infrastructure from threat intel
			OnError:     orchestrator.ErrorContinue,
			Timeout:     10 * time.Minute,
			Retries:     2,
			RetryDelay:  15 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Extract infrastructure from threat intel results
				threatIntelResult, ok := ctx.GetResult("query_threat_intel")
				if ok {
					ctx.SetVariable("threat_intel_data", threatIntelResult)

					// Parse infrastructure from threat intel
					// In production, this would extract IPs, domains, etc.
					osintRequest := investigation.StartInvestigationRequest{
						Query:             options.ActorName,
						InvestigationType: "infrastructure",
						Parameters: map[string]interface{}{
							"sources": []string{"whois", "dns", "ssl", "passive_dns"},
						},
					}
					ctx.SetVariable("osint_request", osintRequest)
				}
				return nil
			},
		})

		// Get OSINT results
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "get_osint_results",
			Description: "Retrieve OSINT investigation results",
			Service:     "osint",
			Operation:   "GetInvestigationReport",
			Input:       nil,
			OnError:     orchestrator.ErrorContinue,
			Timeout:     5 * time.Minute,
			Retries:     3,
			RetryDelay:  15 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				osintResult, ok := ctx.GetResult("osint_infrastructure")
				if ok {
					ctx.SetVariable("osint_investigation_id", osintResult)
				}
				return nil
			},
		})
	}

	// Step 3: Retrieve Detailed Actor Profile
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "get_actor_profile",
		Description: "Retrieve comprehensive actor profile from autonomous investigation",
		Service:     "autonomous_investigation",
		Operation:   "GetActor",
		Input: map[string]interface{}{
			"actor_id": options.ActorID,
		},
		OnError:    orchestrator.ErrorContinue, // Continue even if no stored profile
		Timeout:    3 * time.Minute,
		Retries:    2,
		RetryDelay: 10 * time.Second,
	})

	// Step 4: Attribute Incidents to Actor (if enabled)
	if options.IncludeAttribution {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "attribute_incidents",
			Description: "Attribute recent incidents to this actor",
			Service:     "autonomous_investigation",
			Operation:   "AttributeIncident",
			Input:       nil, // Will use actor profile + threat intel
			OnError:     orchestrator.ErrorContinue,
			Timeout:     10 * time.Minute,
			Retries:     2,
			RetryDelay:  15 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Combine actor profile and threat intel for attribution
				actorProfile, _ := ctx.GetResult("get_actor_profile")
				threatIntel, _ := ctx.GetResult("query_threat_intel")

				attributionInput := map[string]interface{}{
					"actor_profile":  actorProfile,
					"threat_intel":   threatIntel,
					"timeframe":      "90d", // Last 90 days
					"confidence_min": 0.6,   // Minimum 60% confidence
				}

				ctx.SetVariable("attribution_input", attributionInput)
				return nil
			},
		})
	}

	// Step 5: Correlate Campaigns (if enabled)
	if options.IncludeCampaigns {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "correlate_campaigns",
			Description: "Correlate actor's campaigns and operations",
			Service:     "autonomous_investigation",
			Operation:   "CorrelateCampaigns",
			Input:       nil, // Will use attribution results
			OnError:     orchestrator.ErrorContinue,
			Timeout:     10 * time.Minute,
			Retries:     2,
			RetryDelay:  15 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				attributionResult, ok := ctx.GetResult("attribute_incidents")
				if ok {
					ctx.SetVariable("attribution_data", attributionResult)
				}
				return nil
			},
		})
	}

	// Step 6: Build Infrastructure Relationship Graph (if enabled)
	if options.BuildInfraGraph {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "build_infrastructure_graph",
			Description: "Map actor's infrastructure relationships (C2s, domains, IPs)",
			Service:     "seriema_graph",
			Operation:   "StoreFramework",
			Input:       nil, // Will construct from threat intel + OSINT
			OnError:     orchestrator.ErrorContinue,
			Timeout:     5 * time.Minute,
			Retries:     2,
			RetryDelay:  10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Build infrastructure graph
				arguments := make([]graph.Argument, 0)
				attacks := make([]graph.Attack, 0)

				// Add actor as root node
				arguments = append(arguments, graph.Argument{
					ID:   options.ActorID,
					Text: options.ActorName,
					Type: "threat_actor",
					Metadata: map[string]interface{}{
						"actor_id": options.ActorID,
					},
				})

				// Parse threat intel for infrastructure
				_, ok := ctx.GetResult("query_threat_intel")
				if ok {
					// In production, parse actual infrastructure data
					// Add C2 servers, domains, IPs as nodes
					arguments = append(arguments, graph.Argument{
						ID:   "c2_infrastructure",
						Text: "C2 Infrastructure",
						Type: "infrastructure",
					})
					attacks = append(attacks, graph.Attack{
						From: options.ActorID,
						To:   "c2_infrastructure",
						Type: "controls",
					})
				}

				// Add OSINT infrastructure
				if options.IncludeOSINT {
					_, ok := ctx.GetResult("get_osint_results")
					if ok {
						arguments = append(arguments, graph.Argument{
							ID:   "osint_infrastructure",
							Text: "OSINT-discovered Infrastructure",
							Type: "infrastructure",
						})
						attacks = append(attacks, graph.Attack{
							From: options.ActorID,
							To:   "osint_infrastructure",
							Type: "uses",
						})
					}
				}

				// Add campaigns as nodes
				if options.IncludeCampaigns {
					_, ok := ctx.GetResult("correlate_campaigns")
					if ok {
						arguments = append(arguments, graph.Argument{
							ID:   "campaigns",
							Text: "Correlated Campaigns",
							Type: "campaign",
						})
						attacks = append(attacks, graph.Attack{
							From: options.ActorID,
							To:   "campaigns",
							Type: "orchestrates",
						})
					}
				}

				framework := graph.Framework{
					Name:      fmt.Sprintf("Actor Infrastructure: %s", options.ActorName),
					Arguments: arguments,
					Attacks:   attacks,
					Metadata: map[string]interface{}{
						"actor_id":   options.ActorID,
						"actor_name": options.ActorName,
						"type":       "infrastructure_graph",
						"created_at": time.Now().Format(time.RFC3339),
					},
				}

				ctx.SetVariable("infrastructure_graph", framework)
				return nil
			},
		})
	}

	// Step 7: Generate AI Insights on Actor
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "generate_actor_insights",
		Description: "Generate AI insights on actor motivation, TTPs, and future targeting",
		Service:     "maximus_eureka",
		Operation:   "GenerateInsight",
		Input:       nil, // Will aggregate all profiling data
		OnError:     orchestrator.ErrorContinue,
		Timeout:     5 * time.Minute,
		Retries:     2,
		RetryDelay:  10 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Aggregate all profiling data
			insightData := map[string]interface{}{
				"actor_id":             options.ActorID,
				"actor_name":           options.ActorName,
				"threat_intel":         ctx.Results["query_threat_intel"],
				"osint_results":        ctx.Results["get_osint_results"],
				"actor_profile":        ctx.Results["get_actor_profile"],
				"attributed_incidents": ctx.Results["attribute_incidents"],
				"campaigns":            ctx.Results["correlate_campaigns"],
				"infrastructure_graph": ctx.Results["build_infrastructure_graph"],
			}

			ctx.SetVariable("insight_data", insightData)
			return nil
		},
	})

	// Step 8: Store Comprehensive Profile (if enabled)
	if options.IngestProfile {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "store_actor_profile",
			Description: "Store comprehensive actor profile in Tatacá",
			Service:     "tataca_ingestion",
			Operation:   "TriggerIngestion",
			Input: data.TriggerIngestRequest{
				Source: data.DataSourceManual,
				Filters: map[string]interface{}{
					"profile_type": "threat_actor",
					"actor_id":     options.ActorID,
				},
			},
			OnError:    orchestrator.ErrorContinue,
			Timeout:    5 * time.Minute,
			Retries:    2,
			RetryDelay: 10 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Calculate total duration
				startTime, _ := ctx.GetVariable("profiling_start")
				if start, ok := startTime.(time.Time); ok {
					duration := time.Since(start)
					ctx.SetVariable("profiling_duration", duration)
				}
				return nil
			},
		})
	}

	return workflow
}
