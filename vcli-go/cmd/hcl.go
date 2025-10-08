package main

import (
	"encoding/json"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/hcl"
)

var hclCmd = &cobra.Command{
	Use:   "hcl",
	Short: "Homeostatic Control Loop operations",
	Long:  "HCL services: analyzer (anomaly detection), planner (resource planning), executor (plan execution)",
}

// Analyzer commands
var analyzerCmd = &cobra.Command{
	Use:   "analyzer",
	Short: "HCL Analyzer operations",
	Long:  "Analyze system metrics, detect anomalies, assess health",
}

var analyzerAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze system metrics",
	RunE:  runAnalyzerAnalyze,
}

var analyzerHistoryCmd = &cobra.Command{
	Use:   "history",
	Short: "Get analysis history",
	RunE:  runAnalyzerHistory,
}

var analyzerHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check analyzer health",
	RunE:  runAnalyzerHealth,
}

// Planner commands
var plannerCmd = &cobra.Command{
	Use:   "planner",
	Short: "HCL Planner operations",
	Long:  "Generate resource alignment plans based on analysis",
}

var plannerGenerateCmd = &cobra.Command{
	Use:   "generate",
	Short: "Generate resource plan",
	RunE:  runPlannerGenerate,
}

var plannerStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get planner status",
	RunE:  runPlannerStatus,
}

var plannerHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check planner health",
	RunE:  runPlannerHealth,
}

// Executor commands
var executorCmd = &cobra.Command{
	Use:   "executor",
	Short: "HCL Executor operations",
	Long:  "Execute resource alignment plans",
}

var executorExecuteCmd = &cobra.Command{
	Use:   "execute",
	Short: "Execute a plan",
	RunE:  runExecutorExecute,
}

var executorK8sStatusCmd = &cobra.Command{
	Use:   "k8s-status",
	Short: "Get Kubernetes status",
	RunE:  runExecutorK8sStatus,
}

var executorHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check executor health",
	RunE:  runExecutorHealth,
}

// Flags
var (
	analyzerEndpoint string
	plannerEndpoint  string
	executorEndpoint string
	hclToken         string

	metricsFile      string
	analysisFile     string
	stateFile        string
	goalsFile        string
	planFile         string
	historyLimit     int
	executePriority  int
)

func init() {
	rootCmd.AddCommand(hclCmd)

	hclCmd.AddCommand(analyzerCmd)
	hclCmd.AddCommand(plannerCmd)
	hclCmd.AddCommand(executorCmd)

	analyzerCmd.AddCommand(analyzerAnalyzeCmd)
	analyzerCmd.AddCommand(analyzerHistoryCmd)
	analyzerCmd.AddCommand(analyzerHealthCmd)

	plannerCmd.AddCommand(plannerGenerateCmd)
	plannerCmd.AddCommand(plannerStatusCmd)
	plannerCmd.AddCommand(plannerHealthCmd)

	executorCmd.AddCommand(executorExecuteCmd)
	executorCmd.AddCommand(executorK8sStatusCmd)
	executorCmd.AddCommand(executorHealthCmd)

	analyzerCmd.PersistentFlags().StringVar(&analyzerEndpoint, "analyzer-endpoint", "http://localhost:8015", "Analyzer service endpoint")
	plannerCmd.PersistentFlags().StringVar(&plannerEndpoint, "planner-endpoint", "http://localhost:8019", "Planner service endpoint")
	executorCmd.PersistentFlags().StringVar(&executorEndpoint, "executor-endpoint", "http://localhost:8016", "Executor service endpoint")

	hclCmd.PersistentFlags().StringVar(&hclToken, "token", "", "Authentication token")

	analyzerAnalyzeCmd.Flags().StringVar(&metricsFile, "metrics-file", "", "System metrics file (JSON)")
	analyzerAnalyzeCmd.MarkFlagRequired("metrics-file")
	analyzerHistoryCmd.Flags().IntVar(&historyLimit, "limit", 10, "Number of results")

	plannerGenerateCmd.Flags().StringVar(&analysisFile, "analysis-file", "", "Analysis result file (JSON)")
	plannerGenerateCmd.Flags().StringVar(&stateFile, "state-file", "", "Current state file (JSON)")
	plannerGenerateCmd.Flags().StringVar(&goalsFile, "goals-file", "", "Operational goals file (JSON)")
	plannerGenerateCmd.MarkFlagRequired("analysis-file")
	plannerGenerateCmd.MarkFlagRequired("state-file")
	plannerGenerateCmd.MarkFlagRequired("goals-file")

	executorExecuteCmd.Flags().StringVar(&planFile, "plan-file", "", "Plan file (JSON)")
	executorExecuteCmd.Flags().IntVar(&executePriority, "priority", 5, "Execution priority (1-10)")
	executorExecuteCmd.MarkFlagRequired("plan-file")
}

func runAnalyzerAnalyze(cmd *cobra.Command, args []string) error {
	client := hcl.NewAnalyzerClient(analyzerEndpoint, hclToken)

	metricsData, err := readJSONFile(metricsFile)
	if err != nil {
		return fmt.Errorf("failed to read metrics: %w", err)
	}

	var metrics hcl.SystemMetrics
	jsonBytes, _ := json.Marshal(metricsData)
	json.Unmarshal(jsonBytes, &metrics)

	result, err := client.AnalyzeMetrics(metrics)
	if err != nil {
		return fmt.Errorf("failed to analyze: %w", err)
	}

	printJSON(result)
	return nil
}

func runAnalyzerHistory(cmd *cobra.Command, args []string) error {
	client := hcl.NewAnalyzerClient(analyzerEndpoint, hclToken)

	result, err := client.GetAnalysisHistory(historyLimit)
	if err != nil {
		return fmt.Errorf("failed to get history: %w", err)
	}

	printJSON(result)
	return nil
}

func runAnalyzerHealth(cmd *cobra.Command, args []string) error {
	client := hcl.NewAnalyzerClient(analyzerEndpoint, hclToken)

	result, err := client.Health()
	if err != nil {
		return fmt.Errorf("failed to check health: %w", err)
	}

	printJSON(result)
	return nil
}

func runPlannerGenerate(cmd *cobra.Command, args []string) error {
	client := hcl.NewPlannerClient(plannerEndpoint, hclToken)

	analysisData, err := readJSONFile(analysisFile)
	if err != nil {
		return fmt.Errorf("failed to read analysis: %w", err)
	}

	stateData, err := readJSONFile(stateFile)
	if err != nil {
		return fmt.Errorf("failed to read state: %w", err)
	}

	goalsData, err := readJSONFile(goalsFile)
	if err != nil {
		return fmt.Errorf("failed to read goals: %w", err)
	}

	result, err := client.GeneratePlan(analysisData, stateData, goalsData)
	if err != nil {
		return fmt.Errorf("failed to generate plan: %w", err)
	}

	printJSON(result)
	return nil
}

func runPlannerStatus(cmd *cobra.Command, args []string) error {
	client := hcl.NewPlannerClient(plannerEndpoint, hclToken)

	result, err := client.GetPlannerStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	printJSON(result)
	return nil
}

func runPlannerHealth(cmd *cobra.Command, args []string) error {
	client := hcl.NewPlannerClient(plannerEndpoint, hclToken)

	result, err := client.Health()
	if err != nil {
		return fmt.Errorf("failed to check health: %w", err)
	}

	printJSON(result)
	return nil
}

func runExecutorExecute(cmd *cobra.Command, args []string) error {
	client := hcl.NewExecutorClient(executorEndpoint, hclToken)

	planData, err := readJSONFile(planFile)
	if err != nil {
		return fmt.Errorf("failed to read plan: %w", err)
	}

	planID, _ := planData["plan_id"].(string)
	actions, _ := planData["actions"].([]interface{})

	actionsMap := make([]map[string]interface{}, len(actions))
	for i, a := range actions {
		actionsMap[i], _ = a.(map[string]interface{})
	}

	result, err := client.ExecutePlan(planID, actionsMap, executePriority)
	if err != nil {
		return fmt.Errorf("failed to execute plan: %w", err)
	}

	printJSON(result)
	return nil
}

func runExecutorK8sStatus(cmd *cobra.Command, args []string) error {
	client := hcl.NewExecutorClient(executorEndpoint, hclToken)

	result, err := client.GetK8sStatus()
	if err != nil {
		return fmt.Errorf("failed to get K8s status: %w", err)
	}

	printJSON(result)
	return nil
}

func runExecutorHealth(cmd *cobra.Command, args []string) error {
	client := hcl.NewExecutorClient(executorEndpoint, hclToken)

	result, err := client.Health()
	if err != nil {
		return fmt.Errorf("failed to check health: %w", err)
	}

	printJSON(result)
	return nil
}
