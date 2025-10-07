package investigation

import (
	"context"
	"fmt"
	"io"
	"strings"

	"github.com/verticedev/vcli-go/internal/visual"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes"
)

// LogViewer manages pod log viewing with filtering
type LogViewer struct {
	lines      []string
	filter     string
	scrollPos  int
	following  bool
	styles     *visual.Styles
	palette    *visual.VerticePalette
	podName    string
	namespace  string
	container  string
}

// NewLogViewer creates a new log viewer
func NewLogViewer() *LogViewer {
	return &LogViewer{
		lines:     make([]string, 0),
		filter:    "",
		scrollPos: 0,
		following: false,
		styles:    visual.DefaultStyles(),
		palette:   visual.DefaultPalette(),
	}
}

// LoadLogs loads logs from a pod
func (lv *LogViewer) LoadLogs(clientset *kubernetes.Clientset, namespace, podName, container string, tailLines int64) error {
	lv.namespace = namespace
	lv.podName = podName
	lv.container = container

	opts := &corev1.PodLogOptions{
		Container: container,
		TailLines: &tailLines,
		Follow:    false,
	}

	req := clientset.CoreV1().Pods(namespace).GetLogs(podName, opts)
	stream, err := req.Stream(context.Background())
	if err != nil {
		return fmt.Errorf("failed to get log stream: %w", err)
	}
	defer stream.Close()

	// Read all logs
	data, err := io.ReadAll(stream)
	if err != nil {
		return fmt.Errorf("failed to read logs: %w", err)
	}

	// Split into lines
	lv.lines = strings.Split(string(data), "\n")

	// Auto-scroll to bottom
	if lv.following {
		lv.scrollPos = len(lv.lines) - 1
	}

	return nil
}

// SetFilter sets the log filter
func (lv *LogViewer) SetFilter(filter string) {
	lv.filter = filter
}

// ClearFilter clears the log filter
func (lv *LogViewer) ClearFilter() {
	lv.filter = ""
}

// ToggleFollow toggles auto-follow mode
func (lv *LogViewer) ToggleFollow() {
	lv.following = !lv.following
	if lv.following {
		lv.scrollPos = len(lv.lines) - 1
	}
}

// ScrollUp scrolls up
func (lv *LogViewer) ScrollUp() {
	if lv.scrollPos > 0 {
		lv.scrollPos--
		lv.following = false
	}
}

// ScrollDown scrolls down
func (lv *LogViewer) ScrollDown() {
	if lv.scrollPos < len(lv.lines)-1 {
		lv.scrollPos++
	}
}

// PageUp scrolls up by page
func (lv *LogViewer) PageUp(pageSize int) {
	lv.scrollPos -= pageSize
	if lv.scrollPos < 0 {
		lv.scrollPos = 0
	}
	lv.following = false
}

// PageDown scrolls down by page
func (lv *LogViewer) PageDown(pageSize int) {
	lv.scrollPos += pageSize
	if lv.scrollPos >= len(lv.lines) {
		lv.scrollPos = len(lv.lines) - 1
	}
}

// Render renders the log viewer
func (lv *LogViewer) Render(width, height int) string {
	var output strings.Builder

	// Header
	gradient := lv.palette.PrimaryGradient()
	title := fmt.Sprintf("📜 LOGS: %s/%s", lv.namespace, lv.podName)
	if lv.container != "" {
		title += fmt.Sprintf(" [%s]", lv.container)
	}
	output.WriteString(visual.GradientText(title, gradient))
	output.WriteString("\n")
	output.WriteString(lv.styles.Muted.Render(strings.Repeat("─", width)))
	output.WriteString("\n")

	// Filter info
	if lv.filter != "" {
		output.WriteString(lv.styles.Warning.Render(fmt.Sprintf("🔍 Filter: %s", lv.filter)))
		output.WriteString("\n")
	}

	// Following indicator
	if lv.following {
		output.WriteString(lv.styles.Success.Render("📡 Following (auto-scroll enabled)"))
		output.WriteString("\n")
	}

	// Calculate visible area
	headerLines := 3
	if lv.filter != "" {
		headerLines++
	}
	if lv.following {
		headerLines++
	}

	visibleLines := height - headerLines - 2 // Leave space for footer

	// Get filtered lines
	displayLines := lv.getFilteredLines()

	if len(displayLines) == 0 {
		output.WriteString(lv.styles.Muted.Render("No logs available"))
		if lv.filter != "" {
			output.WriteString(lv.styles.Muted.Render(" (try clearing filter with Ctrl+X)"))
		}
		return output.String()
	}

	// Calculate scroll window
	startIdx := lv.scrollPos
	if startIdx < 0 {
		startIdx = 0
	}
	endIdx := startIdx + visibleLines
	if endIdx > len(displayLines) {
		endIdx = len(displayLines)
		startIdx = endIdx - visibleLines
		if startIdx < 0 {
			startIdx = 0
		}
	}

	// Render visible lines
	for i := startIdx; i < endIdx && i < len(displayLines); i++ {
		line := displayLines[i]

		// Highlight filter matches
		if lv.filter != "" {
			line = lv.highlightFilter(line)
		}

		output.WriteString(line)
		output.WriteString("\n")
	}

	// Footer with scroll position
	footer := fmt.Sprintf("Lines %d-%d of %d", startIdx+1, endIdx, len(displayLines))
	if len(lv.lines) != len(displayLines) {
		footer += fmt.Sprintf(" (filtered from %d)", len(lv.lines))
	}
	output.WriteString("\n")
	output.WriteString(lv.styles.Muted.Render(footer))

	return output.String()
}

// getFilteredLines returns lines matching the current filter
func (lv *LogViewer) getFilteredLines() []string {
	if lv.filter == "" {
		return lv.lines
	}

	filtered := make([]string, 0)
	filterLower := strings.ToLower(lv.filter)

	for _, line := range lv.lines {
		if strings.Contains(strings.ToLower(line), filterLower) {
			filtered = append(filtered, line)
		}
	}

	return filtered
}

// highlightFilter highlights the filter text in a line
func (lv *LogViewer) highlightFilter(line string) string {
	if lv.filter == "" {
		return line
	}

	// Case-insensitive highlighting
	lowerLine := strings.ToLower(line)
	lowerFilter := strings.ToLower(lv.filter)

	idx := strings.Index(lowerLine, lowerFilter)
	if idx == -1 {
		return line
	}

	// Build highlighted line
	before := line[:idx]
	match := line[idx : idx+len(lv.filter)]
	after := line[idx+len(lv.filter):]

	highlighted := before +
		lv.styles.Warning.Bold(true).Render(match) +
		after

	return highlighted
}

// GetInfo returns current log viewer info
func (lv *LogViewer) GetInfo() string {
	return fmt.Sprintf("%s/%s", lv.namespace, lv.podName)
}
