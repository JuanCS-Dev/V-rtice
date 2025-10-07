package governance

import (
	"context"
	"fmt"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	gov "github.com/verticedev/vcli-go/internal/governance"
)

// GovernanceWorkspace implements the Governance (HITL) workspace for ethical AI decision review
type GovernanceWorkspace struct {
	// Governance manager
	manager *gov.Manager

	// State
	decisions        []*gov.Decision
	selectedIndex    int
	metrics          gov.DecisionMetrics
	connectionStatus gov.ConnectionStatus

	// UI State
	focused    Section
	width      int
	height     int
	filterMode FilterMode

	// Context
	ctx        context.Context
	operatorID string
	sessionID  string

	// Configuration
	serverURL string
}

// Section represents different UI sections
type Section string

const (
	SectionDecisionList Section = "decision_list"
	SectionDetails      Section = "details"
	SectionMetrics      Section = "metrics"
)

// FilterMode represents decision filtering
type FilterMode string

const (
	FilterAll       FilterMode = "all"
	FilterCritical  FilterMode = "critical"
	FilterHigh      FilterMode = "high"
	FilterNearingSLA FilterMode = "nearing_sla"
)

// NewGovernanceWorkspace creates a new Governance workspace
func NewGovernanceWorkspace(ctx context.Context, serverURL, operatorID, sessionID string) *GovernanceWorkspace {
	return &GovernanceWorkspace{
		ctx:        ctx,
		serverURL:  serverURL,
		operatorID: operatorID,
		sessionID:  sessionID,
		focused:    SectionDecisionList,
		filterMode: FilterAll,
	}
}

// ID returns the workspace identifier
func (w *GovernanceWorkspace) ID() string {
	return "governance"
}

// Name returns the workspace display name
func (w *GovernanceWorkspace) Name() string {
	return "🏛️  Ethical AI Governance (HITL)"
}

// Description returns the workspace description
func (w *GovernanceWorkspace) Description() string {
	return "Human-in-the-Loop decision review for ethical AI operations"
}

// Initialize initializes the workspace
func (w *GovernanceWorkspace) Initialize() error {
	// Create governance manager
	w.manager = gov.NewManager(w.serverURL, w.operatorID, w.sessionID)

	// Start manager and connect to backend
	if err := w.manager.Start(w.ctx); err != nil {
		return fmt.Errorf("failed to start governance manager: %w", err)
	}

	// Start event processing
	go w.processManagerEvents()

	return nil
}

// Update handles Bubble Tea messages
func (w *GovernanceWorkspace) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		w.width = msg.Width
		w.height = msg.Height
		return w, nil

	case tea.KeyMsg:
		return w.handleKeyPress(msg)

	case DecisionUpdateMsg:
		w.decisions = msg.Decisions
		w.metrics = msg.Metrics
		return w, nil

	case ConnectionStatusMsg:
		w.connectionStatus = msg.Status
		return w, nil
	}

	return w, nil
}

// View renders the workspace
func (w *GovernanceWorkspace) View() string {
	if w.width == 0 || w.height == 0 {
		return "Loading Governance Workspace..."
	}

	var sections []string

	// Header
	sections = append(sections, w.renderHeader())

	// Connection status bar
	sections = append(sections, w.renderConnectionStatus())

	// Main content area
	mainContent := lipgloss.JoinHorizontal(
		lipgloss.Top,
		w.renderDecisionList(),
		w.renderDecisionDetails(),
		w.renderMetricsPanel(),
	)
	sections = append(sections, mainContent)

	// Footer with keybindings
	sections = append(sections, w.renderFooter())

	return lipgloss.JoinVertical(lipgloss.Left, sections...)
}

// Cleanup cleans up workspace resources
func (w *GovernanceWorkspace) Cleanup() error {
	if w.manager != nil {
		return w.manager.Stop(w.ctx)
	}
	return nil
}

// renderHeader renders the workspace header
func (w *GovernanceWorkspace) renderHeader() string {
	headerStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#FFFFFF")).
		Background(lipgloss.Color("#7D56F4")).
		Padding(0, 2).
		Width(w.width)

	return headerStyle.Render("🏛️  ETHICAL AI GOVERNANCE - Human-in-the-Loop Decision Review")
}

// renderConnectionStatus renders connection status bar
func (w *GovernanceWorkspace) renderConnectionStatus() string {
	var statusText string
	var statusColor string

	if w.connectionStatus.Connected {
		statusColor = "#00FF00"
		lastHeartbeat := time.Since(w.connectionStatus.LastHeartbeat)
		statusText = fmt.Sprintf("● Connected to %s | Events: %d | Last heartbeat: %v ago",
			w.connectionStatus.ServerURL,
			w.connectionStatus.EventsReceived,
			lastHeartbeat.Round(time.Second))
	} else if w.connectionStatus.Reconnecting {
		statusColor = "#FFA500"
		statusText = fmt.Sprintf("◐ Reconnecting to %s...", w.connectionStatus.ServerURL)
	} else {
		statusColor = "#FF0000"
		statusText = fmt.Sprintf("○ Disconnected from %s | %s",
			w.connectionStatus.ServerURL,
			w.connectionStatus.LastError)
	}

	statusStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(statusColor)).
		Padding(0, 1).
		Width(w.width)

	return statusStyle.Render(statusText)
}

// renderDecisionList renders the list of pending decisions
func (w *GovernanceWorkspace) renderDecisionList() string {
	listWidth := w.width / 3

	listStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#7D56F4")).
		Width(listWidth).
		Height(w.height - 8) // Reserve space for header, status, footer

	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#7D56F4")).
		Render(fmt.Sprintf("Pending Decisions (%d)", len(w.decisions)))

	var items []string
	items = append(items, title)
	items = append(items, "")

	if len(w.decisions) == 0 {
		items = append(items, lipgloss.NewStyle().
			Faint(true).
			Render("No pending decisions"))
	} else {
		for i, decision := range w.decisions {
			item := w.renderDecisionListItem(decision, i == w.selectedIndex)
			items = append(items, item)
		}
	}

	content := lipgloss.JoinVertical(lipgloss.Left, items...)
	return listStyle.Render(content)
}

// renderDecisionListItem renders a single decision in the list
func (w *GovernanceWorkspace) renderDecisionListItem(decision *gov.Decision, selected bool) string {
	// Risk level indicator
	riskColor := map[gov.RiskLevel]string{
		gov.RiskLevelLow:      "#00FF00",
		gov.RiskLevelMedium:   "#FFA500",
		gov.RiskLevelHigh:     "#FF6B6B",
		gov.RiskLevelCritical: "#FF0000",
	}

	indicator := lipgloss.NewStyle().
		Foreground(lipgloss.Color(riskColor[decision.RiskLevel])).
		Render("●")

	// SLA urgency
	var slaIndicator string
	if decision.SLADeadline != nil {
		timeLeft := time.Until(*decision.SLADeadline)
		if timeLeft < 5*time.Minute {
			slaIndicator = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#FF0000")).
				Render(" ⚠ URGENT")
		} else if timeLeft < 15*time.Minute {
			slaIndicator = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#FFA500")).
				Render(" ⏰")
		}
	}

	// Decision summary
	summary := fmt.Sprintf("%s %s | %s%s",
		indicator,
		decision.ActionType,
		decision.Target,
		slaIndicator)

	// Apply selection style
	style := lipgloss.NewStyle().Padding(0, 1)
	if selected {
		style = style.
			Background(lipgloss.Color("#7D56F4")).
			Foreground(lipgloss.Color("#FFFFFF")).
			Bold(true)
	}

	return style.Render(summary)
}

// renderDecisionDetails renders detailed view of selected decision
func (w *GovernanceWorkspace) renderDecisionDetails() string {
	detailWidth := w.width / 3

	detailStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#7D56F4")).
		Width(detailWidth).
		Height(w.height - 8)

	if w.selectedIndex < 0 || w.selectedIndex >= len(w.decisions) {
		return detailStyle.Render("No decision selected")
	}

	decision := w.decisions[w.selectedIndex]

	var sections []string

	// Title
	sections = append(sections, lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#7D56F4")).
		Render("Decision Details"))
	sections = append(sections, "")

	// Risk and confidence
	sections = append(sections, fmt.Sprintf("Risk Level: %s", decision.RiskLevel))
	sections = append(sections, fmt.Sprintf("Confidence: %.2f%%", decision.Confidence*100))
	sections = append(sections, fmt.Sprintf("Threat Score: %.2f", decision.ThreatScore))
	sections = append(sections, "")

	// Action
	sections = append(sections, lipgloss.NewStyle().Bold(true).Render("Recommended Action:"))
	sections = append(sections, fmt.Sprintf("  %s → %s", decision.ActionType, decision.Target))
	sections = append(sections, "")

	// AI Reasoning
	sections = append(sections, lipgloss.NewStyle().Bold(true).Render("AI Reasoning:"))
	sections = append(sections, wrapText(decision.Reasoning, detailWidth-4))
	sections = append(sections, "")

	// SLA
	if decision.SLADeadline != nil {
		timeLeft := time.Until(*decision.SLADeadline)
		sections = append(sections, lipgloss.NewStyle().Bold(true).Render("SLA Deadline:"))
		sections = append(sections, fmt.Sprintf("  %s (in %v)", decision.SLADeadline.Format("15:04:05"), timeLeft.Round(time.Second)))
	}

	content := lipgloss.JoinVertical(lipgloss.Left, sections...)
	return detailStyle.Render(content)
}

// renderMetricsPanel renders metrics and statistics
func (w *GovernanceWorkspace) renderMetricsPanel() string {
	metricsWidth := w.width / 3

	metricsStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#7D56F4")).
		Width(metricsWidth).
		Height(w.height - 8)

	var sections []string

	sections = append(sections, lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#7D56F4")).
		Render("Queue Metrics"))
	sections = append(sections, "")

	// Queue status
	sections = append(sections, fmt.Sprintf("Pending: %d", w.metrics.TotalPending))
	sections = append(sections, fmt.Sprintf("  Critical: %d", w.metrics.PendingCritical))
	sections = append(sections, fmt.Sprintf("  High: %d", w.metrics.PendingHigh))
	sections = append(sections, fmt.Sprintf("  Medium: %d", w.metrics.PendingMedium))
	sections = append(sections, fmt.Sprintf("  Low: %d", w.metrics.PendingLow))
	sections = append(sections, "")

	// SLA status
	sections = append(sections, lipgloss.NewStyle().Bold(true).Render("SLA Status:"))
	sections = append(sections, fmt.Sprintf("  Nearing SLA: %d", w.metrics.NearingSLA))
	sections = append(sections, fmt.Sprintf("  Breached: %d", w.metrics.BreachedSLA))
	sections = append(sections, "")

	// Throughput
	sections = append(sections, lipgloss.NewStyle().Bold(true).Render("Throughput:"))
	sections = append(sections, fmt.Sprintf("  %.1f dec/min", w.metrics.DecisionsPerMinute))
	sections = append(sections, fmt.Sprintf("  Avg response: %.1fs", w.metrics.AvgResponseTime))
	sections = append(sections, "")

	// Totals
	sections = append(sections, lipgloss.NewStyle().Bold(true).Render("Totals:"))
	sections = append(sections, fmt.Sprintf("  Approved: %d", w.metrics.TotalApproved))
	sections = append(sections, fmt.Sprintf("  Rejected: %d", w.metrics.TotalRejected))
	sections = append(sections, fmt.Sprintf("  Escalated: %d", w.metrics.TotalEscalated))

	content := lipgloss.JoinVertical(lipgloss.Left, sections...)
	return metricsStyle.Render(content)
}

// renderFooter renders keyboard shortcuts
func (w *GovernanceWorkspace) renderFooter() string {
	footerStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#AAAAAA")).
		Background(lipgloss.Color("#1C1C1C")).
		Padding(0, 1).
		Width(w.width)

	shortcuts := "↑/↓: Navigate | Enter: Approve | r: Reject | e: Escalate | q: Quit | f: Filter"
	return footerStyle.Render(shortcuts)
}

// handleKeyPress handles keyboard input
func (w *GovernanceWorkspace) handleKeyPress(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "up", "k":
		if w.selectedIndex > 0 {
			w.selectedIndex--
		}

	case "down", "j":
		if w.selectedIndex < len(w.decisions)-1 {
			w.selectedIndex++
		}

	case "enter":
		// Approve selected decision
		if w.selectedIndex >= 0 && w.selectedIndex < len(w.decisions) {
			decision := w.decisions[w.selectedIndex]
			go w.manager.ApproveDecision(w.ctx, decision.DecisionID, "Approved via TUI")
		}

	case "r":
		// Reject selected decision
		if w.selectedIndex >= 0 && w.selectedIndex < len(w.decisions) {
			decision := w.decisions[w.selectedIndex]
			go w.manager.RejectDecision(w.ctx, decision.DecisionID, "Rejected via TUI")
		}

	case "e":
		// Escalate selected decision
		if w.selectedIndex >= 0 && w.selectedIndex < len(w.decisions) {
			decision := w.decisions[w.selectedIndex]
			go w.manager.EscalateDecision(w.ctx, decision.DecisionID, "Escalated via TUI")
		}
	}

	return w, nil
}

// processManagerEvents processes events from governance manager
func (w *GovernanceWorkspace) processManagerEvents() {
	for {
		select {
		case <-w.ctx.Done():
			return
		case decision := <-w.manager.Decisions():
			// New decision received
			w.decisions = w.manager.GetPendingDecisions()
			w.metrics = w.manager.GetMetrics()
			// Would send tea.Cmd to update UI

		case event := <-w.manager.Events():
			// Manager event (connection, metrics, etc.)
			if event.Type == gov.EventConnectionEstablished || event.Type == gov.EventConnectionLost {
				w.connectionStatus = w.manager.GetConnectionStatus()
			}
			if event.Metrics != nil {
				w.metrics = *event.Metrics
			}

		case err := <-w.manager.Errors():
			// Error occurred
			_ = err // Would log or display error
		}
	}
}

// DecisionUpdateMsg is a custom message for decision updates
type DecisionUpdateMsg struct {
	Decisions []*gov.Decision
	Metrics   gov.DecisionMetrics
}

// ConnectionStatusMsg is a custom message for connection status updates
type ConnectionStatusMsg struct {
	Status gov.ConnectionStatus
}

// wrapText wraps text to fit within specified width
func wrapText(text string, width int) string {
	// Simple word wrapping
	if len(text) <= width {
		return text
	}
	return text[:width-3] + "..."
}
