package cmd

import (
	"encoding/json"
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/ethical"
)

var ethicalCmd = &cobra.Command{
	Use:   "ethical",
	Short: "Ethical AI operations",
	Long:  "Ethical services: audit (decision logging), hsas (human-system alignment)",
}

// Audit commands
var auditCmd = &cobra.Command{
	Use:   "audit",
	Short: "Ethical Audit operations",
	Long:  "Log ethical decisions, query history, track metrics",
}

var auditLogCmd = &cobra.Command{
	Use:   "log",
	Short: "Log ethical decision",
	RunE:  runAuditLog,
}

var auditGetCmd = &cobra.Command{
	Use:   "get <decision_id>",
	Short: "Get decision by ID",
	Args:  cobra.ExactArgs(1),
	RunE:  runAuditGet,
}

var auditQueryCmd = &cobra.Command{
	Use:   "query",
	Short: "Query decision history",
	RunE:  runAuditQuery,
}

var auditOverrideCmd = &cobra.Command{
	Use:   "override",
	Short: "Log human override",
	RunE:  runAuditOverride,
}

var auditMetricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Get ethical metrics",
	RunE:  runAuditMetrics,
}

var auditFrameworksCmd = &cobra.Command{
	Use:   "frameworks",
	Short: "Get framework metrics",
	RunE:  runAuditFrameworks,
}

var auditHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check audit health",
	RunE:  runAuditHealth,
}

var auditStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Get audit status",
	RunE:  runAuditStatus,
}

// HSAS commands
var hsasCmd = &cobra.Command{
	Use:   "hsas",
	Short: "Human-System Alignment operations",
	Long:  "Submit feedback, request explanations, check alignment",
}

var hsasFeedbackCmd = &cobra.Command{
	Use:   "feedback",
	Short: "Submit human feedback",
	RunE:  runHSASFeedback,
}

var hsasExplainCmd = &cobra.Command{
	Use:   "explain <decision_id>",
	Short: "Request AI explanation",
	Args:  cobra.ExactArgs(1),
	RunE:  runHSASExplain,
}

var hsasAlignmentCmd = &cobra.Command{
	Use:   "alignment",
	Short: "Get alignment status",
	RunE:  runHSASAlignment,
}

var hsasHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check HSAS health",
	RunE:  runHSASHealth,
}

// Flags
var (
	auditEndpoint string
	hsasEndpoint  string
	ethicalToken  string

	decisionFile string
	queryFile    string
	overrideFile string
	feedbackFile string
	contextFile2 string
)

func init() {
	rootCmd.AddCommand(ethicalCmd)

	ethicalCmd.AddCommand(auditCmd)
	ethicalCmd.AddCommand(hsasCmd)

	auditCmd.AddCommand(auditLogCmd)
	auditCmd.AddCommand(auditGetCmd)
	auditCmd.AddCommand(auditQueryCmd)
	auditCmd.AddCommand(auditOverrideCmd)
	auditCmd.AddCommand(auditMetricsCmd)
	auditCmd.AddCommand(auditFrameworksCmd)
	auditCmd.AddCommand(auditHealthCmd)
	auditCmd.AddCommand(auditStatusCmd)

	hsasCmd.AddCommand(hsasFeedbackCmd)
	hsasCmd.AddCommand(hsasExplainCmd)
	hsasCmd.AddCommand(hsasAlignmentCmd)
	hsasCmd.AddCommand(hsasHealthCmd)

	auditCmd.PersistentFlags().StringVar(&auditEndpoint, "audit-endpoint", "http://localhost:8612", "Audit service endpoint")
	hsasCmd.PersistentFlags().StringVar(&hsasEndpoint, "hsas-endpoint", "http://localhost:8021", "HSAS service endpoint")

	ethicalCmd.PersistentFlags().StringVar(&ethicalToken, "token", "", "Authentication token")

	auditLogCmd.Flags().StringVar(&decisionFile, "decision-file", "", "Decision log file (JSON)")
	auditLogCmd.MarkFlagRequired("decision-file")

	auditQueryCmd.Flags().StringVar(&queryFile, "query-file", "", "Query parameters file (JSON)")

	auditOverrideCmd.Flags().StringVar(&overrideFile, "override-file", "", "Override data file (JSON)")
	auditOverrideCmd.MarkFlagRequired("override-file")

	hsasFeedbackCmd.Flags().StringVar(&feedbackFile, "feedback-file", "", "Feedback data file (JSON)")
	hsasFeedbackCmd.MarkFlagRequired("feedback-file")

	hsasExplainCmd.Flags().StringVar(&contextFile2, "context-file", "", "Context file (JSON, optional)")
}

func runAuditLog(cmd *cobra.Command, args []string) error {
	client := ethical.NewAuditClient(auditEndpoint, ethicalToken)

	decisionData, err := readJSONFile(decisionFile)
	if err != nil {
		return fmt.Errorf("failed to read decision: %w", err)
	}

	var log ethical.EthicalDecisionLog
	jsonBytes, _ := json.Marshal(decisionData)
	json.Unmarshal(jsonBytes, &log)

	result, err := client.LogDecision(log)
	if err != nil {
		return fmt.Errorf("failed to log decision: %w", err)
	}

	printJSON(result)
	return nil
}

func runAuditGet(cmd *cobra.Command, args []string) error {
	client := ethical.NewAuditClient(auditEndpoint, ethicalToken)

	result, err := client.GetDecision(args[0])
	if err != nil {
		return fmt.Errorf("failed to get decision: %w", err)
	}

	printJSON(result)
	return nil
}

func runAuditQuery(cmd *cobra.Command, args []string) error {
	client := ethical.NewAuditClient(auditEndpoint, ethicalToken)

	var query ethical.DecisionHistoryQuery
	if queryFile != "" {
		queryData, err := readJSONFile(queryFile)
		if err != nil {
			return fmt.Errorf("failed to read query: %w", err)
		}
		jsonBytes, _ := json.Marshal(queryData)
		json.Unmarshal(jsonBytes, &query)
	}

	result, err := client.QueryDecisions(query)
	if err != nil {
		return fmt.Errorf("failed to query decisions: %w", err)
	}

	printJSON(result)
	return nil
}

func runAuditOverride(cmd *cobra.Command, args []string) error {
	client := ethical.NewAuditClient(auditEndpoint, ethicalToken)

	overrideData, err := readJSONFile(overrideFile)
	if err != nil {
		return fmt.Errorf("failed to read override: %w", err)
	}

	var override ethical.HumanOverrideRequest
	jsonBytes, _ := json.Marshal(overrideData)
	json.Unmarshal(jsonBytes, &override)

	result, err := client.LogOverride(override)
	if err != nil {
		return fmt.Errorf("failed to log override: %w", err)
	}

	printJSON(result)
	return nil
}

func runAuditMetrics(cmd *cobra.Command, args []string) error {
	client := ethical.NewAuditClient(auditEndpoint, ethicalToken)

	result, err := client.GetMetrics()
	if err != nil {
		return fmt.Errorf("failed to get metrics: %w", err)
	}

	printJSON(result)
	return nil
}

func runAuditFrameworks(cmd *cobra.Command, args []string) error {
	client := ethical.NewAuditClient(auditEndpoint, ethicalToken)

	result, err := client.GetFrameworkMetrics()
	if err != nil {
		return fmt.Errorf("failed to get frameworks: %w", err)
	}

	printJSON(result)
	return nil
}

func runAuditHealth(cmd *cobra.Command, args []string) error {
	client := ethical.NewAuditClient(auditEndpoint, ethicalToken)

	result, err := client.Health()
	if err != nil {
		return fmt.Errorf("failed to check health: %w", err)
	}

	printJSON(result)
	return nil
}

func runAuditStatus(cmd *cobra.Command, args []string) error {
	client := ethical.NewAuditClient(auditEndpoint, ethicalToken)

	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	printJSON(result)
	return nil
}

func runHSASFeedback(cmd *cobra.Command, args []string) error {
	client := ethical.NewHSASClient(hsasEndpoint, ethicalToken)

	feedbackData, err := readJSONFile(feedbackFile)
	if err != nil {
		return fmt.Errorf("failed to read feedback: %w", err)
	}

	var feedback ethical.HumanFeedback
	jsonBytes, _ := json.Marshal(feedbackData)
	json.Unmarshal(jsonBytes, &feedback)

	result, err := client.SubmitFeedback(feedback)
	if err != nil {
		return fmt.Errorf("failed to submit feedback: %w", err)
	}

	printJSON(result)
	return nil
}

func runHSASExplain(cmd *cobra.Command, args []string) error {
	client := ethical.NewHSASClient(hsasEndpoint, ethicalToken)

	var context map[string]interface{}
	if contextFile2 != "" {
		data, err := readJSONFile(contextFile2)
		if err != nil {
			return fmt.Errorf("failed to read context: %w", err)
		}
		if data != nil {
			context = data.(map[string]interface{})
		}
	}

	result, err := client.RequestExplanation(args[0], context)
	if err != nil {
		return fmt.Errorf("failed to request explanation: %w", err)
	}

	printJSON(result)
	return nil
}

func runHSASAlignment(cmd *cobra.Command, args []string) error {
	client := ethical.NewHSASClient(hsasEndpoint, ethicalToken)

	result, err := client.GetAlignmentStatus()
	if err != nil {
		return fmt.Errorf("failed to get alignment: %w", err)
	}

	printJSON(result)
	return nil
}

func runHSASHealth(cmd *cobra.Command, args []string) error {
	client := ethical.NewHSASClient(hsasEndpoint, ethicalToken)

	result, err := client.Health()
	if err != nil {
		return fmt.Errorf("failed to check health: %w", err)
	}

	printJSON(result)
	return nil
}
