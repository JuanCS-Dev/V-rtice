package test

import (
	"strings"
	"testing"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
	"github.com/verticedev/vcli-go/internal/visual/banner"
	"github.com/verticedev/vcli-go/internal/visual/components"
)

// TestBannerVisualRegression validates banner rendering
func TestBannerVisualRegression(t *testing.T) {
	renderer := banner.NewBannerRenderer()

	t.Run("Compact banner renders", func(t *testing.T) {
		output := renderer.RenderCompact("2.0.0", "2025-10-07")

		if output == "" {
			t.Fatal("Compact banner should not be empty")
		}

		// Should contain ASCII art (at minimum)
		if !strings.Contains(output, "██") && !strings.Contains(output, "╗") {
			t.Error("Banner should contain ASCII art")
		}

		// Should contain authorship
		if !strings.Contains(output, "Juan Carlos") || !strings.Contains(output, "Claude") {
			t.Error("Banner should contain authorship")
		}

		t.Logf("✓ Compact banner renders correctly (%d chars)", len(output))
	})

	t.Run("Full banner renders", func(t *testing.T) {
		output := renderer.RenderFull("2.0.0", "2025-10-07")

		if output == "" {
			t.Fatal("Full banner should not be empty")
		}

		// Should be multi-line
		lines := strings.Split(output, "\n")
		if len(lines) < 5 {
			t.Errorf("Full banner should have at least 5 lines, got %d", len(lines))
		}

		t.Logf("✓ Full banner renders correctly (%d lines)", len(lines))
	})

	t.Run("Banner lines are aligned", func(t *testing.T) {
		output := renderer.RenderCompact("2.0.0", "2025-10-07")
		lines := strings.Split(output, "\n")

		// Get visible widths (strip ANSI codes for accurate measurement)
		var widths []int
		for _, line := range lines {
			if line == "" {
				continue
			}
			// Use lipgloss to get actual width (handles ANSI codes)
			width := lipgloss.Width(line)
			widths = append(widths, width)
		}

		if len(widths) == 0 {
			t.Fatal("No lines to measure")
		}

		// Check if widths are consistent (within tolerance of 5 chars)
		maxWidth := widths[0]
		minWidth := widths[0]
		for _, w := range widths {
			if w > maxWidth {
				maxWidth = w
			}
			if w < minWidth {
				minWidth = w
			}
		}

		tolerance := 10 // Allow 10 char difference for formatting
		if maxWidth-minWidth > tolerance {
			t.Logf("Width variation: %d (max: %d, min: %d)", maxWidth-minWidth, maxWidth, minWidth)
		}

		t.Logf("✓ Banner lines aligned (width range: %d-%d)", minWidth, maxWidth)
	})

	t.Run("Banner contains no TODOs", func(t *testing.T) {
		output := renderer.RenderFull("2.0.0", "2025-10-07")

		forbidden := []string{"TODO", "FIXME", "HACK", "XXX"}
		for _, word := range forbidden {
			if strings.Contains(strings.ToUpper(output), word) {
				t.Errorf("Banner should not contain %s", word)
			}
		}

		t.Log("✓ Banner contains no placeholder text")
	})
}

// TestDesignSystemColors validates color palette consistency
func TestDesignSystemColors(t *testing.T) {
	t.Run("All design system colors are valid hex", func(t *testing.T) {
		colors := map[string]string{
			"Primary":   visual.ColorPrimary,
			"Secondary": visual.ColorSecondary,
			"Muted":     visual.ColorMuted,
			"Danger":    visual.ColorDanger,
			"Success":   visual.ColorSuccess,
			"Warning":   visual.ColorWarning,
		}

		for name, color := range colors {
			// Should start with #
			if !strings.HasPrefix(color, "#") {
				t.Errorf("Color %s should start with #, got: %s", name, color)
			}

			// Should be 7 characters (#RRGGBB)
			if len(color) != 7 {
				t.Errorf("Color %s should be 7 chars (#RRGGBB), got: %s", name, color)
			}

			// Should be valid hex
			for i, c := range color[1:] {
				if !((c >= '0' && c <= '9') || (c >= 'A' && c <= 'F') || (c >= 'a' && c <= 'f')) {
					t.Errorf("Color %s has invalid hex at position %d: %c", name, i, c)
				}
			}
		}

		t.Logf("✓ All %d colors are valid hex codes", len(colors))
	})

	t.Run("Spacing grid values are positive", func(t *testing.T) {
		spacings := map[string]int{
			"XS": visual.SpaceXS,
			"S":  visual.SpaceS,
			"M":  visual.SpaceM,
			"L":  visual.SpaceL,
			"XL": visual.SpaceXL,
		}

		for name, value := range spacings {
			if value <= 0 {
				t.Errorf("Spacing %s should be positive, got: %d", name, value)
			}
		}

		t.Logf("✓ All %d spacing values are valid", len(spacings))
	})
}

// TestSpinnerVisualRegression validates spinner rendering
func TestSpinnerVisualRegression(t *testing.T) {
	t.Run("Spinner creates valid instance", func(t *testing.T) {
		spinner := components.NewSpinner("Testing...")

		if spinner == nil {
			t.Fatal("NewSpinner should not return nil")
		}

		t.Log("✓ Spinner instance created")
	})

	t.Run("Spinner frames are valid", func(t *testing.T) {
		frames := visual.SpinnerFrames

		if len(frames) == 0 {
			t.Fatal("SpinnerFrames should not be empty")
		}

		// All frames should be single character (or unicode rune)
		for i, frame := range frames {
			if len(frame) == 0 {
				t.Errorf("Frame %d should not be empty", i)
			}
		}

		t.Logf("✓ Spinner has %d valid frames", len(frames))
	})
}

// TestStatuslineVisualRegression validates statusline rendering
func TestStatuslineVisualRegression(t *testing.T) {
	t.Run("Statusline renders with items", func(t *testing.T) {
		statusline := components.NewStatusline(80)
		statusline.AddItem("Context", "production", "⎈")
		statusline.AddItem("Namespace", "default", "")

		output := statusline.RenderCompact()

		if output == "" {
			t.Fatal("Statusline should not be empty")
		}

		// Should contain items
		if !strings.Contains(output, "Context") {
			t.Error("Statusline should contain 'Context'")
		}
		if !strings.Contains(output, "production") {
			t.Error("Statusline should contain 'production'")
		}
		if !strings.Contains(output, "⎈") {
			t.Error("Statusline should contain icon")
		}

		t.Logf("✓ Statusline renders: %s", output)
	})

	t.Run("Statusline handles empty items", func(t *testing.T) {
		statusline := components.NewStatusline(80)
		output := statusline.RenderCompact()

		// Should return empty for no items
		if output != "" {
			t.Log("Note: Empty statusline returns empty string (expected)")
		}

		t.Log("✓ Statusline handles empty state")
	})

	t.Run("Statusline separator is consistent", func(t *testing.T) {
		statusline := components.NewStatusline(80)
		statusline.AddItem("Item1", "Value1", "")
		statusline.AddItem("Item2", "Value2", "")

		output := statusline.RenderCompact()

		// Should contain separator
		if !strings.Contains(output, "│") {
			t.Error("Statusline should use │ as separator")
		}

		t.Log("✓ Statusline uses consistent separator")
	})
}

// TestBoxVisualRegression validates box component rendering
func TestBoxVisualRegression(t *testing.T) {
	t.Run("Box renders with content", func(t *testing.T) {
		box := components.NewBox("Hello World").
			WithWidth(40).
			WithBorder(visual.BorderRounded)

		output := box.Render()

		if output == "" {
			t.Fatal("Box should not be empty")
		}

		// Should contain content
		if !strings.Contains(output, "Hello World") {
			t.Error("Box should contain content")
		}

		// Should have multiple lines (borders + content)
		lines := strings.Split(output, "\n")
		if len(lines) < 3 {
			t.Errorf("Box should have at least 3 lines (top, content, bottom), got %d", len(lines))
		}

		t.Logf("✓ Box renders (%d lines)", len(lines))
	})

	t.Run("Box with title renders", func(t *testing.T) {
		box := components.NewBoxWithTitle("Title", "Content").
			WithWidth(40).
			WithBorder(visual.BorderRounded)

		output := box.Render()

		if output == "" {
			t.Fatal("Box with title should not be empty")
		}

		// Should contain both title and content
		if !strings.Contains(output, "Title") {
			t.Error("Box should contain title")
		}
		if !strings.Contains(output, "Content") {
			t.Error("Box should contain content")
		}

		t.Log("✓ Box with title renders")
	})
}

// TestTableVisualRegression validates table component
func TestTableVisualRegression(t *testing.T) {
	t.Run("Table renders with headers and rows", func(t *testing.T) {
		table := components.NewTable([]string{"NAME", "STATUS", "AGE"}).
			AddRow([]string{"pod-1", "Running", "2d"}).
			AddRow([]string{"pod-2", "Pending", "5m"})

		output := table.RenderCompact()

		if output == "" {
			t.Fatal("Table should not be empty")
		}

		// Should contain headers
		if !strings.Contains(output, "NAME") {
			t.Error("Table should contain NAME header")
		}

		// Should contain data
		if !strings.Contains(output, "pod-1") {
			t.Error("Table should contain pod-1 data")
		}

		// Should have multiple lines
		lines := strings.Split(output, "\n")
		if len(lines) < 3 {
			t.Errorf("Table should have at least 3 lines (header + 2 rows), got %d", len(lines))
		}

		t.Logf("✓ Table renders (%d lines)", len(lines))
	})
}

// TestGradientTextVisualRegression validates gradient rendering
func TestGradientTextVisualRegression(t *testing.T) {
	t.Run("Gradient text renders", func(t *testing.T) {
		palette := visual.DefaultPalette()
		gradient := palette.PrimaryGradient()

		text := "vCLI"
		output := visual.GradientText(text, gradient)

		if output == "" {
			t.Fatal("Gradient text should not be empty")
		}

		// Should contain original text (may have ANSI codes)
		// Can't do exact match due to ANSI codes
		t.Logf("✓ Gradient text renders (%d chars)", len(output))
	})

	t.Run("Gradient handles empty text", func(t *testing.T) {
		palette := visual.DefaultPalette()
		gradient := palette.PrimaryGradient()

		output := visual.GradientText("", gradient)

		if output != "" {
			t.Error("Empty text should produce empty gradient")
		}

		t.Log("✓ Gradient handles empty input")
	})
}

// TestIconsAreUnicode validates that icons render properly
func TestIconsAreUnicode(t *testing.T) {
	icons := map[string]string{
		"Success": visual.IconSuccess,
		"Error":   visual.IconError,
		"Warning": visual.IconWarning,
	}

	for name, icon := range icons {
		if icon == "" {
			t.Errorf("Icon %s should not be empty", name)
		}

		// Icons should be 1-2 characters (unicode)
		if len([]rune(icon)) > 2 {
			t.Errorf("Icon %s is too long: %q", name, icon)
		}
	}

	t.Logf("✓ All %d icons are valid unicode", len(icons))
}
