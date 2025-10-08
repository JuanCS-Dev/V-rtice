package visual

import (
	"strings"

	"github.com/charmbracelet/lipgloss"
)

// GradientText applies a smooth color gradient to text
// Colors are interpolated across the length of the text
func GradientText(text string, colors []RGBColor) string {
	if len(text) == 0 {
		return ""
	}

	if len(colors) == 0 {
		return text
	}

	if len(colors) == 1 {
		// Single color - just apply it
		style := lipgloss.NewStyle().Foreground(colors[0].ToTermenv())
		return style.Render(text)
	}

	var result strings.Builder
	textLen := len(text)

	for i, char := range text {
		// Calculate position in gradient (0.0 to 1.0)
		position := float64(i) / float64(textLen-1)
		if textLen == 1 {
			position = 0.0
		}

		// Get interpolated color at this position
		color := InterpolateMultiple(colors, position)

		// Apply color to character
		style := lipgloss.NewStyle().Foreground(color.ToTermenv())
		result.WriteString(style.Render(string(char)))
	}

	return result.String()
}

// GradientTextMultiline applies gradient to multi-line text
// Each line gets the gradient applied independently
func GradientTextMultiline(text string, colors []RGBColor) string {
	lines := strings.Split(text, "\n")
	var result strings.Builder

	for i, line := range lines {
		if i > 0 {
			result.WriteString("\n")
		}
		result.WriteString(GradientText(line, colors))
	}

	return result.String()
}

// GradientTextVertical applies gradient vertically across lines
// The gradient transitions from first line to last line
func GradientTextVertical(text string, colors []RGBColor) string {
	lines := strings.Split(text, "\n")
	numLines := len(lines)

	if numLines == 0 {
		return ""
	}

	var result strings.Builder

	for i, line := range lines {
		// Calculate position for this line
		position := float64(i) / float64(numLines-1)
		if numLines == 1 {
			position = 0.0
		}

		// Get color for this line
		color := InterpolateMultiple(colors, position)

		// Apply color to entire line
		style := lipgloss.NewStyle().Foreground(color.ToTermenv())
		if i > 0 {
			result.WriteString("\n")
		}
		result.WriteString(style.Render(line))
	}

	return result.String()
}

// GradientBlock creates a gradient text block with consistent color per line
// Useful for large ASCII art where each line should have uniform color
func GradientBlock(lines []string, colors []RGBColor) string {
	if len(lines) == 0 {
		return ""
	}

	numLines := len(lines)
	var result strings.Builder

	for i, line := range lines {
		// Calculate position for this line
		position := float64(i) / float64(numLines-1)
		if numLines == 1 {
			position = 0.0
		}

		// Get color for this line
		color := InterpolateMultiple(colors, position)

		// Apply color to entire line
		style := lipgloss.NewStyle().Foreground(color.ToTermenv())
		if i > 0 {
			result.WriteString("\n")
		}
		result.WriteString(style.Render(line))
	}

	return result.String()
}

// RainbowText creates rainbow gradient effect
func RainbowText(text string) string {
	rainbow := []RGBColor{
		ParseHex("#FF0000"), // Red
		ParseHex("#FF7F00"), // Orange
		ParseHex("#FFFF00"), // Yellow
		ParseHex("#00FF00"), // Green
		ParseHex("#0000FF"), // Blue
		ParseHex("#4B0082"), // Indigo
		ParseHex("#9400D3"), // Violet
	}

	return GradientText(text, rainbow)
}

// HorizontalGradientBar creates a horizontal gradient bar
// Useful for progress bars or visual separators
func HorizontalGradientBar(width int, colors []RGBColor, char rune) string {
	if width <= 0 {
		return ""
	}

	text := strings.Repeat(string(char), width)
	return GradientText(text, colors)
}
