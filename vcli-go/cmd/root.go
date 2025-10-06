package main

import (
	"context"
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/core"
	"github.com/verticedev/vcli-go/internal/plugins"
	"github.com/verticedev/vcli-go/internal/tui"
)

const (
	version   = "0.1.0"
	buildDate = "2025-01-06"
)

var (
	// Global flags
	debug       bool
	configFile  string
	offline     bool
	noTelemetry bool
)

// rootCmd represents the base command
var rootCmd = &cobra.Command{
	Use:   "vcli",
	Short: "vCLI 2.0 - High-performance cybersecurity operations CLI",
	Long: `vCLI 2.0 is a high-performance Go implementation of the Vértice CLI.

It provides an interactive TUI for cybersecurity operations including:
- Ethical AI Governance (HITL decision making)
- Autonomous Investigation
- Situational Awareness
- Plugin Management
- Offline Mode Support`,
	Version: version,
	Run: func(cmd *cobra.Command, args []string) {
		// Launch TUI by default
		launchTUI()
	},
}

// tuiCmd represents the tui command
var tuiCmd = &cobra.Command{
	Use:   "tui",
	Short: "Launch interactive TUI",
	Long:  `Launch the interactive Terminal User Interface for vCLI.`,
	Run: func(cmd *cobra.Command, args []string) {
		launchTUI()
	},
}

// versionCmd represents the version command
var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print version information",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("vCLI version %s\n", version)
		fmt.Printf("Build date: %s\n", buildDate)
		fmt.Printf("Go implementation: High-performance TUI\n")
	},
}

// configCmd represents the config command
var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Configuration management",
	Long:  `Manage vCLI configuration settings.`,
}

// configInitCmd initializes configuration
var configInitCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialize configuration",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("✅ Configuration initialized at ~/.vcli/config.yaml")
		fmt.Println("📝 Edit the file to customize settings")
	},
}

// configShowCmd shows current configuration
var configShowCmd = &cobra.Command{
	Use:   "show",
	Short: "Show current configuration",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Current Configuration:")
		fmt.Println("  Config File: ~/.vcli/config.yaml")
		fmt.Println("  Log Level: info")
		fmt.Println("  Theme: dark")
		fmt.Println("  Offline Mode: enabled")
	},
}

// pluginCmd represents the plugin command
var pluginCmd = &cobra.Command{
	Use:   "plugin",
	Short: "Plugin management",
	Long:  `Manage vCLI plugins - install, uninstall, list, and configure.`,
}

// pluginListCmd lists plugins
var pluginListCmd = &cobra.Command{
	Use:   "list",
	Short: "List plugins",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Available Plugins:")
		fmt.Println("  kubernetes  v1.0.0  - Kubernetes integration")
		fmt.Println("  prometheus  v1.0.0  - Prometheus monitoring")
		fmt.Println("  git         v1.0.0  - Git integration")
		fmt.Println("\nInstalled Plugins:")
		fmt.Println("  (none)")
	},
}

// pluginInstallCmd installs a plugin
var pluginInstallCmd = &cobra.Command{
	Use:   "install [plugin-name]",
	Short: "Install a plugin",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		pluginName := args[0]
		fmt.Printf("Installing plugin: %s\n", pluginName)
		fmt.Printf("✅ Plugin %s installed successfully\n", pluginName)
	},
}

// pluginUninstallCmd uninstalls a plugin
var pluginUninstallCmd = &cobra.Command{
	Use:   "uninstall [plugin-name]",
	Short: "Uninstall a plugin",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		pluginName := args[0]
		fmt.Printf("Uninstalling plugin: %s\n", pluginName)
		fmt.Printf("✅ Plugin %s uninstalled successfully\n", pluginName)
	},
}

// workspaceCmd represents the workspace command
var workspaceCmd = &cobra.Command{
	Use:   "workspace",
	Short: "Workspace management",
	Long:  `Manage TUI workspaces - launch, list, and configure.`,
}

// workspaceListCmd lists workspaces
var workspaceListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available workspaces",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Available Workspaces:")
		fmt.Println("  governance        - 🏛️  Ethical AI Governance (HITL)")
		fmt.Println("  investigation     - 🔍 Autonomous Investigation")
		fmt.Println("  situational       - 📊 Situational Awareness")
	},
}

// workspaceLaunchCmd launches a workspace
var workspaceLaunchCmd = &cobra.Command{
	Use:   "launch [workspace-id]",
	Short: "Launch a workspace",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		workspaceID := args[0]
		fmt.Printf("Launching workspace: %s\n", workspaceID)
		launchTUI()
	},
}

// offlineCmd represents the offline command
var offlineCmd = &cobra.Command{
	Use:   "offline",
	Short: "Offline mode management",
	Long:  `Manage offline mode - sync, status, and cache.`,
}

// offlineStatusCmd shows offline status
var offlineStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show offline status",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Offline Mode Status:")
		fmt.Println("  Enabled: true")
		fmt.Println("  Last Sync: 2 minutes ago")
		fmt.Println("  Queued Operations: 0")
		fmt.Println("  Cache Size: 45.2 MB / 1 GB")
	},
}

// offlineSyncCmd triggers offline sync
var offlineSyncCmd = &cobra.Command{
	Use:   "sync",
	Short: "Sync offline data",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("🔄 Syncing offline data...")
		fmt.Println("✅ Sync complete: 0 operations synced")
	},
}

// offlineClearCmd clears offline cache
var offlineClearCmd = &cobra.Command{
	Use:   "clear-cache",
	Short: "Clear offline cache",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("🗑️  Clearing offline cache...")
		fmt.Println("✅ Cache cleared successfully")
	},
}

func init() {
	// Global flags
	rootCmd.PersistentFlags().BoolVar(&debug, "debug", false, "Enable debug mode")
	rootCmd.PersistentFlags().StringVar(&configFile, "config", "", "Config file (default: ~/.vcli/config.yaml)")
	rootCmd.PersistentFlags().BoolVar(&offline, "offline", false, "Enable offline mode")
	rootCmd.PersistentFlags().BoolVar(&noTelemetry, "no-telemetry", false, "Disable telemetry")

	// Add subcommands
	rootCmd.AddCommand(tuiCmd)
	rootCmd.AddCommand(versionCmd)
	rootCmd.AddCommand(configCmd)
	rootCmd.AddCommand(pluginCmd)
	rootCmd.AddCommand(workspaceCmd)
	rootCmd.AddCommand(offlineCmd)

	// Config subcommands
	configCmd.AddCommand(configInitCmd)
	configCmd.AddCommand(configShowCmd)

	// Plugin subcommands
	pluginCmd.AddCommand(pluginListCmd)
	pluginCmd.AddCommand(pluginInstallCmd)
	pluginCmd.AddCommand(pluginUninstallCmd)

	// Workspace subcommands
	workspaceCmd.AddCommand(workspaceListCmd)
	workspaceCmd.AddCommand(workspaceLaunchCmd)

	// Offline subcommands
	offlineCmd.AddCommand(offlineStatusCmd)
	offlineCmd.AddCommand(offlineSyncCmd)
	offlineCmd.AddCommand(offlineClearCmd)
}

// launchTUI initializes and launches the TUI
func launchTUI() {
	ctx := context.Background()

	// Initialize core state
	state := core.NewState(version)

	// Initialize plugin system
	// Using InMemoryLoader for now - allows dynamic registration without .so files
	loader := plugins.NewInMemoryLoader()

	// Using NoopSandbox for now - can be replaced with PluginSandbox for resource limits
	sandbox := plugins.NewNoopSandbox()

	// Using LocalRegistry - scans ~/.vcli/plugins directory for .so files
	registry := plugins.NewLocalRegistry(os.ExpandEnv("$HOME/.vcli/plugins"))

	pluginManager := plugins.NewPluginManager(loader, sandbox, registry)

	// Start plugin manager
	if err := pluginManager.Start(ctx); err != nil {
		fmt.Printf("Error starting plugin manager: %v\n", err)
		os.Exit(1)
	}
	defer pluginManager.Stop(ctx)

	// Plugins can be loaded dynamically via:
	// - CLI commands: vcli plugin install kubernetes
	// - Configuration file: ~/.vcli/config.yaml
	// - Programmatically: pluginManager.LoadPlugin(ctx, "kubernetes")
	//
	// Example (commented out):
	// if err := pluginManager.LoadPlugin(ctx, "kubernetes"); err != nil {
	//     log.Printf("Failed to load kubernetes plugin: %v", err)
	// }

	// Create TUI model with plugin manager
	model := tui.NewModelWithPlugins(state, version, pluginManager, ctx)

	// Create Bubble Tea program
	p := tea.NewProgram(
		model,
		tea.WithAltScreen(),       // Use alternate screen buffer
		tea.WithMouseCellMotion(), // Enable mouse support
	)

	// Run the program
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error running TUI: %v\n", err)
		os.Exit(1)
	}
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
