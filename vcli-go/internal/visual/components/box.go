package components

import (
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Box represents a bordered container component
type Box struct {
	Title       string
	Content     string
	Width       int
	Border      lipgloss.Border
	BorderColor string
	TitleAlign  lipgloss.Position
}

// NewBox creates a standard box with defaults
func NewBox(content string) *Box {
	return &Box{
		Content:     content,
		Width:       visual.WidthStandard,
		Border:      visual.BorderRounded,
		BorderColor: visual.ColorPrimary,
		TitleAlign:  lipgloss.Left,
	}
}

// NewBoxWithTitle creates a box with a title
func NewBoxWithTitle(title, content string) *Box {
	return &Box{
		Title:       title,
		Content:     content,
		Width:       visual.WidthStandard,
		Border:      visual.BorderRounded,
		BorderColor: visual.ColorPrimary,
		TitleAlign:  lipgloss.Left,
	}
}

// WithWidth sets custom width
func (b *Box) WithWidth(width int) *Box {
	b.Width = width
	return b
}

// WithBorder sets custom border style
func (b *Box) WithBorder(border lipgloss.Border) *Box {
	b.Border = border
	return b
}

// WithBorderColor sets border color
func (b *Box) WithBorderColor(color string) *Box {
	b.BorderColor = color
	return b
}

// WithTitleAlign sets title alignment
func (b *Box) WithTitleAlign(align lipgloss.Position) *Box {
	b.TitleAlign = align
	return b
}

// Render renders the box to string
func (b *Box) Render() string {
	style := lipgloss.NewStyle().
		Border(b.Border).
		BorderForeground(lipgloss.Color(b.BorderColor)).
		Width(b.Width - 2) // Subtract 2 for borders

	// If title exists, render with title
	if b.Title != "" {
		titleStyle := lipgloss.NewStyle().
			Foreground(lipgloss.Color(b.BorderColor)).
			Bold(true)

		renderedTitle := titleStyle.Render(b.Title)

		// Create top border with embedded title
		return b.renderWithTitle(style, renderedTitle)
	}

	// No title - simple box
	return style.Render(b.Content)
}

// renderWithTitle creates box with title in top border
func (b *Box) renderWithTitle(style lipgloss.Style, title string) string {
	// Render box without title first
	boxContent := style.Render(b.Content)

	// Split into lines
	lines := strings.Split(boxContent, "\n")
	if len(lines) < 1 {
		return boxContent
	}

	// Get border characters
	var cornerLeft, cornerRight, horizontal string
	if b.Border == visual.BorderRounded {
		cornerLeft, cornerRight, horizontal = "╭", "╮", "─"
	} else if b.Border == visual.BorderNormal {
		cornerLeft, cornerRight, horizontal = "┌", "┐", "─"
	} else if b.Border == visual.BorderDouble {
		cornerLeft, cornerRight, horizontal = "╔", "╗", "═"
	} else { // Thick
		cornerLeft, cornerRight, horizontal = "┏", "┓", "━"
	}

	// Build new top border with title
	remainingWidth := b.Width - lipgloss.Width(title) - 4
	leftPad := strings.Repeat(horizontal, 1)
	rightPad := strings.Repeat(horizontal, remainingWidth)

	colorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(b.BorderColor))
	titleColorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(b.BorderColor)).Bold(true)

	newTopBorder := colorStyle.Render(cornerLeft+leftPad) +
		titleColorStyle.Render(title) +
		colorStyle.Render(rightPad+cornerRight)

	lines[0] = newTopBorder

	return strings.Join(lines, "\n")
}

// RenderCompact renders box with no internal padding
func (b *Box) RenderCompact() string {
	style := lipgloss.NewStyle().
		Border(b.Border).
		BorderForeground(lipgloss.Color(b.BorderColor)).
		Width(b.Width - 2). // Subtract 2 for borders
		Padding(0)          // No padding

	return style.Render(b.Content)
}
