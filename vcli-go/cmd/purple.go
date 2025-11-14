package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/purple"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	purpleServer   string
	purpleScenario string
)

var purpleCmd = &cobra.Command{
	Use:   "purple",
	Short: "Purple Team - Collaborative security exercises",
	Long:  `Purple team operations combining offensive and defensive security testing`,
}

var purpleExerciseCmd = &cobra.Command{
	Use:   "exercise",
	Short: "Run purple team exercise",
	RunE:  runPurpleExercise,
}

func runPurpleExercise(cmd *cobra.Command, args []string) error {
	client := purple.NewPurpleClient(getPurpleServer())
	req := &purple.ExerciseRequest{Scenario: purpleScenario}

	result, err := client.RunExercise(req)
	if err != nil {
		return fmt.Errorf("exercise failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Purple Team Exercise\n\n", styles.Accent.Render("🟣"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Exercise ID:"), result.ExerciseID)
	fmt.Printf("%s %s\n", styles.Muted.Render("Scenario:"), result.Scenario)
	fmt.Printf("%s %s\n\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))

	if len(result.AttackSteps) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Attack Steps:"))
		for i, step := range result.AttackSteps {
			fmt.Printf("  %d. %s - %s\n", i+1, step, getStatusIcon("ok"))
		}
		fmt.Println()
	}

	if len(result.DefenseSteps) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Defense Steps:"))
		for i, step := range result.DefenseSteps {
			fmt.Printf("  %d. %s - %s\n", i+1, step, getStatusIcon("ok"))
		}
	}

	return nil
}

var purpleReportCmd = &cobra.Command{
	Use:   "report [exercise-id]",
	Short: "Get exercise report",
	Args:  cobra.MinimumNArgs(1),
	RunE:  runPurpleReport,
}

func runPurpleReport(cmd *cobra.Command, args []string) error {
	client := purple.NewPurpleClient(getPurpleServer())
	req := &purple.ReportRequest{ExerciseID: args[0]}

	result, err := client.GetReport(req)
	if err != nil {
		return fmt.Errorf("failed to get report: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Exercise Report - %s\n\n", styles.Accent.Render("📊"), result.ExerciseID)
	fmt.Printf("%s %d/%d detected\n", styles.Muted.Render("Detection Rate:"), result.Detected, result.Total)
	fmt.Printf("%s %.1f%%\n\n", styles.Muted.Render("Coverage:"), result.Coverage)

	if len(result.Gaps) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Detection Gaps:"))
		for i, gap := range result.Gaps {
			fmt.Printf("  %d. %s\n", i+1, gap)
		}
	}

	return nil
}

var purpleStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Purple team service status",
	RunE:  runPurpleStatus,
}

func runPurpleStatus(cmd *cobra.Command, args []string) error {
	client := purple.NewPurpleClient(getPurpleServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Purple Team Status\n\n", styles.Accent.Render("🟣"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %d exercises\n", styles.Muted.Render("Completed:"), result.ExercisesCompleted)

	return nil
}

func getPurpleServer() string {
	if purpleServer != "" {
		return purpleServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(purpleCmd)
	purpleCmd.AddCommand(purpleExerciseCmd)
	purpleCmd.AddCommand(purpleReportCmd)
	purpleCmd.AddCommand(purpleStatusCmd)

	purpleCmd.PersistentFlags().StringVarP(&purpleServer, "server", "s", "", "Purple team server endpoint")
	purpleExerciseCmd.Flags().StringVar(&purpleScenario, "scenario", "web-attack", "Exercise scenario")
}
