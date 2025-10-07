package suggestions

import (
	"fmt"
	"sort"
	"strings"

	"github.com/agnivade/levenshtein"
	"github.com/spf13/cobra"
	"github.com/spf13/pflag"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Suggester provides intelligent command suggestions
type Suggester struct {
	commands []string
	styles   *visual.Styles
}

// NewSuggester creates a new suggester
func NewSuggester(rootCmd *cobra.Command) *Suggester {
	s := &Suggester{
		commands: make([]string, 0),
		styles:   visual.DefaultStyles(),
	}

	s.buildCommandList(rootCmd, "")
	return s
}

// buildCommandList recursively builds the command list
func (s *Suggester) buildCommandList(cmd *cobra.Command, prefix string) {
	for _, subCmd := range cmd.Commands() {
		if subCmd.Hidden {
			continue
		}

		// Build command path
		cmdPath := subCmd.Use
		if prefix != "" {
			cmdPath = prefix + " " + subCmd.Use
		}

		// Extract command name (without args spec)
		cmdName := strings.Split(cmdPath, " ")[0]
		if prefix != "" {
			cmdName = prefix + " " + strings.Split(subCmd.Use, " ")[0]
		}

		s.commands = append(s.commands, cmdName)

		// Add subcommands recursively
		if subCmd.HasSubCommands() {
			s.buildCommandList(subCmd, cmdName)
		}
	}
}

// SuggestCommand suggests a similar command for a typo
func (s *Suggester) SuggestCommand(typo string) string {
	if len(s.commands) == 0 {
		return ""
	}

	// Find best matches
	matches := s.findSimilar(typo, 3)

	if len(matches) == 0 {
		return s.formatNoSuggestion(typo)
	}

	if len(matches) == 1 {
		return s.formatSingleSuggestion(typo, matches[0])
	}

	return s.formatMultipleSuggestions(typo, matches)
}

// findSimilar finds similar commands using Levenshtein distance
func (s *Suggester) findSimilar(typo string, maxResults int) []string {
	type match struct {
		cmd      string
		distance int
	}

	matches := make([]match, 0)

	// Calculate distance for each command
	for _, cmd := range s.commands {
		// Calculate distance
		dist := levenshtein.ComputeDistance(strings.ToLower(typo), strings.ToLower(cmd))

		// Only consider if distance is reasonable
		// (not more than 40% of the length)
		maxDist := len(typo) * 40 / 100
		if maxDist < 2 {
			maxDist = 2
		}

		if dist <= maxDist {
			matches = append(matches, match{cmd: cmd, distance: dist})
		}
	}

	// Sort by distance
	sort.Slice(matches, func(i, j int) bool {
		if matches[i].distance == matches[j].distance {
			// If same distance, prefer shorter commands
			return len(matches[i].cmd) < len(matches[j].cmd)
		}
		return matches[i].distance < matches[j].distance
	})

	// Return top matches
	result := make([]string, 0)
	for i := 0; i < len(matches) && i < maxResults; i++ {
		result = append(result, matches[i].cmd)
	}

	return result
}

// formatNoSuggestion formats message when no suggestion is found
func (s *Suggester) formatNoSuggestion(typo string) string {
	var msg strings.Builder

	msg.WriteString("\n")
	msg.WriteString(s.styles.Error.Render(fmt.Sprintf("❌ Unknown command: '%s'", typo)))
	msg.WriteString("\n\n")
	msg.WriteString(s.styles.Muted.Render("💡 Type 'help' or '--help' to see available commands"))
	msg.WriteString("\n")

	return msg.String()
}

// formatSingleSuggestion formats message with a single suggestion
func (s *Suggester) formatSingleSuggestion(typo, suggestion string) string {
	var msg strings.Builder

	msg.WriteString("\n")
	msg.WriteString(s.styles.Error.Render(fmt.Sprintf("❌ Unknown command: '%s'", typo)))
	msg.WriteString("\n\n")
	msg.WriteString(s.styles.Info.Render("💡 Did you mean:"))
	msg.WriteString("\n")
	msg.WriteString(s.styles.Accent.Render(fmt.Sprintf("   %s", suggestion)))
	msg.WriteString("\n")

	return msg.String()
}

// formatMultipleSuggestions formats message with multiple suggestions
func (s *Suggester) formatMultipleSuggestions(typo string, suggestions []string) string {
	var msg strings.Builder

	msg.WriteString("\n")
	msg.WriteString(s.styles.Error.Render(fmt.Sprintf("❌ Unknown command: '%s'", typo)))
	msg.WriteString("\n\n")
	msg.WriteString(s.styles.Info.Render("💡 Did you mean one of these:"))
	msg.WriteString("\n")

	for _, suggestion := range suggestions {
		msg.WriteString(s.styles.Accent.Render(fmt.Sprintf("   • %s", suggestion)))
		msg.WriteString("\n")
	}

	return msg.String()
}

// SuggestFlag suggests a similar flag for a typo
func (s *Suggester) SuggestFlag(cmd *cobra.Command, typo string) string {
	flags := make([]string, 0)

	// Collect all flags
	cmd.Flags().VisitAll(func(f *pflag.Flag) {
		if f.Name != "" {
			flags = append(flags, "--"+f.Name)
		}
		if f.Shorthand != "" {
			flags = append(flags, "-"+f.Shorthand)
		}
	})

	if len(flags) == 0 {
		return ""
	}

	// Find best match
	bestMatch := ""
	bestDistance := 999

	for _, flag := range flags {
		dist := levenshtein.ComputeDistance(strings.ToLower(typo), strings.ToLower(flag))
		if dist < bestDistance && dist <= 3 {
			bestDistance = dist
			bestMatch = flag
		}
	}

	if bestMatch == "" {
		return ""
	}

	return s.formatSingleSuggestion(typo, bestMatch)
}

// GetAllCommands returns all available commands
func (s *Suggester) GetAllCommands() []string {
	return s.commands
}
