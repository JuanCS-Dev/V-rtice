// Package tokenizer - Unit tests
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package tokenizer

import (
	"testing"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

func TestTokenizer_BasicPortuguese(t *testing.T) {
	tokenizer := NewTokenizer()

	tests := []struct {
		name     string
		input    string
		expected []struct {
			normalized string
			tokenType  nlp.TokenType
		}
	}{
		{
			name:  "simple query",
			input: "mostra os pods",
			expected: []struct {
				normalized string
				tokenType  nlp.TokenType
			}{
				{"show", nlp.TokenTypeVERB},
				{"pods", nlp.TokenTypeNOUN},
			},
		},
		{
			name:  "with namespace",
			input: "lista deployments do namespace prod",
			expected: []struct {
				normalized string
				tokenType  nlp.TokenType
			}{
				{"list", nlp.TokenTypeVERB},
				{"deployments", nlp.TokenTypeNOUN},
				{"namespaces", nlp.TokenTypeNOUN},
				{"prod", nlp.TokenTypeIDENTIFIER},
			},
		},
		{
			name:  "scale command",
			input: "escala nginx pra 5",
			expected: []struct {
				normalized string
				tokenType  nlp.TokenType
			}{
				{"scale", nlp.TokenTypeVERB},
				{"nginx", nlp.TokenTypeIDENTIFIER},
				{"5", nlp.TokenTypeNUMBER},
			},
		},
		{
			name:  "with filter",
			input: "pods com problema",
			expected: []struct {
				normalized string
				tokenType  nlp.TokenType
			}{
				{"pods", nlp.TokenTypeNOUN},
				{"error", nlp.TokenTypeFILTER},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tokens, err := tokenizer.Tokenize(tt.input)
			if err != nil {
				t.Fatalf("Tokenize() error = %v", err)
			}

			if len(tokens) != len(tt.expected) {
				t.Errorf("Tokenize() got %d tokens, want %d", len(tokens), len(tt.expected))
			}

			for i, exp := range tt.expected {
				if i >= len(tokens) {
					break
				}
				if tokens[i].Normalized != exp.normalized {
					t.Errorf("Token[%d].Normalized = %q, want %q", i, tokens[i].Normalized, exp.normalized)
				}
				if tokens[i].Type != exp.tokenType {
					t.Errorf("Token[%d].Type = %q, want %q", i, tokens[i].Type, exp.tokenType)
				}
			}
		})
	}
}

func TestTokenizer_EnglishInput(t *testing.T) {
	tokenizer := NewTokenizer()

	input := "show me the pods"
	tokens, err := tokenizer.Tokenize(input)

	if err != nil {
		t.Fatalf("Tokenize() error = %v", err)
	}

	if len(tokens) < 2 {
		t.Errorf("Tokenize() got %d tokens, want at least 2", len(tokens))
	}

	if tokens[0].Normalized != "show" {
		t.Errorf("Token[0].Normalized = %q, want %q", tokens[0].Normalized, "show")
	}

	if tokens[0].Type != nlp.TokenTypeVERB {
		t.Errorf("Token[0].Type = %q, want %q", tokens[0].Type, nlp.TokenTypeVERB)
	}
}

func TestTokenizer_EmptyInput(t *testing.T) {
	tokenizer := NewTokenizer()

	_, err := tokenizer.Tokenize("")

	if err == nil {
		t.Error("Tokenize(\"\") should return error")
	}
}

func TestTypoCorrector_BasicCorrections(t *testing.T) {
	corrector := NewTypoCorrector()

	tests := []struct {
		input    string
		expected string
		lang     nlp.Language
	}{
		{"posd", "pods", nlp.LanguageEN},
		{"deploiment", "deployment", nlp.LanguageEN},
		{"esacala", "escala", nlp.LanguagePTBR},
		{"pods", "pods", nlp.LanguageEN}, // No correction needed
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			corrected, confidence := corrector.Correct(tt.input, tt.lang)

			if corrected != tt.expected {
				t.Errorf("Correct(%q) = %q, want %q", tt.input, corrected, tt.expected)
			}

			if confidence < 0 || confidence > 1 {
				t.Errorf("Confidence = %f, want between 0 and 1", confidence)
			}

			// Perfect match should have confidence 1.0
			if tt.input == tt.expected && confidence != 1.0 {
				t.Errorf("Perfect match confidence = %f, want 1.0", confidence)
			}
		})
	}
}

func TestLevenshteinDistance(t *testing.T) {
	tests := []struct {
		s1       string
		s2       string
		expected int
	}{
		{"", "", 0},
		{"a", "", 1},
		{"", "a", 1},
		{"abc", "abc", 0},
		{"abc", "abd", 1},
		{"abc", "ac", 1},
		{"pods", "posd", 2},
		{"kitten", "sitting", 3},
	}

	for _, tt := range tests {
		t.Run(tt.s1+"_"+tt.s2, func(t *testing.T) {
			dist := levenshteinDistance(tt.s1, tt.s2)
			if dist != tt.expected {
				t.Errorf("levenshteinDistance(%q, %q) = %d, want %d", tt.s1, tt.s2, dist, tt.expected)
			}
		})
	}
}

func TestNormalizer_RemoveAccents(t *testing.T) {
	normalizer := NewNormalizer()

	tests := []struct {
		input    string
		expected string
	}{
		{"café", "cafe"},
		{"ação", "acao"},
		{"pão", "pao"},
		{"São Paulo", "sao paulo"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result := normalizer.Normalize(tt.input, nlp.LanguagePTBR)
			if result != tt.expected {
				t.Errorf("Normalize(%q) = %q, want %q", tt.input, result, tt.expected)
			}
		})
	}
}

func BenchmarkTokenizer_Tokenize(b *testing.B) {
	tokenizer := NewTokenizer()
	input := "mostra os pods com problema no namespace de producao"

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = tokenizer.Tokenize(input)
	}
}

func BenchmarkLevenshteinDistance(b *testing.B) {
	s1 := "kubernetes"
	s2 := "kubernets"

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = levenshteinDistance(s1, s2)
	}
}
