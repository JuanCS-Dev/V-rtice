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
	executor := NewExecutor(rootCmd)
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

	// Create prompt
	p := prompt.New(
		s.execute,
		s.complete,
		prompt.OptionPrefix("vcli> "),
		prompt.OptionPrefixTextColor(prompt.Cyan),
		prompt.OptionLivePrefix(s.livePrefix),
		prompt.OptionTitle("vCLI Interactive Shell"),
		prompt.OptionHistory(s.executor.GetHistory()),
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

// livePrefix returns the dynamic prompt prefix
func (s *Shell) livePrefix() (string, bool) {
	palette := visual.DefaultPalette()
	gradient := palette.PrimaryGradient()

	// Create gradient "vcli> " prompt
	vcli := visual.GradientText("vcli", gradient)
	return vcli + "> ", true
}

// showWelcome displays the welcome message
func (s *Shell) showWelcome() {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()
	gradient := palette.PrimaryGradient()

	// Clear screen
	fmt.Print("\033[H\033[2J")

	// Show compact banner
	renderer := banner.NewBannerRenderer()
	fmt.Print(renderer.RenderCompact(s.version, s.buildDate))
	fmt.Println()

	// Welcome message
	fmt.Println(styles.Accent.Bold(true).Render("🚀 Interactive Shell Mode"))
	fmt.Println(styles.Muted.Render("Type commands without 'vcli' prefix │ Tab for completion │ /help for help"))
	fmt.Println()

	// Example commands
	fmt.Println(styles.Muted.Render("Examples:"))
	fmt.Printf("  %s\n", visual.GradientText("k8s get pods --all-namespaces", gradient))
	fmt.Printf("  %s\n", visual.GradientText("k8s top nodes", gradient))
	fmt.Printf("  %s\n", visual.GradientText("k8s auth whoami", gradient))
	fmt.Println()
}

// ShowHelp displays shell help
func (s *Shell) ShowHelp() {
	s.executor.showHelp()
}
