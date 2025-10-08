package testutil

import (
	"github.com/spf13/cobra"
	k8scmd "github.com/verticedev/vcli-go/cmd/k8s"
	orchestratecmd "github.com/verticedev/vcli-go/cmd/orchestrate"
)

// BuildRootCommand builds a root command for testing purposes
func BuildRootCommand() *cobra.Command {
	rootCmd := &cobra.Command{
		Use:     "vcli",
		Short:   "vCLI 2.0 - High-performance cybersecurity operations CLI",
		Version: "2.0.0-test",
	}

	// Add all subcommands
	rootCmd.AddCommand(k8scmd.NewK8sCommand())
	rootCmd.AddCommand(orchestratecmd.NewOrchestrateCommand())

	// Add other commands (mock versions for testing)
	rootCmd.AddCommand(&cobra.Command{Use: "data", Short: "Data operations"})
	rootCmd.AddCommand(&cobra.Command{Use: "ethical", Short: "Ethical AI operations"})
	rootCmd.AddCommand(&cobra.Command{Use: "immune", Short: "Immune operations"})
	rootCmd.AddCommand(&cobra.Command{Use: "immunis", Short: "Immunis operations"})
	rootCmd.AddCommand(&cobra.Command{Use: "maximus", Short: "MAXIMUS operations"})
	rootCmd.AddCommand(&cobra.Command{Use: "threat", Short: "Threat intelligence"})
	rootCmd.AddCommand(&cobra.Command{Use: "investigate", Short: "Investigation"})
	rootCmd.AddCommand(&cobra.Command{Use: "metrics", Short: "Metrics"})
	rootCmd.AddCommand(&cobra.Command{Use: "sync", Short: "Sync"})
	rootCmd.AddCommand(&cobra.Command{Use: "stream", Short: "Stream events"})
	rootCmd.AddCommand(&cobra.Command{Use: "gateway", Short: "Gateway operations"})
	rootCmd.AddCommand(&cobra.Command{Use: "hcl", Short: "Homeostatic Control Loop"})
	rootCmd.AddCommand(&cobra.Command{Use: "configure", Short: "Configure"})
	rootCmd.AddCommand(&cobra.Command{Use: "tui", Short: "TUI"})
	rootCmd.AddCommand(&cobra.Command{Use: "workspace", Short: "Workspace management"})
	rootCmd.AddCommand(&cobra.Command{Use: "shell", Short: "Shell"})
	rootCmd.AddCommand(&cobra.Command{Use: "version", Short: "Version"})
	rootCmd.AddCommand(&cobra.Command{Use: "plugin", Short: "Plugin management"})
	rootCmd.AddCommand(&cobra.Command{Use: "offline", Short: "Offline mode"})

	return rootCmd
}
