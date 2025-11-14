package cmd

import (
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/behavior"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Flags for behavioral commands
var (
	behaviorServer   string
	behaviorUser     string
	behaviorEntity   string
	behaviorNetwork  string
	behaviorPCAP     string
	behaviorTimerange string
	behaviorMode     string
	behaviorThreshold float64
)

// behaviorCmd represents the behavioral analysis command
var behaviorCmd = &cobra.Command{
	Use:   "behavior",
	Short: "Behavioral analysis and anomaly detection",
	Long: `Analyze behavioral patterns and detect anomalies across users, entities,
network traffic, and system activities.

The behavioral analysis system uses machine learning models to establish
baselines and identify deviations that may indicate threats, compromises,
or policy violations.

Components:
  analyze      - User/entity behavioral analysis
  bas          - Behavioral Analysis Service (BAS)
  mav          - Malicious Activity Vector detection
  traffic      - Network traffic analysis
  fabric       - Reactive fabric analysis

Examples:
  # Analyze user behavior
  vcli behavior analyze --user john.doe --timerange 24h

  # Detect entity anomalies
  vcli behavior bas detect-anomaly --entity server-web-01

  # Scan network for MAV
  vcli behavior mav scan --network 10.0.0.0/24

  # Analyze network traffic
  vcli behavior traffic analyze --pcap /data/capture.pcap

  # Check reactive fabric status
  vcli behavior fabric status
`,
}

// ============================================================================
// BEHAVIORAL ANALYSIS
// ============================================================================

var behaviorAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze user/entity behavior",
	Long: `Analyze behavioral patterns for users or entities over a specified timerange.

Compares current behavior against historical baselines to identify anomalies,
policy violations, or suspicious activities.`,
	Example: `  # Analyze user for last 24 hours
  vcli behavior analyze --user john.doe --timerange 24h

  # Analyze user with custom threshold
  vcli behavior analyze --user jane.smith --timerange 7d --threshold 0.8`,
	RunE: runBehaviorAnalyze,
}

func runBehaviorAnalyze(cmd *cobra.Command, args []string) error {
	client := behavior.NewAnalysisClient(getBehaviorServer())

	req := &behavior.AnalyzeRequest{
		User:      behaviorUser,
		Timerange: behaviorTimerange,
		Threshold: behaviorThreshold,
	}

	result, err := client.Analyze(req)
	if err != nil {
		return fmt.Errorf("failed to analyze behavior: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("📊 Behavioral Analysis Complete"))
	fmt.Printf("\nUser: %s\n", result.User)
	fmt.Printf("Timerange: %s\n", result.Timerange)
	fmt.Printf("Anomaly Score: %.2f\n", result.AnomalyScore)
	fmt.Printf("Risk Level: %s\n", getThreatLevelColor(result.RiskLevel, styles))

	if len(result.Anomalies) > 0 {
		fmt.Printf("\n%s:\n", styles.Success.Render("Detected Anomalies"))
		for _, anomaly := range result.Anomalies {
			fmt.Printf("  %s %s (confidence: %.2f)\n",
				getSeverityEmoji(anomaly.Severity),
				anomaly.Description,
				anomaly.Confidence,
			)
		}
	}

	return nil
}

// ============================================================================
// BAS (Behavioral Analysis Service)
// ============================================================================

var behaviorBASCmd = &cobra.Command{
	Use:   "bas",
	Short: "Behavioral Analysis Service operations",
	Long:  `BAS provides real-time behavioral anomaly detection for entities.`,
}

var behaviorBASDetectCmd = &cobra.Command{
	Use:   "detect-anomaly",
	Short: "Detect anomalies for entity",
	Long: `Detect behavioral anomalies for a specific entity (server, service, endpoint).

BAS continuously monitors entity behavior and alerts on deviations from
established patterns.`,
	Example: `  # Detect anomalies for web server
  vcli behavior bas detect-anomaly --entity server-web-01

  # Detect with mode
  vcli behavior bas detect-anomaly --entity database-01 --mode strict`,
	RunE: runBehaviorBASDetect,
}

func runBehaviorBASDetect(cmd *cobra.Command, args []string) error {
	client := behavior.NewBASClient(getBehaviorServer())

	req := &behavior.BASDetectRequest{
		Entity: behaviorEntity,
		Mode:   behaviorMode,
	}

	result, err := client.DetectAnomaly(req)
	if err != nil {
		return fmt.Errorf("failed to detect anomaly: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🔍 BAS Anomaly Detection"))
	fmt.Printf("\nEntity: %s\n", result.Entity)
	fmt.Printf("Status: %s\n", getStatusIcon(result.Status))
	fmt.Printf("Anomalies detected: %d\n", len(result.Anomalies))

	if len(result.Anomalies) > 0 {
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "\nTYPE\tSEVERITY\tCONFIDENCE\tTIMESTAMP\n")
		fmt.Fprintf(w, "----\t--------\t----------\t---------\n")

		for _, anomaly := range result.Anomalies {
			fmt.Fprintf(w, "%s\t%s\t%.2f\t%s\n",
				anomaly.Type,
				getSeverityEmoji(anomaly.Severity),
				anomaly.Confidence,
				anomaly.Timestamp.Format("15:04:05"),
			)
		}
		w.Flush()
	}

	return nil
}

// ============================================================================
// MAV (Malicious Activity Vector)
// ============================================================================

var behaviorMAVCmd = &cobra.Command{
	Use:   "mav",
	Short: "Malicious Activity Vector detection",
	Long:  `Detect Malicious Activity Vectors across network segments.`,
}

var behaviorMAVScanCmd = &cobra.Command{
	Use:   "scan",
	Short: "Scan network for MAV",
	Long: `Scan a network segment for Malicious Activity Vectors.

MAV detection identifies coordinated malicious behaviors across multiple
sources that may indicate advanced persistent threats or coordinated attacks.`,
	Example: `  # Scan network segment
  vcli behavior mav scan --network 10.0.0.0/24

  # Scan with mode
  vcli behavior mav scan --network 192.168.1.0/24 --mode deep`,
	RunE: runBehaviorMAVScan,
}

func runBehaviorMAVScan(cmd *cobra.Command, args []string) error {
	client := behavior.NewMAVClient(getBehaviorServer())

	req := &behavior.MAVScanRequest{
		Network: behaviorNetwork,
		Mode:    behaviorMode,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🔎 Scanning network for MAV..."))

	result, err := client.Scan(req)
	if err != nil {
		return fmt.Errorf("failed to scan for MAV: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ MAV Scan Complete"))
	fmt.Printf("\nNetwork: %s\n", result.Network)
	fmt.Printf("Hosts scanned: %d\n", result.HostsScanned)
	fmt.Printf("Vectors detected: %d\n", len(result.Vectors))

	if len(result.Vectors) > 0 {
		fmt.Printf("\n%s:\n", styles.Warning.Render("Detected MAV"))
		for _, vector := range result.Vectors {
			fmt.Printf("  %s %s - %s (severity: %d/10)\n",
				getSeverityEmoji(vector.Severity),
				vector.Type,
				vector.Source,
				vector.Severity,
			)
		}
	}

	return nil
}

// ============================================================================
// TRAFFIC ANALYSIS
// ============================================================================

var behaviorTrafficCmd = &cobra.Command{
	Use:   "traffic",
	Short: "Network traffic behavioral analysis",
	Long:  `Analyze network traffic patterns for behavioral anomalies.`,
}

var behaviorTrafficAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze network traffic",
	Long: `Analyze PCAP files or live traffic for behavioral anomalies.

Traffic analysis examines packet-level data to identify unusual patterns,
data exfiltration attempts, command-and-control traffic, and other threats.`,
	Example: `  # Analyze PCAP file
  vcli behavior traffic analyze --pcap /data/capture.pcap

  # Analyze with mode
  vcli behavior traffic analyze --pcap traffic.pcap --mode deep`,
	RunE: runBehaviorTrafficAnalyze,
}

func runBehaviorTrafficAnalyze(cmd *cobra.Command, args []string) error {
	client := behavior.NewTrafficClient(getBehaviorServer())

	req := &behavior.TrafficAnalyzeRequest{
		PCAPPath: behaviorPCAP,
		Mode:     behaviorMode,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("📡 Analyzing traffic..."))

	result, err := client.Analyze(req)
	if err != nil {
		return fmt.Errorf("failed to analyze traffic: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Traffic Analysis Complete"))
	fmt.Printf("\nPackets analyzed: %d\n", result.PacketsAnalyzed)
	fmt.Printf("Flows identified: %d\n", result.FlowsIdentified)
	fmt.Printf("Anomalous flows: %d\n", len(result.AnomalousFlows))

	if len(result.AnomalousFlows) > 0 {
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintf(w, "\nSRC\tDST\tPROTO\tANOMALY\tSEVERITY\n")
		fmt.Fprintf(w, "---\t---\t-----\t-------\t--------\n")

		for _, flow := range result.AnomalousFlows {
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\n",
				flow.Source,
				flow.Destination,
				flow.Protocol,
				flow.AnomalyType,
				getSeverityEmoji(flow.Severity),
			)
		}
		w.Flush()
	}

	return nil
}

// ============================================================================
// REACTIVE FABRIC
// ============================================================================

var behaviorFabricCmd = &cobra.Command{
	Use:   "fabric",
	Short: "Reactive fabric operations",
	Long:  `Manage and monitor the reactive fabric analysis system.`,
}

var behaviorFabricStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get reactive fabric status",
	Long:  `Check the status of the reactive fabric analysis system.`,
	Example: `  vcli behavior fabric status`,
	RunE: runBehaviorFabricStatus,
}

func runBehaviorFabricStatus(cmd *cobra.Command, args []string) error {
	client := behavior.NewFabricClient(getBehaviorServer())

	status, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get fabric status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🕸️  Reactive Fabric Status"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nCOMPONENT\tSTATUS\tACTIVE RULES\tEVENTS/SEC\n")
	fmt.Fprintf(w, "---------\t------\t------------\t----------\n")

	for _, component := range status.Components {
		fmt.Fprintf(w, "%s\t%s\t%d\t%d\n",
			component.Name,
			getStatusIcon(component.Status),
			component.ActiveRules,
			component.EventsPerSecond,
		)
	}
	w.Flush()

	return nil
}

// ============================================================================
// HELPERS
// ============================================================================

func getBehaviorServer() string {
	if behaviorServer != "" {
		return behaviorServer
	}

	return config.GetEndpoint("behavior")
}
