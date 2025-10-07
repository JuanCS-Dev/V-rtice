package bubbletea

import (
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

// Update handles messages and updates the model
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.textInput.Width = msg.Width - 10

	case tea.KeyMsg:
		return m.handleKeyPress(msg)
	}

	// Update text input
	m.textInput, cmd = m.textInput.Update(msg)

	// Trigger autocomplete on text change
	m.updateAutocomplete()

	return m, cmd
}

// handleKeyPress handles keyboard input
func (m Model) handleKeyPress(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.Type {
	case tea.KeyCtrlC:
		// Clear input
		m.textInput.SetValue("")
		m.suggestions = make([]Suggestion, 0)
		m.suggestCursor = -1
		m.showSuggestions = false
		return m, nil

	case tea.KeyCtrlD:
		// Exit
		m.quitting = true
		return m, tea.Quit

	case tea.KeyCtrlK:
		// Open command palette (will be implemented in FASE 5)
		// For now, just show a message
		// TODO: Open palette
		return m, nil

	case tea.KeyEnter:
		// Execute command or accept suggestion
		if m.suggestCursor >= 0 && len(m.suggestions) > 0 {
			// Accept suggestion
			m.textInput.SetValue(m.suggestions[m.suggestCursor].Text)
			m.suggestCursor = -1
			m.showSuggestions = false
		} else {
			// Execute command
			cmd := m.textInput.Value()
			if cmd != "" {
				m.executeCommand(cmd)
				m.textInput.SetValue("")
			}
		}
		m.suggestions = make([]Suggestion, 0)
		return m, nil

	case tea.KeyTab:
		// Accept suggestion or trigger autocomplete
		if m.suggestCursor >= 0 && len(m.suggestions) > 0 {
			m.textInput.SetValue(m.suggestions[m.suggestCursor].Text)
			m.suggestCursor = -1
			m.showSuggestions = false
			m.suggestions = make([]Suggestion, 0)
		}
		return m, nil

	case tea.KeyUp:
		// Navigate suggestions up
		if len(m.suggestions) > 0 {
			m.showSuggestions = true
			if m.suggestCursor > 0 {
				m.suggestCursor--
			} else if m.suggestCursor == -1 {
				m.suggestCursor = len(m.suggestions) - 1
			}
			return m, nil
		}

	case tea.KeyDown:
		// Navigate suggestions down
		if len(m.suggestions) > 0 {
			m.showSuggestions = true
			if m.suggestCursor < len(m.suggestions)-1 {
				m.suggestCursor++
			} else {
				m.suggestCursor = -1
			}
			return m, nil
		}

	case tea.KeyEsc:
		// Hide suggestions
		m.showSuggestions = false
		m.suggestCursor = -1
		return m, nil
	}

	// Default: update text input
	var cmd tea.Cmd
	m.textInput, cmd = m.textInput.Update(msg)
	return m, cmd
}

// updateAutocomplete updates autocomplete suggestions based on current input
func (m *Model) updateAutocomplete() {
	text := m.textInput.Value()

	// Don't show suggestions if empty or ends with space
	if text == "" || strings.HasSuffix(text, " ") {
		m.suggestions = make([]Suggestion, 0)
		m.suggestCursor = -1
		m.showSuggestions = false
		return
	}

	// Get suggestions from completer
	promptSuggestions := m.completer.CompleteText(text)

	// Convert to our Suggestion type
	m.suggestions = make([]Suggestion, 0, len(promptSuggestions))
	for _, s := range promptSuggestions {
		m.suggestions = append(m.suggestions, Suggestion{
			Text:        s.Text,
			Description: s.Description,
			Icon:        getIconForCommand(s.Text),
		})
	}

	// Show suggestions if we have any
	m.showSuggestions = len(m.suggestions) > 0

	// Reset cursor if suggestions changed
	if m.suggestCursor >= len(m.suggestions) {
		m.suggestCursor = -1
	}
}

// executeCommand executes a command via the executor
func (m *Model) executeCommand(cmd string) {
	// Use existing executor
	m.executor.Execute(cmd)
}

// getIconForCommand returns an icon emoji for a command
func getIconForCommand(cmd string) string {
	// Simple icon mapping
	if strings.HasPrefix(cmd, "k8s") {
		return "📦"
	}
	if strings.HasPrefix(cmd, "orchestrate") {
		return "🚀"
	}
	if strings.HasPrefix(cmd, "data") {
		return "💾"
	}
	if strings.HasPrefix(cmd, "investigate") {
		return "🔍"
	}
	if strings.HasPrefix(cmd, "immune") {
		return "🛡️"
	}
	if strings.HasPrefix(cmd, "maximus") {
		return "🧠"
	}
	if strings.HasPrefix(cmd, "/") {
		return "⚡"
	}
	return "▶"
}
