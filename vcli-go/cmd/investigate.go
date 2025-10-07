package main

import (
	"encoding/json"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/investigation"
)

// investigateCmd represents the investigate command group
var investigateCmd = &cobra.Command{
	Use:   "investigate",
	Short: "Investigation and reconnaissance operations",
	Long: `Investigation and reconnaissance operations including:
- Autonomous Investigation: Threat actor profiling, incident attribution, campaign correlation
- Network Reconnaissance: Active network scanning and enumeration
- OSINT: Open-source intelligence gathering and analysis`,
}

// ============================================================================
// AUTONOMOUS INVESTIGATION COMMANDS
// ============================================================================

var autonomousCmd = &cobra.Command{
	Use:   "autonomous",
	Short: "Autonomous Investigation Service operations",
	Long:  "Threat actor profiling, incident attribution, and autonomous investigations",
}

var autonomousRegisterActorCmd = &cobra.Command{
	Use:   "register-actor",
	Short: "Register a new threat actor profile",
	Long:  "Register a new threat actor with known TTPs, infrastructure, and characteristics",
	RunE:  runAutonomousRegisterActor,
}

var autonomousGetActorCmd = &cobra.Command{
	Use:   "get-actor <actor_id>",
	Short: "Retrieve a threat actor profile",
	Long:  "Get detailed information about a specific threat actor",
	Args:  cobra.ExactArgs(1),
	RunE:  runAutonomousGetActor,
}

var autonomousListActorsCmd = &cobra.Command{
	Use:   "list-actors",
	Short: "List all known threat actors",
	Long:  "List all registered threat actors with optional filtering",
	RunE:  runAutonomousListActors,
}

var autonomousIngestIncidentCmd = &cobra.Command{
	Use:   "ingest-incident",
	Short: "Ingest a new security incident",
	Long:  "Ingest a security incident for analysis and attribution",
	RunE:  runAutonomousIngestIncident,
}

var autonomousAttributeIncidentCmd = &cobra.Command{
	Use:   "attribute-incident <incident_id>",
	Short: "Attribute an incident to threat actors",
	Long:  "Perform attribution analysis to identify likely threat actors",
	Args:  cobra.ExactArgs(1),
	RunE:  runAutonomousAttributeIncident,
}

var autonomousCorrelateCampaignsCmd = &cobra.Command{
	Use:   "correlate-campaigns",
	Short: "Correlate incidents into campaigns",
	Long:  "Correlate multiple incidents to identify attack campaigns",
	RunE:  runAutonomousCorrelateCampaigns,
}

var autonomousGetCampaignCmd = &cobra.Command{
	Use:   "get-campaign <campaign_id>",
	Short: "Retrieve campaign details",
	Long:  "Get detailed information about a specific attack campaign",
	Args:  cobra.ExactArgs(1),
	RunE:  runAutonomousGetCampaign,
}

var autonomousListCampaignsCmd = &cobra.Command{
	Use:   "list-campaigns",
	Short: "List all known campaigns",
	Long:  "List all identified attack campaigns",
	RunE:  runAutonomousListCampaigns,
}

var autonomousInitiateCmd = &cobra.Command{
	Use:   "initiate",
	Short: "Initiate an autonomous investigation",
	Long:  "Start an autonomous investigation with specific parameters",
	RunE:  runAutonomousInitiate,
}

var autonomousGetInvestigationCmd = &cobra.Command{
	Use:   "get-investigation <investigation_id>",
	Short: "Get investigation status and results",
	Long:  "Retrieve the status and results of an autonomous investigation",
	Args:  cobra.ExactArgs(1),
	RunE:  runAutonomousGetInvestigation,
}

var autonomousStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get service status",
	Long:  "Get detailed status of the Autonomous Investigation service",
	RunE:  runAutonomousStatus,
}

var autonomousHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check service health",
	Long:  "Perform health check on the Autonomous Investigation service",
	RunE:  runAutonomousHealth,
}

// ============================================================================
// NETWORK RECONNAISSANCE COMMANDS
// ============================================================================

var reconCmd = &cobra.Command{
	Use:   "recon",
	Short: "Network Reconnaissance Service operations",
	Long:  "Active network scanning and enumeration",
}

var reconStartCmd = &cobra.Command{
	Use:   "start",
	Short: "Start a network reconnaissance task",
	Long:  "Initiate a new network scan (nmap, masscan, etc.)",
	RunE:  runReconStart,
}

var reconStatusCmd = &cobra.Command{
	Use:   "status <task_id>",
	Short: "Get reconnaissance task status",
	Long:  "Retrieve the current status of a reconnaissance task",
	Args:  cobra.ExactArgs(1),
	RunE:  runReconStatus,
}

var reconResultsCmd = &cobra.Command{
	Use:   "results <task_id>",
	Short: "Get reconnaissance task results",
	Long:  "Retrieve the results of a completed reconnaissance task",
	Args:  cobra.ExactArgs(1),
	RunE:  runReconResults,
}

var reconMetricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Get reconnaissance metrics",
	Long:  "Retrieve operational metrics for the reconnaissance service",
	RunE:  runReconMetrics,
}

var reconHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check service health",
	Long:  "Perform health check on the Network Reconnaissance service",
	RunE:  runReconHealth,
}

// ============================================================================
// OSINT COMMANDS
// ============================================================================

var osintCmd = &cobra.Command{
	Use:   "osint",
	Short: "OSINT Service operations",
	Long:  "Open-source intelligence gathering and analysis",
}

var osintStartCmd = &cobra.Command{
	Use:   "start",
	Short: "Start an OSINT investigation",
	Long:  "Initiate a new OSINT investigation (person recon, domain analysis, etc.)",
	RunE:  runOSINTStart,
}

var osintStatusCmd = &cobra.Command{
	Use:   "status <investigation_id>",
	Short: "Get OSINT investigation status",
	Long:  "Retrieve the current status of an OSINT investigation",
	Args:  cobra.ExactArgs(1),
	RunE:  runOSINTStatus,
}

var osintReportCmd = &cobra.Command{
	Use:   "report <investigation_id>",
	Short: "Get OSINT investigation report",
	Long:  "Retrieve the final report of a completed OSINT investigation",
	Args:  cobra.ExactArgs(1),
	RunE:  runOSINTReport,
}

var osintHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check service health",
	Long:  "Perform health check on the OSINT service",
	RunE:  runOSINTHealth,
}

// ============================================================================
// GLOBAL FLAGS
// ============================================================================

var (
	// Investigation service endpoints
	autonomousEndpoint string
	reconEndpoint      string
	osintEndpoint      string
	investigateToken   string

	// Autonomous Investigation flags
	actorFile           string
	incidentFile        string
	investigateTarget   string
	investigateScope    string
	filterFile          string
	thresholdFloat      float64
	timeWindowStr       string

	// Network Recon flags
	reconTarget     string
	reconScanType   string
	reconParamsFile string

	// OSINT flags
	osintQuery      string
	osintType       string
	osintParamsFile string
)

func init() {
	rootCmd.AddCommand(investigateCmd)

	// Add subcommand groups
	investigateCmd.AddCommand(autonomousCmd)
	investigateCmd.AddCommand(reconCmd)
	investigateCmd.AddCommand(osintCmd)

	// Autonomous Investigation subcommands
	autonomousCmd.AddCommand(autonomousRegisterActorCmd)
	autonomousCmd.AddCommand(autonomousGetActorCmd)
	autonomousCmd.AddCommand(autonomousListActorsCmd)
	autonomousCmd.AddCommand(autonomousIngestIncidentCmd)
	autonomousCmd.AddCommand(autonomousAttributeIncidentCmd)
	autonomousCmd.AddCommand(autonomousCorrelateCampaignsCmd)
	autonomousCmd.AddCommand(autonomousGetCampaignCmd)
	autonomousCmd.AddCommand(autonomousListCampaignsCmd)
	autonomousCmd.AddCommand(autonomousInitiateCmd)
	autonomousCmd.AddCommand(autonomousGetInvestigationCmd)
	autonomousCmd.AddCommand(autonomousStatusCmd)
	autonomousCmd.AddCommand(autonomousHealthCmd)

	// Network Recon subcommands
	reconCmd.AddCommand(reconStartCmd)
	reconCmd.AddCommand(reconStatusCmd)
	reconCmd.AddCommand(reconResultsCmd)
	reconCmd.AddCommand(reconMetricsCmd)
	reconCmd.AddCommand(reconHealthCmd)

	// OSINT subcommands
	osintCmd.AddCommand(osintStartCmd)
	osintCmd.AddCommand(osintStatusCmd)
	osintCmd.AddCommand(osintReportCmd)
	osintCmd.AddCommand(osintHealthCmd)

	// Autonomous Investigation flags
	autonomousRegisterActorCmd.Flags().StringVar(&actorFile, "actor-file", "", "Path to JSON file with actor profile")
	autonomousRegisterActorCmd.MarkFlagRequired("actor-file")

	autonomousListActorsCmd.Flags().StringVar(&filterFile, "filter-file", "", "Path to JSON file with filter criteria")

	autonomousIngestIncidentCmd.Flags().StringVar(&incidentFile, "incident-file", "", "Path to JSON file with incident data")
	autonomousIngestIncidentCmd.MarkFlagRequired("incident-file")

	autonomousCorrelateCampaignsCmd.Flags().Float64Var(&thresholdFloat, "threshold", 0.7, "Correlation threshold (0.0-1.0)")
	autonomousCorrelateCampaignsCmd.Flags().StringVar(&timeWindowStr, "time-window", "30d", "Time window for correlation")

	autonomousInitiateCmd.Flags().StringVar(&investigateTarget, "target", "", "Investigation target")
	autonomousInitiateCmd.Flags().StringVar(&investigateScope, "scope", "", "Investigation scope")
	autonomousInitiateCmd.MarkFlagRequired("target")
	autonomousInitiateCmd.MarkFlagRequired("scope")

	// Network Recon flags
	reconStartCmd.Flags().StringVar(&reconTarget, "target", "", "Target for reconnaissance (IP, CIDR, domain)")
	reconStartCmd.Flags().StringVar(&reconScanType, "scan-type", "nmap_full", "Type of scan (nmap_full, masscan_ports)")
	reconStartCmd.Flags().StringVar(&reconParamsFile, "params-file", "", "Path to JSON file with scan parameters")
	reconStartCmd.MarkFlagRequired("target")

	// OSINT flags
	osintStartCmd.Flags().StringVar(&osintQuery, "query", "", "Query for investigation (username, email, domain)")
	osintStartCmd.Flags().StringVar(&osintType, "type", "person_recon", "Investigation type (person_recon, domain_analysis)")
	osintStartCmd.Flags().StringVar(&osintParamsFile, "params-file", "", "Path to JSON file with investigation parameters")
	osintStartCmd.MarkFlagRequired("query")

	// Service endpoints
	autonomousCmd.PersistentFlags().StringVar(&autonomousEndpoint, "autonomous-endpoint", "http://localhost:8035", "Autonomous Investigation service endpoint")
	reconCmd.PersistentFlags().StringVar(&reconEndpoint, "recon-endpoint", "http://localhost:8032", "Network Reconnaissance service endpoint")
	osintCmd.PersistentFlags().StringVar(&osintEndpoint, "osint-endpoint", "http://localhost:8036", "OSINT service endpoint")

	// Authentication token
	investigateCmd.PersistentFlags().StringVar(&investigateToken, "token", "", "Authentication token")
}

// ============================================================================
// AUTONOMOUS INVESTIGATION COMMAND IMPLEMENTATIONS
// ============================================================================

func runAutonomousRegisterActor(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	actorData, err := readJSONFile(actorFile)
	if err != nil {
		return fmt.Errorf("failed to read actor file: %w", err)
	}

	// Convert map to ThreatActorProfile struct
	var profile investigation.ThreatActorProfile
	jsonBytes, err := json.Marshal(actorData)
	if err != nil {
		return fmt.Errorf("failed to marshal actor data: %w", err)
	}
	if err := json.Unmarshal(jsonBytes, &profile); err != nil {
		return fmt.Errorf("failed to unmarshal actor profile: %w", err)
	}

	result, err := client.RegisterActor(profile)
	if err != nil {
		return fmt.Errorf("failed to register actor: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousGetActor(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.GetActor(args[0])
	if err != nil {
		return fmt.Errorf("failed to get actor: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousListActors(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.ListActors()
	if err != nil {
		return fmt.Errorf("failed to list actors: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousIngestIncident(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	incidentData, err := readJSONFile(incidentFile)
	if err != nil {
		return fmt.Errorf("failed to read incident file: %w", err)
	}

	result, err := client.IngestIncident(incidentData)
	if err != nil {
		return fmt.Errorf("failed to ingest incident: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousAttributeIncident(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.AttributeIncident(args[0])
	if err != nil {
		return fmt.Errorf("failed to attribute incident: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousCorrelateCampaigns(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.CorrelateCampaigns()
	if err != nil {
		return fmt.Errorf("failed to correlate campaigns: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousGetCampaign(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.GetCampaign(args[0])
	if err != nil {
		return fmt.Errorf("failed to get campaign: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousListCampaigns(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.ListCampaigns()
	if err != nil {
		return fmt.Errorf("failed to list campaigns: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousInitiate(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.InitiateInvestigation(investigateTarget, investigateScope)
	if err != nil {
		return fmt.Errorf("failed to initiate investigation: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousGetInvestigation(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.GetInvestigation(args[0])
	if err != nil {
		return fmt.Errorf("failed to get investigation: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousStatus(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	printJSON(result)
	return nil
}

func runAutonomousHealth(cmd *cobra.Command, args []string) error {
	client := investigation.NewAutonomousClient(autonomousEndpoint, investigateToken)

	result, err := client.Health()
	if err != nil {
		return fmt.Errorf("failed to check health: %w", err)
	}

	printJSON(result)
	return nil
}

// ============================================================================
// NETWORK RECONNAISSANCE COMMAND IMPLEMENTATIONS
// ============================================================================

func runReconStart(cmd *cobra.Command, args []string) error {
	client := investigation.NewReconClient(reconEndpoint, investigateToken)

	var params map[string]interface{}
	if reconParamsFile != "" {
		var err error
		params, err = readJSONFile(reconParamsFile)
		if err != nil {
			return fmt.Errorf("failed to read params file: %w", err)
		}
	}

	result, err := client.StartRecon(reconTarget, reconScanType, params)
	if err != nil {
		return fmt.Errorf("failed to start recon: %w", err)
	}

	printJSON(result)
	return nil
}

func runReconStatus(cmd *cobra.Command, args []string) error {
	client := investigation.NewReconClient(reconEndpoint, investigateToken)

	result, err := client.GetReconStatus(args[0])
	if err != nil {
		return fmt.Errorf("failed to get recon status: %w", err)
	}

	printJSON(result)
	return nil
}

func runReconResults(cmd *cobra.Command, args []string) error {
	client := investigation.NewReconClient(reconEndpoint, investigateToken)

	result, err := client.GetReconResults(args[0])
	if err != nil {
		return fmt.Errorf("failed to get recon results: %w", err)
	}

	printJSON(result)
	return nil
}

func runReconMetrics(cmd *cobra.Command, args []string) error {
	client := investigation.NewReconClient(reconEndpoint, investigateToken)

	result, err := client.GetMetrics()
	if err != nil {
		return fmt.Errorf("failed to get metrics: %w", err)
	}

	printJSON(result)
	return nil
}

func runReconHealth(cmd *cobra.Command, args []string) error {
	client := investigation.NewReconClient(reconEndpoint, investigateToken)

	result, err := client.Health()
	if err != nil {
		return fmt.Errorf("failed to check health: %w", err)
	}

	printJSON(result)
	return nil
}

// ============================================================================
// OSINT COMMAND IMPLEMENTATIONS
// ============================================================================

func runOSINTStart(cmd *cobra.Command, args []string) error {
	client := investigation.NewOSINTClient(osintEndpoint, investigateToken)

	var params map[string]interface{}
	if osintParamsFile != "" {
		var err error
		params, err = readJSONFile(osintParamsFile)
		if err != nil {
			return fmt.Errorf("failed to read params file: %w", err)
		}
	}

	result, err := client.StartInvestigation(osintQuery, osintType, params)
	if err != nil {
		return fmt.Errorf("failed to start OSINT investigation: %w", err)
	}

	printJSON(result)
	return nil
}

func runOSINTStatus(cmd *cobra.Command, args []string) error {
	client := investigation.NewOSINTClient(osintEndpoint, investigateToken)

	result, err := client.GetInvestigationStatus(args[0])
	if err != nil {
		return fmt.Errorf("failed to get OSINT investigation status: %w", err)
	}

	printJSON(result)
	return nil
}

func runOSINTReport(cmd *cobra.Command, args []string) error {
	client := investigation.NewOSINTClient(osintEndpoint, investigateToken)

	result, err := client.GetInvestigationReport(args[0])
	if err != nil {
		return fmt.Errorf("failed to get OSINT investigation report: %w", err)
	}

	printJSON(result)
	return nil
}

func runOSINTHealth(cmd *cobra.Command, args []string) error {
	client := investigation.NewOSINTClient(osintEndpoint, investigateToken)

	result, err := client.Health()
	if err != nil {
		return fmt.Errorf("failed to check health: %w", err)
	}

	printJSON(result)
	return nil
}
