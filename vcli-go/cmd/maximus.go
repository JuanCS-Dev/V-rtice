package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/grpc"
	pb "github.com/verticedev/vcli-go/api/grpc/maximus"
)

// Flags
var (
	maximusServer    string
	decisionID       string
	decisionType     string
	decisionTitle    string
	decisionDesc     string
	decisionContext  string
	decisionPriority string
	decisionTags     []string
	requesterID      string

	// List filters
	filterStatus     string
	filterType       string
	filterContext    string
	filterTags       []string
	page             int32
	pageSize         int32
	sortBy           string
	sortOrder        string

	// Update
	newStatus        string
	updateReason     string
	updatedBy        string

	// Output
	outputFormat     string
	watch            bool
)

// maximusCmd represents the maximus command
var maximusCmd = &cobra.Command{
	Use:   "maximus",
	Short: "Interact with MAXIMUS Orchestrator",
	Long: `Manage decisions and governance through MAXIMUS Orchestrator.

MAXIMUS is the central decision-making orchestrator for the Vértice platform.
It handles decision workflows, approvals, and governance tracking.

Examples:
  # Submit a new decision
  vcli maximus submit \
    --type deployment \
    --title "Deploy v2.0" \
    --desc "Deploy new version to production" \
    --context production \
    --priority high

  # List pending decisions
  vcli maximus list --status pending

  # Get decision details
  vcli maximus get <decision-id>

  # Watch decision updates in real-time
  vcli maximus watch <decision-id>

  # Get governance metrics
  vcli maximus metrics`,
}

// ============================================================================
// SUBMIT COMMAND
// ============================================================================

var maximusSubmitCmd = &cobra.Command{
	Use:   "submit",
	Short: "Submit a new decision for approval",
	Long: `Submit a new decision to MAXIMUS for governance approval.

All decisions submitted through vCLI are tracked and go through the
configured approval workflow based on decision type, context, and priority.

Examples:
  # Submit deployment decision
  vcli maximus submit \
    --type deployment \
    --title "Deploy feature X" \
    --desc "Deploy new feature to production" \
    --context production \
    --priority high \
    --tags feature,critical

  # Submit scaling decision
  vcli maximus submit \
    --type scaling \
    --title "Scale up agents" \
    --context staging \
    --priority medium`,
	RunE: runSubmitDecision,
}

func runSubmitDecision(cmd *cobra.Command, args []string) error {
	// Validate required fields
	if decisionType == "" || decisionTitle == "" {
		return fmt.Errorf("--type and --title are required")
	}

	// Connect to MAXIMUS
	client, err := grpc.NewMaximusClient(maximusServer)
	if err != nil {
		return fmt.Errorf("failed to connect to MAXIMUS: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Submit decision
	resp, err := client.SubmitDecision(
		ctx,
		decisionType,
		decisionTitle,
		decisionDesc,
		decisionContext,
		decisionPriority,
		decisionTags,
		requesterID,
	)
	if err != nil {
		return fmt.Errorf("failed to submit decision: %w", err)
	}

	// Output response
	if outputFormat == "json" {
		data, _ := json.MarshalIndent(resp, "", "  ")
		fmt.Println(string(data))
	} else {
		fmt.Printf("✅ Decision submitted successfully\n")
		fmt.Printf("ID:         %s\n", resp.DecisionId)
		fmt.Printf("Status:     %s\n", resp.Status)
		fmt.Printf("Created At: %s\n", resp.CreatedAt.AsTime().Format(time.RFC3339))
		if resp.Message != "" {
			fmt.Printf("Message:    %s\n", resp.Message)
		}
	}

	return nil
}

// ============================================================================
// LIST COMMAND
// ============================================================================

var maximusListCmd = &cobra.Command{
	Use:   "list",
	Short: "List decisions with optional filters",
	Long: `List decisions with flexible filtering, sorting, and pagination.

Filters:
  --status      Filter by status (pending, approved, rejected, etc.)
  --type        Filter by decision type
  --context     Filter by context (production, staging, etc.)
  --tags        Filter by tags (comma-separated)

Pagination:
  --page        Page number (default: 1)
  --page-size   Results per page (default: 20)

Sorting:
  --sort-by     Sort field (created_at, priority, status)
  --sort-order  Sort order (asc, desc)

Examples:
  # List all pending decisions
  vcli maximus list --status pending

  # List high-priority deployment decisions
  vcli maximus list --type deployment --priority high

  # List production decisions, sorted by creation time
  vcli maximus list --context production --sort-by created_at --sort-order desc

  # Get second page of results
  vcli maximus list --page 2 --page-size 10`,
	RunE: runListDecisions,
}

func runListDecisions(cmd *cobra.Command, args []string) error {
	// Connect to MAXIMUS
	client, err := grpc.NewMaximusClient(maximusServer)
	if err != nil {
		return fmt.Errorf("failed to connect to MAXIMUS: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// List decisions
	resp, err := client.ListDecisions(
		ctx,
		filterStatus,
		filterType,
		filterContext,
		filterTags,
		page,
		pageSize,
		sortBy,
		sortOrder,
		nil, // start time
		nil, // end time
	)
	if err != nil {
		return fmt.Errorf("failed to list decisions: %w", err)
	}

	// Output
	if outputFormat == "json" {
		data, _ := json.MarshalIndent(resp, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Table format
	if len(resp.Decisions) == 0 {
		fmt.Println("No decisions found")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintln(w, "ID\tTYPE\tTITLE\tSTATUS\tPRIORITY\tCREATED")
	for _, d := range resp.Decisions {
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\n",
			truncate(d.DecisionId, 16),
			d.DecisionType,
			truncate(d.Title, 40),
			d.Status,
			d.Priority,
			d.CreatedAt.AsTime().Format("2006-01-02 15:04"),
		)
	}
	w.Flush()

	fmt.Printf("\nShowing %d of %d total decisions (page %d)\n",
		len(resp.Decisions), resp.TotalCount, resp.Page)

	return nil
}

// ============================================================================
// GET COMMAND
// ============================================================================

var maximusGetCmd = &cobra.Command{
	Use:   "get <decision-id>",
	Short: "Get decision details",
	Long: `Get detailed information about a specific decision.

Examples:
  # Get decision by ID
  vcli maximus get dec_abc123

  # Get decision in JSON format
  vcli maximus get dec_abc123 --output json`,
	Args: cobra.ExactArgs(1),
	RunE: runGetDecision,
}

func runGetDecision(cmd *cobra.Command, args []string) error {
	decisionID := args[0]

	// Connect to MAXIMUS
	client, err := grpc.NewMaximusClient(maximusServer)
	if err != nil {
		return fmt.Errorf("failed to connect to MAXIMUS: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Get decision
	decision, err := client.GetDecision(ctx, decisionID)
	if err != nil {
		return fmt.Errorf("failed to get decision: %w", err)
	}

	// Output
	if outputFormat == "json" {
		data, _ := json.MarshalIndent(decision, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Pretty print
	fmt.Printf("Decision: %s\n", decision.DecisionId)
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
	fmt.Printf("Type:        %s\n", decision.DecisionType)
	fmt.Printf("Title:       %s\n", decision.Title)
	fmt.Printf("Description: %s\n", decision.Description)
	fmt.Printf("Status:      %s\n", decision.Status)
	fmt.Printf("Priority:    %s\n", decision.Priority)
	fmt.Printf("Context:     %s\n", decision.Context)
	if len(decision.Tags) > 0 {
		fmt.Printf("Tags:        %s\n", strings.Join(decision.Tags, ", "))
	}
	fmt.Printf("\n")
	fmt.Printf("Created At:  %s\n", decision.CreatedAt.AsTime().Format(time.RFC3339))
	fmt.Printf("Updated At:  %s\n", decision.UpdatedAt.AsTime().Format(time.RFC3339))
	if decision.ResolvedAt != nil {
		fmt.Printf("Resolved At: %s\n", decision.ResolvedAt.AsTime().Format(time.RFC3339))
	}
	fmt.Printf("\n")
	fmt.Printf("Requester:   %s\n", decision.RequesterId)
	if decision.ApproverId != "" {
		fmt.Printf("Approver:    %s\n", decision.ApproverId)
	}
	if decision.ResolutionReason != "" {
		fmt.Printf("Resolution:  %s\n", decision.ResolutionReason)
	}
	if decision.ProcessingTimeMs > 0 {
		fmt.Printf("Process Time: %dms\n", decision.ProcessingTimeMs)
	}

	return nil
}

// ============================================================================
// WATCH COMMAND
// ============================================================================

var maximusWatchCmd = &cobra.Command{
	Use:   "watch <decision-id>",
	Short: "Watch decision updates in real-time",
	Long: `Watch a specific decision for real-time updates via gRPC streaming.

The watch command keeps a persistent connection open and displays events
as they occur (status changes, approvals, rejections, etc.).

Press Ctrl+C to stop watching.

Examples:
  # Watch a specific decision
  vcli maximus watch dec_abc123`,
	Args: cobra.ExactArgs(1),
	RunE: runWatchDecision,
}

func runWatchDecision(cmd *cobra.Command, args []string) error {
	decisionID := args[0]

	// Connect to MAXIMUS
	client, err := grpc.NewMaximusClient(maximusServer)
	if err != nil {
		return fmt.Errorf("failed to connect to MAXIMUS: %w", err)
	}
	defer client.Close()

	fmt.Printf("👁️  Watching decision: %s\n", decisionID)
	fmt.Printf("Press Ctrl+C to stop\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")

	ctx := context.Background()

	// Watch decision
	err = client.WatchDecision(ctx, decisionID, func(event *pb.DecisionEvent) error {
		fmt.Printf("[%s] %s - Decision %s\n",
			event.Timestamp.AsTime().Format("15:04:05"),
			event.EventType.String(),
			event.DecisionId,
		)
		if event.TriggeredBy != "" {
			fmt.Printf("  Triggered by: %s\n", event.TriggeredBy)
		}
		if event.Decision != nil {
			fmt.Printf("  New status: %s\n", event.Decision.Status)
		}
		fmt.Println()
		return nil
	})

	if err != nil {
		return fmt.Errorf("watch failed: %w", err)
	}

	return nil
}

// ============================================================================
// METRICS COMMAND
// ============================================================================

var maximusMetricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Get governance metrics",
	Long: `Retrieve governance metrics from MAXIMUS.

Metrics include decision counts, approval rates, processing times,
and breakdowns by type and priority.

Examples:
  # Get current metrics
  vcli maximus metrics

  # Get metrics in JSON format
  vcli maximus metrics --output json

  # Get metrics for specific context
  vcli maximus metrics --context production`,
	RunE: runGetMetrics,
}

func runGetMetrics(cmd *cobra.Command, args []string) error {
	// Connect to MAXIMUS
	client, err := grpc.NewMaximusClient(maximusServer)
	if err != nil {
		return fmt.Errorf("failed to connect to MAXIMUS: %w", err)
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Get metrics
	metrics, err := client.GetGovernanceMetrics(ctx, nil, nil, filterContext, nil)
	if err != nil {
		return fmt.Errorf("failed to get metrics: %w", err)
	}

	// Output
	if outputFormat == "json" {
		data, _ := json.MarshalIndent(metrics, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Pretty print
	fmt.Printf("MAXIMUS Governance Metrics\n")
	fmt.Printf("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
	fmt.Printf("Decision Counts:\n")
	fmt.Printf("  Total:    %d\n", metrics.TotalDecisions)
	fmt.Printf("  Pending:  %d\n", metrics.PendingDecisions)
	fmt.Printf("  Approved: %d\n", metrics.ApprovedDecisions)
	fmt.Printf("  Rejected: %d\n", metrics.RejectedDecisions)
	fmt.Printf("\n")
	fmt.Printf("Approval Rate: %.1f%%\n", metrics.ApprovalRate)
	fmt.Printf("\n")
	fmt.Printf("Processing Time (ms):\n")
	fmt.Printf("  Average: %.1f\n", metrics.AvgResolutionTimeMs)
	fmt.Printf("  P50:     %.1f\n", metrics.P50ResolutionTimeMs)
	fmt.Printf("  P95:     %.1f\n", metrics.P95ResolutionTimeMs)
	fmt.Printf("  P99:     %.1f\n", metrics.P99ResolutionTimeMs)

	if len(metrics.DecisionsByPriority) > 0 {
		fmt.Printf("\n")
		fmt.Printf("By Priority:\n")
		for priority, count := range metrics.DecisionsByPriority {
			fmt.Printf("  %s: %d\n", priority, count)
		}
	}

	if len(metrics.DecisionsByType) > 0 {
		fmt.Printf("\n")
		fmt.Printf("By Type:\n")
		for dtype, count := range metrics.DecisionsByType {
			fmt.Printf("  %s: %d\n", dtype, count)
		}
	}

	return nil
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

// ============================================================================
// INIT
// ============================================================================

func init() {
	rootCmd.AddCommand(maximusCmd)

	// Add subcommands
	maximusCmd.AddCommand(maximusSubmitCmd)
	maximusCmd.AddCommand(maximusListCmd)
	maximusCmd.AddCommand(maximusGetCmd)
	maximusCmd.AddCommand(maximusWatchCmd)
	maximusCmd.AddCommand(maximusMetricsCmd)

	// Global flags
	maximusCmd.PersistentFlags().StringVar(&maximusServer, "server", "localhost:50051", "MAXIMUS server address")
	maximusCmd.PersistentFlags().StringVarP(&outputFormat, "output", "o", "table", "Output format (table|json)")

	// Submit flags
	maximusSubmitCmd.Flags().StringVar(&decisionType, "type", "", "Decision type (required)")
	maximusSubmitCmd.Flags().StringVar(&decisionTitle, "title", "", "Decision title (required)")
	maximusSubmitCmd.Flags().StringVar(&decisionDesc, "desc", "", "Decision description")
	maximusSubmitCmd.Flags().StringVar(&decisionContext, "context", "default", "Decision context")
	maximusSubmitCmd.Flags().StringVar(&decisionPriority, "priority", "medium", "Priority (low|medium|high|critical)")
	maximusSubmitCmd.Flags().StringSliceVar(&decisionTags, "tags", []string{}, "Tags (comma-separated)")
	maximusSubmitCmd.Flags().StringVar(&requesterID, "requester", "vcli", "Requester ID")

	// List flags
	maximusListCmd.Flags().StringVar(&filterStatus, "status", "", "Filter by status")
	maximusListCmd.Flags().StringVar(&filterType, "type", "", "Filter by type")
	maximusListCmd.Flags().StringVar(&filterContext, "context", "", "Filter by context")
	maximusListCmd.Flags().StringSliceVar(&filterTags, "tags", []string{}, "Filter by tags")
	maximusListCmd.Flags().Int32Var(&page, "page", 1, "Page number")
	maximusListCmd.Flags().Int32Var(&pageSize, "page-size", 20, "Results per page")
	maximusListCmd.Flags().StringVar(&sortBy, "sort-by", "created_at", "Sort field")
	maximusListCmd.Flags().StringVar(&sortOrder, "sort-order", "desc", "Sort order (asc|desc)")

	// Metrics flags
	maximusMetricsCmd.Flags().StringVar(&filterContext, "context", "", "Filter by context")
}
