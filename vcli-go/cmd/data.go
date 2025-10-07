package main

import (
	"encoding/json"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/data"
	"github.com/verticedev/vcli-go/internal/graph"
	"github.com/verticedev/vcli-go/internal/narrative"
	"github.com/verticedev/vcli-go/internal/triage"
)

// Main data command
var dataCmd = &cobra.Command{
	Use:   "data",
	Short: "Data and graph operations",
	Long:  "Data services: graph (Seriema), ingest (Tatacá), rte (Real-Time Execution), narrative (Cognitive Defense)",
}

// ============================================================================
// SERIEMA GRAPH COMMANDS
// ============================================================================

var graphCmd = &cobra.Command{
	Use:   "graph",
	Short: "Seriema Graph operations",
	Long:  "Argument framework storage and graph analysis",
}

var graphStoreCmd = &cobra.Command{Use: "store", Short: "Store framework", RunE: runGraphStore}
var graphGetCmd = &cobra.Command{Use: "get <framework_id>", Short: "Get framework", Args: cobra.ExactArgs(1), RunE: runGraphGet}
var graphCentralityCmd = &cobra.Command{Use: "centrality <framework_id>", Short: "Calculate centrality metrics", Args: cobra.ExactArgs(1), RunE: runGraphCentrality}
var graphPathsCmd = &cobra.Command{Use: "paths <framework_id>", Short: "Find paths between arguments", Args: cobra.ExactArgs(1), RunE: runGraphPaths}
var graphNeighborhoodCmd = &cobra.Command{Use: "neighborhood <framework_id> <argument_id>", Short: "Get argument neighborhood", Args: cobra.ExactArgs(2), RunE: runGraphNeighborhood}
var graphCircularCmd = &cobra.Command{Use: "circular <framework_id>", Short: "Detect circular arguments", Args: cobra.ExactArgs(1), RunE: runGraphCircular}
var graphStatsCmd = &cobra.Command{Use: "stats <framework_id>", Short: "Get framework statistics", Args: cobra.ExactArgs(1), RunE: runGraphStats}
var graphHealthCmd = &cobra.Command{Use: "health", Short: "Check health", RunE: runGraphHealth}

// ============================================================================
// TATACÁ INGESTION COMMANDS
// ============================================================================

var ingestCmd = &cobra.Command{
	Use:   "ingest",
	Short: "Tatacá Ingestion operations",
	Long:  "ETL pipeline for criminal investigation data",
}

var ingestCreateCmd = &cobra.Command{Use: "create", Short: "Create ingestion job", RunE: runIngestCreate}
var ingestStatusCmd = &cobra.Command{Use: "status <job_id>", Short: "Get job status", Args: cobra.ExactArgs(1), RunE: runIngestStatus}
var ingestListCmd = &cobra.Command{Use: "list", Short: "List ingestion jobs", RunE: runIngestList}
var ingestTriggerCmd = &cobra.Command{Use: "trigger", Short: "Quick trigger ingestion", RunE: runIngestTrigger}
var ingestSourcesCmd = &cobra.Command{Use: "sources", Short: "List data sources", RunE: runIngestSources}
var ingestEntitiesCmd = &cobra.Command{Use: "entities", Short: "List entity types", RunE: runIngestEntities}
var ingestStatsCmd = &cobra.Command{Use: "stats", Short: "Get statistics", RunE: runIngestStats}
var ingestCancelCmd = &cobra.Command{Use: "cancel <job_id>", Short: "Cancel job", Args: cobra.ExactArgs(1), RunE: runIngestCancel}
var ingestHealthCmd = &cobra.Command{Use: "health", Short: "Check health", RunE: runIngestHealth}

// ============================================================================
// RTE (REAL-TIME EXECUTION) COMMANDS
// ============================================================================

var rteCmd = &cobra.Command{
	Use:   "rte",
	Short: "Real-Time Execution operations",
	Long:  "High-speed threat response and data stream processing",
}

var rteExecuteCmd = &cobra.Command{Use: "execute", Short: "Execute real-time command", RunE: runRTEExecute}
var rteIngestCmd = &cobra.Command{Use: "ingest-stream", Short: "Ingest data stream", RunE: runRTEIngest}
var rteHealthCmd = &cobra.Command{Use: "health", Short: "Check health", RunE: runRTEHealth}

// ============================================================================
// NARRATIVE FILTER COMMANDS
// ============================================================================

var narrativeCmd = &cobra.Command{
	Use:   "narrative",
	Short: "Narrative Manipulation Filter operations",
	Long:  "Cognitive Defense System - narrative manipulation detection",
}

var narrativeAnalyzeCmd = &cobra.Command{Use: "analyze", Short: "Analyze content", RunE: runNarrativeAnalyze}
var narrativeHealthCmd = &cobra.Command{Use: "health", Short: "Check health", RunE: runNarrativeHealth}
var narrativeSimpleHealthCmd = &cobra.Command{Use: "simple-health", Short: "Simple health check", RunE: runNarrativeSimpleHealth}
var narrativeCacheStatsCmd = &cobra.Command{Use: "cache-stats", Short: "Get cache statistics", RunE: runNarrativeCacheStats}
var narrativeDbStatsCmd = &cobra.Command{Use: "db-stats", Short: "Get database statistics", RunE: runNarrativeDbStats}
var narrativeInfoCmd = &cobra.Command{Use: "info", Short: "Get service info", RunE: runNarrativeInfo}

// ============================================================================
// FLAGS
// ============================================================================

var (
	graphEndpoint     string
	ingestEndpoint    string
	rteEndpoint       string
	narrativeEndpoint string
	dataToken         string

	// Graph flags
	frameworkFile string
	pathsFile     string
	distance      int

	// Ingestion flags
	jobFile      string
	triggerFile  string
	statusFilter string
	jobLimit     int

	// RTE flags
	commandFile string
	streamFile  string

	// Narrative flags
	narrativeAnalysisFile string
)

// ============================================================================
// INIT
// ============================================================================

func init() {
	rootCmd.AddCommand(dataCmd)

	dataCmd.AddCommand(graphCmd)
	dataCmd.AddCommand(ingestCmd)
	dataCmd.AddCommand(rteCmd)
	dataCmd.AddCommand(narrativeCmd)

	// Graph subcommands
	graphCmd.AddCommand(graphStoreCmd, graphGetCmd, graphCentralityCmd, graphPathsCmd,
		graphNeighborhoodCmd, graphCircularCmd, graphStatsCmd, graphHealthCmd)

	// Ingestion subcommands
	ingestCmd.AddCommand(ingestCreateCmd, ingestStatusCmd, ingestListCmd, ingestTriggerCmd,
		ingestSourcesCmd, ingestEntitiesCmd, ingestStatsCmd, ingestCancelCmd, ingestHealthCmd)

	// RTE subcommands
	rteCmd.AddCommand(rteExecuteCmd, rteIngestCmd, rteHealthCmd)

	// Narrative subcommands
	narrativeCmd.AddCommand(narrativeAnalyzeCmd, narrativeHealthCmd, narrativeSimpleHealthCmd,
		narrativeCacheStatsCmd, narrativeDbStatsCmd, narrativeInfoCmd)

	// Persistent flags for endpoints
	graphCmd.PersistentFlags().StringVar(&graphEndpoint, "graph-endpoint", "http://localhost:8040", "Seriema Graph endpoint")
	ingestCmd.PersistentFlags().StringVar(&ingestEndpoint, "ingest-endpoint", "http://localhost:8041", "Tatacá Ingestion endpoint")
	rteCmd.PersistentFlags().StringVar(&rteEndpoint, "rte-endpoint", "http://localhost:8038", "RTE Service endpoint")
	narrativeCmd.PersistentFlags().StringVar(&narrativeEndpoint, "narrative-endpoint", "http://localhost:8042", "Narrative Filter endpoint")

	dataCmd.PersistentFlags().StringVar(&dataToken, "token", "", "Authentication token")

	// Graph flags
	graphStoreCmd.Flags().StringVar(&frameworkFile, "framework-file", "", "Framework JSON file")
	graphStoreCmd.MarkFlagRequired("framework-file")

	graphPathsCmd.Flags().StringVar(&pathsFile, "paths-file", "", "Paths query JSON file")
	graphPathsCmd.MarkFlagRequired("paths-file")

	graphNeighborhoodCmd.Flags().IntVar(&distance, "distance", 1, "Neighborhood distance")

	// Ingestion flags
	ingestCreateCmd.Flags().StringVar(&jobFile, "job-file", "", "Job request JSON file")
	ingestCreateCmd.MarkFlagRequired("job-file")

	ingestListCmd.Flags().StringVar(&statusFilter, "status", "", "Filter by status (pending, running, completed, failed)")
	ingestListCmd.Flags().IntVar(&jobLimit, "limit", 100, "Maximum number of jobs")

	ingestTriggerCmd.Flags().StringVar(&triggerFile, "trigger-file", "", "Trigger request JSON file")
	ingestTriggerCmd.MarkFlagRequired("trigger-file")

	// RTE flags
	rteExecuteCmd.Flags().StringVar(&commandFile, "command-file", "", "Command JSON file")
	rteExecuteCmd.MarkFlagRequired("command-file")

	rteIngestCmd.Flags().StringVar(&streamFile, "stream-file", "", "Stream data JSON file")
	rteIngestCmd.MarkFlagRequired("stream-file")

	// Narrative flags
	narrativeAnalyzeCmd.Flags().StringVar(&narrativeAnalysisFile, "analysis-file", "", "Analysis request JSON file")
	narrativeAnalyzeCmd.MarkFlagRequired("analysis-file")
}

// ============================================================================
// GRAPH COMMAND IMPLEMENTATIONS
// ============================================================================

func runGraphStore(cmd *cobra.Command, args []string) error {
	client := graph.NewSeriemaClient(graphEndpoint, dataToken)

	frameworkData, err := readJSONFile(frameworkFile)
	if err != nil {
		return err
	}

	var framework graph.Framework
	jsonBytes, _ := json.Marshal(frameworkData)
	json.Unmarshal(jsonBytes, &framework)

	result, err := client.StoreFramework(framework)
	if err != nil {
		return err
	}

	printJSON(result)
	return nil
}

func runGraphGet(cmd *cobra.Command, args []string) error {
	client := graph.NewSeriemaClient(graphEndpoint, dataToken)
	result, err := client.GetFramework(args[0])
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runGraphCentrality(cmd *cobra.Command, args []string) error {
	client := graph.NewSeriemaClient(graphEndpoint, dataToken)
	result, err := client.GetCentrality(args[0])
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runGraphPaths(cmd *cobra.Command, args []string) error {
	client := graph.NewSeriemaClient(graphEndpoint, dataToken)

	pathsData, err := readJSONFile(pathsFile)
	if err != nil {
		return err
	}

	var pathsReq graph.PathsRequest
	jsonBytes, _ := json.Marshal(pathsData)
	json.Unmarshal(jsonBytes, &pathsReq)

	result, err := client.FindPaths(args[0], pathsReq)
	if err != nil {
		return err
	}

	printJSON(result)
	return nil
}

func runGraphNeighborhood(cmd *cobra.Command, args []string) error {
	client := graph.NewSeriemaClient(graphEndpoint, dataToken)
	result, err := client.GetNeighborhood(args[0], args[1], distance)
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runGraphCircular(cmd *cobra.Command, args []string) error {
	client := graph.NewSeriemaClient(graphEndpoint, dataToken)
	result, err := client.GetCircularArguments(args[0])
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runGraphStats(cmd *cobra.Command, args []string) error {
	client := graph.NewSeriemaClient(graphEndpoint, dataToken)
	result, err := client.GetStatistics(args[0])
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runGraphHealth(cmd *cobra.Command, args []string) error {
	client := graph.NewSeriemaClient(graphEndpoint, dataToken)
	result, _ := client.Health()
	printJSON(result)
	return nil
}

// ============================================================================
// INGESTION COMMAND IMPLEMENTATIONS
// ============================================================================

func runIngestCreate(cmd *cobra.Command, args []string) error {
	client := data.NewIngestionClient(ingestEndpoint, dataToken)

	jobData, err := readJSONFile(jobFile)
	if err != nil {
		return err
	}

	var jobReq data.IngestJobRequest
	jsonBytes, _ := json.Marshal(jobData)
	json.Unmarshal(jsonBytes, &jobReq)

	result, err := client.CreateJob(jobReq)
	if err != nil {
		return err
	}

	printJSON(result)
	return nil
}

func runIngestStatus(cmd *cobra.Command, args []string) error {
	client := data.NewIngestionClient(ingestEndpoint, dataToken)
	result, err := client.GetJobStatus(args[0])
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runIngestList(cmd *cobra.Command, args []string) error {
	client := data.NewIngestionClient(ingestEndpoint, dataToken)

	var status *data.JobStatus
	if statusFilter != "" {
		s := data.JobStatus(statusFilter)
		status = &s
	}

	result, err := client.ListJobs(status, jobLimit)
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runIngestTrigger(cmd *cobra.Command, args []string) error {
	client := data.NewIngestionClient(ingestEndpoint, dataToken)

	triggerData, err := readJSONFile(triggerFile)
	if err != nil {
		return err
	}

	var triggerReq data.TriggerIngestRequest
	jsonBytes, _ := json.Marshal(triggerData)
	json.Unmarshal(jsonBytes, &triggerReq)

	result, err := client.TriggerIngestion(triggerReq)
	if err != nil {
		return err
	}

	printJSON(result)
	return nil
}

func runIngestSources(cmd *cobra.Command, args []string) error {
	client := data.NewIngestionClient(ingestEndpoint, dataToken)
	result, err := client.ListSources()
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runIngestEntities(cmd *cobra.Command, args []string) error {
	client := data.NewIngestionClient(ingestEndpoint, dataToken)
	result, err := client.ListEntityTypes()
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runIngestStats(cmd *cobra.Command, args []string) error {
	client := data.NewIngestionClient(ingestEndpoint, dataToken)
	result, err := client.GetStatistics()
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runIngestCancel(cmd *cobra.Command, args []string) error {
	client := data.NewIngestionClient(ingestEndpoint, dataToken)
	result, err := client.CancelJob(args[0])
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runIngestHealth(cmd *cobra.Command, args []string) error {
	client := data.NewIngestionClient(ingestEndpoint, dataToken)
	result, _ := client.Health()
	printJSON(result)
	return nil
}

// ============================================================================
// RTE COMMAND IMPLEMENTATIONS
// ============================================================================

func runRTEExecute(cmd *cobra.Command, args []string) error {
	client := triage.NewRTEClient(rteEndpoint, dataToken)

	commandData, err := readJSONFile(commandFile)
	if err != nil {
		return err
	}

	var cmdReq triage.RealTimeCommand
	jsonBytes, _ := json.Marshal(commandData)
	json.Unmarshal(jsonBytes, &cmdReq)

	result, err := client.ExecuteCommand(cmdReq)
	if err != nil {
		return err
	}

	printJSON(result)
	return nil
}

func runRTEIngest(cmd *cobra.Command, args []string) error {
	client := triage.NewRTEClient(rteEndpoint, dataToken)

	streamData, err := readJSONFile(streamFile)
	if err != nil {
		return err
	}

	var ingestReq triage.DataStreamIngest
	jsonBytes, _ := json.Marshal(streamData)
	json.Unmarshal(jsonBytes, &ingestReq)

	result, err := client.IngestDataStream(ingestReq)
	if err != nil {
		return err
	}

	printJSON(result)
	return nil
}

func runRTEHealth(cmd *cobra.Command, args []string) error {
	client := triage.NewRTEClient(rteEndpoint, dataToken)
	result, _ := client.Health()
	printJSON(result)
	return nil
}

// ============================================================================
// NARRATIVE COMMAND IMPLEMENTATIONS
// ============================================================================

func runNarrativeAnalyze(cmd *cobra.Command, args []string) error {
	client := narrative.NewNarrativeFilterClient(narrativeEndpoint, dataToken)

	analysisData, err := readJSONFile(narrativeAnalysisFile)
	if err != nil {
		return err
	}

	var analysisReq narrative.AnalysisRequest
	jsonBytes, _ := json.Marshal(analysisData)
	json.Unmarshal(jsonBytes, &analysisReq)

	result, err := client.AnalyzeContent(analysisReq)
	if err != nil {
		return err
	}

	printJSON(result)
	return nil
}

func runNarrativeHealth(cmd *cobra.Command, args []string) error {
	client := narrative.NewNarrativeFilterClient(narrativeEndpoint, dataToken)
	result, _ := client.Health()
	printJSON(result)
	return nil
}

func runNarrativeSimpleHealth(cmd *cobra.Command, args []string) error {
	client := narrative.NewNarrativeFilterClient(narrativeEndpoint, dataToken)
	result, _ := client.SimpleHealth()
	printJSON(result)
	return nil
}

func runNarrativeCacheStats(cmd *cobra.Command, args []string) error {
	client := narrative.NewNarrativeFilterClient(narrativeEndpoint, dataToken)
	result, err := client.GetCacheStats()
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runNarrativeDbStats(cmd *cobra.Command, args []string) error {
	client := narrative.NewNarrativeFilterClient(narrativeEndpoint, dataToken)
	result, err := client.GetDatabaseStats()
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}

func runNarrativeInfo(cmd *cobra.Command, args []string) error {
	client := narrative.NewNarrativeFilterClient(narrativeEndpoint, dataToken)
	result, err := client.GetServiceInfo()
	if err != nil {
		return err
	}
	printJSON(result)
	return nil
}
