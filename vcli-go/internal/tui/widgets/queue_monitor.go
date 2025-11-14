package widgets

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/maximus"
)

// QueueMonitor displays real-time decision queue status
type QueueMonitor struct {
	width  int
	height int
	stats  *maximus.PendingStatsResponse
}

// NewQueueMonitor creates a new queue monitor widget
func NewQueueMonitor() *QueueMonitor {
	return &QueueMonitor{}
}

// SetSize sets the widget dimensions
func (w *QueueMonitor) SetSize(width, height int) {
	w.width = width
	w.height = height
}

// Update updates the widget with new stats
func (w *QueueMonitor) Update(stats *maximus.PendingStatsResponse) {
	w.stats = stats
}

// Render renders the widget
func (w *QueueMonitor) Render() string {
	if w.stats == nil {
		return w.renderEmpty()
	}

	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#7D56F4")).
		Width(w.width).
		Height(w.height).
		Padding(1)

	var sections []string

	// Title
	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#7D56F4")).
		Render("📊 Decision Queue Status")
	sections = append(sections, title)
	sections = append(sections, "")

	// Total pending with visual bar
	total := w.stats.TotalPending
	sections = append(sections, fmt.Sprintf("Total Pending: %d", total))

	// Visual bar (0-100 scale)
	barWidth := w.width - 6
	if barWidth > 50 {
		barWidth = 50
	}
	fillRatio := float64(total) / 100.0
	if fillRatio > 1.0 {
		fillRatio = 1.0
	}
	filled := int(float64(barWidth) * fillRatio)
	bar := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#7D56F4")).
		Render(repeat("█", filled) + repeat("░", barWidth-filled))
	sections = append(sections, bar)
	sections = append(sections, "")

	// By Category
	if len(w.stats.ByCategory) > 0 {
		sections = append(sections, lipgloss.NewStyle().Bold(true).Render("By Category:"))
		for category, count := range w.stats.ByCategory {
			sections = append(sections, fmt.Sprintf("  %s: %d", category, count))
		}
		sections = append(sections, "")
	}

	// By Severity with colors
	if len(w.stats.BySeverity) > 0 {
		sections = append(sections, lipgloss.NewStyle().Bold(true).Render("By Severity:"))

		severityOrder := []string{"critical", "high", "medium", "low"}
		for _, severity := range severityOrder {
			if count, ok := w.stats.BySeverity[severity]; ok && count > 0 {
				color := getSeverityColor(severity)
				line := lipgloss.NewStyle().
					Foreground(lipgloss.Color(color)).
					Render(fmt.Sprintf("  %s: %d", severity, count))
				sections = append(sections, line)
			}
		}
	}

	content := lipgloss.JoinVertical(lipgloss.Left, sections...)
	return style.Render(content)
}

// renderEmpty renders empty state
func (w *QueueMonitor) renderEmpty() string {
	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#7D56F4")).
		Width(w.width).
		Height(w.height).
		Padding(1).
		Faint(true)

	return style.Render("📊 Decision Queue Status\n\nNo data available")
}

func getSeverityColor(severity string) string {
	switch severity {
	case "critical":
		return "#FF0000"
	case "high":
		return "#FF6B6B"
	case "medium":
		return "#FFA500"
	case "low":
		return "#00FF00"
	default:
		return "#FFFFFF"
	}
}

func repeat(s string, count int) string {
	if count <= 0 {
		return ""
	}
	result := ""
	for i := 0; i < count; i++ {
		result += s
	}
	return result
}
