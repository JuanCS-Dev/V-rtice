package performance

import (
	"context"
	"fmt"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/maximus"
)

// PerformanceWorkspace implements a real-time performance monitoring dashboard
type PerformanceWorkspace struct {
	// Backend clients
	governanceClient *maximus.GovernanceClient

	// State
	governanceStats  *maximus.PendingStatsResponse
	governanceHealth *maximus.GovernanceHealthResponse
	lastUpdate       time.Time
	updateInterval   time.Duration

	// UI State
	width       int
	height      int
	initialized bool

	// Context
	ctx context.Context

	// Configuration
	maximusEndpoint string
}

// Endpoint holds service endpoint configuration
type Endpoint struct {
	URL     string
	Healthy bool
	LastCheck time.Time
	Version   string
}

// NewPerformanceWorkspace creates a new Performance monitoring workspace
func NewPerformanceWorkspace(ctx context.Context, maximusURL string) *PerformanceWorkspace {
	return &PerformanceWorkspace{
		ctx:              ctx,
		maximusEndpoint:  maximusURL,
		updateInterval:   5 * time.Second,
		initialized:      false,
	}
}

// ID returns the workspace identifier
func (w *PerformanceWorkspace) ID() string {
	return "performance"
}

// Name returns the workspace display name
func (w *PerformanceWorkspace) Name() string {
	return "📊 Performance Dashboard"
}

// Description returns the workspace description
func (w *PerformanceWorkspace) Description() string {
	return "Real-time performance monitoring and system metrics"
}

// Icon returns the workspace icon
func (w *PerformanceWorkspace) Icon() string {
	return "📊"
}

// Initialize initializes the workspace
func (w *PerformanceWorkspace) Initialize() error {
	// Create MAXIMUS Governance client
	w.governanceClient = maximus.NewGovernanceClient(w.maximusEndpoint)

	// Initial health check
	health, err := w.governanceClient.Health()
	if err != nil {
		return fmt.Errorf("failed to connect to MAXIMUS Governance: %w", err)
	}
	w.governanceHealth = health

	// Initial stats fetch
	stats, err := w.governanceClient.GetPendingStats()
	if err != nil {
		return fmt.Errorf("failed to fetch governance stats: %w", err)
	}
	w.governanceStats = stats

	w.lastUpdate = time.Now()
	w.initialized = true

	return nil
}

// Init implements tea.Model interface
func (w *PerformanceWorkspace) Init() tea.Cmd {
	return tea.Batch(
		w.initializeCmd(),
		w.startUpdateTicker(),
	)
}

// Update handles Bubble Tea messages
func (w *PerformanceWorkspace) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		w.width = msg.Width
		w.height = msg.Height
		return w, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "r", "ctrl+r":
			// Manual refresh
			return w, w.fetchMetrics()
		}

	case InitializedMsg:
		w.initialized = true
		return w, w.fetchMetrics()

	case MetricsUpdateMsg:
		w.governanceStats = msg.GovernanceStats
		w.governanceHealth = msg.GovernanceHealth
		w.lastUpdate = time.Now()
		return w, nil

	case UpdateTickMsg:
		// Auto-refresh
		return w, w.fetchMetrics()

	case ErrorMsg:
		// Handle errors (would display in UI)
		return w, nil
	}

	return w, nil
}

// View renders the workspace
func (w *PerformanceWorkspace) View() string {
	if !w.initialized || w.width == 0 || w.height == 0 {
		return "Loading Performance Dashboard..."
	}

	var sections []string

	// Header
	sections = append(sections, w.renderHeader())

	// Main content
	mainContent := lipgloss.JoinHorizontal(
		lipgloss.Top,
		w.renderGovernanceMetrics(),
		w.renderSystemHealth(),
		w.renderThroughputMetrics(),
	)
	sections = append(sections, mainContent)

	// Footer with last update time
	sections = append(sections, w.renderFooter())

	return lipgloss.JoinVertical(lipgloss.Left, sections...)
}

// IsInitialized returns whether the workspace has been initialized
func (w *PerformanceWorkspace) IsInitialized() bool {
	return w.initialized
}

// Shortcuts returns keyboard shortcuts specific to this workspace
func (w *PerformanceWorkspace) Shortcuts() []Shortcut {
	return []Shortcut{
		{
			Key:         "r",
			Description: "Refresh metrics",
			Action: func() tea.Msg {
				return UpdateTickMsg{Timestamp: time.Now()}
			},
		},
		{
			Key:         "ctrl+r",
			Description: "Force refresh",
			Action: func() tea.Msg {
				return UpdateTickMsg{Timestamp: time.Now()}
			},
		},
	}
}

// Cleanup cleans up workspace resources
func (w *PerformanceWorkspace) Cleanup() error {
	// HTTP client cleanup (if needed)
	return nil
}

// renderHeader renders the workspace header
func (w *PerformanceWorkspace) renderHeader() string {
	headerStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#FFFFFF")).
		Background(lipgloss.Color("#4169E1")).
		Padding(0, 2).
		Width(w.width)

	return headerStyle.Render("📊 PERFORMANCE DASHBOARD - Real-Time System Metrics")
}

// renderGovernanceMetrics renders MAXIMUS Governance metrics
func (w *PerformanceWorkspace) renderGovernanceMetrics() string {
	panelWidth := w.width / 3

	panelStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#4169E1")).
		Width(panelWidth).
		Height(w.height - 6)

	var sections []string

	// Title
	sections = append(sections, lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#4169E1")).
		Render("🏛️  Governance Queue"))
	sections = append(sections, "")

	if w.governanceStats == nil {
		sections = append(sections, lipgloss.NewStyle().
			Faint(true).
			Render("No data available"))
	} else {
		// Total pending
		sections = append(sections, lipgloss.NewStyle().
			Bold(true).
			Render(fmt.Sprintf("Total Pending: %d", w.governanceStats.TotalPending)))
		sections = append(sections, "")

		// By Category
		sections = append(sections, lipgloss.NewStyle().
			Bold(true).
			Render("By Category:"))
		for category, count := range w.governanceStats.ByCategory {
			sections = append(sections, fmt.Sprintf("  %s: %d", category, count))
		}
		sections = append(sections, "")

		// By Severity
		sections = append(sections, lipgloss.NewStyle().
			Bold(true).
			Render("By Severity:"))
		for severity, count := range w.governanceStats.BySeverity {
			color := getSeverityColor(severity)
			sections = append(sections, lipgloss.NewStyle().
				Foreground(lipgloss.Color(color)).
				Render(fmt.Sprintf("  %s: %d", severity, count)))
		}
		sections = append(sections, "")

		// Oldest decision
		if w.governanceStats.OldestDecisionAge > 0 {
			age := time.Duration(w.governanceStats.OldestDecisionAge) * time.Second
			sections = append(sections, fmt.Sprintf("Oldest: %v ago", age.Round(time.Second)))
		}
	}

	content := lipgloss.JoinVertical(lipgloss.Left, sections...)
	return panelStyle.Render(content)
}

// renderSystemHealth renders system health status
func (w *PerformanceWorkspace) renderSystemHealth() string {
	panelWidth := w.width / 3

	panelStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#4169E1")).
		Width(panelWidth).
		Height(w.height - 6)

	var sections []string

	// Title
	sections = append(sections, lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#4169E1")).
		Render("💚 System Health"))
	sections = append(sections, "")

	// MAXIMUS Governance health
	sections = append(sections, lipgloss.NewStyle().
		Bold(true).
		Render("MAXIMUS Governance:"))

	if w.governanceHealth != nil {
		statusColor := "#00FF00"
		if w.governanceHealth.Status != "healthy" {
			statusColor = "#FF0000"
		}

		sections = append(sections, lipgloss.NewStyle().
			Foreground(lipgloss.Color(statusColor)).
			Render(fmt.Sprintf("  Status: %s", w.governanceHealth.Status)))

		if w.governanceHealth.Version != "" {
			sections = append(sections, fmt.Sprintf("  Version: %s", w.governanceHealth.Version))
		}
		if w.governanceHealth.Timestamp != "" {
			sections = append(sections, fmt.Sprintf("  Updated: %s", w.governanceHealth.Timestamp))
		}
	} else {
		sections = append(sections, lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FF0000")).
			Render("  Status: Disconnected"))
	}

	sections = append(sections, "")

	// Uptime placeholder
	sections = append(sections, lipgloss.NewStyle().
		Bold(true).
		Render("Uptime:"))
	sections = append(sections, fmt.Sprintf("  Dashboard: %v", time.Since(w.lastUpdate).Round(time.Second)))

	content := lipgloss.JoinVertical(lipgloss.Left, sections...)
	return panelStyle.Render(content)
}

// renderThroughputMetrics renders throughput and performance metrics
func (w *PerformanceWorkspace) renderThroughputMetrics() string {
	panelWidth := w.width / 3

	panelStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#4169E1")).
		Width(panelWidth).
		Height(w.height - 6)

	var sections []string

	// Title
	sections = append(sections, lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#4169E1")).
		Render("⚡ Throughput Metrics"))
	sections = append(sections, "")

	// Governance throughput
	sections = append(sections, lipgloss.NewStyle().
		Bold(true).
		Render("Decision Processing:"))

	if w.governanceStats != nil && w.governanceStats.Metadata != nil {
		if rate, ok := w.governanceStats.Metadata["decisions_per_minute"]; ok {
			sections = append(sections, fmt.Sprintf("  Rate: %.2f dec/min", rate))
		}
		if avgTime, ok := w.governanceStats.Metadata["avg_response_time"]; ok {
			sections = append(sections, fmt.Sprintf("  Avg Time: %.2fs", avgTime))
		}
	} else {
		sections = append(sections, "  No throughput data")
	}

	sections = append(sections, "")

	// Update frequency
	sections = append(sections, lipgloss.NewStyle().
		Bold(true).
		Render("Update Frequency:"))
	sections = append(sections, fmt.Sprintf("  Interval: %v", w.updateInterval))
	sections = append(sections, fmt.Sprintf("  Last: %v ago", time.Since(w.lastUpdate).Round(time.Second)))

	content := lipgloss.JoinVertical(lipgloss.Left, sections...)
	return panelStyle.Render(content)
}

// renderFooter renders the footer with shortcuts and status
func (w *PerformanceWorkspace) renderFooter() string {
	footerStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#AAAAAA")).
		Background(lipgloss.Color("#1C1C1C")).
		Padding(0, 1).
		Width(w.width)

	shortcuts := fmt.Sprintf("r: Refresh | q: Quit | Last update: %s",
		w.lastUpdate.Format("15:04:05"))
	return footerStyle.Render(shortcuts)
}

// initializeCmd returns a command to initialize the workspace
func (w *PerformanceWorkspace) initializeCmd() tea.Cmd {
	return func() tea.Msg {
		if err := w.Initialize(); err != nil {
			return ErrorMsg{Error: err}
		}
		return InitializedMsg{}
	}
}

// fetchMetrics returns a command to fetch latest metrics
func (w *PerformanceWorkspace) fetchMetrics() tea.Cmd {
	return func() tea.Msg {
		// Fetch governance stats
		stats, statsErr := w.governanceClient.GetPendingStats()
		if statsErr != nil {
			return ErrorMsg{Error: statsErr}
		}

		// Fetch governance health
		health, healthErr := w.governanceClient.Health()
		if healthErr != nil {
			return ErrorMsg{Error: healthErr}
		}

		return MetricsUpdateMsg{
			GovernanceStats:  stats,
			GovernanceHealth: health,
			Timestamp:        time.Now(),
		}
	}
}

// startUpdateTicker returns a command that sends update ticks periodically
func (w *PerformanceWorkspace) startUpdateTicker() tea.Cmd {
	return tea.Tick(w.updateInterval, func(t time.Time) tea.Msg {
		return UpdateTickMsg{Timestamp: t}
	})
}

// getSeverityColor returns color for severity level
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

// Shortcut represents a keyboard shortcut
type Shortcut struct {
	Key         string
	Description string
	Action      func() tea.Msg
}

// Custom messages

// InitializedMsg is sent when workspace initialization is complete
type InitializedMsg struct{}

// MetricsUpdateMsg is sent when metrics are updated
type MetricsUpdateMsg struct {
	GovernanceStats  *maximus.PendingStatsResponse
	GovernanceHealth *maximus.GovernanceHealthResponse
	Timestamp        time.Time
}

// UpdateTickMsg is sent periodically to trigger metric updates
type UpdateTickMsg struct {
	Timestamp time.Time
}

// ErrorMsg is sent when an error occurs
type ErrorMsg struct {
	Error error
}
