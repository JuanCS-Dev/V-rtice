// Package intent - Unit tests
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package intent

import (
	"testing"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

func TestClassifier_QueryIntent(t *testing.T) {
	classifier := NewClassifier()

	tests := []struct {
		name           string
		tokens         []nlp.Token
		expectedCat    nlp.IntentCategory
		expectedVerb   string
		expectedTarget string
		expectedRisk   nlp.RiskLevel
	}{
		{
			name: "show pods",
			tokens: []nlp.Token{
				{Normalized: "show", Type: nlp.TokenTypeVERB},
				{Normalized: "pods", Type: nlp.TokenTypeNOUN},
			},
			expectedCat:    nlp.IntentCategoryQUERY,
			expectedVerb:   "show",
			expectedTarget: "pods",
			expectedRisk:   nlp.RiskLevelLOW,
		},
		{
			name: "list deployments",
			tokens: []nlp.Token{
				{Normalized: "list", Type: nlp.TokenTypeVERB},
				{Normalized: "deployments", Type: nlp.TokenTypeNOUN},
			},
			expectedCat:    nlp.IntentCategoryQUERY,
			expectedVerb:   "list",
			expectedTarget: "deployments",
			expectedRisk:   nlp.RiskLevelLOW,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			intent, err := classifier.Classify(tt.tokens)
			if err != nil {
				t.Fatalf("Classify() error = %v", err)
			}

			if intent.Category != tt.expectedCat {
				t.Errorf("Category = %v, want %v", intent.Category, tt.expectedCat)
			}

			if intent.Verb != tt.expectedVerb {
				t.Errorf("Verb = %v, want %v", intent.Verb, tt.expectedVerb)
			}

			if intent.Target != tt.expectedTarget {
				t.Errorf("Target = %v, want %v", intent.Target, tt.expectedTarget)
			}

			if intent.RiskLevel != tt.expectedRisk {
				t.Errorf("RiskLevel = %v, want %v", intent.RiskLevel, tt.expectedRisk)
			}
		})
	}
}

func TestClassifier_ActionIntent(t *testing.T) {
	classifier := NewClassifier()

	tests := []struct {
		name         string
		tokens       []nlp.Token
		expectedCat  nlp.IntentCategory
		expectedRisk nlp.RiskLevel
	}{
		{
			name: "delete pod",
			tokens: []nlp.Token{
				{Normalized: "delete", Type: nlp.TokenTypeVERB},
				{Normalized: "pods", Type: nlp.TokenTypeNOUN},
			},
			expectedCat:  nlp.IntentCategoryACTION,
			expectedRisk: nlp.RiskLevelHIGH,
		},
		{
			name: "scale deployment",
			tokens: []nlp.Token{
				{Normalized: "scale", Type: nlp.TokenTypeVERB},
				{Normalized: "deployments", Type: nlp.TokenTypeNOUN},
			},
			expectedCat:  nlp.IntentCategoryACTION,
			expectedRisk: nlp.RiskLevelMEDIUM,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			intent, err := classifier.Classify(tt.tokens)
			if err != nil {
				t.Fatalf("Classify() error = %v", err)
			}

			if intent.Category != tt.expectedCat {
				t.Errorf("Category = %v, want %v", intent.Category, tt.expectedCat)
			}

			if intent.RiskLevel != tt.expectedRisk {
				t.Errorf("RiskLevel = %v, want %v", intent.RiskLevel, tt.expectedRisk)
			}
		})
	}
}

func TestClassifier_RiskAssessment(t *testing.T) {
	classifier := NewClassifier()

	tests := []struct {
		name         string
		tokens       []nlp.Token
		expectedRisk nlp.RiskLevel
	}{
		{
			name: "delete in production - CRITICAL",
			tokens: []nlp.Token{
				{Normalized: "delete", Type: nlp.TokenTypeVERB},
				{Normalized: "pods", Type: nlp.TokenTypeNOUN},
				{Normalized: "namespaces", Type: nlp.TokenTypeNOUN},
				{Normalized: "prod", Type: nlp.TokenTypeIDENTIFIER},
			},
			expectedRisk: nlp.RiskLevelCRITICAL,
		},
		{
			name: "scale in production - HIGH",
			tokens: []nlp.Token{
				{Normalized: "scale", Type: nlp.TokenTypeVERB},
				{Normalized: "deployments", Type: nlp.TokenTypeNOUN},
				{Normalized: "namespaces", Type: nlp.TokenTypeNOUN},
				{Normalized: "production", Type: nlp.TokenTypeIDENTIFIER},
			},
			expectedRisk: nlp.RiskLevelHIGH,
		},
		{
			name: "show pods - LOW",
			tokens: []nlp.Token{
				{Normalized: "show", Type: nlp.TokenTypeVERB},
				{Normalized: "pods", Type: nlp.TokenTypeNOUN},
			},
			expectedRisk: nlp.RiskLevelLOW,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			intent, err := classifier.Classify(tt.tokens)
			if err != nil {
				t.Fatalf("Classify() error = %v", err)
			}

			if intent.RiskLevel != tt.expectedRisk {
				t.Errorf("RiskLevel = %v, want %v", intent.RiskLevel, tt.expectedRisk)
			}
		})
	}
}

func TestClassifier_ExtractModifiers(t *testing.T) {
	classifier := NewClassifier()

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
		{Normalized: "error", Type: nlp.TokenTypeFILTER},
		{Normalized: "namespaces", Type: nlp.TokenTypeNOUN},
		{Normalized: "prod", Type: nlp.TokenTypeIDENTIFIER},
	}

	intent, err := classifier.Classify(tokens)
	if err != nil {
		t.Fatalf("Classify() error = %v", err)
	}

	if len(intent.Modifiers) == 0 {
		t.Error("Expected modifiers, got none")
	}

	// Should have filter modifier
	hasFilter := false
	hasNamespace := false
	for _, mod := range intent.Modifiers {
		if mod.Type == "filter" {
			hasFilter = true
		}
		if mod.Type == "namespace" {
			hasNamespace = true
		}
	}

	if !hasFilter {
		t.Error("Expected filter modifier")
	}
	if !hasNamespace {
		t.Error("Expected namespace modifier")
	}
}

func TestClassifier_NoVerb(t *testing.T) {
	classifier := NewClassifier()

	tokens := []nlp.Token{
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
		{Normalized: "nginx", Type: nlp.TokenTypeIDENTIFIER},
	}

	_, err := classifier.Classify(tokens)
	if err == nil {
		t.Error("Expected error for tokens without verb")
	}
}

func TestClassifier_EmptyTokens(t *testing.T) {
	classifier := NewClassifier()

	tokens := []nlp.Token{}

	_, err := classifier.Classify(tokens)
	if err == nil {
		t.Error("Expected error for empty tokens")
	}
}

func BenchmarkClassifier_Classify(b *testing.B) {
	classifier := NewClassifier()
	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
		{Normalized: "error", Type: nlp.TokenTypeFILTER},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = classifier.Classify(tokens)
	}
}
