package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/nis"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	nisServer      string
	nisService     string
	nisMetric      string
	nisType        string
	nisFocus       string
	nisThreshold   float64
	nisShowBaseline bool
)

var nisCmd = &cobra.Command{
	Use:   "nis",
	Short: "Narrative Intelligence Service - AI-powered metric narratives",
	Long: `NIS (Narrative Intelligence Service) generates human-readable narratives
from system metrics and observability data using Claude AI. Features include
narrative generation, statistical anomaly detection, and cost management.`,
}

// ============================================================================
// NARRATIVE GENERATION
// ============================================================================

var nisNarrativeCmd = &cobra.Command{
	Use:   "narrative",
	Short: "Generate narratives from metrics",
	Long:  `AI-powered narrative creation from observability data`,
}

var nisNarrativeGenerateCmd = &cobra.Command{
	Use:   "generate [service]",
	Short: "Generate narrative for a service",
	Long:  `Generate AI-powered narrative for service metrics`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runNisNarrativeGenerate,
}

func runNisNarrativeGenerate(cmd *cobra.Command, args []string) error {
	client := nis.NewNISClient(getNISServer())
	req := &nis.NarrativeRequest{
		Service: args[0],
		Type:    nisType,
		Focus:   nisFocus,
	}

	result, err := client.GenerateNarrative(req)
	if err != nil {
		return fmt.Errorf("narrative generation failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Narrative - %s\n\n", styles.Accent.Render("📖"), result.Service)
	fmt.Printf("%s %s\n", styles.Muted.Render("Type:"), result.Type)
	fmt.Printf("%s $%.4f\n", styles.Muted.Render("Cost:"), result.Cost)
	fmt.Printf("%s %d ms\n\n", styles.Muted.Render("Generation Time:"), result.GenerationTime)

	fmt.Printf("%s\n", styles.Info.Render("Narrative:"))
	fmt.Printf("%s\n\n", result.Narrative)

	if len(result.KeyInsights) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Key Insights:"))
		for i, insight := range result.KeyInsights {
			fmt.Printf("  %d. %s\n", i+1, insight)
		}
		fmt.Println()
	}

	if len(result.Recommendations) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Recommendations:"))
		for i, rec := range result.Recommendations {
			fmt.Printf("  %d. %s\n", i+1, rec)
		}
	}

	return nil
}

var nisNarrativeListCmd = &cobra.Command{
	Use:   "list",
	Short: "List recent narratives",
	Long:  `Display recently generated narratives`,
	RunE:  runNisNarrativeList,
}

func runNisNarrativeList(cmd *cobra.Command, args []string) error {
	client := nis.NewNISClient(getNISServer())
	result, err := client.ListNarratives()
	if err != nil {
		return fmt.Errorf("failed to list narratives: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Recent Narratives\n\n", styles.Accent.Render("📚"))
	fmt.Printf("%s %d narratives\n\n", styles.Muted.Render("Total:"), len(result.Narratives))

	for i, narrative := range result.Narratives {
		fmt.Printf("%s %s - %s\n", styles.Info.Render(fmt.Sprintf("#%d", i+1)), narrative.Service, narrative.Type)
		fmt.Printf("  %s %s\n", styles.Muted.Render("Generated:"), narrative.Timestamp)
		fmt.Printf("  %s $%.4f\n", styles.Muted.Render("Cost:"), narrative.Cost)
		fmt.Printf("  %s %s...\n\n", styles.Muted.Render("Preview:"), truncate(narrative.Preview, 80))
	}

	return nil
}

// ============================================================================
// ANOMALY DETECTION
// ============================================================================

var nisAnomalyCmd = &cobra.Command{
	Use:   "anomaly",
	Short: "Statistical anomaly detection",
	Long:  `Z-score based anomaly detection for metrics`,
}

var nisAnomalyDetectCmd = &cobra.Command{
	Use:   "detect [service]",
	Short: "Detect anomalies in service metrics",
	Long:  `Run Z-score based anomaly detection (3-sigma rule)`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runNisAnomalyDetect,
}

func runNisAnomalyDetect(cmd *cobra.Command, args []string) error {
	client := nis.NewNISClient(getNISServer())
	req := &nis.AnomalyRequest{
		Service:   args[0],
		Metric:    nisMetric,
		Threshold: nisThreshold,
	}

	result, err := client.DetectAnomalies(req)
	if err != nil {
		return fmt.Errorf("anomaly detection failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Anomaly Detection - %s\n\n", styles.Accent.Render("🔍"), result.Service)
	fmt.Printf("%s %d anomalies found\n", styles.Muted.Render("Total:"), len(result.Anomalies))
	fmt.Printf("%s %.2f (σ=%.2f)\n\n", styles.Muted.Render("Baseline:"), result.Baseline, result.StdDev)

	if len(result.Anomalies) == 0 {
		fmt.Printf("%s No anomalies detected\n", getStatusIcon("ok"))
		return nil
	}

	for _, anomaly := range result.Anomalies {
		var severity string
		if anomaly.Severity == "critical" {
			severity = "🔴"
		} else if anomaly.Severity == "warning" {
			severity = "🟠"
		} else {
			severity = "🟢"
		}
		fmt.Printf("%s %s - %s\n", severity, anomaly.Timestamp, anomaly.Metric)
		fmt.Printf("  %s %.2f (baseline: %.2f)\n", styles.Muted.Render("Value:"), anomaly.Value, result.Baseline)
		fmt.Printf("  %s %.2fσ (%s)\n", styles.Muted.Render("Deviation:"), anomaly.ZScore, anomaly.Severity)
		fmt.Println()
	}

	return nil
}

var nisAnomalyBaselineCmd = &cobra.Command{
	Use:   "baseline [service]",
	Short: "Show baseline statistics",
	Long:  `Display rolling baseline statistics for a service`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runNisAnomalyBaseline,
}

func runNisAnomalyBaseline(cmd *cobra.Command, args []string) error {
	client := nis.NewNISClient(getNISServer())
	req := &nis.BaselineRequest{
		Service: args[0],
		Metric:  nisMetric,
	}

	result, err := client.GetBaseline(req)
	if err != nil {
		return fmt.Errorf("failed to get baseline: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Baseline Statistics - %s\n\n", styles.Accent.Render("📊"), result.Service)

	for _, baseline := range result.Baselines {
		fmt.Printf("%s %s\n", styles.Info.Render("Metric:"), baseline.Metric)
		fmt.Printf("  %s %.2f\n", styles.Muted.Render("Mean:"), baseline.Mean)
		fmt.Printf("  %s %.2f\n", styles.Muted.Render("Std Dev:"), baseline.StdDev)
		fmt.Printf("  %s %d samples\n", styles.Muted.Render("Window:"), baseline.WindowSize)
		fmt.Printf("  %s %s\n\n", styles.Muted.Render("Last Updated:"), baseline.LastUpdate)
	}

	return nil
}

// ============================================================================
// COST MANAGEMENT
// ============================================================================

var nisCostCmd = &cobra.Command{
	Use:   "cost",
	Short: "Cost tracking and budgets",
	Long:  `Monitor API costs and budget utilization`,
}

var nisCostStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Current cost status",
	Long:  `Display current cost tracking and budget status`,
	RunE:  runNisCostStatus,
}

func runNisCostStatus(cmd *cobra.Command, args []string) error {
	client := nis.NewNISClient(getNISServer())
	result, err := client.GetCostStatus()
	if err != nil {
		return fmt.Errorf("failed to get cost status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Cost Status\n\n", styles.Accent.Render("💰"))

	// Daily
	dailyPct := (result.DailySpent / result.DailyLimit) * 100
	fmt.Printf("%s\n", styles.Info.Render("Daily Budget:"))
	fmt.Printf("  %s $%.4f / $%.2f (%.1f%%)\n", styles.Muted.Render("Spent:"), result.DailySpent, result.DailyLimit, dailyPct)
	if dailyPct > 80 {
		fmt.Printf("  ⚠️  Warning: Approaching daily limit\n")
	}
	fmt.Println()

	// Monthly
	monthlyPct := (result.MonthlySpent / result.MonthlyLimit) * 100
	fmt.Printf("%s\n", styles.Info.Render("Monthly Budget:"))
	fmt.Printf("  %s $%.4f / $%.2f (%.1f%%)\n", styles.Muted.Render("Spent:"), result.MonthlySpent, result.MonthlyLimit, monthlyPct)
	if monthlyPct > 80 {
		fmt.Printf("  ⚠️  Warning: Approaching monthly limit\n")
	}
	fmt.Println()

	// Stats
	fmt.Printf("%s\n", styles.Info.Render("Statistics:"))
	fmt.Printf("  %s %d narratives\n", styles.Muted.Render("Total Requests:"), result.TotalRequests)
	fmt.Printf("  %s $%.6f\n", styles.Muted.Render("Avg Cost/Request:"), result.AvgCost)

	return nil
}

var nisCostHistoryCmd = &cobra.Command{
	Use:   "history",
	Short: "Cost history",
	Long:  `Display historical cost data`,
	RunE:  runNisCostHistory,
}

func runNisCostHistory(cmd *cobra.Command, args []string) error {
	client := nis.NewNISClient(getNISServer())
	result, err := client.GetCostHistory()
	if err != nil {
		return fmt.Errorf("failed to get cost history: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Cost History\n\n", styles.Accent.Render("📈"))

	for _, entry := range result.History {
		fmt.Printf("%s %s\n", styles.Info.Render("Date:"), entry.Date)
		fmt.Printf("  %s %d requests\n", styles.Muted.Render("Requests:"), entry.Requests)
		fmt.Printf("  %s $%.4f\n", styles.Muted.Render("Total Cost:"), entry.TotalCost)
		fmt.Printf("  %s $%.6f\n\n", styles.Muted.Render("Avg Cost:"), entry.AvgCost)
	}

	return nil
}

// ============================================================================
// RATE LIMITING
// ============================================================================

var nisRateLimitCmd = &cobra.Command{
	Use:   "ratelimit",
	Short: "Rate limit status",
	Long:  `Display current rate limit status`,
	RunE:  runNisRateLimit,
}

func runNisRateLimit(cmd *cobra.Command, args []string) error {
	client := nis.NewNISClient(getNISServer())
	result, err := client.GetRateLimit()
	if err != nil {
		return fmt.Errorf("failed to get rate limit: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Rate Limit Status\n\n", styles.Accent.Render("⏱️"))

	fmt.Printf("%s %d / %d (%.1f%%)\n", styles.Muted.Render("Hourly:"), result.HourlyUsed, result.HourlyLimit, float64(result.HourlyUsed)/float64(result.HourlyLimit)*100)
	fmt.Printf("%s %d / %d (%.1f%%)\n", styles.Muted.Render("Daily:"), result.DailyUsed, result.DailyLimit, float64(result.DailyUsed)/float64(result.DailyLimit)*100)
	fmt.Printf("%s %d seconds\n", styles.Muted.Render("Min Interval:"), result.MinInterval)

	if result.NextAvailable > 0 {
		fmt.Printf("\n⚠️  Rate limited. Next request available in %d seconds\n", result.NextAvailable)
	}

	return nil
}

// ============================================================================
// STATUS
// ============================================================================

var nisStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "NIS service status",
	Long:  `Display current NIS service health and statistics`,
	RunE:  runNisStatus,
}

func runNisStatus(cmd *cobra.Command, args []string) error {
	client := nis.NewNISClient(getNISServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s NIS Service Status\n\n", styles.Accent.Render("🚀"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %.1f%%\n", styles.Muted.Render("Health:"), result.Health)
	fmt.Printf("%s %d\n", styles.Muted.Render("Narratives Generated:"), result.NarrativesGenerated)
	fmt.Printf("%s %d\n", styles.Muted.Render("Anomalies Detected:"), result.AnomaliesDetected)
	fmt.Printf("%s $%.4f\n", styles.Muted.Render("Total Cost:"), result.TotalCost)

	return nil
}

// ============================================================================
// HELPERS
// ============================================================================

func getNISServer() string {
	if nisServer != "" {
		return nisServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(nisCmd)

	// Narrative operations
	nisCmd.AddCommand(nisNarrativeCmd)
	nisNarrativeCmd.AddCommand(nisNarrativeGenerateCmd)
	nisNarrativeCmd.AddCommand(nisNarrativeListCmd)

	// Anomaly detection
	nisCmd.AddCommand(nisAnomalyCmd)
	nisAnomalyCmd.AddCommand(nisAnomalyDetectCmd)
	nisAnomalyCmd.AddCommand(nisAnomalyBaselineCmd)

	// Cost management
	nisCmd.AddCommand(nisCostCmd)
	nisCostCmd.AddCommand(nisCostStatusCmd)
	nisCostCmd.AddCommand(nisCostHistoryCmd)

	// Rate limiting
	nisCmd.AddCommand(nisRateLimitCmd)

	// Status
	nisCmd.AddCommand(nisStatusCmd)

	// Flags
	nisCmd.PersistentFlags().StringVarP(&nisServer, "server", "s", "", "NIS server endpoint")

	nisNarrativeGenerateCmd.Flags().StringVar(&nisType, "type", "summary", "Narrative type (summary, detailed, alert)")
	nisNarrativeGenerateCmd.Flags().StringVar(&nisFocus, "focus", "", "Focus area for narrative")

	nisAnomalyDetectCmd.Flags().StringVarP(&nisMetric, "metric", "m", "", "Specific metric to analyze")
	nisAnomalyDetectCmd.Flags().Float64Var(&nisThreshold, "threshold", 3.0, "Z-score threshold (default: 3.0)")

	nisAnomalyBaselineCmd.Flags().StringVarP(&nisMetric, "metric", "m", "", "Specific metric")
}
