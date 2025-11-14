package cmd

import (
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/offensive"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Flags for offensive commands
var (
	offensiveServer    string
	offensiveOutputFmt string
	offensiveTarget    string
	offensivePlaybook  string
	offensiveSample    string
	offensiveScenario  string
	offensiveTemplate  string
	offensiveTags      []string
	offensivePhase     string
	offensiveMode      string
	offensiveConfig    string
)

// offensiveCmd represents the offensive security command
var offensiveCmd = &cobra.Command{
	Use:   "offensive",
	Short: "Offensive security operations",
	Long: `Offensive security tools and workflows for authorized penetration testing,
red team operations, and security validation.

⚠️  CONSTITUTIONAL WARNING:
All offensive operations must comply with DOUTRINA VÉRTICE principles:
- Explicit authorization required
- Audit logging mandatory
- No destructive operations without approval
- Purple team coordination enforced

Services:
  tools         - Offensive security tools catalog
  c2            - Command & Control infrastructure
  social-eng    - Social engineering campaigns (authorized)
  malware       - Malware analysis and reverse engineering
  wargame       - Wargaming simulations
  gateway       - Offensive operations gateway
  orchestrator  - Multi-phase attack orchestration

Examples:
  # List available offensive tools
  vcli offensive tools list

  # Launch C2 infrastructure (simulation)
  vcli offensive c2 launch --target simulation-env

  # Run social engineering awareness campaign
  vcli offensive social-eng campaign --template phishing-awareness

  # Analyze malware sample
  vcli offensive malware analyze --sample /path/to/sample.exe

  # Start APT wargame scenario
  vcli offensive wargame start --scenario apt-simulation

  # Check offensive gateway status
  vcli offensive gateway status

  # Execute multi-phase attack workflow
  vcli offensive orchestrator workflow --playbook red-team-1
`,
}

// ============================================================================
// TOOLS
// ============================================================================

var offensiveToolsCmd = &cobra.Command{
	Use:   "tools",
	Short: "Offensive tools catalog",
	Long:  `Manage and execute offensive security tools from the catalog.`,
}

var offensiveToolsListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available offensive tools",
	Long: `List all offensive security tools available in the arsenal.

Tools are categorized by phase: reconnaissance, weaponization, delivery,
exploitation, installation, command-and-control, actions-on-objectives.`,
	Example: `  # List all tools
  vcli offensive tools list

  # List tools by phase
  vcli offensive tools list --phase reconnaissance`,
	RunE: runOffensiveToolsList,
}

func runOffensiveToolsList(cmd *cobra.Command, args []string) error {
	client := offensive.NewOffensiveClient(getOffensiveServer())

	req := &offensive.ToolsListRequest{
		Phase: offensivePhase,
	}

	tools, err := client.ListTools(req)
	if err != nil {
		return fmt.Errorf("failed to list offensive tools: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🛠️  Offensive Tools Arsenal"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nNAME\tPHASE\tCATEGORY\tAUTHORIZATION\n")
	fmt.Fprintf(w, "----\t-----\t--------\t-------------\n")

	for _, tool := range tools.Tools {
		authIcon := getAuthorizationIcon(tool.RequiresAuth)
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
			tool.Name,
			tool.Phase,
			tool.Category,
			authIcon,
		)
	}
	w.Flush()

	fmt.Printf("\n%s: %d tools\n", styles.Muted.Render("Total"), len(tools.Tools))
	return nil
}

// ============================================================================
// C2 (Command & Control)
// ============================================================================

var offensiveC2Cmd = &cobra.Command{
	Use:   "c2",
	Short: "Command & Control operations",
	Long:  `Manage C2 infrastructure for authorized penetration testing.`,
}

var offensiveC2LaunchCmd = &cobra.Command{
	Use:   "launch",
	Short: "Launch C2 infrastructure",
	Long: `Deploy C2 infrastructure in a controlled, sandboxed environment.

This operation creates isolated C2 listeners, payload generators, and
agent management interfaces for authorized red team engagements.`,
	Example: `  # Launch C2 in simulation environment
  vcli offensive c2 launch --target simulation-env

  # Launch with specific configuration
  vcli offensive c2 launch --target test-range --config c2-config.yaml`,
	RunE: runOffensiveC2Launch,
}

func runOffensiveC2Launch(cmd *cobra.Command, args []string) error {
	client := offensive.NewOffensiveClient(getOffensiveServer())

	req := &offensive.C2LaunchRequest{
		Target: offensiveTarget,
		Config: offensiveConfig,
	}

	// Constitutional AI check: Require explicit authorization
	if err := confirmAuthorization("Launch C2 infrastructure"); err != nil {
		return fmt.Errorf("operation cancelled: authorization required")
	}

	result, err := client.LaunchC2(req)
	if err != nil {
		return fmt.Errorf("failed to launch C2: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🎯 C2 Infrastructure Launched"))
	fmt.Printf("\nC2 Server: %s\n", result.ServerURL)
	fmt.Printf("Listeners: %d active\n", result.ActiveListeners)
	fmt.Printf("Access Token: %s\n", styles.Warning.Render(result.AccessToken))
	fmt.Printf("\n%s: This C2 instance is sandboxed and monitored.\n", styles.Muted.Render("Note"))

	return nil
}

// ============================================================================
// SOCIAL ENGINEERING
// ============================================================================

var offensiveSocialEngCmd = &cobra.Command{
	Use:   "social-eng",
	Short: "Social engineering operations",
	Long:  `Authorized social engineering campaigns for security awareness training.`,
}

var offensiveSocialEngCampaignCmd = &cobra.Command{
	Use:   "campaign",
	Short: "Launch social engineering campaign",
	Long: `Execute a social engineering awareness campaign using predefined templates.

Campaigns are designed for security awareness training and compliance testing.
All activities are logged and require explicit authorization.`,
	Example: `  # Launch phishing awareness campaign
  vcli offensive social-eng campaign --template phishing-awareness

  # Launch custom campaign
  vcli offensive social-eng campaign --template custom --config campaign.yaml`,
	RunE: runOffensiveSocialEngCampaign,
}

func runOffensiveSocialEngCampaign(cmd *cobra.Command, args []string) error {
	client := offensive.NewOffensiveClient(getOffensiveServer())

	req := &offensive.SocialEngCampaignRequest{
		Template: offensiveTemplate,
		Config:   offensiveConfig,
	}

	// Constitutional check
	if err := confirmAuthorization("Launch social engineering campaign"); err != nil {
		return fmt.Errorf("operation cancelled: authorization required")
	}

	result, err := client.LaunchSocialEngCampaign(req)
	if err != nil {
		return fmt.Errorf("failed to launch campaign: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("📧 Campaign Launched"))
	fmt.Printf("\nCampaign ID: %s\n", result.CampaignID)
	fmt.Printf("Template: %s\n", result.Template)
	fmt.Printf("Target users: %d\n", result.TargetCount)
	fmt.Printf("Expected duration: %s\n", result.Duration)

	return nil
}

// ============================================================================
// MALWARE ANALYSIS
// ============================================================================

var offensiveMalwareCmd = &cobra.Command{
	Use:   "malware",
	Short: "Malware analysis operations",
	Long:  `Analyze malware samples in sandboxed environment.`,
}

var offensiveMalwareAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze malware sample",
	Long: `Analyze a malware sample in an isolated sandbox environment.

The analysis includes static analysis, dynamic analysis, behavioral monitoring,
and network traffic inspection.`,
	Example: `  # Analyze malware sample
  vcli offensive malware analyze --sample /path/to/sample.exe

  # Analyze with full report
  vcli offensive malware analyze --sample sample.exe --mode full`,
	RunE: runOffensiveMalwareAnalyze,
}

func runOffensiveMalwareAnalyze(cmd *cobra.Command, args []string) error {
	client := offensive.NewOffensiveClient(getOffensiveServer())

	req := &offensive.MalwareAnalyzeRequest{
		SamplePath: offensiveSample,
		Mode:       offensiveMode,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🔬 Uploading sample to sandbox..."))

	result, err := client.AnalyzeMalware(req)
	if err != nil {
		return fmt.Errorf("failed to analyze malware: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("✅ Analysis Complete"))
	fmt.Printf("\nSample: %s\n", result.SampleHash)
	fmt.Printf("Threat Level: %s\n", getThreatLevelColor(result.ThreatLevel, styles))
	fmt.Printf("Family: %s\n", result.Family)
	fmt.Printf("IOCs detected: %d\n", len(result.IOCs))

	if len(result.Behaviors) > 0 {
		fmt.Printf("\n%s:\n", styles.Success.Render("Observed Behaviors"))
		for _, behavior := range result.Behaviors {
			fmt.Printf("  - %s\n", behavior)
		}
	}

	return nil
}

// ============================================================================
// WARGAMING
// ============================================================================

var offensiveWargameCmd = &cobra.Command{
	Use:   "wargame",
	Short: "Wargaming simulations",
	Long:  `Run wargaming scenarios for training and purple team exercises.`,
}

var offensiveWargameStartCmd = &cobra.Command{
	Use:   "start",
	Short: "Start wargame scenario",
	Long: `Execute a wargaming scenario simulating APT attacks, breach scenarios,
or incident response exercises.`,
	Example: `  # Start APT simulation
  vcli offensive wargame start --scenario apt-simulation

  # Start ransomware scenario
  vcli offensive wargame start --scenario ransomware-attack`,
	RunE: runOffensiveWargameStart,
}

func runOffensiveWargameStart(cmd *cobra.Command, args []string) error {
	client := offensive.NewOffensiveClient(getOffensiveServer())

	req := &offensive.WargameStartRequest{
		Scenario: offensiveScenario,
	}

	fmt.Println(visual.DefaultStyles().Info.Render("🎮 Initializing wargame scenario..."))

	result, err := client.StartWargame(req)
	if err != nil {
		return fmt.Errorf("failed to start wargame: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🎮 Wargame Started"))
	fmt.Printf("\nScenario: %s\n", result.ScenarioName)
	fmt.Printf("Game ID: %s\n", result.GameID)
	fmt.Printf("Phases: %d\n", len(result.Phases))
	fmt.Printf("Estimated duration: %s\n", result.EstimatedDuration)

	fmt.Printf("\n%s:\n", styles.Success.Render("Phases"))
	for i, phase := range result.Phases {
		fmt.Printf("  %d. %s (%s)\n", i+1, phase.Name, phase.Duration)
	}

	return nil
}

// ============================================================================
// GATEWAY
// ============================================================================

var offensiveGatewayCmd = &cobra.Command{
	Use:   "gateway",
	Short: "Offensive gateway operations",
	Long:  `Manage the offensive operations gateway and coordination point.`,
}

var offensiveGatewayStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get offensive gateway status",
	Long:  `Check the status of the offensive operations gateway.`,
	Example: `  vcli offensive gateway status`,
	RunE: runOffensiveGatewayStatus,
}

func runOffensiveGatewayStatus(cmd *cobra.Command, args []string) error {
	client := offensive.NewOffensiveClient(getOffensiveServer())

	status, err := client.GetGatewayStatus()
	if err != nil {
		return fmt.Errorf("failed to get gateway status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("🚪 Offensive Gateway Status"))

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintf(w, "\nCOMPONENT\tSTATUS\tUPTIME\tACTIVE OPS\n")
	fmt.Fprintf(w, "---------\t------\t------\t----------\n")

	for _, component := range status.Components {
		fmt.Fprintf(w, "%s\t%s\t%s\t%d\n",
			component.Name,
			getStatusIcon(component.Status),
			component.Uptime,
			component.ActiveOps,
		)
	}
	w.Flush()

	return nil
}

// ============================================================================
// ORCHESTRATOR
// ============================================================================

var offensiveOrchestratorCmd = &cobra.Command{
	Use:   "orchestrator",
	Short: "Multi-phase attack orchestration",
	Long:  `Orchestrate complex multi-phase offensive operations.`,
}

var offensiveOrchestratorWorkflowCmd = &cobra.Command{
	Use:   "workflow",
	Short: "Execute offensive workflow",
	Long: `Execute a predefined multi-phase offensive workflow (playbook).

Playbooks coordinate multiple tools and techniques across the cyber kill chain.`,
	Example: `  # Execute red team playbook
  vcli offensive orchestrator workflow --playbook red-team-1

  # Execute custom workflow
  vcli offensive orchestrator workflow --playbook custom --config workflow.yaml`,
	RunE: runOffensiveOrchestratorWorkflow,
}

func runOffensiveOrchestratorWorkflow(cmd *cobra.Command, args []string) error {
	client := offensive.NewOffensiveClient(getOffensiveServer())

	req := &offensive.OrchestratorWorkflowRequest{
		Playbook: offensivePlaybook,
		Config:   offensiveConfig,
	}

	// Constitutional check
	if err := confirmAuthorization("Execute offensive workflow"); err != nil {
		return fmt.Errorf("operation cancelled: authorization required")
	}

	result, err := client.ExecuteWorkflow(req)
	if err != nil {
		return fmt.Errorf("failed to execute workflow: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Println(styles.Success.Render("⚡ Workflow Execution Started"))
	fmt.Printf("\nWorkflow ID: %s\n", result.WorkflowID)
	fmt.Printf("Playbook: %s\n", result.PlaybookName)
	fmt.Printf("Phases: %d\n", result.TotalPhases)
	fmt.Printf("Current phase: %s\n", result.CurrentPhase)

	return nil
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

func getOffensiveServer() string {
	if offensiveServer != "" {
		return offensiveServer
	}

	return config.GetEndpoint("offensive")
}

// TODO: Implement authorization icon helper
func getAuthorizationIcon(authorized bool) string {
	if authorized {
		return "✅"
	}
	return "❌"
}

// confirmAuthorization prompts user for explicit authorization
func confirmAuthorization(operation string) error {
	styles := visual.DefaultStyles()

	// Display warning
	fmt.Println(styles.Warning.Render("⚠️  AUTHORIZATION REQUIRED"))
	fmt.Printf("\n%s: %s\n\n", styles.Info.Render("Operation"), operation)
	fmt.Println(styles.Muted.Render("Constitutional AI compliance check:"))
	fmt.Println("  ✓ Explicit authorization required")
	fmt.Println("  ✓ All actions will be audited")
	fmt.Println("  ✓ Purple team coordination enabled")
	fmt.Println("  ✓ Sandboxed execution environment")
	fmt.Printf("\n%s [y/N]: ", styles.Info.Render("Proceed?"))

	var response string
	fmt.Scanln(&response)

	if response == "y" || response == "Y" || response == "yes" || response == "YES" {
		fmt.Println(styles.Success.Render("✅ Authorization granted"))
		return nil
	}

	fmt.Println(styles.Error.Render("❌ Authorization denied"))
	return fmt.Errorf("operation cancelled by user")
}
