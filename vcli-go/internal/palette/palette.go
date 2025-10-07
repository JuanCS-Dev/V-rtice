package palette

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/visual"
)

// CommandItem represents a command in the palette
type CommandItem struct {
	Command     string
	Description string
}

// Model represents the command palette state
type Model struct {
	commands     []CommandItem
	filtered     []CommandItem
	query        string
	cursor       int
	width        int
	height       int
	selected     *CommandItem
	cancelled    bool
	styles       *visual.Styles
	palette      *visual.VerticePalette
}

// NewModel creates a new command palette model
func NewModel(rootCmd *cobra.Command) Model {
	m := Model{
		commands: make([]CommandItem, 0),
		filtered: make([]CommandItem, 0),
		query:    "",
		cursor:   0,
		width:    80,
		height:   20,
		styles:   visual.DefaultStyles(),
		palette:  visual.DefaultPalette(),
	}

	m.buildCommands(rootCmd, "")
	m.filtered = m.commands

	return m
}

// buildCommands recursively builds command list
func (m *Model) buildCommands(cmd *cobra.Command, prefix string) {
	for _, subCmd := range cmd.Commands() {
		if subCmd.Hidden {
			continue
		}

		// Build command path
		cmdName := strings.Split(subCmd.Use, " ")[0]
		fullPath := cmdName
		if prefix != "" {
			fullPath = prefix + " " + cmdName
		}

		// Add to commands
		m.commands = append(m.commands, CommandItem{
			Command:     fullPath,
			Description: subCmd.Short,
		})

		// Add subcommands recursively
		if subCmd.HasSubCommands() {
			m.buildCommands(subCmd, fullPath)
		}
	}
}

// Init initializes the model
func (m Model) Init() tea.Cmd {
	return nil
}

// Update handles messages
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "esc":
			// Cancel
			m.cancelled = true
			return m, tea.Quit

		case "enter":
			// Select current item
			if len(m.filtered) > 0 && m.cursor < len(m.filtered) {
				m.selected = &m.filtered[m.cursor]
			}
			return m, tea.Quit

		case "up", "ctrl+k":
			// Move cursor up
			if m.cursor > 0 {
				m.cursor--
			}

		case "down", "ctrl+j":
			// Move cursor down
			if m.cursor < len(m.filtered)-1 {
				m.cursor++
			}

		case "backspace":
			// Delete character
			if len(m.query) > 0 {
				m.query = m.query[:len(m.query)-1]
				m.updateFiltered()
				m.cursor = 0
			}

		case "ctrl+u":
			// Clear query
			m.query = ""
			m.updateFiltered()
			m.cursor = 0

		default:
			// Add character to query
			if len(msg.String()) == 1 {
				m.query += msg.String()
				m.updateFiltered()
				m.cursor = 0
			}
		}

	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
	}

	return m, nil
}

// updateFiltered updates the filtered commands based on query
func (m *Model) updateFiltered() {
	if m.query == "" {
		m.filtered = m.commands
		return
	}

	// Collect command strings
	commandStrs := make([]string, len(m.commands))
	commandMap := make(map[string]CommandItem)

	for i, cmd := range m.commands {
		commandStrs[i] = cmd.Command
		commandMap[cmd.Command] = cmd
	}

	// Rank matches
	ranked := RankMatches(m.query, commandStrs)

	// Rebuild filtered list
	m.filtered = make([]CommandItem, 0, len(ranked))
	for _, cmdStr := range ranked {
		m.filtered = append(m.filtered, commandMap[cmdStr])
	}
}

// View renders the command palette
func (m Model) View() string {
	if m.width == 0 || m.height == 0 {
		return ""
	}

	gradient := m.palette.PrimaryGradient()

	// Title
	title := visual.GradientText("Command Palette", gradient)

	// Search box
	searchPrompt := m.styles.Accent.Render("Search: ")
	searchQuery := m.query
	if searchQuery == "" {
		searchQuery = m.styles.Muted.Render("Type to search...")
	}

	// Build results
	maxResults := m.height - 8 // Leave room for header and footer
	if maxResults < 1 {
		maxResults = 1
	}

	var results strings.Builder

	for i := 0; i < len(m.filtered) && i < maxResults; i++ {
		item := m.filtered[i]

		// Cursor indicator
		cursor := "  "
		if i == m.cursor {
			cursor = m.styles.Accent.Render("▶ ")
		}

		// Command
		cmdText := item.Command
		if i == m.cursor {
			cmdText = m.styles.Accent.Bold(true).Render(item.Command)
		} else {
			cmdText = m.styles.Info.Render(item.Command)
		}

		// Description
		desc := item.Description
		if len(desc) > 50 {
			desc = desc[:47] + "..."
		}
		descText := m.styles.Muted.Render(desc)

		results.WriteString(fmt.Sprintf("%s%-40s %s\n", cursor, cmdText, descText))
	}

	// Footer
	resultCount := fmt.Sprintf("%d results", len(m.filtered))
	footer := m.styles.Muted.Render(fmt.Sprintf("↑↓: Navigate │ Enter: Select │ Esc: Cancel │ %s", resultCount))

	// Box style
	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.palette.Cyan.ToTermenv()).
		Padding(1, 2).
		Width(m.width - 4)

	// Content
	content := fmt.Sprintf("%s\n\n%s%s\n\n%s\n\n%s",
		title,
		searchPrompt,
		searchQuery,
		results.String(),
		footer,
	)

	return boxStyle.Render(content)
}

// Selected returns the selected command (if any)
func (m Model) Selected() *CommandItem {
	return m.selected
}

// Cancelled returns whether the palette was cancelled
func (m Model) Cancelled() bool {
	return m.cancelled
}

// Run runs the command palette and returns the selected command
func Run(rootCmd *cobra.Command) (*CommandItem, error) {
	m := NewModel(rootCmd)
	p := tea.NewProgram(m, tea.WithAltScreen())

	finalModel, err := p.Run()
	if err != nil {
		return nil, err
	}

	final := finalModel.(Model)
	if final.Cancelled() {
		return nil, nil
	}

	return final.Selected(), nil
}
