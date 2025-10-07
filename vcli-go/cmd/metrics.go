package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/observability"
)

// Metrics command flags
var (
	metricsPrometheusURL string
	metricsQuery         string
	metricsRange         string
	metricsStep          string
	metricsStart         string
	metricsEnd           string
	metricsTime          string
	metricsLabelName     string
	metricsMatches       []string
	metricsOutputFormat  string
)

// metricsCmd represents the metrics command
var metricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Query observability metrics",
	Long: `Query Prometheus metrics for system observability.

Prometheus provides time-series data for all Vértice platform services,
including:
  - Immune system metrics (agent counts, cytokine rates, threat detection)
  - MAXIMUS orchestrator metrics (decision latency, approval rates)
  - Infrastructure metrics (CPU, memory, disk, network)
  - Application metrics (request rates, error rates, latencies)

Examples:
  # Query current agent count
  vcli metrics instant 'immune_agent_count{type="neutrophil"}'

  # Query cytokine rate over last hour
  vcli metrics range 'rate(cytokine_count[5m])' --range 1h

  # Query decision latency percentiles
  vcli metrics instant 'histogram_quantile(0.95, maximus_decision_duration_seconds)'

  # List all services currently up
  vcli metrics instant 'up' --output table`,
}

// ============================================================
// Instant Query
// ============================================================

var metricsInstantCmd = &cobra.Command{
	Use:   "instant <query>",
	Short: "Execute an instant query",
	Long: `Execute a Prometheus instant query at a single point in time.

An instant query evaluates a PromQL expression at a specific timestamp
(default: current time).

Examples:
  # Current agent count
  vcli metrics instant 'immune_agent_count'

  # Current agent count by type
  vcli metrics instant 'immune_agent_count{type="neutrophil"}'

  # Service uptime
  vcli metrics instant 'up{job="maximus"}'

  # Query at specific time
  vcli metrics instant 'cpu_usage' --time 2025-10-07T14:00:00Z`,
	Args: cobra.ExactArgs(1),
	RunE: runMetricsInstant,
}

func runMetricsInstant(cmd *cobra.Command, args []string) error {
	query := args[0]

	// Parse timestamp if provided
	var timestamp *time.Time
	if metricsTime != "" {
		t, err := time.Parse(time.RFC3339, metricsTime)
		if err != nil {
			return fmt.Errorf("invalid timestamp format (expected RFC3339): %w", err)
		}
		timestamp = &t
	}

	// Create client
	client := observability.NewPrometheusClient(metricsPrometheusURL)
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Execute query
	result, err := client.QueryInstant(ctx, query, timestamp)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}

	// Output based on format
	if metricsOutputFormat == "json" {
		data, _ := json.MarshalIndent(result, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Table output
	if len(result.Data.Result) == 0 {
		fmt.Println("No results")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
	fmt.Fprintln(w, "METRIC\tVALUE\tTIMESTAMP")

	for _, metric := range result.Data.Result {
		// Get metric name and labels
		metricName := formatMetricLabels(metric.Metric)

		// Get value and timestamp
		if len(metric.Value) >= 2 {
			timestamp := metric.Value[0]
			value := metric.Value[1]

			// Format timestamp
			var ts string
			if f, ok := timestamp.(float64); ok {
				t := time.Unix(int64(f), 0)
				ts = t.Format("15:04:05")
			}

			fmt.Fprintf(w, "%s\t%v\t%s\n", metricName, value, ts)
		}
	}
	w.Flush()

	return nil
}

// ============================================================
// Range Query
// ============================================================

var metricsRangeCmd = &cobra.Command{
	Use:   "range <query>",
	Short: "Execute a range query",
	Long: `Execute a Prometheus range query over a time period.

A range query evaluates a PromQL expression at multiple points over
a specified time range.

Time Range Shortcuts:
  --range 1h    Last 1 hour
  --range 6h    Last 6 hours
  --range 24h   Last 24 hours
  --range 7d    Last 7 days

Examples:
  # Cytokine rate over last hour
  vcli metrics range 'rate(cytokine_count[5m])' --range 1h --step 1m

  # Agent count over last 24 hours
  vcli metrics range 'immune_agent_count' --range 24h --step 5m

  # CPU usage over specific time range
  vcli metrics range 'cpu_usage_percent' \
    --start 2025-10-07T10:00:00Z \
    --end 2025-10-07T14:00:00Z \
    --step 1m`,
	Args: cobra.ExactArgs(1),
	RunE: runMetricsRange,
}

func runMetricsRange(cmd *cobra.Command, args []string) error {
	query := args[0]

	// Parse time range
	var start, end time.Time
	var err error

	if metricsRange != "" {
		// Use shortcut range (e.g., "1h", "24h")
		duration, err := parseDuration(metricsRange)
		if err != nil {
			return fmt.Errorf("invalid range format: %w", err)
		}
		end = time.Now()
		start = end.Add(-duration)
	} else if metricsStart != "" && metricsEnd != "" {
		// Use explicit start/end
		start, err = time.Parse(time.RFC3339, metricsStart)
		if err != nil {
			return fmt.Errorf("invalid start time format: %w", err)
		}
		end, err = time.Parse(time.RFC3339, metricsEnd)
		if err != nil {
			return fmt.Errorf("invalid end time format: %w", err)
		}
	} else {
		return fmt.Errorf("either --range or --start/--end must be provided")
	}

	// Default step
	if metricsStep == "" {
		metricsStep = "1m"
	}

	// Create client
	client := observability.NewPrometheusClient(metricsPrometheusURL)
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// Execute query
	result, err := client.QueryRange(ctx, query, start, end, metricsStep)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}

	// Output based on format
	if metricsOutputFormat == "json" {
		data, _ := json.MarshalIndent(result, "", "  ")
		fmt.Println(string(data))
		return nil
	}

	// Table output (show summary statistics)
	if len(result.Data.Result) == 0 {
		fmt.Println("No results")
		return nil
	}

	for _, metric := range result.Data.Result {
		metricName := formatMetricLabels(metric.Metric)
		fmt.Printf("\n=== %s ===\n", metricName)

		if len(metric.Values) == 0 {
			fmt.Println("No data points")
			continue
		}

		// Show first 10 and last 10 data points
		displayLimit := 10
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
		fmt.Fprintln(w, "TIMESTAMP\tVALUE")

		for i, point := range metric.Values {
			if i < displayLimit || i >= len(metric.Values)-displayLimit {
				if len(point) >= 2 {
					ts := point[0]
					value := point[1]

					var timestamp string
					if f, ok := ts.(float64); ok {
						t := time.Unix(int64(f), 0)
						timestamp = t.Format("15:04:05")
					}

					fmt.Fprintf(w, "%s\t%v\n", timestamp, value)
				}
			} else if i == displayLimit {
				fmt.Fprintln(w, "...\t...")
			}
		}
		w.Flush()

		// Summary statistics
		values := extractValues(metric.Values)
		if len(values) > 0 {
			min, max, avg := calculateStats(values)
			fmt.Printf("\nTotal points: %d, Min: %.2f, Max: %.2f, Avg: %.2f\n",
				len(values), min, max, avg)
		}
	}

	return nil
}

// ============================================================
// Label Values
// ============================================================

var metricsLabelsCmd = &cobra.Command{
	Use:   "labels <label_name>",
	Short: "Get all values for a label",
	Long: `Retrieve all values for a specific Prometheus label.

Examples:
  # List all job names
  vcli metrics labels job

  # List all service instances
  vcli metrics labels instance

  # List all agent types
  vcli metrics labels type`,
	Args: cobra.ExactArgs(1),
	RunE: runMetricsLabels,
}

func runMetricsLabels(cmd *cobra.Command, args []string) error {
	labelName := args[0]

	client := observability.NewPrometheusClient(metricsPrometheusURL)
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	values, err := client.GetLabelValues(ctx, labelName)
	if err != nil {
		return fmt.Errorf("failed to get label values: %w", err)
	}

	if len(values) == 0 {
		fmt.Printf("No values found for label: %s\n", labelName)
		return nil
	}

	fmt.Printf("Values for label '%s':\n", labelName)
	for _, v := range values {
		fmt.Printf("  - %s\n", v)
	}
	fmt.Printf("\nTotal: %d values\n", len(values))

	return nil
}

// ============================================================
// Targets
// ============================================================

var metricsTargetsCmd = &cobra.Command{
	Use:   "targets",
	Short: "List Prometheus scrape targets",
	Long: `List all Prometheus scrape targets and their health status.

Examples:
  # List all targets
  vcli metrics targets

  # List only active targets
  vcli metrics targets --state active

  # List only unhealthy targets
  vcli metrics targets --state down`,
	RunE: runMetricsTargets,
}

func runMetricsTargets(cmd *cobra.Command, args []string) error {
	client := observability.NewPrometheusClient(metricsPrometheusURL)
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Get targets (state filter is handled by API)
	targets, err := client.GetTargets(ctx, "")
	if err != nil {
		return fmt.Errorf("failed to get targets: %w", err)
	}

	// Display active targets
	if len(targets.ActiveTargets) > 0 {
		fmt.Println("=== Active Targets ===")
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
		fmt.Fprintln(w, "POOL\tENDPOINT\tHEALTH\tLAST SCRAPE\tDURATION")

		for _, t := range targets.ActiveTargets {
			healthIcon := "✅"
			if t.Health != "up" {
				healthIcon = "❌"
			}

			lastScrape := t.LastScrape.Format("15:04:05")
			duration := fmt.Sprintf("%.2fms", t.LastScrapeDuration*1000)

			fmt.Fprintf(w, "%s\t%s\t%s %s\t%s\t%s\n",
				t.ScrapePool,
				truncate(t.ScrapeURL, 50),
				healthIcon,
				t.Health,
				lastScrape,
				duration,
			)

			if t.LastError != "" {
				fmt.Fprintf(w, "\t\t  Error: %s\t\t\n", truncate(t.LastError, 60))
			}
		}
		w.Flush()
		fmt.Printf("\nTotal active: %d\n", len(targets.ActiveTargets))
	}

	// Display dropped targets
	if len(targets.DroppedTargets) > 0 {
		fmt.Println("\n=== Dropped Targets ===")
		for _, t := range targets.DroppedTargets {
			fmt.Printf("  - %s (pool: %s)\n", t.ScrapeURL, t.ScrapePool)
		}
		fmt.Printf("\nTotal dropped: %d\n", len(targets.DroppedTargets))
	}

	if len(targets.ActiveTargets) == 0 && len(targets.DroppedTargets) == 0 {
		fmt.Println("No targets found")
	}

	return nil
}

// ============================================================
// Helper Functions
// ============================================================

func formatMetricLabels(labels map[string]string) string {
	if len(labels) == 0 {
		return ""
	}

	// Extract __name__ first
	name := labels["__name__"]
	if name == "" {
		return ""
	}

	// Build label string
	var labelPairs []string
	for k, v := range labels {
		if k != "__name__" {
			labelPairs = append(labelPairs, fmt.Sprintf("%s=%q", k, v))
		}
	}

	if len(labelPairs) > 0 {
		return fmt.Sprintf("%s{%s}", name, strings.Join(labelPairs, ","))
	}
	return name
}

func parseDuration(s string) (time.Duration, error) {
	// Support shortcuts like "1h", "24h", "7d"
	if strings.HasSuffix(s, "d") {
		days, err := strconv.Atoi(strings.TrimSuffix(s, "d"))
		if err != nil {
			return 0, err
		}
		return time.Duration(days) * 24 * time.Hour, nil
	}
	return time.ParseDuration(s)
}

func extractValues(points [][]interface{}) []float64 {
	var values []float64
	for _, point := range points {
		if len(point) >= 2 {
			if strVal, ok := point[1].(string); ok {
				if f, err := strconv.ParseFloat(strVal, 64); err == nil {
					values = append(values, f)
				}
			} else if f, ok := point[1].(float64); ok {
				values = append(values, f)
			}
		}
	}
	return values
}

func calculateStats(values []float64) (min, max, avg float64) {
	if len(values) == 0 {
		return 0, 0, 0
	}

	min = values[0]
	max = values[0]
	sum := 0.0

	for _, v := range values {
		if v < min {
			min = v
		}
		if v > max {
			max = v
		}
		sum += v
	}

	avg = sum / float64(len(values))
	return min, max, avg
}

func init() {
	rootCmd.AddCommand(metricsCmd)

	// Instant query
	metricsCmd.AddCommand(metricsInstantCmd)
	metricsInstantCmd.Flags().StringVar(&metricsPrometheusURL, "server", "http://localhost:9090", "Prometheus server URL")
	metricsInstantCmd.Flags().StringVar(&metricsTime, "time", "", "Query timestamp (RFC3339 format)")
	metricsInstantCmd.Flags().StringVarP(&metricsOutputFormat, "output", "o", "table", "Output format (json, table)")

	// Range query
	metricsCmd.AddCommand(metricsRangeCmd)
	metricsRangeCmd.Flags().StringVar(&metricsPrometheusURL, "server", "http://localhost:9090", "Prometheus server URL")
	metricsRangeCmd.Flags().StringVar(&metricsRange, "range", "", "Time range (e.g., 1h, 24h, 7d)")
	metricsRangeCmd.Flags().StringVar(&metricsStart, "start", "", "Start time (RFC3339 format)")
	metricsRangeCmd.Flags().StringVar(&metricsEnd, "end", "", "End time (RFC3339 format)")
	metricsRangeCmd.Flags().StringVar(&metricsStep, "step", "1m", "Query step (e.g., 1m, 5m, 1h)")
	metricsRangeCmd.Flags().StringVarP(&metricsOutputFormat, "output", "o", "table", "Output format (json, table)")

	// Label values
	metricsCmd.AddCommand(metricsLabelsCmd)
	metricsLabelsCmd.Flags().StringVar(&metricsPrometheusURL, "server", "http://localhost:9090", "Prometheus server URL")

	// Targets
	metricsCmd.AddCommand(metricsTargetsCmd)
	metricsTargetsCmd.Flags().StringVar(&metricsPrometheusURL, "server", "http://localhost:9090", "Prometheus server URL")
}
