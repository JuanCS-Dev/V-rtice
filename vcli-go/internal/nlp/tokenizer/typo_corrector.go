// Package tokenizer - Typo correction using Levenshtein distance
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package tokenizer

import (
	"math"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// TypoCorrector corrects typos using Levenshtein distance algorithm
type TypoCorrector struct {
	threshold int // Maximum edit distance to consider
}

// NewTypoCorrector creates a new typo corrector
func NewTypoCorrector() *TypoCorrector {
	return &TypoCorrector{
		threshold: 2, // Max 2 character edits
	}
}

// Correct attempts to correct a typo
//
// Uses Levenshtein distance to find closest match in dictionary.
// Returns the corrected word and confidence score (0-1).
func (tc *TypoCorrector) Correct(word string, lang nlp.Language) (string, float64) {
	if len(word) < 3 {
		return word, 1.0 // Too short to correct reliably
	}

	dictionary := tc.getDictionary(lang)

	minDistance := math.MaxInt32
	bestMatch := word

	for dictWord := range dictionary {
		dist := levenshteinDistance(word, dictWord)
		if dist < minDistance && dist <= tc.threshold {
			minDistance = dist
			bestMatch = dictWord
		}
	}

	// Calculate confidence based on edit distance
	confidence := 1.0
	if minDistance > 0 {
		confidence = 1.0 - (float64(minDistance) / float64(len(word)))
	}

	return bestMatch, confidence
}

// getDictionary returns all known words for language
func (tc *TypoCorrector) getDictionary(lang nlp.Language) map[string]bool {
	dict := make(map[string]bool)

	// Merge all dictionaries
	for k := range getVerbDictionary(lang) {
		dict[k] = true
	}
	for k := range getNounDictionary(lang) {
		dict[k] = true
	}
	for k := range getFilterDictionary(lang) {
		dict[k] = true
	}

	return dict
}

// levenshteinDistance calculates edit distance between two strings
//
// This is the core algorithm for typo correction.
// It counts the minimum number of single-character edits (insertions,
// deletions, or substitutions) required to change one word into another.
//
// Example: "posd" → "pods" has distance 2 (swap 's' and 'd')
func levenshteinDistance(s1, s2 string) int {
	if s1 == s2 {
		return 0
	}

	len1 := len(s1)
	len2 := len(s2)

	if len1 == 0 {
		return len2
	}
	if len2 == 0 {
		return len1
	}

	// Create 2D matrix for dynamic programming
	matrix := make([][]int, len1+1)
	for i := range matrix {
		matrix[i] = make([]int, len2+1)
		matrix[i][0] = i
	}
	for j := 0; j <= len2; j++ {
		matrix[0][j] = j
	}

	// Fill matrix using dynamic programming
	for i := 1; i <= len1; i++ {
		for j := 1; j <= len2; j++ {
			cost := 1
			if s1[i-1] == s2[j-1] {
				cost = 0
			}

			matrix[i][j] = min(
				matrix[i-1][j]+1,      // Deletion
				matrix[i][j-1]+1,      // Insertion
				matrix[i-1][j-1]+cost, // Substitution
			)
		}
	}

	return matrix[len1][len2]
}

func min(a, b, c int) int {
	if a < b {
		if a < c {
			return a
		}
		return c
	}
	if b < c {
		return b
	}
	return c
}
