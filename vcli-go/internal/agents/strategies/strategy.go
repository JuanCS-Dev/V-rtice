package strategies

import (
	"context"

	"github.com/verticedev/vcli-go/internal/agents"
	"github.com/verticedev/vcli-go/internal/agents/language"
)

// AnalysisStrategy defines the interface for language-specific code analysis
type AnalysisStrategy interface {
	// Language returns the language this strategy supports
	Language() language.Language

	// Analyze performs code analysis on the given targets
	Analyze(ctx context.Context, targets []string) (*agents.DiagnosticResult, error)

	// GetCapabilities returns the analysis capabilities
	GetCapabilities() []string
}

// TestStrategy defines the interface for language-specific testing
type TestStrategy interface {
	// Language returns the language this strategy supports
	Language() language.Language

	// RunTests executes tests for the given targets
	RunTests(ctx context.Context, targets []string) (*agents.TestResult, error)

	// AnalyzeCoverage analyzes test coverage
	AnalyzeCoverage(ctx context.Context, targets []string) (*agents.CoverageResult, error)

	// GetCapabilities returns the testing capabilities
	GetCapabilities() []string
}

// CodeGenStrategy defines the interface for language-specific code generation
type CodeGenStrategy interface {
	// Language returns the language this strategy supports
	Language() language.Language

	// GenerateCode generates code based on the task description
	GenerateCode(ctx context.Context, task string, context map[string]interface{}) ([]agents.CodeChange, error)

	// FormatCode formats the generated code
	FormatCode(code string) (string, error)

	// ValidateSyntax checks if the generated code is syntactically valid
	ValidateSyntax(code string) error

	// GetCapabilities returns the code generation capabilities
	GetCapabilities() []string
}

// StrategyRegistry manages language-specific strategies
type StrategyRegistry struct {
	analysisStrategies map[language.Language]AnalysisStrategy
	testStrategies     map[language.Language]TestStrategy
	codeGenStrategies  map[language.Language]CodeGenStrategy
}

// NewStrategyRegistry creates a new strategy registry
func NewStrategyRegistry() *StrategyRegistry {
	return &StrategyRegistry{
		analysisStrategies: make(map[language.Language]AnalysisStrategy),
		testStrategies:     make(map[language.Language]TestStrategy),
		codeGenStrategies:  make(map[language.Language]CodeGenStrategy),
	}
}

// RegisterAnalysis registers an analysis strategy for a language
func (r *StrategyRegistry) RegisterAnalysis(strategy AnalysisStrategy) {
	r.analysisStrategies[strategy.Language()] = strategy
}

// RegisterTest registers a test strategy for a language
func (r *StrategyRegistry) RegisterTest(strategy TestStrategy) {
	r.testStrategies[strategy.Language()] = strategy
}

// RegisterCodeGen registers a code generation strategy for a language
func (r *StrategyRegistry) RegisterCodeGen(strategy CodeGenStrategy) {
	r.codeGenStrategies[strategy.Language()] = strategy
}

// GetAnalysis retrieves an analysis strategy for a language
func (r *StrategyRegistry) GetAnalysis(lang language.Language) (AnalysisStrategy, bool) {
	strategy, ok := r.analysisStrategies[lang]
	return strategy, ok
}

// GetTest retrieves a test strategy for a language
func (r *StrategyRegistry) GetTest(lang language.Language) (TestStrategy, bool) {
	strategy, ok := r.testStrategies[lang]
	return strategy, ok
}

// GetCodeGen retrieves a code generation strategy for a language
func (r *StrategyRegistry) GetCodeGen(lang language.Language) (CodeGenStrategy, bool) {
	strategy, ok := r.codeGenStrategies[lang]
	return strategy, ok
}

// HasSupport checks if a language is supported for analysis
func (r *StrategyRegistry) HasSupport(lang language.Language) bool {
	_, hasAnalysis := r.analysisStrategies[lang]
	_, hasTest := r.testStrategies[lang]
	_, hasCodeGen := r.codeGenStrategies[lang]
	return hasAnalysis || hasTest || hasCodeGen
}

// SupportedLanguages returns all supported languages
func (r *StrategyRegistry) SupportedLanguages() []language.Language {
	langs := make(map[language.Language]bool)
	for lang := range r.analysisStrategies {
		langs[lang] = true
	}
	for lang := range r.testStrategies {
		langs[lang] = true
	}
	for lang := range r.codeGenStrategies {
		langs[lang] = true
	}

	result := make([]language.Language, 0, len(langs))
	for lang := range langs {
		result = append(result, lang)
	}
	return result
}
