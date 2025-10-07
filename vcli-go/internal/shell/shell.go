package shell

import (
	"fmt"
	"os"

	prompt "github.com/c-bata/go-prompt"
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/visual"
	"github.com/verticedev/vcli-go/internal/visual/banner"
)

// Shell represents the interactive shell
type Shell struct {
	executor  *Executor
	completer *Completer
	prompt    *prompt.Prompt
	version   string
	buildDate string
}

// NewShell creates a new interactive shell
func NewShell(rootCmd *cobra.Command, version, buildDate string) *Shell {
	executor := NewExecutor(rootCmd, version, buildDate)
	completer := NewCompleter(rootCmd)

	shell := &Shell{
		executor:  executor,
		completer: completer,
		version:   version,
		buildDate: buildDate,
	}

	return shell
}

// Run starts the interactive shell
func (s *Shell) Run() {
	// Show welcome banner
	s.showWelcome()

	// Create prompt with minimal prefix (gemini-style)
	p := prompt.New(
		s.execute,
		s.complete,
		prompt.OptionPrefix("┃ "), // Vertical bar indicator
		prompt.OptionPrefixTextColor(prompt.Cyan),
		prompt.OptionTitle("vCLI Interactive Shell"),
		prompt.OptionHistory(s.executor.GetHistory()),

		// Suggestion dropdown colors (cyan background like gemini)
		prompt.OptionSelectedSuggestionBGColor(prompt.Cyan),
		prompt.OptionSelectedSuggestionTextColor(prompt.Black),
		prompt.OptionSuggestionBGColor(prompt.Black),
		prompt.OptionSuggestionTextColor(prompt.White),
		prompt.OptionDescriptionBGColor(prompt.Cyan),
		prompt.OptionDescriptionTextColor(prompt.Black),
		prompt.OptionSelectedDescriptionBGColor(prompt.Cyan),
		prompt.OptionSelectedDescriptionTextColor(prompt.Black),

		// Input colors
		prompt.OptionInputTextColor(prompt.White),
		prompt.OptionInputBGColor(prompt.Black),

		// Scrollbar
		prompt.OptionScrollbarBGColor(prompt.DarkGray),
		prompt.OptionScrollbarThumbColor(prompt.Cyan),

		// Show more suggestions
		prompt.OptionMaxSuggestion(20),
		prompt.OptionCompletionOnDown(),

		prompt.OptionAddKeyBind(prompt.KeyBind{
			Key: prompt.ControlC,
			Fn: func(buf *prompt.Buffer) {
				// Ctrl+C: cancel current input (buffer will be cleared automatically)
			},
		}),
		prompt.OptionAddKeyBind(prompt.KeyBind{
			Key: prompt.ControlD,
			Fn: func(buf *prompt.Buffer) {
				// Ctrl+D: exit shell
				styles := visual.DefaultStyles()
				fmt.Println()
				fmt.Println(styles.Info.Render("👋 Goodbye!"))
				os.Exit(0)
			},
		}),
	)

	s.prompt = p

	// Run the prompt loop
	p.Run()
}

// execute is called when user submits a command
func (s *Shell) execute(input string) {
	s.executor.Execute(input)
}

// complete provides auto-completion
func (s *Shell) complete(d prompt.Document) []prompt.Suggest {
	return s.completer.Complete(d)
}


// showWelcome displays the welcome message
func (s *Shell) showWelcome() {
	styles := visual.DefaultStyles()

	// Clear screen
	fmt.Print("\033[H\033[2J")

	// Show compact banner
	renderer := banner.NewBannerRenderer()
	fmt.Print(renderer.RenderCompact(s.version, s.buildDate))

	// Show statusline with K8s context if available
	statusline := s.executor.renderStatusline()
	if statusline != "" {
		fmt.Println(statusline)
		fmt.Println()
	}

	// Simple help line (no box)
	fmt.Printf("%s │ %s │ %s │ %s\n\n",
		styles.Muted.Render("Tab/↓: Complete"),
		styles.Muted.Render("/help: Help"),
		styles.Muted.Render("/palette: Search"),
		styles.Muted.Render("Ctrl+D: Exit"))
}

// ShowHelp displays shell help
func (s *Shell) ShowHelp() {
	s.executor.showHelp()
}
