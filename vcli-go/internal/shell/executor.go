package shell

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/suggestions"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Executor handles command execution in the shell
type Executor struct {
	rootCmd   *cobra.Command
	styles    *visual.Styles
	history   []string
	suggester *suggestions.Suggester
}

// NewExecutor creates a new command executor
func NewExecutor(rootCmd *cobra.Command) *Executor {
	return &Executor{
		rootCmd:   rootCmd,
		styles:    visual.DefaultStyles(),
		history:   make([]string, 0),
		suggester: suggestions.NewSuggester(rootCmd),
	}
}

// Execute runs a command string
func (e *Executor) Execute(input string) {
	// Trim whitespace
	input = strings.TrimSpace(input)

	// Skip empty input
	if input == "" {
		return
	}

	// Add to history
	e.history = append(e.history, input)

	// Handle slash commands
	if strings.HasPrefix(input, "/") {
		e.handleSlashCommand(input)
		return
	}

	// Handle shell built-ins
	if e.handleBuiltin(input) {
		return
	}

	// Parse command into args
	args := parseCommand(input)
	if len(args) == 0 {
		return
	}

	// Execute Cobra command
	e.executeCobraCommand(args)
}

// handleSlashCommand handles special slash commands
func (e *Executor) handleSlashCommand(input string) {
	cmd := strings.ToLower(strings.TrimSpace(input))

	switch cmd {
	case "/help", "/?":
		e.showHelp()
	case "/exit", "/quit", "/q":
		fmt.Println(e.styles.Info.Render("👋 Goodbye!"))
		os.Exit(0)
	case "/clear", "/cls":
		// ANSI clear screen
		fmt.Print("\033[H\033[2J")
	case "/history":
		e.showHistory()
	case "/theme":
		fmt.Println(e.styles.Info.Render("Theme management coming soon in FASE 1.3!"))
	default:
		fmt.Println(e.styles.Error.Render(fmt.Sprintf("Unknown slash command: %s", cmd)))
		fmt.Println(e.styles.Muted.Render("Type /help for available commands"))
	}
}

// handleBuiltin handles shell built-in commands
func (e *Executor) handleBuiltin(input string) bool {
	lower := strings.ToLower(input)

	switch lower {
	case "exit", "quit":
		fmt.Println(e.styles.Info.Render("👋 Goodbye!"))
		os.Exit(0)
		return true
	case "clear", "cls":
		fmt.Print("\033[H\033[2J")
		return true
	case "help":
		e.showHelp()
		return true
	case "history":
		e.showHistory()
		return true
	}

	return false
}

// executeCobraCommand executes a Cobra command
func (e *Executor) executeCobraCommand(args []string) {
	// Reset Cobra command for reuse
	e.rootCmd.SetArgs(args)

	// Silence Cobra errors temporarily (we'll handle them ourselves)
	originalSilenceErrors := e.rootCmd.SilenceErrors
	originalSilenceUsage := e.rootCmd.SilenceUsage
	e.rootCmd.SilenceErrors = true
	e.rootCmd.SilenceUsage = true

	// Execute command
	err := e.rootCmd.Execute()

	// Restore Cobra settings
	e.rootCmd.SilenceErrors = originalSilenceErrors
	e.rootCmd.SilenceUsage = originalSilenceUsage

	if err != nil {
		// Check if it's an unknown command error
		errMsg := err.Error()
		if strings.Contains(errMsg, "unknown command") || strings.Contains(errMsg, "unknown flag") {
			// Extract the typo from error message
			typo := e.extractTypo(errMsg)
			if typo != "" {
				// Show our formatted suggestion
				suggestion := e.suggester.SuggestCommand(typo)
				fmt.Print(suggestion)
				return
			}
		}

		// For other errors, show the error
		fmt.Println(e.styles.Error.Render("Error: " + errMsg))
		return
	}
}

// extractTypo extracts the typo from an error message
func (e *Executor) extractTypo(errMsg string) string {
	// Try to extract quoted text
	start := strings.Index(errMsg, "\"")
	if start == -1 {
		return ""
	}
	end := strings.Index(errMsg[start+1:], "\"")
	if end == -1 {
		return ""
	}
	return errMsg[start+1 : start+1+end]
}

// showHelp displays shell help
func (e *Executor) showHelp() {
	gradient := visual.DefaultPalette().PrimaryGradient()

	fmt.Println()
	fmt.Println(visual.GradientText("vCLI Interactive Shell", gradient))
	fmt.Println(e.styles.Muted.Render(strings.Repeat("─", 50)))
	fmt.Println()

	fmt.Println(e.styles.Accent.Bold(true).Render("Shell Commands:"))
	fmt.Println(e.styles.Info.Render("  /help, /?        ") + e.styles.Muted.Render("Show this help"))
	fmt.Println(e.styles.Info.Render("  /exit, /quit     ") + e.styles.Muted.Render("Exit the shell"))
	fmt.Println(e.styles.Info.Render("  /clear           ") + e.styles.Muted.Render("Clear the screen"))
	fmt.Println(e.styles.Info.Render("  /history         ") + e.styles.Muted.Render("Show command history"))
	fmt.Println()

	fmt.Println(e.styles.Accent.Bold(true).Render("Navigation:"))
	fmt.Println(e.styles.Info.Render("  ↑/↓              ") + e.styles.Muted.Render("Navigate command history"))
	fmt.Println(e.styles.Info.Render("  Tab              ") + e.styles.Muted.Render("Auto-complete commands"))
	fmt.Println(e.styles.Info.Render("  Ctrl+C           ") + e.styles.Muted.Render("Cancel current input"))
	fmt.Println()

	fmt.Println(e.styles.Accent.Bold(true).Render("vCLI Commands:"))
	fmt.Println(e.styles.Muted.Render("  Type any vCLI command without the 'vcli' prefix"))
	fmt.Println(e.styles.Muted.Render("  Example: k8s get pods --all-namespaces"))
	fmt.Println()

	fmt.Println(e.styles.Muted.Render("For full command list, type: ") + e.styles.Info.Render("--help"))
	fmt.Println()
}

// showHistory displays command history
func (e *Executor) showHistory() {
	if len(e.history) == 0 {
		fmt.Println(e.styles.Muted.Render("No command history"))
		return
	}

	fmt.Println()
	fmt.Println(e.styles.Accent.Bold(true).Render("Command History:"))
	fmt.Println(e.styles.Muted.Render(strings.Repeat("─", 50)))

	// Show last 20 commands
	start := 0
	if len(e.history) > 20 {
		start = len(e.history) - 20
	}

	for i := start; i < len(e.history); i++ {
		fmt.Printf("%s %s\n",
			e.styles.Muted.Render(fmt.Sprintf("%3d.", i+1)),
			e.history[i])
	}
	fmt.Println()
}

// GetHistory returns command history
func (e *Executor) GetHistory() []string {
	return e.history
}

// parseCommand splits a command string into arguments
// Respects quotes and escaping
func parseCommand(input string) []string {
	var args []string
	var current strings.Builder
	inQuote := false
	quoteChar := rune(0)

	for i, r := range input {
		switch {
		case r == '"' || r == '\'':
			if !inQuote {
				inQuote = true
				quoteChar = r
			} else if r == quoteChar {
				inQuote = false
				quoteChar = 0
			} else {
				current.WriteRune(r)
			}

		case r == '\\' && i+1 < len(input):
			// Handle escape
			next := rune(input[i+1])
			current.WriteRune(next)
			// Skip next character (handled in next iteration)

		case r == ' ' && !inQuote:
			// Word boundary
			if current.Len() > 0 {
				args = append(args, current.String())
				current.Reset()
			}

		default:
			current.WriteRune(r)
		}
	}

	// Add final token
	if current.Len() > 0 {
		args = append(args, current.String())
	}

	return args
}
