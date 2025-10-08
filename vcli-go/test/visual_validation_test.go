package test

import (
	"strings"
	"testing"

	"github.com/verticedev/vcli-go/internal/visual/banner"
)

// TestBannerAlignment validates banner is perfectly aligned
func TestBannerAlignment(t *testing.T) {
	renderer := banner.NewBannerRenderer()
	output := renderer.RenderCompact("2.0.0", "2025-10-07")

	lines := strings.Split(output, "\n")

	// Banner has 6 ASCII lines + 1 empty + 1 author = 8 lines minimum
	if len(lines) < 8 {
		t.Errorf("Banner should have at least 8 lines, got %d", len(lines))
	}

	// Find ASCII art lines (those with box drawing chars)
	asciiLines := []string{}
	for _, line := range lines {
		if strings.Contains(line, "██") || strings.Contains(line, "╚") || strings.Contains(line, "╗") {
			asciiLines = append(asciiLines, line)
		}
	}

	if len(asciiLines) != 6 {
		t.Errorf("Banner should have exactly 6 ASCII art lines, got %d", len(asciiLines))
	}

	// Validate all ASCII lines have same visible width (ignoring ANSI codes)
	expectedWidth := 56 // From design: 56 chars each line
	for i, line := range asciiLines {
		// Strip ANSI color codes for width calculation
		stripped := stripANSI(line)
		// Remove leading/trailing spaces from check
		stripped = strings.TrimSpace(stripped)

		visibleWidth := len([]rune(stripped))

		// Allow some tolerance for trimming
		if visibleWidth < expectedWidth-2 || visibleWidth > expectedWidth+2 {
			t.Errorf("Line %d has width %d, expected ~%d chars: %q",
				i+1, visibleWidth, expectedWidth, stripped)
		}
	}

	// Validate centering (check for leading spaces)
	expectedPadding := (80 - 56) / 2 // Should be 12 spaces
	for i, line := range asciiLines {
		leadingSpaces := 0
		for _, ch := range line {
			if ch == ' ' {
				leadingSpaces++
			} else {
				break
			}
		}

		// Check padding is approximately correct
		if leadingSpaces < expectedPadding-2 || leadingSpaces > expectedPadding+2 {
			t.Errorf("Line %d has %d leading spaces, expected ~%d",
				i+1, leadingSpaces, expectedPadding)
		}
	}
}

// TestBannerNoTODOs validates banner code has no TODOs
func TestBannerNoTODOs(t *testing.T) {
	renderer := banner.NewBannerRenderer()
	output := renderer.RenderCompact("2.0.0", "2025-10-07")

	if strings.Contains(output, "TODO") || strings.Contains(output, "FIXME") {
		t.Error("Banner output contains TODO or FIXME markers")
	}
}

// TestAuthorshipPresent validates authorship is displayed
func TestAuthorshipPresent(t *testing.T) {
	renderer := banner.NewBannerRenderer()
	output := renderer.RenderCompact("2.0.0", "2025-10-07")

	if !strings.Contains(output, "Juan Carlos") || !strings.Contains(output, "Anthropic Claude") {
		t.Error("Banner must display authorship: 'Juan Carlos e Anthropic Claude'")
	}
}

// stripANSI removes ANSI color codes from string for width calculation
func stripANSI(s string) string {
	// Simple ANSI stripper - removes escape sequences
	result := ""
	inEscape := false

	for _, ch := range s {
		if ch == '\033' {
			inEscape = true
			continue
		}

		if inEscape {
			if ch == 'm' {
				inEscape = false
			}
			continue
		}

		result += string(ch)
	}

	return result
}
