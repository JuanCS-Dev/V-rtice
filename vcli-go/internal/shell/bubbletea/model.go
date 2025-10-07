package bubbletea

import (
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/shell"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Model represents the bubble tea shell state
type Model struct {
	// Core components
	textInput   textinput.Model
	executor    *shell.Executor
	completer   *shell.Completer

	// Autocomplete state
	suggestions []Suggestion
	suggestCursor int
	showSuggestions bool

	// Visual state
	width       int
	height      int
	statusline  string

	// Styling
	styles      *visual.Styles
	palette     *visual.VerticePalette

	// Control
	quitting    bool
	version     string
	buildDate   string
}

// Suggestion represents an autocomplete suggestion
type Suggestion struct {
	Text        string
	Description string
	Icon        string
}

// NewModel creates a new bubble tea shell model
func NewModel(rootCmd *cobra.Command, version, buildDate string) Model {
	// Create text input
	ti := textinput.New()
	ti.Placeholder = "Type a command... (or /help)"
	ti.Focus()
	ti.CharLimit = 256
	ti.Width = 80

	// Create executor and completer
	executor := shell.NewExecutor(rootCmd, version, buildDate)
	completer := shell.NewCompleter(rootCmd)

	return Model{
		textInput:       ti,
		executor:        executor,
		completer:       completer,
		suggestions:     make([]Suggestion, 0),
		suggestCursor:   -1,
		showSuggestions: false,
		width:           80,
		height:          24,
		styles:          visual.DefaultStyles(),
		palette:         visual.DefaultPalette(),
		version:         version,
		buildDate:       buildDate,
	}
}

// Init initializes the model
func (m Model) Init() tea.Cmd {
	// Update statusline on init
	m.updateStatusline()
	return textinput.Blink
}
