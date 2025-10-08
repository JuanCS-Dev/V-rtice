package main

import (
	"fmt"
	"os"
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
	configureCmd.AddCommand(configureShowCmd)
	configureCmd.AddCommand(configureProfilesCmd)
	configureCmd.AddCommand(configureUseProfileCmd)
}
