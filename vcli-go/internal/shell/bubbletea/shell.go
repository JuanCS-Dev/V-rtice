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

	// Clear screen before starting (like Claude Code does)
	fmt.Print("\033[2J\033[H")

	// Create model
	m := NewModel(rootCmd, version, buildDate)

	// Create program with alternate screen buffer
	p := tea.NewProgram(
		m,
		tea.WithAltScreen(),       // Use alternate screen buffer
		tea.WithMouseCellMotion(), // Enable mouse support
	)

	// Run
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("error running shell: %w", err)
	}

	// Force terminal cleanup after bubble tea exits
	// This ensures terminal is fully restored
	fmt.Print("\033[?25h")     // Show cursor
	fmt.Print("\033[0m")       // Reset all attributes
	fmt.Print("\033[2J\033[H") // Clear screen
	fmt.Println()              // Newline for clean exit
	fmt.Println("👋 Goodbye!")
	fmt.Println()              // Extra newline to prevent zsh % bug

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

	// Two-column layout: Features and Workflows
	fmt.Println()

	// Column headers with gradient
	shellTitle := visual.GradientText("Modern Interactive Shell", gradient)
	workflowsTitle := visual.GradientText("AI Workflows", gradient)

	fmt.Printf("  %-50s  %s\n", shellTitle, workflowsTitle)
	fmt.Println()

	// Feature bullets (left column)
	features := []string{
		"✨ Autocomplete",
		"📦 Icons for commands",
		"⌨️  Full keyboard navigation",
		"🎨 Visual feedback",
	}

	// Workflows (right column)
	workflows := []struct {
		num   int
		name  string
		alias string
	}{
		{1, "Threat Hunt", "wf1"},
		{2, "Incident Response", "wf2"},
		{3, "Security Audit", "wf3"},
		{4, "Compliance Check", "wf4"},
	}

	// Print both columns side by side
	for i := 0; i < 4; i++ {
		leftCol := styles.Muted.Render(features[i])

		wf := workflows[i]
		alias := styles.Accent.Render(wf.alias)
		name := styles.Muted.Render(wf.name)
		rightCol := fmt.Sprintf("%d. %s (%s)", wf.num, name, alias)

		fmt.Printf("  %-50s  %s\n", leftCol, rightCol)
	}
	fmt.Println()

	// Quick start hints
	fmt.Printf("%s │ %s │ %s │ %s\n\n",
		styles.Accent.Render("Tab: Complete"),
		styles.Accent.Render("↑↓: Navigate"),
		styles.Accent.Render("Ctrl+K: Palette"),
		styles.Accent.Render("Ctrl+D: Exit"))
}
