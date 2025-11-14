package agents

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"
)

// MockAgent implements the Agent interface for testing
type MockAgent struct {
	agentType    AgentType
	name         string
	status       AgentStatus
	capabilities []string
	executeFunc  func(ctx context.Context, input AgentInput) (*AgentOutput, error)
	validateFunc func(input AgentInput) error
	mu           sync.RWMutex
}

func NewMockAgent(agentType AgentType, name string) *MockAgent {
	return &MockAgent{
		agentType:    agentType,
		name:         name,
		status:       StatusIdle,
		capabilities: []string{"mock_capability_1", "mock_capability_2"},
	}
}

func (m *MockAgent) Type() AgentType {
	return m.agentType
}

func (m *MockAgent) Name() string {
	return m.name
}

func (m *MockAgent) Execute(ctx context.Context, input AgentInput) (*AgentOutput, error) {
	m.mu.Lock()
	m.status = StatusRunning
	m.mu.Unlock()

	if m.executeFunc != nil {
		return m.executeFunc(ctx, input)
	}

	// Default mock execution
	time.Sleep(10 * time.Millisecond) // Simulate work

	m.mu.Lock()
	m.status = StatusCompleted
	m.mu.Unlock()

	return &AgentOutput{
		AgentType:   m.agentType,
		Status:      StatusCompleted,
		Result:      fmt.Sprintf("Mock result from %s", m.name),
		Artifacts:   []string{},
		Metrics:     map[string]float64{"execution_time_ms": 10},
		Errors:      []string{},
		StartedAt:   time.Now().Add(-10 * time.Millisecond),
		CompletedAt: time.Now(),
		Duration:    10 * time.Millisecond,
		Metadata:    map[string]interface{}{"mock": true},
	}, nil
}

func (m *MockAgent) Validate(input AgentInput) error {
	if m.validateFunc != nil {
		return m.validateFunc(input)
	}
	// Default validation always passes
	return nil
}

func (m *MockAgent) GetCapabilities() []string {
	return m.capabilities
}

func (m *MockAgent) GetStatus() AgentStatus {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.status
}

// Test: NewAgentOrchestrator - Basic Creation
func TestNewAgentOrchestrator_BasicCreation(t *testing.T) {
	tempDir := t.TempDir()
	config := AgentConfig{
		Type:                         AgentTypeDiagnosticador,
		WorkspacePath:                tempDir,
		MaximusConsciousnessEndpoint: "http://localhost:8080",
		MaximusGovernanceEndpoint:    "http://localhost:8081",
		DefaultTimeout:               30 * time.Second,
		MaxRetries:                   3,
	}

	orchestrator, err := NewAgentOrchestrator(config)
	if err != nil {
		t.Fatalf("Failed to create orchestrator: %v", err)
	}

	if orchestrator == nil {
		t.Fatal("Orchestrator is nil")
	}

	if orchestrator.workspacePath != tempDir {
		t.Errorf("Expected workspace path %s, got %s", tempDir, orchestrator.workspacePath)
	}
}

// Test: NewAgentOrchestrator - Default Workspace Path
func TestNewAgentOrchestrator_DefaultWorkspacePath(t *testing.T) {
	config := AgentConfig{}

	orchestrator, err := NewAgentOrchestrator(config)
	if err != nil {
		t.Fatalf("Failed to create orchestrator: %v", err)
	}

	expectedWorkspace := ".agents-workspace"
	if orchestrator.workspacePath != expectedWorkspace {
		t.Errorf("Expected default workspace path %s, got %s", expectedWorkspace, orchestrator.workspacePath)
	}

	// Cleanup
	os.RemoveAll(expectedWorkspace)
}

// Test: NewAgentOrchestrator - Workspace Creation
func TestNewAgentOrchestrator_WorkspaceCreation(t *testing.T) {
	tempDir := t.TempDir()
	workspacePath := filepath.Join(tempDir, "test-workspace")

	config := AgentConfig{
		WorkspacePath: workspacePath,
	}

	_, err := NewAgentOrchestrator(config)
	if err != nil {
		t.Fatalf("Failed to create orchestrator: %v", err)
	}

	// Verify workspace was created
	if _, err := os.Stat(workspacePath); os.IsNotExist(err) {
		t.Errorf("Workspace directory was not created: %s", workspacePath)
	}
}

// Test: RegisterAgent - Success
func TestRegisterAgent_Success(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	agent := NewMockAgent(AgentTypeDiagnosticador, "Test Diagnosticador")
	err := orchestrator.RegisterAgent(agent)

	if err != nil {
		t.Fatalf("Failed to register agent: %v", err)
	}

	// Verify agent was registered
	if len(orchestrator.agents) != 1 {
		t.Errorf("Expected 1 agent, got %d", len(orchestrator.agents))
	}
}

// Test: RegisterAgent - Duplicate Registration
func TestRegisterAgent_DuplicateRegistration(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	agent1 := NewMockAgent(AgentTypeDiagnosticador, "Agent 1")
	agent2 := NewMockAgent(AgentTypeDiagnosticador, "Agent 2")

	err1 := orchestrator.RegisterAgent(agent1)
	if err1 != nil {
		t.Fatalf("Failed to register first agent: %v", err1)
	}

	err2 := orchestrator.RegisterAgent(agent2)
	if err2 == nil {
		t.Error("Expected error when registering duplicate agent type, got nil")
	}

	expectedError := "already registered"
	if !contains(err2.Error(), expectedError) {
		t.Errorf("Expected error to contain '%s', got: %v", expectedError, err2)
	}
}

// Test: RegisterAgent - Multiple Different Agents
func TestRegisterAgent_MultipleDifferentAgents(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	agents := []*MockAgent{
		NewMockAgent(AgentTypeDiagnosticador, "Diagnosticador"),
		NewMockAgent(AgentTypeArquiteto, "Arquiteto"),
		NewMockAgent(AgentTypeDevSenior, "Dev Senior"),
		NewMockAgent(AgentTypeTester, "Tester"),
	}

	for _, agent := range agents {
		err := orchestrator.RegisterAgent(agent)
		if err != nil {
			t.Fatalf("Failed to register agent %s: %v", agent.Name(), err)
		}
	}

	if len(orchestrator.agents) != 4 {
		t.Errorf("Expected 4 agents registered, got %d", len(orchestrator.agents))
	}
}

// Test: GetAgent - Success
func TestGetAgent_Success(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	mockAgent := NewMockAgent(AgentTypeDiagnosticador, "Test Agent")
	orchestrator.RegisterAgent(mockAgent)

	retrieved, err := orchestrator.GetAgent(AgentTypeDiagnosticador)
	if err != nil {
		t.Fatalf("Failed to get agent: %v", err)
	}

	if retrieved.Type() != mockAgent.Type() {
		t.Errorf("Expected agent type %s, got %s", mockAgent.Type(), retrieved.Type())
	}

	if retrieved.Name() != mockAgent.Name() {
		t.Errorf("Expected agent name %s, got %s", mockAgent.Name(), retrieved.Name())
	}
}

// Test: GetAgent - Not Found
func TestGetAgent_NotFound(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	_, err := orchestrator.GetAgent(AgentTypeDiagnosticador)
	if err == nil {
		t.Error("Expected error when getting non-existent agent, got nil")
	}

	expectedError := "not registered"
	if !contains(err.Error(), expectedError) {
		t.Errorf("Expected error to contain '%s', got: %v", expectedError, err)
	}
}

// Test: ExecuteAgent - Success
func TestExecuteAgent_Success(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	mockAgent := NewMockAgent(AgentTypeDiagnosticador, "Test Agent")
	orchestrator.RegisterAgent(mockAgent)

	ctx := context.Background()
	input := AgentInput{
		Task:    "Test task",
		Context: map[string]interface{}{"test": true},
		Targets: []string{"test.go"},
		Config:  map[string]interface{}{},
	}

	output, err := orchestrator.ExecuteAgent(ctx, AgentTypeDiagnosticador, input)
	if err != nil {
		t.Fatalf("Failed to execute agent: %v", err)
	}

	if output == nil {
		t.Fatal("Output is nil")
	}

	if output.Status != StatusCompleted {
		t.Errorf("Expected status %s, got %s", StatusCompleted, output.Status)
	}
}

// Test: ExecuteAgent - Agent Not Found
func TestExecuteAgent_AgentNotFound(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	ctx := context.Background()
	input := AgentInput{Task: "Test task"}

	_, err := orchestrator.ExecuteAgent(ctx, AgentTypeDiagnosticador, input)
	if err == nil {
		t.Error("Expected error when executing non-existent agent, got nil")
	}
}

// Test: ExecuteAgent - Validation Failure
func TestExecuteAgent_ValidationFailure(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	mockAgent := NewMockAgent(AgentTypeDiagnosticador, "Test Agent")
	mockAgent.validateFunc = func(input AgentInput) error {
		return errors.New("validation failed")
	}
	orchestrator.RegisterAgent(mockAgent)

	ctx := context.Background()
	input := AgentInput{Task: "Test task"}

	_, err := orchestrator.ExecuteAgent(ctx, AgentTypeDiagnosticador, input)
	if err == nil {
		t.Error("Expected validation error, got nil")
	}

	if !contains(err.Error(), "validation failed") {
		t.Errorf("Expected validation error, got: %v", err)
	}
}

// Test: ExecuteAgent - Execution Failure
func TestExecuteAgent_ExecutionFailure(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	mockAgent := NewMockAgent(AgentTypeDiagnosticador, "Test Agent")
	mockAgent.executeFunc = func(ctx context.Context, input AgentInput) (*AgentOutput, error) {
		return nil, errors.New("execution failed")
	}
	orchestrator.RegisterAgent(mockAgent)

	ctx := context.Background()
	input := AgentInput{Task: "Test task"}

	_, err := orchestrator.ExecuteAgent(ctx, AgentTypeDiagnosticador, input)
	if err == nil {
		t.Error("Expected execution error, got nil")
	}

	if !contains(err.Error(), "execution failed") {
		t.Errorf("Expected execution error, got: %v", err)
	}
}

// Test: ExecuteWorkflow - Simple Workflow
func TestExecuteWorkflow_SimpleWorkflow(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	// Register agents
	diagnosticador := NewMockAgent(AgentTypeDiagnosticador, "Diagnosticador")
	arquiteto := NewMockAgent(AgentTypeArquiteto, "Arquiteto")
	orchestrator.RegisterAgent(diagnosticador)
	orchestrator.RegisterAgent(arquiteto)

	// Create workflow
	workflow := Workflow{
		Name:        "Test Workflow",
		Description: "A simple test workflow",
		Steps: []WorkflowStep{
			{
				AgentType:   AgentTypeDiagnosticador,
				Task:        "Analyze code",
				Description: "Step 1: Diagnose",
				Context:     map[string]interface{}{},
				Config:      map[string]interface{}{},
			},
			{
				AgentType:   AgentTypeArquiteto,
				Task:        "Create plan",
				Description: "Step 2: Plan",
				Context:     map[string]interface{}{},
				Config:      map[string]interface{}{},
			},
		},
	}

	ctx := context.Background()
	execution, err := orchestrator.ExecuteWorkflow(ctx, workflow)

	if err != nil {
		t.Fatalf("Workflow execution failed: %v", err)
	}

	if execution == nil {
		t.Fatal("Execution is nil")
	}

	if execution.Status != StatusCompleted {
		t.Errorf("Expected status %s, got %s", StatusCompleted, execution.Status)
	}

	if execution.TotalSteps != 2 {
		t.Errorf("Expected 2 steps, got %d", execution.TotalSteps)
	}

	if len(execution.AgentOutputs) != 2 {
		t.Errorf("Expected 2 agent outputs, got %d", len(execution.AgentOutputs))
	}
}

// Test: ExecuteWorkflow - Agent Not Found
func TestExecuteWorkflow_AgentNotFound(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	workflow := Workflow{
		Name: "Test Workflow",
		Steps: []WorkflowStep{
			{
				AgentType:   AgentTypeDiagnosticador,
				Task:        "Test task",
				Description: "Test step",
			},
		},
	}

	ctx := context.Background()
	execution, err := orchestrator.ExecuteWorkflow(ctx, workflow)

	if err == nil {
		t.Error("Expected error when agent not found, got nil")
	}

	if execution == nil {
		t.Fatal("Execution should not be nil even on error")
	}

	if execution.Status != StatusFailed {
		t.Errorf("Expected status %s, got %s", StatusFailed, execution.Status)
	}
}

// Test: ExecuteWorkflow - Step Validation Failure
func TestExecuteWorkflow_StepValidationFailure(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	mockAgent := NewMockAgent(AgentTypeDiagnosticador, "Test Agent")
	mockAgent.validateFunc = func(input AgentInput) error {
		return errors.New("validation failed")
	}
	orchestrator.RegisterAgent(mockAgent)

	workflow := Workflow{
		Name: "Test Workflow",
		Steps: []WorkflowStep{
			{
				AgentType:   AgentTypeDiagnosticador,
				Task:        "Test task",
				Description: "Test step",
			},
		},
	}

	ctx := context.Background()
	execution, err := orchestrator.ExecuteWorkflow(ctx, workflow)

	if err == nil {
		t.Error("Expected validation error, got nil")
	}

	if execution.Status != StatusFailed {
		t.Errorf("Expected status %s, got %s", StatusFailed, execution.Status)
	}
}

// Test: ExecuteWorkflow - Continue On Error
func TestExecuteWorkflow_ContinueOnError(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	// First agent fails
	failingAgent := NewMockAgent(AgentTypeDiagnosticador, "Failing Agent")
	failingAgent.executeFunc = func(ctx context.Context, input AgentInput) (*AgentOutput, error) {
		return nil, errors.New("execution failed")
	}
	orchestrator.RegisterAgent(failingAgent)

	// Second agent succeeds
	successAgent := NewMockAgent(AgentTypeArquiteto, "Success Agent")
	orchestrator.RegisterAgent(successAgent)

	workflow := Workflow{
		Name: "Test Workflow",
		Steps: []WorkflowStep{
			{
				AgentType:       AgentTypeDiagnosticador,
				Task:            "Task that fails",
				Description:     "Failing step",
				ContinueOnError: true,
			},
			{
				AgentType:   AgentTypeArquiteto,
				Task:        "Task that succeeds",
				Description: "Success step",
			},
		},
	}

	ctx := context.Background()
	execution, err := orchestrator.ExecuteWorkflow(ctx, workflow)

	if err != nil {
		t.Fatalf("Expected workflow to continue despite error: %v", err)
	}

	if execution.Status != StatusCompleted {
		t.Errorf("Expected status %s, got %s", StatusCompleted, execution.Status)
	}

	if len(execution.Errors) == 0 {
		t.Error("Expected errors to be tracked")
	}
}

// Test: ExecuteWorkflow - HITL Workflow Pause
func TestExecuteWorkflow_HITLWorkflowPause(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	// Agent that requires HITL
	hitlAgent := NewMockAgent(AgentTypeDiagnosticador, "HITL Agent")
	hitlAgent.executeFunc = func(ctx context.Context, input AgentInput) (*AgentOutput, error) {
		return &AgentOutput{
			AgentType:      AgentTypeDiagnosticador,
			Status:         StatusWaitingHITL,
			HITLDecisionID: "decision-123",
			StartedAt:      time.Now(),
			CompletedAt:    time.Now(),
		}, nil
	}
	orchestrator.RegisterAgent(hitlAgent)

	workflow := Workflow{
		Name: "HITL Workflow",
		Steps: []WorkflowStep{
			{
				AgentType:    AgentTypeDiagnosticador,
				Task:         "Task requiring HITL",
				Description:  "HITL step",
				HITLRequired: true,
			},
		},
	}

	ctx := context.Background()
	execution, err := orchestrator.ExecuteWorkflow(ctx, workflow)

	if err != nil {
		t.Fatalf("Unexpected error: %v", err)
	}

	if execution.Status != StatusWaitingHITL {
		t.Errorf("Expected status %s, got %s", StatusWaitingHITL, execution.Status)
	}

	if len(execution.HITLDecisions) == 0 {
		t.Error("Expected HITL decisions to be tracked")
	}
}

// Test: GetWorkflowStatus - Success
func TestGetWorkflowStatus_Success(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	mockAgent := NewMockAgent(AgentTypeDiagnosticador, "Test Agent")
	orchestrator.RegisterAgent(mockAgent)

	workflow := Workflow{
		Name: "Test Workflow",
		Steps: []WorkflowStep{
			{
				AgentType:   AgentTypeDiagnosticador,
				Task:        "Test task",
				Description: "Test step",
			},
		},
	}

	ctx := context.Background()
	execution, _ := orchestrator.ExecuteWorkflow(ctx, workflow)

	status, err := orchestrator.GetWorkflowStatus(execution.ID)
	if err != nil {
		t.Fatalf("Failed to get workflow status: %v", err)
	}

	if status.ID != execution.ID {
		t.Errorf("Expected workflow ID %s, got %s", execution.ID, status.ID)
	}
}

// Test: GetWorkflowStatus - Not Found
func TestGetWorkflowStatus_NotFound(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	_, err := orchestrator.GetWorkflowStatus("non-existent-id")
	if err == nil {
		t.Error("Expected error when getting non-existent workflow, got nil")
	}

	if !contains(err.Error(), "not found") {
		t.Errorf("Expected 'not found' error, got: %v", err)
	}
}

// Test: Concurrency - Parallel Agent Registration
func TestConcurrency_ParallelAgentRegistration(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	var wg sync.WaitGroup
	agentTypes := []AgentType{
		AgentTypeDiagnosticador,
		AgentTypeArquiteto,
		AgentTypeDevSenior,
		AgentTypeTester,
	}

	// Register agents concurrently
	for i, agentType := range agentTypes {
		wg.Add(1)
		go func(at AgentType, index int) {
			defer wg.Done()
			agent := NewMockAgent(at, fmt.Sprintf("Agent %d", index))
			orchestrator.RegisterAgent(agent)
		}(agentType, i)
	}

	wg.Wait()

	// Verify all agents registered
	if len(orchestrator.agents) != 4 {
		t.Errorf("Expected 4 agents registered, got %d", len(orchestrator.agents))
	}
}

// Test: Concurrency - Parallel Agent Retrieval
func TestConcurrency_ParallelAgentRetrieval(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	// Register agents
	agentTypes := []AgentType{
		AgentTypeDiagnosticador,
		AgentTypeArquiteto,
		AgentTypeDevSenior,
		AgentTypeTester,
	}

	for i, agentType := range agentTypes {
		agent := NewMockAgent(agentType, fmt.Sprintf("Agent %d", i))
		orchestrator.RegisterAgent(agent)
	}

	// Retrieve agents concurrently
	var wg sync.WaitGroup
	errors := make([]error, len(agentTypes))

	for i, agentType := range agentTypes {
		wg.Add(1)
		go func(at AgentType, index int) {
			defer wg.Done()
			_, err := orchestrator.GetAgent(at)
			errors[index] = err
		}(agentType, i)
	}

	wg.Wait()

	// Verify no errors
	for i, err := range errors {
		if err != nil {
			t.Errorf("Agent retrieval %d failed: %v", i, err)
		}
	}
}

// Test: Context Propagation Through Workflow
func TestWorkflow_ContextPropagation(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	// First agent adds data to output
	agent1 := NewMockAgent(AgentTypeDiagnosticador, "Agent 1")
	agent1.executeFunc = func(ctx context.Context, input AgentInput) (*AgentOutput, error) {
		return &AgentOutput{
			AgentType: AgentTypeDiagnosticador,
			Status:    StatusCompleted,
			Result:    "agent1_result",
			Metadata:  map[string]interface{}{"key": "value1"},
			StartedAt: time.Now(),
			CompletedAt: time.Now(),
		}, nil
	}

	// Second agent should receive first agent's output in context
	agent2 := NewMockAgent(AgentTypeArquiteto, "Agent 2")
	var receivedContext map[string]interface{}
	agent2.executeFunc = func(ctx context.Context, input AgentInput) (*AgentOutput, error) {
		receivedContext = input.Context
		return &AgentOutput{
			AgentType:   AgentTypeArquiteto,
			Status:      StatusCompleted,
			Result:      "agent2_result",
			StartedAt:   time.Now(),
			CompletedAt: time.Now(),
		}, nil
	}

	orchestrator.RegisterAgent(agent1)
	orchestrator.RegisterAgent(agent2)

	workflow := Workflow{
		Name: "Context Test Workflow",
		Steps: []WorkflowStep{
			{
				AgentType:   AgentTypeDiagnosticador,
				Task:        "Step 1",
				Description: "First step",
				Context:     map[string]interface{}{},
			},
			{
				AgentType:   AgentTypeArquiteto,
				Task:        "Step 2",
				Description: "Second step",
				Context:     map[string]interface{}{},
			},
		},
	}

	ctx := context.Background()
	_, err := orchestrator.ExecuteWorkflow(ctx, workflow)
	if err != nil {
		t.Fatalf("Workflow execution failed: %v", err)
	}

	// Verify second agent received first agent's output
	if receivedContext == nil {
		t.Fatal("Second agent did not receive context")
	}

	if _, exists := receivedContext["diagnosticador_output"]; !exists {
		t.Error("Context does not contain first agent's output")
	}
}

// Test: Artifact Saving
func TestOrchestrator_ArtifactSaving(t *testing.T) {
	tempDir := t.TempDir()
	orchestrator, _ := NewAgentOrchestrator(AgentConfig{WorkspacePath: tempDir})

	mockAgent := NewMockAgent(AgentTypeDiagnosticador, "Test Agent")
	mockAgent.executeFunc = func(ctx context.Context, input AgentInput) (*AgentOutput, error) {
		return &AgentOutput{
			AgentType:   AgentTypeDiagnosticador,
			Status:      StatusCompleted,
			Result:      "test result",
			Artifacts:   []string{"artifact1.txt", "artifact2.txt"},
			StartedAt:   time.Now(),
			CompletedAt: time.Now(),
		}, nil
	}
	orchestrator.RegisterAgent(mockAgent)

	ctx := context.Background()
	input := AgentInput{Task: "Test task"}

	_, err := orchestrator.ExecuteAgent(ctx, AgentTypeDiagnosticador, input)
	if err != nil {
		t.Fatalf("Agent execution failed: %v", err)
	}

	// Verify artifacts directory was created
	artifactsDir := filepath.Join(tempDir, "artifacts", "diagnostics")
	if _, err := os.Stat(artifactsDir); os.IsNotExist(err) {
		t.Errorf("Artifacts directory was not created: %s", artifactsDir)
	}

	// Verify artifact file was created
	files, err := os.ReadDir(artifactsDir)
	if err != nil {
		t.Fatalf("Failed to read artifacts directory: %v", err)
	}

	if len(files) == 0 {
		t.Error("No artifact files were saved")
	}
}
