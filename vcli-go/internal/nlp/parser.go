// Package nlp - Main parser implementation
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is the main NLP parser that orchestrates all components.
package nlp

import (
	"context"

	"github.com/verticedev/vcli-go/internal/nlp/entities"
	"github.com/verticedev/vcli-go/internal/nlp/generator"
	"github.com/verticedev/vcli-go/internal/nlp/intent"
	"github.com/verticedev/vcli-go/internal/nlp/tokenizer"
	"github.com/verticedev/vcli-go/pkg/nlp"
)

// parser implements the nlp.Parser interface
type parser struct {
	tokenizer *tokenizer.Tokenizer
	intent    *intent.Classifier
	entities  *entities.Extractor
	generator *generator.Generator
}

// NewParser creates a new NLP parser
func NewParser() nlp.Parser {
	return &parser{
		tokenizer: tokenizer.NewTokenizer(),
		intent:    intent.NewClassifier(),
		entities:  entities.NewExtractor(),
		generator: generator.NewGenerator(),
	}
}

// Parse implements nlp.Parser.Parse
//
// This is the main entry point for NLP processing.
// Pipeline: Input → Tokens → Intent → Entities → Command
func (p *parser) Parse(ctx context.Context, input string) (*nlp.ParseResult, error) {
	return p.ParseWithContext(ctx, input, nil)
}

// ParseWithContext implements nlp.Parser.ParseWithContext
func (p *parser) ParseWithContext(ctx context.Context, input string, sessionCtx *nlp.Context) (*nlp.ParseResult, error) {
	// Step 1: Tokenization
	tokens, err := p.tokenizer.Tokenize(input)
	if err != nil {
		return nil, err
	}

	// Step 2: Intent Classification
	parsedIntent, err := p.intent.Classify(tokens)
	if err != nil {
		return nil, err
	}

	// Store original input
	parsedIntent.OriginalInput = input

	// Step 3: Entity Extraction
	extractedEntities, err := p.entities.Extract(tokens, parsedIntent)
	if err != nil {
		return nil, err
	}

	// Step 4: Resolve ambiguity with context
	if sessionCtx != nil {
		extractedEntities, err = p.entities.ResolveAmbiguity(extractedEntities, sessionCtx)
		if err != nil {
			return nil, err
		}
	}

	// Step 5: Command Generation
	cmd, err := p.generator.Generate(parsedIntent, extractedEntities)
	if err != nil {
		return nil, err
	}

	// Step 6: Validation
	if err := p.generator.ValidateCommand(cmd); err != nil {
		return nil, err
	}

	// Calculate overall confidence
	confidence := p.calculateConfidence(tokens, parsedIntent, cmd)

	result := &nlp.ParseResult{
		Command:    cmd,
		Intent:     parsedIntent,
		Entities:   extractedEntities,
		Confidence: confidence,
	}

	return result, nil
}

// calculateConfidence computes overall parsing confidence
func (p *parser) calculateConfidence(tokens []nlp.Token, intent *nlp.Intent, cmd *nlp.Command) float64 {
	// Start with intent confidence
	confidence := intent.Confidence

	// Reduce confidence if tokens have low confidence (typo corrections)
	minTokenConfidence := 1.0
	for _, token := range tokens {
		if token.Confidence < minTokenConfidence {
			minTokenConfidence = token.Confidence
		}
	}
	confidence *= minTokenConfidence

	// Increase confidence if we successfully generated a valid command
	if len(cmd.Path) >= 2 {
		confidence = (confidence + 0.1)
		if confidence > 1.0 {
			confidence = 1.0
		}
	}

	return confidence
}
