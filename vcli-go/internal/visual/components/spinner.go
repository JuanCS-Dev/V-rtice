package components

import (
	"fmt"
	"time"

	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/visual"
)

// Spinner represents a loading spinner component
type Spinner struct {
	Frames   []string
	Message  string
	Interval time.Duration
	current  int
	Color    string
}

// NewSpinner creates a new spinner with default braille frames
func NewSpinner(message string) *Spinner {
	return &Spinner{
		Frames:   visual.SpinnerFrames,
		Message:  message,
		Interval: time.Duration(visual.SpinnerInterval) * time.Millisecond,
		current:  0,
		Color:    visual.ColorPrimary,
	}
}

// WithFrames sets custom spinner frames
func (s *Spinner) WithFrames(frames []string) *Spinner {
	s.Frames = frames
	return s
}

// WithInterval sets custom interval
func (s *Spinner) WithInterval(interval time.Duration) *Spinner {
	s.Interval = interval
	return s
}

// WithColor sets spinner color
func (s *Spinner) WithColor(color string) *Spinner {
	s.Color = color
	return s
}

// Next advances to next frame
func (s *Spinner) Next() {
	s.current = (s.current + 1) % len(s.Frames)
}

// Render renders current spinner frame
func (s *Spinner) Render() string {
	if len(s.Frames) == 0 {
		return s.Message
	}

	frame := s.Frames[s.current]

	frameStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(s.Color)).
		Bold(true)

	messageStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color(visual.ColorSecondary))

	return frameStyle.Render(frame) + " " + messageStyle.Render(s.Message)
}

// RenderWithFrame renders specific frame
func (s *Spinner) RenderWithFrame(index int) string {
	if index < 0 || index >= len(s.Frames) {
		return s.Render()
	}

	s.current = index
	return s.Render()
}

// String returns current state as string (for fmt.Print)
func (s *Spinner) String() string {
	return s.Render()
}

// Start starts spinner animation (prints to stdout)
// Returns a channel to stop the spinner
func (s *Spinner) Start() chan<- bool {
	stopChan := make(chan bool)

	go func() {
		ticker := time.NewTicker(s.Interval)
		defer ticker.Stop()

		for {
			select {
			case <-stopChan:
				return
			case <-ticker.C:
				// Clear line and print spinner
				fmt.Printf("\r%s", s.Render())
				s.Next()
			}
		}
	}()

	return stopChan
}

// Stop stops spinner and prints final message
func (s *Spinner) Stop(stopChan chan<- bool, finalMessage string, success bool) {
	stopChan <- true
	close(stopChan)

	// Clear spinner line
	fmt.Print("\r")

	// Print final message
	if success {
		icon := visual.IconSuccess
		iconStyle := lipgloss.NewStyle().
			Foreground(lipgloss.Color(visual.ColorSuccess)).
			Bold(true)
		fmt.Printf("%s %s\n", iconStyle.Render(icon), finalMessage)
	} else {
		icon := visual.IconError
		iconStyle := lipgloss.NewStyle().
			Foreground(lipgloss.Color(visual.ColorDanger)).
			Bold(true)
		fmt.Printf("%s %s\n", iconStyle.Render(icon), finalMessage)
	}
}

// Preset Spinners

// SpinnerDots - Simple dots
var SpinnerDots = []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}

// SpinnerLine - Rotating line
var SpinnerLine = []string{"-", "\\", "|", "/"}

// SpinnerArrow - Circular arrow
var SpinnerArrow = []string{"←", "↖", "↑", "↗", "→", "↘", "↓", "↙"}

// SpinnerBox - Box drawing
var SpinnerBox = []string{"◰", "◳", "◲", "◱"}

// SpinnerCircle - Growing circle
var SpinnerCircle = []string{"◡", "⊙", "◠"}
