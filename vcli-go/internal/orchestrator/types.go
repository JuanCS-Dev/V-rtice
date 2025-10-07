package orchestrator

import (
	"fmt"
	"time"
)

// ErrorStrategy defines how to handle errors during workflow execution
type ErrorStrategy string

const (
	ErrorContinue ErrorStrategy = "continue" // Continue to next step despite error
	ErrorAbort    ErrorStrategy = "abort"    // Abort entire workflow on error
	ErrorRetry    ErrorStrategy = "retry"    // Retry step with exponential backoff
)

// WorkflowStatus represents the execution status of a workflow
type WorkflowStatus string

const (
	StatusPending   WorkflowStatus = "pending"
	StatusRunning   WorkflowStatus = "running"
	StatusCompleted WorkflowStatus = "completed"
	StatusFailed    WorkflowStatus = "failed"
	StatusAborted   WorkflowStatus = "aborted"
)

// Workflow represents a coordinated multi-service operation
type Workflow struct {
	ID          string
	Name        string
	Description string
	Category    string // offensive, defensive, osint, monitoring
	Steps       []WorkflowStep
	Timeout     time.Duration
	Metadata    map[string]interface{}
}

// WorkflowStep represents a single operation in a workflow
type WorkflowStep struct {
	Name        string
	Description string
	Service     string                                // Service name (e.g., "maximus_eureka")
	Operation   string                                // Operation name (e.g., "GenerateInsight")
	Input       interface{}                           // Input data for this step
	Output      interface{}                           // Output from this step (populated during execution)
	OnError     ErrorStrategy                         // How to handle errors
	Condition   func(ctx *ExecutionContext) bool      // Optional: condition to execute this step
	Transform   func(ctx *ExecutionContext) error     // Optional: transform data before execution
	Validate    func(result interface{}) error        // Optional: validate step output
	Timeout     time.Duration                         // Step-specific timeout
	Retries     int                                   // Number of retries for ErrorRetry strategy
	RetryDelay  time.Duration                         // Initial delay for retries
}

// ExecutionContext holds the runtime state of a workflow execution
type ExecutionContext struct {
	WorkflowID    string
	WorkflowName  string
	StartTime     time.Time
	EndTime       *time.Time
	CurrentStep   int
	TotalSteps    int
	Status        WorkflowStatus
	Results       map[string]interface{} // Step name -> result
	Errors        []StepError
	Metadata      map[string]interface{}
	Variables     map[string]interface{} // Shared variables between steps
}

// StepError represents an error that occurred during step execution
type StepError struct {
	StepIndex   int
	StepName    string
	Service     string
	Operation   string
	Error       error
	Timestamp   time.Time
	Recovered   bool
	RetryCount  int
}

// WorkflowResult represents the final result of a workflow execution
type WorkflowResult struct {
	WorkflowID     string
	WorkflowName   string
	Status         WorkflowStatus
	StartedAt      time.Time
	CompletedAt    *time.Time
	Duration       time.Duration
	TotalSteps     int
	CompletedSteps int
	FailedSteps    int
	Results        map[string]interface{}
	Errors         []StepError
	Summary        string
}

// Progress returns the execution progress as a percentage
func (ctx *ExecutionContext) Progress() float64 {
	if ctx.TotalSteps == 0 {
		return 0.0
	}
	return (float64(ctx.CurrentStep) / float64(ctx.TotalSteps)) * 100.0
}

// SetResult stores a step result in the context
func (ctx *ExecutionContext) SetResult(stepName string, result interface{}) {
	if ctx.Results == nil {
		ctx.Results = make(map[string]interface{})
	}
	ctx.Results[stepName] = result
}

// GetResult retrieves a step result from the context
func (ctx *ExecutionContext) GetResult(stepName string) (interface{}, bool) {
	if ctx.Results == nil {
		return nil, false
	}
	result, ok := ctx.Results[stepName]
	return result, ok
}

// SetVariable stores a shared variable in the context
func (ctx *ExecutionContext) SetVariable(key string, value interface{}) {
	if ctx.Variables == nil {
		ctx.Variables = make(map[string]interface{})
	}
	ctx.Variables[key] = value
}

// GetVariable retrieves a shared variable from the context
func (ctx *ExecutionContext) GetVariable(key string) (interface{}, bool) {
	if ctx.Variables == nil {
		return nil, false
	}
	value, ok := ctx.Variables[key]
	return value, ok
}

// AddError records an error during workflow execution
func (ctx *ExecutionContext) AddError(stepIndex int, stepName, service, operation string, err error) {
	ctx.Errors = append(ctx.Errors, StepError{
		StepIndex: stepIndex,
		StepName:  stepName,
		Service:   service,
		Operation: operation,
		Error:     err,
		Recovered: false,
		RetryCount: 0,
	})
}

// MarkErrorRecovered marks the last error as recovered
func (ctx *ExecutionContext) MarkErrorRecovered() {
	if len(ctx.Errors) > 0 {
		ctx.Errors[len(ctx.Errors)-1].Recovered = true
	}
}

// IncrementRetryCount increments the retry count for the last error
func (ctx *ExecutionContext) IncrementRetryCount() {
	if len(ctx.Errors) > 0 {
		ctx.Errors[len(ctx.Errors)-1].RetryCount++
	}
}

// HasUnrecoveredErrors returns true if there are unrecovered errors
func (ctx *ExecutionContext) HasUnrecoveredErrors() bool {
	for _, err := range ctx.Errors {
		if !err.Recovered {
			return true
		}
	}
	return false
}

// ToResult converts ExecutionContext to WorkflowResult
func (ctx *ExecutionContext) ToResult() *WorkflowResult {
	var duration time.Duration
	if ctx.EndTime != nil {
		duration = ctx.EndTime.Sub(ctx.StartTime)
	} else {
		duration = time.Since(ctx.StartTime)
	}

	failedSteps := 0
	for _, err := range ctx.Errors {
		if !err.Recovered {
			failedSteps++
		}
	}

	summary := fmt.Sprintf("Workflow '%s' %s. Completed %d/%d steps",
		ctx.WorkflowName, ctx.Status, ctx.CurrentStep, ctx.TotalSteps)

	if failedSteps > 0 {
		summary += fmt.Sprintf(" with %d errors", failedSteps)
	}

	return &WorkflowResult{
		WorkflowID:     ctx.WorkflowID,
		WorkflowName:   ctx.WorkflowName,
		Status:         ctx.Status,
		StartedAt:      ctx.StartTime,
		CompletedAt:    ctx.EndTime,
		Duration:       duration,
		TotalSteps:     ctx.TotalSteps,
		CompletedSteps: ctx.CurrentStep,
		FailedSteps:    failedSteps,
		Results:        ctx.Results,
		Errors:         ctx.Errors,
		Summary:        summary,
	}
}

// StepInput is a helper interface for steps that need dynamic input
type StepInput interface {
	Build(ctx *ExecutionContext) (interface{}, error)
}

// StepOutput is a helper interface for steps that need dynamic output processing
type StepOutput interface {
	Process(result interface{}, ctx *ExecutionContext) error
}
