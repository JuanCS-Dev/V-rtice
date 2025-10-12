// Package tokenizer - Text normalization
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package tokenizer

import (
	"strings"
	"unicode"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// Normalizer handles text normalization
type Normalizer struct{}

// NewNormalizer creates a new normalizer
func NewNormalizer() *Normalizer {
	return &Normalizer{}
}

// Normalize normalizes a word for processing
//
// Normalization steps:
// 1. Convert to lowercase
// 2. Remove accents (for Portuguese)
// 3. Trim punctuation
func (n *Normalizer) Normalize(word string, lang nlp.Language) string {
	// Convert to lowercase
	normalized := strings.ToLower(word)

	// Remove accents for Portuguese
	if lang == nlp.LanguagePTBR {
		normalized = n.removeAccents(normalized)
	}

	// Trim punctuation
	normalized = n.trimPunctuation(normalized)

	return normalized
}

// removeAccents removes Portuguese accents
func (n *Normalizer) removeAccents(s string) string {
	replacements := map[rune]rune{
		'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
		'é': 'e', 'ê': 'e',
		'í': 'i',
		'ó': 'o', 'ô': 'o', 'õ': 'o',
		'ú': 'u', 'ü': 'u',
		'ç': 'c',
	}

	var result strings.Builder
	for _, r := range s {
		if replacement, ok := replacements[r]; ok {
			result.WriteRune(replacement)
		} else {
			result.WriteRune(r)
		}
	}

	return result.String()
}

// trimPunctuation removes leading/trailing punctuation
func (n *Normalizer) trimPunctuation(s string) string {
	return strings.TrimFunc(s, func(r rune) bool {
		return unicode.IsPunct(r)
	})
}
