package visual

import (
	"fmt"
	"math"

	"github.com/charmbracelet/lipgloss"
)

// RGBColor represents a color in RGB space
type RGBColor struct {
	R, G, B uint8
}

// ParseHex converts a hex color string to RGBColor
// Supports formats: "#RRGGBB" or "RRGGBB"
func ParseHex(hex string) RGBColor {
	if len(hex) > 0 && hex[0] == '#' {
		hex = hex[1:]
	}

	var r, g, b uint8
	fmt.Sscanf(hex, "%02x%02x%02x", &r, &g, &b)

	return RGBColor{R: r, G: g, B: b}
}

// ToHex converts RGBColor to hex string
func (c RGBColor) ToHex() string {
	return fmt.Sprintf("#%02x%02x%02x", c.R, c.G, c.B)
}

// ToTermenv converts RGBColor to lipgloss.Color (compatible with termenv)
func (c RGBColor) ToTermenv() lipgloss.Color {
	return lipgloss.Color(fmt.Sprintf("#%02x%02x%02x", c.R, c.G, c.B))
}

// Interpolate smoothly transitions between two colors
// factor should be between 0.0 (color1) and 1.0 (color2)
func Interpolate(c1, c2 RGBColor, factor float64) RGBColor {
	// Clamp factor to [0, 1]
	factor = math.Max(0, math.Min(1, factor))

	r := uint8(float64(c1.R) + (float64(c2.R)-float64(c1.R))*factor)
	g := uint8(float64(c1.G) + (float64(c2.G)-float64(c1.G))*factor)
	b := uint8(float64(c1.B) + (float64(c2.B)-float64(c1.B))*factor)

	return RGBColor{R: r, G: g, B: b}
}

// InterpolateMultiple transitions through multiple colors
// position should be between 0.0 and 1.0
func InterpolateMultiple(colors []RGBColor, position float64) RGBColor {
	if len(colors) == 0 {
		return RGBColor{R: 255, G: 255, B: 255} // Default to white
	}
	if len(colors) == 1 {
		return colors[0]
	}

	// Clamp position to [0, 1]
	position = math.Max(0, math.Min(1, position))

	// Calculate which color segment we're in
	numSegments := len(colors) - 1
	segmentSize := 1.0 / float64(numSegments)
	segmentIndex := int(position / segmentSize)

	// Handle edge case: position = 1.0
	if segmentIndex >= numSegments {
		return colors[len(colors)-1]
	}

	// Calculate local position within segment
	localPosition := (position - float64(segmentIndex)*segmentSize) / segmentSize

	return Interpolate(colors[segmentIndex], colors[segmentIndex+1], localPosition)
}

// Distance calculates the perceptual distance between two colors
// Uses simple Euclidean distance in RGB space
func Distance(c1, c2 RGBColor) float64 {
	dr := float64(c1.R) - float64(c2.R)
	dg := float64(c1.G) - float64(c2.G)
	db := float64(c1.B) - float64(c2.B)

	return math.Sqrt(dr*dr + dg*dg + db*db)
}

// Lighten increases the brightness of a color
func (c RGBColor) Lighten(amount float64) RGBColor {
	amount = math.Max(0, math.Min(1, amount))

	r := uint8(math.Min(255, float64(c.R)+(255-float64(c.R))*amount))
	g := uint8(math.Min(255, float64(c.G)+(255-float64(c.G))*amount))
	b := uint8(math.Min(255, float64(c.B)+(255-float64(c.B))*amount))

	return RGBColor{R: r, G: g, B: b}
}

// Darken decreases the brightness of a color
func (c RGBColor) Darken(amount float64) RGBColor {
	amount = math.Max(0, math.Min(1, amount))

	r := uint8(float64(c.R) * (1 - amount))
	g := uint8(float64(c.G) * (1 - amount))
	b := uint8(float64(c.B) * (1 - amount))

	return RGBColor{R: r, G: g, B: b}
}
