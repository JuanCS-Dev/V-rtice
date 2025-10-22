package main

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/help"
)

// examplesCmd represents the examples command
var examplesCmd = &cobra.Command{
	Use:   "examples [category]",
	Short: "Show interactive examples for vcli commands",
	Long: `Show interactive examples and usage patterns for vcli commands.

Categories:
  k8s        - Kubernetes operations
  maximus    - MAXIMUS orchestrator
  hitl       - Human-in-the-Loop console
  config     - Configuration management
  shell      - Interactive shell
  tui        - Terminal UI workspaces
  all        - Show all examples`,
	Example: `  # Show all examples
  vcli examples

  # Show Kubernetes examples
  vcli examples k8s

  # Show MAXIMUS examples
  vcli examples maximus

  # Show configuration examples
  vcli examples config`,
	Run: handleExamples,
}

// handleExamples handles the examples command execution
func handleExamples(cmd *cobra.Command, args []string) {
	category := "all"
	if len(args) > 0 {
		category = args[0]
	}

	switch category {
	case "k8s", "kubernetes":
		showK8sExamples()
	case "maximus":
		showMaximusExamples()
	case "hitl":
		showHITLExamples()
	case "config", "configure":
		showConfigExamples()
	case "shell":
		showShellExamples()
	case "tui", "workspace":
		showTUIExamples()
	case "all":
		showAllExamples()
	default:
		fmt.Printf("Unknown category: %s\n\n", category)
		fmt.Println("Available categories: k8s, maximus, hitl, config, shell, tui, all")
	}
}

// showK8sExamples shows Kubernetes examples
func showK8sExamples() {
	fmt.Println("═══════════════════════════════════════════════════════════════════")
	fmt.Println("  📦 KUBERNETES EXAMPLES")
	fmt.Println("═══════════════════════════════════════════════════════════════════")

	examples := help.AllK8sExamples()
	for _, group := range examples {
		fmt.Print(help.FormatExampleGroup(group))
	}

	fmt.Println("\n" + "═══════════════════════════════════════════════════════════════════")
	fmt.Println("💡 TIP: Use 'vcli k8s <command> --help' for detailed help on any command")
	fmt.Println("═══════════════════════════════════════════════════════════════════")
}

// showMaximusExamples shows MAXIMUS examples
func showMaximusExamples() {
	fmt.Println("═══════════════════════════════════════════════════════════════════")
	fmt.Println("  🧠 MAXIMUS ORCHESTRATOR EXAMPLES")
	fmt.Println("═══════════════════════════════════════════════════════════════════")

	examples := help.AllMaximusExamples()
	for _, group := range examples {
		fmt.Print(help.FormatExampleGroup(group))
	}

	fmt.Println("\n" + "═══════════════════════════════════════════════════════════════════")
	fmt.Println("💡 TIP: Use 'vcli maximus <command> --help' for detailed help")
	fmt.Println("═══════════════════════════════════════════════════════════════════")
}

// showHITLExamples shows HITL examples
func showHITLExamples() {
	fmt.Println("═══════════════════════════════════════════════════════════════════")
	fmt.Println("  🏛️  HUMAN-IN-THE-LOOP EXAMPLES")
	fmt.Println("═══════════════════════════════════════════════════════════════════")

	examples := help.AllHITLExamples()
	for _, group := range examples {
		fmt.Print(help.FormatExampleGroup(group))
	}

	fmt.Println("\n" + "═══════════════════════════════════════════════════════════════════")
	fmt.Println("💡 TIP: Use 'vcli hitl <command> --help' for detailed help")
	fmt.Println("═══════════════════════════════════════════════════════════════════")
}

// showConfigExamples shows configuration examples
func showConfigExamples() {
	fmt.Println("═══════════════════════════════════════════════════════════════════")
	fmt.Println("  ⚙️  CONFIGURATION EXAMPLES")
	fmt.Println("═══════════════════════════════════════════════════════════════════")

	fmt.Print(help.FormatExampleGroup(help.ConfigureExamples))

	fmt.Println("\n" + "═══════════════════════════════════════════════════════════════════")
	fmt.Println("💡 TIP: Configuration precedence: CLI flags > ENV vars > config file > defaults")
	fmt.Println("═══════════════════════════════════════════════════════════════════")
}

// showShellExamples shows shell examples
func showShellExamples() {
	fmt.Println("═══════════════════════════════════════════════════════════════════")
	fmt.Println("  💻 INTERACTIVE SHELL EXAMPLES")
	fmt.Println("═══════════════════════════════════════════════════════════════════")

	fmt.Print(help.FormatExampleGroup(help.ShellExamples))

	fmt.Println("\n" + "═══════════════════════════════════════════════════════════════════")
	fmt.Println("💡 TIP: Press Ctrl+P or type '/palette' for command palette with fuzzy search")
	fmt.Println("═══════════════════════════════════════════════════════════════════")
}

// showTUIExamples shows TUI examples
func showTUIExamples() {
	fmt.Println("═══════════════════════════════════════════════════════════════════")
	fmt.Println("  🎨 TERMINAL UI EXAMPLES")
	fmt.Println("═══════════════════════════════════════════════════════════════════")

	fmt.Print(help.FormatExampleGroup(help.TUIExamples))

	fmt.Println("\n" + "═══════════════════════════════════════════════════════════════════")
	fmt.Println("💡 TIP: Press '?' in TUI for keyboard shortcuts, Tab to switch workspaces")
	fmt.Println("═══════════════════════════════════════════════════════════════════")
}

// showAllExamples shows all examples by category
func showAllExamples() {
	fmt.Println("═══════════════════════════════════════════════════════════════════")
	fmt.Println("  📚 VCLI 2.0 - COMPLETE EXAMPLES LIBRARY")
	fmt.Println("═══════════════════════════════════════════════════════════════════\n")

	// General
	fmt.Print(help.FormatExampleGroup(help.GeneralExamples))

	// Config
	fmt.Println("\n" + "───────────────────────────────────────────────────────────────────")
	fmt.Print(help.FormatExampleGroup(help.ConfigureExamples))

	// Shell & TUI
	fmt.Println("\n" + "───────────────────────────────────────────────────────────────────")
	fmt.Print(help.FormatExampleGroup(help.ShellExamples))

	fmt.Println("\n" + "───────────────────────────────────────────────────────────────────")
	fmt.Print(help.FormatExampleGroup(help.TUIExamples))

	// Kubernetes (show first few groups)
	fmt.Println("\n" + "───────────────────────────────────────────────────────────────────")
	fmt.Println("\n  📦 KUBERNETES (Sample)")
	fmt.Print(help.FormatExampleGroup(help.K8sGetExamples))
	fmt.Print(help.FormatExampleGroup(help.K8sLogsExamples))

	// MAXIMUS
	fmt.Println("\n" + "───────────────────────────────────────────────────────────────────")
	fmt.Println("\n  🧠 MAXIMUS ORCHESTRATOR (Sample)")
	fmt.Print(help.FormatExampleGroup(help.MaximusExamples))

	// HITL
	fmt.Println("\n" + "───────────────────────────────────────────────────────────────────")
	fmt.Println("\n  🏛️  HUMAN-IN-THE-LOOP (Sample)")
	fmt.Print(help.FormatExampleGroup(help.HITLExamples))

	// Footer
	fmt.Println("\n" + "═══════════════════════════════════════════════════════════════════")
	fmt.Println("💡 TIPS:")
	fmt.Println("  • Use 'vcli examples <category>' to see focused examples")
	fmt.Println("  • Use '<command> --help' for detailed command documentation")
	fmt.Println("  • Launch 'vcli shell' for interactive mode with autocomplete")
	fmt.Println("  • Press 'vcli tui' for visual workspaces")
	fmt.Println("═══════════════════════════════════════════════════════════════════")
}

func init() {
	rootCmd.AddCommand(examplesCmd)
}
