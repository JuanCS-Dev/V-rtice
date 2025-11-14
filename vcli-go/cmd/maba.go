package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/maba"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	mabaServer string
	mabaURL    string
	mabaAction string
	mabaQuery  string
	mabaData   string
	mabaWait   bool
)

var mabaCmd = &cobra.Command{
	Use:   "maba",
	Short: "MAXIMUS Browser Agent - Autonomous web automation",
	Long: `MABA (MAXIMUS Browser Agent) provides autonomous browser automation
for MAXIMUS AI. Features include intelligent navigation, data extraction,
form automation, and cognitive map learning.`,
}

// ============================================================================
// BROWSER OPERATIONS
// ============================================================================

var mabaBrowserCmd = &cobra.Command{
	Use:   "browser",
	Short: "Browser automation operations",
	Long:  `Control browser sessions, navigate websites, and execute actions`,
}

var mabaBrowserNavigateCmd = &cobra.Command{
	Use:   "navigate [url]",
	Short: "Navigate to a URL",
	Long:  `Autonomously navigate to a URL with intelligent interaction`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runMabaBrowserNavigate,
}

func runMabaBrowserNavigate(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	req := &maba.NavigateRequest{
		URL:    args[0],
		Action: mabaAction,
		Wait:   mabaWait,
	}

	result, err := client.Navigate(req)
	if err != nil {
		return fmt.Errorf("navigation failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MABA Browser Navigation\n\n", styles.Accent.Render("🌐"))
	fmt.Printf("%s %s\n", styles.Muted.Render("URL:"), result.URL)
	fmt.Printf("%s %s\n", styles.Muted.Render("Title:"), result.Title)
	fmt.Printf("%s %d\n", styles.Muted.Render("Load Time:"), result.LoadTime)
	fmt.Printf("%s %s\n\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))

	if len(result.ExtractedData) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Extracted Data:"))
		for key, value := range result.ExtractedData {
			fmt.Printf("  %s: %v\n", styles.Muted.Render(key), value)
		}
	}

	return nil
}

var mabaBrowserExtractCmd = &cobra.Command{
	Use:   "extract [url]",
	Short: "Extract data from a webpage",
	Long:  `Intelligently extract structured data from a webpage`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runMabaBrowserExtract,
}

func runMabaBrowserExtract(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	req := &maba.ExtractRequest{
		URL:   args[0],
		Query: mabaQuery,
	}

	result, err := client.Extract(req)
	if err != nil {
		return fmt.Errorf("extraction failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MABA Data Extraction\n\n", styles.Accent.Render("📊"))
	fmt.Printf("%s %s\n", styles.Muted.Render("URL:"), result.URL)
	fmt.Printf("%s %d items\n\n", styles.Muted.Render("Extracted:"), len(result.Data))

	for i, item := range result.Data {
		fmt.Printf("%s Item %d\n", styles.Info.Render("📄"), i+1)
		for key, value := range item {
			fmt.Printf("  %s: %v\n", styles.Muted.Render(key), value)
		}
		fmt.Println()
	}

	return nil
}

var mabaBrowserSessionsCmd = &cobra.Command{
	Use:   "sessions",
	Short: "List active browser sessions",
	Long:  `Display all active browser sessions and their status`,
	RunE:  runMabaBrowserSessions,
}

func runMabaBrowserSessions(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	result, err := client.ListSessions()
	if err != nil {
		return fmt.Errorf("failed to list sessions: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MABA Browser Sessions\n\n", styles.Accent.Render("🖥️"))
	fmt.Printf("%s %d active sessions\n\n", styles.Muted.Render("Total:"), len(result.Sessions))

	for _, session := range result.Sessions {
		fmt.Printf("%s Session %s\n", getStatusIcon(session.Status), session.ID)
		fmt.Printf("  %s %s\n", styles.Muted.Render("URL:"), session.CurrentURL)
		fmt.Printf("  %s %d seconds\n", styles.Muted.Render("Duration:"), session.Duration)
		fmt.Printf("  %s %d%%\n\n", styles.Muted.Render("Resource:"), session.ResourceUsage)
	}

	return nil
}

// ============================================================================
// COGNITIVE MAP
// ============================================================================

var mabaMapCmd = &cobra.Command{
	Use:   "map",
	Short: "Cognitive map operations",
	Long:  `View and manage the learned website structure graph`,
}

var mabaMapQueryCmd = &cobra.Command{
	Use:   "query [domain]",
	Short: "Query cognitive map for a domain",
	Long:  `Retrieve learned navigation patterns for a domain`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runMabaMapQuery,
}

func runMabaMapQuery(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	req := &maba.MapQueryRequest{
		Domain: args[0],
	}

	result, err := client.QueryMap(req)
	if err != nil {
		return fmt.Errorf("map query failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Cognitive Map - %s\n\n", styles.Accent.Render("🧠"), result.Domain)
	fmt.Printf("%s %d pages\n", styles.Muted.Render("Known Pages:"), result.PageCount)
	fmt.Printf("%s %d paths\n", styles.Muted.Render("Navigation Paths:"), result.PathCount)
	fmt.Printf("%s %.1f%%\n\n", styles.Muted.Render("Confidence:"), result.Confidence*100)

	if len(result.CommonPaths) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Common Navigation Paths:"))
		for i, path := range result.CommonPaths {
			fmt.Printf("  %d. %s (used %d times)\n", i+1, path.Path, path.Usage)
		}
	}

	return nil
}

var mabaMapStatsCmd = &cobra.Command{
	Use:   "stats",
	Short: "Cognitive map statistics",
	Long:  `Display overall statistics for the cognitive map`,
	RunE:  runMabaMapStats,
}

func runMabaMapStats(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	result, err := client.MapStats()
	if err != nil {
		return fmt.Errorf("failed to get stats: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Cognitive Map Statistics\n\n", styles.Accent.Render("📈"))
	fmt.Printf("%s %d domains\n", styles.Muted.Render("Total Domains:"), result.TotalDomains)
	fmt.Printf("%s %d pages\n", styles.Muted.Render("Total Pages:"), result.TotalPages)
	fmt.Printf("%s %d paths\n", styles.Muted.Render("Total Paths:"), result.TotalPaths)
	fmt.Printf("%s %d interactions\n\n", styles.Muted.Render("Total Interactions:"), result.TotalInteractions)

	if len(result.TopDomains) > 0 {
		fmt.Printf("%s\n", styles.Info.Render("Most Visited Domains:"))
		for i, domain := range result.TopDomains {
			fmt.Printf("  %d. %s (%d visits)\n", i+1, domain.Domain, domain.Visits)
		}
	}

	return nil
}

// ============================================================================
// TOOLS & STATUS
// ============================================================================

var mabaToolsCmd = &cobra.Command{
	Use:   "tools",
	Short: "List registered MAXIMUS tools",
	Long:  `Display all browser tools registered with MAXIMUS Core`,
	RunE:  runMabaTools,
}

func runMabaTools(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	result, err := client.ListTools()
	if err != nil {
		return fmt.Errorf("failed to list tools: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MABA Tools\n\n", styles.Accent.Render("🔧"))
	fmt.Printf("%s %d tools registered\n\n", styles.Muted.Render("Total:"), len(result.Tools))

	for _, tool := range result.Tools {
		fmt.Printf("%s %s\n", getStatusIcon(tool.Status), tool.Name)
		fmt.Printf("  %s %s\n", styles.Muted.Render("Description:"), tool.Description)
		fmt.Printf("  %s %d times\n\n", styles.Muted.Render("Usage:"), tool.UsageCount)
	}

	return nil
}

var mabaStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "MABA service status",
	Long:  `Display current status and health of MABA service`,
	RunE:  runMabaStatus,
}

func runMabaStatus(cmd *cobra.Command, args []string) error {
	client := maba.NewMABAClient(getMABAServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s MABA Service Status\n\n", styles.Accent.Render("🚀"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %d active\n", styles.Muted.Render("Browser Sessions:"), result.ActiveSessions)
	fmt.Printf("%s %d pages\n", styles.Muted.Render("Cognitive Map:"), result.MapSize)
	fmt.Printf("%s %.1f%%\n", styles.Muted.Render("Resource Usage:"), result.ResourceUsage)
	fmt.Printf("%s %d\n", styles.Muted.Render("Tools Registered:"), result.ToolsRegistered)

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

	// Browser operations
	mabaCmd.AddCommand(mabaBrowserCmd)
	mabaBrowserCmd.AddCommand(mabaBrowserNavigateCmd)
	mabaBrowserCmd.AddCommand(mabaBrowserExtractCmd)
	mabaBrowserCmd.AddCommand(mabaBrowserSessionsCmd)

	// Cognitive map
	mabaCmd.AddCommand(mabaMapCmd)
	mabaMapCmd.AddCommand(mabaMapQueryCmd)
	mabaMapCmd.AddCommand(mabaMapStatsCmd)

	// Tools & status
	mabaCmd.AddCommand(mabaToolsCmd)
	mabaCmd.AddCommand(mabaStatusCmd)

	// Flags
	mabaCmd.PersistentFlags().StringVarP(&mabaServer, "server", "s", "", "MABA server endpoint")

	mabaBrowserNavigateCmd.Flags().StringVar(&mabaAction, "action", "", "Action to perform (click, fill, submit)")
	mabaBrowserNavigateCmd.Flags().BoolVar(&mabaWait, "wait", false, "Wait for page load")

	mabaBrowserExtractCmd.Flags().StringVarP(&mabaQuery, "query", "q", "", "Extraction query/selector")
}
