package cmd

import (
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/hunting"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Flags for hunting commands
var (
	huntingServer    string
	huntingQuery     string
	huntingTimerange string
	huntingTarget    string
	huntingScope     string
	huntingConfidence float64
	huntingMode      string
)

// huntingCmd represents the prediction and threat hunting command
var huntingCmd = &cobra.Command{
	Use:   "hunting",
	Short: "Threat hunting and prediction operations",
	Long: `Advanced threat hunting, APT prediction, anomaly forecasting, and attack surface analysis.

The hunting system provides proactive threat detection capabilities including
APT prediction, threat hunting operations, anomaly prediction, and attack surface mapping.

Components:
  apt          - APT prediction and detection
  hunt         - Threat hunting operations
  predict      - Anomaly prediction
  surface      - Attack surface analysis

Examples:
  # Predict APT threats
  vcli hunting apt predict --target organization

  # Start threat hunt
  vcli hunting hunt start --query "suspicious process behavior"

  # Predict anomalies
  vcli hunting predict --target network --timerange 24h

  # Analyze attack surface
  vcli hunting surface analyze --target infrastructure
`,
}

// ============================================================================
// APT PREDICTION
// ============================================================================

var huntingAPTCmd = &cobra.Command{
	Use:   "apt",
	Short: "APT prediction operations",
	Long:  `Predict Advanced Persistent Threat campaigns and tactics.`,
}

var huntingAPTPredictCmd = &cobra.Command{
	Use:   "predict",
	Short: "Predict APT threats",
	Long: `Use ML models to predict potential APT campaigns targeting the organization.

Analyzes historical patterns, threat intelligence, and environmental factors
to forecast likely APT threats.`,
	Example: `  # Predict APT threats
  vcli hunting apt predict --target organization

  # Predict with high confidence threshold
  vcli hunting apt predict --target infrastructure --confidence 0.8`,
	RunE: runHuntingAPTPredict,
}

func runHuntingAPTPredict(cmd *cobra.Command, args []string) error {
	client := hunting.NewHuntingClient(getHuntingServer())

	req := &hunting.APTPredictRequest{
		Target:     huntingTarget,
		Confidence: huntingConfidence,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🔮 Predicting APT threats..."))

	result, err := client.PredictAPT(req)
	if err != nil {
		return fmt.Errorf("failed to predict APT threats: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ APT Prediction Complete"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nTarget:\t%s\n", result.Target)
	fmt.Fprintf(w, "Prediction ID:\t%s\n", result.PredictionID)
	fmt.Fprintf(w, "Threats Predicted:\t%d\n", len(result.Threats))
	fmt.Fprintf(w, "Overall Risk:\t%s\n", getThreatLevelColor(result.OverallRisk, styles))
	w.Flush()

	if len(result.Threats) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Predicted APT Threats"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "ACTOR\tCAMPAIGN\tPROBABILITY\tTACTICS\n")
		fmt.Fprintf(w, "-----\t--------\t-----------\t-------\n")
		for _, threat := range result.Threats {
			fmt.Fprintf(w, "%s\t%s\t%.1f%%\t%s\n",
				threat.Actor,
				threat.Campaign,
				threat.Probability*100,
				threat.Tactics,
			)
		}
		w.Flush()
	}

	return nil
}

var huntingAPTProfileCmd = &cobra.Command{
	Use:   "profile",
	Short: "Profile APT actors",
	Long:  `Get detailed profile of known APT actors and their tactics.`,
	Example: `  # Profile APT actor
  vcli hunting apt profile --target APT29`,
	RunE: runHuntingAPTProfile,
}

func runHuntingAPTProfile(cmd *cobra.Command, args []string) error {
	client := hunting.NewHuntingClient(getHuntingServer())

	req := &hunting.APTProfileRequest{Actor: huntingTarget}

	result, err := client.ProfileAPT(req)
	if err != nil {
		return fmt.Errorf("failed to profile APT actor: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🎭 APT Actor Profile"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nActor:\t%s\n", result.Actor)
	fmt.Fprintf(w, "Aliases:\t%s\n", result.Aliases)
	fmt.Fprintf(w, "Origin:\t%s\n", result.Origin)
	fmt.Fprintf(w, "Active Since:\t%s\n", result.ActiveSince)
	fmt.Fprintf(w, "Sophistication:\t%s\n", result.Sophistication)
	w.Flush()

	if len(result.KnownTactics) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Known Tactics (MITRE ATT&CK)"))
		for _, tactic := range result.KnownTactics {
			fmt.Printf("  • %s: %s\n", tactic.ID, tactic.Description)
		}
	}

	if len(result.TargetedSectors) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Targeted Sectors"))
		for _, sector := range result.TargetedSectors {
			fmt.Printf("  • %s\n", sector)
		}
	}

	return nil
}

// ============================================================================
// THREAT HUNTING
// ============================================================================

var huntingHuntCmd = &cobra.Command{
	Use:   "hunt",
	Short: "Threat hunting operations",
	Long:  `Proactive threat hunting to find hidden threats in the environment.`,
}

var huntingHuntStartCmd = &cobra.Command{
	Use:   "start",
	Short: "Start threat hunt",
	Long: `Start a new threat hunting operation based on hypothesis or indicators.

Hunts can use queries, IOCs, behavioral patterns, or custom hypotheses.`,
	Example: `  # Start hunt with query
  vcli hunting hunt start --query "suspicious process behavior"

  # Start hunt with timerange
  vcli hunting hunt start --query "lateral movement" --timerange 7d`,
	RunE: runHuntingHuntStart,
}

func runHuntingHuntStart(cmd *cobra.Command, args []string) error {
	client := hunting.NewHuntingClient(getHuntingServer())

	req := &hunting.HuntStartRequest{
		Query:     huntingQuery,
		Timerange: huntingTimerange,
		Scope:     huntingScope,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🎯 Starting threat hunt..."))

	result, err := client.StartHunt(req)
	if err != nil {
		return fmt.Errorf("failed to start hunt: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Threat Hunt Started"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nHunt ID:\t%s\n", result.HuntID)
	fmt.Fprintf(w, "Query:\t%s\n", result.Query)
	fmt.Fprintf(w, "Scope:\t%s\n", result.Scope)
	fmt.Fprintf(w, "Status:\t%s\n", getStatusIcon(result.Status))
	fmt.Fprintf(w, "Progress:\t%.1f%%\n", result.Progress)
	w.Flush()

	if len(result.InitialFindings) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Initial Findings"))
		for _, finding := range result.InitialFindings {
			fmt.Printf("  • %s (severity: %d/10)\n", finding.Description, finding.Severity)
		}
	}

	return nil
}

var huntingHuntResultsCmd = &cobra.Command{
	Use:   "results <hunt_id>",
	Short: "Get hunt results",
	Long:  `Retrieve results from a completed or in-progress threat hunt.`,
	Args:  cobra.ExactArgs(1),
	Example: `  # Get hunt results
  vcli hunting hunt results hunt_20250113001`,
	RunE: runHuntingHuntResults,
}

func runHuntingHuntResults(cmd *cobra.Command, args []string) error {
	client := hunting.NewHuntingClient(getHuntingServer())

	result, err := client.GetHuntResults(args[0])
	if err != nil {
		return fmt.Errorf("failed to get hunt results: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🎯 Threat Hunt Results"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nHunt ID:\t%s\n", result.HuntID)
	fmt.Fprintf(w, "Status:\t%s\n", getStatusIcon(result.Status))
	fmt.Fprintf(w, "Total Findings:\t%d\n", len(result.Findings))
	fmt.Fprintf(w, "High Severity:\t%d\n", result.HighSeverityCount)
	w.Flush()

	if len(result.Findings) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Findings"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "TYPE\tDESCRIPTION\tSEVERITY\tCONFIDENCE\n")
		fmt.Fprintf(w, "----\t-----------\t--------\t----------\n")
		for _, finding := range result.Findings {
			fmt.Fprintf(w, "%s\t%s\t%s\t%.2f\n",
				finding.Type,
				finding.Description,
				getSeverityEmoji(finding.Severity),
				finding.Confidence,
			)
		}
		w.Flush()
	}

	return nil
}

// ============================================================================
// ANOMALY PREDICTION
// ============================================================================

var huntingPredictCmd = &cobra.Command{
	Use:   "predict",
	Short: "Anomaly prediction",
	Long: `Predict future anomalies based on historical patterns and trends.

Uses time-series analysis and ML to forecast likely anomalies.`,
	Example: `  # Predict network anomalies
  vcli hunting predict --target network --timerange 24h

  # Predict with specific mode
  vcli hunting predict --target system --mode advanced`,
	RunE: runHuntingPredict,
}

func runHuntingPredict(cmd *cobra.Command, args []string) error {
	client := hunting.NewHuntingClient(getHuntingServer())

	req := &hunting.AnomalyPredictRequest{
		Target:    huntingTarget,
		Timerange: huntingTimerange,
		Mode:      huntingMode,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("📊 Predicting anomalies..."))

	result, err := client.PredictAnomaly(req)
	if err != nil {
		return fmt.Errorf("failed to predict anomalies: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Anomaly Prediction Complete"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nTarget:\t%s\n", result.Target)
	fmt.Fprintf(w, "Prediction Horizon:\t%s\n", result.PredictionHorizon)
	fmt.Fprintf(w, "Model Confidence:\t%.1f%%\n", result.ModelConfidence)
	fmt.Fprintf(w, "Predicted Anomalies:\t%d\n", len(result.Predictions))
	w.Flush()

	if len(result.Predictions) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Predicted Anomalies"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "TIME WINDOW\tTYPE\tPROBABILITY\tIMPACT\n")
		fmt.Fprintf(w, "-----------\t----\t-----------\t------\n")
		for _, pred := range result.Predictions {
			fmt.Fprintf(w, "%s\t%s\t%.1f%%\t%s\n",
				pred.TimeWindow,
				pred.Type,
				pred.Probability*100,
				pred.Impact,
			)
		}
		w.Flush()
	}

	return nil
}

// ============================================================================
// ATTACK SURFACE ANALYSIS
// ============================================================================

var huntingSurfaceCmd = &cobra.Command{
	Use:   "surface",
	Short: "Attack surface analysis",
	Long:  `Analyze and map the organization's attack surface.`,
}

var huntingSurfaceAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze attack surface",
	Long: `Perform comprehensive attack surface analysis to identify exposure points.

Maps external and internal attack surface including services, APIs, and assets.`,
	Example: `  # Analyze attack surface
  vcli hunting surface analyze --target infrastructure

  # Deep analysis with scope
  vcli hunting surface analyze --target external --scope internet-facing`,
	RunE: runHuntingSurfaceAnalyze,
}

func runHuntingSurfaceAnalyze(cmd *cobra.Command, args []string) error {
	client := hunting.NewHuntingClient(getHuntingServer())

	req := &hunting.SurfaceAnalyzeRequest{
		Target: huntingTarget,
		Scope:  huntingScope,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🗺️  Analyzing attack surface..."))

	result, err := client.AnalyzeSurface(req)
	if err != nil {
		return fmt.Errorf("failed to analyze attack surface: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Attack Surface Analysis Complete"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nTarget:\t%s\n", result.Target)
	fmt.Fprintf(w, "Scope:\t%s\n", result.Scope)
	fmt.Fprintf(w, "Total Assets:\t%d\n", result.TotalAssets)
	fmt.Fprintf(w, "Exposed Services:\t%d\n", result.ExposedServices)
	fmt.Fprintf(w, "Risk Score:\t%.1f/10\n", result.RiskScore)
	w.Flush()

	if len(result.ExposurePoints) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Exposure Points"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "ASSET\tTYPE\tEXPOSURE\tRISK\n")
		fmt.Fprintf(w, "-----\t----\t--------\t----\n")
		for _, exp := range result.ExposurePoints {
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
				exp.Asset,
				exp.Type,
				exp.Exposure,
				getThreatLevelColor(exp.RiskLevel, styles),
			)
		}
		w.Flush()
	}

	if len(result.Recommendations) > 0 {
		fmt.Printf("\n%s:\n", styles.Info.Render("Recommendations"))
		for i, rec := range result.Recommendations {
			fmt.Printf("%d. %s\n", i+1, rec)
		}
	}

	return nil
}

var huntingSurfaceMapCmd = &cobra.Command{
	Use:   "map",
	Short: "Map attack surface",
	Long:  `Generate visual map of the attack surface.`,
	Example: `  # Generate attack surface map
  vcli hunting surface map --target infrastructure`,
	RunE: runHuntingSurfaceMap,
}

func runHuntingSurfaceMap(cmd *cobra.Command, args []string) error {
	client := hunting.NewHuntingClient(getHuntingServer())

	req := &hunting.SurfaceMapRequest{Target: huntingTarget}

	result, err := client.MapSurface(req)
	if err != nil {
		return fmt.Errorf("failed to map attack surface: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🗺️  Attack Surface Map"))

	fmt.Printf("\nMap ID: %s\n", result.MapID)
	fmt.Printf("Nodes: %d\n", result.Nodes)
	fmt.Printf("Edges: %d\n", result.Edges)
	fmt.Printf("Critical Paths: %d\n", result.CriticalPaths)

	fmt.Printf("\n%s\n", styles.Info.Render("Map visualization available at:"))
	fmt.Printf("%s\n", result.VisualizationURL)

	return nil
}

// ============================================================================
// HELPERS
// ============================================================================

func getHuntingServer() string {
	if huntingServer != "" {
		return huntingServer
	}

	return config.GetEndpoint("hunting")
}
