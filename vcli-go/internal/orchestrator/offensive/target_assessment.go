package offensive

import (
	"fmt"
	"time"

	"github.com/verticedev/vcli-go/internal/ethical"
	"github.com/verticedev/vcli-go/internal/investigation"
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/offensive"
	"github.com/verticedev/vcli-go/internal/orchestrator"
	"github.com/verticedev/vcli-go/internal/threat"
)

// TargetAssessmentOptions configures the target assessment workflow
type TargetAssessmentOptions struct {
	Target          string   // Target IP, domain, or CIDR
	TargetType      string   // Type: ip, domain, cidr
	ReconScope      string   // Recon scope: quick, standard, deep
	EnableOSINT     bool     // Enable OSINT investigation
	EnableVulnScan  bool     // Enable vulnerability scanning
	EnableWebAttack bool     // Enable web attack simulation
	AttackType      string   // Attack type: scan, sqli, xss
	EthicalContext  string   // Ethical justification (required)
	MaxDuration     time.Duration // Maximum workflow duration
}

// TargetAssessmentResult contains the comprehensive assessment results
type TargetAssessmentResult struct {
	Target                string
	ReconResults          *investigation.ReconResult
	OSINTResults          *investigation.InvestigationReport
	ThreatIntelResults    *threat.ThreatIntelResponse
	VulnIntelResults      *threat.VulnResponse
	WebAttackResults      *offensive.AttackResponse
	AIInsights            *maximus.InsightResponse
	EthicalAudit          interface{}
	TotalDuration         time.Duration
	VulnerabilitiesFound  int
	RiskScore             float64
	Recommendations       []string
}

// NewTargetAssessmentWorkflow creates a comprehensive target assessment workflow
//
// This workflow combines 7 services to provide complete target reconnaissance:
// 1. Network Recon - Map attack surface (nmap/masscan)
// 2. OSINT - Collect open-source intelligence
// 3. Threat Intel - Query known IoCs and TTPs
// 4. Vuln Intel - Identify applicable CVEs
// 5. Web Attack - Execute automated scans
// 6. Maximus Eureka - Generate AI-powered insights
// 7. Ethical Audit - Log ethical decision
//
// Pipeline:
// Network Recon → OSINT → Threat Intel → Vuln Intel → Web Attack → AI Insights → Ethical Audit
func NewTargetAssessmentWorkflow(options TargetAssessmentOptions) orchestrator.Workflow {
	if options.MaxDuration == 0 {
		options.MaxDuration = 45 * time.Minute
	}

	if options.ReconScope == "" {
		options.ReconScope = "standard"
	}

	if options.AttackType == "" {
		options.AttackType = "scan"
	}

	workflow := orchestrator.Workflow{
		Name:        "Target Assessment",
		Description: fmt.Sprintf("Comprehensive security assessment of target: %s", options.Target),
		Category:    "offensive",
		Timeout:     options.MaxDuration,
		Metadata: map[string]interface{}{
			"target":          options.Target,
			"target_type":     options.TargetType,
			"ethical_context": options.EthicalContext,
			"timestamp":       time.Now().Format(time.RFC3339),
		},
		Steps: []orchestrator.WorkflowStep{},
	}

	// Step 1: Network Reconnaissance
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "network_recon",
		Description: "Map attack surface using nmap/masscan",
		Service:     "network_recon",
		Operation:   "StartRecon",
		Input: investigation.StartReconRequest{
			Target:   options.Target,
			ScanType: options.ReconScope,
		},
		OnError: orchestrator.ErrorAbort,
		Timeout: 15 * time.Minute,
		Retries: 2,
		RetryDelay: 30 * time.Second,
		Validate: func(result interface{}) error {
			reconResp, ok := result.(*investigation.ReconTask)
			if !ok {
				return fmt.Errorf("invalid recon response type")
			}
			if reconResp.ID == "" {
				return fmt.Errorf("no recon ID returned")
			}
			return nil
		},
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			ctx.SetVariable("start_time", time.Now())
			ctx.SetVariable("target", options.Target)
			return nil
		},
	})

	// Step 2: Wait for recon completion & get results
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "get_recon_results",
		Description: "Retrieve network reconnaissance results",
		Service:     "network_recon",
		Operation:   "GetReconResults",
		Input:       nil, // Will be populated from previous step
		OnError:     orchestrator.ErrorAbort,
		Timeout:     10 * time.Minute,
		Retries:     5,
		RetryDelay:  30 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Get recon ID from previous step
			reconResult, ok := ctx.GetResult("network_recon")
			if !ok {
				return fmt.Errorf("network_recon result not found")
			}
			reconResp := reconResult.(*investigation.ReconTask)
			ctx.SetVariable("recon_id", reconResp.ID)
			return nil
		},
	})

	// Step 3: OSINT Investigation (optional)
	if options.EnableOSINT {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "osint_investigation",
			Description: "Collect open-source intelligence",
			Service:     "osint",
			Operation:   "StartInvestigation",
			Input: investigation.StartInvestigationRequest{
				Query:             options.Target,
				InvestigationType: "domain",
				Parameters: map[string]interface{}{
					"sources": []string{"whois", "dns", "ssl", "social"},
				},
			},
			OnError:    orchestrator.ErrorContinue, // Continue even if OSINT fails
			Timeout:    10 * time.Minute,
			Retries:    2,
			RetryDelay: 15 * time.Second,
		})

		// Get OSINT results
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "get_osint_results",
			Description: "Retrieve OSINT investigation results",
			Service:     "osint",
			Operation:   "GetInvestigationReport",
			Input:       nil, // Populated from previous step
			OnError:     orchestrator.ErrorContinue,
			Timeout:     5 * time.Minute,
			Retries:     3,
			RetryDelay:  20 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				osintResult, ok := ctx.GetResult("osint_investigation")
				if !ok {
					return fmt.Errorf("osint_investigation result not found")
				}
				osintResp := osintResult.(*investigation.StartInvestigationResponse)
				ctx.SetVariable("investigation_id", osintResp.InvestigationID)
				return nil
			},
		})
	}

	// Step 4: Threat Intelligence Query
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "threat_intel",
		Description: "Query threat intelligence for known IoCs",
		Service:     "threat_intel",
		Operation:   "QueryThreatIntel",
		Input: map[string]interface{}{
			"indicator":      options.Target,
			"indicator_type": options.TargetType,
		},
		OnError:    orchestrator.ErrorContinue,
		Timeout:    3 * time.Minute,
		Retries:    2,
		RetryDelay: 10 * time.Second,
	})

	// Step 5: Vulnerability Intelligence (if enabled)
	if options.EnableVulnScan {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "vuln_intel",
			Description: "Identify applicable CVEs and vulnerabilities",
			Service:     "vuln_intel",
			Operation:   "QueryVulnerability",
			Input:       nil, // Will extract from recon results
			OnError:     orchestrator.ErrorContinue,
			Timeout:     5 * time.Minute,
			Retries:     2,
			RetryDelay:  15 * time.Second,
			Transform: func(ctx *orchestrator.ExecutionContext) error {
				// Extract product/version from recon results
				reconResults, ok := ctx.GetResult("get_recon_results")
				if ok {
					ctx.SetVariable("recon_data", reconResults)
				}
				return nil
			},
		})
	}

	// Step 6: Web Attack Scan (if enabled)
	if options.EnableWebAttack {
		workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
			Name:        "web_attack",
			Description: fmt.Sprintf("Execute %s attack scan", options.AttackType),
			Service:     "web_attack",
			Operation:   "LaunchAttack",
			Input: map[string]interface{}{
				"target_url":  fmt.Sprintf("http://%s", options.Target),
				"attack_type": options.AttackType,
			},
			OnError:    orchestrator.ErrorContinue, // Don't abort on scan failure
			Timeout:    20 * time.Minute,
			Retries:    1,
			RetryDelay: 30 * time.Second,
		})
	}

	// Step 7: AI-Powered Insights (Maximus Eureka)
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "ai_insights",
		Description: "Generate AI-powered attack vector insights",
		Service:     "maximus_eureka",
		Operation:   "GenerateInsight",
		Input:       nil, // Will aggregate all previous results
		OnError:     orchestrator.ErrorContinue,
		Timeout:     5 * time.Minute,
		Retries:     2,
		RetryDelay:  10 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			// Aggregate all results for AI analysis
			aggregated := map[string]interface{}{
				"target":         options.Target,
				"recon_results":  ctx.Results["get_recon_results"],
				"osint_results":  ctx.Results["get_osint_results"],
				"threat_intel":   ctx.Results["threat_intel"],
				"vuln_intel":     ctx.Results["vuln_intel"],
				"attack_results": ctx.Results["web_attack"],
			}
			ctx.SetVariable("aggregated_data", aggregated)
			return nil
		},
	})

	// Step 8: Ethical Audit Logging
	workflow.Steps = append(workflow.Steps, orchestrator.WorkflowStep{
		Name:        "ethical_audit",
		Description: "Log ethical decision and authorization",
		Service:     "ethical_audit",
		Operation:   "LogDecision",
		Input: ethical.EthicalDecisionLog{
			DecisionID:             "",
			RequestID:              "",
			ServiceName:            "target_assessment",
			DecisionType:           "offensive_operation",
			Context: map[string]interface{}{
				"target":        options.Target,
				"justification": options.EthicalContext,
				"authorized":    true,
			},
			KantianResult:          map[string]interface{}{},
			ConsequentialistResult: map[string]interface{}{},
			VirtueResult:           map[string]interface{}{},
			PrinciplismResult:      map[string]interface{}{},
			FinalDecision:          map[string]interface{}{},
		},
		OnError:    orchestrator.ErrorContinue, // Log but don't fail workflow
		Timeout:    2 * time.Minute,
		Retries:    2,
		RetryDelay: 5 * time.Second,
		Transform: func(ctx *orchestrator.ExecutionContext) error {
			startTime, _ := ctx.GetVariable("start_time")
			if start, ok := startTime.(time.Time); ok {
				duration := time.Since(start).Minutes()
				ctx.SetVariable("total_duration_minutes", duration)
			}
			return nil
		},
	})

	return workflow
}
