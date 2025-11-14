package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/integration"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	integrationServer string
	integrationName   string
)

var integrationCmd = &cobra.Command{
	Use:   "integration",
	Short: "MAXIMUS Integration - External system integrations",
	Long:  `Manage MAXIMUS integrations with external systems and services`,
}

var integrationListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all integrations",
	RunE:  runIntegrationList,
}

func runIntegrationList(cmd *cobra.Command, args []string) error {
	client := integration.NewIntegrationClient(getIntegrationServer())
	result, err := client.List()
	if err != nil {
		return fmt.Errorf("failed to list integrations: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MAXIMUS Integrations\n\n", styles.Accent.Render("🔌"))

	for _, integ := range result.Integrations {
		fmt.Printf("%s %s\n", getStatusIcon(integ.Status), integ.Name)
		fmt.Printf("  %s %s\n", styles.Muted.Render("Type:"), integ.Type)
		fmt.Printf("  %s %.1f%%\n\n", styles.Muted.Render("Health:"), integ.Health)
	}

	return nil
}

var integrationTestCmd = &cobra.Command{
	Use:   "test [integration]",
	Short: "Test integration",
	Args:  cobra.MinimumNArgs(1),
	RunE:  runIntegrationTest,
}

func runIntegrationTest(cmd *cobra.Command, args []string) error {
	client := integration.NewIntegrationClient(getIntegrationServer())
	req := &integration.TestRequest{Integration: args[0]}

	result, err := client.Test(req)
	if err != nil {
		return fmt.Errorf("integration test failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Integration Test - %s\n\n", styles.Accent.Render("🧪"), result.Integration)
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %d ms\n", styles.Muted.Render("Response Time:"), result.ResponseTime)

	return nil
}

var integrationStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Integration service status",
	RunE:  runIntegrationStatus,
}

func runIntegrationStatus(cmd *cobra.Command, args []string) error {
	client := integration.NewIntegrationClient(getIntegrationServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Integration Service Status\n\n", styles.Accent.Render("🔌"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %d integrations\n", styles.Muted.Render("Active:"), result.ActiveIntegrations)

	return nil
}

func getIntegrationServer() string {
	if integrationServer != "" {
		return integrationServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(integrationCmd)
	integrationCmd.AddCommand(integrationListCmd)
	integrationCmd.AddCommand(integrationTestCmd)
	integrationCmd.AddCommand(integrationStatusCmd)

	integrationCmd.PersistentFlags().StringVarP(&integrationServer, "server", "s", "", "Integration server endpoint")
}
