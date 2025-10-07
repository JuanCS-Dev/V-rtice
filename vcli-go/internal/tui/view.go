package tui

import (
	"fmt"
	"strings"
	"time"

	"github.com/charmbracelet/lipgloss"
)

// View renders the complete TUI
// This is the "View" part of the MVU (Model-View-Update) pattern
func (m Model) View() string {
	if !m.ready {
		return "Initializing vCLI..."
	}

	// Build view based on active view type
	var content string

	switch m.activeView {
	case ViewTypeWorkspace:
		content = m.renderWorkspaceView()
	case ViewTypeList:
		content = m.renderListView()
	case ViewTypeDetails:
		content = m.renderDetailsView()
	case ViewTypeHelp:
		content = m.renderHelpView()
	case ViewTypeCommandPalette:
		content = m.renderCommandPaletteView()
	default:
		content = m.renderWorkspaceView()
	}

	// Build layout
	header := m.renderHeader()
	statusBar := m.renderStatusBar()
	notifications := m.renderNotifications()

	// Combine components
	var view strings.Builder

	view.WriteString(header)
	view.WriteString("\n")
	view.WriteString(content)
	view.WriteString("\n")
	view.WriteString(notifications)
	view.WriteString(statusBar)

	// Overlay help if active
	if m.helpOpen {
		return m.renderHelpOverlay(view.String())
	}

	// Overlay command palette if active
	if m.commandPaletteOpen {
		return m.renderCommandPaletteOverlay(view.String())
	}

	return view.String()
}

// renderHeader renders the header component
func (m Model) renderHeader() string {
	// Styles
	var (
		headerStyle = lipgloss.NewStyle().
				Background(lipgloss.Color("#7D56F4")).
				Foreground(lipgloss.Color("#FAFAFA")).
				Padding(0, 2).
				Bold(true)

		versionStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#FAFAFA")).
				Padding(0, 1)

		onlineStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#00FF00")).
				Padding(0, 1)

		offlineStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#FF0000")).
				Padding(0, 1)
	)

	// Build header content
	title := headerStyle.Render("vCLI 2.0")
	version := versionStyle.Render("v" + m.version)

	onlineStatus := "●"
	statusStyle := onlineStyle
	if m.offlineMode {
		onlineStatus = "○"
		statusStyle = offlineStyle
	}
	status := statusStyle.Render(onlineStatus)

	// Workspace indicator
	wsName := "No Workspace"
	if m.activeWS != "" && m.GetActiveWorkspace() != nil {
		wsName = m.GetActiveWorkspace().Name()
	}
	workspace := versionStyle.Render("📁 " + wsName)

	// Combine header elements
	header := lipgloss.JoinHorizontal(
		lipgloss.Left,
		title,
		version,
		status,
		workspace,
	)

	// Add padding to fill width
	width := m.windowSize.Width
	if width > 0 {
		header = lipgloss.NewStyle().
			Width(width).
			Background(lipgloss.Color("#7D56F4")).
			Render(header)
	}

	return header
}

// renderStatusBar renders the status bar component
func (m Model) renderStatusBar() string {
	// Styles
	var (
		statusStyle = lipgloss.NewStyle().
				Background(lipgloss.Color("#3C3C3C")).
				Foreground(lipgloss.Color("#FAFAFA")).
				Padding(0, 2)

		errorStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#FF0000")).
				Bold(true)

		warningStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#FFA500")).
				Bold(true)

		infoStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#00BFFF"))
	)

	// Build status bar content
	var parts []string

	// Error/Warning counts
	if len(m.errors) > 0 {
		parts = append(parts, errorStyle.Render(fmt.Sprintf("✗ %d", len(m.errors))))
	}

	if len(m.warnings) > 0 {
		parts = append(parts, warningStyle.Render(fmt.Sprintf("⚠ %d", len(m.warnings))))
	}

	// Plugin count
	parts = append(parts, infoStyle.Render(fmt.Sprintf("🔌 %d", len(m.loadedPlugins))))

	// Metrics
	if m.metrics.Timestamp.After(time.Time{}) {
		parts = append(parts, infoStyle.Render(fmt.Sprintf("CPU: %.1f%%", m.metrics.CPU)))
		parts = append(parts, infoStyle.Render(fmt.Sprintf("MEM: %.1f%%", m.metrics.Memory)))
	}

	// Loading indicators
	if len(m.loading) > 0 {
		parts = append(parts, infoStyle.Render("⏳ Loading..."))
	}

	// Sync status
	if m.syncInProgress {
		parts = append(parts, infoStyle.Render("🔄 Syncing..."))
	} else if m.queuedOps > 0 {
		parts = append(parts, infoStyle.Render(fmt.Sprintf("📦 %d queued", m.queuedOps)))
	}

	// Help hint
	parts = append(parts, infoStyle.Render("? Help"))

	// Combine status bar elements
	statusBar := statusStyle.Render(strings.Join(parts, " │ "))

	// Add padding to fill width
	width := m.windowSize.Width
	if width > 0 {
		statusBar = lipgloss.NewStyle().
			Width(width).
			Background(lipgloss.Color("#3C3C3C")).
			Render(statusBar)
	}

	return statusBar
}

// renderNotifications renders active notifications
func (m Model) renderNotifications() string {
	active := m.GetActiveNotifications()
	if len(active) == 0 {
		return ""
	}

	var notifications strings.Builder

	for _, notif := range active {
		style := lipgloss.NewStyle().
			Padding(0, 2).
			Margin(1, 2).
			Border(lipgloss.RoundedBorder())

		// Color based on severity
		switch notif.Severity {
		case SeverityLow:
			style = style.BorderForeground(lipgloss.Color("#00FF00"))
		case SeverityMedium:
			style = style.BorderForeground(lipgloss.Color("#FFA500"))
		case SeverityHigh:
			style = style.BorderForeground(lipgloss.Color("#FF4500"))
		case SeverityCritical:
			style = style.BorderForeground(lipgloss.Color("#FF0000"))
		}

		content := fmt.Sprintf("%s\n%s", notif.Title, notif.Message)
		notifications.WriteString(style.Render(content))
		notifications.WriteString("\n")
	}

	return notifications.String()
}

// renderWorkspaceView renders the workspace view
func (m Model) renderWorkspaceView() string {
	if m.GetActiveWorkspace() == nil {
		return m.renderNoWorkspace()
	}

	// Delegate to workspace's View method
	return m.GetActiveWorkspace().View()
}

// renderNoWorkspace renders the "no workspace" state
func (m Model) renderNoWorkspace() string {
	style := lipgloss.NewStyle().
		Padding(2, 4).
		Foreground(lipgloss.Color("#AAAAAA"))

	content := `No workspace selected

Available commands:
  Ctrl+W - Switch workspace
  Ctrl+P - Command palette
  ?      - Help
  q      - Quit`

	return style.Render(content)
}

// renderListView renders the list view (workspace selector)
func (m Model) renderListView() string {
	var items []string

	style := lipgloss.NewStyle().
		Padding(1, 2).
		Margin(0, 2)

	selectedStyle := lipgloss.NewStyle().
		Padding(1, 2).
		Margin(0, 2).
		Background(lipgloss.Color("#7D56F4")).
		Foreground(lipgloss.Color("#FAFAFA")).
		Bold(true)

	for id, ws := range m.workspaces {
		var itemStyle lipgloss.Style
		if id == m.activeWS {
			itemStyle = selectedStyle
		} else {
			itemStyle = style
		}

		item := fmt.Sprintf("%s %s - %s", ws.Icon(), ws.Name(), ws.Description())
		items = append(items, itemStyle.Render(item))
	}

	title := lipgloss.NewStyle().
		Bold(true).
		Padding(1, 2).
		Render("Select Workspace:")

	return title + "\n" + strings.Join(items, "\n")
}

// renderDetailsView renders the details view
func (m Model) renderDetailsView() string {
	style := lipgloss.NewStyle().
		Padding(2, 4)

	// Show details based on focused component
	var content string

	switch m.focused {
	case ComponentIDWorkspace:
		content = m.renderWorkspaceDetails()
	default:
		content = "No details available"
	}

	return style.Render(content)
}

// renderWorkspaceDetails renders workspace details
func (m Model) renderWorkspaceDetails() string {
	if m.GetActiveWorkspace() == nil {
		return "No workspace selected"
	}

	ws := m.GetActiveWorkspace()

	var details strings.Builder

	details.WriteString(fmt.Sprintf("Workspace: %s\n", ws.Name()))
	details.WriteString(fmt.Sprintf("ID: %s\n", ws.ID()))
	details.WriteString(fmt.Sprintf("Description: %s\n", ws.Description()))
	details.WriteString(fmt.Sprintf("Initialized: %v\n", ws.IsInitialized()))

	shortcuts := ws.Shortcuts()
	if len(shortcuts) > 0 {
		details.WriteString("\nShortcuts:\n")
		for _, sc := range shortcuts {
			details.WriteString(fmt.Sprintf("  %s - %s\n", sc.Key, sc.Description))
		}
	}

	return details.String()
}

// renderHelpView renders the help view
func (m Model) renderHelpView() string {
	style := lipgloss.NewStyle().
		Padding(2, 4)

	var help strings.Builder

	help.WriteString("vCLI 2.0 - Help\n")
	help.WriteString(strings.Repeat("=", 40))
	help.WriteString("\n\n")

	help.WriteString("Global Shortcuts:\n")
	help.WriteString("  Ctrl+C, q  - Quit\n")
	help.WriteString("  Ctrl+P     - Command palette\n")
	help.WriteString("  Ctrl+W     - Switch workspace\n")
	help.WriteString("  Ctrl+R     - Refresh metrics\n")
	help.WriteString("  ?          - Toggle help\n")
	help.WriteString("\n")

	help.WriteString("Navigation:\n")
	help.WriteString("  Tab        - Next component\n")
	help.WriteString("  Shift+Tab  - Previous component\n")
	help.WriteString("  ←/→        - Navigate history\n")
	help.WriteString("\n")

	help.WriteString("Workspace Shortcuts:\n")
	if ws := m.GetActiveWorkspace(); ws != nil {
		for _, sc := range ws.Shortcuts() {
			help.WriteString(fmt.Sprintf("  %-10s - %s\n", sc.Key, sc.Description))
		}
	} else {
		help.WriteString("  (No workspace active)\n")
	}

	return style.Render(help.String())
}

// renderCommandPaletteView renders the command palette
func (m Model) renderCommandPaletteView() string {
	style := lipgloss.NewStyle().
		Padding(1, 2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#7D56F4"))

	var palette strings.Builder

	palette.WriteString("Command Palette\n")
	palette.WriteString(strings.Repeat("-", 40))
	palette.WriteString("\n\n")

	// Available commands
	commands := []struct {
		name string
		desc string
	}{
		{"workspace:switch", "Switch workspace"},
		{"plugin:load", "Load plugin"},
		{"plugin:unload", "Unload plugin"},
		{"config:reload", "Reload configuration"},
		{"offline:sync", "Sync offline data"},
		{"theme:toggle", "Toggle theme"},
	}

	for _, cmd := range commands {
		palette.WriteString(fmt.Sprintf("  %-20s %s\n", cmd.name, cmd.desc))
	}

	return style.Render(palette.String())
}

// renderHelpOverlay renders help as an overlay
func (m Model) renderHelpOverlay(baseView string) string {
	help := m.renderHelpView()

	// Center the help box
	overlayStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#7D56F4")).
		Padding(1, 2).
		Background(lipgloss.Color("#1A1A1A"))

	helpBox := overlayStyle.Render(help)

	// Place help box in center (simplified - in production would calculate position)
	return lipgloss.Place(
		m.windowSize.Width,
		m.windowSize.Height,
		lipgloss.Center,
		lipgloss.Center,
		helpBox,
	)
}

// renderCommandPaletteOverlay renders command palette as an overlay
func (m Model) renderCommandPaletteOverlay(baseView string) string {
	palette := m.renderCommandPaletteView()

	// Place palette at top center
	return lipgloss.Place(
		m.windowSize.Width,
		m.windowSize.Height,
		lipgloss.Center,
		lipgloss.Top,
		palette,
		lipgloss.WithWhitespaceChars(" "),
	)
}

// renderErrorPanel renders the error panel
func (m Model) renderErrorPanel() string {
	if len(m.errors) == 0 {
		return ""
	}

	style := lipgloss.NewStyle().
		Padding(1, 2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#FF0000"))

	var panel strings.Builder

	panel.WriteString("Errors:\n")
	panel.WriteString(strings.Repeat("-", 40))
	panel.WriteString("\n")

	// Show last 5 errors
	start := 0
	if len(m.errors) > 5 {
		start = len(m.errors) - 5
	}

	for _, err := range m.errors[start:] {
		panel.WriteString(fmt.Sprintf("[%s] %s: %s\n",
			err.Timestamp.Format("15:04:05"),
			err.Code,
			err.Message,
		))
	}

	return style.Render(panel.String())
}

// renderMetricsPanel renders the metrics panel
func (m Model) renderMetricsPanel() string {
	if m.metrics.Timestamp.IsZero() {
		return ""
	}

	style := lipgloss.NewStyle().
		Padding(1, 2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#00BFFF"))

	var panel strings.Builder

	panel.WriteString("System Metrics:\n")
	panel.WriteString(strings.Repeat("-", 40))
	panel.WriteString("\n")

	panel.WriteString(fmt.Sprintf("CPU:        %.1f%%\n", m.metrics.CPU))
	panel.WriteString(fmt.Sprintf("Memory:     %.1f%%\n", m.metrics.Memory))
	panel.WriteString(fmt.Sprintf("Disk:       %.1f%%\n", m.metrics.Disk))
	panel.WriteString(fmt.Sprintf("Network In: %.1f KB/s\n", m.metrics.NetworkIn))
	panel.WriteString(fmt.Sprintf("Network Out:%.1f KB/s\n", m.metrics.NetworkOut))
	panel.WriteString(fmt.Sprintf("Plugins:    %d\n", m.metrics.PluginsLoaded))
	panel.WriteString(fmt.Sprintf("Errors:     %d\n", m.metrics.Errors))
	panel.WriteString(fmt.Sprintf("Warnings:   %d\n", m.metrics.Warnings))

	return style.Render(panel.String())
}

// renderPluginPanel renders the plugin panel
func (m Model) renderPluginPanel() string {
	if len(m.loadedPlugins) == 0 {
		return ""
	}

	style := lipgloss.NewStyle().
		Padding(1, 2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#00FF00"))

	var panel strings.Builder

	panel.WriteString("Loaded Plugins:\n")
	panel.WriteString(strings.Repeat("-", 40))
	panel.WriteString("\n")

	for name, info := range m.loadedPlugins {
		status := "●"
		if !info.Healthy {
			status = "○"
		}

		panel.WriteString(fmt.Sprintf("%s %s v%s\n", status, name, info.Version))
	}

	return style.Render(panel.String())
}
