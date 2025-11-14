package system

import (
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/dashboard"
	"github.com/verticedev/vcli-go/internal/dashboard/k8s"
	"github.com/verticedev/vcli-go/internal/dashboard/network"
	"github.com/verticedev/vcli-go/internal/dashboard/services"
	"github.com/verticedev/vcli-go/internal/dashboard/threat"
)

// SystemOverview is a meta-dashboard that composes all other dashboards
type SystemOverview struct {
	id            string
	focused       bool
	width         int
	height        int
	styles        dashboard.DashboardStyles
	layout        *dashboard.Layout
	k8sDash       dashboard.Dashboard
	servicesDash  dashboard.Dashboard
	threatDash    dashboard.Dashboard
	networkDash   dashboard.Dashboard
	refreshTicker *time.Ticker
}

// New creates a new system overview dashboard
func New(namespace string) *SystemOverview {
	return &SystemOverview{
		id:     "system-overview",
		styles: dashboard.DefaultStyles(),
	}
}

// Init initializes all sub-dashboards
func (d *SystemOverview) Init() tea.Cmd {
	// Create sub-dashboards
	d.k8sDash = k8s.New("default")
	d.servicesDash = services.New()
	d.threatDash = threat.New()
	d.networkDash = network.New()

	// Create 2x3 grid layout (Sampler style)
	d.layout = dashboard.NewLayout(dashboard.LayoutTypeGrid, 2, 3)
	d.layout.AddDashboard(d.k8sDash)
	d.layout.AddDashboard(d.servicesDash)
	d.layout.AddDashboard(d.threatDash)
	d.layout.AddDashboard(d.networkDash)

	// Resize layout to current dimensions
	d.layout.Resize(d.width, d.height)

	// Start refresh ticker
	d.refreshTicker = time.NewTicker(5 * time.Second)

	return tea.Batch(
		d.k8sDash.Init(),
		d.servicesDash.Init(),
		d.threatDash.Init(),
		d.networkDash.Init(),
		d.tickRefresh(),
	)
}

// Update handles messages and routes to sub-dashboards
func (d *SystemOverview) Update(msg tea.Msg) (dashboard.Dashboard, tea.Cmd) {
	cmds := make([]tea.Cmd, 0)

	switch msg := msg.(type) {
	case dashboard.RefreshMsg:
		if msg.DashboardID == d.id || msg.DashboardID == "" {
			// Refresh all sub-dashboards
			_, cmd := d.layout.Update(msg)
			if cmd != nil {
				cmds = append(cmds, cmd)
			}
		}

	case tea.KeyMsg:
		if d.focused {
			switch msg.String() {
			case "r":
				// Refresh all dashboards
				refreshMsg := dashboard.RefreshMsg{
					DashboardID: "",
					Timestamp:   time.Now(),
				}
				_, cmd := d.layout.Update(refreshMsg)
				if cmd != nil {
					cmds = append(cmds, cmd)
				}

			case "1":
				// Focus K8s dashboard
				d.k8sDash.Focus()
				d.servicesDash.Blur()
				d.threatDash.Blur()
				d.networkDash.Blur()

			case "2":
				// Focus services dashboard
				d.k8sDash.Blur()
				d.servicesDash.Focus()
				d.threatDash.Blur()
				d.networkDash.Blur()

			case "3":
				// Focus threat dashboard
				d.k8sDash.Blur()
				d.servicesDash.Blur()
				d.threatDash.Focus()
				d.networkDash.Blur()

			case "4":
				// Focus network dashboard
				d.k8sDash.Blur()
				d.servicesDash.Blur()
				d.threatDash.Blur()
				d.networkDash.Focus()
			}
		}

	case tickMsg:
		// Periodic refresh
		refreshMsg := dashboard.RefreshMsg{
			DashboardID: "",
			Timestamp:   time.Now(),
		}
		_, cmd := d.layout.Update(refreshMsg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
		cmds = append(cmds, d.tickRefresh())

	default:
		// Forward message to all sub-dashboards
		_, cmd := d.layout.Update(msg)
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
	}

	if len(cmds) > 0 {
		return d, tea.Batch(cmds...)
	}
	return d, nil
}

type tickMsg time.Time

func (d *SystemOverview) tickRefresh() tea.Cmd {
	return func() tea.Msg {
		time.Sleep(5 * time.Second)
		return tickMsg(time.Now())
	}
}

// View renders the complete system overview
func (d *SystemOverview) View() string {
	if d.layout == nil {
		return d.styles.Error.Render("System overview not initialized")
	}

	var b strings.Builder

	// Header
	b.WriteString(d.renderHeader())
	b.WriteString("\n\n")

	// Grid layout - 2x3 (top row: K8s + Services, middle row: Threat + Network, bottom row: reserved)
	b.WriteString(d.renderGrid())

	b.WriteString("\n")

	// Footer - hotkeys
	b.WriteString(d.renderFooter())

	return b.String()
}

// renderHeader renders system overview header
func (d *SystemOverview) renderHeader() string {
	titleStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#7D56F4")).
		Padding(0, 1)

	timeStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#808080"))

	title := titleStyle.Render("VÉRTICE System Overview")
	timestamp := timeStyle.Render(time.Now().Format("2006-01-02 15:04:05"))

	// Calculate padding to right-align timestamp
	padding := d.width - lipgloss.Width(title) - lipgloss.Width(timestamp) - 2
	if padding < 0 {
		padding = 0
	}

	return lipgloss.JoinHorizontal(
		lipgloss.Top,
		title,
		strings.Repeat(" ", padding),
		timestamp,
	)
}

// renderGrid renders 2x3 dashboard grid
func (d *SystemOverview) renderGrid() string {
	if d.layout == nil {
		return ""
	}

	// Calculate dimensions for each dashboard (2x3 grid)
	cellWidth := d.width / 3
	cellHeight := (d.height - 6) / 2 // -6 for header and footer

	// Top row: K8s | Services | Threat
	row1 := lipgloss.JoinHorizontal(
		lipgloss.Top,
		d.renderCell(d.k8sDash, cellWidth, cellHeight, "1"),
		d.renderCell(d.servicesDash, cellWidth, cellHeight, "2"),
		d.renderCell(d.threatDash, cellWidth, cellHeight, "3"),
	)

	// Bottom row: Network | Reserved | Reserved
	row2 := lipgloss.JoinHorizontal(
		lipgloss.Top,
		d.renderCell(d.networkDash, cellWidth, cellHeight, "4"),
		d.renderEmptyCell(cellWidth, cellHeight, "Reserved"),
		d.renderEmptyCell(cellWidth, cellHeight, "Reserved"),
	)

	return lipgloss.JoinVertical(lipgloss.Left, row1, row2)
}

// renderCell renders a dashboard in a bordered cell
func (d *SystemOverview) renderCell(dash dashboard.Dashboard, width, height int, hotkey string) string {
	borderColor := lipgloss.Color("#7D56F4")
	if dash.IsFocused() {
		borderColor = lipgloss.Color("#00BFFF")
	}

	cellStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(borderColor).
		Width(width - 2).
		Height(height - 2).
		Padding(0, 1)

	// Title with hotkey
	titleStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(borderColor)

	title := fmt.Sprintf("[%s] %s", hotkey, dash.Title())

	// Content
	content := dash.View()

	// Combine title and content
	combined := lipgloss.JoinVertical(
		lipgloss.Left,
		titleStyle.Render(title),
		"",
		content,
	)

	return cellStyle.Render(combined)
}

// renderEmptyCell renders placeholder for reserved cells
func (d *SystemOverview) renderEmptyCell(width, height int, label string) string {
	cellStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#404040")).
		Width(width - 2).
		Height(height - 2).
		Padding(0, 1).
		Align(lipgloss.Center, lipgloss.Center)

	labelStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#606060")).
		Italic(true)

	return cellStyle.Render(labelStyle.Render(label))
}

// renderFooter renders hotkey help
func (d *SystemOverview) renderFooter() string {
	helpStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#808080")).
		Faint(true)

	help := []string{
		"[1-4] Focus dashboard",
		"[r] Refresh",
		"[q] Quit",
	}

	return helpStyle.Render(strings.Join(help, "  •  "))
}

// Dashboard interface implementation

func (d *SystemOverview) ID() string      { return d.id }
func (d *SystemOverview) Title() string   { return "System Overview" }
func (d *SystemOverview) Focus()          { d.focused = true }
func (d *SystemOverview) Blur()           { d.focused = false }
func (d *SystemOverview) IsFocused() bool { return d.focused }

func (d *SystemOverview) Resize(width, height int) {
	d.width = width
	d.height = height

	if d.layout != nil {
		d.layout.Resize(width, height-6) // -6 for header and footer

		// Resize sub-dashboards
		cellWidth := width / 3
		cellHeight := (height - 6) / 2

		if d.k8sDash != nil {
			d.k8sDash.Resize(cellWidth-4, cellHeight-4)
		}
		if d.servicesDash != nil {
			d.servicesDash.Resize(cellWidth-4, cellHeight-4)
		}
		if d.threatDash != nil {
			d.threatDash.Resize(cellWidth-4, cellHeight-4)
		}
		if d.networkDash != nil {
			d.networkDash.Resize(cellWidth-4, cellHeight-4)
		}
	}
}
