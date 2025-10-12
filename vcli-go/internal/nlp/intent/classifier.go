// Package intent implements intent classification
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This classifier determines user intent from tokenized natural language.
// It uses rule-based pattern matching for high accuracy and explainability.
package intent

import (
	"strings"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// Classifier handles intent classification from tokens
type Classifier struct {
	patterns []Pattern
}

// Pattern represents an intent recognition pattern
type Pattern struct {
	VerbPattern  []string             // Required verb(s)
	NounPattern  []string             // Expected noun types
	Category     nlp.IntentCategory   // Resulting category
	RiskLevel    nlp.RiskLevel        // Security risk level
	Confidence   float64              // Base confidence
}

// NewClassifier creates a new intent classifier
func NewClassifier() *Classifier {
	return &Classifier{
		patterns: buildPatterns(),
	}
}

// Classify determines intent from tokens
//
// Classification strategy:
// 1. Identify primary verb from tokens
// 2. Match verb against known patterns
// 3. Determine target resource
// 4. Assess risk level
// 5. Return structured Intent
func (c *Classifier) Classify(tokens []nlp.Token) (*nlp.Intent, error) {
	if len(tokens) == 0 {
		return nil, &nlp.ParseError{
			Type:    nlp.ErrorTypeClassification,
			Message: "No tokens to classify",
		}
	}

	// Extract primary verb
	verb := c.findVerb(tokens)
	if verb == "" {
		return nil, &nlp.ParseError{
			Type:    nlp.ErrorTypeClassification,
			Message: "No verb found in input",
			Suggestion: "Try starting with an action like 'show', 'list', 'delete', etc.",
		}
	}

	// Extract target resource
	target := c.findTarget(tokens)

	// Match against patterns
	pattern := c.matchPattern(verb, target, tokens)
	if pattern == nil {
		// Default to query if we can't match
		pattern = &Pattern{
			Category:   nlp.IntentCategoryQUERY,
			RiskLevel:  nlp.RiskLevelLOW,
			Confidence: 0.5,
		}
	}

	// Extract modifiers (filters, namespaces, etc.)
	modifiers := c.extractModifiers(tokens)

	// Assess risk level based on verb and target
	risk := c.assessRisk(verb, target, modifiers)

	intent := &nlp.Intent{
		Category:   pattern.Category,
		Verb:       verb,
		Target:     target,
		Modifiers:  modifiers,
		Confidence: pattern.Confidence,
		RiskLevel:  risk,
	}

	return intent, nil
}

// findVerb extracts the primary verb from tokens
func (c *Classifier) findVerb(tokens []nlp.Token) string {
	for _, token := range tokens {
		if token.Type == nlp.TokenTypeVERB {
			return token.Normalized
		}
	}
	return ""
}

// findTarget extracts the primary target resource
func (c *Classifier) findTarget(tokens []nlp.Token) string {
	for _, token := range tokens {
		if token.Type == nlp.TokenTypeNOUN {
			return token.Normalized
		}
	}
	return ""
}

// matchPattern finds the best matching pattern
func (c *Classifier) matchPattern(verb, target string, tokens []nlp.Token) *Pattern {
	var bestMatch *Pattern
	bestScore := 0.0

	for i := range c.patterns {
		pattern := &c.patterns[i]
		score := c.scorePattern(pattern, verb, target, tokens)
		if score > bestScore {
			bestScore = score
			bestMatch = pattern
		}
	}

	return bestMatch
}

// scorePattern calculates how well a pattern matches
func (c *Classifier) scorePattern(pattern *Pattern, verb, target string, tokens []nlp.Token) float64 {
	score := 0.0

	// Check verb match
	for _, v := range pattern.VerbPattern {
		if v == verb {
			score += 0.6
			break
		}
	}

	// Check noun match
	for _, n := range pattern.NounPattern {
		if strings.Contains(target, n) {
			score += 0.4
			break
		}
	}

	return score
}

// extractModifiers extracts command modifiers from tokens
func (c *Classifier) extractModifiers(tokens []nlp.Token) []nlp.Modifier {
	modifiers := make([]nlp.Modifier, 0)

	for i, token := range tokens {
		switch token.Type {
		case nlp.TokenTypeFILTER:
			// Filter conditions (status, error, etc.)
			modifiers = append(modifiers, nlp.Modifier{
				Type:  "filter",
				Key:   "status",
				Value: token.Normalized,
			})

		case nlp.TokenTypeIDENTIFIER:
			// Check if previous token indicates namespace
			if i > 0 && tokens[i-1].Normalized == "namespaces" {
				modifiers = append(modifiers, nlp.Modifier{
					Type:  "namespace",
					Key:   "-n",
					Value: token.Normalized,
				})
			}

		case nlp.TokenTypeNUMBER:
			// Numeric values (replicas, limits, etc.)
			if i > 0 {
				prevToken := tokens[i-1].Normalized
				if prevToken == "to" || prevToken == "pra" {
					modifiers = append(modifiers, nlp.Modifier{
						Type:  "count",
						Key:   "--replicas",
						Value: token.Normalized,
					})
				}
			}
		}
	}

	return modifiers
}

// assessRisk determines security risk level
func (c *Classifier) assessRisk(verb, target string, modifiers []nlp.Modifier) nlp.RiskLevel {
	// CRITICAL: Destructive actions with broad scope
	if verb == "delete" {
		// Check for --all flag or multiple resources
		for _, mod := range modifiers {
			if mod.Key == "--all" || mod.Value == "all" {
				return nlp.RiskLevelCRITICAL
			}
		}
		// Check for production namespace
		for _, mod := range modifiers {
			if mod.Type == "namespace" && (mod.Value == "production" || mod.Value == "prod") {
				return nlp.RiskLevelCRITICAL
			}
		}
		return nlp.RiskLevelHIGH
	}

	// HIGH: Significant state changes in production
	if verb == "scale" || verb == "apply" || verb == "patch" {
		for _, mod := range modifiers {
			if mod.Type == "namespace" && (mod.Value == "production" || mod.Value == "prod") {
				return nlp.RiskLevelHIGH
			}
		}
		return nlp.RiskLevelMEDIUM
	}

	// MEDIUM: Reversible changes
	if verb == "create" || verb == "update" {
		return nlp.RiskLevelMEDIUM
	}

	// LOW: Read-only operations
	if verb == "show" || verb == "list" || verb == "get" || verb == "describe" {
		return nlp.RiskLevelLOW
	}

	// Default to MEDIUM for unknown
	return nlp.RiskLevelMEDIUM
}

// GetAlternatives returns alternative intent interpretations
func (c *Classifier) GetAlternatives(tokens []nlp.Token) ([]*nlp.Intent, error) {
	// For ambiguous cases, provide multiple interpretations
	alternatives := make([]*nlp.Intent, 0)

	verb := c.findVerb(tokens)
	if verb == "" {
		return alternatives, nil
	}

	// Try different target interpretations
	for _, token := range tokens {
		if token.Type == nlp.TokenTypeNOUN {
			intent, err := c.Classify(tokens)
			if err == nil {
				alternatives = append(alternatives, intent)
			}
		}
	}

	return alternatives, nil
}

// buildPatterns creates the pattern database
func buildPatterns() []Pattern {
	return []Pattern{
		// QUERY patterns (read-only, LOW risk)
		{
			VerbPattern:  []string{"show", "list", "get", "describe"},
			NounPattern:  []string{"pods", "deployments", "services", "nodes"},
			Category:     nlp.IntentCategoryQUERY,
			RiskLevel:    nlp.RiskLevelLOW,
			Confidence:   0.95,
		},

		// ACTION patterns (write operations)
		{
			VerbPattern:  []string{"delete", "remove"},
			NounPattern:  []string{"pod", "deployment", "service"},
			Category:     nlp.IntentCategoryACTION,
			RiskLevel:    nlp.RiskLevelHIGH,
			Confidence:   0.90,
		},
		{
			VerbPattern:  []string{"scale"},
			NounPattern:  []string{"deployment", "statefulset", "replicaset"},
			Category:     nlp.IntentCategoryACTION,
			RiskLevel:    nlp.RiskLevelMEDIUM,
			Confidence:   0.90,
		},
		{
			VerbPattern:  []string{"create", "apply"},
			NounPattern:  []string{},
			Category:     nlp.IntentCategoryACTION,
			RiskLevel:    nlp.RiskLevelMEDIUM,
			Confidence:   0.85,
		},

		// INVESTIGATE patterns
		{
			VerbPattern:  []string{"investigate", "analyze", "debug"},
			NounPattern:  []string{},
			Category:     nlp.IntentCategoryINVESTIGATE,
			RiskLevel:    nlp.RiskLevelLOW,
			Confidence:   0.95,
		},

		// ORCHESTRATE patterns
		{
			VerbPattern:  []string{"execute", "run", "start"},
			NounPattern:  []string{"workflow", "offensive", "defensive"},
			Category:     nlp.IntentCategoryORCHESTRATE,
			RiskLevel:    nlp.RiskLevelMEDIUM,
			Confidence:   0.90,
		},

		// HELP patterns
		{
			VerbPattern:  []string{"help", "explain"},
			NounPattern:  []string{},
			Category:     nlp.IntentCategoryHELP,
			RiskLevel:    nlp.RiskLevelLOW,
			Confidence:   1.0,
		},
	}
}
