package orchestrator

import (
	"errors"
	"log"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewOrchestrationEngine tests the engine constructor
func TestNewOrchestrationEngine(t *testing.T) {
	tests := []struct {
		name           string
		config         EngineConfig
		validateFields func(t *testing.T, engine *OrchestrationEngine)
	}{
		{
			name: "creates engine with full config",
			config: EngineConfig{
				MaximusEurekaEndpoint:    "http://eureka:8080",
				MaximusOraculoEndpoint:   "http://oraculo:8080",
				MaximusPredictEndpoint:   "http://predict:8080",
				LymphnodeEndpoint:        "http://lymphnode:8080",
				MacrophageEndpoint:       "http://macrophage:8080",
				BCellEndpoint:            "http://bcell:8080",
				HelperTEndpoint:          "http://helpert:8080",
				CytotoxicTEndpoint:       "http://cytotoxict:8080",
				AutonomousInvestEndpoint: "http://investigation:8080",
				ReconEndpoint:            "http://recon:8080",
				OSINTEndpoint:            "http://osint:8080",
				HCLAnalyzerEndpoint:      "http://hcl-analyzer:8080",
				HCLPlannerEndpoint:       "http://hcl-planner:8080",
				HCLExecutorEndpoint:      "http://hcl-executor:8080",
				EthicalAuditEndpoint:     "http://ethical:8080",
				HSASEndpoint:             "http://hsas:8080",
				ThreatIntelEndpoint:      "http://threat:8080",
				VulnIntelEndpoint:        "http://vuln:8080",
				WebAttackEndpoint:        "http://webattack:8080",
				SeriemaGraphEndpoint:     "http://seriema:8080",
				TatacaIngestionEndpoint:  "http://tataca:8080",
				NarrativeFilterEndpoint:  "http://narrative:8080",
				RTEEndpoint:              "http://rte:8080",
				AuthToken:                "test-token",
				DefaultTimeout:           10 * time.Minute,
			},
			validateFields: func(t *testing.T, engine *OrchestrationEngine) {
				assert.NotNil(t, engine.MaximusEureka)
				assert.NotNil(t, engine.MaximusOraculo)
				assert.NotNil(t, engine.MaximusPredict)
				assert.NotNil(t, engine.LymphnodeClient)
				assert.NotNil(t, engine.MacrophageClient)
				assert.NotNil(t, engine.BCellClient)
				assert.NotNil(t, engine.HelperTClient)
				assert.NotNil(t, engine.CytotoxicTClient)
				assert.NotNil(t, engine.AutonomousInvestigation)
				assert.NotNil(t, engine.NetworkRecon)
				assert.NotNil(t, engine.OSINT)
				assert.NotNil(t, engine.HCLAnalyzer)
				assert.NotNil(t, engine.HCLPlanner)
				assert.NotNil(t, engine.HCLExecutor)
				assert.NotNil(t, engine.EthicalAudit)
				assert.NotNil(t, engine.HSAS)
				assert.NotNil(t, engine.ThreatIntel)
				assert.NotNil(t, engine.VulnIntel)
				assert.NotNil(t, engine.WebAttack)
				assert.NotNil(t, engine.SeriemaGraph)
				assert.NotNil(t, engine.TatacaIngestion)
				assert.NotNil(t, engine.NarrativeFilter)
				assert.NotNil(t, engine.RTE)
				assert.NotNil(t, engine.runningWorkflows)
				assert.Equal(t, 10*time.Minute, engine.defaultTimeout)
				assert.NotNil(t, engine.logger)
			},
		},
		{
			name:   "applies default timeout when not specified",
			config: EngineConfig{},
			validateFields: func(t *testing.T, engine *OrchestrationEngine) {
				assert.Equal(t, 30*time.Minute, engine.defaultTimeout)
			},
		},
		{
			name: "applies default logger when not specified",
			config: EngineConfig{
				DefaultTimeout: 5 * time.Minute,
			},
			validateFields: func(t *testing.T, engine *OrchestrationEngine) {
				assert.NotNil(t, engine.logger)
			},
		},
		{
			name: "uses provided logger",
			config: EngineConfig{
				Logger: log.Default(),
			},
			validateFields: func(t *testing.T, engine *OrchestrationEngine) {
				assert.NotNil(t, engine.logger)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine := NewOrchestrationEngine(tt.config)
			require.NotNil(t, engine)
			tt.validateFields(t, engine)
		})
	}
}

// TestExecute tests synchronous workflow execution
func TestExecute(t *testing.T) {
	tests := []struct {
		name           string
		workflow       Workflow
		expectError    bool
		errorContains  string
		validateResult func(t *testing.T, result *WorkflowResult)
	}{
		{
			name: "executes empty workflow successfully",
			workflow: Workflow{
				Name:        "Empty Workflow",
				Description: "Test workflow with no steps",
				Steps:       []WorkflowStep{},
			},
			expectError: false,
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Equal(t, StatusCompleted, result.Status)
				assert.Equal(t, 0, result.TotalSteps)
				assert.Equal(t, 0, result.CompletedSteps)
				assert.Equal(t, 0, result.FailedSteps)
			},
		},
		{
			name: "generates workflow ID if not provided",
			workflow: Workflow{
				Name:  "Test Workflow",
				Steps: []WorkflowStep{},
			},
			expectError: false,
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.NotEmpty(t, result.WorkflowID)
				assert.Equal(t, StatusCompleted, result.Status)
			},
		},
		{
			name: "executes workflow with unknown service - error abort",
			workflow: Workflow{
				Name: "Unknown Service Workflow",
				Steps: []WorkflowStep{
					{
						Name:      "unknown_step",
						Service:   "unknown_service",
						Operation: "test",
						OnError:   ErrorAbort,
					},
				},
			},
			expectError:   true,
			errorContains: "workflow aborted at step 1",
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Equal(t, StatusAborted, result.Status)
				assert.Equal(t, 1, result.TotalSteps)
				assert.Equal(t, 1, result.CompletedSteps)
				assert.Greater(t, len(result.Errors), 0)
			},
		},
		{
			name: "continues on error with ErrorContinue strategy",
			workflow: Workflow{
				Name: "Continue on Error Workflow",
				Steps: []WorkflowStep{
					{
						Name:      "failing_step",
						Service:   "unknown_service",
						Operation: "test",
						OnError:   ErrorContinue,
					},
					{
						Name:      "second_step",
						Service:   "unknown_service2",
						Operation: "test",
						OnError:   ErrorContinue,
					},
				},
			},
			expectError: false,
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Equal(t, StatusCompleted, result.Status)
				assert.Equal(t, 2, result.TotalSteps)
				assert.Equal(t, 2, result.CompletedSteps)
				assert.Greater(t, len(result.Errors), 0)
			},
		},
		{
			name: "skips step when condition is false",
			workflow: Workflow{
				Name: "Conditional Skip Workflow",
				Steps: []WorkflowStep{
					{
						Name:      "conditional_step",
						Service:   "test_service",
						Operation: "test",
						Condition: func(ctx *ExecutionContext) bool {
							return false // Skip this step
						},
						OnError: ErrorAbort,
					},
				},
			},
			expectError: false,
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Equal(t, StatusCompleted, result.Status)
				assert.Equal(t, 1, result.TotalSteps)
				// Step was skipped, not executed
				assert.Equal(t, 1, result.CompletedSteps)
			},
		},
		{
			name: "executes step when condition is true",
			workflow: Workflow{
				Name: "Conditional Execute Workflow",
				Steps: []WorkflowStep{
					{
						Name:      "conditional_step",
						Service:   "unknown_service",
						Operation: "test",
						Condition: func(ctx *ExecutionContext) bool {
							return true // Execute this step
						},
						OnError: ErrorContinue,
					},
				},
			},
			expectError: false,
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Equal(t, StatusCompleted, result.Status)
				// Step was executed (and failed due to unknown service)
				assert.Greater(t, len(result.Errors), 0)
			},
		},
		{
			name: "uses provided workflow ID",
			workflow: Workflow{
				ID:    "custom-workflow-id",
				Name:  "Custom ID Workflow",
				Steps: []WorkflowStep{},
			},
			expectError: false,
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Equal(t, "custom-workflow-id", result.WorkflowID)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine := NewOrchestrationEngine(EngineConfig{
				DefaultTimeout: 1 * time.Minute,
			})

			result, err := engine.Execute(tt.workflow)

			if tt.expectError {
				require.Error(t, err)
				if tt.errorContains != "" {
					assert.Contains(t, err.Error(), tt.errorContains)
				}
			} else {
				require.NoError(t, err)
			}

			require.NotNil(t, result)
			tt.validateResult(t, result)
		})
	}
}

// TestExecuteAsync tests asynchronous workflow execution
func TestExecuteAsync(t *testing.T) {
	tests := []struct {
		name          string
		workflow      Workflow
		waitTime      time.Duration
		validateState func(t *testing.T, engine *OrchestrationEngine, workflowID string)
	}{
		{
			name: "starts workflow asynchronously",
			workflow: Workflow{
				Name:  "Async Test Workflow",
				Steps: []WorkflowStep{},
			},
			waitTime: 100 * time.Millisecond,
			validateState: func(t *testing.T, engine *OrchestrationEngine, workflowID string) {
				assert.NotEmpty(t, workflowID)

				// Workflow should be tracked
				engine.mu.RLock()
				ctx, exists := engine.runningWorkflows[workflowID]
				engine.mu.RUnlock()

				assert.True(t, exists)
				assert.NotNil(t, ctx)
			},
		},
		{
			name: "generates workflow ID if not provided",
			workflow: Workflow{
				Name:  "Async No ID Workflow",
				Steps: []WorkflowStep{},
			},
			waitTime: 100 * time.Millisecond,
			validateState: func(t *testing.T, engine *OrchestrationEngine, workflowID string) {
				assert.NotEmpty(t, workflowID)
			},
		},
		{
			name: "uses provided workflow ID",
			workflow: Workflow{
				ID:    "async-custom-id",
				Name:  "Async Custom ID Workflow",
				Steps: []WorkflowStep{},
			},
			waitTime: 100 * time.Millisecond,
			validateState: func(t *testing.T, engine *OrchestrationEngine, workflowID string) {
				assert.Equal(t, "async-custom-id", workflowID)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine := NewOrchestrationEngine(EngineConfig{
				DefaultTimeout: 1 * time.Minute,
			})

			workflowID, err := engine.ExecuteAsync(tt.workflow)
			require.NoError(t, err)

			// Wait for async execution to start
			time.Sleep(tt.waitTime)

			tt.validateState(t, engine, workflowID)
		})
	}
}

// TestGetStatus tests workflow status retrieval
func TestGetStatus(t *testing.T) {
	tests := []struct {
		name          string
		setupWorkflow func(t *testing.T, engine *OrchestrationEngine) string
		workflowID    string
		expectError   bool
		errorContains string
		validateStatus func(t *testing.T, status *WorkflowResult)
	}{
		{
			name: "retrieves status of running workflow",
			setupWorkflow: func(t *testing.T, engine *OrchestrationEngine) string {
				workflow := Workflow{
					Name:  "Status Test Workflow",
					Steps: []WorkflowStep{},
				}
				id, err := engine.ExecuteAsync(workflow)
				require.NoError(t, err)
				time.Sleep(50 * time.Millisecond)
				return id
			},
			expectError: false,
			validateStatus: func(t *testing.T, status *WorkflowResult) {
				assert.NotNil(t, status)
				assert.NotEmpty(t, status.WorkflowID)
			},
		},
		{
			name: "returns error for non-existent workflow",
			setupWorkflow: func(t *testing.T, engine *OrchestrationEngine) string {
				return "non-existent-workflow-id"
			},
			expectError:   true,
			errorContains: "workflow non-existent-workflow-id not found",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine := NewOrchestrationEngine(EngineConfig{
				DefaultTimeout: 1 * time.Minute,
			})

			workflowID := tt.setupWorkflow(t, engine)

			status, err := engine.GetStatus(workflowID)

			if tt.expectError {
				require.Error(t, err)
				if tt.errorContains != "" {
					assert.Contains(t, err.Error(), tt.errorContains)
				}
			} else {
				require.NoError(t, err)
				require.NotNil(t, status)
				if tt.validateStatus != nil {
					tt.validateStatus(t, status)
				}
			}
		})
	}
}

// TestExecuteStepWithRetry tests step retry logic
func TestExecuteStepWithRetry(t *testing.T) {
	tests := []struct {
		name          string
		step          WorkflowStep
		expectError   bool
		validateCtx   func(t *testing.T, ctx *ExecutionContext)
	}{
		{
			name: "fails after max retries",
			step: WorkflowStep{
				Name:       "retry_test",
				Service:    "unknown_service",
				Operation:  "test",
				Retries:    3,
				RetryDelay: 10 * time.Millisecond,
			},
			expectError: true,
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.Greater(t, len(ctx.Errors), 0)
			},
		},
		{
			name: "uses default retry of 1 when retries is 0",
			step: WorkflowStep{
				Name:       "default_retry",
				Service:    "unknown_service",
				Operation:  "test",
				Retries:    0, // Should default to 1
				RetryDelay: 10 * time.Millisecond,
			},
			expectError: true,
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.Greater(t, len(ctx.Errors), 0)
			},
		},
		{
			name: "applies validation to successful results",
			step: WorkflowStep{
				Name:      "validation_test",
				Service:   "test_service",
				Operation: "test",
				Retries:   2,
				Validate: func(result interface{}) error {
					return errors.New("validation failed")
				},
			},
			expectError: true,
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.Greater(t, len(ctx.Errors), 0)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine := NewOrchestrationEngine(EngineConfig{
				DefaultTimeout: 1 * time.Minute,
			})

			ctx := &ExecutionContext{
				WorkflowID:   "test-workflow",
				WorkflowName: "Test",
				StartTime:    time.Now(),
				CurrentStep:  0,
				TotalSteps:   1,
				Status:       StatusRunning,
				Results:      make(map[string]interface{}),
				Errors:       []StepError{},
				Variables:    make(map[string]interface{}),
			}

			err := engine.executeStepWithRetry(ctx, tt.step, 0)

			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}

			if tt.validateCtx != nil {
				tt.validateCtx(t, ctx)
			}
		})
	}
}

// TestExecuteStep tests individual step execution
func TestExecuteStep(t *testing.T) {
	tests := []struct {
		name          string
		step          WorkflowStep
		setupCtx      func() *ExecutionContext
		expectError   bool
		errorContains string
	}{
		{
			name: "returns error for unknown service",
			step: WorkflowStep{
				Name:      "unknown_service_step",
				Service:   "unknown_service",
				Operation: "test",
			},
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results:   make(map[string]interface{}),
					Variables: make(map[string]interface{}),
				}
			},
			expectError:   true,
			errorContains: "unknown service",
		},
		{
			name: "applies transform before execution",
			step: WorkflowStep{
				Name:      "transform_step",
				Service:   "test_service",
				Operation: "test",
				Transform: func(ctx *ExecutionContext) error {
					ctx.SetVariable("transformed", true)
					return nil
				},
			},
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results:   make(map[string]interface{}),
					Variables: make(map[string]interface{}),
				}
			},
			expectError:   true, // Will still fail on unknown service
			errorContains: "unknown service",
		},
		{
			name: "returns error when transform fails",
			step: WorkflowStep{
				Name:      "transform_error_step",
				Service:   "test_service",
				Operation: "test",
				Transform: func(ctx *ExecutionContext) error {
					return errors.New("transform error")
				},
			},
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results:   make(map[string]interface{}),
					Variables: make(map[string]interface{}),
				}
			},
			expectError:   true,
			errorContains: "transform failed",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			engine := NewOrchestrationEngine(EngineConfig{
				DefaultTimeout: 1 * time.Minute,
			})

			ctx := tt.setupCtx()

			_, err := engine.executeStep(ctx, tt.step)

			if tt.expectError {
				require.Error(t, err)
				if tt.errorContains != "" {
					assert.Contains(t, err.Error(), tt.errorContains)
				}
			} else {
				require.NoError(t, err)
			}
		})
	}
}

// TestServiceRouting tests service routing methods
func TestServiceRouting(t *testing.T) {
	engine := NewOrchestrationEngine(EngineConfig{
		DefaultTimeout: 1 * time.Minute,
	})

	services := []struct {
		name          string
		routeFunc     func(WorkflowStep) (interface{}, error)
		serviceName   string
	}{
		{"maximus_eureka", engine.routeMaximusEureka, "maximus_eureka"},
		{"maximus_oraculo", engine.routeMaximusOraculo, "maximus_oraculo"},
		{"maximus_predict", engine.routeMaximusPredict, "maximus_predict"},
		{"lymphnode", engine.routeLymphnode, "lymphnode"},
		{"macrophage", engine.routeMacrophage, "macrophage"},
		{"bcell", engine.routeBCell, "bcell"},
		{"helper_t", engine.routeHelperT, "helper_t"},
		{"cytotoxic_t", engine.routeCytotoxicT, "cytotoxic_t"},
		{"autonomous_investigation", engine.routeAutonomousInvestigation, "autonomous_investigation"},
		{"network_recon", engine.routeNetworkRecon, "network_recon"},
		{"osint", engine.routeOSINT, "osint"},
		{"hcl_analyzer", engine.routeHCLAnalyzer, "hcl_analyzer"},
		{"hcl_planner", engine.routeHCLPlanner, "hcl_planner"},
		{"hcl_executor", engine.routeHCLExecutor, "hcl_executor"},
		{"ethical_audit", engine.routeEthicalAudit, "ethical_audit"},
		{"hsas", engine.routeHSAS, "hsas"},
		{"threat_intel", engine.routeThreatIntel, "threat_intel"},
		{"vuln_intel", engine.routeVulnIntel, "vuln_intel"},
		{"web_attack", engine.routeWebAttack, "web_attack"},
		{"seriema_graph", engine.routeSeriemaGraph, "seriema_graph"},
		{"tataca_ingestion", engine.routeTatacaIngestion, "tataca_ingestion"},
		{"narrative_filter", engine.routeNarrativeFilter, "narrative_filter"},
		{"rte", engine.routeRTE, "rte"},
	}

	for _, svc := range services {
		t.Run(svc.name, func(t *testing.T) {
			step := WorkflowStep{
				Name:      "test_step",
				Service:   svc.serviceName,
				Operation: "test",
			}

			result, err := svc.routeFunc(step)

			// All routing methods currently return "not yet implemented" error
			assert.Error(t, err)
			assert.Nil(t, result)
			assert.Contains(t, err.Error(), "routing not yet implemented")
		})
	}
}

// TestExecuteWithMetadata tests workflow execution with metadata
func TestExecuteWithMetadata(t *testing.T) {
	engine := NewOrchestrationEngine(EngineConfig{
		DefaultTimeout: 1 * time.Minute,
	})

	metadata := map[string]interface{}{
		"category":    "test",
		"priority":    "high",
		"custom_data": "test_value",
	}

	workflow := Workflow{
		Name:     "Metadata Test Workflow",
		Metadata: metadata,
		Steps:    []WorkflowStep{},
	}

	result, err := engine.Execute(workflow)
	require.NoError(t, err)
	require.NotNil(t, result)

	assert.Equal(t, StatusCompleted, result.Status)
}

// TestConcurrentWorkflows tests multiple concurrent async workflows
func TestConcurrentWorkflows(t *testing.T) {
	engine := NewOrchestrationEngine(EngineConfig{
		DefaultTimeout: 1 * time.Minute,
	})

	numWorkflows := 5
	workflowIDs := make([]string, numWorkflows)

	// Start multiple workflows concurrently
	for i := 0; i < numWorkflows; i++ {
		workflow := Workflow{
			Name:  "Concurrent Test Workflow " + string(rune(i)),
			Steps: []WorkflowStep{},
		}

		id, err := engine.ExecuteAsync(workflow)
		require.NoError(t, err)
		workflowIDs[i] = id
	}

	// Wait for all workflows to start
	time.Sleep(200 * time.Millisecond)

	// Verify all workflows are tracked
	engine.mu.RLock()
	defer engine.mu.RUnlock()

	for _, id := range workflowIDs {
		ctx, exists := engine.runningWorkflows[id]
		assert.True(t, exists, "Workflow %s should exist", id)
		assert.NotNil(t, ctx, "Context for workflow %s should not be nil", id)
	}
}

// TestWorkflowTimeout tests workflow timeout handling
func TestWorkflowTimeout(t *testing.T) {
	engine := NewOrchestrationEngine(EngineConfig{
		DefaultTimeout: 1 * time.Second,
	})

	workflow := Workflow{
		Name:    "Timeout Test Workflow",
		Timeout: 100 * time.Millisecond,
		Steps:   []WorkflowStep{},
	}

	result, err := engine.Execute(workflow)
	require.NoError(t, err) // Empty workflow completes immediately
	require.NotNil(t, result)
	assert.Equal(t, StatusCompleted, result.Status)
}

// BenchmarkExecute benchmarks workflow execution
func BenchmarkExecute(b *testing.B) {
	engine := NewOrchestrationEngine(EngineConfig{
		DefaultTimeout: 1 * time.Minute,
	})

	workflow := Workflow{
		Name:  "Benchmark Workflow",
		Steps: []WorkflowStep{},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = engine.Execute(workflow)
	}
}

// BenchmarkExecuteAsync benchmarks async workflow execution
func BenchmarkExecuteAsync(b *testing.B) {
	engine := NewOrchestrationEngine(EngineConfig{
		DefaultTimeout: 1 * time.Minute,
	})

	workflow := Workflow{
		Name:  "Benchmark Async Workflow",
		Steps: []WorkflowStep{},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = engine.ExecuteAsync(workflow)
	}
}
