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
	"github.com/verticedev/vcli-go/internal/gateway"
)

// Gateway command flags
var (
	gatewayServer      string
	gatewayToken       string
	gatewayService     string
	gatewayEndpoint    string
	gatewayMethod      string
	gatewayData        string
	gatewayParams      []string
	gatewayOutputFormat string
)

// gatewayCmd represents the gateway command
var gatewayCmd = &cobra.Command{
	Use:   "gateway",
	Short: "Interact with API Gateway",
	Long: `Query backend services via the unified API Gateway.

The API Gateway provides a unified REST interface to backend services
that don't expose gRPC endpoints directly.

Supported Services:
  ethical-audit         - Ethical decision auditing
  narrative-filter      - Narrative manipulation detection
  osint                 - Open-source intelligence gathering
  vuln-intel            - Vulnerability intelligence
  network-recon         - Network reconnaissance
  web-attack            - Web application attack simulation

Examples:
  # Query ethical audit decisions
  vcli gateway query --service ethical-audit --endpoint /decisions

  # Analyze content for narrative manipulation
  vcli gateway post --service narrative-filter --endpoint /analyze \
    --data '{"content":"Article text here"}'

  # Get vulnerability intelligence
  vcli gateway query --service vuln-intel --endpoint /cves \
    --param severity=critical --param year=2025`,
}

// ============================================================
// Query Command
// ============================================================

var gatewayQueryCmd = &cobra.Command{
	Use:   "query",
	Short: "Execute a GET request to a service",
	Long: `Execute a GET request to a backend service via API Gateway.

Examples:
  # List ethical audit decisions
  vcli gateway query --service ethical-audit --endpoint /decisions

  # Get specific decision
  vcli gateway query --service ethical-audit --endpoint /decisions/abc123

  # Filter with parameters
  vcli gateway query --service vuln-intel --endpoint /cves \
    --param severity=critical --param year=2025 --param product=nginx`,
	RunE: runGatewayQuery,
}

func runGatewayQuery(cmd *cobra.Command, args []string) error {
	// Validate inputs
	if gatewayService == "" {
		return fmt.Errorf("--service is required")
	}
	if gatewayEndpoint == "" {
		return fmt.Errorf("--endpoint is required")
	}

	// Parse parameters
	params := make(map[string]string)
	for _, p := range gatewayParams {
		parts := strings.SplitN(p, "=", 2)
		if len(parts) != 2 {
			return fmt.Errorf("invalid parameter format: %s (expected key=value)", p)
		}
		params[parts[0]] = parts[1]
	}

	// Create client
	client := gateway.NewGatewayClient(gatewayServer, gatewayToken)
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Execute query
	result, err := client.Query(ctx, gatewayService, gatewayEndpoint, params)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}

	// Output result
	if gatewayOutputFormat == "json" {
		var prettyJSON interface{}
		if err := json.Unmarshal(result, &prettyJSON); err == nil {
			data, _ := json.MarshalIndent(prettyJSON, "", "  ")
			fmt.Println(string(data))
		} else {
			fmt.Println(string(result))
		}
	} else {
		// Pretty print for table format
		var prettyJSON interface{}
		if err := json.Unmarshal(result, &prettyJSON); err == nil {
			data, _ := json.MarshalIndent(prettyJSON, "", "  ")
			fmt.Println(string(data))
		} else {
			fmt.Println(string(result))
		}
	}

	return nil
}

// ============================================================
// Post Command
// ============================================================

var gatewayPostCmd = &cobra.Command{
	Use:   "post",
	Short: "Execute a POST request to a service",
	Long: `Execute a POST request to a backend service via API Gateway.

Examples:
  # Analyze content for narrative manipulation
  vcli gateway post --service narrative-filter --endpoint /analyze \
    --data '{"content":"Article text"}'

  # Audit an ethical decision
  vcli gateway post --service ethical-audit --endpoint /decisions/abc123/audit \
    --data '{"auditor":"user123","outcome":"approved"}'

  # Submit OSINT query
  vcli gateway post --service osint --endpoint /query \
    --data '{"target":"example.com","scope":"dns,whois"}'`,
	RunE: runGatewayPost,
}

func runGatewayPost(cmd *cobra.Command, args []string) error {
	// Validate inputs
	if gatewayService == "" {
		return fmt.Errorf("--service is required")
	}
	if gatewayEndpoint == "" {
		return fmt.Errorf("--endpoint is required")
	}

	// Parse data
	var data interface{}
	if gatewayData != "" {
		if err := json.Unmarshal([]byte(gatewayData), &data); err != nil {
			return fmt.Errorf("invalid JSON data: %w", err)
		}
	}

	// Create client
	client := gateway.NewGatewayClient(gatewayServer, gatewayToken)
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Execute POST
	result, err := client.Post(ctx, gatewayService, gatewayEndpoint, data)
	if err != nil {
		return fmt.Errorf("post failed: %w", err)
	}

	// Output result
	var prettyJSON interface{}
	if err := json.Unmarshal(result, &prettyJSON); err == nil {
		output, _ := json.MarshalIndent(prettyJSON, "", "  ")
		fmt.Println(string(output))
	} else {
		fmt.Println(string(result))
	}

	return nil
}

// ============================================================
// Service-Specific Commands
// ============================================================

var ethicalAuditCmd = &cobra.Command{
	Use:   "ethical-audit",
	Short: "Query ethical audit service",
	Long: `Interact with the Ethical Audit Service.

The Ethical Audit Service tracks and audits ethical decisions made
by MAXIMUS orchestrator and other autonomous systems.

Examples:
  # List recent decisions
  vcli gateway ethical-audit decisions --status pending

  # Get specific decision
  vcli gateway ethical-audit decision abc123

  # Audit a decision
  vcli gateway ethical-audit audit abc123 \
    --outcome approved --reason "Meets ethical guidelines"`,
}

var ethicalAuditDecisionsCmd = &cobra.Command{
	Use:   "decisions",
	Short: "List ethical decisions",
	RunE:  runEthicalAuditDecisions,
}

func runEthicalAuditDecisions(cmd *cobra.Command, args []string) error {
	// Parse filters from params
	params := make(map[string]string)
	for _, p := range gatewayParams {
		parts := strings.SplitN(p, "=", 2)
		if len(parts) == 2 {
			params[parts[0]] = parts[1]
		}
	}

	client := gateway.NewEthicalAuditClient(gatewayServer, gatewayToken)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	result, err := client.GetDecisions(ctx, params)
	if err != nil {
		return fmt.Errorf("failed to get decisions: %w", err)
	}

	// Parse and display
	var decisions []map[string]interface{}
	if err := json.Unmarshal(result, &decisions); err != nil {
		// If not array, just print raw
		var prettyJSON interface{}
		json.Unmarshal(result, &prettyJSON)
		data, _ := json.MarshalIndent(prettyJSON, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	if len(decisions) == 0 {
		fmt.Println("No decisions found")
		return nil
	}

	// Table output
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintln(w, "ID\tSTATUS\tTYPE\tTIMESTAMP")
	for _, d := range decisions {
		id := getString(d, "id")
		status := getString(d, "status")
		dtype := getString(d, "type")
		timestamp := getString(d, "timestamp")

		fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
			truncate(id, 16),
			status,
			dtype,
			timestamp,
		)
	}
	w.Flush()

	fmt.Printf("\nTotal: %d decisions\n", len(decisions))
	return nil
}

var narrativeFilterCmd = &cobra.Command{
	Use:   "narrative-filter",
	Short: "Analyze content for narrative manipulation",
	Long: `Interact with the Narrative Manipulation Filter service.

This service analyzes content for cognitive manipulation patterns,
propaganda techniques, and narrative framing.

Examples:
  # Analyze article
  vcli gateway narrative-filter analyze --data '{"content":"Article text"}'

  # Get analysis history
  vcli gateway narrative-filter history --param days=7`,
}

var narrativeFilterAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze content for manipulation",
	RunE:  runNarrativeFilterAnalyze,
}

func runNarrativeFilterAnalyze(cmd *cobra.Command, args []string) error {
	if gatewayData == "" {
		return fmt.Errorf("--data is required with content to analyze")
	}

	var data interface{}
	if err := json.Unmarshal([]byte(gatewayData), &data); err != nil {
		return fmt.Errorf("invalid JSON data: %w", err)
	}

	client := gateway.NewNarrativeFilterClient(gatewayServer, gatewayToken)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	result, err := client.AnalyzeContent(ctx, data)
	if err != nil {
		return fmt.Errorf("analysis failed: %w", err)
	}

	var prettyJSON interface{}
	json.Unmarshal(result, &prettyJSON)
	output, _ := json.MarshalIndent(prettyJSON, "", "  ")
	fmt.Println(string(output))

	return nil
}

// ============================================================
// Helper Functions
// ============================================================

func getString(m map[string]interface{}, key string) string {
	if v, ok := m[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
		return fmt.Sprintf("%v", v)
	}
	return ""
}

func init() {
	rootCmd.AddCommand(gatewayCmd)

	// Query command
	gatewayCmd.AddCommand(gatewayQueryCmd)
	gatewayQueryCmd.Flags().StringVar(&gatewayServer, "server", "http://localhost:8080", "API Gateway server URL")
	gatewayQueryCmd.Flags().StringVar(&gatewayToken, "token", "", "JWT authentication token")
	gatewayQueryCmd.Flags().StringVar(&gatewayService, "service", "", "Service name (required)")
	gatewayQueryCmd.Flags().StringVar(&gatewayEndpoint, "endpoint", "", "Endpoint path (required)")
	gatewayQueryCmd.Flags().StringArrayVar(&gatewayParams, "param", []string{}, "Query parameters (key=value)")
	gatewayQueryCmd.Flags().StringVarP(&gatewayOutputFormat, "output", "o", "pretty", "Output format (json, pretty)")
	gatewayQueryCmd.MarkFlagRequired("service")
	gatewayQueryCmd.MarkFlagRequired("endpoint")

	// Post command
	gatewayCmd.AddCommand(gatewayPostCmd)
	gatewayPostCmd.Flags().StringVar(&gatewayServer, "server", "http://localhost:8080", "API Gateway server URL")
	gatewayPostCmd.Flags().StringVar(&gatewayToken, "token", "", "JWT authentication token")
	gatewayPostCmd.Flags().StringVar(&gatewayService, "service", "", "Service name (required)")
	gatewayPostCmd.Flags().StringVar(&gatewayEndpoint, "endpoint", "", "Endpoint path (required)")
	gatewayPostCmd.Flags().StringVar(&gatewayData, "data", "", "JSON data for POST body (required)")
	gatewayPostCmd.MarkFlagRequired("service")
	gatewayPostCmd.MarkFlagRequired("endpoint")

	// Service-specific commands
	gatewayCmd.AddCommand(ethicalAuditCmd)
	ethicalAuditCmd.AddCommand(ethicalAuditDecisionsCmd)
	ethicalAuditDecisionsCmd.Flags().StringVar(&gatewayServer, "server", "http://localhost:8080", "API Gateway server URL")
	ethicalAuditDecisionsCmd.Flags().StringVar(&gatewayToken, "token", "", "JWT authentication token")
	ethicalAuditDecisionsCmd.Flags().StringArrayVar(&gatewayParams, "param", []string{}, "Filter parameters (key=value)")

	gatewayCmd.AddCommand(narrativeFilterCmd)
	narrativeFilterCmd.AddCommand(narrativeFilterAnalyzeCmd)
	narrativeFilterAnalyzeCmd.Flags().StringVar(&gatewayServer, "server", "http://localhost:8080", "API Gateway server URL")
	narrativeFilterAnalyzeCmd.Flags().StringVar(&gatewayToken, "token", "", "JWT authentication token")
	narrativeFilterAnalyzeCmd.Flags().StringVar(&gatewayData, "data", "", "JSON data with content to analyze")
	narrativeFilterAnalyzeCmd.MarkFlagRequired("data")
}
