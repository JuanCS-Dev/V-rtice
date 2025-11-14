package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/config"
	vcliFs "github.com/verticedev/vcli-go/internal/fs"
	"github.com/verticedev/vcli-go/internal/visual"
	"gopkg.in/yaml.v3"
)

var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Manage VCLI configuration",
	Long: `Manage VCLI configuration including viewing, editing, and validating settings.
Configuration precedence: flags > env > VCLI.md > ~/.vcli/config.yaml > defaults`,
}

// ============================================================================
// CONFIG SHOW
// ============================================================================

var configShowCmd = &cobra.Command{
	Use:   "show",
	Short: "Show effective configuration",
	Long:  `Display the effective configuration after merging all sources`,
	RunE:  runConfigShow,
}

func runConfigShow(cmd *cobra.Command, args []string) error {
	cfg, err := config.Get()
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Effective Configuration\n\n", styles.Accent.Render("⚙️"))

	// API Settings
	fmt.Printf("%s\n", styles.Info.Render("API Settings:"))
	fmt.Printf("  %s %v\n", styles.Muted.Render("Timeout:"), cfg.API.Timeout)
	fmt.Printf("  %s %d\n\n", styles.Muted.Render("Retry:"), cfg.API.Retry)

	// Auth Settings
	fmt.Printf("%s\n", styles.Info.Render("Auth Settings:"))
	tokenDisplay := cfg.Auth.Token
	if tokenDisplay != "" {
		tokenDisplay = tokenDisplay[:min(8, len(tokenDisplay))] + "..."
	} else {
		tokenDisplay = "(not set)"
	}
	fmt.Printf("  %s %s\n", styles.Muted.Render("Token:"), tokenDisplay)
	fmt.Printf("  %s %s\n\n", styles.Muted.Render("Method:"), cfg.Auth.Method)

	// Output Settings
	fmt.Printf("%s\n", styles.Info.Render("Output Settings:"))
	fmt.Printf("  %s %s\n", styles.Muted.Render("Format:"), cfg.Output.Format)
	fmt.Printf("  %s %s\n", styles.Muted.Render("Color:"), cfg.Output.Color)
	fmt.Printf("  %s %v\n\n", styles.Muted.Render("Verbose:"), cfg.Output.Verbose)

	// Endpoints
	fmt.Printf("%s\n", styles.Info.Render("Endpoints:"))
	for service, endpoint := range cfg.Endpoints {
		fmt.Printf("  %s %s\n", styles.Muted.Render(service+":"), endpoint)
	}

	return nil
}

// ============================================================================
// CONFIG GET
// ============================================================================

var configGetCmd = &cobra.Command{
	Use:   "get <key>",
	Short: "Get a configuration value",
	Long:  `Get a specific configuration value (e.g., api.timeout, endpoints.maximus)`,
	Args:  cobra.ExactArgs(1),
	RunE:  runConfigGet,
}

func runConfigGet(cmd *cobra.Command, args []string) error {
	key := args[0]
	cfg, err := config.Get()
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	// Parse key
	parts := strings.Split(key, ".")
	if len(parts) < 2 {
		return fmt.Errorf("invalid key format (use section.key, e.g., api.timeout)")
	}

	section := parts[0]
	subkey := parts[1]

	var value interface{}

	switch section {
	case "api":
		switch subkey {
		case "timeout":
			value = cfg.API.Timeout
		case "retry":
			value = cfg.API.Retry
		default:
			return fmt.Errorf("unknown api key: %s", subkey)
		}
	case "auth":
		switch subkey {
		case "token":
			value = cfg.Auth.Token
		case "method":
			value = cfg.Auth.Method
		default:
			return fmt.Errorf("unknown auth key: %s", subkey)
		}
	case "output":
		switch subkey {
		case "format":
			value = cfg.Output.Format
		case "color":
			value = cfg.Output.Color
		case "verbose":
			value = cfg.Output.Verbose
		default:
			return fmt.Errorf("unknown output key: %s", subkey)
		}
	case "endpoints":
		if endpoint, ok := cfg.Endpoints[subkey]; ok {
			value = endpoint
		} else {
			return fmt.Errorf("unknown endpoint: %s", subkey)
		}
	default:
		return fmt.Errorf("unknown section: %s", section)
	}

	fmt.Printf("%v\n", value)
	return nil
}

// ============================================================================
// CONFIG SET
// ============================================================================

var configSetCmd = &cobra.Command{
	Use:   "set <key> <value>",
	Short: "Set a configuration value",
	Long:  `Set a configuration value in ~/.vcli/config.yaml`,
	Args:  cobra.ExactArgs(2),
	RunE:  runConfigSet,
}

func runConfigSet(cmd *cobra.Command, args []string) error {
	key := args[0]
	value := args[1]

	// Load or create user config using fs helpers
	configPath, err := vcliFs.GetVCLIConfigFile()
	if err != nil {
		return fmt.Errorf("failed to get config file path: %w", err)
	}

	// Ensure directory exists
	if err := vcliFs.EnsureVCLIConfigDir(); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	// Load existing config or create new
	var cfg *config.Config
	if data, err := os.ReadFile(configPath); err == nil {
		cfg = &config.Config{}
		if err := yaml.Unmarshal(data, cfg); err != nil {
			return fmt.Errorf("failed to parse existing config: %w", err)
		}
	} else {
		cfg = config.DefaultConfig()
	}

	// Set value
	parts := strings.Split(key, ".")
	if len(parts) < 2 {
		return fmt.Errorf("invalid key format (use section.key)")
	}

	section := parts[0]
	subkey := parts[1]

	switch section {
	case "endpoints":
		if cfg.Endpoints == nil {
			cfg.Endpoints = make(map[string]string)
		}
		cfg.Endpoints[subkey] = value
	case "auth":
		switch subkey {
		case "token":
			cfg.Auth.Token = value
		case "method":
			cfg.Auth.Method = value
		default:
			return fmt.Errorf("unknown auth key: %s", subkey)
		}
	case "output":
		switch subkey {
		case "format":
			cfg.Output.Format = value
		case "color":
			cfg.Output.Color = value
		case "verbose":
			cfg.Output.Verbose = (value == "true" || value == "1")
		default:
			return fmt.Errorf("unknown output key: %s", subkey)
		}
	default:
		return fmt.Errorf("unknown section: %s", section)
	}

	// Write back
	data, err := yaml.Marshal(cfg)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(configPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write config: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Configuration updated: %s = %s\n", styles.Success.Render("✅"), key, value)
	fmt.Printf("%s Saved to: %s\n", styles.Muted.Render("📝"), configPath)

	return nil
}

// ============================================================================
// CONFIG VALIDATE
// ============================================================================

var configValidateCmd = &cobra.Command{
	Use:   "validate",
	Short: "Validate configuration",
	Long:  `Validate the current configuration for errors`,
	RunE:  runConfigValidate,
}

func runConfigValidate(cmd *cobra.Command, args []string) error {
	loader := config.NewLoader()
	cfg, err := loader.Load()
	if err != nil {
		styles := visual.DefaultStyles()
		fmt.Printf("%s Configuration validation failed:\n", styles.Error.Render("❌"))
		fmt.Printf("%s\n", err.Error())
		return err
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Configuration is valid\n", styles.Success.Render("✅"))

	// Show loaded sources
	fmt.Printf("\n%s\n", styles.Info.Render("Loaded from:"))

	// Check which files exist
	if _, err := os.Stat("VCLI.md"); err == nil {
		fmt.Printf("  %s ./VCLI.md\n", styles.Success.Render("✓"))
	} else if _, err := os.Stat(".vcli/VCLI.md"); err == nil {
		fmt.Printf("  %s ./.vcli/VCLI.md\n", styles.Success.Render("✓"))
	}

	// Use fs helper for proper error handling
	userConfig, err := vcliFs.GetVCLIConfigFile()
	if err == nil {
		if _, statErr := os.Stat(userConfig); statErr == nil {
			fmt.Printf("  %s ~/.vcli/config.yaml\n", styles.Success.Render("✓"))
		}
	}

	fmt.Printf("  %s defaults\n", styles.Success.Render("✓"))

	// Show summary
	fmt.Printf("\n%s\n", styles.Info.Render("Summary:"))
	fmt.Printf("  %s %d\n", styles.Muted.Render("Endpoints:"), len(cfg.Endpoints))
	fmt.Printf("  %s %v\n", styles.Muted.Render("Timeout:"), cfg.API.Timeout)
	fmt.Printf("  %s %d\n", styles.Muted.Render("Retry:"), cfg.API.Retry)

	return nil
}

// ============================================================================
// CONFIG INIT
// ============================================================================

var configInitCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialize VCLI.md in current directory",
	Long:  `Create a VCLI.md file with default configuration in the current directory`,
	RunE:  runConfigInit,
}

func runConfigInit(cmd *cobra.Command, args []string) error {
	vcliMDPath := "VCLI.md"

	// Check if already exists
	if _, err := os.Stat(vcliMDPath); err == nil {
		return fmt.Errorf("VCLI.md already exists")
	}

	// Create template
	template := `---
endpoints:
  maximus: http://localhost:8000
  immune: http://localhost:8001
  maba: http://localhost:9700
  nis: http://localhost:9800
  rte: http://localhost:9900

api:
  timeout: 30s
  retry: 3

output:
  format: json
  color: auto
  verbose: false
---

# VCLI Configuration

This file configures the VCLI (Vértice CLI) for this project.

## Endpoints

Override service endpoints above to point to your environment.

## Usage

All VCLI commands in this directory will automatically use these settings.
You can override individual values with:
- Environment variables: VCLI_MAXIMUS_ENDPOINT, VCLI_TOKEN, etc.
- CLI flags: --server, --timeout, etc.

## Precedence

Configuration is merged in this order (highest to lowest):
1. CLI flags (highest priority)
2. Environment variables
3. This VCLI.md file
4. ~/.vcli/config.yaml
5. Built-in defaults
`

	if err := os.WriteFile(vcliMDPath, []byte(template), 0644); err != nil {
		return fmt.Errorf("failed to write VCLI.md: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Created VCLI.md\n", styles.Success.Render("✅"))
	fmt.Printf("%s Edit the file to customize your configuration\n", styles.Muted.Render("📝"))

	return nil
}

// ============================================================================
// HELPERS
// ============================================================================

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func init() {
	rootCmd.AddCommand(configCmd)

	configCmd.AddCommand(configShowCmd)
	configCmd.AddCommand(configGetCmd)
	configCmd.AddCommand(configSetCmd)
	configCmd.AddCommand(configValidateCmd)
	configCmd.AddCommand(configInitCmd)
}
