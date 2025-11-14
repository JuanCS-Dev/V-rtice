package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/registry"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	registryServer  string
	registryService string
)

var registryCmd = &cobra.Command{
	Use:   "registry",
	Short: "Service Registry - Service discovery and health",
	Long:  `Vértice Service Registry for service discovery, health checks, and sidecar management`,
}

var registryListCmd = &cobra.Command{
	Use:   "list",
	Short: "List registered services",
	RunE:  runRegistryList,
}

func runRegistryList(cmd *cobra.Command, args []string) error {
	client := registry.NewRegistryClient(getRegistryServer())
	result, err := client.List()
	if err != nil {
		return fmt.Errorf("failed to list services: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Service Registry\n\n", styles.Accent.Render("📋"))

	for _, svc := range result.Services {
		fmt.Printf("%s %s\n", getStatusIcon(svc.Status), svc.Name)
		fmt.Printf("  %s %s\n", styles.Muted.Render("Endpoint:"), svc.Endpoint)
		fmt.Printf("  %s %.1f%%\n\n", styles.Muted.Render("Health:"), svc.Health)
	}

	return nil
}

var registryHealthCmd = &cobra.Command{
	Use:   "health [service]",
	Short: "Check service health",
	Args:  cobra.MinimumNArgs(1),
	RunE:  runRegistryHealth,
}

func runRegistryHealth(cmd *cobra.Command, args []string) error {
	client := registry.NewRegistryClient(getRegistryServer())
	req := &registry.HealthRequest{Service: args[0]}

	result, err := client.Health(req)
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Service Health - %s\n\n", styles.Accent.Render("❤️"), result.Service)
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %.1f%%\n", styles.Muted.Render("Health:"), result.Health)
	fmt.Printf("%s %d ms\n", styles.Muted.Render("Response Time:"), result.ResponseTime)

	return nil
}

var registryStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Registry service status",
	RunE:  runRegistryStatus,
}

func runRegistryStatus(cmd *cobra.Command, args []string) error {
	client := registry.NewRegistryClient(getRegistryServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Registry Status\n\n", styles.Accent.Render("🏥"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %d services\n", styles.Muted.Render("Registered:"), result.RegisteredServices)
	fmt.Printf("%s %d sidecars\n", styles.Muted.Render("Sidecars:"), result.ActiveSidecars)

	return nil
}

func getRegistryServer() string {
	if registryServer != "" {
		return registryServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(registryCmd)
	registryCmd.AddCommand(registryListCmd)
	registryCmd.AddCommand(registryHealthCmd)
	registryCmd.AddCommand(registryStatusCmd)
	registryCmd.PersistentFlags().StringVarP(&registryServer, "server", "s", "", "Registry server endpoint")
}
