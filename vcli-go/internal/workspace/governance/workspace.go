package governance

import (
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/visual"
	"github.com/verticedev/vcli-go/internal/workspace"
)

// Workspace implements Governance HITL workspace
type Workspace struct {
	workspace.BaseWorkspace
	client         *maximus.GovernanceClient
	stats          *maximus.PendingStatsResponse
	selectedIndex  int
	loading        bool
	error          string
	lastUpdate     time.Time
	autoRefresh    bool
	refreshTicker  *time.Ticker
	styles         *visual.Styles
}

// NewWorkspace creates a new governance workspace
func NewWorkspace(serverURL string) *Workspace {
	base := workspace.NewBaseWorkspace(
		"governance",
		"Governance",
		"🏛️",
		"Human-in-the-Loop ethical AI decision making",
	)

	return &Workspace{
		BaseWorkspace: base,
		client:        maximus.NewGovernanceClient(serverURL),
		selectedIndex: 0,
		loading:       true,
		autoRefresh:   true,
		styles:        visual.DefaultStyles(),
	}
}

// tickMsg is sent by ticker for auto-refresh
type tickMsg time.Time

// statsMsg contains loaded stats
type statsMsg struct {
	stats *maximus.PendingStatsResponse
	err   error
}

// Init initializes the workspace
func (w *Workspace) Init() tea.Cmd {
	return tea.Batch(
		w.loadStats(),
		w.tickCmd(),
	)
}

// Update handles messages
func (w *Workspace) Update(msg tea.Msg) (workspace.Workspace, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "r":
			return w, w.loadStats()
		case "a":
			w.autoRefresh = !w.autoRefresh
			if w.autoRefresh {
				return w, w.tickCmd()
			}
			return w, nil
		}

	case tickMsg:
		if w.autoRefresh {
			return w, tea.Batch(w.loadStats(), w.tickCmd())
		}
		return w, nil

	case statsMsg:
		w.loading = false
		w.lastUpdate = time.Now()
		if msg.err != nil {
			w.error = msg.err.Error()
		} else {
			w.stats = msg.stats
			w.error = ""
		}
		return w, nil
	}

	return w, nil
}

// View renders the workspace
func (w *Workspace) View(width, height int) string {
	// Header
	header := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("205")).
		Render("🏛️  GOVERNANCE WORKSPACE - HITL Decision Queue")

	// Status bar
	status := w.renderStatusBar()

	// Main content
	var content string
	if w.loading {
		content = w.styles.Muted.Render("⏳ Loading decision queue...")
	} else if w.error != "" {
		content = w.styles.Error.Render(fmt.Sprintf("❌ Error: %s", w.error))
	} else if w.stats == nil {
		content = w.styles.Muted.Render("No stats available")
	} else {
		content = w.renderStats()
	}

	// Help
	help := w.renderHelp()

	// Combine
	return fmt.Sprintf("\n%s\n\n%s\n\n%s\n\n%s\n\n%s",
		header,
		status,
		content,
		strings.Repeat("─", width-2),
		help,
	)
}

func (w *Workspace) renderStatusBar() string {
	statusParts := []string{}

	if w.stats != nil {
		totalStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("33"))
		statusParts = append(statusParts, totalStyle.Render(fmt.Sprintf("Total: %d", w.stats.TotalPending)))
	}

	if w.autoRefresh {
		statusParts = append(statusParts, "🔄 Auto-refresh: ON")
	} else {
		statusParts = append(statusParts, "⏸️  Auto-refresh: OFF")
	}

	if !w.lastUpdate.IsZero() {
		elapsed := time.Since(w.lastUpdate)
		statusParts = append(statusParts, fmt.Sprintf("Updated: %ds ago", int(elapsed.Seconds())))
	}

	return strings.Join(statusParts, " | ")
}

func (w *Workspace) renderStats() string {
	var parts []string

	// Total pending
	parts = append(parts, fmt.Sprintf("📋 Pending Decisions: %d", w.stats.TotalPending))

	// By risk level
	if len(w.stats.ByCategory) > 0 {
		parts = append(parts, "\n📊 By Risk Level:")
		for category, count := range w.stats.ByCategory {
			if count > 0 {
				parts = append(parts, fmt.Sprintf("  • %s: %d", category, count))
			}
		}
	}

	// Oldest decision age
	if w.stats.OldestDecisionAge > 0 {
		age := time.Duration(w.stats.OldestDecisionAge) * time.Second
		parts = append(parts, fmt.Sprintf("\n⏰ Oldest Decision: %s", age.Round(time.Second)))
	}

	return strings.Join(parts, "\n")
}

func (w *Workspace) renderHelp() string {
	helpItems := []string{
		"R: Refresh",
		"A: Toggle auto-refresh",
		"Q: Quit to shell",
	}
	return w.styles.Muted.Render("Keys: " + strings.Join(helpItems, " • "))
}

func (w *Workspace) loadStats() tea.Cmd {
	return func() tea.Msg {
		stats, err := w.client.GetPendingStats()
		return statsMsg{stats: stats, err: err}
	}
}

func (w *Workspace) tickCmd() tea.Cmd {
	return tea.Tick(5*time.Second, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}
