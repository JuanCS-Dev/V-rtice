package bubbletea

import (
	"testing"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestModel_Update verifies Update method
func TestModel_Update(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("handles window size message", func(t *testing.T) {
		msg := tea.WindowSizeMsg{
			Width:  100,
			Height: 40,
		}

		updatedModel, cmd := model.Update(msg)
		assert.NotNil(t, updatedModel)
		_ = cmd // cmd may be nil

		m, ok := updatedModel.(Model)
		require.True(t, ok)
		assert.Equal(t, 100, m.width)
		assert.Equal(t, 40, m.height)
	})

	t.Run("enforces minimum width", func(t *testing.T) {
		msg := tea.WindowSizeMsg{
			Width:  50, // Less than MinWidth (86)
			Height: 40,
		}

		updatedModel, _ := model.Update(msg)
		m := updatedModel.(Model)
		assert.Equal(t, MinWidth, m.width)
	})

	t.Run("enforces minimum height", func(t *testing.T) {
		msg := tea.WindowSizeMsg{
			Width:  100,
			Height: 20, // Less than MinHeight (30)
		}

		updatedModel, _ := model.Update(msg)
		m := updatedModel.(Model)
		assert.Equal(t, MinHeight, m.height)
	})
}

// TestModel_HandleKeyPress verifies keyboard input handling
func TestModel_HandleKeyPress(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	tests := []struct {
		name          string
		keyType       tea.KeyType
		expectedState func(Model) bool
	}{
		{
			name:    "Ctrl+C clears input",
			keyType: tea.KeyCtrlC,
			expectedState: func(m Model) bool {
				return m.textInput.Value() == "" && !m.showSuggestions
			},
		},
		{
			name:    "Ctrl+D quits",
			keyType: tea.KeyCtrlD,
			expectedState: func(m Model) bool {
				return m.quitting
			},
		},
		{
			name:    "Ctrl+K is handled",
			keyType: tea.KeyCtrlK,
			expectedState: func(m Model) bool {
				return true // Just verify it doesn't panic
			},
		},
		{
			name:    "Esc hides suggestions",
			keyType: tea.KeyEsc,
			expectedState: func(m Model) bool {
				return !m.showSuggestions && m.suggestCursor == -1
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			model := NewModel(rootCmd, "1.0.0", "2024-01-01")
			msg := tea.KeyMsg{Type: tt.keyType}

			updatedModel, _ := model.handleKeyPress(msg)
			m := updatedModel.(Model)

			assert.True(t, tt.expectedState(m))
		})
	}
}

// TestModel_HandleEnterKey verifies Enter key handling
func TestModel_HandleEnterKey(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("Enter executes command", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.textInput.SetValue("help")
		model.showWelcome = true

		msg := tea.KeyMsg{Type: tea.KeyEnter}
		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.Empty(t, m.textInput.Value())
		assert.False(t, m.showWelcome)
	})

	t.Run("Enter accepts suggestion", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "k8s get pods", Description: "List pods"},
		}
		model.suggestCursor = 0
		model.showSuggestions = true

		msg := tea.KeyMsg{Type: tea.KeyEnter}
		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.Equal(t, "k8s get pods", m.textInput.Value())
		assert.Equal(t, -1, m.suggestCursor)
		assert.False(t, m.showSuggestions)
	})

	t.Run("Enter with empty command does nothing", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.textInput.SetValue("")

		msg := tea.KeyMsg{Type: tea.KeyEnter}
		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.Empty(t, m.textInput.Value())
	})
}

// TestModel_HandleTabKey verifies Tab key handling
func TestModel_HandleTabKey(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("Tab accepts suggestion", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "k8s get pods", Description: "List pods"},
		}
		model.suggestCursor = 0
		model.showSuggestions = true

		msg := tea.KeyMsg{Type: tea.KeyTab}
		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.Equal(t, "k8s get pods", m.textInput.Value())
		assert.Equal(t, -1, m.suggestCursor)
		assert.False(t, m.showSuggestions)
		assert.Len(t, m.suggestions, 0)
	})

	t.Run("Tab with no selection does nothing", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestCursor = -1

		msg := tea.KeyMsg{Type: tea.KeyTab}
		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.Equal(t, -1, m.suggestCursor)
	})
}

// TestModel_HandleUpDownKeys verifies arrow key navigation
func TestModel_HandleUpDownKeys(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("Up key navigates suggestions up", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "cmd1"},
			{Text: "cmd2"},
			{Text: "cmd3"},
		}
		model.suggestCursor = 1

		msg := tea.KeyMsg{Type: tea.KeyUp}
		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.Equal(t, 0, m.suggestCursor)
		assert.True(t, m.showSuggestions)
	})

	t.Run("Up key wraps to end", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "cmd1"},
			{Text: "cmd2"},
			{Text: "cmd3"},
		}
		model.suggestCursor = -1

		msg := tea.KeyMsg{Type: tea.KeyUp}
		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.Equal(t, 2, m.suggestCursor)
	})

	t.Run("Down key navigates suggestions down", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "cmd1"},
			{Text: "cmd2"},
			{Text: "cmd3"},
		}
		model.suggestCursor = 0

		msg := tea.KeyMsg{Type: tea.KeyDown}
		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.Equal(t, 1, m.suggestCursor)
		assert.True(t, m.showSuggestions)
	})

	t.Run("Down key wraps to top", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "cmd1"},
			{Text: "cmd2"},
			{Text: "cmd3"},
		}
		model.suggestCursor = 2

		msg := tea.KeyMsg{Type: tea.KeyDown}
		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.Equal(t, -1, m.suggestCursor)
	})

	t.Run("Up/Down with no suggestions does nothing", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{}

		msgUp := tea.KeyMsg{Type: tea.KeyUp}
		updatedModel, _ := model.handleKeyPress(msgUp)
		mUp := updatedModel.(Model)
		assert.Equal(t, -1, mUp.suggestCursor)

		msgDown := tea.KeyMsg{Type: tea.KeyDown}
		updatedModel, _ = model.handleKeyPress(msgDown)
		mDown := updatedModel.(Model)
		assert.Equal(t, -1, mDown.suggestCursor)
	})
}

// TestModel_HandleSlashKey verifies slash key special handling
func TestModel_HandleSlashKey(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("slash key triggers autocomplete", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		msg := tea.KeyMsg{
			Type:  tea.KeyRunes,
			Runes: []rune{'/'},
		}

		updatedModel, _ := model.handleKeyPress(msg)
		m := updatedModel.(Model)

		assert.True(t, m.showSuggestions)
	})
}

// TestModel_UpdateAutocomplete verifies autocomplete logic
func TestModel_UpdateAutocomplete(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}
	rootCmd.AddCommand(&cobra.Command{
		Use:   "k8s",
		Short: "Kubernetes",
	})

	t.Run("empty input clears suggestions", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.textInput.SetValue("")

		model.updateAutocomplete()

		assert.Len(t, model.suggestions, 0)
		assert.Equal(t, -1, model.suggestCursor)
		assert.False(t, model.showSuggestions)
	})

	t.Run("slash triggers slash commands", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.textInput.SetValue("/")

		model.updateAutocomplete()

		assert.NotEmpty(t, model.suggestions)
		assert.True(t, model.showSuggestions)
	})

	t.Run("input ending with space clears suggestions", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.textInput.SetValue("k8s ")

		model.updateAutocomplete()

		assert.Len(t, model.suggestions, 0)
		assert.False(t, model.showSuggestions)
	})

	t.Run("regular input shows suggestions", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.textInput.SetValue("k8s")

		model.updateAutocomplete()

		// Should have suggestions
		assert.NotNil(t, model.suggestions)
	})

	t.Run("cursor resets if out of bounds", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestCursor = 10
		model.textInput.SetValue("k")

		model.updateAutocomplete()

		if len(model.suggestions) > 0 {
			assert.LessOrEqual(t, model.suggestCursor, len(model.suggestions)-1)
		} else {
			assert.Equal(t, -1, model.suggestCursor)
		}
	})
}

// TestModel_UpdateSlashCommands verifies slash command autocomplete
func TestModel_UpdateSlashCommands(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("empty query shows all slash commands", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		model.updateSlashCommands("/")

		assert.NotEmpty(t, model.suggestions)
		assert.True(t, model.showSuggestions)
	})

	t.Run("partial query filters slash commands", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		model.updateSlashCommands("/he")

		// Should have /help
		found := false
		for _, sug := range model.suggestions {
			if sug.Text == "/help" {
				found = true
				break
			}
		}
		assert.True(t, found)
	})

	t.Run("includes all standard slash commands", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		model.updateSlashCommands("/")

		expectedCommands := map[string]bool{
			"/help":    false,
			"/clear":   false,
			"/exit":    false,
			"/version": false,
		}

		for _, sug := range model.suggestions {
			if _, exists := expectedCommands[sug.Text]; exists {
				expectedCommands[sug.Text] = true
			}
		}

		for cmd, found := range expectedCommands {
			assert.True(t, found, "expected to find command: %s", cmd)
		}
	})
}

// TestModel_ExecuteCommand verifies command execution
func TestModel_ExecuteCommand(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("executes regular command", func(t *testing.T) {
		assert.NotPanics(t, func() {
			model.executeCommand("help")
		})
	})

	t.Run("executes slash command", func(t *testing.T) {
		assert.NotPanics(t, func() {
			model.executeCommand("/help")
		})
	})

	t.Run("strips leading slash", func(t *testing.T) {
		assert.NotPanics(t, func() {
			model.executeCommand("/clear")
		})
	})
}

// TestGetIconForCommand verifies icon mapping
func TestGetIconForCommand(t *testing.T) {
	tests := []struct {
		name     string
		command  string
		expected string
	}{
		{
			name:     "k8s command",
			command:  "k8s get pods",
			expected: "📦",
		},
		{
			name:     "orchestrate command",
			command:  "orchestrate workflow",
			expected: "🚀",
		},
		{
			name:     "data command",
			command:  "data query",
			expected: "💾",
		},
		{
			name:     "investigate command",
			command:  "investigate threat",
			expected: "🔍",
		},
		{
			name:     "immune command",
			command:  "immune status",
			expected: "🛡️",
		},
		{
			name:     "maximus command",
			command:  "maximus ask",
			expected: "🧠",
		},
		{
			name:     "slash command",
			command:  "/help",
			expected: "⚡",
		},
		{
			name:     "unknown command",
			command:  "unknown",
			expected: "▶",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			icon := getIconForCommand(tt.command)
			assert.Equal(t, tt.expected, icon)
		})
	}
}

// TestModel_CtrlCClearsInput verifies Ctrl+C behavior
func TestModel_CtrlCClearsInput(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")
	model.textInput.SetValue("some command")
	model.suggestions = []Suggestion{{Text: "test"}}
	model.suggestCursor = 0
	model.showSuggestions = true

	msg := tea.KeyMsg{Type: tea.KeyCtrlC}
	updatedModel, _ := model.handleKeyPress(msg)
	m := updatedModel.(Model)

	assert.Empty(t, m.textInput.Value())
	assert.Len(t, m.suggestions, 0)
	assert.Equal(t, -1, m.suggestCursor)
	assert.False(t, m.showSuggestions)
}

// TestModel_EscHidesSuggestions verifies Esc behavior
func TestModel_EscHidesSuggestions(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")
	model.showSuggestions = true
	model.suggestCursor = 2

	msg := tea.KeyMsg{Type: tea.KeyEsc}
	updatedModel, _ := model.handleKeyPress(msg)
	m := updatedModel.(Model)

	assert.False(t, m.showSuggestions)
	assert.Equal(t, -1, m.suggestCursor)
}

// TestModel_WindowSizeUpdate verifies window resize handling
func TestModel_WindowSizeUpdate(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("updates width and height", func(t *testing.T) {
		msg := tea.WindowSizeMsg{
			Width:  150,
			Height: 50,
		}

		updatedModel, _ := model.Update(msg)
		m := updatedModel.(Model)

		assert.Equal(t, 150, m.width)
		assert.Equal(t, 50, m.height)
	})

	t.Run("updates text input width", func(t *testing.T) {
		msg := tea.WindowSizeMsg{
			Width:  120,
			Height: 40,
		}

		updatedModel, _ := model.Update(msg)
		m := updatedModel.(Model)

		assert.Equal(t, 110, m.textInput.Width) // width - 10
	})
}
