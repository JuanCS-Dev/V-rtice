package workspace

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Manager manages multiple workspaces
type Manager struct {
	workspaces    []Workspace
	activeIndex   int
	width         int
	height        int
	styles        *visual.Styles
	palette       *visual.VerticePalette
	showHelp      bool
}

// NewManager creates a new workspace manager
func NewManager() *Manager {
	return &Manager{
		workspaces:  make([]Workspace, 0),
		activeIndex: 0,
		width:       80,
		height:      24,
		styles:      visual.DefaultStyles(),
		palette:     visual.DefaultPalette(),
		showHelp:    false,
	}
}

// AddWorkspace adds a workspace to the manager
func (m *Manager) AddWorkspace(w Workspace) {
	m.workspaces = append(m.workspaces, w)

	// Set first workspace as active
	if len(m.workspaces) == 1 {
		w.SetActive(true)
	}
}

// GetActive returns the currently active workspace
func (m *Manager) GetActive() Workspace {
	if len(m.workspaces) == 0 || m.activeIndex >= len(m.workspaces) {
		return nil
	}
	return m.workspaces[m.activeIndex]
}

// Next switches to the next workspace
func (m *Manager) Next() {
	if len(m.workspaces) == 0 {
		return
	}

	// Deactivate current
	m.workspaces[m.activeIndex].SetActive(false)

	// Move to next (wrap around)
	m.activeIndex = (m.activeIndex + 1) % len(m.workspaces)

	// Activate new
	m.workspaces[m.activeIndex].SetActive(true)
}

// Previous switches to the previous workspace
func (m *Manager) Previous() {
	if len(m.workspaces) == 0 {
		return
	}

	// Deactivate current
	m.workspaces[m.activeIndex].SetActive(false)

	// Move to previous (wrap around)
	m.activeIndex = (m.activeIndex - 1 + len(m.workspaces)) % len(m.workspaces)

	// Activate new
	m.workspaces[m.activeIndex].SetActive(true)
}

// Switch switches to workspace by index
func (m *Manager) Switch(index int) {
	if index < 0 || index >= len(m.workspaces) {
		return
	}

	// Deactivate current
	m.workspaces[m.activeIndex].SetActive(false)

	// Switch
	m.activeIndex = index

	// Activate new
	m.workspaces[m.activeIndex].SetActive(true)
}

// SetSize updates the terminal size
func (m *Manager) SetSize(width, height int) {
	m.width = width
	m.height = height
}

// ToggleHelp toggles help display
func (m *Manager) ToggleHelp() {
	m.showHelp = !m.showHelp
}

// Init initializes the manager
func (m *Manager) Init() tea.Cmd {
	var cmds []tea.Cmd

	// Initialize all workspaces
	for _, w := range m.workspaces {
		cmds = append(cmds, w.Init())
	}

	return tea.Batch(cmds...)
}

// Update handles messages
func (m *Manager) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.SetSize(msg.Width, msg.Height)
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			// Quit
			return m, tea.Quit
		case "tab":
			m.Next()
			return m, nil
		case "shift+tab":
			m.Previous()
			return m, nil
		case "1", "2", "3", "4", "5", "6", "7", "8", "9":
			// Quick switch to workspace by number
			index := int(msg.String()[0] - '1')
			m.Switch(index)
			return m, nil
		case "?":
			m.ToggleHelp()
			return m, nil
		}
	}

	// Forward to active workspace
	active := m.GetActive()
	if active != nil {
		updated, cmd := active.Update(msg)
		m.workspaces[m.activeIndex] = updated
		return m, cmd
	}

	return m, nil
}

// View renders the manager
func (m *Manager) View() string {
	if len(m.workspaces) == 0 {
		return m.styles.Error.Render("No workspaces available")
	}

	var output strings.Builder

	// Render header with workspace tabs
	output.WriteString(m.renderHeader())
	output.WriteString("\n")

	// Render active workspace content
	active := m.GetActive()
	if active != nil {
		// Calculate content area size (minus header and footer)
		contentHeight := m.height - 4 // Header (2) + Footer (2)
		if contentHeight < 1 {
			contentHeight = 1
		}

		content := active.View(m.width, contentHeight)
		output.WriteString(content)
		output.WriteString("\n")
	}

	// Render footer
	output.WriteString(m.renderFooter())

	// Render help overlay if enabled
	if m.showHelp {
		return m.renderHelpOverlay(output.String())
	}

	return output.String()
}

// renderHeader renders the workspace tabs
func (m *Manager) renderHeader() string {
	gradient := m.palette.PrimaryGradient()

	var tabs strings.Builder

	// Title
	title := visual.GradientText("vCLI Cognitive Cockpit", gradient)
	tabs.WriteString("╔══════════════════════════════════════════════════════════════════════════════╗\n")
	tabs.WriteString(fmt.Sprintf("║  %s                                                      ║\n", title))
	tabs.WriteString("╠══════════════════════════════════════════════════════════════════════════════╣\n")

	// Workspace tabs
	tabs.WriteString("║  ")

	for i, w := range m.workspaces {
		// Tab style
		tabText := fmt.Sprintf("%s %s", w.Icon(), w.Name())

		if i == m.activeIndex {
			// Active tab
			tabs.WriteString(m.styles.Accent.Bold(true).Render(fmt.Sprintf("[%s]", tabText)))
		} else {
			// Inactive tab
			tabs.WriteString(m.styles.Muted.Render(tabText))
		}

		if i < len(m.workspaces)-1 {
			tabs.WriteString(" │ ")
		}
	}

	// Padding
	tabs.WriteString(strings.Repeat(" ", m.width-len(tabs.String())-6))
	tabs.WriteString("  ║\n")
	tabs.WriteString("╠══════════════════════════════════════════════════════════════════════════════╣")

	return tabs.String()
}

// renderFooter renders the keyboard shortcuts
func (m *Manager) renderFooter() string {
	var footer strings.Builder

	footer.WriteString("╠══════════════════════════════════════════════════════════════════════════════╣\n")
	footer.WriteString(fmt.Sprintf("║  %s │ %s │ %s │ %s │ %s  ║\n",
		m.styles.Muted.Render("Tab: Next"),
		m.styles.Muted.Render("Shift+Tab: Prev"),
		m.styles.Muted.Render("1-9: Quick switch"),
		m.styles.Muted.Render("?: Help"),
		m.styles.Muted.Render("Q: Quit"),
	))
	footer.WriteString("╚══════════════════════════════════════════════════════════════════════════════╝")

	return footer.String()
}

// renderHelpOverlay renders help overlay
func (m *Manager) renderHelpOverlay(content string) string {
	helpStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.palette.Cyan.ToTermenv()).
		Padding(1, 2).
		Width(60).
		Align(lipgloss.Center)

	helpText := `
🎯 vCLI Cognitive Cockpit - Help

Keyboard Shortcuts:
  Tab / Shift+Tab    Navigate between workspaces
  1-9                Quick switch to workspace
  ?                  Toggle this help
  Q / Ctrl+C         Quit

Workspaces:
  🎯 Situational     Real-time cluster overview
  🔍 Investigation   Logs and resource inspection
  🏛️ Governance     HITL decision making (future)

Press ? to close this help
`

	help := helpStyle.Render(strings.TrimSpace(helpText))

	// Overlay on content
	return lipgloss.Place(m.width, m.height, lipgloss.Center, lipgloss.Center, help, lipgloss.WithWhitespaceChars(" "))
}
