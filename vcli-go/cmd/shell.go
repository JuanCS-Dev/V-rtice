package main

import (
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/shell"
)

// shellCmd represents the shell command
var shellCmd = &cobra.Command{
	Use:   "shell",
	Short: "Launch interactive shell",
	Long: `Launch the vCLI interactive shell mode.

The interactive shell allows you to execute multiple vCLI commands
without having to type 'vcli' every time. Features include:

  • Command history (↑/↓ to navigate)
  • Tab completion for commands and flags
  • Slash commands (/help, /exit, /clear, etc.)
  • Persistent session

Examples:
  vcli shell                    # Launch interactive shell

Once in the shell:
  vcli> k8s get pods --all-namespaces
  vcli> k8s top nodes
  vcli> /help                   # Show shell help
  vcli> /exit                   # Exit shell`,
	Run: func(cmd *cobra.Command, args []string) {
		// Create and run shell
		sh := shell.NewShell(rootCmd, version, buildDate)
		sh.Run()
	},
}

func init() {
	rootCmd.AddCommand(shellCmd)
}
