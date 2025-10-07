package visual

import "github.com/charmbracelet/lipgloss"

// VerticePalette defines the official Vértice color scheme
type VerticePalette struct {
	// Primary gradient colors (Green → Cyan → Blue)
	Green     RGBColor
	Cyan      RGBColor
	Blue      RGBColor
	DeepBlue  RGBColor

	// Semantic colors
	Success   RGBColor
	Warning   RGBColor
	Error     RGBColor
	Info      RGBColor

	// Accent colors
	Accent    RGBColor
	Secondary RGBColor

	// Neutral colors
	White     RGBColor
	Gray      RGBColor
	DarkGray  RGBColor
}

// DefaultPalette returns the default Vértice color palette
func DefaultPalette() *VerticePalette {
	return &VerticePalette{
		// Primary gradient: Green → Cyan → Blue (from original vCLI)
		Green:     ParseHex("#00ff87"), // Bright green
		Cyan:      ParseHex("#00d4ff"), // Bright cyan
		Blue:      ParseHex("#0080ff"), // Blue
		DeepBlue:  ParseHex("#0040ff"), // Deep blue

		// Semantic colors
		Success:   ParseHex("#00ff87"), // Green
		Warning:   ParseHex("#ffaa00"), // Orange
		Error:     ParseHex("#ff0055"), // Red
		Info:      ParseHex("#00d4ff"), // Cyan

		// Accents
		Accent:    ParseHex("#00d4ff"), // Cyan
		Secondary: ParseHex("#8800ff"), // Purple

		// Neutrals
		White:     ParseHex("#ffffff"),
		Gray:      ParseHex("#888888"),
		DarkGray:  ParseHex("#444444"),
	}
}

// PrimaryGradient returns the signature Vértice gradient colors
func (p *VerticePalette) PrimaryGradient() []RGBColor {
	return []RGBColor{p.Green, p.Cyan, p.Blue}
}

// ExtendedGradient returns an extended gradient with deep blue
func (p *VerticePalette) ExtendedGradient() []RGBColor {
	return []RGBColor{p.Green, p.Cyan, p.Blue, p.DeepBlue}
}

// GetStyle returns a lipgloss style with the specified color
func (p *VerticePalette) GetStyle(color RGBColor) lipgloss.Style {
	return lipgloss.NewStyle().Foreground(color.ToTermenv())
}

// Styles provides common pre-configured styles
type Styles struct {
	Success   lipgloss.Style
	Warning   lipgloss.Style
	Error     lipgloss.Style
	Info      lipgloss.Style
	Accent    lipgloss.Style
	Secondary lipgloss.Style
	Muted     lipgloss.Style
	Bold      lipgloss.Style
}

// DefaultStyles returns a set of pre-configured styles
func DefaultStyles() *Styles {
	palette := DefaultPalette()

	return &Styles{
		Success:   lipgloss.NewStyle().Foreground(palette.Success.ToTermenv()),
		Warning:   lipgloss.NewStyle().Foreground(palette.Warning.ToTermenv()),
		Error:     lipgloss.NewStyle().Foreground(palette.Error.ToTermenv()),
		Info:      lipgloss.NewStyle().Foreground(palette.Info.ToTermenv()),
		Accent:    lipgloss.NewStyle().Foreground(palette.Accent.ToTermenv()),
		Secondary: lipgloss.NewStyle().Foreground(palette.Secondary.ToTermenv()),
		Muted:     lipgloss.NewStyle().Foreground(palette.Gray.ToTermenv()),
		Bold:      lipgloss.NewStyle().Bold(true),
	}
}

// Icon provides commonly used icons with colors
type Icon struct {
	Success string
	Warning string
	Error   string
	Info    string
	Rocket  string
	Fire    string
	Star    string
	Check   string
	Cross   string
	Arrow   string
	Bullet  string
}

// DefaultIcons returns the default icon set
func DefaultIcons() *Icon {
	styles := DefaultStyles()

	return &Icon{
		Success: styles.Success.Render("✅"),
		Warning: styles.Warning.Render("⚠️"),
		Error:   styles.Error.Render("❌"),
		Info:    styles.Info.Render("ℹ️"),
		Rocket:  styles.Accent.Render("🚀"),
		Fire:    styles.Error.Render("🔥"),
		Star:    styles.Warning.Render("⭐"),
		Check:   styles.Success.Render("✓"),
		Cross:   styles.Error.Render("✗"),
		Arrow:   styles.Accent.Render("→"),
		Bullet:  styles.Accent.Render("•"),
	}
}

// BoxStyles provides pre-configured box/border styles
type BoxStyles struct {
	Primary   lipgloss.Style
	Secondary lipgloss.Style
	Success   lipgloss.Style
	Warning   lipgloss.Style
	Error     lipgloss.Style
}

// DefaultBoxStyles returns pre-configured box styles
func DefaultBoxStyles() *BoxStyles {
	palette := DefaultPalette()

	primary := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(palette.Cyan.ToTermenv()).
		Padding(1, 2)

	secondary := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(palette.Blue.ToTermenv()).
		Padding(1, 2)

	success := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(palette.Success.ToTermenv()).
		Padding(1, 2)

	warning := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(palette.Warning.ToTermenv()).
		Padding(1, 2)

	errorStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(palette.Error.ToTermenv()).
		Padding(1, 2)

	return &BoxStyles{
		Primary:   primary,
		Secondary: secondary,
		Success:   success,
		Warning:   warning,
		Error:     errorStyle,
	}
}
