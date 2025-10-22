package widgets

import (
	"fmt"
	"time"

	"github.com/charmbracelet/lipgloss"
)

// ThroughputMeter displays real-time throughput metrics
type ThroughputMeter struct {
	width  int
	height int

	// Metrics
	decisionsPerMinute float64
	avgResponseTime    float64
	totalProcessed     int
	lastUpdate         time.Time

	// History for sparkline
	history []float64
	maxHistory int
}

// NewThroughputMeter creates a new throughput meter widget
func NewThroughputMeter() *ThroughputMeter {
	return &ThroughputMeter{
		maxHistory: 20,
		history:    make([]float64, 0, 20),
		lastUpdate: time.Now(),
	}
}

// SetSize sets the widget dimensions
func (w *ThroughputMeter) SetSize(width, height int) {
	w.width = width
	w.height = height
}

// Update updates the widget with new metrics
func (w *ThroughputMeter) Update(decisionsPerMinute, avgResponseTime float64, totalProcessed int) {
	w.decisionsPerMinute = decisionsPerMinute
	w.avgResponseTime = avgResponseTime
	w.totalProcessed = totalProcessed
	w.lastUpdate = time.Now()

	// Add to history
	w.history = append(w.history, decisionsPerMinute)
	if len(w.history) > w.maxHistory {
		w.history = w.history[1:]
	}
}

// Render renders the widget
func (w *ThroughputMeter) Render() string {
	style := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#4169E1")).
		Width(w.width).
		Height(w.height).
		Padding(1)

	var sections []string

	// Title
	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#4169E1")).
		Render("⚡ Throughput Metrics")
	sections = append(sections, title)
	sections = append(sections, "")

	// Current rate with color coding
	rateColor := "#00FF00"
	if w.decisionsPerMinute < 5 {
		rateColor = "#FFA500" // Yellow for low throughput
	} else if w.decisionsPerMinute > 50 {
		rateColor = "#FF6B6B" // Red for high throughput (potential overload)
	}

	rateLine := lipgloss.NewStyle().
		Foreground(lipgloss.Color(rateColor)).
		Bold(true).
		Render(fmt.Sprintf("Rate: %.1f decisions/min", w.decisionsPerMinute))
	sections = append(sections, rateLine)
	sections = append(sections, "")

	// Average response time
	timeColor := "#00FF00"
	if w.avgResponseTime > 5.0 {
		timeColor = "#FFA500" // Yellow for slow
	} else if w.avgResponseTime > 10.0 {
		timeColor = "#FF0000" // Red for very slow
	}

	timeLine := lipgloss.NewStyle().
		Foreground(lipgloss.Color(timeColor)).
		Render(fmt.Sprintf("Avg Response: %.2fs", w.avgResponseTime))
	sections = append(sections, timeLine)
	sections = append(sections, "")

	// Total processed
	sections = append(sections, fmt.Sprintf("Total Processed: %d", w.totalProcessed))
	sections = append(sections, "")

	// Sparkline (simple text-based trend indicator)
	if len(w.history) > 1 {
		sections = append(sections, lipgloss.NewStyle().Bold(true).Render("Trend:"))
		sparkline := w.renderSparkline()
		sections = append(sections, sparkline)
	}

	content := lipgloss.JoinVertical(lipgloss.Left, sections...)
	return style.Render(content)
}

// renderSparkline renders a simple text-based sparkline
func (w *ThroughputMeter) renderSparkline() string {
	if len(w.history) == 0 {
		return ""
	}

	// Find min/max for scaling
	min, max := w.history[0], w.history[0]
	for _, v := range w.history {
		if v < min {
			min = v
		}
		if v > max {
			max = v
		}
	}

	// Sparkline characters (8 levels)
	sparks := []string{"▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"}

	var result string
	for _, v := range w.history {
		var normalized float64
		if max > min {
			normalized = (v - min) / (max - min)
		} else {
			normalized = 0.5
		}

		index := int(normalized * float64(len(sparks)-1))
		if index < 0 {
			index = 0
		}
		if index >= len(sparks) {
			index = len(sparks) - 1
		}

		result += sparks[index]
	}

	return lipgloss.NewStyle().
		Foreground(lipgloss.Color("#4169E1")).
		Render(result)
}
