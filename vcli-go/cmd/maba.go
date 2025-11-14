package cmd

import (
	"context"
	"fmt"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/maba"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	mabaServer   string
	mabaURL      string
	mabaSelector string
	mabaWait     bool
	mabaHeadless bool
)

var mabaCmd = &cobra.Command{
	Use:   "maba",
	Short: "MAXIMUS Browser Agent - Autonomous web automation",
	Long: `MABA (MAXIMUS Browser Agent) provides autonomous browser automation
for MAXIMUS AI. Features include intelligent navigation, data extraction,
form automation, and cognitive map learning.`,
}

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

var mabaSessionCmd = &cobra.Command{
	Use:   "session",
	Short: "Browser session management",
	Long:  `Create, list, and close browser sessions`,
}

var mabaSessionCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new browser session",
	Long:  `Create a new browser session with specified viewport and options`,
	RunE:  runMabaSessionCreate,
}

func runMabaSessionCreate(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	req := &maba.SessionRequest{
		Headless:       mabaHeadless,
		ViewportWidth:  1920,
		ViewportHeight: 1080,
	}

	result, err := client.CreateSession(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to create session: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MABA Browser Session Created\n\n", styles.Accent.Render("🌐"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Session ID:"), result.SessionID)
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("\n%s Use this session ID for browser operations\n", styles.Info.Render("ℹ️"))
	fmt.Printf("%s vcli maba navigate --session %s https://example.com\n", styles.Muted.Render("Example:"), result.SessionID)

	return nil
}

var mabaSessionCloseCmd = &cobra.Command{
	Use:   "close [session-id]",
	Short: "Close a browser session",
	Long:  `Close and cleanup an existing browser session`,
	Args:  cobra.ExactArgs(1),
	RunE:  runMabaSessionClose,
}

func runMabaSessionClose(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	sessionID := args[0]
	err := client.CloseSession(ctx, sessionID)
	if err != nil {
		return fmt.Errorf("failed to close session: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Session %s closed successfully\n", styles.Success.Render("✓"), sessionID)

	return nil
}

// ============================================================================
// NAVIGATION
// ============================================================================

var mabaNavigateCmd = &cobra.Command{
	Use:   "navigate [url] --session [session-id]",
	Short: "Navigate to a URL",
	Long:  `Navigate to a URL in an existing browser session`,
	Args:  cobra.ExactArgs(1),
	RunE:  runMabaNavigate,
}

var mabaSessionID string

func runMabaNavigate(cmd *cobra.Command, args []string) error {
	if mabaSessionID == "" {
		return fmt.Errorf("session-id is required (use --session flag or create a session first)")
	}

	client := maba.NewMABAClient(getMABAServer())
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	req := &maba.NavigateRequest{
		URL:       args[0],
		WaitUntil: "networkidle",
		TimeoutMs: 30000,
	}

	result, err := client.Navigate(ctx, mabaSessionID, req)
	if err != nil {
		return fmt.Errorf("navigation failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MABA Browser Navigation\n\n", styles.Accent.Render("🌐"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %.2f ms\n", styles.Muted.Render("Execution Time:"), result.ExecutionTimeMs)

	if result.Result != nil && len(result.Result) > 0 {
		fmt.Printf("\n%s\n", styles.Info.Render("Result:"))
		for key, value := range result.Result {
			fmt.Printf("  %s: %v\n", styles.Muted.Render(key), value)
		}
	}

	return nil
}

// ============================================================================
// DATA EXTRACTION
// ============================================================================

var mabaExtractCmd = &cobra.Command{
	Use:   "extract --session [session-id] --selector [css-selector]",
	Short: "Extract data from current page",
	Long:  `Extract data from the current page using CSS selectors`,
	RunE:  runMabaExtract,
}

func runMabaExtract(cmd *cobra.Command, args []string) error {
	if mabaSessionID == "" {
		return fmt.Errorf("session-id is required (use --session flag)")
	}
	if mabaSelector == "" {
		return fmt.Errorf("selector is required (use --selector flag)")
	}

	client := maba.NewMABAClient(getMABAServer())
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	req := &maba.ExtractRequest{
		Selectors: map[string]string{
			"data": mabaSelector,
		},
		ExtractAll: false,
	}

	result, err := client.Extract(ctx, mabaSessionID, req)
	if err != nil {
		return fmt.Errorf("extraction failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MABA Data Extraction\n\n", styles.Accent.Render("📊"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %.2f ms\n\n", styles.Muted.Render("Execution Time:"), result.ExecutionTimeMs)

	if result.Result != nil && len(result.Result) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Extracted Data:"))
		for key, value := range result.Result {
			fmt.Printf("  %s: %v\n", styles.Muted.Render(key), value)
		}
	}

	return nil
}

// ============================================================================
// BROWSER ACTIONS
// ============================================================================

var mabaClickCmd = &cobra.Command{
	Use:   "click --session [session-id] --selector [css-selector]",
	Short: "Click an element on the page",
	Long:  `Click an element specified by CSS selector`,
	RunE:  runMabaClick,
}

func runMabaClick(cmd *cobra.Command, args []string) error {
	if mabaSessionID == "" {
		return fmt.Errorf("session-id is required (use --session flag)")
	}
	if mabaSelector == "" {
		return fmt.Errorf("selector is required (use --selector flag)")
	}

	client := maba.NewMABAClient(getMABAServer())
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	req := &maba.ClickRequest{
		Selector:   mabaSelector,
		Button:     "left",
		ClickCount: 1,
		TimeoutMs:  30000,
	}

	result, err := client.Click(ctx, mabaSessionID, req)
	if err != nil {
		return fmt.Errorf("click failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Element clicked successfully\n", styles.Success.Render("✓"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), result.Status)

	return nil
}

// ============================================================================
// COGNITIVE MAP
// ============================================================================

var mabaMapCmd = &cobra.Command{
	Use:   "map",
	Short: "Cognitive map operations",
	Long:  `Query the cognitive map for learned patterns`,
}

var mabaMapQueryCmd = &cobra.Command{
	Use:   "query",
	Short: "Query cognitive map",
	Long:  `Query the cognitive map for navigation patterns`,
	RunE:  runMabaMapQuery,
}

var mapQueryType string
var mapFromURL string
var mapToURL string

func runMabaMapQuery(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	req := &maba.CognitiveMapQueryRequest{
		QueryType: mapQueryType,
		Parameters: map[string]interface{}{
			"from_url": mapFromURL,
			"to_url":   mapToURL,
		},
	}

	result, err := client.QueryCognitiveMap(ctx, req)
	if err != nil {
		return fmt.Errorf("map query failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Cognitive Map Query\n\n", styles.Accent.Render("🧠"))
	fmt.Printf("%s %v\n", styles.Muted.Render("Found:"), result.Found)
	fmt.Printf("%s %.1f%%\n\n", styles.Muted.Render("Confidence:"), result.Confidence*100)

	if result.Result != nil && len(result.Result) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Result:"))
		for key, value := range result.Result {
			fmt.Printf("  %s: %v\n", styles.Muted.Render(key), value)
		}
	}

	return nil
}

// ============================================================================
// STATS & HEALTH
// ============================================================================

var mabaStatsCmd = &cobra.Command{
	Use:   "stats",
	Short: "MABA service statistics",
	Long:  `Display current statistics and health of MABA service`,
	RunE:  runMabaStats,
}

func runMabaStats(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	result, err := client.GetStats(ctx)
	if err != nil {
		return fmt.Errorf("failed to get stats: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MABA Service Statistics\n\n", styles.Accent.Render("📈"))
	fmt.Printf("%s %.1f seconds\n\n", styles.Muted.Render("Uptime:"), result.UptimeSeconds)

	if result.CognitiveMap != nil && len(result.CognitiveMap) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Cognitive Map:"))
		for key, value := range result.CognitiveMap {
			fmt.Printf("  %s: %v\n", styles.Muted.Render(key), value)
		}
		fmt.Println()
	}

	if result.Browser != nil && len(result.Browser) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Browser:"))
		for key, value := range result.Browser {
			fmt.Printf("  %s: %v\n", styles.Muted.Render(key), value)
		}
	}

	return nil
}

// ============================================================================
// HELPERS
// ============================================================================

func getMABAServer() string {
	if mabaServer != "" {
		return mabaServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(mabaCmd)

	// Session management
	mabaCmd.AddCommand(mabaSessionCmd)
	mabaSessionCmd.AddCommand(mabaSessionCreateCmd)
	mabaSessionCmd.AddCommand(mabaSessionCloseCmd)
	mabaSessionCreateCmd.Flags().BoolVar(&mabaHeadless, "headless", true, "Run browser in headless mode")

	// Navigation
	mabaCmd.AddCommand(mabaNavigateCmd)
	mabaNavigateCmd.Flags().StringVar(&mabaSessionID, "session", "", "Browser session ID (required)")
	mabaNavigateCmd.MarkFlagRequired("session")

	// Extraction
	mabaCmd.AddCommand(mabaExtractCmd)
	mabaExtractCmd.Flags().StringVar(&mabaSessionID, "session", "", "Browser session ID (required)")
	mabaExtractCmd.Flags().StringVar(&mabaSelector, "selector", "", "CSS selector (required)")
	mabaExtractCmd.MarkFlagRequired("session")
	mabaExtractCmd.MarkFlagRequired("selector")

	// Browser actions
	mabaCmd.AddCommand(mabaClickCmd)
	mabaClickCmd.Flags().StringVar(&mabaSessionID, "session", "", "Browser session ID (required)")
	mabaClickCmd.Flags().StringVar(&mabaSelector, "selector", "", "CSS selector (required)")
	mabaClickCmd.MarkFlagRequired("session")
	mabaClickCmd.MarkFlagRequired("selector")

	// Cognitive map
	mabaCmd.AddCommand(mabaMapCmd)
	mabaMapCmd.AddCommand(mabaMapQueryCmd)
	mabaMapQueryCmd.Flags().StringVar(&mapQueryType, "type", "get_path", "Query type (find_element, get_path)")
	mabaMapQueryCmd.Flags().StringVar(&mapFromURL, "from", "", "From URL")
	mabaMapQueryCmd.Flags().StringVar(&mapToURL, "to", "", "To URL")

	// Stats
	mabaCmd.AddCommand(mabaStatsCmd)

	// Global flags
	mabaCmd.PersistentFlags().StringVarP(&mabaServer, "server", "s", "", "MABA server endpoint")
}
