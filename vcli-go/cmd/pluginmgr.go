package main

import (
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/plugins"
)

var pluginMgrCmd = &cobra.Command{
	Use:   "plugin",
	Short: "Manage vCLI plugins",
	Long: `Load, list, and manage vCLI plugins.

Plugins extend vCLI with custom commands and functionality.

Examples:
  # List loaded plugins
  vcli plugin list

  # Execute plugin command
  vcli plugin exec my-plugin arg1 arg2`,
}

var pluginListCmd = &cobra.Command{
	Use:   "list",
	Short: "List loaded plugins",
	RunE:  runPluginList,
}

func runPluginList(cmd *cobra.Command, args []string) error {
	mgr, err := getPluginManager()
	if err != nil {
		return err
	}

	pluginsList := mgr.List()
	if len(pluginsList) == 0 {
		fmt.Println("No plugins loaded")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintln(w, "NAME\tVERSION\tDESCRIPTION")

	for _, p := range pluginsList {
		fmt.Fprintf(w, "%s\t%s\t%s\n", p.Name(), p.Version(), p.Description())
	}
	w.Flush()

	fmt.Printf("\nTotal: %d plugins\n", len(pluginsList))
	return nil
}

var pluginExecCmd = &cobra.Command{
	Use:   "exec <name> [args...]",
	Short: "Execute plugin command",
	Args:  cobra.MinimumNArgs(1),
	RunE:  runPluginExec,
}

func runPluginExec(cmd *cobra.Command, args []string) error {
	mgr, err := getPluginManager()
	if err != nil {
		return err
	}

	pluginName := args[0]
	pluginArgs := []string{}
	if len(args) > 1 {
		pluginArgs = args[1:]
	}

	return mgr.Execute(pluginName, pluginArgs)
}

func getPluginManager() (*plugins.Manager, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return nil, fmt.Errorf("failed to get home directory: %w", err)
	}

	pluginsPath := fmt.Sprintf("%s/.vcli/plugins", home)
	mgr := plugins.NewManager(pluginsPath, []string{})

	if err := mgr.LoadAll(); err != nil {
		return nil, fmt.Errorf("failed to load plugins: %w", err)
	}

	return mgr, nil
}

func init() {
	rootCmd.AddCommand(pluginMgrCmd)
	pluginMgrCmd.AddCommand(pluginListCmd)
	pluginMgrCmd.AddCommand(pluginExecCmd)
}
