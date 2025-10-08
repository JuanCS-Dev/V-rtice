package narrative

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// FormatAnalysisReport formats the cognitive defense report with visual styling
func FormatAnalysisReport(report *CognitiveDefenseReport) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()
	var output strings.Builder

	// Header
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("COGNITIVE DEFENSE ANALYSIS", gradient)
	output.WriteString(title)
	output.WriteString("\n")
	output.WriteString(strings.Repeat("━", 70))
	output.WriteString("\n\n")

	// Analysis ID and metadata
	output.WriteString(styles.Muted.Render(fmt.Sprintf("Analysis ID:  %s\n", report.AnalysisID)))
	output.WriteString(styles.Muted.Render(fmt.Sprintf("Timestamp:    %s\n", report.Timestamp)))
	output.WriteString(styles.Muted.Render(fmt.Sprintf("Version:      %s\n", report.Version)))
	if report.SourceURL != nil {
		output.WriteString(styles.Muted.Render(fmt.Sprintf("Source URL:   %s\n", *report.SourceURL)))
	}
	output.WriteString("\n")

	// Overall Threat Assessment
	output.WriteString(styles.Bold.Render("THREAT ASSESSMENT"))
	output.WriteString("\n\n")

	// Threat score with visual bar
	threatBar := renderThreatBar(report.ThreatScore, palette)
	severityStyle := getSeverityStyle(report.Severity, styles)
	output.WriteString(fmt.Sprintf("Threat Score:     %.2f %s\n", report.ThreatScore, threatBar))
	output.WriteString(fmt.Sprintf("Severity:         %s\n", severityStyle.Render(strings.ToUpper(string(report.Severity)))))
	output.WriteString(fmt.Sprintf("Recommended:      %s\n", getActionStyle(report.RecommendedAction, styles).Render(strings.ToUpper(string(report.RecommendedAction)))))
	output.WriteString(fmt.Sprintf("Confidence:       %.0f%%\n", report.Confidence*100))
	output.WriteString("\n")

	// Module Results
	output.WriteString(styles.Bold.Render("MODULE ANALYSIS"))
	output.WriteString("\n\n")

	// Module 1: Source Credibility
	output.WriteString(styles.Info.Render("📰 Source Credibility"))
	output.WriteString("\n")
	credBar := renderScoreBar(report.CredibilityResult.CredibilityScore, 100, palette)
	output.WriteString(fmt.Sprintf("  Score:    %.1f/100 %s\n", report.CredibilityResult.CredibilityScore, credBar))
	output.WriteString(fmt.Sprintf("  Rating:   %s\n", getCredibilityStyle(report.CredibilityResult.Rating, styles).Render(strings.ToUpper(string(report.CredibilityResult.Rating)))))
	output.WriteString(fmt.Sprintf("  Domain:   %s\n", styles.Muted.Render(report.CredibilityResult.Domain)))
	output.WriteString("\n")

	// Module 2: Emotional Manipulation
	output.WriteString(styles.Info.Render("😡 Emotional Manipulation"))
	output.WriteString("\n")
	emotionBar := renderScoreBar(report.EmotionalResult.ManipulationScore, 1.0, palette)
	output.WriteString(fmt.Sprintf("  Manipulation: %.2f %s\n", report.EmotionalResult.ManipulationScore, emotionBar))
	output.WriteString(fmt.Sprintf("  Primary:      %s\n", styles.Accent.Render(string(report.EmotionalResult.EmotionProfile.PrimaryEmotion))))
	output.WriteString(fmt.Sprintf("  Arousal:      %.2f  Valence: %.2f\n",
		report.EmotionalResult.EmotionProfile.Arousal,
		report.EmotionalResult.EmotionProfile.Valence))
	output.WriteString("\n")

	// Module 3: Logical Fallacies
	output.WriteString(styles.Info.Render("🧠 Logical Analysis"))
	output.WriteString("\n")
	fallacyBar := renderScoreBar(report.LogicalResult.FallacyScore, 1.0, palette)
	coherenceBar := renderScoreBar(report.LogicalResult.CoherenceScore, 1.0, palette)
	output.WriteString(fmt.Sprintf("  Fallacies:  %.2f %s\n", report.LogicalResult.FallacyScore, fallacyBar))
	output.WriteString(fmt.Sprintf("  Coherence:  %.2f %s\n", report.LogicalResult.CoherenceScore, coherenceBar))
	output.WriteString("\n")

	// Module 4: Reality Distortion
	output.WriteString(styles.Info.Render("🔍 Reality Check"))
	output.WriteString("\n")
	distortionBar := renderScoreBar(report.RealityResult.DistortionScore, 1.0, palette)
	factualityBar := renderScoreBar(report.RealityResult.FactualityScore, 1.0, palette)
	output.WriteString(fmt.Sprintf("  Distortion: %.2f %s\n", report.RealityResult.DistortionScore, distortionBar))
	output.WriteString(fmt.Sprintf("  Factuality: %.2f %s\n", report.RealityResult.FactualityScore, factualityBar))
	output.WriteString("\n")

	// Reasoning and Evidence
	output.WriteString(styles.Bold.Render("ANALYSIS REASONING"))
	output.WriteString("\n\n")
	output.WriteString(styles.Info.Render(report.Reasoning))
	output.WriteString("\n\n")

	if len(report.Evidence) > 0 {
		output.WriteString(styles.Bold.Render("EVIDENCE"))
		output.WriteString("\n")
		for _, evidence := range report.Evidence {
			output.WriteString(fmt.Sprintf("  • %s\n", styles.Muted.Render(evidence)))
		}
		output.WriteString("\n")
	}

	// Performance
	output.WriteString(styles.Muted.Render(fmt.Sprintf("Processing Time: %.2fms", report.ProcessingTimeMs)))
	if len(report.ModelsUsed) > 0 {
		output.WriteString(styles.Muted.Render(fmt.Sprintf(" | Models: %s", strings.Join(report.ModelsUsed, ", "))))
	}
	output.WriteString("\n")

	return output.String()
}

// FormatHealthCheck formats health check response
func FormatHealthCheck(health *HealthCheckResponse) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()
	var output strings.Builder

	gradient := palette.PrimaryGradient()
	title := visual.GradientText("NARRATIVE FILTER HEALTH", gradient)
	output.WriteString(title)
	output.WriteString("\n")
	output.WriteString(strings.Repeat("━", 50))
	output.WriteString("\n\n")

	// Overall status
	statusIcon := "✅"
	statusStyle := styles.Success
	switch health.Status {
	case "degraded":
		statusIcon = "⚠️"
		statusStyle = styles.Warning
	case "unhealthy":
		statusIcon = "❌"
		statusStyle = styles.Error
	}

	output.WriteString(fmt.Sprintf("Status:    %s %s\n", statusIcon, statusStyle.Render(strings.ToUpper(health.Status))))
	output.WriteString(fmt.Sprintf("Version:   %s\n", styles.Info.Render(health.Version)))
	output.WriteString(fmt.Sprintf("Timestamp: %s\n\n", styles.Muted.Render(health.Timestamp)))

	// Services
	output.WriteString(styles.Bold.Render("INFRASTRUCTURE"))
	output.WriteString("\n")
	for service, healthy := range health.Services {
		icon := "✅"
		status := styles.Success.Render("healthy")
		if !healthy {
			icon = "❌"
			status = styles.Error.Render("unhealthy")
		}
		output.WriteString(fmt.Sprintf("  %s %-12s %s\n", icon, service+":", status))
	}
	output.WriteString("\n")

	// ML Models
	if len(health.ModelsLoaded) > 0 {
		output.WriteString(styles.Bold.Render("ML MODELS"))
		output.WriteString("\n")
		for _, model := range health.ModelsLoaded {
			output.WriteString(fmt.Sprintf("  ✅ %s\n", styles.Info.Render(model)))
		}
	} else {
		output.WriteString(styles.Muted.Render("No ML models loaded (using rule-based pipeline)\n"))
	}

	return output.String()
}

// FormatServiceInfo formats service information
func FormatServiceInfo(info *ServiceInfo) string {
	styles := visual.DefaultStyles()
	var output strings.Builder

	output.WriteString(styles.Bold.Render(strings.ToUpper(info.Service)))
	output.WriteString("\n")
	output.WriteString(strings.Repeat("━", 50))
	output.WriteString("\n\n")

	output.WriteString(fmt.Sprintf("Version:     %s\n", styles.Info.Render(info.Version)))
	output.WriteString(fmt.Sprintf("Environment: %s\n\n", styles.Accent.Render(info.Environment)))

	if len(info.Config) > 0 {
		output.WriteString(styles.Bold.Render("CONFIGURATION"))
		output.WriteString("\n")
		for key, value := range info.Config {
			output.WriteString(fmt.Sprintf("  %-20s %v\n", key+":", value))
		}
	}

	return output.String()
}

// FormatDatabaseStats formats database statistics
func FormatDatabaseStats(stats *DatabaseStats) string {
	styles := visual.DefaultStyles()
	var output strings.Builder

	output.WriteString(styles.Bold.Render("DATABASE STATISTICS"))
	output.WriteString("\n")
	output.WriteString(strings.Repeat("━", 50))
	output.WriteString("\n\n")

	for table, count := range stats.TableCounts {
		countStr := fmt.Sprintf("%d", count)
		if count == -1 {
			countStr = styles.Muted.Render("N/A")
		} else {
			countStr = styles.Info.Render(countStr)
		}
		output.WriteString(fmt.Sprintf("%-30s %s\n", table+":", countStr))
	}

	return output.String()
}

// ==================== HELPER FUNCTIONS ====================

// renderThreatBar creates a visual bar for threat score (0-1)
func renderThreatBar(score float64, palette *visual.VerticePalette) string {
	barLength := 20
	filled := int(score * float64(barLength))
	if filled > barLength {
		filled = barLength
	}
	if filled < 0 {
		filled = 0
	}

	bar := strings.Repeat("█", filled) + strings.Repeat("░", barLength-filled)

	// Color based on score
	if score >= 0.7 {
		return lipgloss.NewStyle().Foreground(palette.Error.ToTermenv()).Render(bar)
	} else if score >= 0.4 {
		return lipgloss.NewStyle().Foreground(palette.Warning.ToTermenv()).Render(bar)
	} else {
		return lipgloss.NewStyle().Foreground(palette.Success.ToTermenv()).Render(bar)
	}
}

// renderScoreBar creates a visual bar for any score
func renderScoreBar(score float64, max float64, palette *visual.VerticePalette) string {
	barLength := 15
	normalized := score / max
	if normalized > 1.0 {
		normalized = 1.0
	}
	if normalized < 0.0 {
		normalized = 0.0
	}

	filled := int(normalized * float64(barLength))
	bar := strings.Repeat("●", filled) + strings.Repeat("○", barLength-filled)

	// Color based on normalized score
	if normalized >= 0.7 {
		return lipgloss.NewStyle().Foreground(palette.Warning.ToTermenv()).Render(bar)
	} else if normalized >= 0.4 {
		return lipgloss.NewStyle().Foreground(palette.Accent.ToTermenv()).Render(bar)
	} else {
		return lipgloss.NewStyle().Foreground(palette.Info.ToTermenv()).Render(bar)
	}
}

// getSeverityStyle returns appropriate style for severity level
func getSeverityStyle(severity ManipulationSeverity, styles *visual.Styles) lipgloss.Style {
	switch severity {
	case SeverityCritical, SeverityHigh:
		return styles.Error
	case SeverityMedium:
		return styles.Warning
	case SeverityLow:
		return styles.Accent
	default:
		return styles.Success
	}
}

// getCredibilityStyle returns appropriate style for credibility rating
func getCredibilityStyle(rating CredibilityRating, styles *visual.Styles) lipgloss.Style {
	switch rating {
	case RatingTrusted, RatingGenerallyReliable:
		return styles.Success
	case RatingProceedWithCaution:
		return styles.Warning
	case RatingUnreliable, RatingHighlyUnreliable:
		return styles.Error
	default:
		return styles.Muted
	}
}

// getActionStyle returns appropriate style for recommended action
func getActionStyle(action CognitiveDefenseAction, styles *visual.Styles) lipgloss.Style {
	switch action {
	case ActionAllow:
		return styles.Success
	case ActionFlag:
		return styles.Accent
	case ActionQuarantine, ActionHumanReview:
		return styles.Warning
	case ActionBlock:
		return styles.Error
	default:
		return styles.Muted
	}
}
