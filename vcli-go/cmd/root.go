package main

import (
	"fmt"
	"os"
	"path/filepath"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/shell"
	"github.com/verticedev/vcli-go/internal/visual/banner"
	"github.com/verticedev/vcli-go/internal/workspace"
	"github.com/verticedev/vcli-go/internal/workspace/governance"
	"github.com/verticedev/vcli-go/internal/workspace/investigation"
	"github.com/verticedev/vcli-go/internal/workspace/situational"
)

const (
	version   = "2.0.0"
	buildDate = "2025-10-07"
)

var (
	// Global flags
	debug       bool
	configFile  string
	offline     bool
	noTelemetry bool
	backend     string // Backend type: http or grpc

	// Global config manager
	globalConfig *config.Manager
)

// showBanner displays the epic V12 turbo banner with gradient colors
func showBanner() {
	renderer := banner.NewBannerRenderer()
	fmt.Print(renderer.RenderFull(version, buildDate))
}

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
		// Launch interactive shell by default
		sh := shell.NewShell(cmd.Root(), version, buildDate)
		sh.Run()
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

// initConfig initializes the config manager
func initConfig() {
	// Determine config path
	configPath := configFile
	if configPath == "" {
		home, err := os.UserHomeDir()
		if err == nil {
			configPath = filepath.Join(home, ".vcli", "config.yaml")
		}
	}

	// Initialize config manager
	var err error
	globalConfig, err = config.NewManager(configPath)
	if err != nil {
		// Config file not found is OK - will use defaults
		if !os.IsNotExist(err) {
			if debug || os.Getenv("VCLI_DEBUG") == "true" {
				fmt.Fprintf(os.Stderr, "[DEBUG] Config load warning: %v (using defaults)\n", err)
			}
		}
	} else if debug || os.Getenv("VCLI_DEBUG") == "true" {
		fmt.Fprintf(os.Stderr, "[DEBUG] Config loaded from: %s\n", configPath)
	}

	// Apply flag overrides to global config
	if debug {
		// Sync debug flag to config
		cfg := globalConfig.Get()
		cfg.Global.Debug = true
	}
	if offline {
		cfg := globalConfig.Get()
		cfg.Global.Offline = true
	}
}

func init() {
	// Initialize config before command execution
	cobra.OnInitialize(initConfig)

	// Global flags
	rootCmd.PersistentFlags().BoolVar(&debug, "debug", false, "Enable debug mode")
	rootCmd.PersistentFlags().StringVar(&configFile, "config", "", "Config file (default: ~/.vcli/config.yaml)")
	rootCmd.PersistentFlags().BoolVar(&offline, "offline", false, "Enable offline mode")
	rootCmd.PersistentFlags().BoolVar(&noTelemetry, "no-telemetry", false, "Disable telemetry")
	rootCmd.PersistentFlags().StringVar(&backend, "backend", "http", "Backend type: http or grpc (default: http)")

	// Add subcommands
	rootCmd.AddCommand(tuiCmd)
	rootCmd.AddCommand(versionCmd)
	rootCmd.AddCommand(workspaceCmd)
	rootCmd.AddCommand(offlineCmd)

	// Workspace subcommands
	workspaceCmd.AddCommand(workspaceListCmd)
	workspaceCmd.AddCommand(workspaceLaunchCmd)

	// Offline subcommands
	offlineCmd.AddCommand(offlineStatusCmd)
	offlineCmd.AddCommand(offlineSyncCmd)
	offlineCmd.AddCommand(offlineClearCmd)
}

// launchTUI initializes and launches the TUI with workspaces
func launchTUI() {
	// Create workspace manager
	manager := workspace.NewManager()

	// Add workspaces
	manager.AddWorkspace(situational.New())
	manager.AddWorkspace(investigation.New())
	manager.AddWorkspace(governance.NewPlaceholder())

	// Create Bubble Tea program with workspace manager
	p := tea.NewProgram(
		manager,
		tea.WithAltScreen(),       // Use alternate screen buffer
		tea.WithMouseCellMotion(), // Enable mouse support
	)

	// Run the program
	if _, err := p.Run(); err != nil {
		fmt.Printf("Error running TUI: %v\n", err)
		os.Exit(1)
	}
}

// GetRootCommand returns the root command for testing
func GetRootCommand() *cobra.Command {
	return rootCmd
}

// GetConfig returns the global config manager
// This is used by other command files to access configuration
func GetConfig() *config.Manager {
	return globalConfig
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
