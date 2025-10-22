package widgets

import (
	"fmt"
	"time"

	"github.com/charmbracelet/lipgloss"
)

// SLATracker displays SLA compliance metrics
type SLATracker struct {
	width  int
	height int

	// SLA Metrics
	nearingSLA  int // Decisions nearing SLA deadline
	breachedSLA int // Decisions that breached SLA
	onTime      int // Decisions completed on time
	oldestAge   time.Duration // Age of oldest pending decision

	// Compliance percentage
	complianceRate float64 // Percentage of decisions completed within SLA
}

// NewSLATracker creates a new SLA tracker widget
func NewSLATracker() *SLATracker {
	return &SLATracker{}
}

// SetSize sets the widget dimensions
func (w *SLATracker) SetSize(width, height int) {
	w.width = width
	w.height = height
}

// Update updates the widget with new SLA metrics
func (w *SLATracker) Update(nearingSLA, breachedSLA, onTime int, oldestAge time.Duration) {
	w.nearingSLA = nearingSLA
	w.breachedSLA = breachedSLA
	w.onTime = onTime
	w.oldestAge = oldestAge

	// Calculate compliance rate
	total := onTime + breachedSLA
	if total > 0 {
		w.complianceRate = float64(onTime) / float64(total) * 100.0
	} else {
		w.complianceRate = 100.0
	}
}

// Render renders the widget
func (w *SLATracker) Render() string {
	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#FF6B6B")).
		Width(w.width).
		Height(w.height).
		Padding(1)

	var sections []string

	// Title
	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#FF6B6B")).
		Render("⏰ SLA Compliance Tracker")
	sections = append(sections, title)
	sections = append(sections, "")

	// Compliance rate with color coding
	complianceColor := "#00FF00"
	if w.complianceRate < 95.0 {
		complianceColor = "#FFA500" // Yellow for < 95%
	}
	if w.complianceRate < 90.0 {
		complianceColor = "#FF0000" // Red for < 90%
	}

	complianceLine := lipgloss.NewStyle().
		Foreground(lipgloss.Color(complianceColor)).
		Bold(true).
		Render(fmt.Sprintf("Compliance: %.1f%%", w.complianceRate))
	sections = append(sections, complianceLine)

	// Visual compliance bar
	barWidth := w.width - 6
	if barWidth > 40 {
		barWidth = 40
	}
	filled := int(float64(barWidth) * w.complianceRate / 100.0)
	bar := lipgloss.NewStyle().
		Foreground(lipgloss.Color(complianceColor)).
		Render(repeat("█", filled) + repeat("░", barWidth-filled))
	sections = append(sections, bar)
	sections = append(sections, "")

	// SLA Status breakdown
	sections = append(sections, lipgloss.NewStyle().Bold(true).Render("Status Breakdown:"))

	// On time (green)
	onTimeLine := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#00FF00")).
		Render(fmt.Sprintf("  ✓ On Time: %d", w.onTime))
	sections = append(sections, onTimeLine)

	// Nearing SLA (yellow)
	if w.nearingSLA > 0 {
		nearingLine := lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFA500")).
			Render(fmt.Sprintf("  ⚠ Nearing SLA: %d", w.nearingSLA))
		sections = append(sections, nearingLine)
	}

	// Breached SLA (red)
	if w.breachedSLA > 0 {
		breachedLine := lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FF0000")).
			Render(fmt.Sprintf("  ✗ Breached: %d", w.breachedSLA))
		sections = append(sections, breachedLine)
	}

	sections = append(sections, "")

	// Oldest pending decision
	if w.oldestAge > 0 {
		ageColor := "#00FF00"
		if w.oldestAge > 15*time.Minute {
			ageColor = "#FFA500"
		}
		if w.oldestAge > 30*time.Minute {
			ageColor = "#FF0000"
		}

		ageLine := lipgloss.NewStyle().
			Foreground(lipgloss.Color(ageColor)).
			Render(fmt.Sprintf("Oldest Pending: %v", w.oldestAge.Round(time.Second)))
		sections = append(sections, ageLine)
	}

	content := lipgloss.JoinVertical(lipgloss.Left, sections...)
	return style.Render(content)
}
