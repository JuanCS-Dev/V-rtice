package bubbletea

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
	"github.com/verticedev/vcli-go/internal/visual/banner"
)

// View renders the shell
func (m Model) View() string {
	if m.quitting {
		// Return empty - let shell.go handle cleanup
		return ""
	}

	var output strings.Builder

	// Show welcome banner on first render
	if m.showWelcome {
		output.WriteString(m.renderWelcomeBanner())
		output.WriteString("\n\n")
	}

	// Warning if terminal is too small (below minimum)
	if m.width < MinWidth || m.height < MinHeight {
		warning := m.styles.Warning.Render(fmt.Sprintf(
			"⚠️  Terminal too small! Minimum: %dx%d (current: %dx%d)",
			MinWidth, MinHeight, m.width, m.height,
		))
		output.WriteString(warning)
		output.WriteString("\n\n")
	}

	// Render prompt
	output.WriteString(m.renderPrompt())
	output.WriteString("\n")

	// Render autocomplete suggestions
	if m.showSuggestions && len(m.suggestions) > 0 {
		output.WriteString(m.renderSuggestions())
		output.WriteString("\n")
	}

	// Render bottom toolbar
	output.WriteString("\n")
	output.WriteString(m.renderToolbar())

	return output.String()
}

// renderPrompt renders the multi-line prompt
func (m Model) renderPrompt() string {
	gradient := m.palette.PrimaryGradient()

	// Top line: vCLI title with gradient + statusline inline
	title := visual.GradientText("vCLI", gradient)
	edition := m.styles.Muted.Render(" 🚀 Kubernetes Edition")

	var topLine string
	if m.statusline != "" {
		// Include statusline: ╭─[vCLI] 🚀 Kubernetes Edition │ ⎈ context │ namespace
		topLine = fmt.Sprintf("╭─[%s]%s │ %s", title, edition, m.statusline)
	} else {
		topLine = fmt.Sprintf("╭─[%s]%s", title, edition)
	}

	// Bottom line: input prompt
	promptSymbol := m.styles.Accent.Render("╰─> ")
	inputLine := promptSymbol + m.textInput.View()

	return topLine + "\n" + inputLine
}

// renderSuggestions renders autocomplete suggestions as a dropdown
func (m Model) renderSuggestions() string {
	if len(m.suggestions) == 0 {
		return ""
	}

	var content strings.Builder

	// Limit to 8 suggestions for better UX
	maxSuggestions := 8
	displaySuggestions := m.suggestions
	if len(displaySuggestions) > maxSuggestions {
		displaySuggestions = displaySuggestions[:maxSuggestions]
	}

	// Render each suggestion
	for i, sug := range displaySuggestions {
		// Cursor indicator
		cursor := "  "
		if i == m.suggestCursor {
			cursor = m.styles.Accent.Render("→ ")
		} else {
			cursor = "  "
		}

		// Icon
		icon := sug.Icon
		if icon != "" {
			icon = icon + " "
		}

		// Command text
		var cmdText string
		if i == m.suggestCursor {
			cmdText = m.styles.Accent.Bold(true).Render(sug.Text)
		} else {
			cmdText = m.styles.Info.Render(sug.Text)
		}

		// Description (with max length)
		desc := sug.Description
		maxDescLen := 50
		if m.width > 100 {
			maxDescLen = 60
		}
		if len(desc) > maxDescLen {
			desc = desc[:maxDescLen-3] + "..."
		}
		descText := m.styles.Muted.Render(desc)

		// Format: cursor icon command     description
		line := fmt.Sprintf("%s%s%-35s %s", cursor, icon, cmdText, descText)
		content.WriteString(line)

		// Add newline except for last item
		if i < len(displaySuggestions)-1 {
			content.WriteString("\n")
		}
	}

	// Box style with rounded border
	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.palette.Cyan.ToTermenv()).
		Padding(1, 2).
		MarginTop(1)

	// Add count footer if more suggestions available
	footer := ""
	if len(m.suggestions) > maxSuggestions {
		footer = "\n" + m.styles.Muted.Render(fmt.Sprintf("... %d more", len(m.suggestions)-maxSuggestions))
	}

	return boxStyle.Render(content.String() + footer)
}

// renderToolbar renders the bottom toolbar with keybindings
func (m Model) renderToolbar() string {
	// Separator line - use full width with minimum enforcement
	separatorWidth := m.width
	if separatorWidth < MinWidth {
		separatorWidth = MinWidth
	}
	separator := m.styles.Muted.Render(strings.Repeat("━", separatorWidth))

	// Keybindings with icons
	bindings := []struct {
		key  string
		desc string
	}{
		{"/", "Commands"},
		{"Tab", "Complete"},
		{"↑↓", "Navigate"},
		{"Ctrl+D", "Exit"},
	}

	var formattedBindings []string
	for _, binding := range bindings {
		key := m.styles.Accent.Bold(true).Render(binding.key)
		desc := m.styles.Muted.Render(binding.desc)
		formattedBindings = append(formattedBindings, key+": "+desc)
	}

	toolbar := strings.Join(formattedBindings, " │ ")

	return separator + "\n" + toolbar
}

// renderWelcomeBanner renders the welcome banner with two columns
func (m Model) renderWelcomeBanner() string {
	var output strings.Builder
	gradient := m.palette.PrimaryGradient()

	// Show compact banner with gradient
	renderer := banner.NewBannerRenderer()
	output.WriteString(renderer.RenderCompact(m.version, m.buildDate))
	output.WriteString("\n")

	// Column headers with gradient
	featuresTitle := visual.GradientText("Key Features", gradient)
	workflowsTitle := visual.GradientText("AI-Powered Workflows", gradient)

	// Calculate exact spacing for perfect alignment
	// Right column starts at position 46 (same as content below)
	// "Key Features" = 12 chars
	// 2 (prefix) + 12 (text) = 14
	// Gap needed: 46 - 14 = 32 spaces
	titleGap := 32

	output.WriteString(fmt.Sprintf("  %s%s%s\n",
		featuresTitle,
		strings.Repeat(" ", titleGap),
		workflowsTitle))
	output.WriteString("\n")

	// Feature bullets (left column) - Most impactful features
	features := []string{
		"🧠 MAXIMUS Conscious AI integration",
		"🛡️ Active Immune System protection",
		"⎈ Real-time Kubernetes orchestration",
		"🔍 AI-powered threat hunting",
	}

	// Workflows data (right column)
	workflows := []struct {
		emoji string
		name  string
		alias string
	}{
		{"🎯", "Threat Hunt", "wf1"},
		{"🚨", "Incident Response", "wf2"},
		{"🔐", "Security Audit", "wf3"},
		{"✅", "Compliance Check", "wf4"},
	}

	// Use lipgloss for PERFECT alignment (Stack Overflow style! 😄)
	leftColStyle := lipgloss.NewStyle().
		Width(45).
		Align(lipgloss.Left).
		PaddingLeft(2)

	rightColStyle := lipgloss.NewStyle().
		Width(35).
		Align(lipgloss.Left)

	for i := 0; i < 4; i++ {
		// Left column with fixed width
		leftText := m.styles.Muted.Render(features[i])
		leftCol := leftColStyle.Render(leftText)

		// Right column with fixed width
		// Add extra space before 2nd workflow to align it
		spacing := ""
		if i == 1 { // Incident Response needs 1 extra space
			spacing = " "
		}
		rightText := fmt.Sprintf("%s%s %s (%s)",
			spacing,
			workflows[i].emoji,
			m.styles.Muted.Render(workflows[i].name),
			m.styles.Accent.Render(workflows[i].alias))
		rightCol := rightColStyle.Render(rightText)

		// Join horizontally with lipgloss magic
		line := lipgloss.JoinHorizontal(lipgloss.Top, leftCol, rightCol)
		output.WriteString(line + "\n")
	}

	return output.String()
}
