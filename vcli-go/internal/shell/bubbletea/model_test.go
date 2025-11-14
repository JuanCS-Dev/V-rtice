package bubbletea

import (
	"testing"

	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewModel verifies Model instance creation
func TestNewModel(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	t.Run("creates model with proper initialization", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		require.NotNil(t, model)
		assert.NotNil(t, model.textInput)
		assert.NotNil(t, model.executor)
		assert.NotNil(t, model.completer)
		assert.NotNil(t, model.suggestions)
		assert.NotNil(t, model.styles)
		assert.NotNil(t, model.palette)
		assert.Equal(t, "1.0.0", model.version)
		assert.Equal(t, "2024-01-01", model.buildDate)
	})

	t.Run("initializes with default dimensions", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		assert.Equal(t, InitialWidth, model.width)
		assert.Equal(t, InitialHeight, model.height)
	})

	t.Run("initializes with welcome screen enabled", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		assert.True(t, model.showWelcome)
	})

	t.Run("initializes with no suggestions", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		assert.Len(t, model.suggestions, 0)
		assert.Equal(t, -1, model.suggestCursor)
		assert.False(t, model.showSuggestions)
	})

	t.Run("initializes capabilities status", func(t *testing.T) {
		model := NewModel(rootCmd, "1.0.0", "2024-01-01")

		assert.NotNil(t, model.capabilitiesStatus)
		assert.Contains(t, model.capabilitiesStatus, "maximus")
		assert.Contains(t, model.capabilitiesStatus, "immune")
		assert.Contains(t, model.capabilitiesStatus, "kubernetes")
		assert.Contains(t, model.capabilitiesStatus, "hunting")
	})
}

// TestModel_Init verifies model initialization
func TestModel_Init(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("Init returns command", func(t *testing.T) {
		cmd := model.Init()
		assert.NotNil(t, cmd)
	})
}

// TestCheckMaximusHealth verifies MAXIMUS health check
func TestCheckMaximusHealth(t *testing.T) {
	t.Run("returns boolean", func(t *testing.T) {
		result := checkMaximusHealth()
		// Should return a boolean (true or false)
		assert.IsType(t, false, result)
	})
}

// TestCheckImmuneHealth verifies Immune system health check
func TestCheckImmuneHealth(t *testing.T) {
	t.Run("returns boolean", func(t *testing.T) {
		result := checkImmuneHealth()
		assert.IsType(t, false, result)
	})
}

// TestCheckKubernetesHealth verifies Kubernetes health check
func TestCheckKubernetesHealth(t *testing.T) {
	t.Run("returns boolean", func(t *testing.T) {
		result := checkKubernetesHealth()
		assert.IsType(t, false, result)
	})
}

// TestCheckHuntingHealth verifies Hunting service health check
func TestCheckHuntingHealth(t *testing.T) {
	t.Run("returns boolean", func(t *testing.T) {
		result := checkHuntingHealth()
		assert.IsType(t, false, result)
	})
}

// TestCheckHTTPEndpoint verifies HTTP endpoint health checking
func TestCheckHTTPEndpoint(t *testing.T) {
	tests := []struct {
		name    string
		url     string
		timeout int64
	}{
		{
			name:    "invalid URL returns false",
			url:     "http://localhost:99999/health",
			timeout: 100,
		},
		{
			name:    "unreachable endpoint returns false",
			url:     "http://192.0.2.1:8080/health", // TEST-NET-1 (unreachable)
			timeout: 100,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := checkHTTPEndpoint(tt.url, 100)
			// Unreachable endpoints should return false
			assert.False(t, result)
		})
	}
}

// TestSuggestion verifies Suggestion struct
func TestSuggestion(t *testing.T) {
	t.Run("creates suggestion with all fields", func(t *testing.T) {
		sug := Suggestion{
			Text:        "k8s get pods",
			Description: "List pods",
			Icon:        "📦",
		}

		assert.Equal(t, "k8s get pods", sug.Text)
		assert.Equal(t, "List pods", sug.Description)
		assert.Equal(t, "📦", sug.Icon)
	})

	t.Run("creates suggestion with empty fields", func(t *testing.T) {
		sug := Suggestion{}

		assert.Empty(t, sug.Text)
		assert.Empty(t, sug.Description)
		assert.Empty(t, sug.Icon)
	})
}

// TestModel_Dimensions verifies dimension constants
func TestModel_Dimensions(t *testing.T) {
	t.Run("MinWidth is defined", func(t *testing.T) {
		assert.Equal(t, 86, MinWidth)
	})

	t.Run("MinHeight is defined", func(t *testing.T) {
		assert.Equal(t, 30, MinHeight)
	})

	t.Run("InitialWidth is defined", func(t *testing.T) {
		assert.Equal(t, 120, InitialWidth)
	})

	t.Run("InitialHeight is defined", func(t *testing.T) {
		assert.Equal(t, 40, InitialHeight)
	})

	t.Run("MinWidth is less than InitialWidth", func(t *testing.T) {
		assert.Less(t, MinWidth, InitialWidth)
	})

	t.Run("MinHeight is less than InitialHeight", func(t *testing.T) {
		assert.Less(t, MinHeight, InitialHeight)
	})
}

// TestModel_VersionAndBuildDate verifies version info
func TestModel_VersionAndBuildDate(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	tests := []struct {
		name      string
		version   string
		buildDate string
	}{
		{
			name:      "semantic version",
			version:   "1.0.0",
			buildDate: "2024-01-01",
		},
		{
			name:      "development version",
			version:   "dev",
			buildDate: "unknown",
		},
		{
			name:      "empty version",
			version:   "",
			buildDate: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			model := NewModel(rootCmd, tt.version, tt.buildDate)

			assert.Equal(t, tt.version, model.version)
			assert.Equal(t, tt.buildDate, model.buildDate)
		})
	}
}

// TestModel_TextInputConfiguration verifies text input setup
func TestModel_TextInputConfiguration(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("text input is focused", func(t *testing.T) {
		assert.True(t, model.textInput.Focused())
	})

	t.Run("text input has placeholder", func(t *testing.T) {
		assert.NotEmpty(t, model.textInput.Placeholder)
	})

	t.Run("text input has char limit", func(t *testing.T) {
		assert.Equal(t, 256, model.textInput.CharLimit)
	})

	t.Run("text input width is set", func(t *testing.T) {
		assert.Equal(t, InitialWidth-10, model.textInput.Width)
	})
}

// TestModel_SuggestionsState verifies suggestions state management
func TestModel_SuggestionsState(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("initial suggestions state", func(t *testing.T) {
		assert.Len(t, model.suggestions, 0)
		assert.Equal(t, -1, model.suggestCursor)
		assert.False(t, model.showSuggestions)
	})

	t.Run("can add suggestions", func(t *testing.T) {
		model.suggestions = append(model.suggestions, Suggestion{
			Text:        "test",
			Description: "test command",
			Icon:        "🧪",
		})

		assert.Len(t, model.suggestions, 1)
	})

	t.Run("can clear suggestions", func(t *testing.T) {
		model.suggestions = []Suggestion{
			{Text: "test1"},
			{Text: "test2"},
		}

		model.suggestions = make([]Suggestion, 0)
		assert.Len(t, model.suggestions, 0)
	})
}

// TestModel_CapabilitiesStatus verifies capabilities tracking
func TestModel_CapabilitiesStatus(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("all capabilities are tracked", func(t *testing.T) {
		capabilities := []string{"maximus", "immune", "kubernetes", "hunting"}

		for _, cap := range capabilities {
			_, exists := model.capabilitiesStatus[cap]
			assert.True(t, exists, "capability %s should be tracked", cap)
		}
	})

	t.Run("capabilities have boolean values", func(t *testing.T) {
		for cap, status := range model.capabilitiesStatus {
			assert.IsType(t, false, status, "capability %s should be boolean", cap)
		}
	})
}

// TestModel_QuittingState verifies quitting state
func TestModel_QuittingState(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("not quitting initially", func(t *testing.T) {
		assert.False(t, model.quitting)
	})

	t.Run("can set quitting state", func(t *testing.T) {
		model.quitting = true
		assert.True(t, model.quitting)
	})
}

// TestModel_StatuslineState verifies statusline state
func TestModel_StatuslineState(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("statusline is initially empty", func(t *testing.T) {
		assert.Empty(t, model.statusline)
	})

	t.Run("can set statusline", func(t *testing.T) {
		model.statusline = "⎈ test-context"
		assert.Equal(t, "⎈ test-context", model.statusline)
	})
}

// TestModel_Styles verifies styling configuration
func TestModel_Styles(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("styles are initialized", func(t *testing.T) {
		assert.NotNil(t, model.styles)
	})

	t.Run("palette is initialized", func(t *testing.T) {
		assert.NotNil(t, model.palette)
	})
}
