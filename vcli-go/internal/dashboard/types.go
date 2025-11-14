package dashboard

import (
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Dashboard represents a composable dashboard component
type Dashboard interface {
	// Init initializes the dashboard
	Init() tea.Cmd

	// Update handles messages and updates state
	Update(msg tea.Msg) (Dashboard, tea.Cmd)

	// View renders the dashboard
	View() string

	// ID returns unique dashboard identifier
	ID() string

	// Title returns dashboard title
	Title() string

	// Focus sets keyboard focus
	Focus()

	// Blur removes keyboard focus
	Blur()

	// IsFocused returns focus state
	IsFocused() bool

	// Resize handles window resize
	Resize(width, height int)
}

// RefreshMsg triggers dashboard data refresh
type RefreshMsg struct {
	DashboardID string
	Timestamp   time.Time
}

// ErrorMsg represents dashboard error
type ErrorMsg struct {
	DashboardID string
	Error       error
}

// DataMsg represents data update
type DataMsg struct {
	DashboardID string
	Data        interface{}
}

// Layout manages dashboard positioning
type Layout struct {
	Type     LayoutType
	Rows     int
	Cols     int
	Dashboards []Dashboard
	Width    int
	Height   int
}

// LayoutType defines layout strategy
type LayoutType int

const (
	LayoutTypeGrid LayoutType = iota
	LayoutTypeStack
	LayoutTypeSplit
)

// DefaultStyles returns default dashboard styles
func DefaultStyles() DashboardStyles {
	return DashboardStyles{
		Border:      lipgloss.RoundedBorder(),
		BorderColor: lipgloss.Color("#7D56F4"),
		Title: lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#7D56F4")).
			Padding(0, 1),
		Value: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#00BFFF")),
		Label: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#808080")),
		Success: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#00FF00")),
		Warning: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFA500")),
		Error: lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FF0000")),
	}
}

// DashboardStyles contains style definitions
type DashboardStyles struct {
	Border      lipgloss.Border
	BorderColor lipgloss.Color
	Title       lipgloss.Style
	Value       lipgloss.Style
	Label       lipgloss.Style
	Success     lipgloss.Style
	Warning     lipgloss.Style
	Error       lipgloss.Style
}
