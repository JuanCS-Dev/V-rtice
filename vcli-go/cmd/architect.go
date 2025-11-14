package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/architect"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	architectServer string
	architectTarget string
	architectFormat string
)

var architectCmd = &cobra.Command{
	Use:   "architect",
	Short: "System Architect - Platform-wide analysis",
	Long: `System Architect provides macro-level architectural analysis of the entire
VÉRTICE platform. Identifies gaps, redundancies, and optimization opportunities.`,
}

var architectAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze platform architecture",
	Long:  `Scan all services and analyze integration patterns`,
	RunE:  runArchitectAnalyze,
}

func runArchitectAnalyze(cmd *cobra.Command, args []string) error {
	client := architect.NewArchitectClient(getArchitectServer())
	result, err := client.Analyze()
	if err != nil {
		return fmt.Errorf("analysis failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Platform Architecture Analysis\n\n", styles.Accent.Render("🏗️"))
	fmt.Printf("%s %d services\n", styles.Muted.Render("Total Services:"), result.TotalServices)
	fmt.Printf("%s %d gaps\n", styles.Muted.Render("Gaps Found:"), result.GapsFound)
	fmt.Printf("%s %d redundancies\n", styles.Muted.Render("Redundancies:"), result.Redundancies)
	fmt.Printf("%s %.1f%%\n\n", styles.Muted.Render("Health Score:"), result.HealthScore)

	if len(result.Recommendations) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Recommendations:"))
		for i, rec := range result.Recommendations {
			fmt.Printf("  %d. %s\n", i+1, rec)
		}
	}

	return nil
}

var architectBlueprintCmd = &cobra.Command{
	Use:   "blueprint [service-name]",
	Short: "Generate service blueprint",
	Long:  `Generate architectural blueprint for a new service`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runArchitectBlueprint,
}

func runArchitectBlueprint(cmd *cobra.Command, args []string) error {
	client := architect.NewArchitectClient(getArchitectServer())
	req := &architect.BlueprintRequest{
		ServiceName: args[0],
		Format:      architectFormat,
	}

	result, err := client.Blueprint(req)
	if err != nil {
		return fmt.Errorf("blueprint generation failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Service Blueprint - %s\n\n", styles.Accent.Render("📐"), result.ServiceName)
	fmt.Printf("%s\n%s\n", styles.Info.Render("Blueprint:"), result.Blueprint)

	return nil
}

var architectStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Architect service status",
	RunE:  runArchitectStatus,
}

func runArchitectStatus(cmd *cobra.Command, args []string) error {
	client := architect.NewArchitectClient(getArchitectServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s System Architect Status\n\n", styles.Accent.Render("🏗️"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %d analyses\n", styles.Muted.Render("Completed:"), result.AnalysesCompleted)

	return nil
}

func getArchitectServer() string {
	if architectServer != "" {
		return architectServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(architectCmd)
	architectCmd.AddCommand(architectAnalyzeCmd)
	architectCmd.AddCommand(architectBlueprintCmd)
	architectCmd.AddCommand(architectStatusCmd)

	architectCmd.PersistentFlags().StringVarP(&architectServer, "server", "s", "", "Architect server endpoint")
	architectBlueprintCmd.Flags().StringVar(&architectFormat, "format", "yaml", "Blueprint format")
}
