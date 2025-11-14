package cmd

import (
	"strings"

	"github.com/verticedev/vcli-go/internal/visual"
)

// Shared helper functions used across multiple commands

func getStatusIcon(status string) string {
	status = strings.ToLower(status)
	switch status {
	case "active", "healthy", "ok":
		return "✅"
	case "warning", "degraded":
		return "⚠️"
	case "error", "critical", "failed":
		return "❌"
	default:
		return "ℹ️"
	}
}

func getThreatLevelColor(level string, styles *visual.Styles) string {
	level = strings.ToLower(level)
	switch level {
	case "critical", "high":
		return styles.Error.Render(strings.ToUpper(level))
	case "medium":
		return styles.Warning.Render(strings.ToUpper(level))
	case "low":
		return styles.Success.Render(strings.ToUpper(level))
	default:
		return styles.Muted.Render(strings.ToUpper(level))
	}
}

func getSeverityEmoji(severity int) string {
	switch {
	case severity >= 8:
		return "🔴"
	case severity >= 5:
		return "🟠"
	case severity >= 3:
		return "🟡"
	default:
		return "🟢"
	}
}
