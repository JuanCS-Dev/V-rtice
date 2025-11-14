package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/rte"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	rteServer   string
	rteAlert    string
	rteSeverity string
	rtePlaybook string
	rteAuto     bool
)

var rteCmd = &cobra.Command{
	Use:   "rte",
	Short: "Reflex Triage Engine - Real-time threat triage",
	Long: `RTE (Reflex Triage Engine) provides real-time execution for critical,
time-sensitive operations. Features include fusion engine for data correlation,
fast ML predictions, and hyperscan pattern matching.`,
}

// ============================================================================
// TRIAGE OPERATIONS
// ============================================================================

var rteTriageCmd = &cobra.Command{
	Use:   "triage [alert-id]",
	Short: "Triage an alert",
	Long:  `Execute real-time triage on an alert using RTE playbooks`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runRteTriage,
}

func runRteTriage(cmd *cobra.Command, args []string) error {
	client := rte.NewRTEClient(getRTEServer())
	req := &rte.TriageRequest{
		AlertID:  args[0],
		Playbook: rtePlaybook,
		Auto:     rteAuto,
	}

	result, err := client.Triage(req)
	if err != nil {
		return fmt.Errorf("triage failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s RTE Triage Result\n\n", styles.Accent.Render("⚡"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Alert ID:"), result.AlertID)
	fmt.Printf("%s %s\n", styles.Muted.Render("Verdict:"), result.Verdict)
	fmt.Printf("%s %.1f%%\n", styles.Muted.Render("Confidence:"), result.Confidence*100)
	fmt.Printf("%s %d ms\n", styles.Muted.Render("Execution Time:"), result.ExecutionTime)
	fmt.Printf("%s %s\n\n", styles.Muted.Render("Playbook:"), result.PlaybookUsed)

	if len(result.Actions) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Actions Taken:"))
		for i, action := range result.Actions {
			fmt.Printf("  %d. %s - %s\n", i+1, action.Action, getStatusIcon(action.Status))
		}
		fmt.Println()
	}

	if result.Reasoning != "" {
		fmt.Printf("%s\n", styles.Info.Render("Reasoning:"))
		fmt.Printf("%s\n", result.Reasoning)
	}

	return nil
}

// ============================================================================
// FUSION ENGINE
// ============================================================================

var rteFusionCmd = &cobra.Command{
	Use:   "fusion",
	Short: "Fusion engine operations",
	Long:  `Data correlation and fusion across multiple sources`,
}

var rteFusionCorrelateCmd = &cobra.Command{
	Use:   "correlate [event-id]",
	Short: "Correlate event data",
	Long:  `Correlate event across multiple data sources`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runRteFusionCorrelate,
}

func runRteFusionCorrelate(cmd *cobra.Command, args []string) error {
	client := rte.NewRTEClient(getRTEServer())
	req := &rte.FusionRequest{
		EventID: args[0],
	}

	result, err := client.Correlate(req)
	if err != nil {
		return fmt.Errorf("correlation failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Fusion Correlation\n\n", styles.Accent.Render("🔗"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Event ID:"), result.EventID)
	fmt.Printf("%s %d sources\n", styles.Muted.Render("Correlated:"), len(result.CorrelatedSources))
	fmt.Printf("%s %.1f%%\n\n", styles.Muted.Render("Confidence:"), result.CorrelationScore*100)

	for _, source := range result.CorrelatedSources {
		fmt.Printf("%s %s\n", styles.Info.Render("Source:"), source.Name)
		fmt.Printf("  %s %d events\n", styles.Muted.Render("Events:"), source.EventCount)
		fmt.Printf("  %s %.2f\n", styles.Muted.Render("Relevance:"), source.Relevance)
		fmt.Println()
	}

	if len(result.Insights) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Fusion Insights:"))
		for i, insight := range result.Insights {
			fmt.Printf("  %d. %s\n", i+1, insight)
		}
	}

	return nil
}

// ============================================================================
// FAST ML
// ============================================================================

var rtePredictCmd = &cobra.Command{
	Use:   "predict [data]",
	Short: "Fast ML prediction",
	Long:  `Execute rapid ML prediction for threat classification`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runRtePredict,
}

func runRtePredict(cmd *cobra.Command, args []string) error {
	client := rte.NewRTEClient(getRTEServer())
	req := &rte.PredictRequest{
		Data: args[0],
	}

	result, err := client.Predict(req)
	if err != nil {
		return fmt.Errorf("prediction failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Fast ML Prediction\n\n", styles.Accent.Render("🤖"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Prediction:"), result.Prediction)
	fmt.Printf("%s %.1f%%\n", styles.Muted.Render("Confidence:"), result.Confidence*100)
	fmt.Printf("%s %d ms\n\n", styles.Muted.Render("Inference Time:"), result.InferenceTime)

	if len(result.Features) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Top Features:"))
		for i, feature := range result.Features {
			fmt.Printf("  %d. %s: %.3f\n", i+1, feature.Name, feature.Importance)
		}
	}

	return nil
}

// ============================================================================
// HYPERSCAN MATCHER
// ============================================================================

var rteMatchCmd = &cobra.Command{
	Use:   "match [pattern]",
	Short: "Hyperscan pattern matching",
	Long:  `High-speed pattern detection using Hyperscan`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runRteMatch,
}

func runRteMatch(cmd *cobra.Command, args []string) error {
	client := rte.NewRTEClient(getRTEServer())
	req := &rte.MatchRequest{
		Pattern: args[0],
	}

	result, err := client.Match(req)
	if err != nil {
		return fmt.Errorf("pattern matching failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Hyperscan Pattern Match\n\n", styles.Accent.Render("🎯"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Pattern:"), result.Pattern)
	fmt.Printf("%s %d matches\n", styles.Muted.Render("Matches:"), len(result.Matches))
	fmt.Printf("%s %d μs\n\n", styles.Muted.Render("Scan Time:"), result.ScanTime)

	if len(result.Matches) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Matches:"))
		for i, match := range result.Matches {
			fmt.Printf("  %d. Position %d: %s\n", i+1, match.Position, match.Context)
		}
	}

	return nil
}

// ============================================================================
// PLAYBOOKS
// ============================================================================

var rtePlaybooksCmd = &cobra.Command{
	Use:   "playbooks",
	Short: "List available playbooks",
	Long:  `Display all real-time playbooks available for execution`,
	RunE:  runRtePlaybooks,
}

func runRtePlaybooks(cmd *cobra.Command, args []string) error {
	client := rte.NewRTEClient(getRTEServer())
	result, err := client.ListPlaybooks()
	if err != nil {
		return fmt.Errorf("failed to list playbooks: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s RTE Playbooks\n\n", styles.Accent.Render("📖"))
	fmt.Printf("%s %d playbooks\n\n", styles.Muted.Render("Total:"), len(result.Playbooks))

	for _, playbook := range result.Playbooks {
		fmt.Printf("%s %s\n", styles.Info.Render("Playbook:"), playbook.Name)
		fmt.Printf("  %s %s\n", styles.Muted.Render("Description:"), playbook.Description)
		fmt.Printf("  %s %d ms avg\n", styles.Muted.Render("Avg Execution:"), playbook.AvgExecTime)
		fmt.Printf("  %s %d times\n\n", styles.Muted.Render("Used:"), playbook.UsageCount)
	}

	return nil
}

// ============================================================================
// STATUS
// ============================================================================

var rteStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "RTE service status",
	Long:  `Display current RTE service health and statistics`,
	RunE:  runRteStatus,
}

func runRteStatus(cmd *cobra.Command, args []string) error {
	client := rte.NewRTEClient(getRTEServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s RTE Service Status\n\n", styles.Accent.Render("⚡"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %.1f ms avg\n", styles.Muted.Render("Response Time:"), result.AvgResponseTime)
	fmt.Printf("%s %d\n", styles.Muted.Render("Triages Executed:"), result.TriagesExecuted)
	fmt.Printf("%s %d\n", styles.Muted.Render("Active Playbooks:"), result.ActivePlaybooks)

	if len(result.ComponentHealth) > 0 {
		fmt.Printf("\n%s\n", styles.Info.Render("Component Health:"))
		for _, comp := range result.ComponentHealth {
			fmt.Printf("  %s %s\n", getStatusIcon(comp.Status), comp.Name)
		}
	}

	return nil
}

// ============================================================================
// HELPERS
// ============================================================================

func getRTEServer() string {
	if rteServer != "" {
		return rteServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(rteCmd)

	// Triage
	rteCmd.AddCommand(rteTriageCmd)

	// Fusion engine
	rteCmd.AddCommand(rteFusionCmd)
	rteFusionCmd.AddCommand(rteFusionCorrelateCmd)

	// Fast ML
	rteCmd.AddCommand(rtePredictCmd)

	// Hyperscan
	rteCmd.AddCommand(rteMatchCmd)

	// Playbooks
	rteCmd.AddCommand(rtePlaybooksCmd)

	// Status
	rteCmd.AddCommand(rteStatusCmd)

	// Flags
	rteCmd.PersistentFlags().StringVarP(&rteServer, "server", "s", "", "RTE server endpoint")

	rteTriageCmd.Flags().StringVar(&rtePlaybook, "playbook", "auto", "Playbook to use")
	rteTriageCmd.Flags().BoolVar(&rteAuto, "auto", false, "Enable automatic response")
}
