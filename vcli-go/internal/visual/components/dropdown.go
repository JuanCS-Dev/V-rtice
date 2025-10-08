package components

import (
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// DropdownItem represents a single item in dropdown
type DropdownItem struct {
	Text        string
	Description string
}

// Dropdown represents an autocomplete dropdown component
type Dropdown struct {
	Items       []DropdownItem
	Selected    int
	MaxVisible  int
	Width       int
	Border      lipgloss.Border
	BorderColor string
}

// NewDropdown creates a new dropdown
func NewDropdown(items []DropdownItem) *Dropdown {
	return &Dropdown{
		Items:       items,
		Selected:    0,
		MaxVisible:  visual.MaxSuggestionsVisible,
		Width:       visual.WidthStandard,
		Border:      visual.BorderNormal,
		BorderColor: visual.ColorPrimary,
	}
}

// WithSelected sets the selected index
func (d *Dropdown) WithSelected(index int) *Dropdown {
	if index >= 0 && index < len(d.Items) {
		d.Selected = index
	}
	return d
}

// WithMaxVisible sets max visible items
func (d *Dropdown) WithMaxVisible(max int) *Dropdown {
	d.MaxVisible = max
	return d
}

// WithWidth sets dropdown width
func (d *Dropdown) WithWidth(width int) *Dropdown {
	d.Width = width
	return d
}

// Render renders the dropdown to string
func (d *Dropdown) Render() string {
	if len(d.Items) == 0 {
		return ""
	}

	// Calculate visible range
	visibleStart, visibleEnd := d.calculateVisibleRange()

	var lines []string

	// Top border
	topBorder := d.renderBorder(true)
	lines = append(lines, topBorder)

	// Render visible items
	for i := visibleStart; i < visibleEnd; i++ {
		itemLine := d.renderItem(i)
		lines = append(lines, itemLine)
	}

	// Bottom border
	bottomBorder := d.renderBorder(false)
	lines = append(lines, bottomBorder)

	return strings.Join(lines, "\n")
}

// calculateVisibleRange returns start and end indices for visible items
func (d *Dropdown) calculateVisibleRange() (int, int) {
	totalItems := len(d.Items)

	if totalItems <= d.MaxVisible {
		return 0, totalItems
	}

	// Scroll window around selected item
	start := d.Selected - (d.MaxVisible / 2)
	if start < 0 {
		start = 0
	}

	end := start + d.MaxVisible
	if end > totalItems {
		end = totalItems
		start = end - d.MaxVisible
		if start < 0 {
			start = 0
		}
	}

	return start, end
}

// renderBorder renders top or bottom border
func (d *Dropdown) renderBorder(isTop bool) string {
	var cornerLeft, cornerRight, horizontal string

	if d.Border == visual.BorderRounded {
		if isTop {
			cornerLeft, cornerRight, horizontal = "╭", "╮", "─"
		} else {
			cornerLeft, cornerRight, horizontal = "╰", "╯", "─"
		}
	} else if d.Border == visual.BorderNormal {
		if isTop {
			cornerLeft, cornerRight, horizontal = "┌", "┐", "─"
		} else {
			cornerLeft, cornerRight, horizontal = "└", "┘", "─"
		}
	} else if d.Border == visual.BorderDouble {
		if isTop {
			cornerLeft, cornerRight, horizontal = "╔", "╗", "═"
		} else {
			cornerLeft, cornerRight, horizontal = "╚", "╝", "═"
		}
	} else { // Thick
		if isTop {
			cornerLeft, cornerRight, horizontal = "┏", "┓", "━"
		} else {
			cornerLeft, cornerRight, horizontal = "┗", "┛", "━"
		}
	}

	line := strings.Repeat(horizontal, d.Width-2)
	colorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(d.BorderColor))

	return colorStyle.Render(cornerLeft + line + cornerRight)
}

// renderItem renders a single dropdown item
func (d *Dropdown) renderItem(index int) string {
	if index < 0 || index >= len(d.Items) {
		return ""
	}

	item := d.Items[index]
	isSelected := index == d.Selected

	// Border vertical char
	var verticalChar string
	if d.Border == visual.BorderDouble {
		verticalChar = "║"
	} else if d.Border == visual.BorderThick {
		verticalChar = "┃"
	} else {
		verticalChar = "│"
	}

	borderStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(d.BorderColor))
	leftBorder := borderStyle.Render(verticalChar)
	rightBorder := borderStyle.Render(verticalChar)

	// Content width (subtract 2 for borders, 2 for padding)
	contentWidth := d.Width - 4

	// Calculate text and description widths
	// Reserve space for description (right-aligned)
	descWidth := lipgloss.Width(item.Description)
	textWidth := contentWidth - descWidth - 3 // 3 spaces between text and description

	if textWidth < 10 {
		textWidth = contentWidth - 3
		descWidth = 0
	}

	// Truncate or pad text
	displayText := item.Text
	if lipgloss.Width(displayText) > textWidth {
		displayText = displayText[:textWidth-3] + "..."
	} else {
		displayText = lipgloss.PlaceHorizontal(textWidth, lipgloss.Left, displayText)
	}

	// Format description (right-aligned)
	displayDesc := ""
	if descWidth > 0 && item.Description != "" {
		displayDesc = lipgloss.PlaceHorizontal(descWidth, lipgloss.Right, item.Description)
	}

	// Combine text and description
	var content string
	if displayDesc != "" {
		content = displayText + "   " + displayDesc
	} else {
		content = displayText
	}

	// Pad to full width
	content = lipgloss.PlaceHorizontal(contentWidth, lipgloss.Left, content)

	// Apply selection styling
	var styledContent string
	if isSelected {
		styledContent = visual.StyleSelected.Render(" " + content + " ")
	} else {
		styledContent = visual.StyleUnselected.Render(" " + content + " ")
	}

	return leftBorder + styledContent + rightBorder
}

// RenderMinimal renders dropdown without borders (gemini-cli style)
func (d *Dropdown) RenderMinimal() string {
	if len(d.Items) == 0 {
		return ""
	}

	visibleStart, visibleEnd := d.calculateVisibleRange()
	var lines []string

	for i := visibleStart; i < visibleEnd; i++ {
		item := d.Items[i]
		isSelected := i == d.Selected

		// Calculate widths
		contentWidth := d.Width - 2 // 2 for padding
		descWidth := lipgloss.Width(item.Description)
		textWidth := contentWidth - descWidth - 3

		if textWidth < 10 {
			textWidth = contentWidth - 3
			descWidth = 0
		}

		// Format components
		displayText := item.Text
		if lipgloss.Width(displayText) > textWidth {
			displayText = displayText[:textWidth-3] + "..."
		} else {
			displayText = lipgloss.PlaceHorizontal(textWidth, lipgloss.Left, displayText)
		}

		displayDesc := ""
		if descWidth > 0 && item.Description != "" {
			displayDesc = lipgloss.PlaceHorizontal(descWidth, lipgloss.Right, item.Description)
		}

		var content string
		if displayDesc != "" {
			content = displayText + "   " + displayDesc
		} else {
			content = displayText
		}

		content = lipgloss.PlaceHorizontal(contentWidth, lipgloss.Left, content)

		// Apply styling
		var line string
		if isSelected {
			line = visual.StyleSelected.Render(" " + content + " ")
		} else {
			line = visual.StyleUnselected.Render(" " + content + " ")
		}

		lines = append(lines, line)
	}

	return strings.Join(lines, "\n")
}
