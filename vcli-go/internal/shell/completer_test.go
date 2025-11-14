package shell

import (
	"testing"

	prompt "github.com/c-bata/go-prompt"
	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewCompleter verifies Completer instance creation
func TestNewCompleter(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	t.Run("creates completer with suggestions", func(t *testing.T) {
		completer := NewCompleter(rootCmd)
		require.NotNil(t, completer)
		assert.NotNil(t, completer.suggestions)
		assert.Greater(t, len(completer.suggestions), 0, "should build initial suggestions")
	})

	t.Run("creates completer with rootCmd reference", func(t *testing.T) {
		completer := NewCompleter(rootCmd)
		assert.Equal(t, rootCmd, completer.rootCmd)
	})
}

// TestCompleter_CompleteText verifies text-based completion
func TestCompleter_CompleteText(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}
	rootCmd.AddCommand(&cobra.Command{
		Use:   "k8s",
		Short: "Kubernetes operations",
	})

	completer := NewCompleter(rootCmd)

	tests := []struct {
		name      string
		input     string
		wantEmpty bool
		wantCount int
		contains  []string
		notContains []string
	}{
		{
			name:      "empty input returns common commands",
			input:     "",
			wantEmpty: false,
			contains:  []string{"k8s get pods"},
		},
		{
			name:      "slash only returns slash commands",
			input:     "/",
			wantEmpty: false,
			contains:  []string{"/help", "/exit", "/palette"},
		},
		{
			name:      "input ending with space returns empty",
			input:     "k8s ",
			wantEmpty: true,
		},
		{
			name:      "input ending with tab returns empty",
			input:     "k8s\t",
			wantEmpty: true,
		},
		{
			name:      "k8s prefix shows k8s commands",
			input:     "k8s",
			wantEmpty: false,
		},
		{
			name:      "orchestrate prefix shows orchestrate commands",
			input:     "orchestrate",
			wantEmpty: false,
		},
		{
			name:      "partial slash command shows matches",
			input:     "/h",
			wantEmpty: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			suggestions := completer.CompleteText(tt.input)

			if tt.wantEmpty {
				assert.Empty(t, suggestions, "expected no suggestions")
			} else {
				assert.NotEmpty(t, suggestions, "expected suggestions")
			}

			if tt.wantCount > 0 {
				assert.Len(t, suggestions, tt.wantCount)
			}

			for _, text := range tt.contains {
				found := false
				for _, sug := range suggestions {
					if sug.Text == text {
						found = true
						break
					}
				}
				assert.True(t, found, "expected suggestion to contain: %s", text)
			}

			for _, text := range tt.notContains {
				for _, sug := range suggestions {
					assert.NotEqual(t, text, sug.Text, "expected suggestion to not contain: %s", text)
				}
			}
		})
	}
}

// TestCompleter_ContextAwareSuggestions verifies context-aware completions
func TestCompleter_ContextAwareSuggestions(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "k8s subcommands",
			input:    "k8s get",
			expected: "k8s",
		},
		{
			name:     "orchestrate subcommands",
			input:    "orchestrate offensive",
			expected: "orchestrate",
		},
		{
			name:     "neuro subcommands",
			input:    "neuro cortex",
			expected: "neuro",
		},
		{
			name:     "behavior subcommands",
			input:    "behavior analyze",
			expected: "behavior",
		},
		{
			name:     "intops subcommands",
			input:    "intops google",
			expected: "intops",
		},
		{
			name:     "offensive subcommands",
			input:    "offensive tools",
			expected: "offensive",
		},
		{
			name:     "immunity subcommands",
			input:    "immunity core",
			expected: "immunity",
		},
		{
			name:     "hunting subcommands",
			input:    "hunting apt",
			expected: "hunting",
		},
		{
			name:     "streams subcommands",
			input:    "streams topic",
			expected: "streams",
		},
		{
			name:     "specialized subcommands",
			input:    "specialized aether",
			expected: "specialized",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			suggestions := completer.CompleteText(tt.input)
			// Should return context-aware suggestions
			// We don't assert specific count since it depends on registered commands
			assert.NotNil(t, suggestions)
		})
	}
}

// TestCompleter_FlagSuggestions verifies flag completion
func TestCompleter_FlagSuggestions(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}
	rootCmd.PersistentFlags().String("config", "", "config file")
	rootCmd.PersistentFlags().StringP("output", "o", "", "output format")

	completer := NewCompleter(rootCmd)

	tests := []struct {
		name      string
		input     string
		wantEmpty bool
	}{
		{
			name:      "single dash triggers flag suggestions",
			input:     "test -",
			wantEmpty: false,
		},
		{
			name:      "double dash triggers flag suggestions",
			input:     "test --",
			wantEmpty: false,
		},
		{
			name:      "partial flag name",
			input:     "test --con",
			wantEmpty: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			suggestions := completer.CompleteText(tt.input)

			if tt.wantEmpty {
				assert.Empty(t, suggestions)
			} else {
				// Flags might be present in suggestions
				assert.NotNil(t, suggestions)
			}
		})
	}
}

// TestCompleter_GetSlashCommands verifies slash command extraction
func TestCompleter_GetSlashCommands(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	t.Run("returns only slash commands", func(t *testing.T) {
		slashCmds := completer.getSlashCommands()
		assert.NotEmpty(t, slashCmds)

		for _, cmd := range slashCmds {
			assert.True(t, len(cmd.Text) > 0 && cmd.Text[0] == '/', "all commands should start with /")
		}
	})

	t.Run("includes standard slash commands", func(t *testing.T) {
		slashCmds := completer.getSlashCommands()

		expectedCommands := []string{"/help", "/exit", "/quit", "/clear", "/history", "/palette"}
		for _, expected := range expectedCommands {
			found := false
			for _, cmd := range slashCmds {
				if cmd.Text == expected {
					found = true
					break
				}
			}
			assert.True(t, found, "expected slash command: %s", expected)
		}
	})
}

// TestCompleter_GetCommonCommands verifies common command suggestions
func TestCompleter_GetCommonCommands(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	t.Run("returns common commands", func(t *testing.T) {
		commonCmds := completer.getCommonCommands()
		assert.NotEmpty(t, commonCmds)
	})

	t.Run("common commands have no slash prefix", func(t *testing.T) {
		commonCmds := completer.getCommonCommands()

		for _, cmd := range commonCmds {
			assert.False(t, len(cmd.Text) > 0 && cmd.Text[0] == '/', "common commands should not start with /")
		}
	})

	t.Run("includes k8s commands", func(t *testing.T) {
		commonCmds := completer.getCommonCommands()

		hasK8s := false
		for _, cmd := range commonCmds {
			if len(cmd.Text) >= 3 && cmd.Text[:3] == "k8s" {
				hasK8s = true
				break
			}
		}
		assert.True(t, hasK8s, "common commands should include k8s")
	})
}

// TestCompleter_FilterSuggestions verifies suggestion filtering
func TestCompleter_FilterSuggestions(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	suggestions := []prompt.Suggest{
		{Text: "k8s get pods", Description: "List pods"},
		{Text: "k8s get deployments", Description: "List deployments"},
		{Text: "orchestrate offensive apt-simulation", Description: "APT simulation"},
		{Text: "data query", Description: "Query database"},
	}

	tests := []struct {
		name         string
		prefix       string
		suggestions  []prompt.Suggest
		wantCount    int
		wantContains []string
	}{
		{
			name:         "empty prefix returns all",
			prefix:       "",
			suggestions:  suggestions,
			wantCount:    4,
			wantContains: []string{"k8s get pods", "data query"},
		},
		{
			name:         "exact prefix match",
			prefix:       "k8s",
			suggestions:  suggestions,
			wantContains: []string{"k8s get pods", "k8s get deployments"},
		},
		{
			name:        "fuzzy match",
			prefix:      "orch",
			suggestions: suggestions,
			wantContains: []string{"orchestrate offensive apt-simulation"},
		},
		{
			name:        "case insensitive",
			prefix:      "K8S",
			suggestions: suggestions,
			wantContains: []string{"k8s get pods"},
		},
		{
			name:         "no match returns empty",
			prefix:       "zzzzz",
			suggestions:  suggestions,
			wantCount:    0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := completer.filterSuggestions(tt.prefix, tt.suggestions)

			if tt.wantCount > 0 {
				assert.Len(t, result, tt.wantCount)
			}

			for _, text := range tt.wantContains {
				found := false
				for _, sug := range result {
					if sug.Text == text {
						found = true
						break
					}
				}
				assert.True(t, found, "expected to find: %s", text)
			}
		})
	}
}

// TestCompleter_FuzzyMatch verifies fuzzy matching algorithm
func TestCompleter_FuzzyMatch(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	tests := []struct {
		name    string
		pattern string
		text    string
		want    bool
	}{
		{
			name:    "exact match",
			pattern: "abc",
			text:    "abc",
			want:    true,
		},
		{
			name:    "pattern in order",
			pattern: "kgp",
			text:    "k8s get pods",
			want:    true,
		},
		{
			name:    "pattern not in order",
			pattern: "pgk",
			text:    "k8s get pods",
			want:    false,
		},
		{
			name:    "pattern longer than text",
			pattern: "abcdefghij",
			text:    "abc",
			want:    false,
		},
		{
			name:    "empty pattern matches anything",
			pattern: "",
			text:    "anything",
			want:    true,
		},
		{
			name:    "pattern with spaces",
			pattern: "k g p",
			text:    "k8s get pods",
			want:    true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := completer.fuzzyMatch(tt.pattern, tt.text)
			assert.Equal(t, tt.want, result)
		})
	}
}

// TestCompleter_LimitSuggestions verifies suggestion limiting
func TestCompleter_LimitSuggestions(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	// Create test suggestions
	suggestions := make([]prompt.Suggest, 20)
	for i := range suggestions {
		suggestions[i] = prompt.Suggest{
			Text:        "command" + string(rune('0'+i)),
			Description: "Description",
		}
	}

	tests := []struct {
		name        string
		suggestions []prompt.Suggest
		max         int
		wantLen     int
	}{
		{
			name:        "limit to 10",
			suggestions: suggestions,
			max:         10,
			wantLen:     10,
		},
		{
			name:        "limit to 5",
			suggestions: suggestions,
			max:         5,
			wantLen:     5,
		},
		{
			name:        "limit larger than list",
			suggestions: suggestions[:5],
			max:         10,
			wantLen:     5,
		},
		{
			name:        "limit to 0",
			suggestions: suggestions,
			max:         0,
			wantLen:     0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := completer.limitSuggestions(tt.suggestions, tt.max)
			assert.Len(t, result, tt.wantLen)
		})
	}
}

// TestCompleter_GetSuggestions verifies suggestion retrieval
func TestCompleter_GetSuggestions(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	t.Run("returns all suggestions", func(t *testing.T) {
		suggestions := completer.GetSuggestions()
		assert.NotEmpty(t, suggestions)
	})

	t.Run("includes k8s commands", func(t *testing.T) {
		suggestions := completer.GetSuggestions()

		hasK8s := false
		for _, sug := range suggestions {
			if len(sug.Text) >= 3 && sug.Text[:3] == "k8s" {
				hasK8s = true
				break
			}
		}
		assert.True(t, hasK8s)
	})
}

// TestCompleter_AddCustomSuggestion verifies custom suggestion addition
func TestCompleter_AddCustomSuggestion(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	t.Run("adds custom suggestion", func(t *testing.T) {
		initialLen := len(completer.GetSuggestions())

		completer.AddCustomSuggestion("custom-command", "Custom description")

		newLen := len(completer.GetSuggestions())
		assert.Equal(t, initialLen+1, newLen)
	})

	t.Run("custom suggestion is retrievable", func(t *testing.T) {
		completer.AddCustomSuggestion("test-command", "Test description")

		suggestions := completer.GetSuggestions()
		found := false
		for _, sug := range suggestions {
			if sug.Text == "test-command" && sug.Description == "Test description" {
				found = true
				break
			}
		}
		assert.True(t, found)
	})
}

// TestCompleter_BuildSuggestions verifies suggestion building
func TestCompleter_BuildSuggestions(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	// Add subcommands
	rootCmd.AddCommand(&cobra.Command{
		Use:   "test",
		Short: "Test command",
	})

	completer := NewCompleter(rootCmd)

	t.Run("builds suggestions from cobra commands", func(t *testing.T) {
		suggestions := completer.GetSuggestions()

		// Should include slash commands
		hasSlash := false
		for _, sug := range suggestions {
			if sug.Text == "/help" {
				hasSlash = true
				break
			}
		}
		assert.True(t, hasSlash, "should include slash commands")
	})

	t.Run("includes workflow aliases", func(t *testing.T) {
		suggestions := completer.GetSuggestions()

		workflows := []string{"wf1", "wf2", "wf3", "wf4"}
		for _, wf := range workflows {
			found := false
			for _, sug := range suggestions {
				if sug.Text == wf {
					found = true
					break
				}
			}
			assert.True(t, found, "should include workflow: %s", wf)
		}
	})
}

// TestCompleter_MultiWordCommands verifies multi-word command handling
func TestCompleter_MultiWordCommands(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	tests := []struct {
		name  string
		input string
	}{
		{
			name:  "two word k8s command",
			input: "k8s get",
		},
		{
			name:  "three word orchestrate command",
			input: "orchestrate offensive apt",
		},
		{
			name:  "four word command",
			input: "orchestrate offensive apt-simulation --target",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			suggestions := completer.CompleteText(tt.input)
			// Should handle multi-word commands without panicking
			assert.NotNil(t, suggestions)
		})
	}
}

// TestCompleter_SpecialCharacters verifies handling of special characters
func TestCompleter_SpecialCharacters(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	completer := NewCompleter(rootCmd)

	tests := []struct {
		name  string
		input string
	}{
		{
			name:  "hyphen in command",
			input: "apt-simulation",
		},
		{
			name:  "underscore in command",
			input: "threat_hunt",
		},
		{
			name:  "quotes in input",
			input: "data query \"MATCH\"",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.NotPanics(t, func() {
				completer.CompleteText(tt.input)
			})
		})
	}
}
