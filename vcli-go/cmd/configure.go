package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/config"
	"gopkg.in/yaml.v3"
)

var configureCmd = &cobra.Command{
	Use:   "configure",
	Short: "Manage vCLI configuration",
	Long: `Configure vCLI settings, profiles, and preferences.

Examples:
  # Show current configuration
  vcli configure show

  # List profiles
  vcli configure profiles

  # Set active profile
  vcli configure use-profile production

  # Set endpoint
  vcli configure set endpoints.maximus localhost:50051`,
}

var configureShowCmd = &cobra.Command{
	Use:   "show",
	Short: "Show current configuration",
	RunE:  runConfigureShow,
}

func runConfigureShow(cmd *cobra.Command, args []string) error {
	mgr, err := getConfigManager()
	if err != nil {
		return err
	}

	cfg := mgr.Get()
	data, err := yaml.Marshal(cfg)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	fmt.Println(string(data))
	return nil
}

var configureProfilesCmd = &cobra.Command{
	Use:   "profiles",
	Short: "List configuration profiles",
	RunE:  runConfigureProfiles,
}

func runConfigureProfiles(cmd *cobra.Command, args []string) error {
	mgr, err := getConfigManager()
	if err != nil {
		return err
	}

	cfg := mgr.Get()
	if len(cfg.Profiles) == 0 {
		fmt.Println("No profiles configured")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintln(w, "NAME\tDESCRIPTION\tACTIVE")

	for name, profile := range cfg.Profiles {
		active := ""
		if name == cfg.CurrentProfile {
			active = "✓"
		}
		fmt.Fprintf(w, "%s\t%s\t%s\n", name, profile.Description, active)
	}
	w.Flush()

	return nil
}

var configureUseProfileCmd = &cobra.Command{
	Use:   "use-profile <name>",
	Short: "Set active profile",
	Args:  cobra.ExactArgs(1),
	RunE:  runConfigureUseProfile,
}

func runConfigureUseProfile(cmd *cobra.Command, args []string) error {
	mgr, err := getConfigManager()
	if err != nil {
		return err
	}

	if err := mgr.SetProfile(args[0]); err != nil {
		return err
	}

	fmt.Printf("✅ Switched to profile: %s\n", args[0])
	return nil
}

// configureInitCmd initializes configuration file
var configureInitCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialize configuration file",
	Long:  `Create a new configuration file with default settings.`,
	RunE:  runConfigureInit,
}

func runConfigureInit(cmd *cobra.Command, args []string) error {
	home, err := os.UserHomeDir()
	if err != nil {
		return fmt.Errorf("error getting home directory: %w", err)
	}

	configPath := filepath.Join(home, ".vcli", "config.yaml")

	// Check if config already exists
	if _, err := os.Stat(configPath); err == nil {
		fmt.Printf("⚠️  Configuration file already exists at: %s\n", configPath)
		fmt.Print("Overwrite? (y/N): ")
		reader := bufio.NewReader(os.Stdin)
		response, _ := reader.ReadString('\n')
		response = strings.TrimSpace(strings.ToLower(response))
		if response != "y" && response != "yes" {
			return fmt.Errorf("aborted")
		}
	}

	// Create config directory
	configDir := filepath.Dir(configPath)
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return fmt.Errorf("error creating config directory: %w", err)
	}

	// Initialize config manager with default config
	mgr, err := config.NewManager(configPath)
	if err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("error initializing config: %w", err)
	}

	// Save default config
	if err := mgr.Save(); err != nil {
		return fmt.Errorf("error saving config: %w", err)
	}

	fmt.Printf("✅ Configuration file created at: %s\n\n", configPath)
	fmt.Println("Default configuration includes:")
	fmt.Println("  • Profile: default")
	fmt.Println("  • MAXIMUS endpoint: localhost:50051")
	fmt.Println("  • Consciousness endpoint: http://localhost:8022")
	fmt.Println("  • HITL endpoint: http://localhost:8000/api")
	fmt.Println("  • Immune endpoint: localhost:50052")
	fmt.Println("  • All AI services (Eureka, Oraculo, Predict)")
	fmt.Println("\nEdit the file or use 'vcli configure set' to customize.")
	return nil
}

// configureSetCmd sets a configuration value
var configureSetCmd = &cobra.Command{
	Use:   "set [key] [value]",
	Short: "Set a configuration value",
	Long:  `Set a specific configuration value. Example: vcli configure set endpoints.maximus localhost:50051`,
	Args:  cobra.ExactArgs(2),
	RunE:  runConfigureSet,
}

func runConfigureSet(cmd *cobra.Command, args []string) error {
	mgr, err := getConfigManager()
	if err != nil {
		return err
	}

	key := args[0]
	value := args[1]

	parts := strings.Split(key, ".")
	if len(parts) < 2 {
		return fmt.Errorf("invalid key format. Use: section.field (e.g., endpoints.maximus)")
	}

	cfg := mgr.Get()

	// Handle different config sections
	switch strings.ToLower(parts[0]) {
	case "endpoints", "endpoint":
		if len(parts) != 2 {
			return fmt.Errorf("invalid endpoint key. Use: endpoints.<service>")
		}
		service := strings.ToLower(parts[1])
		switch service {
		case "maximus":
			cfg.Endpoints.MAXIMUS = value
		case "consciousness":
			cfg.Endpoints.Consciousness = value
		case "hitl":
			cfg.Endpoints.HITL = value
		case "immune":
			cfg.Endpoints.Immune = value
		case "gateway":
			cfg.Endpoints.Gateway = value
		case "prometheus":
			cfg.Endpoints.Prometheus = value
		case "kafka_proxy", "kafkaproxy":
			cfg.Endpoints.KafkaProxy = value
		case "eureka":
			cfg.Endpoints.Eureka = value
		case "oraculo":
			cfg.Endpoints.Oraculo = value
		case "predict":
			cfg.Endpoints.Predict = value
		case "governance":
			cfg.Endpoints.Governance = value
		default:
			return fmt.Errorf("unknown service: %s", service)
		}

	case "global":
		if len(parts) != 2 {
			return fmt.Errorf("invalid global key. Use: global.<field>")
		}
		field := strings.ToLower(parts[1])
		switch field {
		case "debug":
			cfg.Global.Debug = value == "true" || value == "1"
		case "offline":
			cfg.Global.Offline = value == "true" || value == "1"
		case "telemetry":
			cfg.Global.Telemetry = value == "true" || value == "1"
		case "output_format", "outputformat":
			cfg.Global.OutputFormat = value
		case "color_output", "coloroutput":
			cfg.Global.ColorOutput = value == "true" || value == "1"
		default:
			return fmt.Errorf("unknown global field: %s", field)
		}

	default:
		return fmt.Errorf("unknown config section: %s. Valid sections: endpoints, global", parts[0])
	}

	// Save updated config
	if err := mgr.Save(); err != nil {
		return fmt.Errorf("error saving config: %w", err)
	}

	fmt.Printf("✅ Configuration updated: %s = %s\n", key, value)
	return nil
}

// configureCreateProfileCmd creates a new profile
var configureCreateProfileCmd = &cobra.Command{
	Use:   "create-profile [name]",
	Short: "Create a new configuration profile",
	Args:  cobra.ExactArgs(1),
	RunE:  runConfigureCreateProfile,
}

func runConfigureCreateProfile(cmd *cobra.Command, args []string) error {
	mgr, err := getConfigManager()
	if err != nil {
		return err
	}

	profileName := args[0]
	reader := bufio.NewReader(os.Stdin)

	fmt.Printf("Creating new profile: %s\n\n", profileName)

	// Description
	fmt.Print("Description: ")
	description, _ := reader.ReadString('\n')
	description = strings.TrimSpace(description)

	// MAXIMUS endpoint
	fmt.Print("MAXIMUS endpoint (default: localhost:50051): ")
	maximus, _ := reader.ReadString('\n')
	maximus = strings.TrimSpace(maximus)
	if maximus == "" {
		maximus = "localhost:50051"
	}

	// Create profile
	profile := config.Profile{
		Name:        profileName,
		Description: description,
		Endpoints: config.EndpointsConfig{
			MAXIMUS:       maximus,
			Consciousness: "http://localhost:8022",
			HITL:          "http://localhost:8000/api",
			Immune:        "localhost:50052",
			Eureka:        "http://localhost:8024",
			Oraculo:       "http://localhost:8026",
			Predict:       "http://localhost:8028",
			Gateway:       "http://localhost:8080",
			Prometheus:    "http://localhost:9090",
			KafkaProxy:    "localhost:50053",
			Governance:    "localhost:50053",
		},
		Auth: config.AuthConfig{
			Method: "jwt",
		},
	}

	if err := mgr.AddProfile(profile); err != nil {
		return fmt.Errorf("error creating profile: %w", err)
	}

	fmt.Printf("✅ Profile created: %s\n", profileName)
	fmt.Printf("Use 'vcli configure use-profile %s' to activate it.\n", profileName)
	return nil
}

// configureDeleteProfileCmd deletes a profile
var configureDeleteProfileCmd = &cobra.Command{
	Use:   "delete-profile [name]",
	Short: "Delete a configuration profile",
	Args:  cobra.ExactArgs(1),
	RunE:  runConfigureDeleteProfile,
}

func runConfigureDeleteProfile(cmd *cobra.Command, args []string) error {
	mgr, err := getConfigManager()
	if err != nil {
		return err
	}

	profileName := args[0]

	if profileName == "default" {
		return fmt.Errorf("cannot delete default profile")
	}

	fmt.Printf("⚠️  Delete profile '%s'? (y/N): ", profileName)
	reader := bufio.NewReader(os.Stdin)
	response, _ := reader.ReadString('\n')
	response = strings.TrimSpace(strings.ToLower(response))

	if response != "y" && response != "yes" {
		return fmt.Errorf("aborted")
	}

	if err := mgr.DeleteProfile(profileName); err != nil {
		return fmt.Errorf("error deleting profile: %w", err)
	}

	fmt.Printf("✅ Profile deleted: %s\n", profileName)
	return nil
}

func getConfigManager() (*config.Manager, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return nil, fmt.Errorf("failed to get home directory: %w", err)
	}

	configPath := fmt.Sprintf("%s/.vcli/config.yaml", home)
	return config.NewManager(configPath)
}

func init() {
	rootCmd.AddCommand(configureCmd)
	configureCmd.AddCommand(configureInitCmd)
	configureCmd.AddCommand(configureShowCmd)
	configureCmd.AddCommand(configureSetCmd)
	configureCmd.AddCommand(configureProfilesCmd)
	configureCmd.AddCommand(configureUseProfileCmd)
	configureCmd.AddCommand(configureCreateProfileCmd)
	configureCmd.AddCommand(configureDeleteProfileCmd)
}
