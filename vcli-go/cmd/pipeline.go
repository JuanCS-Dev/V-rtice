package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/pipeline"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	pipelineServer string
	pipelineSource string
	pipelineFormat string
	pipelineTopic  string
	pipelineMessage string
)

var pipelineCmd = &cobra.Command{
	Use:   "pipeline",
	Short: "Data Pipeline - Tataca ingestion, Seriema graph, Command bus",
	Long: `Data pipeline operations including Tataca ingestion, Seriema graph database,
and Command bus for event-driven architecture.`,
}

// ============================================================================
// TATACA INGESTION
// ============================================================================

var pipelineTatacaCmd = &cobra.Command{
	Use:   "tataca",
	Short: "Tataca data ingestion",
	Long:  `Ingest data from various sources into the platform`,
}

var pipelineTatacaIngestCmd = &cobra.Command{
	Use:   "ingest [source]",
	Short: "Ingest data from source",
	Long:  `Start data ingestion from specified source`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runPipelineTatacaIngest,
}

func runPipelineTatacaIngest(cmd *cobra.Command, args []string) error {
	client := pipeline.NewPipelineClient(getPipelineServer())
	req := &pipeline.IngestRequest{
		Source: args[0],
		Format: pipelineFormat,
	}

	result, err := client.Ingest(req)
	if err != nil {
		return fmt.Errorf("ingestion failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Tataca Data Ingestion\n\n", styles.Accent.Render("📥"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Source:"), result.Source)
	fmt.Printf("%s %d records\n", styles.Muted.Render("Ingested:"), result.RecordsIngested)
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))

	return nil
}

// ============================================================================
// SERIEMA GRAPH
// ============================================================================

var pipelineSeriemaCmd = &cobra.Command{
	Use:   "seriema",
	Short: "Seriema graph database",
	Long:  `Graph database operations for threat relationships`,
}

var pipelineSeriemaQueryCmd = &cobra.Command{
	Use:   "query [cypher]",
	Short: "Execute Cypher query",
	Long:  `Run a Cypher query against the graph database`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runPipelineSeriemaQuery,
}

func runPipelineSeriemaQuery(cmd *cobra.Command, args []string) error {
	client := pipeline.NewPipelineClient(getPipelineServer())
	req := &pipeline.GraphQueryRequest{
		Cypher: args[0],
	}

	result, err := client.GraphQuery(req)
	if err != nil {
		return fmt.Errorf("graph query failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Seriema Graph Query\n\n", styles.Accent.Render("🕸️"))
	fmt.Printf("%s %d results\n\n", styles.Muted.Render("Results:"), len(result.Results))

	for i, res := range result.Results {
		fmt.Printf("%s Result %d\n", styles.Info.Render(fmt.Sprintf("#%d", i+1)), i+1)
		for key, value := range res {
			fmt.Printf("  %s: %v\n", key, value)
		}
		fmt.Println()
	}

	return nil
}

var pipelineSeriemaVisualizeCmd = &cobra.Command{
	Use:   "visualize [entity]",
	Short: "Visualize entity relationships",
	Long:  `Generate visual graph of entity relationships`,
	Args:  cobra.MinimumNArgs(1),
	RunE:  runPipelineSeriemaVisualize,
}

func runPipelineSeriemaVisualize(cmd *cobra.Command, args []string) error {
	client := pipeline.NewPipelineClient(getPipelineServer())
	req := &pipeline.VisualizeRequest{
		Entity: args[0],
	}

	result, err := client.Visualize(req)
	if err != nil {
		return fmt.Errorf("visualization failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Graph Visualization - %s\n\n", styles.Accent.Render("🌐"), result.Entity)
	fmt.Printf("%s %d nodes\n", styles.Muted.Render("Nodes:"), result.NodeCount)
	fmt.Printf("%s %d edges\n", styles.Muted.Render("Edges:"), result.EdgeCount)
	fmt.Printf("%s %s\n", styles.Muted.Render("Graph URL:"), result.GraphURL)

	return nil
}

// ============================================================================
// COMMAND BUS
// ============================================================================

var pipelineBusCmd = &cobra.Command{
	Use:   "bus",
	Short: "Command bus operations",
	Long:  `Event-driven command bus for service communication`,
}

var pipelineBusPublishCmd = &cobra.Command{
	Use:   "publish",
	Short: "Publish command to bus",
	Long:  `Publish a command message to the command bus`,
	RunE:  runPipelineBusPublish,
}

func runPipelineBusPublish(cmd *cobra.Command, args []string) error {
	client := pipeline.NewPipelineClient(getPipelineServer())
	req := &pipeline.CommandRequest{
		Topic:   pipelineTopic,
		Message: pipelineMessage,
	}

	result, err := client.PublishCommand(req)
	if err != nil {
		return fmt.Errorf("publish failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Command Published\n\n", styles.Accent.Render("📤"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Topic:"), result.Topic)
	fmt.Printf("%s %s\n", styles.Muted.Render("Message ID:"), result.MessageID)
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))

	return nil
}

var pipelineBusListCmd = &cobra.Command{
	Use:   "list",
	Short: "List command topics",
	Long:  `Display all available command bus topics`,
	RunE:  runPipelineBusList,
}

func runPipelineBusList(cmd *cobra.Command, args []string) error {
	client := pipeline.NewPipelineClient(getPipelineServer())
	result, err := client.ListTopics()
	if err != nil {
		return fmt.Errorf("failed to list topics: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Command Bus Topics\n\n", styles.Accent.Render("📋"))

	for _, topic := range result.Topics {
		fmt.Printf("%s %s\n", styles.Info.Render("Topic:"), topic.Name)
		fmt.Printf("  %s %d subscribers\n", styles.Muted.Render("Subscribers:"), topic.Subscribers)
		fmt.Printf("  %s %d messages\n\n", styles.Muted.Render("Messages:"), topic.MessageCount)
	}

	return nil
}

// ============================================================================
// STATUS
// ============================================================================

var pipelineStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Pipeline service status",
	RunE:  runPipelineStatus,
}

func runPipelineStatus(cmd *cobra.Command, args []string) error {
	client := pipeline.NewPipelineClient(getPipelineServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Pipeline Status\n\n", styles.Accent.Render("⚙️"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %d records\n", styles.Muted.Render("Tataca Ingested:"), result.TatacaIngested)
	fmt.Printf("%s %d nodes\n", styles.Muted.Render("Seriema Nodes:"), result.SeriemaNodes)
	fmt.Printf("%s %d messages\n", styles.Muted.Render("Bus Messages:"), result.BusMessages)

	return nil
}

func getPipelineServer() string {
	if pipelineServer != "" {
		return pipelineServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(pipelineCmd)

	// Tataca
	pipelineCmd.AddCommand(pipelineTatacaCmd)
	pipelineTatacaCmd.AddCommand(pipelineTatacaIngestCmd)

	// Seriema
	pipelineCmd.AddCommand(pipelineSeriemaCmd)
	pipelineSeriemaCmd.AddCommand(pipelineSeriemaQueryCmd)
	pipelineSeriemaCmd.AddCommand(pipelineSeriemaVisualizeCmd)

	// Command Bus
	pipelineCmd.AddCommand(pipelineBusCmd)
	pipelineBusCmd.AddCommand(pipelineBusPublishCmd)
	pipelineBusCmd.AddCommand(pipelineBusListCmd)

	// Status
	pipelineCmd.AddCommand(pipelineStatusCmd)

	// Flags
	pipelineCmd.PersistentFlags().StringVarP(&pipelineServer, "server", "s", "", "Pipeline server endpoint")
	pipelineTatacaIngestCmd.Flags().StringVar(&pipelineFormat, "format", "json", "Data format")
	pipelineBusPublishCmd.Flags().StringVar(&pipelineTopic, "topic", "commands", "Command topic")
	pipelineBusPublishCmd.Flags().StringVar(&pipelineMessage, "message", "", "Command message (JSON)")
}
