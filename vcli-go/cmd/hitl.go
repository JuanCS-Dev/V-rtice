package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/help"
	"github.com/verticedev/vcli-go/internal/hitl"
)

// ============================================================================
// FLAGS
// ============================================================================

var (
	hitlEndpoint string
	hitlUsername string
	hitlPassword string
	hitlToken    string

	// List filters
	hitlPriority string

	// Decision flags
	hitlStatus  string
	hitlActions []string
	hitlNotes   string
	hitlReason  string

	// Output
	hitlOutputFormat string
	hitlWatch        bool
)

// ============================================================================
// MAIN COMMAND
// ============================================================================

var hitlCmd = &cobra.Command{
	Use:   "hitl",
	Short: "Human-in-the-Loop decision management",
	Long: `HITL (Human-in-the-Loop) Console for managing critical security decisions.

The HITL system provides human oversight for high-stakes decisions identified
by the CANDI threat analysis engine. Security analysts can review, approve,
reject, or escalate decisions via this command-line interface.`,
	Example: help.BuildCobraExample(help.HITLExamples, help.HITLDecisionExamples),
}

// ============================================================================
// STATUS COMMAND
// ============================================================================

var hitlStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get HITL system status",
	Long:  `Display current HITL system status including pending decisions and system health.`,
	RunE:  runHITLStatus,
}

func runHITLStatus(cmd *cobra.Command, args []string) error {
	client, err := createHITLClient()
	if err != nil {
		return err
	}

	status, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	if hitlOutputFormat == "json" {
		data, _ := json.MarshalIndent(status, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Pretty print
	fmt.Printf("HITL System Status\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
	fmt.Printf("Status:             %s\n", status.Status)
	fmt.Printf("Pending Decisions:  %d\n", status.PendingDecisions)
	fmt.Printf("Critical Pending:   %d\n", status.CriticalPending)
	fmt.Printf("In Review:          %d\n", status.InReviewDecisions)
	fmt.Printf("Decisions Today:    %d\n", status.TotalDecisionsToday)

	return nil
}

// ============================================================================
// LIST COMMAND
// ============================================================================

var hitlListCmd = &cobra.Command{
	Use:   "list",
	Short: "List pending decisions",
	Long: `List all pending HITL decisions with optional priority filtering.

Priority levels:
  - critical: APT-level threats requiring immediate attention
  - high: Targeted attacks
  - medium: Opportunistic attacks
  - low: Low-priority events

Examples:
  # List all pending decisions
  vcli hitl list

  # List only critical decisions
  vcli hitl list --priority critical

  # List in JSON format
  vcli hitl list --output json`,
	RunE: runHITLList,
}

func runHITLList(cmd *cobra.Command, args []string) error {
	client, err := createHITLClient()
	if err != nil {
		return err
	}

	decisions, err := client.ListPendingDecisions(hitlPriority)
	if err != nil {
		return fmt.Errorf("failed to list decisions: %w", err)
	}

	if hitlOutputFormat == "json" {
		data, _ := json.MarshalIndent(decisions, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Table format
	if len(decisions) == 0 {
		fmt.Println("No pending decisions")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintln(w, "ANALYSIS_ID\tTHREAT\tSOURCE_IP\tATTRIBUTION\tPRIORITY\tAGE")

	for _, d := range decisions {
		age := time.Since(d.CreatedAt)
		ageStr := formatDuration(age)

		actor := d.AttributedActor
		if actor == "" {
			actor = "Unknown"
		}

		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\n",
			truncate(d.AnalysisID, 16),
			d.ThreatLevel,
			d.SourceIP,
			truncate(actor, 20),
			d.Priority,
			ageStr,
		)
	}
	w.Flush()

	fmt.Printf("\n%d pending decision(s)\n", len(decisions))

	return nil
}

// ============================================================================
// SHOW COMMAND
// ============================================================================

var hitlShowCmd = &cobra.Command{
	Use:   "show <analysis-id>",
	Short: "Show decision details",
	Long: `Display detailed information about a specific decision.

The show command displays complete forensic details, IOCs, TTPs,
recommended actions, and attribution information.

Examples:
  # Show decision details
  vcli hitl show CANDI-abc123

  # Show in JSON format
  vcli hitl show CANDI-abc123 --output json`,
	Args: cobra.ExactArgs(1),
	RunE: runHITLShow,
}

func runHITLShow(cmd *cobra.Command, args []string) error {
	analysisID := args[0]

	client, err := createHITLClient()
	if err != nil {
		return err
	}

	decision, err := client.GetDecision(analysisID)
	if err != nil {
		return fmt.Errorf("failed to get decision: %w", err)
	}

	if hitlOutputFormat == "json" {
		data, _ := json.MarshalIndent(decision, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Pretty print
	fmt.Printf("Decision: %s\n", decision.AnalysisID)
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")

	fmt.Printf("Threat Assessment:\n")
	fmt.Printf("  Threat Level:     %s\n", decision.ThreatLevel)
	fmt.Printf("  Priority:         %s\n", decision.Priority)
	fmt.Printf("  Status:           %s\n", decision.Status)
	fmt.Printf("\n")

	fmt.Printf("Attack Details:\n")
	fmt.Printf("  Source IP:        %s\n", decision.SourceIP)
	fmt.Printf("  Attribution:      %s (%.1f%% confidence)\n", decision.AttributedActor, decision.Confidence)
	if decision.IncidentID != "" {
		fmt.Printf("  Incident ID:      %s\n", decision.IncidentID)
	}
	fmt.Printf("\n")

	if len(decision.IOCs) > 0 {
		fmt.Printf("Indicators of Compromise (%d):\n", len(decision.IOCs))
		for _, ioc := range decision.IOCs {
			fmt.Printf("  - %s\n", ioc)
		}
		fmt.Printf("\n")
	}

	if len(decision.TTPs) > 0 {
		fmt.Printf("TTPs (%d):\n", len(decision.TTPs))
		for _, ttp := range decision.TTPs {
			fmt.Printf("  - %s\n", ttp)
		}
		fmt.Printf("\n")
	}

	if len(decision.RecommendedActions) > 0 {
		fmt.Printf("Recommended Actions:\n")
		for _, action := range decision.RecommendedActions {
			fmt.Printf("  - %s\n", action)
		}
		fmt.Printf("\n")
	}

	fmt.Printf("Forensic Summary:\n")
	fmt.Printf("  %s\n", decision.ForensicSummary)
	fmt.Printf("\n")

	fmt.Printf("Timeline:\n")
	fmt.Printf("  Created:  %s\n", decision.CreatedAt.Format(time.RFC3339))
	fmt.Printf("  Updated:  %s\n", decision.UpdatedAt.Format(time.RFC3339))
	fmt.Printf("  Age:      %s\n", formatDuration(time.Since(decision.CreatedAt)))

	return nil
}

// ============================================================================
// APPROVE COMMAND
// ============================================================================

var hitlApproveCmd = &cobra.Command{
	Use:   "approve <analysis-id>",
	Short: "Approve decision and execute actions",
	Long: `Approve a HITL decision and authorize execution of specified actions.

Actions are selected from the recommended actions list. If no actions are
specified via --actions flag, all recommended actions will be executed.

Available action types:
  - block_ip: Block source IP at firewall
  - quarantine_system: Isolate affected systems
  - activate_killswitch: Trigger emergency kill switch
  - deploy_countermeasure: Deploy active countermeasures
  - escalate_to_soc: Escalate to SOC team
  - no_action: Approve but take no automated action

Examples:
  # Approve with specific actions
  vcli hitl approve CANDI-abc123 --actions block_ip,quarantine_system

  # Approve with notes
  vcli hitl approve CANDI-abc123 --actions block_ip --notes "Confirmed APT28 C2"

  # Approve with no automated action
  vcli hitl approve CANDI-abc123 --actions no_action --notes "Manual response initiated"`,
	Args: cobra.ExactArgs(1),
	RunE: runHITLApprove,
}

func runHITLApprove(cmd *cobra.Command, args []string) error {
	analysisID := args[0]

	client, err := createHITLClient()
	if err != nil {
		return err
	}

	// If no actions specified, get recommended actions
	actions := hitlActions
	if len(actions) == 0 {
		decision, err := client.GetDecision(analysisID)
		if err != nil {
			return fmt.Errorf("failed to get decision: %w", err)
		}
		actions = decision.RecommendedActions
	}

	decisionCreate := hitl.DecisionCreate{
		Status:          "approved",
		ApprovedActions: actions,
		Notes:           hitlNotes,
	}

	response, err := client.MakeDecision(analysisID, decisionCreate)
	if err != nil {
		return fmt.Errorf("failed to approve decision: %w", err)
	}

	if hitlOutputFormat == "json" {
		data, _ := json.MarshalIndent(response, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Success message
	fmt.Printf("✅ Decision approved: %s\n", response.AnalysisID)
	fmt.Printf("Status:      %s\n", response.Status)
	fmt.Printf("Decided by:  %s\n", response.DecidedBy)
	fmt.Printf("Decided at:  %s\n", response.DecidedAt.Format(time.RFC3339))
	fmt.Printf("\n")
	fmt.Printf("Approved actions (%d):\n", len(response.ApprovedActions))
	for _, action := range response.ApprovedActions {
		fmt.Printf("  - %s\n", action)
	}

	if response.Notes != "" {
		fmt.Printf("\nNotes: %s\n", response.Notes)
	}

	return nil
}

// ============================================================================
// REJECT COMMAND
// ============================================================================

var hitlRejectCmd = &cobra.Command{
	Use:   "reject <analysis-id>",
	Short: "Reject decision",
	Long: `Reject a HITL decision and provide reasoning.

Rejection indicates that the security analyst has determined the threat
assessment is incorrect or that the recommended actions are not appropriate.

Examples:
  # Reject with reason
  vcli hitl reject CANDI-abc123 --notes "False positive - legitimate admin activity"

  # Reject APT detection
  vcli hitl reject CANDI-abc123 --notes "Not APT - opportunistic scanner"`,
	Args: cobra.ExactArgs(1),
	RunE: runHITLReject,
}

func runHITLReject(cmd *cobra.Command, args []string) error {
	analysisID := args[0]

	if hitlNotes == "" {
		return fmt.Errorf("--notes is required when rejecting a decision")
	}

	client, err := createHITLClient()
	if err != nil {
		return err
	}

	decisionCreate := hitl.DecisionCreate{
		Status:          "rejected",
		ApprovedActions: []string{},
		Notes:           hitlNotes,
	}

	response, err := client.MakeDecision(analysisID, decisionCreate)
	if err != nil {
		return fmt.Errorf("failed to reject decision: %w", err)
	}

	if hitlOutputFormat == "json" {
		data, _ := json.MarshalIndent(response, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Success message
	fmt.Printf("✅ Decision rejected: %s\n", response.AnalysisID)
	fmt.Printf("Status:      %s\n", response.Status)
	fmt.Printf("Decided by:  %s\n", response.DecidedBy)
	fmt.Printf("Decided at:  %s\n", response.DecidedAt.Format(time.RFC3339))
	fmt.Printf("Notes:       %s\n", response.Notes)

	return nil
}

// ============================================================================
// ESCALATE COMMAND
// ============================================================================

var hitlEscalateCmd = &cobra.Command{
	Use:   "escalate <analysis-id>",
	Short: "Escalate decision to higher authority",
	Long: `Escalate a HITL decision to a higher authority (e.g., SOC manager, CISO).

Use escalation when the decision requires senior approval or when you need
additional expertise before making a determination.

Examples:
  # Escalate with reason
  vcli hitl escalate CANDI-abc123 --reason "Potential nation-state actor - requires CISO approval"

  # Escalate for additional analysis
  vcli hitl escalate CANDI-abc123 --reason "Unclear attribution - need threat intel team review"`,
	Args: cobra.ExactArgs(1),
	RunE: runHITLEscalate,
}

func runHITLEscalate(cmd *cobra.Command, args []string) error {
	analysisID := args[0]

	if hitlReason == "" {
		return fmt.Errorf("--reason is required when escalating")
	}

	client, err := createHITLClient()
	if err != nil {
		return err
	}

	response, err := client.EscalateDecision(analysisID, hitlReason)
	if err != nil {
		return fmt.Errorf("failed to escalate decision: %w", err)
	}

	if hitlOutputFormat == "json" {
		data, _ := json.MarshalIndent(response, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Success message
	fmt.Printf("⬆️  Decision escalated: %s\n", response.AnalysisID)
	fmt.Printf("Status:      %s\n", response.Status)
	fmt.Printf("Escalated by: %s\n", response.DecidedBy)
	fmt.Printf("Escalated at: %s\n", response.DecidedAt.Format(time.RFC3339))
	fmt.Printf("Reason:       %s\n", response.Notes)

	return nil
}

// ============================================================================
// STATS COMMAND
// ============================================================================

var hitlStatsCmd = &cobra.Command{
	Use:   "stats",
	Short: "Show decision statistics",
	Long: `Display comprehensive decision statistics including counts by priority,
approval rates, and response time metrics.

Examples:
  # Show statistics
  vcli hitl stats

  # Show in JSON format
  vcli hitl stats --output json`,
	RunE: runHITLStats,
}

func runHITLStats(cmd *cobra.Command, args []string) error {
	client, err := createHITLClient()
	if err != nil {
		return err
	}

	stats, err := client.GetStats()
	if err != nil {
		return fmt.Errorf("failed to get stats: %w", err)
	}

	if hitlOutputFormat == "json" {
		data, _ := json.MarshalIndent(stats, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Pretty print
	fmt.Printf("HITL Decision Statistics\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")

	fmt.Printf("Pending Decisions:\n")
	fmt.Printf("  Total:     %d\n", stats.TotalPending)
	fmt.Printf("  Critical:  %d\n", stats.CriticalPending)
	fmt.Printf("  High:      %d\n", stats.HighPending)
	fmt.Printf("  Medium:    %d\n", stats.MediumPending)
	fmt.Printf("  Low:       %d\n", stats.LowPending)
	fmt.Printf("\n")

	fmt.Printf("Completed Decisions:\n")
	fmt.Printf("  Approved:  %d\n", stats.TotalApproved)
	fmt.Printf("  Rejected:  %d\n", stats.TotalRejected)
	fmt.Printf("  Escalated: %d\n", stats.TotalEscalated)
	fmt.Printf("\n")

	fmt.Printf("Performance Metrics:\n")
	fmt.Printf("  Approval Rate:        %.1f%%\n", stats.ApprovalRate)
	fmt.Printf("  Avg Response Time:    %.1f minutes\n", stats.AvgResponseTimeMinutes)
	if stats.OldestPendingMinutes > 0 {
		fmt.Printf("  Oldest Pending:       %.1f minutes\n", stats.OldestPendingMinutes)
	}

	return nil
}

// ============================================================================
// WATCH COMMAND
// ============================================================================

var hitlWatchCmd = &cobra.Command{
	Use:   "watch",
	Short: "Watch for new decisions in real-time",
	Long: `Watch for new HITL decisions in real-time (polling mode).

This command polls the HITL API every few seconds and displays new
decisions as they arrive.

Press Ctrl+C to stop watching.

Examples:
  # Watch all decisions
  vcli hitl watch

  # Watch only critical decisions
  vcli hitl watch --priority critical`,
	RunE: runHITLWatch,
}

func runHITLWatch(cmd *cobra.Command, args []string) error {
	client, err := createHITLClient()
	if err != nil {
		return err
	}

	fmt.Printf("👁️  Watching for new HITL decisions")
	if hitlPriority != "" {
		fmt.Printf(" (priority: %s)", hitlPriority)
	}
	fmt.Printf("...\n")
	fmt.Printf("Press Ctrl+C to stop\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")

	seenIDs := make(map[string]bool)

	// Get initial decisions
	decisions, err := client.ListPendingDecisions(hitlPriority)
	if err != nil {
		return fmt.Errorf("failed to get initial decisions: %w", err)
	}

	for _, d := range decisions {
		seenIDs[d.AnalysisID] = true
	}

	fmt.Printf("Tracking %d existing decision(s)\n\n", len(decisions))

	// Poll for new decisions
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		decisions, err := client.ListPendingDecisions(hitlPriority)
		if err != nil {
			fmt.Printf("⚠️  Error fetching decisions: %v\n", err)
			continue
		}

		for _, d := range decisions {
			if !seenIDs[d.AnalysisID] {
				seenIDs[d.AnalysisID] = true

				// New decision found
				fmt.Printf("[%s] 🚨 NEW DECISION\n", time.Now().Format("15:04:05"))
				fmt.Printf("  Analysis ID:  %s\n", d.AnalysisID)
				fmt.Printf("  Threat Level: %s\n", d.ThreatLevel)
				fmt.Printf("  Priority:     %s\n", d.Priority)
				fmt.Printf("  Source IP:    %s\n", d.SourceIP)
				fmt.Printf("  Attribution:  %s (%.1f%% confidence)\n", d.AttributedActor, d.Confidence)
				fmt.Printf("  Actions:      %s\n", strings.Join(d.RecommendedActions, ", "))
				fmt.Printf("\n")
			}
		}
	}

	return nil
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

func createHITLClient() (*hitl.Client, error) {
	client := hitl.NewClient(hitlEndpoint)

	// If token provided directly, use it
	if hitlToken != "" {
		client.SetToken(hitlToken)
		return client, nil
	}

	// Otherwise, login with username/password
	if hitlUsername == "" || hitlPassword == "" {
		return nil, fmt.Errorf("either --token or both --username and --password are required")
	}

	if err := client.Login(hitlUsername, hitlPassword); err != nil {
		return nil, fmt.Errorf("authentication failed: %w", err)
	}

	return client, nil
}

func formatDuration(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%.0fs", d.Seconds())
	} else if d < time.Hour {
		return fmt.Sprintf("%.0fm", d.Minutes())
	} else if d < 24*time.Hour {
		return fmt.Sprintf("%.1fh", d.Hours())
	}
	return fmt.Sprintf("%.1fd", d.Hours()/24)
}

// ============================================================================
// INIT
// ============================================================================

func init() {
	rootCmd.AddCommand(hitlCmd)

	// Add subcommands
	hitlCmd.AddCommand(hitlStatusCmd)
	hitlCmd.AddCommand(hitlListCmd)
	hitlCmd.AddCommand(hitlShowCmd)
	hitlCmd.AddCommand(hitlApproveCmd)
	hitlCmd.AddCommand(hitlRejectCmd)
	hitlCmd.AddCommand(hitlEscalateCmd)
	hitlCmd.AddCommand(hitlStatsCmd)
	hitlCmd.AddCommand(hitlWatchCmd)

	// Global flags
	hitlCmd.PersistentFlags().StringVar(&hitlEndpoint, "endpoint", "", "HITL API endpoint (default: env VCLI_HITL_ENDPOINT or http://localhost:8000/api)")
	hitlCmd.PersistentFlags().StringVar(&hitlUsername, "username", "", "Username for authentication")
	hitlCmd.PersistentFlags().StringVar(&hitlPassword, "password", "", "Password for authentication")
	hitlCmd.PersistentFlags().StringVar(&hitlToken, "token", "", "Access token (alternative to username/password)")
	hitlCmd.PersistentFlags().StringVarP(&hitlOutputFormat, "output", "o", "table", "Output format (table|json)")

	// List flags
	hitlListCmd.Flags().StringVar(&hitlPriority, "priority", "", "Filter by priority (critical|high|medium|low)")

	// Approve flags
	hitlApproveCmd.Flags().StringSliceVar(&hitlActions, "actions", []string{}, "Actions to execute (comma-separated)")
	hitlApproveCmd.Flags().StringVar(&hitlNotes, "notes", "", "Additional notes")

	// Reject flags
	hitlRejectCmd.Flags().StringVar(&hitlNotes, "notes", "", "Rejection reason (required)")
	hitlRejectCmd.MarkFlagRequired("notes")

	// Escalate flags
	hitlEscalateCmd.Flags().StringVar(&hitlReason, "reason", "", "Escalation reason (required)")
	hitlEscalateCmd.MarkFlagRequired("reason")

	// Watch flags
	hitlWatchCmd.Flags().StringVar(&hitlPriority, "priority", "", "Filter by priority (critical|high|medium|low)")
}
