package agents

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/verticedev/vcli-go/internal/maximus"
)

// AgentOrchestrator coordinates multi-agent workflows
type AgentOrchestrator struct {
	// Agent registry
	agents map[AgentType]Agent
	mu     sync.RWMutex

	// Configuration
	config AgentConfig

	// Workspace path
	workspacePath string

	// MAXIMUS clients
	consciousnessClient *maximus.ConsciousnessClient
	governanceClient    *maximus.GovernanceClient

	// Workflow tracking
	runningWorkflows map[string]*WorkflowExecution
	workflowMu       sync.RWMutex

	// Logger
	logger *log.Logger
}

// WorkflowExecution tracks a running workflow
type WorkflowExecution struct {
	ID           string
	Name         string
	StartedAt    time.Time
	CompletedAt  *time.Time
	Status       AgentStatus
	CurrentStep  int
	TotalSteps   int
	AgentOutputs map[AgentType]*AgentOutput
	Errors       []error
	HITLDecisions []string
}

// NewAgentOrchestrator creates a new agent orchestrator
func NewAgentOrchestrator(config AgentConfig) (*AgentOrchestrator, error) {
	// Validate workspace path
	if config.WorkspacePath == "" {
		config.WorkspacePath = ".agents-workspace"
	}

	// Create workspace if it doesn't exist
	if err := os.MkdirAll(config.WorkspacePath, 0755); err != nil {
		return nil, fmt.Errorf("failed to create workspace: %w", err)
	}

	// Create MAXIMUS clients
	consciousnessClient := maximus.NewConsciousnessClient(config.MaximusConsciousnessEndpoint)
	governanceClient := maximus.NewGovernanceClient(config.MaximusGovernanceEndpoint)

	orchestrator := &AgentOrchestrator{
		agents:              make(map[AgentType]Agent),
		config:              config,
		workspacePath:       config.WorkspacePath,
		consciousnessClient: consciousnessClient,
		governanceClient:    governanceClient,
		runningWorkflows:    make(map[string]*WorkflowExecution),
		logger:              log.New(os.Stdout, "[AgentOrchestrator] ", log.LstdFlags),
	}

	return orchestrator, nil
}

// RegisterAgent registers an agent with the orchestrator
func (o *AgentOrchestrator) RegisterAgent(agent Agent) error {
	o.mu.Lock()
	defer o.mu.Unlock()

	agentType := agent.Type()
	if _, exists := o.agents[agentType]; exists {
		return fmt.Errorf("agent %s already registered", agentType)
	}

	o.agents[agentType] = agent
	o.logger.Printf("Registered agent: %s (%s)", agent.Name(), agentType)

	return nil
}

// GetAgent retrieves a registered agent by type
func (o *AgentOrchestrator) GetAgent(agentType AgentType) (Agent, error) {
	o.mu.RLock()
	defer o.mu.RUnlock()

	agent, exists := o.agents[agentType]
	if !exists {
		return nil, fmt.Errorf("agent %s not registered", agentType)
	}

	return agent, nil
}

// ExecuteWorkflow runs a multi-agent workflow
func (o *AgentOrchestrator) ExecuteWorkflow(ctx context.Context, workflow Workflow) (*WorkflowExecution, error) {
	// Generate workflow ID
	workflowID := uuid.New().String()

	execution := &WorkflowExecution{
		ID:           workflowID,
		Name:         workflow.Name,
		StartedAt:    time.Now(),
		Status:       StatusRunning,
		TotalSteps:   len(workflow.Steps),
		AgentOutputs: make(map[AgentType]*AgentOutput),
		Errors:       make([]error, 0),
		HITLDecisions: make([]string, 0),
	}

	// Store workflow
	o.workflowMu.Lock()
	o.runningWorkflows[workflowID] = execution
	o.workflowMu.Unlock()

	o.logger.Printf("Starting workflow '%s' (ID: %s) with %d steps", workflow.Name, workflowID, len(workflow.Steps))

	// Report to consciousness system
	if o.consciousnessClient != nil {
		salience := maximus.SalienceInput{
			Novelty:   0.7,
			Relevance: 0.9,
			Urgency:   0.6,
			Context: map[string]interface{}{
				"source":       "agent_orchestrator",
				"workflow_id":  workflowID,
				"workflow_name": workflow.Name,
				"total_steps":  len(workflow.Steps),
			},
		}
		_, _ = o.consciousnessClient.TriggerESGT(salience)
	}

	// Execute each step
	for i, step := range workflow.Steps {
		execution.CurrentStep = i + 1

		o.logger.Printf("[%s] Step %d/%d: %s (%s)", workflowID, i+1, len(workflow.Steps), step.Description, step.AgentType)

		// Get agent
		agent, err := o.GetAgent(step.AgentType)
		if err != nil {
			execution.Errors = append(execution.Errors, err)
			execution.Status = StatusFailed
			now := time.Now()
			execution.CompletedAt = &now
			return execution, fmt.Errorf("agent not found: %w", err)
		}

		// Build agent input from step
		agentInput := AgentInput{
			Task:        step.Task,
			Context:     step.Context,
			Targets:     step.Targets,
			Config:      step.Config,
			HITLEnabled: step.HITLRequired,
		}

		// Add previous agent outputs to context
		for agentType, output := range execution.AgentOutputs {
			agentInput.Context[string(agentType)+"_output"] = output
		}

		// Validate agent can execute
		if err := agent.Validate(agentInput); err != nil {
			execution.Errors = append(execution.Errors, err)
			if step.ContinueOnError {
				o.logger.Printf("[%s] Step %d validation failed (continuing): %v", workflowID, i+1, err)
				continue
			}
			execution.Status = StatusFailed
			now := time.Now()
			execution.CompletedAt = &now
			return execution, fmt.Errorf("step %d validation failed: %w", i+1, err)
		}

		// Execute agent
		output, err := agent.Execute(ctx, agentInput)
		if err != nil {
			execution.Errors = append(execution.Errors, err)
			if step.ContinueOnError {
				o.logger.Printf("[%s] Step %d execution failed (continuing): %v", workflowID, i+1, err)
				continue
			}
			execution.Status = StatusFailed
			now := time.Now()
			execution.CompletedAt = &now
			return execution, fmt.Errorf("step %d execution failed: %w", i+1, err)
		}

		// Store output
		execution.AgentOutputs[step.AgentType] = output

		// Track HITL decisions
		if output.HITLDecisionID != "" {
			execution.HITLDecisions = append(execution.HITLDecisions, output.HITLDecisionID)
		}

		// Save artifacts
		if err := o.saveArtifacts(workflowID, step.AgentType, output); err != nil {
			o.logger.Printf("[%s] Failed to save artifacts: %v", workflowID, err)
		}

		// Check if we need to wait for HITL approval
		if output.Status == StatusWaitingHITL {
			o.logger.Printf("[%s] Waiting for HITL approval (decision ID: %s)", workflowID, output.HITLDecisionID)
			execution.Status = StatusWaitingHITL
			return execution, nil // Workflow paused, will resume after approval
		}

		o.logger.Printf("[%s] Step %d completed: %s", workflowID, i+1, output.Status)
	}

	// Workflow completed
	execution.Status = StatusCompleted
	now := time.Now()
	execution.CompletedAt = &now

	o.logger.Printf("Workflow '%s' (ID: %s) completed successfully", workflow.Name, workflowID)

	// Report completion to consciousness
	if o.consciousnessClient != nil {
		salience := maximus.SalienceInput{
			Novelty:   0.5,
			Relevance: 0.9,
			Urgency:   0.3,
			Context: map[string]interface{}{
				"source":        "agent_orchestrator",
				"workflow_id":   workflowID,
				"workflow_name": workflow.Name,
				"status":        "completed",
				"duration_ms":   time.Since(execution.StartedAt).Milliseconds(),
			},
		}
		_, _ = o.consciousnessClient.TriggerESGT(salience)
	}

	return execution, nil
}

// ExecuteAgent runs a single agent
func (o *AgentOrchestrator) ExecuteAgent(ctx context.Context, agentType AgentType, input AgentInput) (*AgentOutput, error) {
	agent, err := o.GetAgent(agentType)
	if err != nil {
		return nil, err
	}

	o.logger.Printf("Executing agent: %s (%s)", agent.Name(), agentType)

	// Validate
	if err := agent.Validate(input); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Execute
	output, err := agent.Execute(ctx, input)
	if err != nil {
		return nil, fmt.Errorf("execution failed: %w", err)
	}

	// Save artifacts
	if err := o.saveArtifacts("single-"+uuid.New().String()[:8], agentType, output); err != nil {
		o.logger.Printf("Failed to save artifacts: %v", err)
	}

	return output, nil
}

// GetWorkflowStatus retrieves the status of a workflow
func (o *AgentOrchestrator) GetWorkflowStatus(workflowID string) (*WorkflowExecution, error) {
	o.workflowMu.RLock()
	defer o.workflowMu.RUnlock()

	execution, exists := o.runningWorkflows[workflowID]
	if !exists {
		return nil, fmt.Errorf("workflow %s not found", workflowID)
	}

	return execution, nil
}

// ResumeWorkflow resumes a paused workflow after HITL approval
func (o *AgentOrchestrator) ResumeWorkflow(ctx context.Context, workflowID string, workflow Workflow, stepIndex int) error {
	execution, err := o.GetWorkflowStatus(workflowID)
	if err != nil {
		return err
	}

	if execution.Status != StatusWaitingHITL {
		return fmt.Errorf("workflow %s is not waiting for HITL approval", workflowID)
	}

	o.logger.Printf("Resuming workflow '%s' (ID: %s) from step %d", execution.Name, workflowID, stepIndex)

	// Continue execution from the next step
	// (Implementation would be similar to ExecuteWorkflow but starting from stepIndex)

	return nil
}

// saveArtifacts saves agent output artifacts to workspace
func (o *AgentOrchestrator) saveArtifacts(workflowID string, agentType AgentType, output *AgentOutput) error {
	// Determine artifact directory
	var artifactDir string
	switch agentType {
	case AgentTypeDiagnosticador:
		artifactDir = filepath.Join(o.workspacePath, "artifacts", "diagnostics")
	case AgentTypeArquiteto:
		artifactDir = filepath.Join(o.workspacePath, "artifacts", "plans")
	case AgentTypeDevSenior:
		artifactDir = filepath.Join(o.workspacePath, "artifacts", "implementations")
	case AgentTypeTester:
		artifactDir = filepath.Join(o.workspacePath, "artifacts", "test_reports")
	default:
		artifactDir = filepath.Join(o.workspacePath, "artifacts", "misc")
	}

	// Create directory
	if err := os.MkdirAll(artifactDir, 0755); err != nil {
		return fmt.Errorf("failed to create artifact directory: %w", err)
	}

	// Save output as JSON
	outputFile := filepath.Join(artifactDir, fmt.Sprintf("%s-%s.json", workflowID, time.Now().Format("20060102-150405")))
	data, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal output: %w", err)
	}

	if err := os.WriteFile(outputFile, data, 0644); err != nil {
		return fmt.Errorf("failed to write output file: %w", err)
	}

	o.logger.Printf("Saved artifacts to: %s", outputFile)

	return nil
}

// Workflow represents a multi-agent workflow
type Workflow struct {
	Name        string
	Description string
	Steps       []WorkflowStep
}

// WorkflowStep represents a single step in a workflow
type WorkflowStep struct {
	AgentType       AgentType
	Task            string
	Description     string
	Targets         []string
	Context         map[string]interface{}
	Config          map[string]interface{}
	HITLRequired    bool
	ContinueOnError bool
}
