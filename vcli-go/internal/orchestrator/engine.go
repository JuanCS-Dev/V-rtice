package orchestrator

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/verticedev/vcli-go/internal/data"
	"github.com/verticedev/vcli-go/internal/ethical"
	"github.com/verticedev/vcli-go/internal/graph"
	"github.com/verticedev/vcli-go/internal/hcl"
	"github.com/verticedev/vcli-go/internal/immunis"
	"github.com/verticedev/vcli-go/internal/investigation"
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/narrative"
	"github.com/verticedev/vcli-go/internal/offensive"
	"github.com/verticedev/vcli-go/internal/threat"
	"github.com/verticedev/vcli-go/internal/triage"
)

// OrchestrationEngine coordinates multi-service workflows
type OrchestrationEngine struct {
	// Service clients (all 23 integrated services)

	// Maximus AI (4 services)
	MaximusEureka  *maximus.EurekaClient
	MaximusOraculo *maximus.OraculoClient
	MaximusPredict *maximus.PredictClient

	// Immunis System (5 services)
	LymphnodeClient      *immunis.LymphnodeClient
	MacrophageClient     *immunis.MacrophageClient
	BCellClient          *immunis.BCellClient
	HelperTClient        *immunis.HelperTClient
	CytotoxicTClient     *immunis.CytotoxicTClient

	// Investigation & Recon (3 services)
	AutonomousInvestigation *investigation.InvestigationClient
	NetworkRecon            *investigation.ReconClient
	OSINT                   *investigation.OSINTClient

	// HCL (3 services)
	HCLAnalyzer  *hcl.AnalyzerClient
	HCLPlanner   *hcl.PlannerClient
	HCLExecutor  *hcl.ExecutorClient

	// Ethical (2 services)
	EthicalAudit *ethical.AuditClient
	HSAS         *ethical.HSASClient

	// Threat Intel (2 services)
	ThreatIntel *threat.IntelClient
	VulnIntel   *threat.VulnClient

	// Offensive (1 service)
	WebAttack *offensive.WebAttackClient

	// Data & Graph (3 services)
	SeriemaGraph    *graph.SeriemaClient
	TatacaIngestion *data.IngestionClient
	NarrativeFilter *narrative.NarrativeClient

	// Triage & RTE (1 service)
	RTE *triage.RTEClient

	// Workflow tracking for async execution
	runningWorkflows map[string]*ExecutionContext
	mu               sync.RWMutex

	// Configuration
	defaultTimeout time.Duration
	logger         *log.Logger
}

// EngineConfig holds configuration for the orchestration engine
type EngineConfig struct {
	// Endpoint URLs for all services
	MaximusEurekaEndpoint   string
	MaximusOraculoEndpoint  string
	MaximusPredictEndpoint  string
	LymphnodeEndpoint       string
	MacrophageEndpoint      string
	BCellEndpoint           string
	HelperTEndpoint         string
	CytotoxicTEndpoint      string
	AutonomousInvestEndpoint string
	ReconEndpoint           string
	OSINTEndpoint           string
	HCLAnalyzerEndpoint     string
	HCLPlannerEndpoint      string
	HCLExecutorEndpoint     string
	EthicalAuditEndpoint    string
	HSASEndpoint            string
	ThreatIntelEndpoint     string
	VulnIntelEndpoint       string
	WebAttackEndpoint       string
	SeriemaGraphEndpoint    string
	TatacaIngestionEndpoint string
	NarrativeFilterEndpoint string
	RTEEndpoint             string

	// Authentication
	AuthToken string

	// Timeouts
	DefaultTimeout time.Duration

	// Logger
	Logger *log.Logger
}

// NewOrchestrationEngine creates a new orchestration engine with all service clients
func NewOrchestrationEngine(config EngineConfig) *OrchestrationEngine {
	if config.DefaultTimeout == 0 {
		config.DefaultTimeout = 30 * time.Minute // Default 30 min for long workflows
	}

	if config.Logger == nil {
		config.Logger = log.Default()
	}

	return &OrchestrationEngine{
		// Initialize all service clients
		MaximusEureka:  maximus.NewEurekaClient(config.MaximusEurekaEndpoint, config.AuthToken),
		MaximusOraculo: maximus.NewOraculoClient(config.MaximusOraculoEndpoint, config.AuthToken),
		MaximusPredict: maximus.NewPredictClient(config.MaximusPredictEndpoint, config.AuthToken),

		LymphnodeClient:  immunis.NewLymphnodeClient(config.LymphnodeEndpoint, config.AuthToken),
		MacrophageClient: immunis.NewMacrophageClient(config.MacrophageEndpoint, config.AuthToken),
		BCellClient:      immunis.NewBCellClient(config.BCellEndpoint, config.AuthToken),
		HelperTClient:    immunis.NewHelperTClient(config.HelperTEndpoint, config.AuthToken),
		CytotoxicTClient: immunis.NewCytotoxicTClient(config.CytotoxicTEndpoint, config.AuthToken),

		AutonomousInvestigation: investigation.NewInvestigationClient(config.AutonomousInvestEndpoint),
		NetworkRecon:            investigation.NewReconClient(config.ReconEndpoint, config.AuthToken),
		OSINT:                   investigation.NewOSINTClient(config.OSINTEndpoint, config.AuthToken),

		HCLAnalyzer: hcl.NewAnalyzerClient(config.HCLAnalyzerEndpoint, config.AuthToken),
		HCLPlanner:  hcl.NewPlannerClient(config.HCLPlannerEndpoint, config.AuthToken),
		HCLExecutor: hcl.NewExecutorClient(config.HCLExecutorEndpoint, config.AuthToken),

		EthicalAudit: ethical.NewAuditClient(config.EthicalAuditEndpoint, config.AuthToken),
		HSAS:         ethical.NewHSASClient(config.HSASEndpoint, config.AuthToken),

		ThreatIntel: threat.NewIntelClient(config.ThreatIntelEndpoint, config.AuthToken),
		VulnIntel:   threat.NewVulnClient(config.VulnIntelEndpoint, config.AuthToken),

		WebAttack: offensive.NewWebAttackClient(config.WebAttackEndpoint, config.AuthToken),

		SeriemaGraph:    graph.NewSeriemaClient(config.SeriemaGraphEndpoint, config.AuthToken),
		TatacaIngestion: data.NewIngestionClient(config.TatacaIngestionEndpoint, config.AuthToken),
		NarrativeFilter: narrative.NewNarrativeClient(config.NarrativeFilterEndpoint),

		RTE: triage.NewRTEClient(config.RTEEndpoint, config.AuthToken),

		runningWorkflows: make(map[string]*ExecutionContext),
		defaultTimeout:   config.DefaultTimeout,
		logger:           config.Logger,
	}
}

// Execute runs a workflow synchronously and returns the result
func (e *OrchestrationEngine) Execute(workflow Workflow) (*WorkflowResult, error) {
	// Generate workflow ID
	if workflow.ID == "" {
		workflow.ID = uuid.New().String()
	}

	// Create execution context
	ctx := &ExecutionContext{
		WorkflowID:   workflow.ID,
		WorkflowName: workflow.Name,
		StartTime:    time.Now(),
		CurrentStep:  0,
		TotalSteps:   len(workflow.Steps),
		Status:       StatusRunning,
		Results:      make(map[string]interface{}),
		Errors:       []StepError{},
		Metadata:     workflow.Metadata,
		Variables:    make(map[string]interface{}),
	}

	e.logger.Printf("[Orchestrator] Starting workflow '%s' (ID: %s) with %d steps",
		workflow.Name, workflow.ID, len(workflow.Steps))

	// Execute each step
	for i, step := range workflow.Steps {
		ctx.CurrentStep = i + 1

		e.logger.Printf("[Orchestrator] [%s] Step %d/%d: %s (%s.%s)",
			workflow.ID, i+1, len(workflow.Steps), step.Name, step.Service, step.Operation)

		// Check condition (if present)
		if step.Condition != nil && !step.Condition(ctx) {
			e.logger.Printf("[Orchestrator] [%s] Step %d skipped (condition not met)", workflow.ID, i+1)
			continue
		}

		// Execute step with retry logic
		if err := e.executeStepWithRetry(ctx, step, i); err != nil {
			e.logger.Printf("[Orchestrator] [%s] Step %d failed: %v", workflow.ID, i+1, err)

			// Handle error based on strategy
			switch step.OnError {
			case ErrorAbort:
				ctx.Status = StatusAborted
				now := time.Now()
				ctx.EndTime = &now
				e.logger.Printf("[Orchestrator] [%s] Workflow aborted due to error in step %d", workflow.ID, i+1)
				return ctx.ToResult(), fmt.Errorf("workflow aborted at step %d: %w", i+1, err)

			case ErrorContinue:
				e.logger.Printf("[Orchestrator] [%s] Continuing despite error in step %d", workflow.ID, i+1)
				continue

			case ErrorRetry:
				// Retry logic is handled in executeStepWithRetry
				continue
			}
		}
	}

	// Workflow completed
	ctx.Status = StatusCompleted
	now := time.Now()
	ctx.EndTime = &now

	e.logger.Printf("[Orchestrator] Workflow '%s' (ID: %s) completed successfully", workflow.Name, workflow.ID)

	return ctx.ToResult(), nil
}

// ExecuteAsync runs a workflow asynchronously and returns the workflow ID for tracking
func (e *OrchestrationEngine) ExecuteAsync(workflow Workflow) (string, error) {
	// Generate workflow ID
	if workflow.ID == "" {
		workflow.ID = uuid.New().String()
	}

	// Create execution context
	ctx := &ExecutionContext{
		WorkflowID:   workflow.ID,
		WorkflowName: workflow.Name,
		StartTime:    time.Now(),
		CurrentStep:  0,
		TotalSteps:   len(workflow.Steps),
		Status:       StatusPending,
		Results:      make(map[string]interface{}),
		Errors:       []StepError{},
		Metadata:     workflow.Metadata,
		Variables:    make(map[string]interface{}),
	}

	// Store context
	e.mu.Lock()
	e.runningWorkflows[workflow.ID] = ctx
	e.mu.Unlock()

	// Execute in goroutine
	go func() {
		ctx.Status = StatusRunning
		_, err := e.Execute(workflow)

		e.mu.Lock()
		defer e.mu.Unlock()

		if err != nil && ctx.Status != StatusAborted {
			ctx.Status = StatusFailed
		}
	}()

	e.logger.Printf("[Orchestrator] Workflow '%s' (ID: %s) started asynchronously", workflow.Name, workflow.ID)

	return workflow.ID, nil
}

// GetStatus returns the current status of a workflow
func (e *OrchestrationEngine) GetStatus(workflowID string) (*WorkflowResult, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	ctx, exists := e.runningWorkflows[workflowID]
	if !exists {
		return nil, fmt.Errorf("workflow %s not found", workflowID)
	}

	return ctx.ToResult(), nil
}

// executeStepWithRetry executes a step with retry logic
func (e *OrchestrationEngine) executeStepWithRetry(ctx *ExecutionContext, step WorkflowStep, stepIndex int) error {
	maxRetries := step.Retries
	if maxRetries == 0 {
		maxRetries = 1 // At least one attempt
	}

	retryDelay := step.RetryDelay
	if retryDelay == 0 {
		retryDelay = 1 * time.Second
	}

	var lastError error

	for attempt := 0; attempt < maxRetries; attempt++ {
		if attempt > 0 {
			// Exponential backoff
			delay := retryDelay * time.Duration(1<<uint(attempt-1))
			e.logger.Printf("[Orchestrator] [%s] Retrying step %d (attempt %d/%d) after %v",
				ctx.WorkflowID, stepIndex+1, attempt+1, maxRetries, delay)
			time.Sleep(delay)
			ctx.IncrementRetryCount()
		}

		// Execute step
		result, err := e.executeStep(ctx, step)
		if err == nil {
			// Success
			ctx.SetResult(step.Name, result)

			// Validate output if validator present
			if step.Validate != nil {
				if validationErr := step.Validate(result); validationErr != nil {
					lastError = fmt.Errorf("validation failed: %w", validationErr)
					ctx.AddError(stepIndex, step.Name, step.Service, step.Operation, lastError)
					continue
				}
			}

			if attempt > 0 {
				ctx.MarkErrorRecovered()
			}

			return nil
		}

		lastError = err
		ctx.AddError(stepIndex, step.Name, step.Service, step.Operation, err)
	}

	return fmt.Errorf("step failed after %d attempts: %w", maxRetries, lastError)
}

// executeStep executes a single workflow step
func (e *OrchestrationEngine) executeStep(ctx *ExecutionContext, step WorkflowStep) (interface{}, error) {
	// Apply transform if present
	if step.Transform != nil {
		if err := step.Transform(ctx); err != nil {
			return nil, fmt.Errorf("transform failed: %w", err)
		}
	}

	// Route to appropriate service client
	// This is a simplified routing - in production, use reflection or a service registry
	switch step.Service {
	// Maximus services
	case "maximus_eureka":
		return e.routeMaximusEureka(step)
	case "maximus_oraculo":
		return e.routeMaximusOraculo(step)
	case "maximus_predict":
		return e.routeMaximusPredict(step)

	// Immunis services
	case "lymphnode":
		return e.routeLymphnode(step)
	case "macrophage":
		return e.routeMacrophage(step)
	case "bcell":
		return e.routeBCell(step)
	case "helper_t":
		return e.routeHelperT(step)
	case "cytotoxic_t":
		return e.routeCytotoxicT(step)

	// Investigation services
	case "autonomous_investigation":
		return e.routeAutonomousInvestigation(step)
	case "network_recon":
		return e.routeNetworkRecon(step)
	case "osint":
		return e.routeOSINT(step)

	// HCL services
	case "hcl_analyzer":
		return e.routeHCLAnalyzer(step)
	case "hcl_planner":
		return e.routeHCLPlanner(step)
	case "hcl_executor":
		return e.routeHCLExecutor(step)

	// Ethical services
	case "ethical_audit":
		return e.routeEthicalAudit(step)
	case "hsas":
		return e.routeHSAS(step)

	// Threat intel services
	case "threat_intel":
		return e.routeThreatIntel(step)
	case "vuln_intel":
		return e.routeVulnIntel(step)

	// Offensive services
	case "web_attack":
		return e.routeWebAttack(step)

	// Data & Graph services
	case "seriema_graph":
		return e.routeSeriemaGraph(step)
	case "tataca_ingestion":
		return e.routeTatacaIngestion(step)
	case "narrative_filter":
		return e.routeNarrativeFilter(step)

	// RTE service
	case "rte":
		return e.routeRTE(step)

	default:
		return nil, fmt.Errorf("unknown service: %s", step.Service)
	}
}

// Service routing methods (to be implemented in separate file for clarity)
// These will be implemented in engine_routes.go

func (e *OrchestrationEngine) routeMaximusEureka(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for maximus_eureka")
}

func (e *OrchestrationEngine) routeMaximusOraculo(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for maximus_oraculo")
}

func (e *OrchestrationEngine) routeMaximusPredict(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for maximus_predict")
}

func (e *OrchestrationEngine) routeLymphnode(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for lymphnode")
}

func (e *OrchestrationEngine) routeMacrophage(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for macrophage")
}

func (e *OrchestrationEngine) routeBCell(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for bcell")
}

func (e *OrchestrationEngine) routeHelperT(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for helper_t")
}

func (e *OrchestrationEngine) routeCytotoxicT(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for cytotoxic_t")
}

func (e *OrchestrationEngine) routeAutonomousInvestigation(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for autonomous_investigation")
}

func (e *OrchestrationEngine) routeNetworkRecon(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for network_recon")
}

func (e *OrchestrationEngine) routeOSINT(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for osint")
}

func (e *OrchestrationEngine) routeHCLAnalyzer(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for hcl_analyzer")
}

func (e *OrchestrationEngine) routeHCLPlanner(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for hcl_planner")
}

func (e *OrchestrationEngine) routeHCLExecutor(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for hcl_executor")
}

func (e *OrchestrationEngine) routeEthicalAudit(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for ethical_audit")
}

func (e *OrchestrationEngine) routeHSAS(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for hsas")
}

func (e *OrchestrationEngine) routeThreatIntel(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for threat_intel")
}

func (e *OrchestrationEngine) routeVulnIntel(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for vuln_intel")
}

func (e *OrchestrationEngine) routeWebAttack(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for web_attack")
}

func (e *OrchestrationEngine) routeSeriemaGraph(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for seriema_graph")
}

func (e *OrchestrationEngine) routeTatacaIngestion(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for tataca_ingestion")
}

func (e *OrchestrationEngine) routeNarrativeFilter(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for narrative_filter")
}

func (e *OrchestrationEngine) routeRTE(step WorkflowStep) (interface{}, error) {
	return nil, fmt.Errorf("routing not yet implemented for rte")
}
