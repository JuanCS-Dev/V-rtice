package palette

import (
	"strings"
)

// FuzzyMatch performs fuzzy matching of query against target
// Returns a score (higher is better) and whether it matches
func FuzzyMatch(query, target string) (int, bool) {
	if query == "" {
		return 0, true // Empty query matches everything
	}

	query = strings.ToLower(query)
	target = strings.ToLower(target)

	// Simple contains check first
	if strings.Contains(target, query) {
		// Exact substring gets high score
		score := len(query) * 10
		// Bonus for matching at start
		if strings.HasPrefix(target, query) {
			score += 50
		}
		return score, true
	}

	// Fuzzy match: each character must appear in order
	queryIdx := 0
	score := 0
	lastMatchIdx := -1

	for targetIdx, targetChar := range target {
		if queryIdx >= len(query) {
			break
		}

		queryChar := rune(query[queryIdx])

		if queryChar == targetChar {
			// Character matches
			queryIdx++
			score += 1

			// Bonus for consecutive matches
			if lastMatchIdx == targetIdx-1 {
				score += 5
			}

			// Bonus for matching after space or dash
			if targetIdx > 0 && (target[targetIdx-1] == ' ' || target[targetIdx-1] == '-') {
				score += 3
			}

			lastMatchIdx = targetIdx
		}
	}

	// All characters must be matched
	if queryIdx == len(query) {
		return score, true
	}

	return 0, false
}

// RankMatches sorts matches by score
func RankMatches(query string, targets []string) []string {
	type match struct {
		target string
		score  int
	}

	matches := make([]match, 0)

	for _, target := range targets {
		score, ok := FuzzyMatch(query, target)
		if ok {
			matches = append(matches, match{target: target, score: score})
		}
	}

	// Sort by score (descending)
	for i := 0; i < len(matches); i++ {
		for j := i + 1; j < len(matches); j++ {
			if matches[j].score > matches[i].score {
				matches[i], matches[j] = matches[j], matches[i]
			}
		}
	}

	result := make([]string, len(matches))
	for i, m := range matches {
		result[i] = m.target
	}

	return result
}

// HighlightMatches returns the target with matched characters highlighted
func HighlightMatches(query, target string) string {
	if query == "" {
		return target
	}

	query = strings.ToLower(query)
	targetLower := strings.ToLower(target)

	// Build result with highlighting
	var result strings.Builder
	queryIdx := 0

	for i, char := range target {
		if queryIdx < len(query) && targetLower[i] == query[queryIdx] {
			// Matched character - will be styled by caller
			result.WriteRune(char)
			queryIdx++
		} else {
			result.WriteRune(char)
		}
	}

	return result.String()
}
