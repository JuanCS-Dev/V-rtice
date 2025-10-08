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
		// Clear screen and show goodbye message
		return "\033[2J\033[H" + m.styles.Info.Render("👋 Goodbye!") + "\n\n"
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
		{"Tab", "Complete"},
		{"↑↓", "Navigate"},
		{"Ctrl+K", "Palette"},
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
	// Left column: 2 spaces padding + content
	// Gap: spacing between columns
	// Right column: content
	titleGap := 24 // Spacing between column titles
	if titleGap < 0 {
		titleGap = 4 // Minimum gap
	}

	output.WriteString(fmt.Sprintf("  %s%s%s\n",
		featuresTitle,
		strings.Repeat(" ", titleGap),
		workflowsTitle))
	output.WriteString("\n")

	// Feature bullets (left column) - Most impactful features
	features := []string{
		"🧠 MAXIMUS Conscious AI integration",
		"🛡️  Active Immune System protection",
		"⎈ Real-time Kubernetes orchestration",
		"🔍 AI-powered threat hunting",
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

	// Print both columns side by side with perfect alignment
	// Left column width: 40 chars (visible) for consistent spacing
	leftColWidth := 40

	for i := 0; i < 4; i++ {
		// Left column - plain text length for spacing calculation
		leftText := features[i]
		leftStyled := m.styles.Muted.Render(leftText)

		// Calculate padding needed (accounting for emoji width)
		// Note: Emojis count as 1 char in len() but render wider
		textLen := len(leftText)
		leftPadding := leftColWidth - textLen

		// Ensure padding is never negative
		if leftPadding < 0 {
			leftPadding = 0
		}

		// Right column - format: "N. Name (alias)"
		wf := workflows[i]
		alias := m.styles.Accent.Render(wf.alias)
		name := m.styles.Muted.Render(wf.name)
		rightCol := fmt.Sprintf("%d. %s (%s)", wf.num, name, alias)

		output.WriteString(fmt.Sprintf("  %s%s    %s\n",
			leftStyled,
			strings.Repeat(" ", leftPadding),
			rightCol))
	}

	return output.String()
}
