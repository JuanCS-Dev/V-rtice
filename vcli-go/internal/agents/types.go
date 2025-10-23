package agents

import (
	"context"
	"time"
)

// AgentType represents the type of agent
type AgentType string

const (
	AgentTypeDiagnosticador AgentType = "diagnosticador"
	AgentTypeArquiteto      AgentType = "arquiteto"
	AgentTypeDevSenior      AgentType = "dev_senior"
	AgentTypeTester         AgentType = "tester"
)

// AgentStatus represents the current status of an agent
type AgentStatus string

const (
	StatusIdle       AgentStatus = "idle"
	StatusRunning    AgentStatus = "running"
	StatusCompleted  AgentStatus = "completed"
	StatusFailed     AgentStatus = "failed"
	StatusWaitingHITL AgentStatus = "waiting_hitl"
)

// Agent represents the core interface that all agents must implement
type Agent interface {
	// Type returns the agent type
	Type() AgentType

	// Name returns the agent name
	Name() string

	// Execute runs the agent with the given context and input
	Execute(ctx context.Context, input AgentInput) (*AgentOutput, error)

	// Validate checks if the agent can execute with the given input
	Validate(input AgentInput) error

	// GetCapabilities returns the agent's capabilities
	GetCapabilities() []string

	// GetStatus returns the current agent status
	GetStatus() AgentStatus
}

// AgentInput represents input data for an agent
type AgentInput struct {
	// Task description
	Task string

	// Context data (previous agent outputs, user data, etc.)
	Context map[string]interface{}

	// Target files or directories
	Targets []string

	// Configuration options
	Config map[string]interface{}

	// HITL (Human-in-the-Loop) settings
	HITLEnabled bool
	HITLContext map[string]interface{}
}

// AgentOutput represents output data from an agent
type AgentOutput struct {
	// Agent type that produced this output
	AgentType AgentType

	// Status of execution
	Status AgentStatus

	// Primary result data
	Result interface{}

	// Artifacts generated (file paths)
	Artifacts []string

	// Metrics collected during execution
	Metrics map[string]float64

	// Errors encountered (non-fatal)
	Errors []string

	// HITL decision ID (if approval required)
	HITLDecisionID string

	// Execution metadata
	StartedAt   time.Time
	CompletedAt time.Time
	Duration    time.Duration

	// Next recommended agent (for workflow)
	NextAgent AgentType

	// Additional metadata
	Metadata map[string]interface{}

	// Claude Code Integration: Structured prompt for Sonnet 4.5 processing
	// When running in Claude Code, agents return a formatted prompt here
	// for Claude to process instead of using Oráculo HTTP API
	ClaudePrompt string
}

// AgentConfig holds configuration for agent behavior
type AgentConfig struct {
	// Agent type
	Type AgentType

	// Workspace path
	WorkspacePath string

	// MAXIMUS endpoints
	MaximusEurekaEndpoint      string
	MaximusOraculoEndpoint     string
	MaximusPredictEndpoint     string
	MaximusConsciousnessEndpoint string
	MaximusGovernanceEndpoint  string

	// Immunis endpoints
	ImmunisLymphnodeEndpoint  string
	ImmunisMacrophageEndpoint string
	ImmunisBCellEndpoint      string
	ImmunisHelperTEndpoint    string
	ImmunisCytotoxicTEndpoint string

	// Quality gates
	MinCoveragePercent   float64
	AllowLintWarnings    bool
	RequireSecurityScan  bool
	RequireTestPass      bool

	// HITL triggers
	HITLOnFileDelete     bool
	HITLOnSchemaChange   bool
	HITLOnSecurityChange bool
	HITLOnDeployment     bool

	// Timeouts
	DefaultTimeout time.Duration
	MaxRetries     int

	// Authentication
	AuthToken string

	// Self-Healing configuration
	RetryConfig RetryConfig
}

// RetryConfig configures retry behavior for self-healing agents
type RetryConfig struct {
	// Enable self-healing retry loop
	Enabled bool

	// Maximum retry attempts (default: 3)
	MaxRetries int

	// Backoff strategy: "none", "linear", "exponential"
	BackoffStrategy string

	// Initial backoff duration (for linear/exponential)
	InitialBackoff time.Duration

	// Enable reflection between retries (LLM-as-judge)
	EnableReflection bool

	// Maximum reflection depth (avoid infinite loops)
	MaxReflectionDepth int
}

// RetryAttempt tracks a single retry attempt
type RetryAttempt struct {
	AttemptNumber int
	Error         error
	ErrorType     string // "compilation", "test_failure", "validation", "runtime"
	Reflection    string // LLM reflection on what went wrong
	ActionTaken   string // What was tried to fix
	Timestamp     time.Time
}

// SelfHealingResult tracks the result of self-healing attempts
type SelfHealingResult struct {
	Success       bool
	TotalAttempts int
	Attempts      []RetryAttempt
	FinalError    error
	Recovered     bool
	Duration      time.Duration
}

// DiagnosticResult represents output from DIAGNOSTICADOR agent
type DiagnosticResult struct {
	// Code quality metrics
	CodeQuality struct {
		LinesOfCode       int
		CyclomaticComplexity float64
		MaintainabilityIndex float64
		TechnicalDebt     time.Duration
	}

	// Security findings
	SecurityFindings []SecurityFinding

	// Performance issues
	PerformanceIssues []PerformanceIssue

	// Dependencies analysis
	Dependencies struct {
		Total        int
		Outdated     []string
		Vulnerable   []string
		Licenses     map[string]int
	}

	// Test coverage
	TestCoverage struct {
		LineCoverage   float64
		BranchCoverage float64
		UncoveredFiles []string
	}

	// Recommendations
	Recommendations []string

	// Summary
	Summary string
}

// SecurityFinding represents a security issue found
type SecurityFinding struct {
	Severity    string // critical, high, medium, low
	Category    string // vulnerability, misconfiguration, etc.
	Description string
	FilePath    string
	LineNumber  int
	CWE         string
	Remediation string
}

// PerformanceIssue represents a performance problem
type PerformanceIssue struct {
	Severity    string // high, medium, low
	Category    string // memory, cpu, io, network
	Description string
	FilePath    string
	LineNumber  int
	Impact      string
	Suggestion  string
}

// ArchitecturePlan represents output from ARQUITETO agent
type ArchitecturePlan struct {
	// Plan metadata
	PlanID      string
	Title       string
	Description string
	CreatedAt   time.Time

	// Architecture decision records
	ADRs []ADR

	// Implementation steps
	Steps []ImplementationStep

	// Risk assessment
	Risks []Risk

	// Integration tests required
	IntegrationTests []TestScenario

	// Estimated effort
	EstimatedHours float64

	// Dependencies
	Dependencies []string

	// Summary
	Summary string
}

// ADR represents an Architecture Decision Record
type ADR struct {
	ID          string
	Title       string
	Context     string
	Decision    string
	Consequences []string
	Status      string // proposed, accepted, rejected, superseded
	CreatedAt   time.Time
}

// ImplementationStep represents a step in the implementation plan
type ImplementationStep struct {
	StepNumber  int
	Description string
	AgentType   AgentType
	Inputs      map[string]interface{}
	Outputs     []string
	EstimatedTime time.Duration
	HITLRequired bool
}

// Risk represents a potential risk in the architecture
type Risk struct {
	Severity    string // critical, high, medium, low
	Category    string // technical, security, operational
	Description string
	Impact      string
	Mitigation  string
	Probability float64
}

// TestScenario represents a test scenario
type TestScenario struct {
	Name        string
	Description string
	Type        string // unit, integration, e2e
	PreConditions []string
	Steps       []string
	Expected    string
}

// ImplementationResult represents output from DEV SENIOR agent
type ImplementationResult struct {
	// Task description
	TaskDescription string

	// Implementation plan (FASE 4.5: Planning Phase)
	Plan *ImplementationPlan

	// Self-healing results (FASE 4.5: Retry Loop)
	SelfHealing *SelfHealingResult

	// Files created
	FilesCreated []FileChange

	// Files modified
	FilesModified []FileChange

	// Files deleted
	FilesDeleted []FileChange

	// Git operations
	GitBranch  string
	GitCommit  string   // Single commit hash
	GitCommits []string // Multiple commits (if any)

	// Code generation stats
	LinesAdded   int
	LinesRemoved int
	LinesChanged int

	// Compilation result
	CompilationSuccess bool
	CompilationErrors  []string

	// Test results
	TestsExecuted int
	TestsPassed   int
	TestsFailed   int

	// Quality checks
	QualityChecks struct {
		LintPass     bool
		FormatPass   bool
		SecurityPass bool
	}

	// Code quality score (0-100)
	CodeQualityScore float64

	// Recommendations
	Recommendations []string

	// HITL decisions submitted
	HITLDecisions []string

	// Summary
	Summary string
}

// ImplementationPlan represents the plan before code generation
type ImplementationPlan struct {
	// Plan ID for tracking
	PlanID string

	// Approach description
	Approach string

	// Files to be modified
	FilesToModify []string

	// Files to be created
	FilesToCreate []string

	// Files to be deleted
	FilesToDelete []string

	// Tests needed
	TestsNeeded []string

	// Risks identified
	Risks []string

	// Estimated complexity (1-10)
	Complexity int

	// Dependencies required
	Dependencies []string

	// Generated timestamp
	GeneratedAt time.Time

	// User approved (for HITL)
	UserApproved bool
}

// FileChange represents a file modification
type FileChange struct {
	FilePath  string
	Operation string // create, modify, delete
	Language  string
	Lines     int
	Before    string // content before (for modify/delete)
	After     string // content after (for create/modify)
}

// CodeChange is an alias for FileChange (used in code generation context)
type CodeChange = FileChange

// TestResult represents output from TESTER agent
type TestResult struct {
	// Task description
	TaskDescription string

	// Unit test results
	UnitTests TestSuiteResult

	// Integration test results
	IntegrationTests TestSuiteResult

	// Coverage analysis
	Coverage CoverageResult

	// Performance benchmarks
	Benchmarks []BenchmarkResult

	// Quality gate status
	QualityGates QualityGateResult

	// Regressions detected
	Regressions []Regression

	// Recommendations
	Recommendations []string
}

// TestSuiteResult represents results from a test suite
type TestSuiteResult struct {
	TotalTests   int
	PassedTests  int
	FailedTests  int
	SkippedTests int
	Duration     time.Duration
	Failures     []TestFailure
}

// TestFailure represents a single test failure
type TestFailure struct {
	TestName string
	Message  string
	File     string
	Line     int
}

// CoverageResult represents coverage analysis results
type CoverageResult struct {
	LineCoverage   float64
	BranchCoverage float64
	UncoveredFiles []string
	CoverageByFile map[string]float64
}

// BenchmarkResult represents a single benchmark result
type BenchmarkResult struct {
	Name       string
	Iterations string
	NsPerOp    string
	BytesPerOp string
	AllocsPerOp string
}

// QualityGateResult represents quality gate check results
type QualityGateResult struct {
	AllPassed bool
	Gates     []QualityGate
}

// QualityGate represents a single quality gate
type QualityGate struct {
	Name        string
	Required    float64
	Actual      float64
	Passed      bool
	Description string
}

// Regression represents a detected regression
type Regression struct {
	Type        string // test_failure, performance, coverage
	Description string
	Impact      string // low, medium, high, critical
	Details     string
}

// Legacy types for backward compatibility
type FailedTest struct {
	Name    string
	Message string
	File    string
	Line    int
}

// Legacy Benchmark type (kept for backward compatibility)
type Benchmark struct {
	Name          string
	Iterations    int
	NsPerOp       int64
	BytesPerOp    int64
	AllocsPerOp   int64
	BaselineNsPerOp int64
	Regression    bool
}

// Note: ApprovalRecommendation was moved to QualityGateResult.AllPassed
