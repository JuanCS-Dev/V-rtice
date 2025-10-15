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
			input: "escala nginx 5",
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
			input: "pods problema",
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
				t.Logf("Got tokens:")
				for i, tok := range tokens {
					t.Logf("  [%d] %q (%v)", i, tok.Normalized, tok.Type)
				}
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
		{"poods", "pods", nlp.LanguageEN}, // Changed from "posd" which is ambiguous
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

// NEW TESTS FOR 100% COVERAGE

// TestDictionaries_UnknownLanguage tests default cases in dictionary functions
func TestDictionaries_UnknownLanguage(t *testing.T) {
	unknownLang := nlp.Language("unknown")

	verbDict := getVerbDictionary(unknownLang)
	if len(verbDict) != 0 {
		t.Errorf("getVerbDictionary(unknown) should return empty map, got %d entries", len(verbDict))
	}

	nounDict := getNounDictionary(unknownLang)
	if len(nounDict) != 0 {
		t.Errorf("getNounDictionary(unknown) should return empty map, got %d entries", len(nounDict))
	}

	filterDict := getFilterDictionary(unknownLang)
	if len(filterDict) != 0 {
		t.Errorf("getFilterDictionary(unknown) should return empty map, got %d entries", len(filterDict))
	}

	prepDict := getPrepositionDictionary(unknownLang)
	if len(prepDict) != 0 {
		t.Errorf("getPrepositionDictionary(unknown) should return empty map, got %d entries", len(prepDict))
	}
}

// TestTokenizer_ClassifyUnknownToken tests classifyTokenType default case
func TestTokenizer_ClassifyUnknownToken(t *testing.T) {
	tokenizer := NewTokenizer()

	// Token that's not in any dictionary - should be classified as IDENTIFIER
	input := "xyz123abc"
	tokens, err := tokenizer.Tokenize(input)

	if err != nil {
		t.Fatalf("Tokenize() error = %v", err)
	}

	if len(tokens) == 0 {
		t.Fatal("Expected at least one token")
	}

	// Unknown word should be classified as IDENTIFIER
	if tokens[0].Type != nlp.TokenTypeIDENTIFIER {
		t.Errorf("Unknown token type = %q, want %q", tokens[0].Type, nlp.TokenTypeIDENTIFIER)
	}
}

// TestTypoCorrector_NoCorrection tests typo corrector when no correction needed
func TestTypoCorrector_NoCorrection(t *testing.T) {
	corrector := NewTypoCorrector()

	// Test exact match (no correction needed) - already covered but let's be explicit
	word := "pods"
	corrected, confidence := corrector.Correct(word, nlp.LanguageEN)

	if corrected != word {
		t.Errorf("Correct(%q) = %q, want %q (no correction)", word, corrected, word)
	}

	if confidence != 1.0 {
		t.Errorf("Confidence for exact match = %f, want 1.0", confidence)
	}
}

// TestTypoCorrector_UnknownLanguage tests typo corrector with unsupported language
func TestTypoCorrector_UnknownLanguage(t *testing.T) {
	corrector := NewTypoCorrector()

	unknownLang := nlp.Language("unknown")
	word := "poods"

	// Should return original word when language dictionary is empty
	corrected, confidence := corrector.Correct(word, unknownLang)

	if corrected != word {
		t.Errorf("Correct(%q, unknown) = %q, want %q (unchanged)", word, corrected, word)
	}

	if confidence != 1.0 {
		t.Errorf("Confidence for unknown language = %f, want 1.0", confidence)
	}
}

// TestTypoCorrector_ShortWord tests typo corrector with word < 3 characters (line 30-32)
func TestTypoCorrector_ShortWord(t *testing.T) {
	corrector := NewTypoCorrector()

	// Words shorter than 3 chars should be returned unchanged
	shortWords := []string{"a", "ab", ""}

	for _, word := range shortWords {
		corrected, confidence := corrector.Correct(word, nlp.LanguageEN)

		if corrected != word {
			t.Errorf("Correct(%q) = %q, want %q (short word unchanged)", word, corrected, word)
		}

		if confidence != 1.0 {
			t.Errorf("Confidence for short word %q = %f, want 1.0", word, confidence)
		}
	}
}

// TestTypoCorrector_ConfidenceCalculation tests confidence scoring (line 56-60)
func TestTypoCorrector_ConfidenceCalculation(t *testing.T) {
	corrector := NewTypoCorrector()

	// Test a typo that should be corrected with confidence < 1.0
	// "poods" is close to "pods" but should have confidence based on edit distance
	word := "poods"
	corrected, confidence := corrector.Correct(word, nlp.LanguageEN)

	// Should be corrected to "pods"
	if corrected != "pods" {
		t.Errorf("Correct(%q) = %q, want %q", word, corrected, "pods")
	}

	// Confidence should be < 1.0 (since there was an edit)
	if confidence >= 1.0 || confidence <= 0.0 {
		t.Errorf("Confidence = %f, want between 0 and 1 (exclusive)", confidence)
	}
}

// TestTokenizer_PrepositionClassification tests classifyTokenType with prepositions (line 156-158)
func TestTokenizer_PrepositionClassification(t *testing.T) {
	tokenizer := NewTokenizer()

	// Test Portuguese preposition "para" which is NOT a stop word
	input := "para production"
	tokens, err := tokenizer.Tokenize(input)

	if err != nil {
		t.Fatalf("Tokenize() error = %v", err)
	}

	// Should get at least "para" as a preposition
	found := false
	for _, tok := range tokens {
		if tok.Type == nlp.TokenTypePREP {
			found = true
			break
		}
	}

	if !found {
		t.Error("Expected to find a preposition token in 'para production'")
	}

	// Test classifyTokenType directly to ensure PREP classification works
	tokenType := tokenizer.classifyTokenType("with", nlp.LanguageEN)

	if tokenType != nlp.TokenTypePREP {
		t.Errorf("classifyTokenType('with', EN) = %q, want %q", tokenType, nlp.TokenTypePREP)
	}

	// Test Portuguese preposition
	tokenType2 := tokenizer.classifyTokenType("para", nlp.LanguagePTBR)

	if tokenType2 != nlp.TokenTypePREP {
		t.Errorf("classifyTokenType('para', PT-BR) = %q, want %q", tokenType2, nlp.TokenTypePREP)
	}
}

// TestTypoCorrector_NoMatchBeyondThreshold tests when no correction is found
func TestTypoCorrector_NoMatchBeyondThreshold(t *testing.T) {
	corrector := NewTypoCorrector()

	// Test a word that's too different from anything in dictionary
	// Should return original word with confidence 1.0 (no correction applied)
	word := "xyzabc123"
	corrected, confidence := corrector.Correct(word, nlp.LanguageEN)

	if corrected != word {
		t.Errorf("Correct(%q) = %q, want %q (no match beyond threshold)", word, corrected, word)
	}

	if confidence != 1.0 {
		t.Errorf("Confidence for no match = %f, want 1.0", confidence)
	}
}
