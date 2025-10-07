package shell

import (
	"strings"

	prompt "github.com/c-bata/go-prompt"
	"github.com/spf13/cobra"
	"github.com/spf13/pflag"
)

// Completer handles auto-completion for the shell
type Completer struct {
	rootCmd     *cobra.Command
	suggestions []prompt.Suggest
}

// NewCompleter creates a new completer
func NewCompleter(rootCmd *cobra.Command) *Completer {
	c := &Completer{
		rootCmd:     rootCmd,
		suggestions: make([]prompt.Suggest, 0),
	}

	c.buildSuggestions()
	return c
}

// Complete returns completion suggestions
func (c *Completer) Complete(d prompt.Document) []prompt.Suggest {
	if d.TextBeforeCursor() == "" {
		return []prompt.Suggest{}
	}

	// Get word before cursor
	args := strings.Split(d.TextBeforeCursor(), " ")
	return prompt.FilterHasPrefix(c.suggestions, args[len(args)-1], true)
}

// buildSuggestions builds the suggestion list from Cobra commands
func (c *Completer) buildSuggestions() {
	// Add slash commands
	c.suggestions = append(c.suggestions, []prompt.Suggest{
		{Text: "/help", Description: "Show shell help"},
		{Text: "/exit", Description: "Exit the shell"},
		{Text: "/quit", Description: "Exit the shell"},
		{Text: "/clear", Description: "Clear the screen"},
		{Text: "/history", Description: "Show command history"},
		{Text: "/theme", Description: "Manage themes (coming soon)"},
	}...)

	// Add built-in commands
	c.suggestions = append(c.suggestions, []prompt.Suggest{
		{Text: "help", Description: "Show shell help"},
		{Text: "exit", Description: "Exit the shell"},
		{Text: "quit", Description: "Exit the shell"},
		{Text: "clear", Description: "Clear the screen"},
		{Text: "history", Description: "Show command history"},
	}...)

	// Add Cobra commands
	c.addCobraCommands(c.rootCmd, "")
}

// addCobraCommands recursively adds Cobra commands to suggestions
func (c *Completer) addCobraCommands(cmd *cobra.Command, prefix string) {
	for _, subCmd := range cmd.Commands() {
		// Skip hidden commands
		if subCmd.Hidden {
			continue
		}

		// Build command path
		cmdPath := subCmd.Use
		if prefix != "" {
			cmdPath = prefix + " " + subCmd.Use
		}

		fullPath := cmdPath

		// Add to suggestions
		c.suggestions = append(c.suggestions, prompt.Suggest{
			Text:        fullPath,
			Description: subCmd.Short,
		})

		// Add subcommands recursively
		if subCmd.HasSubCommands() {
			c.addCobraCommands(subCmd, fullPath)
		}

		// Add flags
		subCmd.Flags().VisitAll(func(f *pflag.Flag) {
			// Long flag
			if f.Name != "" {
				c.suggestions = append(c.suggestions, prompt.Suggest{
					Text:        "--" + f.Name,
					Description: f.Usage,
				})
			}

			// Short flag
			if f.Shorthand != "" {
				c.suggestions = append(c.suggestions, prompt.Suggest{
					Text:        "-" + f.Shorthand,
					Description: f.Usage,
				})
			}
		})
	}
}

// GetSuggestions returns all available suggestions
func (c *Completer) GetSuggestions() []prompt.Suggest {
	return c.suggestions
}

// AddCustomSuggestion adds a custom suggestion
func (c *Completer) AddCustomSuggestion(text, description string) {
	c.suggestions = append(c.suggestions, prompt.Suggest{
		Text:        text,
		Description: description,
	})
}
