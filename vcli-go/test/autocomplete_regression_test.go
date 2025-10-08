package test

import (
	"strings"
	"testing"

	prompt "github.com/c-bata/go-prompt"
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/shell"
)

// TestAutocompleteEdgeCases tests ALL edge cases for autocomplete
func TestAutocompleteEdgeCases(t *testing.T) {
	// Setup
	rootCmd := &cobra.Command{Use: "vcli"}
	rootCmd.AddCommand(&cobra.Command{Use: "k8s", Short: "Kubernetes"})
	rootCmd.AddCommand(&cobra.Command{Use: "orchestrate", Short: "Orchestrate"})
	rootCmd.AddCommand(&cobra.Command{Use: "data", Short: "Data"})

	completer := shell.NewCompleter(rootCmd)

	testCases := []struct {
		name           string
		input          string
		cursorPos      int
		expectNonEmpty bool
		maxSuggestions int
		description    string
	}{
		// Edge Case 1: Empty input
		{
			name:           "empty input",
			input:          "",
			cursorPos:      0,
			expectNonEmpty: true, // Should show common commands
			maxSuggestions: 10,
			description:    "Empty input should show common commands hint",
		},

		// Edge Case 2: Just slash
		{
			name:           "single slash",
			input:          "/",
			cursorPos:      1,
			expectNonEmpty: true,
			maxSuggestions: 10,
			description:    "Single / should show slash commands",
		},

		// Edge Case 3: Slash with space (impossible but can happen)
		{
			name:           "slash with trailing space",
			input:          "/ ",
			cursorPos:      2,
			expectNonEmpty: false, // Last word empty
			maxSuggestions: 0,
			description:    "Slash with space should return empty",
		},

		// Edge Case 4: Command with trailing space
		{
			name:           "k8s with trailing space",
			input:          "k8s ",
			cursorPos:      4,
			expectNonEmpty: false, // Last word empty after space
			maxSuggestions: 0,
			description:    "Command + space should return empty (prevents sticky bug)",
		},

		// Edge Case 5: Partial command
		{
			name:           "partial k8",
			input:          "k8",
			cursorPos:      2,
			expectNonEmpty: true,
			maxSuggestions: 20,
			description:    "Partial command should show matches",
		},

		// Edge Case 6: Complete command (exact match)
		{
			name:           "exact k8s",
			input:          "k8s",
			cursorPos:      3,
			expectNonEmpty: true,
			maxSuggestions: 20,
			description:    "Exact command should still show suggestions",
		},

		// Edge Case 7: k8s subcommand
		{
			name:           "k8s get",
			input:          "k8s get",
			cursorPos:      7,
			expectNonEmpty: true,
			maxSuggestions: 20,
			description:    "k8s subcommand should filter k8s commands",
		},

		// Edge Case 8: k8s subcommand with space (THE BUG)
		{
			name:           "k8s get with space",
			input:          "k8s get ",
			cursorPos:      8,
			expectNonEmpty: false, // CRITICAL: must be empty
			maxSuggestions: 0,
			description:    "k8s get + space MUST return empty (sticky autocomplete bug)",
		},

		// Edge Case 9: Multiple spaces (user spam)
		{
			name:           "multiple spaces",
			input:          "k8s   ",
			cursorPos:      6,
			expectNonEmpty: false,
			maxSuggestions: 0,
			description:    "Multiple spaces should return empty",
		},

		// Edge Case 10: Tab character (can happen with copy-paste)
		{
			name:           "with tab",
			input:          "k8s\t",
			cursorPos:      4,
			expectNonEmpty: true, // Tab splits to new word
			maxSuggestions: 20,
			description:    "Tab should be treated as word separator",
		},

		// Edge Case 11: Newline (impossible but let's test)
		{
			name:           "with newline",
			input:          "k8s\n",
			cursorPos:      4,
			expectNonEmpty: true,
			maxSuggestions: 20,
			description:    "Newline should be handled gracefully",
		},

		// Edge Case 12: Very long input
		{
			name:           "very long command",
			input:          "k8s get pods deployments services nodes namespaces all",
			cursorPos:      54,
			expectNonEmpty: true,
			maxSuggestions: 20,
			description:    "Long input should still work",
		},

		// Edge Case 13: Flag prefix
		{
			name:           "flag prefix",
			input:          "k8s get pods --",
			cursorPos:      15,
			expectNonEmpty: true,
			maxSuggestions: 15,
			description:    "Flag prefix should show flags",
		},

		// Edge Case 14: Single dash (short flag)
		{
			name:           "single dash",
			input:          "k8s get pods -",
			cursorPos:      14,
			expectNonEmpty: true,
			maxSuggestions: 15,
			description:    "Single dash should show short flags",
		},

		// Edge Case 15: Orchestrate workflow
		{
			name:           "orchestrate partial",
			input:          "orchestrate off",
			cursorPos:      15,
			expectNonEmpty: true,
			maxSuggestions: 15,
			description:    "Orchestrate should filter workflows",
		},

		// Edge Case 16: Orchestrate with space
		{
			name:           "orchestrate with space",
			input:          "orchestrate ",
			cursorPos:      12,
			expectNonEmpty: false, // Last word empty
			maxSuggestions: 0,
			description:    "Orchestrate + space should return empty",
		},

		// Edge Case 17: Unicode characters (can break string splitting)
		{
			name:           "unicode",
			input:          "k8s 你好",
			cursorPos:      7,
			expectNonEmpty: true,
			maxSuggestions: 20,
			description:    "Unicode should be handled",
		},

		// Edge Case 18: Special characters
		{
			name:           "special chars",
			input:          "k8s get @#$",
			cursorPos:      11,
			expectNonEmpty: true, // Will try to match
			maxSuggestions: 20,
			description:    "Special chars should not crash",
		},

		// Edge Case 19: Only spaces
		{
			name:           "only spaces",
			input:          "   ",
			cursorPos:      3,
			expectNonEmpty: true, // Falls back to common commands
			maxSuggestions: 10,
			description:    "Only spaces should show common commands",
		},

		// Edge Case 20: Backspace simulation (cursor in middle)
		{
			name:           "cursor in middle",
			input:          "k8s get",
			cursorPos:      4, // Cursor at "k8s |get"
			expectNonEmpty: true,
			maxSuggestions: 20,
			description:    "Cursor in middle should use text before cursor",
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			// Create Document
			doc := prompt.Document{
				Text:   tc.input,
				CursorPositionCol: tc.cursorPos,
			}

			// Execute completion
			var suggestions []prompt.Suggest
			func() {
				defer func() {
					if r := recover(); r != nil {
						t.Errorf("PANIC on input %q: %v", tc.input, r)
					}
				}()
				suggestions = completer.Complete(doc)
			}()

			// Validate non-empty expectation
			if tc.expectNonEmpty && len(suggestions) == 0 {
				t.Errorf("Expected suggestions but got empty. Input: %q, Cursor: %d",
					tc.input, tc.cursorPos)
			}

			if !tc.expectNonEmpty && len(suggestions) > 0 {
				t.Errorf("Expected empty but got %d suggestions. Input: %q, Cursor: %d",
					len(suggestions), tc.input, tc.cursorPos)
			}

			// Validate max suggestions (prevent rendering bug)
			if len(suggestions) > tc.maxSuggestions {
				t.Errorf("Too many suggestions (%d > %d). This causes rendering bugs! Input: %q",
					len(suggestions), tc.maxSuggestions, tc.input)
			}

			// Validate no nil suggestions
			for i, s := range suggestions {
				if s.Text == "" {
					t.Errorf("Suggestion %d has empty Text. Input: %q", i, tc.input)
				}
			}

			t.Logf("✓ %s: %d suggestions (expected: %v)",
				tc.description, len(suggestions), tc.expectNonEmpty)
		})
	}
}

// TestAutocompleteLimitsAreRespected validates suggestion limits
func TestAutocompleteLimitsAreRespected(t *testing.T) {
	rootCmd := &cobra.Command{Use: "vcli"}
	rootCmd.AddCommand(&cobra.Command{Use: "k8s", Short: "Kubernetes"})

	completer := shell.NewCompleter(rootCmd)

	testCases := []struct {
		input    string
		maxLimit int
	}{
		{"k", 15},         // Main commands
		{"k8s g", 15},     // K8s subcommands
		{"orchestrate o", 10}, // Orchestrate workflows
		{"k8s get pods -", 10},  // Flags
	}

	for _, tc := range testCases {
		doc := prompt.Document{
			Text:              tc.input,
			CursorPositionCol: len(tc.input),
		}

		suggestions := completer.Complete(doc)

		if len(suggestions) > tc.maxLimit {
			t.Errorf("Input %q returned %d suggestions, exceeds limit of %d (causes rendering bugs)",
				tc.input, len(suggestions), tc.maxLimit)
		}

		t.Logf("✓ Input %q: %d suggestions (limit: %d)", tc.input, len(suggestions), tc.maxLimit)
	}
}

// TestAutocompleteNoPanicsOnMalformed tests malformed input doesn't crash
func TestAutocompleteNoPanicsOnMalformed(t *testing.T) {
	rootCmd := &cobra.Command{Use: "vcli"}
	completer := shell.NewCompleter(rootCmd)

	malformedInputs := []string{
		"",
		" ",
		"  ",
		"\t",
		"\n",
		"\r\n",
		"k8s\x00", // Null byte
		"k8s\x01", // Control char
		"k8s" + string(rune(0xFFFD)), // Invalid UTF-8
		"k8s " + string([]byte{0xFF, 0xFE}), // Invalid bytes
		strings.Repeat("a", 10000), // Very long
		"k8s " + strings.Repeat(" ", 100), // Many spaces
	}

	for _, input := range malformedInputs {
		t.Run("malformed_"+input[:min(len(input), 10)], func(t *testing.T) {
			defer func() {
				if r := recover(); r != nil {
					t.Errorf("PANIC on malformed input: %v", r)
				}
			}()

			doc := prompt.Document{
				Text:              input,
				CursorPositionCol: len(input),
			}

			suggestions := completer.Complete(doc)

			t.Logf("✓ Malformed input handled: %d suggestions", len(suggestions))
		})
	}
}

// TestAutocompleteConsistency validates same input gives same output
func TestAutocompleteConsistency(t *testing.T) {
	rootCmd := &cobra.Command{Use: "vcli"}
	rootCmd.AddCommand(&cobra.Command{Use: "k8s", Short: "Kubernetes"})

	completer := shell.NewCompleter(rootCmd)

	testInputs := []string{
		"k8s",
		"k8s get",
		"/help",
		"orchestrate",
	}

	for _, input := range testInputs {
		doc := prompt.Document{
			Text:              input,
			CursorPositionCol: len(input),
		}

		// Run 10 times
		var firstResult []prompt.Suggest
		for i := 0; i < 10; i++ {
			suggestions := completer.Complete(doc)

			if i == 0 {
				firstResult = suggestions
			} else {
				// Validate consistency
				if len(suggestions) != len(firstResult) {
					t.Errorf("Inconsistent results for %q: run 1 had %d, run %d had %d",
						input, len(firstResult), i+1, len(suggestions))
				}
			}
		}

		t.Logf("✓ Input %q consistent across 10 runs: %d suggestions",
			input, len(firstResult))
	}
}

// TestAutocompleteFuzzyMatching validates fuzzy matching works
func TestAutocompleteFuzzyMatching(t *testing.T) {
	rootCmd := &cobra.Command{Use: "vcli"}
	rootCmd.AddCommand(&cobra.Command{Use: "k8s", Short: "Kubernetes"})

	completer := shell.NewCompleter(rootCmd)

	testCases := []struct {
		input          string
		shouldContain  string
		description    string
	}{
		{
			input:         "k8",
			shouldContain: "k8s",
			description:   "Partial match should suggest full command",
		},
		{
			input:         "ks",
			shouldContain: "k8s",
			description:   "Fuzzy match should work (k_s matches k8s)",
		},
	}

	for _, tc := range testCases {
		doc := prompt.Document{
			Text:              tc.input,
			CursorPositionCol: len(tc.input),
		}

		suggestions := completer.Complete(doc)

		found := false
		for _, s := range suggestions {
			if strings.Contains(s.Text, tc.shouldContain) {
				found = true
				break
			}
		}

		if !found {
			t.Errorf("%s: Input %q should suggest %q",
				tc.description, tc.input, tc.shouldContain)
		}

		t.Logf("✓ %s", tc.description)
	}
}

// Helper
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
