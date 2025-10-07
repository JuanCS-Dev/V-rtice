package bubbletea

import (
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"golang.org/x/term"
	"github.com/verticedev/vcli-go/internal/visual"
	"github.com/verticedev/vcli-go/internal/visual/banner"
)

// Run starts the bubble tea interactive shell
func Run(rootCmd *cobra.Command, version, buildDate string) error {
	// Check if stdin is a terminal
	if !term.IsTerminal(int(os.Stdin.Fd())) {
		return fmt.Errorf("shell requires an interactive terminal (TTY)")
	}

	// Show welcome banner
	showWelcomeBanner(version, buildDate)

	// Create model
	m := NewModel(rootCmd, version, buildDate)

	// Create program (without AltScreen to avoid TTY issues)
	p := tea.NewProgram(m)

	// Run
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("error running shell: %w", err)
	}

	return nil
}

// showWelcomeBanner displays the welcome banner
func showWelcomeBanner(version, buildDate string) {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()
	gradient := palette.PrimaryGradient()

	// Clear screen
	fmt.Print("\033[H\033[2J")

	// Show compact banner with gradient
	renderer := banner.NewBannerRenderer()
	fmt.Print(renderer.RenderCompact(version, buildDate))

	// Welcome message with gradient
	welcome := visual.GradientText("Modern Interactive Shell", gradient)
	fmt.Printf("  %s\n", welcome)

	// Feature bullets
	features := []string{
		"✨ Autocomplete appears as you type",
		"📦 Icons for commands",
		"⌨️  Full keyboard navigation",
		"🎨 Visual feedback",
	}

	for _, feature := range features {
		fmt.Printf("  %s\n", styles.Muted.Render(feature))
	}
	fmt.Println()

	// Quick start hints
	fmt.Printf("%s │ %s │ %s │ %s\n\n",
		styles.Accent.Render("Tab: Complete"),
		styles.Accent.Render("↑↓: Navigate"),
		styles.Accent.Render("Ctrl+K: Palette"),
		styles.Accent.Render("Ctrl+D: Exit"))
}
