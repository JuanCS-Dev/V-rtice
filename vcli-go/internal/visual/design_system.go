package visual

// Design System - Minimalist Color Palette
// Based on benchmark analysis: gemini-cli, VSCode CLI, Claude Code
// Date: 2025-10-07

import (
	"github.com/charmbracelet/lipgloss"
)

// Core Colors (4 Primary)
const (
	// ColorPrimary - Actions, selections, interactive elements
	// Used in: Selected dropdown items, active borders, links
	ColorPrimary = "#00D9FF" // Cyan

	// ColorSecondary - Main text, primary content
	// Used in: Command text, output, body text
	ColorSecondary = "#FFFFFF" // White

	// ColorMuted - Hints, metadata, secondary information
	// Used in: Placeholders, help text, timestamps
	ColorMuted = "#6C6C6C" // DarkGray

	// ColorDanger - Errors only
	// Used in: Error messages, failed states
	ColorDanger = "#FF5555" // Red
)

// Semantic Colors (2 Additional)
const (
	// ColorSuccess - Success states
	// Used in: Completion messages, success indicators
	ColorSuccess = "#50FA7B" // Green

	// ColorWarning - Warnings
	// Used in: Warning messages, caution states
	ColorWarning = "#FFB86C" // Yellow
)

// Background Colors
const (
	ColorBgPrimary   = "#000000" // Black - Main background
	ColorBgSecondary = "#1A1A1A" // Darker - Elevated surfaces
)

// Spacing Grid (Character-based for terminal)
const (
	SpaceXS = 1  // 1 char  - Tight spacing
	SpaceS  = 2  // 2 chars - Small padding
	SpaceM  = 3  // 3 chars - Medium padding
	SpaceL  = 4  // 4 chars - Large padding
	SpaceXL = 6  // 6 chars - Extra large padding
)

// Layout Constants
const (
	// WidthStandard - Standard box width (80 - 2 for borders)
	WidthStandard = 78

	// WidthWide - Wide box width (120 - 2 for borders)
	WidthWide = 118

	// MaxSuggestionsVisible - Maximum dropdown items visible
	MaxSuggestionsVisible = 10
)

// Lipgloss Styles - Pre-configured

var (
	// StylePrimary - Primary action style (cyan)
	StylePrimary = lipgloss.NewStyle().
			Foreground(lipgloss.Color(ColorPrimary)).
			Bold(true)

	// StyleSecondary - Normal text style (white)
	StyleSecondary = lipgloss.NewStyle().
			Foreground(lipgloss.Color(ColorSecondary))

	// StyleMuted - Muted text style (gray)
	StyleMuted = lipgloss.NewStyle().
			Foreground(lipgloss.Color(ColorMuted))

	// StyleDanger - Error style (red)
	StyleDanger = lipgloss.NewStyle().
			Foreground(lipgloss.Color(ColorDanger)).
			Bold(true)

	// StyleSuccess - Success style (green)
	StyleSuccess = lipgloss.NewStyle().
			Foreground(lipgloss.Color(ColorSuccess)).
			Bold(true)

	// StyleWarning - Warning style (yellow)
	StyleWarning = lipgloss.NewStyle().
			Foreground(lipgloss.Color(ColorWarning)).
			Bold(true)

	// StyleBox - Standard box with rounded borders
	StyleBox = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color(ColorPrimary)).
			Padding(0, SpaceS).
			Width(WidthStandard)

	// StyleBoxCompact - Compact box (no padding)
	StyleBoxCompact = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color(ColorPrimary)).
			Width(WidthStandard)

	// StyleSelected - Selected item in dropdown (cyan background)
	StyleSelected = lipgloss.NewStyle().
			Background(lipgloss.Color(ColorPrimary)).
			Foreground(lipgloss.Color("#000000")). // Black text on cyan
			Bold(true)

	// StyleUnselected - Unselected dropdown item
	StyleUnselected = lipgloss.NewStyle().
			Foreground(lipgloss.Color(ColorSecondary))
)

// Border Styles
var (
	// BorderRounded - Rounded corners (╭─╮ │ ╰─╯)
	BorderRounded = lipgloss.RoundedBorder()

	// BorderNormal - Normal corners (┌─┐ │ └─┘)
	BorderNormal = lipgloss.NormalBorder()

	// BorderDouble - Double line (╔═╗ ║ ╚═╝)
	BorderDouble = lipgloss.DoubleBorder()

	// BorderThick - Thick line (┏━┓ ┃ ┗━┛)
	BorderThick = lipgloss.ThickBorder()
)

// Helper Functions

// Render renders text with primary style
func RenderPrimary(text string) string {
	return StylePrimary.Render(text)
}

// RenderSecondary renders text with secondary style
func RenderSecondary(text string) string {
	return StyleSecondary.Render(text)
}

// RenderMuted renders text with muted style
func RenderMuted(text string) string {
	return StyleMuted.Render(text)
}

// RenderDanger renders text with danger style
func RenderDanger(text string) string {
	return StyleDanger.Render(text)
}

// RenderSuccess renders text with success style
func RenderSuccess(text string) string {
	return StyleSuccess.Render(text)
}

// RenderWarning renders text with warning style
func RenderWarning(text string) string {
	return StyleWarning.Render(text)
}

// RenderBox renders content in a standard box
func RenderBox(title, content string) string {
	if title != "" {
		return StyleBox.
			BorderTop(true).
			BorderLeft(true).
			BorderRight(true).
			BorderBottom(true).
			Render(content)
	}
	return StyleBox.Render(content)
}

// RenderBoxCompact renders content in a compact box
func RenderBoxCompact(content string) string {
	return StyleBoxCompact.Render(content)
}

// Icons - Minimal set (matching benchmark anti-patterns: max 2-3 types)
const (
	IconSuccess = "✓" // Success checkmark
	IconError   = "✗" // Error cross
	IconWarning = "⚠" // Warning triangle
)

// Spinner Frames - Braille dots (gemini-cli pattern)
var SpinnerFrames = []string{
	"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏",
}

// SpinnerInterval - 120ms per frame (benchmark consensus)
const SpinnerInterval = 120
