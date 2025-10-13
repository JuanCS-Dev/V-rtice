package investigation

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// FormatThreatActorProfile formats a threat actor profile for display
func FormatThreatActorProfile(profile *ThreatActorProfileResponse) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Header
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("THREAT ACTOR PROFILE", gradient)
	output.WriteString(title + "\n")
	output.WriteString(strings.Repeat("━", 70) + "\n\n")

	// Actor Identity
	output.WriteString(styles.Bold.Render("Actor Identity") + "\n\n")
	output.WriteString(fmt.Sprintf("  ID:                  %s\n",
		styles.Info.Render(profile.ActorID)))
	output.WriteString(fmt.Sprintf("  Name:                %s\n",
		styles.Bold.Render(profile.ActorName)))
	output.WriteString(fmt.Sprintf("  Sophistication:      %s\n",
		formatSophisticationScore(profile.SophisticationScore, styles)))
	output.WriteString(fmt.Sprintf("  Activity Count:      %s\n",
		styles.Accent.Render(fmt.Sprintf("%d", profile.ActivityCount))))
	output.WriteString(fmt.Sprintf("  Attribution Conf:    %s\n\n",
		formatConfidence(profile.AttributionConfidence, styles)))

	// TTPs
	if len(profile.TTPs) > 0 {
		output.WriteString(styles.Bold.Render("Tactics, Techniques & Procedures (TTPs)") + "\n\n")
		for i, ttp := range profile.TTPs {
			output.WriteString(fmt.Sprintf("  %s %s\n",
				styles.Muted.Render(fmt.Sprintf("%2d.", i+1)),
				styles.Secondary.Render(ttp)))
		}
		output.WriteString("\n")
	}

	// Infrastructure
	if len(profile.Infrastructure) > 0 {
		output.WriteString(styles.Bold.Render("Known Infrastructure") + "\n\n")
		for _, infra := range profile.Infrastructure {
			output.WriteString(fmt.Sprintf("  • %s\n", styles.Muted.Render(infra)))
		}
		output.WriteString("\n")
	}

	// Malware Families
	if len(profile.MalwareFamilies) > 0 {
		output.WriteString(styles.Bold.Render("Malware Families") + "\n\n")
		for _, malware := range profile.MalwareFamilies {
			output.WriteString(fmt.Sprintf("  • %s\n", styles.Error.Render(malware)))
		}
		output.WriteString("\n")
	}

	// Targets
	if len(profile.Targets) > 0 {
		output.WriteString(styles.Bold.Render("Known Targets") + "\n\n")
		for _, target := range profile.Targets {
			output.WriteString(fmt.Sprintf("  • %s\n", styles.Warning.Render(target)))
		}
		output.WriteString("\n")
	}

	return output.String()
}

// FormatAttributionReport formats an attribution response
func FormatAttributionReport(attribution *AttributionResponse) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Header
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("INCIDENT ATTRIBUTION REPORT", gradient)
	output.WriteString(title + "\n")
	output.WriteString(strings.Repeat("━", 70) + "\n\n")

	// Incident Details
	output.WriteString(styles.Bold.Render("Incident Information") + "\n\n")
	
	incidentID := attribution.GetIncidentID()
	output.WriteString(fmt.Sprintf("  Incident ID:         %s\n",
		styles.Info.Render(incidentID)))

	// Attribution Result
	actorID := attribution.GetAttributedActorID()
	actorName := attribution.GetAttributedActorName()
	if actorID != "" {
		output.WriteString(fmt.Sprintf("  Attributed Actor:    %s\n",
			styles.Success.Render(actorID)))
		if actorName != "" && actorName != "Unknown" {
			output.WriteString(fmt.Sprintf("  Actor Name:          %s\n",
				styles.Bold.Render(actorName)))
		}
	} else {
		output.WriteString(fmt.Sprintf("  Attributed Actor:    %s\n",
			styles.Muted.Render("No attribution")))
	}

	confidence := attribution.GetConfidenceScore()
	output.WriteString(fmt.Sprintf("  Confidence:          %s\n\n",
		formatConfidence(confidence, styles)))

	// Matching TTPs (from flexible data schema)
	if attribution.Data != nil {
		if ttps, ok := attribution.Data["matching_ttps"].([]interface{}); ok && len(ttps) > 0 {
			output.WriteString(styles.Bold.Render("Matching TTPs") + "\n\n")
			for i, ttp := range ttps {
				if ttpStr, ok := ttp.(string); ok {
					output.WriteString(fmt.Sprintf("  %s %s\n",
						styles.Muted.Render(fmt.Sprintf("%2d.", i+1)),
						styles.Secondary.Render(ttpStr)))
				}
			}
		}
		output.WriteString("\n")
	}

	return output.String()
}

// FormatCampaignReport formats a campaign response
func FormatCampaignReport(campaign *CampaignResponse) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Header
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("CAMPAIGN ANALYSIS", gradient)
	output.WriteString(title + "\n\n")

	// Campaign Overview (flexible schema via Data)
	output.WriteString(styles.Bold.Render("Campaign Overview") + "\n")
	
	if campaignID, ok := campaign.Data["campaign_id"].(string); ok {
		output.WriteString(fmt.Sprintf("  Campaign ID:         %s\n",
			styles.Info.Render(campaignID)))
	}
	
	if campaignName, ok := campaign.Data["campaign_name"].(string); ok {
		output.WriteString(fmt.Sprintf("  Campaign Name:       %s\n",
			styles.Bold.Render(campaignName)))
	}

	if attributedActor, ok := campaign.Data["attributed_actor"].(string); ok && attributedActor != "" {
		output.WriteString(fmt.Sprintf("  Attributed Actor:    %s\n",
			styles.Success.Render(attributedActor)))
	}

	if pattern, ok := campaign.Data["campaign_pattern"].(string); ok {
		output.WriteString(fmt.Sprintf("  Pattern:             %s\n",
			styles.Accent.Render(pattern)))
	}
	
	if confidence, ok := campaign.Data["confidence_score"].(float64); ok {
		output.WriteString(fmt.Sprintf("  Confidence:          %s\n\n",
			formatConfidence(confidence, styles)))
	}

	// Timeline
	output.WriteString(styles.Bold.Render("Timeline") + "\n")
	if startDate, ok := campaign.Data["start_date"].(string); ok {
		output.WriteString(fmt.Sprintf("  Start Date:          %s\n",
			styles.Muted.Render(startDate)))
	}
	if lastActivity, ok := campaign.Data["last_activity"].(string); ok {
		output.WriteString(fmt.Sprintf("  Last Activity:       %s\n",
			styles.Warning.Render(lastActivity)))
	}
	
	// Incidents
	if incidentsRaw, ok := campaign.Data["incidents"].([]interface{}); ok {
		output.WriteString(fmt.Sprintf("  Incident Count:      %s\n\n",
			styles.Accent.Render(fmt.Sprintf("%d", len(incidentsRaw)))))
			
		if len(incidentsRaw) > 0 {
			output.WriteString(styles.Bold.Render("Related Incidents") + "\n")
			for i, incidentRaw := range incidentsRaw {
				if incident, ok := incidentRaw.(string); ok {
					output.WriteString(fmt.Sprintf("  %s %s\n",
						styles.Muted.Render(fmt.Sprintf("%2d.", i+1)),
						styles.Secondary.Render(incident)))
				}
			}
		}
		output.WriteString("\n")
	}

	// TTPs (flexible schema)
	if ttpsRaw, ok := campaign.Data["ttps"].([]interface{}); ok && len(ttpsRaw) > 0 {
		output.WriteString(styles.Bold.Render("Campaign TTPs") + "\n")
		for i, ttpRaw := range ttpsRaw {
			if ttp, ok := ttpRaw.(string); ok {
				output.WriteString(fmt.Sprintf("  %s %s\n",
					styles.Muted.Render(fmt.Sprintf("%2d.", i+1)),
					styles.Secondary.Render(ttp)))
			}
		}
		output.WriteString("\n")
	}

	// Targets (flexible schema)
	if targetsRaw, ok := campaign.Data["targets"].([]interface{}); ok && len(targetsRaw) > 0 {
		output.WriteString(styles.Bold.Render("Targeted Entities") + "\n")
		for _, targetRaw := range targetsRaw {
			if target, ok := targetRaw.(string); ok {
				output.WriteString(fmt.Sprintf("  • %s\n", styles.Warning.Render(target)))
			}
		}
		output.WriteString("\n")
	}

	return output.String()
}

// FormatInvestigationReport formats an investigation response
func FormatInvestigationReport(investigation *InvestigationResponse) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Header
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("AUTONOMOUS INVESTIGATION REPORT", gradient)
	output.WriteString(title + "\n\n")

	// Investigation Overview
	output.WriteString(styles.Bold.Render("Investigation Overview") + "\n")
	output.WriteString(fmt.Sprintf("  Investigation ID:    %s\n",
		styles.Info.Render(investigation.InvestigationID)))
	output.WriteString(fmt.Sprintf("  Incident ID:         %s\n",
		styles.Secondary.Render(investigation.IncidentID)))
	output.WriteString(fmt.Sprintf("  Status:              %s\n",
		formatStatus(investigation.Status)))
	output.WriteString(fmt.Sprintf("  Playbook Used:       %s\n",
		styles.Accent.Render(investigation.PlaybookUsed)))

	if investigation.DurationSeconds != nil {
		output.WriteString(fmt.Sprintf("  Duration:            %s\n",
			styles.Muted.Render(fmt.Sprintf("%.2f seconds", *investigation.DurationSeconds))))
	}

	output.WriteString(fmt.Sprintf("  Evidence Count:      %s\n",
		styles.Bold.Render(fmt.Sprintf("%d", investigation.EvidenceCount))))
	output.WriteString(fmt.Sprintf("  Confidence:          %s\n\n",
		formatConfidence(investigation.ConfidenceScore, styles)))

	// Attribution
	if investigation.AttributedActor != nil {
		output.WriteString(styles.Bold.Render("Attribution") + "\n")
			output.WriteString(fmt.Sprintf("  Attributed Actor:    %s\n\n",
			styles.Success.Render(*investigation.AttributedActor)))
	}

	// Findings
	if len(investigation.Findings) > 0 {
		output.WriteString(styles.Bold.Render("Key Findings") + "\n")
			for i, finding := range investigation.Findings {
			output.WriteString(fmt.Sprintf("  %s %s\n",
				styles.Muted.Render(fmt.Sprintf("%2d.", i+1)),
				styles.Secondary.Render(finding)))
		}
		output.WriteString("\n")
	}

	// Related Campaigns
	if len(investigation.RelatedCampaigns) > 0 {
		output.WriteString(styles.Bold.Render("Related Campaigns") + "\n")
			for i, campaign := range investigation.RelatedCampaigns {
			output.WriteString(fmt.Sprintf("  %s %s\n",
				styles.Muted.Render(fmt.Sprintf("%2d.", i+1)),
				styles.Warning.Render(campaign)))
		}
		output.WriteString("\n")
	}

	// Recommendations
	if len(investigation.Recommendations) > 0 {
		output.WriteString(styles.Bold.Render("Recommendations") + "\n")
			for _, rec := range investigation.Recommendations {
			output.WriteString(fmt.Sprintf("  %s %s\n",
				styles.Success.Render(fmt.Sprintf("✓")),
				styles.Secondary.Render(rec)))
		}
		output.WriteString("\n")
	}

	return output.String()
}

// FormatServiceStatus formats service status
func FormatServiceStatus(status *StatusResponse) string {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()

	var output strings.Builder

	// Header
	gradient := palette.PrimaryGradient()
	title := visual.GradientText("INVESTIGATION SERVICE STATUS", gradient)
	output.WriteString(title + "\n\n")

	// Service Info
	output.WriteString(styles.Bold.Render("Service Information") + "\n")
	output.WriteString(fmt.Sprintf("  Service:             %s\n",
		styles.Info.Render(status.Service)))
	output.WriteString(fmt.Sprintf("  Status:              %s\n",
		formatStatus(status.Status)))
	output.WriteString(fmt.Sprintf("  Timestamp:           %s\n\n",
		styles.Muted.Render(status.Timestamp)))

	// Components
	if len(status.Components) > 0 {
		output.WriteString(styles.Bold.Render("Components") + "\n")
			for name, details := range status.Components {
			componentStatus := "unknown"
			if s, ok := details["status"].(string); ok {
				componentStatus = s
			}
			output.WriteString(fmt.Sprintf("  %s:  %s\n",
				styles.Bold.Render(name),
				formatStatus(componentStatus)))
		}
		output.WriteString("\n")
	}

	return output.String()
}

// Helper functions

func formatSophisticationScore(score float64, styles *visual.Styles) string {
	bar := createProgressBar(score, 20)

	var level string
	var style lipgloss.Style

	if score >= 0.8 {
		level = "ADVANCED"
		style = styles.Error
	} else if score >= 0.6 {
		level = "INTERMEDIATE"
		style = styles.Warning
	} else if score >= 0.4 {
		level = "MODERATE"
		style = styles.Accent
	} else {
		level = "LOW"
		style = styles.Success
	}

	return fmt.Sprintf("%s %s (%s)",
		bar,
		style.Render(fmt.Sprintf("%.1f%%", score*100)),
		style.Render(level))
}

func formatConfidence(score float64, styles *visual.Styles) string {
	bar := createProgressBar(score, 20)

	var style lipgloss.Style
	if score >= 0.7 {
		style = styles.Success
	} else if score >= 0.5 {
		style = styles.Warning
	} else {
		style = styles.Error
	}

	return fmt.Sprintf("%s %s",
		bar,
		style.Render(fmt.Sprintf("%.1f%%", score*100)))
}

func formatStatus(status string) string {
	styles := visual.DefaultStyles()

	switch strings.ToLower(status) {
	case "active", "running", "healthy", "completed":
		return styles.Success.Render("● " + strings.ToUpper(status))
	case "pending", "in_progress":
		return styles.Warning.Render("◐ " + strings.ToUpper(status))
	case "failed", "error", "unhealthy":
		return styles.Error.Render("✗ " + strings.ToUpper(status))
	default:
		return styles.Muted.Render("○ " + strings.ToUpper(status))
	}
}

func createProgressBar(value float64, width int) string {
	filled := int(value * float64(width))
	if filled > width {
		filled = width
	}
	if filled < 0 {
		filled = 0
	}

	bar := strings.Repeat("█", filled) + strings.Repeat("░", width-filled)
	return bar
}
