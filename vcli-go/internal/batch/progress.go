package batch

import (
	"fmt"
	"io"
	"strings"
	"time"
)

// ProgressBar represents a visual progress indicator
type ProgressBar struct {
	Total     int
	Current   int
	Width     int
	StartTime time.Time
	Writer    io.Writer
}

// NewProgressBar creates a new progress bar
func NewProgressBar(total int, writer io.Writer) *ProgressBar {
	return &ProgressBar{
		Total:     total,
		Current:   0,
		Width:     40,
		StartTime: time.Now(),
		Writer:    writer,
	}
}

// Update updates the progress bar with current count
func (p *ProgressBar) Update(current int) {
	p.Current = current
	p.Render()
}

// Increment increments the progress by 1
func (p *ProgressBar) Increment() {
	p.Current++
	p.Render()
}

// Render renders the progress bar to the writer
func (p *ProgressBar) Render() {
	if p.Writer == nil || p.Total == 0 {
		return
	}

	percentage := float64(p.Current) / float64(p.Total) * 100
	filled := int(float64(p.Width) * float64(p.Current) / float64(p.Total))

	// Build progress bar
	bar := strings.Repeat("█", filled) + strings.Repeat("░", p.Width-filled)

	// Calculate ETA
	elapsed := time.Since(p.StartTime)
	var eta string
	if p.Current > 0 {
		remaining := elapsed * time.Duration(p.Total-p.Current) / time.Duration(p.Current)
		eta = fmt.Sprintf(" ETA: %s", remaining.Round(time.Second))
	}

	// Render (with carriage return to overwrite previous line)
	fmt.Fprintf(p.Writer, "\r[%s] %d/%d (%.1f%%)%s",
		bar, p.Current, p.Total, percentage, eta)

	// Newline if complete
	if p.Current >= p.Total {
		fmt.Fprintln(p.Writer)
	}
}

// Finish completes the progress bar
func (p *ProgressBar) Finish() {
	p.Current = p.Total
	p.Render()
}
