package bubbletea

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// View renders the shell
func (m Model) View() string {
	if m.quitting {
		return m.styles.Info.Render("👋 Goodbye!\n")
	}

	var output strings.Builder

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
	// Separator line
	separatorWidth := m.width
	if separatorWidth < 80 {
		separatorWidth = 80
	}
	if separatorWidth > 120 {
		separatorWidth = 120
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
