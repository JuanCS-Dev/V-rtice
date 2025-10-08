package components

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// StatusItem represents a single item in the statusline
type StatusItem struct {
	Label string
	Value string
	Icon  string
}

// Statusline displays context information at the top of the shell
type Statusline struct {
	Items      []StatusItem
	Width      int
	Background string
	Foreground string
}

// NewStatusline creates a new statusline
func NewStatusline(width int) *Statusline {
	return &Statusline{
		Items:      make([]StatusItem, 0),
		Width:      width,
		Background: visual.ColorMuted,
		Foreground: visual.ColorSecondary,
	}
}

// AddItem adds an item to the statusline
func (s *Statusline) AddItem(label, value, icon string) *Statusline {
	s.Items = append(s.Items, StatusItem{
		Label: label,
		Value: value,
		Icon:  icon,
	})
	return s
}

// WithBackground sets background color
func (s *Statusline) WithBackground(color string) *Statusline {
	s.Background = color
	return s
}

// WithForeground sets foreground color
func (s *Statusline) WithForeground(color string) *Statusline {
	s.Foreground = color
	return s
}

// Render renders the statusline
func (s *Statusline) Render() string {
	if len(s.Items) == 0 {
		return ""
	}

	// Styles
	labelStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(visual.ColorMuted)).
		Bold(false)

	valueStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(visual.ColorPrimary)).
		Bold(true)

	separatorStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(visual.ColorMuted))

	// Build items
	var parts []string
	for _, item := range s.Items {
		var part string
		if item.Icon != "" {
			part = fmt.Sprintf("%s %s %s",
				item.Icon,
				labelStyle.Render(item.Label+":"),
				valueStyle.Render(item.Value))
		} else {
			part = fmt.Sprintf("%s %s",
				labelStyle.Render(item.Label+":"),
				valueStyle.Render(item.Value))
		}
		parts = append(parts, part)
	}

	// Join with separator
	separator := separatorStyle.Render(" │ ")
	content := strings.Join(parts, separator)

	// Calculate padding
	contentWidth := lipgloss.Width(content)
	paddingNeeded := s.Width - contentWidth - 4 // 4 for borders

	if paddingNeeded < 0 {
		paddingNeeded = 0
	}

	// Add padding to center or left-align
	padding := strings.Repeat(" ", paddingNeeded)

	// Create box
	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color(visual.ColorMuted)).
		Width(s.Width - 2) // Subtract 2 for borders

	return boxStyle.Render(content + padding)
}

// RenderCompact renders a compact version without box
func (s *Statusline) RenderCompact() string {
	if len(s.Items) == 0 {
		return ""
	}

	labelStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(visual.ColorMuted))

	valueStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(visual.ColorPrimary)).
		Bold(true)

	separatorStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(visual.ColorMuted))

	var parts []string
	for _, item := range s.Items {
		var part string
		if item.Icon != "" {
			part = fmt.Sprintf("%s %s %s",
				item.Icon,
				labelStyle.Render(item.Label+":"),
				valueStyle.Render(item.Value))
		} else {
			part = fmt.Sprintf("%s %s",
				labelStyle.Render(item.Label+":"),
				valueStyle.Render(item.Value))
		}
		parts = append(parts, part)
	}

	separator := separatorStyle.Render(" │ ")
	return strings.Join(parts, separator)
}
