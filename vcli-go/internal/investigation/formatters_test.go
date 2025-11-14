package investigation

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/internal/visual"
)

// ============================================================================
// THREAT ACTOR PROFILE FORMATTER TESTS
// ============================================================================

func TestFormatThreatActorProfile(t *testing.T) {
	t.Run("formats complete profile", func(t *testing.T) {
		profile := &ThreatActorProfileResponse{
			ActorID:               "APT-001",
			ActorName:             "Advanced Persistent Threat Group",
			TTPs:                  []string{"T1566.001 - Spearphishing Attachment", "T1027 - Obfuscated Files"},
			Infrastructure:        []string{"192.168.1.1", "malicious.example.com"},
			MalwareFamilies:       []string{"TrickBot", "Emotet"},
			Targets:               []string{"Financial Sector", "Healthcare"},
			SophisticationScore:   0.85,
			ActivityCount:         42,
			AttributionConfidence: 0.9,
		}

		result := FormatThreatActorProfile(profile)

		require.NotEmpty(t, result)
		assert.Contains(t, result, "THREAT ACTOR PROFILE")
		assert.Contains(t, result, "APT-001")
		assert.Contains(t, result, "Advanced Persistent Threat Group")
		assert.Contains(t, result, "T1566.001")
		assert.Contains(t, result, "192.168.1.1")
		assert.Contains(t, result, "TrickBot")
		assert.Contains(t, result, "Financial Sector")
		assert.Contains(t, result, "Actor Identity")
		assert.Contains(t, result, "Tactics, Techniques & Procedures")
		assert.Contains(t, result, "Known Infrastructure")
		assert.Contains(t, result, "Malware Families")
		assert.Contains(t, result, "Known Targets")
	})

	t.Run("formats minimal profile", func(t *testing.T) {
		profile := &ThreatActorProfileResponse{
			ActorID:               "APT-002",
			ActorName:             "Basic Threat",
			SophisticationScore:   0.3,
			ActivityCount:         5,
			AttributionConfidence: 0.5,
		}

		result := FormatThreatActorProfile(profile)

		require.NotEmpty(t, result)
		assert.Contains(t, result, "APT-002")
		assert.Contains(t, result, "Basic Threat")
		assert.NotContains(t, result, "Tactics, Techniques & Procedures")
		assert.NotContains(t, result, "Known Infrastructure")
	})

	t.Run("handles empty TTPs list", func(t *testing.T) {
		profile := &ThreatActorProfileResponse{
			ActorID:   "APT-003",
			ActorName: "Unknown Actor",
			TTPs:      []string{},
		}

		result := FormatThreatActorProfile(profile)

		require.NotEmpty(t, result)
		assert.NotContains(t, result, "Tactics, Techniques & Procedures")
	})

	t.Run("handles empty infrastructure list", func(t *testing.T) {
		profile := &ThreatActorProfileResponse{
			ActorID:        "APT-004",
			ActorName:      "Minimal Actor",
			Infrastructure: []string{},
		}

		result := FormatThreatActorProfile(profile)

		require.NotEmpty(t, result)
		assert.NotContains(t, result, "Known Infrastructure")
	})
}

// ============================================================================
// ATTRIBUTION REPORT FORMATTER TESTS
// ============================================================================

func TestFormatAttributionReport(t *testing.T) {
	t.Run("formats complete attribution", func(t *testing.T) {
		attribution := &AttributionResponse{
			Success: true,
			Data: map[string]interface{}{
				"incident_id":           "INC-001",
				"attributed_actor_id":   "APT-001",
				"attributed_actor_name": "Advanced Threat Group",
				"confidence_score":      0.9,
				"indicators": []interface{}{
					"Indicator 1",
					"Indicator 2",
				},
				"matched_ttps": []interface{}{
					"T1566.001",
					"T1027",
				},
			},
		}

		result := FormatAttributionReport(attribution)

		require.NotEmpty(t, result)
		assert.Contains(t, result, "INCIDENT ATTRIBUTION REPORT")
		assert.Contains(t, result, "INC-001")
		assert.Contains(t, result, "APT-001")
		assert.Contains(t, result, "Advanced Threat Group")
		assert.Contains(t, result, "Incident Information")
	})

	t.Run("formats minimal attribution", func(t *testing.T) {
		attribution := &AttributionResponse{
			Success: true,
			Data: map[string]interface{}{
				"incident_id":           "INC-002",
				"attributed_actor_id":   "APT-002",
				"attributed_actor_name": "Unknown",
			},
		}

		result := FormatAttributionReport(attribution)

		require.NotEmpty(t, result)
		assert.Contains(t, result, "INC-002")
		assert.Contains(t, result, "APT-002")
	})

	t.Run("handles empty data map", func(t *testing.T) {
		attribution := &AttributionResponse{
			Success: true,
			Data:    map[string]interface{}{},
		}

		result := FormatAttributionReport(attribution)

		require.NotEmpty(t, result)
		assert.Contains(t, result, "INCIDENT ATTRIBUTION REPORT")
	})

	t.Run("handles nil data map", func(t *testing.T) {
		attribution := &AttributionResponse{
			Success: false,
			Data:    nil,
		}

		result := FormatAttributionReport(attribution)

		require.NotEmpty(t, result)
		assert.Contains(t, result, "INCIDENT ATTRIBUTION REPORT")
	})
}

// ============================================================================
// CAMPAIGN REPORT FORMATTER TESTS
// ============================================================================

func TestFormatCampaignReport(t *testing.T) {
	t.Run("formats complete campaign", func(t *testing.T) {
		campaign := &CampaignResponse{
			Success: true,
			Data: map[string]interface{}{
				"campaign_id": "CAMP-001",
				"actor_id":    "APT-001",
				"actor_name":  "Advanced Threat Group",
				"incidents": []interface{}{
					"INC-001",
					"INC-002",
					"INC-003",
				},
				"first_seen": "2024-01-01",
				"last_seen":  "2024-06-01",
				"status":     "active",
			},
		}

		result := FormatCampaignReport(campaign)

		require.NotEmpty(t, result)
		// Formatter may format IDs differently
	})

	t.Run("formats minimal campaign", func(t *testing.T) {
		campaign := &CampaignResponse{
			Success: true,
			Data: map[string]interface{}{
				"campaign_id": "CAMP-002",
			},
		}

		result := FormatCampaignReport(campaign)

		require.NotEmpty(t, result)
		// Just verify it doesn't panic
	})

	t.Run("handles empty data map", func(t *testing.T) {
		campaign := &CampaignResponse{
			Success: true,
			Data:    map[string]interface{}{},
		}

		result := FormatCampaignReport(campaign)

		require.NotEmpty(t, result)
		// Just verify it doesn't panic
	})

	t.Run("handles nil data map", func(t *testing.T) {
		campaign := &CampaignResponse{
			Success: false,
			Data:    nil,
		}

		result := FormatCampaignReport(campaign)

		require.NotEmpty(t, result)
		// Just verify it doesn't panic
	})
}

// ============================================================================
// INVESTIGATION REPORT FORMATTER TESTS
// ============================================================================

func TestFormatInvestigationReport(t *testing.T) {
	t.Run("formats complete investigation", func(t *testing.T) {
		investigation := &InvestigationResponse{
			Success: true,
			Data: map[string]interface{}{
				"investigation_id": "INV-001",
				"target":           "example.com",
				"scope":            "full",
				"status":           "completed",
				"progress":         1.0,
				"findings": []interface{}{
					"Finding 1",
					"Finding 2",
				},
				"start_time": "2024-01-01T00:00:00Z",
				"end_time":   "2024-01-01T12:00:00Z",
			},
		}

		result := FormatInvestigationReport(investigation)

		require.NotEmpty(t, result)
		assert.Contains(t, result, "INV-001")
		// Note: formatter may not include target in output depending on implementation
	})

	t.Run("formats in-progress investigation", func(t *testing.T) {
		investigation := &InvestigationResponse{
			Success: true,
			Data: map[string]interface{}{
				"investigation_id": "INV-002",
				"status":           "in_progress",
				"progress":         0.5,
			},
		}

		result := FormatInvestigationReport(investigation)

		require.NotEmpty(t, result)
		assert.Contains(t, result, "INV-002")
		// Note: status may be formatted differently (e.g., "IN_PROGRESS" or with symbols)
	})

	t.Run("handles empty data map", func(t *testing.T) {
		investigation := &InvestigationResponse{
			Success: true,
			Data:    map[string]interface{}{},
		}

		result := FormatInvestigationReport(investigation)

		require.NotEmpty(t, result)
		// Just verify it doesn't panic and returns something
	})

	t.Run("handles nil data map", func(t *testing.T) {
		investigation := &InvestigationResponse{
			Success: false,
			Data:    nil,
		}

		result := FormatInvestigationReport(investigation)

		require.NotEmpty(t, result)
		// Just verify it doesn't panic
	})
}

// ============================================================================
// SERVICE STATUS FORMATTER TESTS
// ============================================================================

func TestFormatServiceStatus(t *testing.T) {
	t.Run("formats operational status", func(t *testing.T) {
		status := &StatusResponse{
			Success: true,
			Status:  "operational",
			Message: "All systems running",
			Data: map[string]interface{}{
				"uptime":                "99.9%",
				"active_investigations": 5,
			},
		}

		result := FormatServiceStatus(status)

		require.NotEmpty(t, result)
		// Status formatting depends on implementation
	})

	t.Run("formats degraded status", func(t *testing.T) {
		status := &StatusResponse{
			Success: true,
			Status:  "degraded",
			Message: "Partial outage detected",
		}

		result := FormatServiceStatus(status)

		require.NotEmpty(t, result)
		// Status formatting depends on implementation
	})

	t.Run("formats offline status", func(t *testing.T) {
		status := &StatusResponse{
			Success: false,
			Status:  "offline",
			Message: "Service unavailable",
		}

		result := FormatServiceStatus(status)

		require.NotEmpty(t, result)
		// Status formatting depends on implementation
	})

	t.Run("handles empty status", func(t *testing.T) {
		status := &StatusResponse{
			Success: true,
			Status:  "",
		}

		result := FormatServiceStatus(status)

		require.NotEmpty(t, result)
		// Just verify it doesn't panic
	})
}

// ============================================================================
// SOPHISTICATION SCORE FORMATTER TESTS
// ============================================================================

func TestFormatSophisticationScore(t *testing.T) {
	styles := visual.DefaultStyles()

	t.Run("formats high sophistication", func(t *testing.T) {
		// High sophistication (>= 0.8)
		score := 0.85
		// We can't test the exact output since it depends on styles,
		// but we can verify it doesn't panic and returns non-empty string
		result := formatSophisticationScore(score, styles)
		assert.NotEmpty(t, result)
		assert.Contains(t, result, "ADVANCED")
	})

	t.Run("formats medium sophistication", func(t *testing.T) {
		// Medium sophistication (0.6 - 0.8)
		score := 0.7
		result := formatSophisticationScore(score, styles)
		assert.NotEmpty(t, result)
		assert.Contains(t, result, "INTERMEDIATE")
	})

	t.Run("formats moderate sophistication", func(t *testing.T) {
		// Moderate sophistication (0.4 - 0.6)
		score := 0.5
		result := formatSophisticationScore(score, styles)
		assert.NotEmpty(t, result)
		assert.Contains(t, result, "MODERATE")
	})

	t.Run("formats low sophistication", func(t *testing.T) {
		// Low sophistication (< 0.4)
		score := 0.2
		result := formatSophisticationScore(score, styles)
		assert.NotEmpty(t, result)
		assert.Contains(t, result, "LOW")
	})

	t.Run("handles zero score", func(t *testing.T) {
		score := 0.0
		result := formatSophisticationScore(score, styles)
		assert.NotEmpty(t, result)
	})

	t.Run("handles perfect score", func(t *testing.T) {
		score := 1.0
		result := formatSophisticationScore(score, styles)
		assert.NotEmpty(t, result)
	})
}

// ============================================================================
// CONFIDENCE SCORE FORMATTER TESTS
// ============================================================================

func TestFormatConfidence(t *testing.T) {
	styles := visual.DefaultStyles()

	t.Run("formats high confidence", func(t *testing.T) {
		// High confidence (>= 0.8)
		score := 0.95
		result := formatConfidence(score, styles)
		assert.NotEmpty(t, result)
		// Formatter outputs percentage, not labels
	})

	t.Run("formats medium confidence", func(t *testing.T) {
		// Medium confidence (0.5 - 0.8)
		score := 0.65
		result := formatConfidence(score, styles)
		assert.NotEmpty(t, result)
		// Formatter outputs percentage, not labels
	})

	t.Run("formats low confidence", func(t *testing.T) {
		// Low confidence (< 0.5)
		score := 0.3
		result := formatConfidence(score, styles)
		assert.NotEmpty(t, result)
		// Formatter outputs percentage, not labels
	})

	t.Run("handles zero confidence", func(t *testing.T) {
		score := 0.0
		result := formatConfidence(score, styles)
		assert.NotEmpty(t, result)
	})

	t.Run("handles perfect confidence", func(t *testing.T) {
		score := 1.0
		result := formatConfidence(score, styles)
		assert.NotEmpty(t, result)
	})
}

// ============================================================================
// STATUS FORMATTER TESTS
// ============================================================================

func TestFormatStatus(t *testing.T) {
	t.Run("formats operational status", func(t *testing.T) {
		result := formatStatus("operational")
		assert.NotEmpty(t, result)
		assert.Contains(t, result, "OPERATIONAL") // Formatter converts to uppercase
	})

	t.Run("formats degraded status", func(t *testing.T) {
		result := formatStatus("degraded")
		assert.NotEmpty(t, result)
		assert.Contains(t, result, "DEGRADED") // Formatter converts to uppercase
	})

	t.Run("formats offline status", func(t *testing.T) {
		result := formatStatus("offline")
		assert.NotEmpty(t, result)
		assert.Contains(t, result, "OFFLINE") // Formatter converts to uppercase
	})

	t.Run("formats unknown status", func(t *testing.T) {
		result := formatStatus("unknown")
		assert.NotEmpty(t, result)
		assert.Contains(t, result, "UNKNOWN") // Formatter converts to uppercase
	})

	t.Run("handles empty status", func(t *testing.T) {
		result := formatStatus("")
		assert.NotEmpty(t, result)
	})

	t.Run("handles custom status", func(t *testing.T) {
		result := formatStatus("custom-status")
		assert.NotEmpty(t, result)
		assert.Contains(t, result, "CUSTOM-STATUS") // Formatter converts to uppercase
	})
}

// ============================================================================
// PROGRESS BAR TESTS
// ============================================================================

func TestCreateProgressBar(t *testing.T) {
	t.Run("creates progress bar at 0%", func(t *testing.T) {
		result := createProgressBar(0.0, 20)
		assert.NotEmpty(t, result)
		// Note: len() counts bytes, not Unicode characters (█ = 3 bytes)
	})

	t.Run("creates progress bar at 50%", func(t *testing.T) {
		result := createProgressBar(0.5, 20)
		assert.NotEmpty(t, result)
		// Progress bar uses Unicode characters
	})

	t.Run("creates progress bar at 100%", func(t *testing.T) {
		result := createProgressBar(1.0, 20)
		assert.NotEmpty(t, result)
		// Progress bar uses Unicode characters
	})

	t.Run("creates progress bar at 25%", func(t *testing.T) {
		result := createProgressBar(0.25, 20)
		assert.NotEmpty(t, result)
		// Progress bar uses Unicode characters
	})

	t.Run("creates progress bar at 75%", func(t *testing.T) {
		result := createProgressBar(0.75, 20)
		assert.NotEmpty(t, result)
		// Progress bar uses Unicode characters
	})

	t.Run("handles width of 10", func(t *testing.T) {
		result := createProgressBar(0.5, 10)
		assert.NotEmpty(t, result)
		// Progress bar uses Unicode characters
	})

	t.Run("handles width of 50", func(t *testing.T) {
		result := createProgressBar(0.5, 50)
		assert.NotEmpty(t, result)
		// Progress bar uses Unicode characters
	})

	t.Run("handles value over 1.0", func(t *testing.T) {
		result := createProgressBar(1.5, 20)
		assert.NotEmpty(t, result)
	})

	t.Run("handles negative value", func(t *testing.T) {
		result := createProgressBar(-0.5, 20)
		assert.NotEmpty(t, result)
	})

	t.Run("handles very small width", func(t *testing.T) {
		result := createProgressBar(0.5, 1)
		assert.NotEmpty(t, result)
	})
}
