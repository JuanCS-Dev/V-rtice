package help

import (
	"fmt"
	"strings"

	"github.com/fatih/color"
)

// Example represents a command example with description and command
type Example struct {
	Description string
	Command     string
	Output      string // Optional expected output
}

// ExampleGroup represents a group of related examples
type ExampleGroup struct {
	Title    string
	Examples []Example
}

// FormatExample formats a single example with colors
func FormatExample(ex Example) string {
	var b strings.Builder

	// Description in cyan
	cyan := color.New(color.FgCyan).SprintFunc()
	b.WriteString(fmt.Sprintf("  %s\n", cyan(ex.Description)))

	// Command in yellow with $ prefix
	yellow := color.New(color.FgYellow).SprintFunc()
	b.WriteString(fmt.Sprintf("  $ %s\n", yellow(ex.Command)))

	// Optional output in dim white
	if ex.Output != "" {
		dim := color.New(color.Faint).SprintFunc()
		for _, line := range strings.Split(ex.Output, "\n") {
			b.WriteString(fmt.Sprintf("  %s\n", dim(line)))
		}
	}

	return b.String()
}

// FormatExampleGroup formats a group of examples
func FormatExampleGroup(group ExampleGroup) string {
	var b strings.Builder

	// Title in bold green
	green := color.New(color.FgGreen, color.Bold).SprintFunc()
	b.WriteString(fmt.Sprintf("\n%s:\n\n", green(group.Title)))

	// Format each example
	for i, ex := range group.Examples {
		b.WriteString(FormatExample(ex))
		if i < len(group.Examples)-1 {
			b.WriteString("\n")
		}
	}

	return b.String()
}

// FormatExamples formats multiple example groups
func FormatExamples(groups ...ExampleGroup) string {
	var b strings.Builder
	for _, group := range groups {
		b.WriteString(FormatExampleGroup(group))
	}
	return b.String()
}

// BuildCobraExample builds a Cobra-style example string from groups
func BuildCobraExample(groups ...ExampleGroup) string {
	var b strings.Builder
	for _, group := range groups {
		if group.Title != "" {
			b.WriteString(fmt.Sprintf("# %s\n", group.Title))
		}
		for _, ex := range group.Examples {
			if ex.Description != "" {
				b.WriteString(fmt.Sprintf("  # %s\n", ex.Description))
			}
			b.WriteString(fmt.Sprintf("  %s\n\n", ex.Command))
		}
	}
	return strings.TrimSpace(b.String())
}
