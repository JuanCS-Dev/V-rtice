package dashboard

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// NewLayout creates a new layout manager
func NewLayout(layoutType LayoutType, rows, cols int) *Layout {
	return &Layout{
		Type:       layoutType,
		Rows:       rows,
		Cols:       cols,
		Dashboards: make([]Dashboard, 0),
	}
}

// AddDashboard adds a dashboard to the layout
func (l *Layout) AddDashboard(d Dashboard) {
	l.Dashboards = append(l.Dashboards, d)
}

// Init initializes all dashboards
func (l *Layout) Init() tea.Cmd {
	cmds := make([]tea.Cmd, len(l.Dashboards))
	for i, d := range l.Dashboards {
		cmds[i] = d.Init()
	}
	return tea.Batch(cmds...)
}

// Update updates all dashboards
func (l *Layout) Update(msg tea.Msg) (*Layout, tea.Cmd) {
	cmds := make([]tea.Cmd, 0)

	for i, d := range l.Dashboards {
		updated, cmd := d.Update(msg)
		l.Dashboards[i] = updated
		if cmd != nil {
			cmds = append(cmds, cmd)
		}
	}

	return l, tea.Batch(cmds...)
}

// Resize resizes the layout and all dashboards
func (l *Layout) Resize(width, height int) {
	l.Width = width
	l.Height = height

	switch l.Type {
	case LayoutTypeGrid:
		l.resizeGrid(width, height)
	case LayoutTypeStack:
		l.resizeStack(width, height)
	case LayoutTypeSplit:
		l.resizeSplit(width, height)
	}
}

// resizeGrid resizes dashboards in grid layout
func (l *Layout) resizeGrid(width, height int) {
	if len(l.Dashboards) == 0 {
		return
	}

	dashWidth := width / l.Cols
	dashHeight := height / l.Rows

	for _, d := range l.Dashboards {
		d.Resize(dashWidth-2, dashHeight-2) // -2 for borders
	}
}

// resizeStack resizes dashboards in stack layout
func (l *Layout) resizeStack(width, height int) {
	if len(l.Dashboards) == 0 {
		return
	}

	dashHeight := height / len(l.Dashboards)

	for _, d := range l.Dashboards {
		d.Resize(width-2, dashHeight-2)
	}
}

// resizeSplit resizes dashboards in split layout
func (l *Layout) resizeSplit(width, height int) {
	if len(l.Dashboards) == 0 {
		return
	}

	dashWidth := width / len(l.Dashboards)

	for _, d := range l.Dashboards {
		d.Resize(dashWidth-2, height-2)
	}
}

// View renders the layout
func (l *Layout) View() string {
	if len(l.Dashboards) == 0 {
		return "No dashboards"
	}

	switch l.Type {
	case LayoutTypeGrid:
		return l.viewGrid()
	case LayoutTypeStack:
		return l.viewStack()
	case LayoutTypeSplit:
		return l.viewSplit()
	default:
		return l.viewGrid()
	}
}

// viewGrid renders grid layout
func (l *Layout) viewGrid() string {
	rows := make([]string, 0)

	for row := 0; row < l.Rows; row++ {
		cols := make([]string, 0)
		for col := 0; col < l.Cols; col++ {
			idx := row*l.Cols + col
			if idx < len(l.Dashboards) {
				cols = append(cols, l.Dashboards[idx].View())
			}
		}
		if len(cols) > 0 {
			rows = append(rows, lipgloss.JoinHorizontal(lipgloss.Top, cols...))
		}
	}

	return lipgloss.JoinVertical(lipgloss.Left, rows...)
}

// viewStack renders stack layout (vertical)
func (l *Layout) viewStack() string {
	views := make([]string, len(l.Dashboards))
	for i, d := range l.Dashboards {
		views[i] = d.View()
	}
	return lipgloss.JoinVertical(lipgloss.Left, views...)
}

// viewSplit renders split layout (horizontal)
func (l *Layout) viewSplit() string {
	views := make([]string, len(l.Dashboards))
	for i, d := range l.Dashboards {
		views[i] = d.View()
	}
	return lipgloss.JoinHorizontal(lipgloss.Top, views...)
}

// renderBox renders content in a bordered box
func renderBox(title, content string, width, height int, styles DashboardStyles) string {
	titleStyle := styles.Title

	boxStyle := lipgloss.NewStyle().
		Border(styles.Border).
		BorderForeground(styles.BorderColor).
		Width(width).
		Height(height)

	titleBar := titleStyle.Render(title)

	// Calculate content height (total - title - borders)
	contentHeight := height - 3
	if contentHeight < 0 {
		contentHeight = 0
	}

	// Split content into lines and truncate if needed
	lines := strings.Split(content, "\n")
	if len(lines) > contentHeight {
		lines = lines[:contentHeight]
	}

	body := strings.Join(lines, "\n")

	return boxStyle.Render(lipgloss.JoinVertical(lipgloss.Left, titleBar, body))
}
