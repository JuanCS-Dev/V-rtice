// Package nlp - NLP Orchestrator
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// The Orchestrator coordinates all NLP modules into a complete
// natural language processing pipeline.
package nlp

import (
	"fmt"
	"sync"
	"time"

	"github.com/verticedev/vcli-go/internal/nlp/context"
	"github.com/verticedev/vcli-go/internal/nlp/entities"
	"github.com/verticedev/vcli-go/internal/nlp/generator"
	"github.com/verticedev/vcli-go/internal/nlp/learning"
	"github.com/verticedev/vcli-go/internal/nlp/tokenizer"
	"github.com/verticedev/vcli-go/internal/nlp/validator"
	"github.com/verticedev/vcli-go/pkg/nlp"
)

// Orchestrator coordinates all NLP modules
type Orchestrator struct {
	tokenizer     *tokenizer.Tokenizer
	extractor     *entities.Extractor
	contextMgr    *context.Manager
	generator     *generator.Generator
	validator     *validator.Validator
	learner       *learning.Engine
	mu            sync.RWMutex
	statsEnabled  bool
	stats         *OrchestratorStats
}

// OrchestratorStats tracks pipeline statistics
type OrchestratorStats struct {
	TotalRequests      int     `json:"total_requests"`
	SuccessfulRequests int     `json:"successful_requests"`
	FailedRequests     int     `json:"failed_requests"`
	ValidationFailures int     `json:"validation_failures"`
	AverageLatencyMs   float64 `json:"avg_latency_ms"`
	totalLatencyMs     float64
}

// ProcessingResult represents the result of NLP processing
type ProcessingResult struct {
	// Input
	Input     string `json:"input"`
	SessionID string `json:"session_id"`

	// Pipeline outputs
	Tokens     []nlp.Token    `json:"tokens"`
	Entities   []nlp.Entity   `json:"entities"`
	Intent     *nlp.Intent    `json:"intent"`
	Command    *nlp.Command   `json:"command"`
	Validation *validator.ValidationResult `json:"validation"`

	// Pattern info
	PatternID       string  `json:"pattern_id,omitempty"`
	PatternLearned  bool    `json:"pattern_learned"`
	SimilarPatterns int     `json:"similar_patterns"`

	// Status
	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`

	// Performance
	LatencyMs float64 `json:"latency_ms"`
}

// NewOrchestrator creates a new NLP orchestrator
func NewOrchestrator(learningDBPath string) (*Orchestrator, error) {
	learner, err := learning.NewEngine(learningDBPath, 100)
	if err != nil {
		return nil, fmt.Errorf("failed to create learning engine: %w", err)
	}

	return &Orchestrator{
		tokenizer:    tokenizer.NewTokenizer(),
		extractor:    entities.NewExtractor(),
		contextMgr:   context.NewManager(),
		generator:    generator.NewGenerator(),
		validator:    validator.NewValidator(),
		learner:      learner,
		statsEnabled: true,
		stats:        &OrchestratorStats{},
	}, nil
}

// Close closes all resources
func (o *Orchestrator) Close() error {
	return o.learner.Close()
}

// Process processes natural language input through the complete pipeline
func (o *Orchestrator) Process(input string, sessionID string) (*ProcessingResult, error) {
	startTime := getCurrentTimeMs()

	result := &ProcessingResult{
		Input:     input,
		SessionID: sessionID,
		Success:   false,
	}

	// Update stats
	defer func() {
		result.LatencyMs = getCurrentTimeMs() - startTime
		o.updateStats(result)
	}()

	// Step 1: Tokenize
	tokens, err := o.tokenizer.Tokenize(input)
	if err != nil {
		result.Error = fmt.Sprintf("Tokenization failed: %v", err)
		return result, err
	}
	result.Tokens = tokens

	// Step 2: Extract entities
	// Note: Intent would come from a classifier, but for now we infer from entities
	intent := o.inferIntent(tokens)
	result.Intent = intent

	ctx, _ := o.contextMgr.GetSession(sessionID)
	if ctx == nil {
		ctx = o.contextMgr.CreateSession()
		result.SessionID = ctx.SessionID
	}

	extractedEntities, err := o.extractor.Extract(tokens, intent)
	if err != nil {
		result.Error = fmt.Sprintf("Entity extraction failed: %v", err)
		return result, err
	}
	result.Entities = extractedEntities

	// Resolve ambiguities with context
	resolvedEntities, _ := o.extractor.ResolveAmbiguity(extractedEntities, ctx)
	result.Entities = resolvedEntities

	// Step 3: Generate command
	command, err := o.generator.Generate(intent, resolvedEntities)
	if err != nil {
		result.Error = fmt.Sprintf("Command generation failed: %v", err)
		return result, err
	}
	result.Command = command

	// Step 4: Validate command
	validation, err := o.validator.ValidateCommand(command)
	if err != nil {
		result.Error = fmt.Sprintf("Validation failed: %v", err)
		return result, err
	}
	result.Validation = validation

	if !validation.Valid {
		result.Error = validation.Error
		result.Success = false
		return result, fmt.Errorf("validation failed: %s", validation.Error)
	}

	// Step 5: Check for similar patterns
	similar, _ := o.learner.FindSimilarPatterns(input, 5)
	result.SimilarPatterns = len(similar)

	// Step 6: Learn pattern
	if err := o.learner.LearnPattern(input, intent, command); err == nil {
		result.PatternLearned = true
		result.PatternID = GeneratePatternID(input)
	}

	// Step 7: Update context
	o.contextMgr.AddToHistory(result.SessionID, nlp.HistoryEntry{
		Input:     input,
		Intent:    intent,
		Command:   command,
		Success:   true,
		Timestamp: time.Now(),
	})

	// Track resource if applicable
	if len(resolvedEntities) > 0 {
		for _, entity := range resolvedEntities {
			if entity.Type == nlp.EntityTypeK8S_RESOURCE && entity.Value != "" {
				// Track the resource type
				o.contextMgr.SetCurrentResource(result.SessionID, entity.Value)
			}
			if entity.Type == nlp.EntityTypeNAMESPACE && entity.Value != "" {
				o.contextMgr.SetCurrentNamespace(result.SessionID, entity.Value)
			}
		}
	}

	result.Success = true
	return result, nil
}

// ProcessWithFeedback processes input and records feedback
func (o *Orchestrator) ProcessWithFeedback(input string, sessionID string, feedback *learning.Feedback) (*ProcessingResult, error) {
	result, err := o.Process(input, sessionID)

	// Record feedback if pattern was learned
	if result.PatternLearned && feedback != nil {
		feedback.PatternID = result.PatternID
		feedback.Input = input
		if result.Command != nil {
			feedback.Command = o.generator.ExplainCommand(result.Command)
		}
		o.learner.RecordFeedback(feedback)
	}

	return result, err
}

// GetSuggestions returns suggestions for incomplete input
func (o *Orchestrator) GetSuggestions(input string) []validator.Suggestion {
	// Tokenize to get structure
	tokens, err := o.tokenizer.Tokenize(input)
	if err != nil || len(tokens) == 0 {
		return o.validator.Suggest("", []nlp.Token{})
	}

	return o.validator.Suggest(input, tokens)
}

// GetPopularCommands returns popular learned commands
func (o *Orchestrator) GetPopularCommands(limit int) ([]*learning.Pattern, error) {
	return o.learner.GetPopularPatterns(limit)
}

// GetStats returns orchestrator statistics
func (o *Orchestrator) GetStats() *OrchestratorStats {
	o.mu.RLock()
	defer o.mu.RUnlock()

	if !o.statsEnabled {
		return nil
	}

	// Calculate average latency
	if o.stats.TotalRequests > 0 {
		o.stats.AverageLatencyMs = o.stats.totalLatencyMs / float64(o.stats.TotalRequests)
	}

	return o.stats
}

// GetDetailedStats returns detailed stats from all modules
func (o *Orchestrator) GetDetailedStats() map[string]interface{} {
	stats := make(map[string]interface{})

	// Orchestrator stats
	stats["orchestrator"] = o.GetStats()

	// Learning engine stats
	stats["learning"] = o.learner.GetStats()

	// Context manager stats
	stats["active_sessions"] = o.contextMgr.GetActiveSessionCount()

	return stats
}

// ClearCache clears all caches
func (o *Orchestrator) ClearCache() {
	o.learner.ClearCache()
	// Context manager doesn't have explicit cache, but we could add cleanup
}

// inferIntent infers intent from tokens (simple heuristic)
// In a real system, this would be a trained classifier
func (o *Orchestrator) inferIntent(tokens []nlp.Token) *nlp.Intent {
	intent := &nlp.Intent{
		Category:   nlp.IntentCategoryQUERY, // Default to query
		Confidence: 0.8,
		Modifiers:  []nlp.Modifier{},
	}

	// Find verb and target
	for i, token := range tokens {
		if token.Type == nlp.TokenTypeVERB && intent.Verb == "" {
			intent.Verb = token.Normalized
			// Check if it's an action verb
			if isActionVerb(token.Normalized) {
				intent.Category = nlp.IntentCategoryACTION
			}
		}
		if token.Type == nlp.TokenTypeNOUN && intent.Target == "" {
			intent.Target = token.Normalized
		}
		if token.Type == nlp.TokenTypeNUMBER && i > 0 {
			// Likely a count/replica modifier
			intent.Modifiers = append(intent.Modifiers, nlp.Modifier{
				Type:  "count",
				Key:   "replicas",
				Value: token.Normalized,
			})
		}
	}

	// If no verb found, assume "show"
	if intent.Verb == "" {
		intent.Verb = "show"
		intent.Confidence = 0.6 // Lower confidence
	}

	return intent
}

// isActionVerb checks if a verb is an action (vs query)
func isActionVerb(verb string) bool {
	actionVerbs := []string{"create", "delete", "update", "scale", "apply", "patch", "remove", "destroy", "kill"}
	for _, av := range actionVerbs {
		if verb == av {
			return true
		}
	}
	return false
}

// updateStats updates orchestrator statistics
func (o *Orchestrator) updateStats(result *ProcessingResult) {
	if !o.statsEnabled {
		return
	}

	o.mu.Lock()
	defer o.mu.Unlock()

	o.stats.TotalRequests++
	o.stats.totalLatencyMs += result.LatencyMs

	if result.Success {
		o.stats.SuccessfulRequests++
	} else {
		o.stats.FailedRequests++
		if result.Validation != nil && !result.Validation.Valid {
			o.stats.ValidationFailures++
		}
	}
}

// String returns string representation
func (o *Orchestrator) String() string {
	return fmt.Sprintf("NLPOrchestrator(modules=6, sessions=%d, patterns=%d)",
		o.contextMgr.GetActiveSessionCount(),
		o.learner.GetStats().TotalPatterns)
}

// Helper functions
func getCurrentTimeMs() float64 {
	return float64(time.Now().UnixNano()) / 1e6
}

// GeneratePatternID is exported for testing
func GeneratePatternID(input string) string {
	return fmt.Sprintf("%x", []byte(input))
}
