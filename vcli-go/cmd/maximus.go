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
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/visual"
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

	// Maximus AI services endpoints
	eurekaEndpoint   string
	oraculoEndpoint  string
	predictEndpoint  string
	maximusToken     string

	// Eureka flags
	dataFile         string
	dataType         string
	contextFile      string
	patternFile      string

	// Oraculo flags
	predictionType   string
	timeHorizon      string
	codeFile         string
	language         string
	analysisType     string
	taskDesc         string
	targetLang       string
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
// EUREKA COMMANDS (Insight Generation)
// ============================================================================

var maximusEurekaCmd = &cobra.Command{
	Use:   "eureka",
	Short: "Interact with Maximus Eureka (Insight Generation)",
	Long: `Maximus Eureka Service for novel insights, pattern detection, and IoC extraction.

Examples:
  # Generate insights from data
  vcli maximus eureka generate-insight --data-file data.json --data-type logs

  # Detect patterns
  vcli maximus eureka detect-pattern --data-file data.json --pattern-file pattern.json

  # Extract IoCs
  vcli maximus eureka extract-iocs --data-file data.json`,
}

var eurekaGenerateInsightCmd = &cobra.Command{
	Use:   "generate-insight",
	Short: "Generate novel insights from data",
	RunE:  runEurekaGenerateInsight,
}

func runEurekaGenerateInsight(cmd *cobra.Command, args []string) error {
	if dataFile == "" || dataType == "" {
		return fmt.Errorf("--data-file and --data-type are required")
	}

	// Read data file
	data, err := readJSONFile(dataFile)
	if err != nil {
		return fmt.Errorf("failed to read data file: %w", err)
	}

	// Read context if provided
	var context map[string]interface{}
	if contextFile != "" {
		context, err = readJSONFile(contextFile)
		if err != nil {
			return fmt.Errorf("failed to read context file: %w", err)
		}
	}

	client := maximus.NewEurekaClient(eurekaEndpoint, maximusToken)
	resp, err := client.GenerateInsight(data, dataType, context)
	if err != nil {
		return fmt.Errorf("failed to generate insight: %w", err)
	}

	printJSON(resp)
	return nil
}

var eurekaDetectPatternCmd = &cobra.Command{
	Use:   "detect-pattern",
	Short: "Detect specific patterns in data",
	RunE:  runEurekaDetectPattern,
}

func runEurekaDetectPattern(cmd *cobra.Command, args []string) error {
	if dataFile == "" || patternFile == "" {
		return fmt.Errorf("--data-file and --pattern-file are required")
	}

	data, err := readJSONFile(dataFile)
	if err != nil {
		return fmt.Errorf("failed to read data file: %w", err)
	}

	pattern, err := readJSONFile(patternFile)
	if err != nil {
		return fmt.Errorf("failed to read pattern file: %w", err)
	}

	client := maximus.NewEurekaClient(eurekaEndpoint, maximusToken)
	resp, err := client.DetectPattern(data, pattern)
	if err != nil {
		return fmt.Errorf("failed to detect pattern: %w", err)
	}

	printJSON(resp)
	return nil
}

var eurekaExtractIoCsCmd = &cobra.Command{
	Use:   "extract-iocs",
	Short: "Extract Indicators of Compromise from data",
	RunE:  runEurekaExtractIoCs,
}

func runEurekaExtractIoCs(cmd *cobra.Command, args []string) error {
	if dataFile == "" {
		return fmt.Errorf("--data-file is required")
	}

	data, err := readJSONFile(dataFile)
	if err != nil {
		return fmt.Errorf("failed to read data file: %w", err)
	}

	client := maximus.NewEurekaClient(eurekaEndpoint, maximusToken)
	resp, err := client.ExtractIoCs(data)
	if err != nil {
		return fmt.Errorf("failed to extract IoCs: %w", err)
	}

	printJSON(resp)
	return nil
}

var eurekaHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check Eureka service health",
	RunE:  runEurekaHealth,
}

func runEurekaHealth(cmd *cobra.Command, args []string) error {
	client := maximus.NewEurekaClient(eurekaEndpoint, maximusToken)
	resp, err := client.Health()
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	fmt.Printf("Status: %s - %s\n", resp.Status, resp.Message)
	return nil
}

// ============================================================================
// ORACULO COMMANDS (Predictions & Code Analysis)
// ============================================================================

var maximusOraculoCmd = &cobra.Command{
	Use:   "oraculo",
	Short: "Interact with Maximus Oraculo (Predictions & Code Analysis)",
	Long: `Maximus Oraculo Service for predictive insights and code analysis.

Examples:
  # Generate prediction
  vcli maximus oraculo predict --data-file data.json --prediction-type threat_level --time-horizon 24h

  # Analyze code
  vcli maximus oraculo analyze-code --code-file app.go --language go --analysis-type vulnerability

  # Auto-implement code
  vcli maximus oraculo auto-implement --task "create REST endpoint" --target-lang go`,
}

var oraculoPredictCmd = &cobra.Command{
	Use:   "predict",
	Short: "Generate predictive insights",
	RunE:  runOraculoPredict,
}

func runOraculoPredict(cmd *cobra.Command, args []string) error {
	if dataFile == "" || predictionType == "" || timeHorizon == "" {
		return fmt.Errorf("--data-file, --prediction-type, and --time-horizon are required")
	}

	data, err := readJSONFile(dataFile)
	if err != nil {
		return fmt.Errorf("failed to read data file: %w", err)
	}

	client := maximus.NewOraculoClient(oraculoEndpoint, maximusToken)
	resp, err := client.Predict(data, predictionType, timeHorizon)
	if err != nil {
		return fmt.Errorf("failed to generate prediction: %w", err)
	}

	printJSON(resp)
	return nil
}

var oraculoAnalyzeCodeCmd = &cobra.Command{
	Use:   "analyze-code",
	Short: "Analyze code for vulnerabilities or issues",
	RunE:  runOraculoAnalyzeCode,
}

func runOraculoAnalyzeCode(cmd *cobra.Command, args []string) error {
	if codeFile == "" || language == "" || analysisType == "" {
		return fmt.Errorf("--code-file, --language, and --analysis-type are required")
	}

	code, err := os.ReadFile(codeFile)
	if err != nil {
		return fmt.Errorf("failed to read code file: %w", err)
	}

	client := maximus.NewOraculoClient(oraculoEndpoint, maximusToken)
	resp, err := client.AnalyzeCode(string(code), language, analysisType)
	if err != nil {
		return fmt.Errorf("failed to analyze code: %w", err)
	}

	printJSON(resp)
	return nil
}

var oraculoAutoImplementCmd = &cobra.Command{
	Use:   "auto-implement",
	Short: "Request automated code implementation",
	RunE:  runOraculoAutoImplement,
}

func runOraculoAutoImplement(cmd *cobra.Command, args []string) error {
	if taskDesc == "" || targetLang == "" {
		return fmt.Errorf("--task and --target-lang are required")
	}

	var context map[string]interface{}
	if contextFile != "" {
		var err error
		context, err = readJSONFile(contextFile)
		if err != nil {
			return fmt.Errorf("failed to read context file: %w", err)
		}
	}

	client := maximus.NewOraculoClient(oraculoEndpoint, maximusToken)
	resp, err := client.AutoImplement(taskDesc, targetLang, context)
	if err != nil {
		return fmt.Errorf("failed to auto-implement: %w", err)
	}

	printJSON(resp)
	return nil
}

var oraculoHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check Oraculo service health",
	RunE:  runOraculoHealth,
}

func runOraculoHealth(cmd *cobra.Command, args []string) error {
	client := maximus.NewOraculoClient(oraculoEndpoint, maximusToken)
	resp, err := client.Health()
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	fmt.Printf("Status: %s - %s\n", resp.Status, resp.Message)
	return nil
}

// ============================================================================
// PREDICT COMMANDS (ML Predictions)
// ============================================================================

var maximusPredictCmd = &cobra.Command{
	Use:   "predict",
	Short: "Interact with Maximus Predict (ML Predictions)",
	Long: `Maximus Predict Service for machine learning predictions.

Examples:
  # Generate prediction
  vcli maximus predict generate --data-file data.json --prediction-type resource_demand --time-horizon 1h`,
}

var predictGenerateCmd = &cobra.Command{
	Use:   "generate",
	Short: "Generate ML prediction",
	RunE:  runPredictGenerate,
}

func runPredictGenerate(cmd *cobra.Command, args []string) error {
	if dataFile == "" || predictionType == "" {
		return fmt.Errorf("--data-file and --prediction-type are required")
	}

	data, err := readJSONFile(dataFile)
	if err != nil {
		return fmt.Errorf("failed to read data file: %w", err)
	}

	client := maximus.NewPredictClient(predictEndpoint, maximusToken)
	resp, err := client.Predict(data, predictionType, timeHorizon)
	if err != nil {
		return fmt.Errorf("failed to generate prediction: %w", err)
	}

	printJSON(resp)
	return nil
}

var predictHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check Predict service health",
	RunE:  runPredictHealth,
}

func runPredictHealth(cmd *cobra.Command, args []string) error {
	client := maximus.NewPredictClient(predictEndpoint, maximusToken)
	resp, err := client.Health()
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	fmt.Printf("Status: %s - %s\n", resp.Status, resp.Message)
	return nil
}

// ============================================================================
// CONSCIOUSNESS COMMANDS
// ============================================================================

var (
	consciousnessEndpoint string
	consciousnessStreamURL string
	esgtLimit             int
	esgtNovelty           float64
	esgtRelevance         float64
	esgtUrgency           float64
	arousalDelta          float64
	arousalDuration       float64
)

var maximusConsciousnessCmd = &cobra.Command{
	Use:   "consciousness",
	Short: "Interact with MAXIMUS Consciousness System",
	Long: `Monitor and control the MAXIMUS Consciousness System.

The consciousness system consists of:
  - TIG (Topological Information Graph) - Information fabric
  - ESGT (Event-Salience Global Triggers) - Attention mechanism
  - Arousal Controller - System activation level

Examples:
  # Get consciousness state
  vcli maximus consciousness state

  # Get recent ESGT events
  vcli maximus consciousness esgt events --limit 20

  # Trigger ESGT ignition manually
  vcli maximus consciousness esgt trigger --novelty 0.9 --relevance 0.8 --urgency 0.7

  # Get arousal state
  vcli maximus consciousness arousal

  # Adjust arousal level
  vcli maximus consciousness arousal adjust --delta 0.2 --duration 5

  # Get system metrics
  vcli maximus consciousness metrics`,
}

// State command
var consciousnessStateCmd = &cobra.Command{
	Use:   "state",
	Short: "Get current consciousness state",
	Long:  `Retrieve the complete consciousness system state including ESGT status, arousal level, and TIG metrics.`,
	RunE:  runConsciousnessState,
}

func runConsciousnessState(cmd *cobra.Command, args []string) error {
	client := maximus.NewConsciousnessClient(consciousnessEndpoint)

	state, err := client.GetState()
	if err != nil {
		return fmt.Errorf("failed to get consciousness state: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(state, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	fmt.Println(maximus.FormatConsciousnessState(state))
	return nil
}

// ESGT parent command
var consciousnessESGTCmd = &cobra.Command{
	Use:   "esgt",
	Short: "ESGT (Event-Salience Global Triggers) commands",
	Long:  `Commands for interacting with the ESGT attention mechanism.`,
}

// ESGT events command
var consciousnessESGTEventsCmd = &cobra.Command{
	Use:   "events",
	Short: "Get recent ESGT ignition events",
	Long:  `Retrieve recent ESGT events with configurable limit (1-100).`,
	RunE:  runConsciousnessESGTEvents,
}

func runConsciousnessESGTEvents(cmd *cobra.Command, args []string) error {
	client := maximus.NewConsciousnessClient(consciousnessEndpoint)

	events, err := client.GetESGTEvents(esgtLimit)
	if err != nil {
		return fmt.Errorf("failed to get ESGT events: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(events, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	fmt.Println(maximus.FormatESGTEvents(events))
	return nil
}

// ESGT trigger command
var consciousnessESGTTriggerCmd = &cobra.Command{
	Use:   "trigger",
	Short: "Manually trigger ESGT ignition",
	Long: `Trigger ESGT ignition with custom salience scores.

Salience components (all 0-1):
  --novelty    How novel/unexpected the stimulus is
  --relevance  How relevant to current goals
  --urgency    How urgent/time-sensitive

Example:
  vcli maximus consciousness esgt trigger --novelty 0.9 --relevance 0.8 --urgency 0.7`,
	RunE: runConsciousnessESGTTrigger,
}

func runConsciousnessESGTTrigger(cmd *cobra.Command, args []string) error {
	client := maximus.NewConsciousnessClient(consciousnessEndpoint)

	salience := maximus.SalienceInput{
		Novelty:   esgtNovelty,
		Relevance: esgtRelevance,
		Urgency:   esgtUrgency,
		Context:   map[string]interface{}{"source": "vcli-manual"},
	}

	event, err := client.TriggerESGT(salience)
	if err != nil {
		return fmt.Errorf("failed to trigger ESGT: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(event, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Pretty print event result
	styles := visual.DefaultStyles()
	if event.Success {
		fmt.Printf("%s ESGT ignition successful!\n", styles.Success.Render("✅"))
		fmt.Printf("Event ID: %s\n", styles.Info.Render(event.EventID))
		if event.Coherence > 0 {
			fmt.Printf("Coherence: %.3f\n", event.Coherence)
		}
		if event.DurationMs > 0 {
			fmt.Printf("Duration: %.1fms\n", event.DurationMs)
		}
		fmt.Printf("Nodes: %d\n", event.NodesParticipating)
	} else {
		fmt.Printf("%s ESGT ignition failed\n", styles.Error.Render("❌"))
		if event.Reason != "" {
			fmt.Printf("Reason: %s\n", styles.Error.Render(string(event.Reason)))
		}
	}

	return nil
}

// Arousal parent command
var consciousnessArousalCmd = &cobra.Command{
	Use:   "arousal",
	Short: "Arousal controller commands",
	Long:  `Commands for monitoring and adjusting system arousal level.`,
	RunE:  runConsciousnessArousal,
}

func runConsciousnessArousal(cmd *cobra.Command, args []string) error {
	client := maximus.NewConsciousnessClient(consciousnessEndpoint)

	arousal, err := client.GetArousal()
	if err != nil {
		return fmt.Errorf("failed to get arousal state: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(arousal, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	fmt.Println(maximus.FormatArousalState(arousal))
	return nil
}

// Arousal adjust command
var consciousnessArousalAdjustCmd = &cobra.Command{
	Use:   "adjust",
	Short: "Adjust arousal level",
	Long: `Temporarily adjust the system arousal level.

Example:
  # Increase arousal by 0.2 for 5 seconds
  vcli maximus consciousness arousal adjust --delta 0.2 --duration 5

  # Decrease arousal by 0.1 for 10 seconds
  vcli maximus consciousness arousal adjust --delta -0.1 --duration 10`,
	RunE: runConsciousnessArousalAdjust,
}

func runConsciousnessArousalAdjust(cmd *cobra.Command, args []string) error {
	client := maximus.NewConsciousnessClient(consciousnessEndpoint)

	adjustment := maximus.ArousalAdjustment{
		Delta:           arousalDelta,
		DurationSeconds: arousalDuration,
		Source:          "vcli",
	}

	arousal, err := client.AdjustArousal(adjustment)
	if err != nil {
		return fmt.Errorf("failed to adjust arousal: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(arousal, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Arousal adjusted successfully\n", styles.Success.Render("✅"))
	fmt.Printf("New arousal: %.3f (%s)\n", arousal.Arousal, arousal.Level)
	fmt.Printf("Delta: %+.3f for %.1fs\n", arousalDelta, arousalDuration)

	return nil
}

// Metrics command
var consciousnessMetricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Get consciousness system metrics",
	Long:  `Retrieve TIG topology metrics and ESGT statistics.`,
	RunE:  runConsciousnessMetrics,
}

// Watch command
var consciousnessWatchCmd = &cobra.Command{
	Use:   "watch",
	Short: "Watch consciousness events in real-time",
	Long: `Watch consciousness system events via WebSocket streaming.

Streams real-time events:
  - ESGT ignitions (success/failure)
  - Arousal level changes
  - System heartbeats

Press Ctrl+C to stop watching.

Example:
  vcli maximus consciousness watch`,
	RunE: runConsciousnessWatch,
}

func runConsciousnessMetrics(cmd *cobra.Command, args []string) error {
	client := maximus.NewConsciousnessClient(consciousnessEndpoint)

	metrics, err := client.GetMetrics()
	if err != nil {
		return fmt.Errorf("failed to get metrics: %w", err)
	}

	if outputFormat == "json" {
		data, _ := json.MarshalIndent(metrics, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	fmt.Println(maximus.FormatMetrics(metrics))
	return nil
}

func runConsciousnessWatch(cmd *cobra.Command, args []string) error {
	client := maximus.NewConsciousnessClient(consciousnessEndpoint)
	if consciousnessStreamURL != "" {
		client.WithStreamURL(consciousnessStreamURL)
	}
	styles := visual.DefaultStyles()

	// Print header
	fmt.Printf("👁️  Watching consciousness system...\n")
	fmt.Printf("Press Ctrl+C to stop\n")
	fmt.Printf("%s\n\n", strings.Repeat("━", 80))

	// Connect to WebSocket and handle events
	err := client.ConnectWebSocket(func(event *maximus.WSEvent) error {
		timestamp := event.Timestamp
		if t, err := time.Parse(time.RFC3339, event.Timestamp); err == nil {
			timestamp = t.Format("15:04:05")
		}

		switch event.Type {
		case maximus.WSEventESGT:
			esgtEvent, err := maximus.ParseESGTEvent(event)
			if err != nil {
				fmt.Printf("[%s] %s Error parsing ESGT event: %v\n",
					styles.Muted.Render(timestamp),
					styles.Error.Render("❌"),
					err)
				return nil
			}

			// Format ESGT event
			icon := "✅"
			status := styles.Success.Render("ESGT_EVENT")
			if !esgtEvent.Success {
				icon = "❌"
				status = styles.Error.Render("ESGT_FAILED")
			}

			coherenceStr := ""
			if esgtEvent.Coherence != nil {
				coherenceStr = fmt.Sprintf(" | coherence: %.2f", *esgtEvent.Coherence)
			}

			fmt.Printf("[%s] %s %s - %s%s\n",
				styles.Muted.Render(timestamp),
				icon,
				status,
				styles.Info.Render(esgtEvent.EventID),
				coherenceStr)

			if esgtEvent.Reason != nil && *esgtEvent.Reason != "" {
				fmt.Printf("         Reason: %s\n", styles.Error.Render(*esgtEvent.Reason))
			}

		case maximus.WSEventArousalChange:
			arousalEvent, err := maximus.ParseArousalChangeEvent(event)
			if err != nil {
				fmt.Printf("[%s] %s Error parsing arousal event: %v\n",
					styles.Muted.Render(timestamp),
					styles.Error.Render("❌"),
					err)
				return nil
			}

			// Format arousal change
			arrow := "→"
			if arousalEvent.NewLevel > arousalEvent.OldLevel {
				arrow = styles.Success.Render("↑")
			} else if arousalEvent.NewLevel < arousalEvent.OldLevel {
				arrow = styles.Warning.Render("↓")
			}

			fmt.Printf("[%s] 📊 %s - Level: %s (%.2f %s %.2f)\n",
				styles.Muted.Render(timestamp),
				styles.Accent.Render("AROUSAL_CHANGE"),
				styles.Accent.Render(arousalEvent.NewClass),
				arousalEvent.OldLevel,
				arrow,
				arousalEvent.NewLevel)

		case maximus.WSEventHeartbeat:
			heartbeat, err := maximus.ParseHeartbeatEvent(event)
			if err != nil {
				fmt.Printf("[%s] %s Error parsing heartbeat: %v\n",
					styles.Muted.Render(timestamp),
					styles.Error.Render("❌"),
					err)
				return nil
			}

			// Format heartbeat (muted, less prominent)
			fmt.Printf("[%s] %s - %s (uptime: %ds, events: %d)\n",
				styles.Muted.Render(timestamp),
				styles.Muted.Render("💓 HEARTBEAT"),
				styles.Muted.Render(heartbeat.Status),
				heartbeat.Uptime,
				heartbeat.ESGTCount)

		default:
			// Unknown event type
			fmt.Printf("[%s] %s Unknown event type: %s\n",
				styles.Muted.Render(timestamp),
				styles.Warning.Render("⚠️"),
				event.Type)
		}

		return nil
	})

	if err != nil {
		return fmt.Errorf("WebSocket error: %w", err)
	}

	return nil
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

func readJSONFile(path string) (map[string]interface{}, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, err
	}

	return result, nil
}

func printJSON(v interface{}) {
	data, _ := json.MarshalIndent(v, "", "  ")
	fmt.Println(string(data))
}

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

	// Add Maximus AI service commands
	maximusCmd.AddCommand(maximusEurekaCmd)
	maximusCmd.AddCommand(maximusOraculoCmd)
	maximusCmd.AddCommand(maximusPredictCmd)
	maximusCmd.AddCommand(maximusConsciousnessCmd)

	// Eureka subcommands
	maximusEurekaCmd.AddCommand(eurekaGenerateInsightCmd)
	maximusEurekaCmd.AddCommand(eurekaDetectPatternCmd)
	maximusEurekaCmd.AddCommand(eurekaExtractIoCsCmd)
	maximusEurekaCmd.AddCommand(eurekaHealthCmd)

	// Oraculo subcommands
	maximusOraculoCmd.AddCommand(oraculoPredictCmd)
	maximusOraculoCmd.AddCommand(oraculoAnalyzeCodeCmd)
	maximusOraculoCmd.AddCommand(oraculoAutoImplementCmd)
	maximusOraculoCmd.AddCommand(oraculoHealthCmd)

	// Predict subcommands
	maximusPredictCmd.AddCommand(predictGenerateCmd)
	maximusPredictCmd.AddCommand(predictHealthCmd)

	// Consciousness subcommands
	maximusConsciousnessCmd.AddCommand(consciousnessStateCmd)
	maximusConsciousnessCmd.AddCommand(consciousnessESGTCmd)
	maximusConsciousnessCmd.AddCommand(consciousnessArousalCmd)
	maximusConsciousnessCmd.AddCommand(consciousnessMetricsCmd)
	maximusConsciousnessCmd.AddCommand(consciousnessWatchCmd)

	// ESGT subcommands
	consciousnessESGTCmd.AddCommand(consciousnessESGTEventsCmd)
	consciousnessESGTCmd.AddCommand(consciousnessESGTTriggerCmd)

	// Arousal subcommands
	consciousnessArousalCmd.AddCommand(consciousnessArousalAdjustCmd)

	// Global flags
	maximusCmd.PersistentFlags().StringVar(&maximusServer, "server", "", "MAXIMUS server address (default: env VCLI_MAXIMUS_ENDPOINT or localhost:50051)")
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

	// Maximus AI service endpoints
	maximusEurekaCmd.PersistentFlags().StringVar(&eurekaEndpoint, "eureka-endpoint", "http://localhost:8024", "Eureka service endpoint")
	maximusOraculoCmd.PersistentFlags().StringVar(&oraculoEndpoint, "oraculo-endpoint", "http://localhost:8026", "Oraculo service endpoint")
	maximusPredictCmd.PersistentFlags().StringVar(&predictEndpoint, "predict-endpoint", "http://localhost:8028", "Predict service endpoint")

	// Auth token for all AI services
	maximusEurekaCmd.PersistentFlags().StringVar(&maximusToken, "token", "", "Authentication token")
	maximusOraculoCmd.PersistentFlags().StringVar(&maximusToken, "token", "", "Authentication token")
	maximusPredictCmd.PersistentFlags().StringVar(&maximusToken, "token", "", "Authentication token")

	// Eureka flags
	eurekaGenerateInsightCmd.Flags().StringVar(&dataFile, "data-file", "", "Data file (JSON)")
	eurekaGenerateInsightCmd.Flags().StringVar(&dataType, "data-type", "", "Data type (logs, network_traffic, threat_intel)")
	eurekaGenerateInsightCmd.Flags().StringVar(&contextFile, "context-file", "", "Context file (JSON, optional)")

	eurekaDetectPatternCmd.Flags().StringVar(&dataFile, "data-file", "", "Data file (JSON)")
	eurekaDetectPatternCmd.Flags().StringVar(&patternFile, "pattern-file", "", "Pattern definition file (JSON)")

	eurekaExtractIoCsCmd.Flags().StringVar(&dataFile, "data-file", "", "Data file (JSON)")

	// Oraculo flags
	oraculoPredictCmd.Flags().StringVar(&dataFile, "data-file", "", "Data file (JSON)")
	oraculoPredictCmd.Flags().StringVar(&predictionType, "prediction-type", "", "Prediction type (threat_level, resource_demand)")
	oraculoPredictCmd.Flags().StringVar(&timeHorizon, "time-horizon", "", "Time horizon (24h, 7d)")

	oraculoAnalyzeCodeCmd.Flags().StringVar(&codeFile, "code-file", "", "Code file to analyze")
	oraculoAnalyzeCodeCmd.Flags().StringVar(&language, "language", "", "Programming language")
	oraculoAnalyzeCodeCmd.Flags().StringVar(&analysisType, "analysis-type", "", "Analysis type (vulnerability, performance, refactoring)")

	oraculoAutoImplementCmd.Flags().StringVar(&taskDesc, "task", "", "Task description")
	oraculoAutoImplementCmd.Flags().StringVar(&targetLang, "target-lang", "", "Target programming language")
	oraculoAutoImplementCmd.Flags().StringVar(&contextFile, "context-file", "", "Context file (JSON, optional)")

	// Predict flags
	predictGenerateCmd.Flags().StringVar(&dataFile, "data-file", "", "Data file (JSON)")
	predictGenerateCmd.Flags().StringVar(&predictionType, "prediction-type", "", "Prediction type (resource_demand, threat_likelihood)")
	predictGenerateCmd.Flags().StringVar(&timeHorizon, "time-horizon", "", "Time horizon (1h, 24h, optional)")

	// Consciousness flags
	maximusConsciousnessCmd.PersistentFlags().StringVar(&consciousnessEndpoint, "consciousness-endpoint", "http://localhost:8022", "Consciousness API endpoint")
	maximusConsciousnessCmd.PersistentFlags().StringVar(&consciousnessStreamURL, "consciousness-stream-url", "", "Override streaming endpoint (SSE/WebSocket)")

	// ESGT flags
	consciousnessESGTEventsCmd.Flags().IntVar(&esgtLimit, "limit", 20, "Maximum number of events (1-100)")
	consciousnessESGTTriggerCmd.Flags().Float64Var(&esgtNovelty, "novelty", 0.8, "Novelty score (0-1)")
	consciousnessESGTTriggerCmd.Flags().Float64Var(&esgtRelevance, "relevance", 0.8, "Relevance score (0-1)")
	consciousnessESGTTriggerCmd.Flags().Float64Var(&esgtUrgency, "urgency", 0.8, "Urgency score (0-1)")

	// Arousal flags
	consciousnessArousalAdjustCmd.Flags().Float64Var(&arousalDelta, "delta", 0.1, "Arousal delta (-0.5 to 0.5)")
	consciousnessArousalAdjustCmd.Flags().Float64Var(&arousalDuration, "duration", 5.0, "Duration in seconds (0.1-60)")
}
