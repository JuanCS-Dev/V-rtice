package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"golang.org/x/term"
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
		// Check if stdin is a terminal
		if !term.IsTerminal(int(os.Stdin.Fd())) {
			fmt.Fprintf(os.Stderr, "Error: Interactive shell requires a terminal (TTY)\n\n")
			fmt.Fprintf(os.Stderr, "Solutions:\n")
			fmt.Fprintf(os.Stderr, "  • Run from an interactive terminal (not via pipe or SSH without TTY)\n")
			fmt.Fprintf(os.Stderr, "  • Use: ssh -t user@host vcli shell (force TTY allocation)\n")
			fmt.Fprintf(os.Stderr, "  • Use individual commands instead: vcli k8s get pods\n")
			os.Exit(1)
		}

		if useLegacyShell {
			// Legacy go-prompt shell
			sh := shell.NewShell(rootCmd, version, buildDate)
			sh.Run()
		} else {
			// New bubble-tea shell (default)
			if err := bubbletea.Run(rootCmd, version, buildDate); err != nil {
				fmt.Fprintf(os.Stderr, "Error: %v\n", err)
				fmt.Fprintf(os.Stderr, "\nTip: Try using legacy shell mode: vcli shell --legacy\n")
				os.Exit(1)
			}
		}
	},
}

func init() {
	rootCmd.AddCommand(shellCmd)
	shellCmd.Flags().BoolVar(&useLegacyShell, "legacy", false, "Use legacy go-prompt shell")
}
