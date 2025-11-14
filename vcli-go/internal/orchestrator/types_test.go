package orchestrator

import (
	"errors"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestExecutionContextProgress tests the Progress method
func TestExecutionContextProgress(t *testing.T) {
	tests := []struct {
		name           string
		currentStep    int
		totalSteps     int
		expectedProgress float64
	}{
		{
			name:           "zero steps returns zero progress",
			currentStep:    0,
			totalSteps:     0,
			expectedProgress: 0.0,
		},
		{
			name:           "50% progress",
			currentStep:    5,
			totalSteps:     10,
			expectedProgress: 50.0,
		},
		{
			name:           "100% progress",
			currentStep:    10,
			totalSteps:     10,
			expectedProgress: 100.0,
		},
		{
			name:           "25% progress",
			currentStep:    1,
			totalSteps:     4,
			expectedProgress: 25.0,
		},
		{
			name:           "single step completed",
			currentStep:    1,
			totalSteps:     1,
			expectedProgress: 100.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := &ExecutionContext{
				CurrentStep: tt.currentStep,
				TotalSteps:  tt.totalSteps,
			}

			progress := ctx.Progress()
			assert.Equal(t, tt.expectedProgress, progress)
		})
	}
}

// TestExecutionContextSetResult tests result storage
func TestExecutionContextSetResult(t *testing.T) {
	tests := []struct {
		name       string
		setupCtx   func() *ExecutionContext
		stepName   string
		result     interface{}
		validateCtx func(t *testing.T, ctx *ExecutionContext)
	}{
		{
			name: "stores result in initialized map",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results: make(map[string]interface{}),
				}
			},
			stepName: "test_step",
			result:   "test_result",
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.Equal(t, "test_result", ctx.Results["test_step"])
			},
		},
		{
			name: "initializes map if nil",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results: nil,
				}
			},
			stepName: "test_step",
			result:   42,
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.NotNil(t, ctx.Results)
				assert.Equal(t, 42, ctx.Results["test_step"])
			},
		},
		{
			name: "overwrites existing result",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results: map[string]interface{}{
						"test_step": "old_value",
					},
				}
			},
			stepName: "test_step",
			result:   "new_value",
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.Equal(t, "new_value", ctx.Results["test_step"])
			},
		},
		{
			name: "stores complex object",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results: make(map[string]interface{}),
				}
			},
			stepName: "complex_step",
			result: map[string]interface{}{
				"key1": "value1",
				"key2": 123,
			},
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				result := ctx.Results["complex_step"].(map[string]interface{})
				assert.Equal(t, "value1", result["key1"])
				assert.Equal(t, 123, result["key2"])
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := tt.setupCtx()
			ctx.SetResult(tt.stepName, tt.result)
			tt.validateCtx(t, ctx)
		})
	}
}

// TestExecutionContextGetResult tests result retrieval
func TestExecutionContextGetResult(t *testing.T) {
	tests := []struct {
		name          string
		setupCtx      func() *ExecutionContext
		stepName      string
		expectedValue interface{}
		expectedOk    bool
	}{
		{
			name: "retrieves existing result",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results: map[string]interface{}{
						"test_step": "test_value",
					},
				}
			},
			stepName:      "test_step",
			expectedValue: "test_value",
			expectedOk:    true,
		},
		{
			name: "returns false for missing result",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results: map[string]interface{}{},
				}
			},
			stepName:      "missing_step",
			expectedValue: nil,
			expectedOk:    false,
		},
		{
			name: "returns false for nil map",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Results: nil,
				}
			},
			stepName:      "any_step",
			expectedValue: nil,
			expectedOk:    false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := tt.setupCtx()
			value, ok := ctx.GetResult(tt.stepName)
			assert.Equal(t, tt.expectedOk, ok)
			assert.Equal(t, tt.expectedValue, value)
		})
	}
}

// TestExecutionContextSetVariable tests variable storage
func TestExecutionContextSetVariable(t *testing.T) {
	tests := []struct {
		name       string
		setupCtx   func() *ExecutionContext
		key        string
		value      interface{}
		validateCtx func(t *testing.T, ctx *ExecutionContext)
	}{
		{
			name: "stores variable in initialized map",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Variables: make(map[string]interface{}),
				}
			},
			key:   "test_var",
			value: "test_value",
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.Equal(t, "test_value", ctx.Variables["test_var"])
			},
		},
		{
			name: "initializes map if nil",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Variables: nil,
				}
			},
			key:   "test_var",
			value: 123,
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.NotNil(t, ctx.Variables)
				assert.Equal(t, 123, ctx.Variables["test_var"])
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := tt.setupCtx()
			ctx.SetVariable(tt.key, tt.value)
			tt.validateCtx(t, ctx)
		})
	}
}

// TestExecutionContextGetVariable tests variable retrieval
func TestExecutionContextGetVariable(t *testing.T) {
	tests := []struct {
		name          string
		setupCtx      func() *ExecutionContext
		key           string
		expectedValue interface{}
		expectedOk    bool
	}{
		{
			name: "retrieves existing variable",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Variables: map[string]interface{}{
						"test_var": "test_value",
					},
				}
			},
			key:           "test_var",
			expectedValue: "test_value",
			expectedOk:    true,
		},
		{
			name: "returns false for missing variable",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Variables: map[string]interface{}{},
				}
			},
			key:           "missing_var",
			expectedValue: nil,
			expectedOk:    false,
		},
		{
			name: "returns false for nil map",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Variables: nil,
				}
			},
			key:           "any_var",
			expectedValue: nil,
			expectedOk:    false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := tt.setupCtx()
			value, ok := ctx.GetVariable(tt.key)
			assert.Equal(t, tt.expectedOk, ok)
			assert.Equal(t, tt.expectedValue, value)
		})
	}
}

// TestExecutionContextAddError tests error recording
func TestExecutionContextAddError(t *testing.T) {
	tests := []struct {
		name       string
		stepIndex  int
		stepName   string
		service    string
		operation  string
		err        error
		validateCtx func(t *testing.T, ctx *ExecutionContext)
	}{
		{
			name:      "adds error to empty list",
			stepIndex: 0,
			stepName:  "failing_step",
			service:   "test_service",
			operation: "test_op",
			err:       errors.New("test error"),
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				require.Len(t, ctx.Errors, 1)
				assert.Equal(t, 0, ctx.Errors[0].StepIndex)
				assert.Equal(t, "failing_step", ctx.Errors[0].StepName)
				assert.Equal(t, "test_service", ctx.Errors[0].Service)
				assert.Equal(t, "test_op", ctx.Errors[0].Operation)
				assert.Equal(t, "test error", ctx.Errors[0].Error.Error())
				assert.False(t, ctx.Errors[0].Recovered)
				assert.Equal(t, 0, ctx.Errors[0].RetryCount)
			},
		},
		{
			name:      "adds multiple errors",
			stepIndex: 1,
			stepName:  "second_failing_step",
			service:   "another_service",
			operation: "another_op",
			err:       errors.New("second error"),
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				// Should have the error we just added
				require.Len(t, ctx.Errors, 1)
				assert.Equal(t, "second_failing_step", ctx.Errors[0].StepName)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := &ExecutionContext{
				Errors: []StepError{},
			}

			ctx.AddError(tt.stepIndex, tt.stepName, tt.service, tt.operation, tt.err)
			tt.validateCtx(t, ctx)
		})
	}
}

// TestExecutionContextMarkErrorRecovered tests error recovery marking
func TestExecutionContextMarkErrorRecovered(t *testing.T) {
	tests := []struct {
		name       string
		setupCtx   func() *ExecutionContext
		validateCtx func(t *testing.T, ctx *ExecutionContext)
	}{
		{
			name: "marks last error as recovered",
			setupCtx: func() *ExecutionContext {
				ctx := &ExecutionContext{
					Errors: []StepError{
						{
							StepName:  "error1",
							Recovered: false,
						},
						{
							StepName:  "error2",
							Recovered: false,
						},
					},
				}
				return ctx
			},
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.False(t, ctx.Errors[0].Recovered)
				assert.True(t, ctx.Errors[1].Recovered)
			},
		},
		{
			name: "handles empty error list",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Errors: []StepError{},
				}
			},
			validateCtx: func(t *testing.T, ctx *ExecutionContext) {
				assert.Len(t, ctx.Errors, 0)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := tt.setupCtx()
			ctx.MarkErrorRecovered()
			tt.validateCtx(t, ctx)
		})
	}
}

// TestExecutionContextIncrementRetryCount tests retry count increment
func TestExecutionContextIncrementRetryCount(t *testing.T) {
	tests := []struct {
		name       string
		setupCtx   func() *ExecutionContext
		increments int
		expectedCount int
	}{
		{
			name: "increments retry count for last error",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Errors: []StepError{
						{
							StepName:   "test_step",
							RetryCount: 0,
						},
					},
				}
			},
			increments:    1,
			expectedCount: 1,
		},
		{
			name: "increments multiple times",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Errors: []StepError{
						{
							StepName:   "test_step",
							RetryCount: 0,
						},
					},
				}
			},
			increments:    3,
			expectedCount: 3,
		},
		{
			name: "handles empty error list",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Errors: []StepError{},
				}
			},
			increments:    1,
			expectedCount: 0, // No error to increment
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := tt.setupCtx()
			for i := 0; i < tt.increments; i++ {
				ctx.IncrementRetryCount()
			}

			if len(ctx.Errors) > 0 {
				assert.Equal(t, tt.expectedCount, ctx.Errors[len(ctx.Errors)-1].RetryCount)
			}
		})
	}
}

// TestExecutionContextHasUnrecoveredErrors tests unrecovered error detection
func TestExecutionContextHasUnrecoveredErrors(t *testing.T) {
	tests := []struct {
		name     string
		setupCtx func() *ExecutionContext
		expected bool
	}{
		{
			name: "returns true when unrecovered errors exist",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Errors: []StepError{
						{Recovered: true},
						{Recovered: false},
					},
				}
			},
			expected: true,
		},
		{
			name: "returns false when all errors recovered",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Errors: []StepError{
						{Recovered: true},
						{Recovered: true},
					},
				}
			},
			expected: false,
		},
		{
			name: "returns false for empty error list",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					Errors: []StepError{},
				}
			},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := tt.setupCtx()
			result := ctx.HasUnrecoveredErrors()
			assert.Equal(t, tt.expected, result)
		})
	}
}

// TestExecutionContextToResult tests conversion to WorkflowResult
func TestExecutionContextToResult(t *testing.T) {
	tests := []struct {
		name       string
		setupCtx   func() *ExecutionContext
		validateResult func(t *testing.T, result *WorkflowResult)
	}{
		{
			name: "converts completed workflow",
			setupCtx: func() *ExecutionContext {
				endTime := time.Now().Add(1 * time.Minute)
				return &ExecutionContext{
					WorkflowID:   "test-workflow-1",
					WorkflowName: "Test Workflow",
					StartTime:    time.Now(),
					EndTime:      &endTime,
					CurrentStep:  5,
					TotalSteps:   5,
					Status:       StatusCompleted,
					Results:      map[string]interface{}{"step1": "result1"},
					Errors:       []StepError{},
				}
			},
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Equal(t, "test-workflow-1", result.WorkflowID)
				assert.Equal(t, "Test Workflow", result.WorkflowName)
				assert.Equal(t, StatusCompleted, result.Status)
				assert.Equal(t, 5, result.TotalSteps)
				assert.Equal(t, 5, result.CompletedSteps)
				assert.Equal(t, 0, result.FailedSteps)
				assert.NotNil(t, result.CompletedAt)
				assert.Greater(t, result.Duration, time.Duration(0))
				assert.Contains(t, result.Summary, "completed")
			},
		},
		{
			name: "converts running workflow (no end time)",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					WorkflowID:   "test-workflow-2",
					WorkflowName: "Running Workflow",
					StartTime:    time.Now(),
					EndTime:      nil,
					CurrentStep:  3,
					TotalSteps:   10,
					Status:       StatusRunning,
					Results:      map[string]interface{}{},
					Errors:       []StepError{},
				}
			},
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Equal(t, StatusRunning, result.Status)
				assert.Nil(t, result.CompletedAt)
				assert.Greater(t, result.Duration, time.Duration(0))
			},
		},
		{
			name: "counts failed steps correctly",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					WorkflowID:   "test-workflow-3",
					WorkflowName: "Failed Workflow",
					StartTime:    time.Now(),
					CurrentStep:  3,
					TotalSteps:   5,
					Status:       StatusFailed,
					Results:      map[string]interface{}{},
					Errors: []StepError{
						{Recovered: false},
						{Recovered: true},
						{Recovered: false},
					},
				}
			},
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Equal(t, 2, result.FailedSteps)
				assert.Contains(t, result.Summary, "2 errors")
			},
		},
		{
			name: "includes metadata in summary",
			setupCtx: func() *ExecutionContext {
				return &ExecutionContext{
					WorkflowID:   "test-workflow-4",
					WorkflowName: "Metadata Workflow",
					StartTime:    time.Now(),
					CurrentStep:  2,
					TotalSteps:   5,
					Status:       StatusRunning,
					Results:      map[string]interface{}{},
					Errors:       []StepError{},
				}
			},
			validateResult: func(t *testing.T, result *WorkflowResult) {
				assert.Contains(t, result.Summary, "Metadata Workflow")
				assert.Contains(t, result.Summary, "2/5")
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := tt.setupCtx()
			result := ctx.ToResult()
			require.NotNil(t, result)
			tt.validateResult(t, result)
		})
	}
}

// TestErrorStrategy tests error strategy constants
func TestErrorStrategy(t *testing.T) {
	tests := []struct {
		name     string
		strategy ErrorStrategy
		expected string
	}{
		{"continue strategy", ErrorContinue, "continue"},
		{"abort strategy", ErrorAbort, "abort"},
		{"retry strategy", ErrorRetry, "retry"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.expected, string(tt.strategy))
		})
	}
}

// TestWorkflowStatus tests workflow status constants
func TestWorkflowStatus(t *testing.T) {
	tests := []struct {
		name     string
		status   WorkflowStatus
		expected string
	}{
		{"pending status", StatusPending, "pending"},
		{"running status", StatusRunning, "running"},
		{"completed status", StatusCompleted, "completed"},
		{"failed status", StatusFailed, "failed"},
		{"aborted status", StatusAborted, "aborted"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.expected, string(tt.status))
		})
	}
}

// TestWorkflow tests the Workflow structure
func TestWorkflow(t *testing.T) {
	workflow := Workflow{
		ID:          "test-id",
		Name:        "Test Workflow",
		Description: "Test Description",
		Category:    "test",
		Steps: []WorkflowStep{
			{Name: "step1"},
			{Name: "step2"},
		},
		Timeout: 5 * time.Minute,
		Metadata: map[string]interface{}{
			"key": "value",
		},
	}

	assert.Equal(t, "test-id", workflow.ID)
	assert.Equal(t, "Test Workflow", workflow.Name)
	assert.Equal(t, 2, len(workflow.Steps))
	assert.Equal(t, 5*time.Minute, workflow.Timeout)
	assert.Equal(t, "value", workflow.Metadata["key"])
}

// TestWorkflowStep tests the WorkflowStep structure
func TestWorkflowStep(t *testing.T) {
	step := WorkflowStep{
		Name:        "test_step",
		Description: "Test Description",
		Service:     "test_service",
		Operation:   "test_operation",
		Input:       map[string]interface{}{"key": "value"},
		OnError:     ErrorRetry,
		Timeout:     1 * time.Minute,
		Retries:     3,
		RetryDelay:  5 * time.Second,
	}

	assert.Equal(t, "test_step", step.Name)
	assert.Equal(t, "test_service", step.Service)
	assert.Equal(t, ErrorRetry, step.OnError)
	assert.Equal(t, 3, step.Retries)
	assert.Equal(t, 5*time.Second, step.RetryDelay)
}

// TestStepError tests the StepError structure
func TestStepError(t *testing.T) {
	err := StepError{
		StepIndex:  0,
		StepName:   "test_step",
		Service:    "test_service",
		Operation:  "test_op",
		Error:      errors.New("test error"),
		Timestamp:  time.Now(),
		Recovered:  false,
		RetryCount: 2,
	}

	assert.Equal(t, 0, err.StepIndex)
	assert.Equal(t, "test_step", err.StepName)
	assert.Equal(t, "test error", err.Error.Error())
	assert.False(t, err.Recovered)
	assert.Equal(t, 2, err.RetryCount)
}

// TestWorkflowStepWithCondition tests step conditions
func TestWorkflowStepWithCondition(t *testing.T) {
	tests := []struct {
		name      string
		condition func(ctx *ExecutionContext) bool
		ctx       *ExecutionContext
		expected  bool
	}{
		{
			name: "condition returns true",
			condition: func(ctx *ExecutionContext) bool {
				return true
			},
			ctx:      &ExecutionContext{},
			expected: true,
		},
		{
			name: "condition returns false",
			condition: func(ctx *ExecutionContext) bool {
				return false
			},
			ctx:      &ExecutionContext{},
			expected: false,
		},
		{
			name: "condition checks context state",
			condition: func(ctx *ExecutionContext) bool {
				_, ok := ctx.GetResult("previous_step")
				return ok
			},
			ctx: &ExecutionContext{
				Results: map[string]interface{}{
					"previous_step": "result",
				},
			},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.condition(tt.ctx)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// TestWorkflowStepWithTransform tests step transforms
func TestWorkflowStepWithTransform(t *testing.T) {
	tests := []struct {
		name      string
		transform func(ctx *ExecutionContext) error
		ctx       *ExecutionContext
		expectErr bool
		validate  func(t *testing.T, ctx *ExecutionContext)
	}{
		{
			name: "transform modifies context",
			transform: func(ctx *ExecutionContext) error {
				ctx.SetVariable("transformed", true)
				return nil
			},
			ctx: &ExecutionContext{
				Variables: make(map[string]interface{}),
			},
			expectErr: false,
			validate: func(t *testing.T, ctx *ExecutionContext) {
				val, ok := ctx.GetVariable("transformed")
				assert.True(t, ok)
				assert.Equal(t, true, val)
			},
		},
		{
			name: "transform returns error",
			transform: func(ctx *ExecutionContext) error {
				return errors.New("transform error")
			},
			ctx:       &ExecutionContext{},
			expectErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.transform(tt.ctx)
			if tt.expectErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				if tt.validate != nil {
					tt.validate(t, tt.ctx)
				}
			}
		})
	}
}

// TestWorkflowStepWithValidate tests step validation
func TestWorkflowStepWithValidate(t *testing.T) {
	tests := []struct {
		name      string
		validate  func(result interface{}) error
		result    interface{}
		expectErr bool
	}{
		{
			name: "validation passes",
			validate: func(result interface{}) error {
				if result == nil {
					return errors.New("result is nil")
				}
				return nil
			},
			result:    "valid_result",
			expectErr: false,
		},
		{
			name: "validation fails",
			validate: func(result interface{}) error {
				if result == nil {
					return errors.New("result is nil")
				}
				return nil
			},
			result:    nil,
			expectErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.validate(tt.result)
			if tt.expectErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}
