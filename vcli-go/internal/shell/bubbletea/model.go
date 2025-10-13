package bubbletea

import (
	"context"
	"net/http"
	"os/exec"
	"time"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/shell"
	"github.com/verticedev/vcli-go/internal/visual"
)

const (
	// MinWidth is the minimum terminal width for perfect banner alignment (80 chars + margin)
	MinWidth = 82
	// MinHeight is the minimum terminal height
	MinHeight = 30
	// InitialWidth is the initial/preferred terminal width
	InitialWidth = 120
	// InitialHeight is the initial/preferred terminal height
	InitialHeight = 40
)

// Model represents the bubble tea shell state
type Model struct {
	// Core components
	textInput textinput.Model
	executor  *shell.Executor
	completer *shell.Completer

	// Autocomplete state
	suggestions     []Suggestion
	suggestCursor   int
	showSuggestions bool

	// Visual state
	width       int
	height      int
	statusline  string
	showWelcome bool // Show welcome banner on first render

	// Styling
	styles  *visual.Styles
	palette *visual.VerticePalette

	// Control
	quitting  bool
	version   string
	buildDate string

	// Capabilities health status
	capabilitiesStatus map[string]bool
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
	ti.Placeholder = "Type / for commands or start typing..."
	ti.Focus()
	ti.CharLimit = 256
	ti.Width = InitialWidth - 10

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
		width:           InitialWidth,
		height:          InitialHeight,
		showWelcome:     true, // Show welcome banner on first render
		styles:          visual.DefaultStyles(),
		palette:         visual.DefaultPalette(),
		version:         version,
		buildDate:       buildDate,
		capabilitiesStatus: map[string]bool{
			"maximus":    checkMaximusHealth(),
			"immune":     checkImmuneHealth(),
			"kubernetes": checkKubernetesHealth(),
			"hunting":    checkHuntingHealth(),
		},
	}
}

// Init initializes the model
func (m Model) Init() tea.Cmd {
	// Update statusline on init
	m.updateStatusline()
	return textinput.Blink
}

// checkMaximusHealth verifies MAXIMUS Conscious AI integration
func checkMaximusHealth() bool {
	// Check if MAXIMUS service is responding (port 8080 typical)
	return checkHTTPEndpoint("http://localhost:8080/health", 500*time.Millisecond)
}

// checkImmuneHealth verifies Active Immune System protection
func checkImmuneHealth() bool {
	// Check if Active Immune Core service is responding
	return checkHTTPEndpoint("http://localhost:8001/health", 500*time.Millisecond)
}

// checkKubernetesHealth verifies Real-time Kubernetes orchestration
func checkKubernetesHealth() bool {
	// Check if kubectl is available and cluster is accessible
	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()

	cmd := exec.CommandContext(ctx, "kubectl", "cluster-info")
	err := cmd.Run()
	return err == nil
}

// checkHuntingHealth verifies AI-powered threat hunting
func checkHuntingHealth() bool {
	// Check if Reactive Fabric service is responding
	return checkHTTPEndpoint("http://localhost:8002/health", 500*time.Millisecond)
}

// checkHTTPEndpoint performs a quick health check on an HTTP endpoint
func checkHTTPEndpoint(url string, timeout time.Duration) bool {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return false
	}

	client := &http.Client{Timeout: timeout}
	resp, err := client.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	return resp.StatusCode >= 200 && resp.StatusCode < 300
}
