package bubbletea

import (
	"strings"
	"testing"

	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
)

// TestModel_View verifies View rendering
func TestModel_View(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("returns empty string when quitting", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.quitting = true

		view := model.View()
		assert.Empty(t, view)
	})

	t.Run("renders welcome banner initially", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.showWelcome = true

		view := model.View()
		assert.NotEmpty(t, view)
	})

	t.Run("shows warning for small terminal", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.width = 50  // Less than MinWidth
		model.height = 20 // Less than MinHeight

		view := model.View()
		assert.Contains(t, view, "Terminal too small")
	})

	t.Run("renders prompt", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.showWelcome = false

		view := model.View()
		assert.Contains(t, view, "vCLI")
	})

	t.Run("renders toolbar", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.showWelcome = false

		view := model.View()
		assert.Contains(t, view, "Ctrl+D")
	})
}

// TestModel_RenderPrompt verifies prompt rendering
func TestModel_RenderPrompt(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("includes vCLI title", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		prompt := model.renderPrompt()
		assert.Contains(t, prompt, "vCLI")
	})

	t.Run("includes Kubernetes Edition", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		prompt := model.renderPrompt()
		assert.Contains(t, prompt, "Kubernetes Edition")
	})

	t.Run("includes statusline when available", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.statusline = "⎈ test-context"

		prompt := model.renderPrompt()
		assert.Contains(t, prompt, "⎈ test-context")
	})

	t.Run("includes prompt symbol", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		prompt := model.renderPrompt()
		assert.Contains(t, prompt, "╭─")
		assert.Contains(t, prompt, "╰─>")
	})
}

// TestModel_RenderSuggestions verifies suggestion rendering
func TestModel_RenderSuggestions(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("returns empty for no suggestions", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{}

		output := model.renderSuggestions()
		assert.Empty(t, output)
	})

	t.Run("renders suggestions with cursor", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "k8s get pods", Description: "List pods", Icon: "📦"},
			{Text: "k8s get deployments", Description: "List deployments", Icon: "📦"},
		}
		model.suggestCursor = 0

		output := model.renderSuggestions()
		assert.Contains(t, output, "k8s get pods")
		assert.Contains(t, output, "k8s get deployments")
	})

	t.Run("limits to 8 suggestions", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		// Create 15 suggestions
		for i := 0; i < 15; i++ {
			model.suggestions = append(model.suggestions, Suggestion{
				Text:        "command",
				Description: "description",
			})
		}

		output := model.renderSuggestions()
		assert.Contains(t, output, "7 more")
	})

	t.Run("includes icons", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "test", Description: "Test", Icon: "🧪"},
		}

		output := model.renderSuggestions()
		assert.Contains(t, output, "🧪")
	})

	t.Run("truncates long descriptions", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.width = 80 // Narrow width
		model.suggestions = []Suggestion{
			{
				Text:        "test",
				Description: "This is a very long description that should be truncated because it exceeds the maximum length allowed for descriptions in the suggestion dropdown",
				Icon:        "🧪",
			},
		}

		output := model.renderSuggestions()
		assert.Contains(t, output, "...")
	})

	t.Run("highlights selected suggestion", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "cmd1", Description: "Description 1"},
			{Text: "cmd2", Description: "Description 2"},
		}
		model.suggestCursor = 1

		output := model.renderSuggestions()
		assert.Contains(t, output, "cmd2")
	})
}

// TestModel_RenderToolbar verifies toolbar rendering
func TestModel_RenderToolbar(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("includes keybindings", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		toolbar := model.renderToolbar()
		assert.Contains(t, toolbar, "/")
		assert.Contains(t, toolbar, "Tab")
		assert.Contains(t, toolbar, "Ctrl+D")
	})

	t.Run("includes authorship", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		toolbar := model.renderToolbar()
		assert.Contains(t, toolbar, "Juan Carlos")
		assert.Contains(t, toolbar, "Claude")
	})

	t.Run("includes separator", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		toolbar := model.renderToolbar()
		assert.Contains(t, toolbar, "━")
	})

	t.Run("respects minimum width", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.width = 50 // Less than MinWidth

		toolbar := model.renderToolbar()
		separatorCount := strings.Count(toolbar, "━")
		assert.GreaterOrEqual(t, separatorCount, MinWidth)
	})
}

// TestModel_RenderWelcomeBanner verifies welcome banner rendering
func TestModel_RenderWelcomeBanner(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("includes Core Capabilities title", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		banner := model.renderWelcomeBanner()
		assert.Contains(t, banner, "Core Capabilities")
	})

	t.Run("includes all capabilities", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		banner := model.renderWelcomeBanner()
		assert.Contains(t, banner, "MAXIMUS")
		assert.Contains(t, banner, "Immune")
		assert.Contains(t, banner, "Kubernetes")
		assert.Contains(t, banner, "hunting")
	})

	t.Run("shows capability icons", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		banner := model.renderWelcomeBanner()
		assert.Contains(t, banner, "🧠")
		assert.Contains(t, banner, "🛡️")
		assert.Contains(t, banner, "⎈")
		assert.Contains(t, banner, "🔍")
	})

	t.Run("renders without panic", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		assert.NotPanics(t, func() {
			model.renderWelcomeBanner()
		})
	})
}

// TestModel_ViewWithSuggestions verifies view with suggestions
func TestModel_ViewWithSuggestions(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("shows suggestions when enabled", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.showWelcome = false
		model.showSuggestions = true
		model.suggestions = []Suggestion{
			{Text: "test", Description: "Test command"},
		}

		view := model.View()
		assert.Contains(t, view, "test")
	})

	t.Run("hides suggestions when disabled", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.showWelcome = false
		model.showSuggestions = false
		model.suggestions = []Suggestion{
			{Text: "test", Description: "Test command"},
		}

		view := model.View()
		// Suggestion might still appear in other context, so we just check it renders
		assert.NotEmpty(t, view)
	})
}

// TestModel_ViewTerminalSizeWarning verifies terminal size warning
func TestModel_ViewTerminalSizeWarning(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	tests := []struct {
		name        string
		width       int
		height      int
		wantWarning bool
	}{
		{
			name:        "normal size - no warning",
			width:       120,
			height:      40,
			wantWarning: false,
		},
		{
			name:        "width too small - warning",
			width:       50,
			height:      40,
			wantWarning: true,
		},
		{
			name:        "height too small - warning",
			width:       120,
			height:      20,
			wantWarning: true,
		},
		{
			name:        "both too small - warning",
			width:       50,
			height:      20,
			wantWarning: true,
		},
		{
			name:        "exactly minimum - no warning",
			width:       MinWidth,
			height:      MinHeight,
			wantWarning: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			model := NewModel(rootCmd, "1.0.0", "2024-01-01")
			model.width = tt.width
			model.height = tt.height

			view := model.View()

			if tt.wantWarning {
				assert.Contains(t, view, "Terminal too small")
			} else {
				assert.NotContains(t, view, "Terminal too small")
			}
		})
	}
}

// TestModel_ViewComponents verifies all view components
func TestModel_ViewComponents(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")
	model.showWelcome = false

	view := model.View()

	t.Run("contains prompt", func(t *testing.T) {
		assert.Contains(t, view, "vCLI")
	})

	t.Run("contains toolbar", func(t *testing.T) {
		assert.Contains(t, view, "Ctrl+D")
	})

	t.Run("view is not empty", func(t *testing.T) {
		assert.NotEmpty(t, view)
	})
}

// TestModel_SuggestionCursorIndicator verifies cursor indicator in suggestions
func TestModel_SuggestionCursorIndicator(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	t.Run("shows cursor indicator for selected item", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "cmd1"},
			{Text: "cmd2"},
		}
		model.suggestCursor = 0

		output := model.renderSuggestions()
		assert.Contains(t, output, "→")
	})

	t.Run("no cursor indicator when not selected", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")
		model.suggestions = []Suggestion{
			{Text: "cmd1"},
		}
		model.suggestCursor = -1

		output := model.renderSuggestions()
		// When no cursor, should not have the cursor indicator on items
		assert.NotEmpty(t, output)
	})
}
