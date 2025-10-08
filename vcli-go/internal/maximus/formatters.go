package maximus

import (
	"fmt"
	"strings"
	"time"

	"github.com/verticedev/vcli-go/internal/visual"
)

// FormatConsciousnessState formats consciousness state for display
func FormatConsciousnessState(state *ConsciousnessState) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Title
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("MAXIMUS CONSCIOUS AI", gradient)
	output.WriteString(fmt.Sprintf("%s - Consciousness State\n", title))
	output.WriteString(strings.Repeat("━", 80))
	output.WriteString("\n\n")

	// System Health
	healthIcon := "✅"
	healthColor := styles.Success
	if state.SystemHealth != "HEALTHY" {
		healthIcon = "⚠️"
		healthColor = styles.Warning
	}
	output.WriteString(fmt.Sprintf("System Health:    %s %s\n",
		healthIcon,
		healthColor.Render(state.SystemHealth)))

	// ESGT Status
	esgtIcon := "⚡"
	esgtStatus := "INACTIVE"
	esgtColor := styles.Muted
	if state.ESGTActive {
		esgtStatus = "ACTIVE"
		esgtColor = styles.Success
	}
	output.WriteString(fmt.Sprintf("ESGT Status:      %s %s\n",
		esgtIcon,
		esgtColor.Render(esgtStatus)))

	// Arousal Level
	arousalBar := renderArousalBar(state.ArousalLevel, palette)
	output.WriteString(fmt.Sprintf("Arousal Level:    %.2f %s (%s)\n",
		state.ArousalLevel,
		arousalBar,
		styles.Accent.Render(state.ArousalClassification)))

	// Recent Events
	output.WriteString(fmt.Sprintf("Recent Events:    %s\n",
		styles.Info.Render(fmt.Sprintf("%d events", state.RecentEventsCount))))

	// TIG Metrics (if available)
	if len(state.TIGMetrics) > 0 {
		output.WriteString("\n")
		output.WriteString(styles.Accent.Render("TIG Metrics:"))
		output.WriteString("\n")
		for key, value := range state.TIGMetrics {
			output.WriteString(fmt.Sprintf("  %s: %v\n",
				styles.Muted.Render(key),
				value))
		}
	}

	// Timestamp
	output.WriteString(fmt.Sprintf("\nUpdated: %s\n", styles.Muted.Render(state.Timestamp)))

	return output.String()
}

// FormatESGTEvents formats ESGT events for display
func FormatESGTEvents(events []ESGTEvent) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Title
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("ESGT Events", gradient)
	output.WriteString(fmt.Sprintf("%s - Timeline\n", title))
	output.WriteString(strings.Repeat("━", 80))
	output.WriteString("\n\n")

	if len(events) == 0 {
		output.WriteString(styles.Muted.Render("No ESGT events recorded"))
		return output.String()
	}

	// Render events in reverse chronological order
	for i := len(events) - 1; i >= 0; i-- {
		event := events[i]
		output.WriteString(formatESGTEvent(event, styles))
		if i > 0 {
			output.WriteString("\n")
		}
	}

	return output.String()
}

func formatESGTEvent(event ESGTEvent, styles *visual.Styles) string {
	var output strings.Builder

	// Parse timestamp
	timestamp := event.Timestamp
	if t, err := time.Parse(time.RFC3339, event.Timestamp); err == nil {
		timestamp = t.Format("15:04:05")
	}

	// Success indicator
	icon := "✅"
	statusColor := styles.Success
	if !event.Success {
		icon = "❌"
		statusColor = styles.Error
	}

	// Event header
	output.WriteString(fmt.Sprintf("[%s] %s %s - %s\n",
		styles.Muted.Render(timestamp),
		icon,
		statusColor.Render("ESGT"),
		styles.Info.Render(event.EventID)))

	// Salience scores
	output.WriteString(fmt.Sprintf("  Salience: N:%.2f R:%.2f U:%.2f",
		event.Salience["novelty"],
		event.Salience["relevance"],
		event.Salience["urgency"]))

	// Coherence (if available)
	if event.Coherence != nil {
		coherenceBar := renderCoherenceBar(*event.Coherence)
		output.WriteString(fmt.Sprintf(" | Coherence: %.2f %s",
			*event.Coherence,
			coherenceBar))
	}

	output.WriteString("\n")

	// Additional details
	if event.NodesParticipating > 0 {
		output.WriteString(fmt.Sprintf("  Nodes: %d",
			event.NodesParticipating))
	}

	if event.DurationMs != nil {
		output.WriteString(fmt.Sprintf(" | Duration: %.1fms",
			*event.DurationMs))
	}

	output.WriteString("\n")

	// Reason (if failed)
	if event.Reason != nil && *event.Reason != "" {
		output.WriteString(fmt.Sprintf("  Reason: %s\n",
			styles.Error.Render(*event.Reason)))
	}

	return output.String()
}

// FormatArousalState formats arousal state for display
func FormatArousalState(arousal *ArousalState) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Title
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("Arousal State", gradient)
	output.WriteString(fmt.Sprintf("%s\n", title))
	output.WriteString(strings.Repeat("━", 80))
	output.WriteString("\n\n")

	// Current arousal with bar
	arousalBar := renderArousalBar(arousal.Arousal, palette)
	output.WriteString(fmt.Sprintf("Current Arousal:  %.3f %s\n",
		arousal.Arousal,
		arousalBar))

	// Classification
	output.WriteString(fmt.Sprintf("Classification:   %s\n",
		styles.Accent.Bold(true).Render(arousal.Level)))

	// Baseline
	output.WriteString(fmt.Sprintf("Baseline:         %.3f\n",
		arousal.Baseline))

	// Contributions
	output.WriteString("\n")
	output.WriteString(styles.Accent.Render("Contributions:"))
	output.WriteString("\n")
	output.WriteString(fmt.Sprintf("  Need:    %+.3f\n", arousal.NeedContribution))
	output.WriteString(fmt.Sprintf("  Stress:  %+.3f\n", arousal.StressContribution))

	// Timestamp
	output.WriteString(fmt.Sprintf("\nUpdated: %s\n", styles.Muted.Render(arousal.Timestamp)))

	return output.String()
}

// FormatMetrics formats consciousness metrics for display
func FormatMetrics(metrics *ConsciousnessMetrics) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Title
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("Consciousness Metrics", gradient)
	output.WriteString(fmt.Sprintf("%s\n", title))
	output.WriteString(strings.Repeat("━", 80))
	output.WriteString("\n\n")

	// TIG Metrics
	if len(metrics.TIGMetrics) > 0 {
		output.WriteString(styles.Accent.Render("TIG Fabric Metrics:"))
		output.WriteString("\n")
		for key, value := range metrics.TIGMetrics {
			output.WriteString(fmt.Sprintf("  %-25s %v\n",
				styles.Muted.Render(key+":"),
				value))
		}
		output.WriteString("\n")
	}

	// ESGT Stats
	if len(metrics.ESGTStats) > 0 {
		output.WriteString(styles.Accent.Render("ESGT Statistics:"))
		output.WriteString("\n")
		for key, value := range metrics.ESGTStats {
			output.WriteString(fmt.Sprintf("  %-25s %v\n",
				styles.Muted.Render(key+":"),
				value))
		}
	}

	return output.String()
}

// Helper functions

func renderArousalBar(level float64, palette *visual.VerticePalette) string {
	barLength := 20
	filled := int(level * float64(barLength))

	if filled < 0 {
		filled = 0
	}
	if filled > barLength {
		filled = barLength
	}

	bar := strings.Repeat("█", filled) + strings.Repeat("░", barLength-filled)

	// Color based on level
	var colorCode string
	if level < 0.3 {
		colorCode = "\033[36m" // Cyan (low)
	} else if level < 0.7 {
		colorCode = "\033[32m" // Green (medium)
	} else {
		colorCode = "\033[33m" // Yellow (high)
	}

	return fmt.Sprintf("%s%s\033[0m", colorCode, bar)
}

func renderCoherenceBar(coherence float64) string {
	barLength := 10
	filled := int(coherence * float64(barLength))

	if filled < 0 {
		filled = 0
	}
	if filled > barLength {
		filled = barLength
	}

	bar := strings.Repeat("●", filled) + strings.Repeat("○", barLength-filled)

	return bar
}
