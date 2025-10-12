// Package tokenizer implements natural language tokenization
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
package tokenizer

import (
	"strings"
	"unicode"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// Tokenizer handles text tokenization with multi-language support
type Tokenizer struct {
	normalizer    *Normalizer
	typoCorrector *TypoCorrector
	stopWords     map[string]bool
}

// NewTokenizer creates a new tokenizer instance
func NewTokenizer() *Tokenizer {
	return &Tokenizer{
		normalizer:    NewNormalizer(),
		typoCorrector: NewTypoCorrector(),
		stopWords:     loadStopWords(),
	}
}

// Tokenize converts natural language input into structured tokens
//
// This is the entry point for NLP processing. It handles:
// - Language detection (PT-BR vs EN)
// - Word splitting and normalization
// - Typo correction using Levenshtein distance
// - Token type classification (VERB, NOUN, etc.)
func (t *Tokenizer) Tokenize(input string) ([]nlp.Token, error) {
	if input == "" {
		return nil, &nlp.ParseError{
			Type:       nlp.ErrorTypeInvalidInput,
			Message:    "Empty input",
			Suggestion: "Try a command like 'show pods' or 'mostra os pods'",
		}
	}

	// Detect language (PT-BR or EN)
	lang := t.detectLanguage(input)

	// Split into raw words
	rawTokens := t.splitWords(input)

	// Process each token
	tokens := make([]nlp.Token, 0, len(rawTokens))
	for i, raw := range rawTokens {
		// Skip stop words (articles, prepositions, etc.)
		if t.stopWords[strings.ToLower(raw)] {
			continue
		}

		// Normalize (lowercase, remove accents)
		normalized := t.normalizer.Normalize(raw, lang)

		// Correct typos using Levenshtein distance
		corrected, confidence := t.typoCorrector.Correct(normalized, lang)

		// Classify token type (VERB, NOUN, NUMBER, etc.)
		tokenType := t.classifyTokenType(corrected, lang)

		// Map to canonical English form if it's a verb/noun
		canonical := t.mapToCanonical(corrected, tokenType, lang)

		token := nlp.Token{
			Raw:        raw,
			Normalized: canonical,
			Type:       tokenType,
			Language:   lang,
			Confidence: confidence,
			Position:   i,
		}

		tokens = append(tokens, token)
	}

	return tokens, nil
}

// splitWords splits input into raw words
func (t *Tokenizer) splitWords(input string) []string {
	words := make([]string, 0)
	var current strings.Builder

	for _, r := range input {
		if unicode.IsSpace(r) {
			if current.Len() > 0 {
				words = append(words, current.String())
				current.Reset()
			}
		} else {
			current.WriteRune(r)
		}
	}

	if current.Len() > 0 {
		words = append(words, current.String())
	}

	return words
}

// detectLanguage detects input language using keyword heuristics
func (t *Tokenizer) detectLanguage(input string) nlp.Language {
	lower := strings.ToLower(input)

	// Portuguese keywords
	ptKeywords := []string{
		"mostra", "lista", "deleta", "escala", "escalona",
		"do", "da", "dos", "das", "no", "na", "nos", "nas",
		"pra", "para", "com", "sem",
	}

	for _, kw := range ptKeywords {
		if strings.Contains(lower, kw) {
			return nlp.LanguagePTBR
		}
	}

	// Default to English
	return nlp.LanguageEN
}

// classifyTokenType determines the semantic type of a token
func (t *Tokenizer) classifyTokenType(word string, lang nlp.Language) nlp.TokenType {
	lower := strings.ToLower(word)

	// Check if it's a number
	if isNumber(lower) {
		return nlp.TokenTypeNUMBER
	}

	// Check verb dictionary
	if t.isVerb(lower, lang) {
		return nlp.TokenTypeVERB
	}

	// Check noun dictionary (K8s resources, etc.)
	if t.isNoun(lower, lang) {
		return nlp.TokenTypeNOUN
	}

	// Check filter keywords
	if t.isFilter(lower, lang) {
		return nlp.TokenTypeFILTER
	}

	// Check prepositions
	if t.isPreposition(lower, lang) {
		return nlp.TokenTypePREP
	}

	// Default to identifier (names, namespaces, etc.)
	return nlp.TokenTypeIDENTIFIER
}

// isNumber checks if string is numeric
func isNumber(s string) bool {
	for _, r := range s {
		if !unicode.IsDigit(r) {
			return false
		}
	}
	return len(s) > 0
}

// isVerb checks if word is a verb
func (t *Tokenizer) isVerb(word string, lang nlp.Language) bool {
	verbs := getVerbDictionary(lang)
	_, ok := verbs[word]
	return ok
}

// isNoun checks if word is a noun
func (t *Tokenizer) isNoun(word string, lang nlp.Language) bool {
	nouns := getNounDictionary(lang)
	_, ok := nouns[word]
	return ok
}

// isFilter checks if word is a filter keyword
func (t *Tokenizer) isFilter(word string, lang nlp.Language) bool {
	filters := getFilterDictionary(lang)
	_, ok := filters[word]
	return ok
}

// isPreposition checks if word is a preposition
func (t *Tokenizer) isPreposition(word string, lang nlp.Language) bool {
	preps := getPrepositionDictionary(lang)
	_, ok := preps[word]
	return ok
}

// mapToCanonical maps word to canonical English form
func (t *Tokenizer) mapToCanonical(word string, tokenType nlp.TokenType, lang nlp.Language) string {
	switch tokenType {
	case nlp.TokenTypeVERB:
		verbs := getVerbDictionary(lang)
		if canonical, ok := verbs[word]; ok {
			return canonical
		}
	case nlp.TokenTypeNOUN:
		nouns := getNounDictionary(lang)
		if canonical, ok := nouns[word]; ok {
			return canonical
		}
	case nlp.TokenTypeFILTER:
		filters := getFilterDictionary(lang)
		if canonical, ok := filters[word]; ok {
			return canonical
		}
	}
	return word
}

// loadStopWords loads stop words for all languages
func loadStopWords() map[string]bool {
	return map[string]bool{
		// Portuguese articles and connectors
		"o": true, "a": true, "os": true, "as": true,
		"de": true, "do": true, "da": true, "dos": true, "das": true,
		"em": true, "no": true, "na": true, "nos": true, "nas": true,
		"um": true, "uma": true, "uns": true, "umas": true,
		"e": true, "ou": true,
		
		// English articles and connectors
		"the": true, "an": true,
		"in": true, "on": true, "at": true,
		"of": true, "to": true, "for": true,
		"and": true, "or": true,
		"with": true, "from": true,
		"me": true, "my": true,
	}
}
