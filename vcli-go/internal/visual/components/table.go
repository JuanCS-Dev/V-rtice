package components

import (
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Table represents a data table component
type Table struct {
	Headers      []string
	Rows         [][]string
	Width        int
	HeaderStyle  lipgloss.Style
	RowStyle     lipgloss.Style
	AltRowStyle  lipgloss.Style
	BorderColor  string
	ZebraStriped bool
}

// NewTable creates a new table
func NewTable(headers []string) *Table {
	return &Table{
		Headers: headers,
		Rows:    make([][]string, 0),
		Width:   visual.WidthStandard,
		HeaderStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color(visual.ColorPrimary)).
			Bold(true).
			Underline(true),
		RowStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color(visual.ColorSecondary)),
		AltRowStyle: lipgloss.NewStyle().
			Foreground(lipgloss.Color(visual.ColorSecondary)),
		BorderColor:  visual.ColorPrimary,
		ZebraStriped: true,
	}
}

// AddRow adds a row to table
func (t *Table) AddRow(row []string) *Table {
	t.Rows = append(t.Rows, row)
	return t
}

// AddRows adds multiple rows
func (t *Table) AddRows(rows [][]string) *Table {
	t.Rows = append(t.Rows, rows...)
	return t
}

// WithWidth sets table width
func (t *Table) WithWidth(width int) *Table {
	t.Width = width
	return t
}

// WithZebraStriping enables/disables zebra striping
func (t *Table) WithZebraStriping(enabled bool) *Table {
	t.ZebraStriped = enabled
	return t
}

// Render renders the table to string
func (t *Table) Render() string {
	if len(t.Headers) == 0 {
		return ""
	}

	// Calculate column widths
	colWidths := t.calculateColumnWidths()

	var lines []string

	// Render header
	headerLine := t.renderHeader(colWidths)
	lines = append(lines, headerLine)

	// Render separator
	separator := t.renderSeparator(colWidths)
	lines = append(lines, separator)

	// Render rows
	for i, row := range t.Rows {
		useAltStyle := t.ZebraStriped && i%2 == 1
		rowLine := t.renderRow(row, colWidths, useAltStyle)
		lines = append(lines, rowLine)
	}

	return strings.Join(lines, "\n")
}

// calculateColumnWidths calculates optimal column widths
func (t *Table) calculateColumnWidths() []int {
	numCols := len(t.Headers)
	colWidths := make([]int, numCols)

	// Start with header widths
	for i, header := range t.Headers {
		colWidths[i] = lipgloss.Width(header)
	}

	// Check all rows for max width
	for _, row := range t.Rows {
		for i := 0; i < numCols && i < len(row); i++ {
			cellWidth := lipgloss.Width(row[i])
			if cellWidth > colWidths[i] {
				colWidths[i] = cellWidth
			}
		}
	}

	// Calculate total width needed
	totalWidth := 0
	for _, w := range colWidths {
		totalWidth += w
	}

	// Add spacing (3 chars per column: " | ")
	totalWidth += (numCols - 1) * 3

	// If over limit, proportionally reduce
	if totalWidth > t.Width {
		ratio := float64(t.Width) / float64(totalWidth)
		for i := range colWidths {
			colWidths[i] = int(float64(colWidths[i]) * ratio)
			if colWidths[i] < 5 {
				colWidths[i] = 5 // Minimum column width
			}
		}
	}

	return colWidths
}

// renderHeader renders header row
func (t *Table) renderHeader(colWidths []int) string {
	var cells []string

	for i, header := range t.Headers {
		width := colWidths[i]
		cell := t.HeaderStyle.Render(lipgloss.PlaceHorizontal(width, lipgloss.Left, header))
		cells = append(cells, cell)
	}

	return strings.Join(cells, " │ ")
}

// renderSeparator renders separator line
func (t *Table) renderSeparator(colWidths []int) string {
	var segments []string

	separatorStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(visual.ColorMuted))

	for _, width := range colWidths {
		segment := strings.Repeat("─", width)
		segments = append(segments, separatorStyle.Render(segment))
	}

	return strings.Join(segments, "─┼─")
}

// renderRow renders a data row
func (t *Table) renderRow(row []string, colWidths []int, useAltStyle bool) string {
	var cells []string

	style := t.RowStyle
	if useAltStyle {
		style = t.AltRowStyle
	}

	for i := 0; i < len(t.Headers); i++ {
		width := colWidths[i]
		cellValue := ""

		if i < len(row) {
			cellValue = row[i]
		}

		// Truncate if too long
		if lipgloss.Width(cellValue) > width {
			cellValue = cellValue[:width-3] + "..."
		}

		cell := style.Render(lipgloss.PlaceHorizontal(width, lipgloss.Left, cellValue))
		cells = append(cells, cell)
	}

	return strings.Join(cells, " │ ")
}

// RenderCompact renders table without borders (VSCode style)
func (t *Table) RenderCompact() string {
	if len(t.Headers) == 0 {
		return ""
	}

	colWidths := t.calculateColumnWidths()
	var lines []string

	// Header (uppercase)
	var headerCells []string
	for i, header := range t.Headers {
		width := colWidths[i]
		upperHeader := strings.ToUpper(header)
		cell := t.HeaderStyle.Render(lipgloss.PlaceHorizontal(width, lipgloss.Left, upperHeader))
		headerCells = append(headerCells, cell)
	}
	lines = append(lines, strings.Join(headerCells, "  "))

	// Rows (no separator)
	for i, row := range t.Rows {
		useAltStyle := t.ZebraStriped && i%2 == 1
		var rowCells []string

		style := t.RowStyle
		if useAltStyle {
			style = t.AltRowStyle
		}

		for j := 0; j < len(t.Headers); j++ {
			width := colWidths[j]
			cellValue := ""

			if j < len(row) {
				cellValue = row[j]
			}

			if lipgloss.Width(cellValue) > width {
				cellValue = cellValue[:width-3] + "..."
			}

			cell := style.Render(lipgloss.PlaceHorizontal(width, lipgloss.Left, cellValue))
			rowCells = append(rowCells, cell)
		}

		lines = append(lines, strings.Join(rowCells, "  "))
	}

	return strings.Join(lines, "\n")
}
