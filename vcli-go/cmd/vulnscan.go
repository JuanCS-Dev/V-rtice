package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/vulnscan"
	"github.com/verticedev/vcli-go/internal/visual"
)

var (
	vulnscanServer string
	vulnscanTarget string
	vulnscanFull   bool
)

var vulnscanCmd = &cobra.Command{
	Use:   "vulnscan",
	Short: "Vulnerability Scanner - Security scanning",
	Long:  `Comprehensive vulnerability scanning for infrastructure and applications`,
}

var vulnscanScanCmd = &cobra.Command{
	Use:   "scan [target]",
	Short: "Scan target for vulnerabilities",
	Args:  cobra.MinimumNArgs(1),
	RunE:  runVulnscanScan,
}

func runVulnscanScan(cmd *cobra.Command, args []string) error {
	client := vulnscan.NewVulnScanClient(getVulnscanServer())
	req := &vulnscan.ScanRequest{
		Target: args[0],
		Full:   vulnscanFull,
	}

	result, err := client.Scan(req)
	if err != nil {
		return fmt.Errorf("scan failed: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Vulnerability Scan - %s\n\n", styles.Accent.Render("🔍"), result.Target)
	fmt.Printf("%s %s\n", styles.Muted.Render("Scan ID:"), result.ScanID)
	fmt.Printf("%s %d vulnerabilities\n\n", styles.Muted.Render("Found:"), len(result.Vulnerabilities))

	if len(result.Vulnerabilities) > 0 {
		for _, vuln := range result.Vulnerabilities {
			var severity string
			if vuln.Severity == "critical" {
				severity = "🔴"
			} else if vuln.Severity == "high" {
				severity = "🟠"
			} else if vuln.Severity == "medium" {
				severity = "🟡"
			} else {
				severity = "🟢"
			}
			fmt.Printf("%s %s - %s\n", severity, vuln.CVE, vuln.Title)
			fmt.Printf("  %s %s\n", styles.Muted.Render("Severity:"), vuln.Severity)
			fmt.Printf("  %s %.1f\n\n", styles.Muted.Render("CVSS:"), vuln.CVSS)
		}
	}

	return nil
}

var vulnscanReportCmd = &cobra.Command{
	Use:   "report [scan-id]",
	Short: "Get scan report",
	Args:  cobra.MinimumNArgs(1),
	RunE:  runVulnscanReport,
}

func runVulnscanReport(cmd *cobra.Command, args []string) error {
	client := vulnscan.NewVulnScanClient(getVulnscanServer())
	req := &vulnscan.ReportRequest{ScanID: args[0]}

	result, err := client.GetReport(req)
	if err != nil {
		return fmt.Errorf("failed to get report: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Scan Report - %s\n\n", styles.Accent.Render("📄"), result.ScanID)
	fmt.Printf("%s %d critical\n", styles.Muted.Render("Critical:"), result.Critical)
	fmt.Printf("%s %d high\n", styles.Muted.Render("High:"), result.High)
	fmt.Printf("%s %d medium\n", styles.Muted.Render("Medium:"), result.Medium)
	fmt.Printf("%s %d low\n\n", styles.Muted.Render("Low:"), result.Low)

	fmt.Printf("%s %.1f\n", styles.Muted.Render("Risk Score:"), result.RiskScore)

	return nil
}

var vulnscanStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Vulnerability scanner status",
	RunE:  runVulnscanStatus,
}

func runVulnscanStatus(cmd *cobra.Command, args []string) error {
	client := vulnscan.NewVulnScanClient(getVulnscanServer())
	result, err := client.GetStatus()
	if err != nil {
		return fmt.Errorf("failed to get status: %w", err)
	}

	styles := visual.DefaultStyles()
	fmt.Printf("%s Vulnerability Scanner Status\n\n", styles.Accent.Render("🔍"))
	fmt.Printf("%s %s\n", styles.Muted.Render("Status:"), getStatusIcon(result.Status))
	fmt.Printf("%s %d scans\n", styles.Muted.Render("Completed:"), result.ScansCompleted)
	fmt.Printf("%s %d vulnerabilities\n", styles.Muted.Render("Total Found:"), result.TotalVulnerabilities)

	return nil
}

func getVulnscanServer() string {
	if vulnscanServer != "" {
		return vulnscanServer
	}
	return ""
}

func init() {
	rootCmd.AddCommand(vulnscanCmd)
	vulnscanCmd.AddCommand(vulnscanScanCmd)
	vulnscanCmd.AddCommand(vulnscanReportCmd)
	vulnscanCmd.AddCommand(vulnscanStatusCmd)

	vulnscanCmd.PersistentFlags().StringVarP(&vulnscanServer, "server", "s", "", "VulnScan server endpoint")
	vulnscanScanCmd.Flags().BoolVar(&vulnscanFull, "full", false, "Full vulnerability scan")
}
