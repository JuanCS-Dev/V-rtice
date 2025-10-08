package osint

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// FormatInvestigationResponse formats investigation start response
func FormatInvestigationResponse(resp *InvestigationResponse) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Header
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("OSINT INVESTIGATION STARTED", gradient)
	output.WriteString(title + "\n")
	output.WriteString(strings.Repeat("━", 70) + "\n\n")

	// Investigation details
	output.WriteString(fmt.Sprintf("  Investigation ID:    %s\n",
		styles.Info.Render(resp.InvestigationID)))
	output.WriteString(fmt.Sprintf("  Status:              %s\n",
		formatStatus(resp.Status, styles)))

	if resp.Message != "" {
		output.WriteString(fmt.Sprintf("  Message:             %s\n",
			styles.Muted.Render(resp.Message)))
	}

	output.WriteString("\n")
	output.WriteString(styles.Accent.Render("Use 'vcli investigate osint status " + resp.InvestigationID + "' to check progress\n"))

	return output.String()
}

// FormatStatusResponse formats investigation status
func FormatStatusResponse(status *StatusResponse) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Header
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("OSINT INVESTIGATION STATUS", gradient)
	output.WriteString(title + "\n")
	output.WriteString(strings.Repeat("━", 70) + "\n\n")

	// Status details
	output.WriteString(fmt.Sprintf("  Investigation ID:    %s\n",
		styles.Info.Render(status.InvestigationID)))
	output.WriteString(fmt.Sprintf("  Status:              %s\n",
		formatStatus(status.Status, styles)))

	if status.Progress > 0 {
		output.WriteString(fmt.Sprintf("  Progress:            %s\n",
			formatProgress(status.Progress, styles)))
	}

	if status.CurrentPhase != "" {
		output.WriteString(fmt.Sprintf("  Current Phase:       %s\n",
			styles.Accent.Render(status.CurrentPhase)))
	}

	if status.Message != "" {
		output.WriteString(fmt.Sprintf("  Message:             %s\n",
			styles.Muted.Render(status.Message)))
	}

	output.WriteString("\n")

	return output.String()
}

// FormatReportResponse formats full OSINT report
func FormatReportResponse(report *ReportResponse) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Header
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("OSINT INVESTIGATION REPORT", gradient)
	output.WriteString(title + "\n")
	output.WriteString(strings.Repeat("━", 70) + "\n\n")

	// Investigation Overview
	output.WriteString(styles.Bold.Render("Investigation Overview") + "\n\n")
	output.WriteString(fmt.Sprintf("  Investigation ID:    %s\n",
		styles.Info.Render(report.InvestigationID)))
	output.WriteString(fmt.Sprintf("  Query:               %s\n",
		styles.Bold.Render(report.Query)))
	output.WriteString(fmt.Sprintf("  Type:                %s\n",
		styles.Accent.Render(report.InvestigationType)))
	output.WriteString(fmt.Sprintf("  Status:              %s\n",
		formatStatus(report.Status, styles)))
	output.WriteString(fmt.Sprintf("  Started:             %s\n",
		styles.Muted.Render(report.StartedAt)))

	if report.CompletedAt != "" {
		output.WriteString(fmt.Sprintf("  Completed:           %s\n",
			styles.Muted.Render(report.CompletedAt)))
	}

	if report.RiskScore > 0 {
		output.WriteString(fmt.Sprintf("  Risk Score:          %s\n",
			formatRiskScore(report.RiskScore, styles)))
	}

	output.WriteString("\n")

	// Summary
	if report.Summary != "" {
		output.WriteString(styles.Bold.Render("Summary") + "\n\n")
		output.WriteString(fmt.Sprintf("  %s\n\n", styles.Secondary.Render(report.Summary)))
	}

	// Findings
	if len(report.Findings) > 0 {
		output.WriteString(styles.Bold.Render(fmt.Sprintf("Findings (%d)", len(report.Findings))) + "\n\n")

		for i, finding := range report.Findings {
			output.WriteString(formatFinding(&finding, i+1, styles))
			if i < len(report.Findings)-1 {
				output.WriteString("\n")
			}
		}
	}

	return output.String()
}

// formatFinding formats a single finding
func formatFinding(finding *Finding, index int, styles *visual.Styles) string {
	var output strings.Builder

	// Finding number and title
	output.WriteString(fmt.Sprintf("  %s %s\n",
		styles.Muted.Render(fmt.Sprintf("[%d]", index)),
		styles.Bold.Render(finding.Title)))

	// Category and severity
	output.WriteString(fmt.Sprintf("      Category:    %s",
		styles.Accent.Render(finding.Category)))

	if finding.Severity != "" {
		severityStyle := getSeverityStyle(finding.Severity, styles)
		output.WriteString(fmt.Sprintf("  |  Severity: %s",
			severityStyle.Render(strings.ToUpper(finding.Severity))))
	}
	output.WriteString("\n")

	// Source
	output.WriteString(fmt.Sprintf("      Source:      %s\n",
		styles.Muted.Render(finding.Source)))

	// Description
	if finding.Description != "" {
		output.WriteString(fmt.Sprintf("      %s\n",
			styles.Secondary.Render(finding.Description)))
	}

	// URL
	if finding.URL != "" {
		output.WriteString(fmt.Sprintf("      URL:         %s\n",
			styles.Info.Render(finding.URL)))
	}

	// Timestamp
	if finding.Timestamp != "" {
		output.WriteString(fmt.Sprintf("      Timestamp:   %s\n",
			styles.Muted.Render(finding.Timestamp)))
	}

	return output.String()
}

// Helper functions

func formatStatus(status string, styles *visual.Styles) string {
	switch strings.ToLower(status) {
	case "completed", "success":
		return styles.Success.Render("✓ " + strings.ToUpper(status))
	case "running", "in_progress":
		return styles.Warning.Render("◐ " + strings.ToUpper(status))
	case "failed", "error":
		return styles.Error.Render("✗ " + strings.ToUpper(status))
	case "pending", "queued":
		return styles.Muted.Render("○ " + strings.ToUpper(status))
	default:
		return styles.Muted.Render(strings.ToUpper(status))
	}
}

func formatProgress(progress float64, styles *visual.Styles) string {
	width := 20
	filled := int(progress * float64(width))
	if filled > width {
		filled = width
	}
	if filled < 0 {
		filled = 0
	}

	bar := strings.Repeat("█", filled) + strings.Repeat("░", width-filled)
	percentage := fmt.Sprintf("%.1f%%", progress*100)

	var style lipgloss.Style
	if progress >= 0.8 {
		style = styles.Success
	} else if progress >= 0.4 {
		style = styles.Warning
	} else {
		style = styles.Accent
	}

	return fmt.Sprintf("%s %s", bar, style.Render(percentage))
}

func formatRiskScore(score float64, styles *visual.Styles) string {
	width := 20
	normalized := score / 10.0 // Assuming score is 0-10
	if normalized > 1.0 {
		normalized = 1.0
	}

	filled := int(normalized * float64(width))
	bar := strings.Repeat("█", filled) + strings.Repeat("░", width-filled)

	var level string
	var style lipgloss.Style

	if score >= 7.0 {
		level = "HIGH"
		style = styles.Error
	} else if score >= 4.0 {
		level = "MEDIUM"
		style = styles.Warning
	} else {
		level = "LOW"
		style = styles.Success
	}

	return fmt.Sprintf("%s %s (%s)",
		bar,
		style.Render(fmt.Sprintf("%.1f", score)),
		style.Render(level))
}

func getSeverityStyle(severity string, styles *visual.Styles) lipgloss.Style {
	switch strings.ToLower(severity) {
	case "critical", "high":
		return styles.Error
	case "medium", "moderate":
		return styles.Warning
	case "low", "info":
		return styles.Success
	default:
		return styles.Muted
	}
}
