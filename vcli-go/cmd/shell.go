package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/shell"
	"github.com/verticedev/vcli-go/internal/shell/bubbletea"
)

var useLegacyShell bool

// shellCmd represents the shell command
var shellCmd = &cobra.Command{
	Use:   "shell",
	Short: "Launch interactive shell",
	Long: `Launch the vCLI interactive shell mode.

The interactive shell allows you to execute multiple vCLI commands
without having to type 'vcli' every time. Features include:

  • Autocomplete (appears as you type)
  • Command history (↑/↓ to navigate)
  • Tab completion for commands and flags
  • Slash commands (/help, /exit, /clear, etc.)
  • Visual feedback and icons
  • Bottom toolbar with keybindings

Examples:
  vcli shell                    # Launch interactive shell
  vcli shell --legacy           # Use legacy go-prompt shell

Once in the shell:
  vcli> k8s get pods --all-namespaces
  vcli> k8s top nodes
  vcli> /help                   # Show shell help
  vcli> /exit                   # Exit shell`,
	Run: func(cmd *cobra.Command, args []string) {
		if useLegacyShell {
			// Legacy go-prompt shell
			sh := shell.NewShell(rootCmd, version, buildDate)
			sh.Run()
		} else {
			// New bubble-tea shell (default)
			if err := bubbletea.Run(rootCmd, version, buildDate); err != nil {
				fmt.Fprintf(os.Stderr, "Error: %v\n", err)
				os.Exit(1)
			}
		}
	},
}

func init() {
	rootCmd.AddCommand(shellCmd)
	shellCmd.Flags().BoolVar(&useLegacyShell, "legacy", false, "Use legacy go-prompt shell")
}
