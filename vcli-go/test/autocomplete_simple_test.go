package test

import (
	"strings"
	"testing"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/shell"
)

// TestAutocompleteRegressionCRITICAL tests the critical sticky autocomplete bug
func TestAutocompleteRegressionCRITICAL(t *testing.T) {
	rootCmd := &cobra.Command{Use: "vcli"}
	rootCmd.AddCommand(&cobra.Command{Use: "k8s", Short: "Kubernetes"})

	completer := shell.NewCompleter(rootCmd)

	criticalCases := []struct {
		name        string
		input       string
		expectEmpty bool
		reason      string
	}{
		{
			name:        "CRITICAL: k8s with trailing space",
			input:       "k8s ",
			expectEmpty: true,
			reason:      "Trailing space causes sticky autocomplete bug",
		},
		{
			name:        "CRITICAL: k8s get with trailing space",
			input:       "k8s get ",
			expectEmpty: true,
			reason:      "Subcommand + space causes rendering artifacts",
		},
		{
			name:        "CRITICAL: multiple trailing spaces",
			input:       "k8s   ",
			expectEmpty: true,
			reason:      "Multiple spaces should return empty",
		},
		{
			name:        "CRITICAL: orchestrate with space",
			input:       "orchestrate ",
			expectEmpty: true,
			reason:      "Orchestrate + space bug",
		},
		{
			name:        "OK: k8s without space",
			input:       "k8s",
			expectEmpty: false,
			reason:      "Without space should show suggestions",
		},
		{
			name:        "OK: k8s get without space",
			input:       "k8s get",
			expectEmpty: false,
			reason:      "Partial subcommand should show suggestions",
		},
	}

	for _, tc := range criticalCases {
		t.Run(tc.name, func(t *testing.T) {
			// Use CompleteText() directly - it's the pure logic without go-prompt dependency
			suggestions := completer.CompleteText(tc.input)

			isEmpty := len(suggestions) == 0

			if tc.expectEmpty && !isEmpty {
				t.Errorf("CRITICAL BUG: %s\nInput: %q\nExpected: empty\nGot: %d suggestions\nReason: %s",
					tc.name, tc.input, len(suggestions), tc.reason)
				t.Log("First 5 suggestions:")
				for i := 0; i < min(5, len(suggestions)); i++ {
					t.Logf("  - %s", suggestions[i].Text)
				}
			}

			if !tc.expectEmpty && isEmpty {
				t.Errorf("Input %q should return suggestions but got empty", tc.input)
			}

			t.Logf("✓ %s: %d suggestions (expected empty: %v)",
				tc.reason, len(suggestions), tc.expectEmpty)
		})
	}
}

// TestAutocompleteLimits ensures we never exceed safe suggestion count
func TestAutocompleteLimits(t *testing.T) {
	rootCmd := &cobra.Command{Use: "vcli"}
	rootCmd.AddCommand(&cobra.Command{Use: "k8s", Short: "Kubernetes"})

	completer := shell.NewCompleter(rootCmd)

	const SAFE_MAX = 20 // Never exceed this to prevent rendering bugs

	testCases := []string{
		"k",
		"k8s",
		"k8s g",
		"k8s get p",
		"orchestrate",
		"orchestrate o",
		"/",
		"/h",
		"-",
		"--",
	}

	for _, input := range testCases {
		suggestions := completer.CompleteText(input)

		if len(suggestions) > SAFE_MAX {
			t.Errorf("RENDERING BUG RISK: Input %q returned %d suggestions (max safe: %d)",
				input, len(suggestions), SAFE_MAX)
		}

		t.Logf("✓ Input %q: %d suggestions (safe)", input, len(suggestions))
	}
}

// TestAutocompleteNoPanics ensures no crashes on any input
func TestAutocompleteNoPanics(t *testing.T) {
	rootCmd := &cobra.Command{Use: "vcli"}
	completer := shell.NewCompleter(rootCmd)

	dangerousInputs := []string{
		"",
		" ",
		"  ",
		"\t",
		"\n",
		"\r\n",
		strings.Repeat("a", 10000),
		"k8s " + strings.Repeat(" ", 100),
		"你好世界",
		"k8s @#$%^&*()",
		"/////",
		"---",
		"\\\\\\",
	}

	for _, input := range dangerousInputs {
		t.Run("input_"+input[:min(len(input), 20)], func(t *testing.T) {
			defer func() {
				if r := recover(); r != nil {
					t.Errorf("PANIC on input %q: %v", input, r)
				}
			}()

			suggestions := completer.CompleteText(input)

			t.Logf("✓ Input handled safely: %d suggestions", len(suggestions))
		})
	}
}

// TestAutocompleteConsistency validates deterministic behavior
func TestAutocompleteConsistency(t *testing.T) {
	rootCmd := &cobra.Command{Use: "vcli"}
	rootCmd.AddCommand(&cobra.Command{Use: "k8s", Short: "Kubernetes"})

	completer := shell.NewCompleter(rootCmd)

	testInputs := []string{
		"k8s",
		"k8s get",
		"/help",
	}

	for _, input := range testInputs {
		var firstCount int
		for i := 0; i < 5; i++ {
			suggestions := completer.CompleteText(input)

			if i == 0 {
				firstCount = len(suggestions)
			} else if len(suggestions) != firstCount {
				t.Errorf("Inconsistent results for %q: first run %d, run %d got %d",
					input, firstCount, i+1, len(suggestions))
			}
		}

		t.Logf("✓ Input %q consistent: %d suggestions", input, firstCount)
	}
}

// TestSlashCommandsWork validates slash commands trigger
func TestSlashCommandsWork(t *testing.T) {
	rootCmd := &cobra.Command{Use: "vcli"}
	completer := shell.NewCompleter(rootCmd)

	suggestions := completer.CompleteText("/")

	if len(suggestions) == 0 {
		t.Error("Slash / should show slash commands")
	}

	// All should start with /
	for i, s := range suggestions {
		if !strings.HasPrefix(s.Text, "/") {
			t.Errorf("Suggestion %d doesn't start with /: %q", i, s.Text)
		}
	}

	t.Logf("✓ Slash commands work: %d commands", len(suggestions))
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
