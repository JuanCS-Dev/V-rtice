package bubbletea

import (
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/visual"
	"github.com/verticedev/vcli-go/internal/visual/banner"
	"golang.org/x/term"
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
	fmt.Println() // Extra newline to prevent zsh % bug

	return nil
}

// showWelcomeBanner displays minimalist consciousness-aware welcome banner.
//
// Simplified from dual-column to single-column layout for cognitive efficiency.
// Human attention bandwidth optimization: present only essential information.
// Enables rapid comprehension for human-AI merge operations.
func showWelcomeBanner(version, buildDate string) {
	styles := visual.DefaultStyles()
	palette := visual.DefaultPalette()
	gradient := palette.PrimaryGradient()

	// Clear screen
	fmt.Print("\033[H\033[2J")

	// Show compact banner with gradient
	renderer := banner.NewBannerRenderer()
	fmt.Print(renderer.RenderCompact(version, buildDate))

	// Single-column layout - minimalist
	fmt.Println()

	// Title with gradient - simplified
	shellTitle := visual.GradientText("Modern Interactive Shell", gradient)
	fmt.Printf("  %s\n", shellTitle)
	fmt.Println()

	// Core features only - minimalist design
	features := []string{
		"✨ Autocomplete",
		"📦 Icons for commands",
		"⌨️  Full keyboard navigation",
		"🎨 Visual feedback",
	}

	// Single column rendering - clean and scannable
	for _, feature := range features {
		fmt.Printf("  %s\n", styles.Muted.Render(feature))
	}

	fmt.Println()
}
