package services

import (
	"context"
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/dashboard"
)

// ServicesDashboard monitors health of all Vértice services
type ServicesDashboard struct {
	id            string
	focused       bool
	width         int
	height        int
	styles        dashboard.DashboardStyles
	data          *ServicesData
	refreshTicker *time.Ticker
}

// ServicesData holds service health metrics
type ServicesData struct {
	Services       []ServiceHealth
	TotalServices  int
	HealthyCount   int
	DegradedCount  int
	UnhealthyCount int
	LastUpdate     time.Time
}

// ServiceHealth represents individual service status
type ServiceHealth struct {
	Name           string
	Status         HealthStatus
	ResponseTime   time.Duration
	Uptime         float64
	ErrorRate      float64
	LastCheck      time.Time
	Endpoint       string
	Version        string
	ResponseHistory []float64 // Last 20 response times for sparkline
}

// HealthStatus represents service health state
type HealthStatus string

const (
	HealthStatusHealthy  HealthStatus = "healthy"
	HealthStatusDegraded HealthStatus = "degraded"
	HealthStatusUnhealthy HealthStatus = "unhealthy"
	HealthStatusUnknown  HealthStatus = "unknown"
)

// New creates a new services health dashboard
func New() *ServicesDashboard {
	return &ServicesDashboard{
		id:     "services-dashboard",
		styles: dashboard.DefaultStyles(),
		data: &ServicesData{
			Services: make([]ServiceHealth, 0),
		},
	}
}

// Init initializes the dashboard
func (d *ServicesDashboard) Init() tea.Cmd {
	// Start refresh ticker (every 5 seconds)
	d.refreshTicker = time.NewTicker(5 * time.Second)

	return tea.Batch(
		d.refresh(),
		d.tickRefresh(),
	)
}

// Update handles messages
func (d *ServicesDashboard) Update(msg tea.Msg) (dashboard.Dashboard, tea.Cmd) {
	switch msg := msg.(type) {
	case dashboard.RefreshMsg:
		if msg.DashboardID == d.id {
			return d, d.refresh()
		}

	case dashboard.DataMsg:
		if msg.DashboardID == d.id {
			if data, ok := msg.Data.(*ServicesData); ok {
				d.data = data
			}
		}

	case tea.KeyMsg:
		if d.focused {
			switch msg.String() {
			case "r":
				return d, d.refresh()
			}
		}

	case tickMsg:
		return d, tea.Batch(
			d.refresh(),
			d.tickRefresh(),
		)
	}

	return d, nil
}

// tickMsg triggers periodic refresh
type tickMsg time.Time

// tickRefresh creates periodic refresh command
func (d *ServicesDashboard) tickRefresh() tea.Cmd {
	return func() tea.Msg {
		time.Sleep(5 * time.Second)
		return tickMsg(time.Now())
	}
}

// View renders the dashboard
func (d *ServicesDashboard) View() string {
	if d.data == nil {
		return d.styles.Error.Render("No data")
	}

	var b strings.Builder

	// Header - Overall status
	b.WriteString(d.renderHeader())
	b.WriteString("\n\n")

	// Service grid - compact format (Sampler style)
	b.WriteString(d.renderServiceGrid())

	b.WriteString("\n")
	b.WriteString(d.styles.Label.Render(fmt.Sprintf("Last update: %s", d.data.LastUpdate.Format("15:04:05"))))
	b.WriteString(d.styles.Label.Render(" | Press 'r' to refresh"))

	return b.String()
}

// renderHeader renders overall health summary
func (d *ServicesDashboard) renderHeader() string {
	var b strings.Builder

	// Total services
	b.WriteString(d.styles.Label.Render("Services: "))
	b.WriteString(d.styles.Value.Render(fmt.Sprintf("%d", d.data.TotalServices)))
	b.WriteString("  ")

	// Healthy
	b.WriteString(d.styles.Success.Render(fmt.Sprintf("✓ %d", d.data.HealthyCount)))
	b.WriteString("  ")

	// Degraded
	if d.data.DegradedCount > 0 {
		b.WriteString(d.styles.Warning.Render(fmt.Sprintf("⚠ %d", d.data.DegradedCount)))
		b.WriteString("  ")
	}

	// Unhealthy
	if d.data.UnhealthyCount > 0 {
		b.WriteString(d.styles.Error.Render(fmt.Sprintf("✗ %d", d.data.UnhealthyCount)))
	}

	return b.String()
}

// renderServiceGrid renders services in compact grid
func (d *ServicesDashboard) renderServiceGrid() string {
	var b strings.Builder

	for _, svc := range d.data.Services {
		// Status icon
		icon := d.getStatusIcon(svc.Status)
		statusStyle := d.getStatusStyle(svc.Status)

		// Service name (fixed width for alignment)
		name := fmt.Sprintf("%-20s", truncate(svc.Name, 20))

		// Response time
		responseTime := fmt.Sprintf("%6s", formatDuration(svc.ResponseTime))

		// Uptime
		uptime := fmt.Sprintf("%5.1f%%", svc.Uptime)

		// Error rate
		errorRate := fmt.Sprintf("%4.1f%%", svc.ErrorRate)
		errorStyle := d.styles.Success
		if svc.ErrorRate > 5.0 {
			errorStyle = d.styles.Error
		} else if svc.ErrorRate > 1.0 {
			errorStyle = d.styles.Warning
		}

		// Sparkline for response time trend
		sparklineStr := d.renderSparkline(svc.ResponseHistory)

		// Build row
		b.WriteString(statusStyle.Render(icon))
		b.WriteString(" ")
		b.WriteString(d.styles.Value.Render(name))
		b.WriteString(" ")
		b.WriteString(d.styles.Label.Render("RT:"))
		b.WriteString(d.styles.Value.Render(responseTime))
		b.WriteString(" ")
		b.WriteString(d.styles.Label.Render("Up:"))
		b.WriteString(d.styles.Success.Render(uptime))
		b.WriteString(" ")
		b.WriteString(d.styles.Label.Render("Err:"))
		b.WriteString(errorStyle.Render(errorRate))
		b.WriteString("  ")
		b.WriteString(sparklineStr)
		b.WriteString("\n")
	}

	return b.String()
}

// renderSparkline renders simple ASCII sparkline for response time history
func (d *ServicesDashboard) renderSparkline(history []float64) string {
	if len(history) == 0 {
		return strings.Repeat("─", 10)
	}

	// Simple ASCII sparkline using Unicode block characters
	chars := []rune{'▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'}

	// Find min/max for normalization
	min, max := history[0], history[0]
	for _, v := range history {
		if v < min {
			min = v
		}
		if v > max {
			max = v
		}
	}

	// Build sparkline
	var b strings.Builder
	for i := 0; i < 10 && i < len(history); i++ {
		normalized := 0.0
		if max > min {
			normalized = (history[i] - min) / (max - min)
		}
		idx := int(normalized * float64(len(chars)-1))
		if idx < 0 {
			idx = 0
		}
		if idx >= len(chars) {
			idx = len(chars) - 1
		}
		b.WriteRune(chars[idx])
	}

	// Pad if needed
	for b.Len() < 10 {
		b.WriteRune('─')
	}

	return b.String()
}

// getStatusIcon returns icon for status
func (d *ServicesDashboard) getStatusIcon(status HealthStatus) string {
	switch status {
	case HealthStatusHealthy:
		return "●"
	case HealthStatusDegraded:
		return "◐"
	case HealthStatusUnhealthy:
		return "○"
	default:
		return "?"
	}
}

// getStatusStyle returns lipgloss.Style for status
func (d *ServicesDashboard) getStatusStyle(status HealthStatus) lipgloss.Style {
	switch status {
	case HealthStatusHealthy:
		return d.styles.Success
	case HealthStatusDegraded:
		return d.styles.Warning
	case HealthStatusUnhealthy:
		return d.styles.Error
	default:
		return d.styles.Value
	}
}


// refresh fetches new service health data
func (d *ServicesDashboard) refresh() tea.Cmd {
	return func() tea.Msg {
		data := &ServicesData{
			Services:   make([]ServiceHealth, 0),
			LastUpdate: time.Now(),
		}

		// List of Vértice services to monitor
		services := []string{
			"maximus_core",
			"maximus_oraculo",
			"maximus_orchestrator",
			"atlas",
			"maba",
			"penelope",
			"nis",
			"thalamus",
			"mvp",
		}

		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()

		for _, serviceName := range services {
			health := d.checkServiceHealth(ctx, serviceName)
			data.Services = append(data.Services, health)

			// Update counters
			data.TotalServices++
			switch health.Status {
			case HealthStatusHealthy:
				data.HealthyCount++
			case HealthStatusDegraded:
				data.DegradedCount++
			case HealthStatusUnhealthy:
				data.UnhealthyCount++
			}
		}

		return dashboard.DataMsg{
			DashboardID: d.id,
			Data:        data,
		}
	}
}

// checkServiceHealth checks individual service health
func (d *ServicesDashboard) checkServiceHealth(ctx context.Context, serviceName string) ServiceHealth {
	endpoint := config.GetEndpoint(serviceName)

	start := time.Now()

	// Mock health check (in production, would call /health endpoint)
	// For now, simulate with random-ish data based on service name
	health := ServiceHealth{
		Name:            serviceName,
		Endpoint:        endpoint,
		LastCheck:       time.Now(),
		ResponseHistory: make([]float64, 0),
	}

	// Simulate response time (would be actual HTTP call in production)
	responseTime := 50 * time.Millisecond
	health.ResponseTime = responseTime

	// Simulate uptime (would come from service metrics)
	health.Uptime = 99.9

	// Simulate error rate
	health.ErrorRate = 0.1

	// Determine status
	if health.Uptime >= 99.0 && health.ErrorRate < 1.0 {
		health.Status = HealthStatusHealthy
	} else if health.Uptime >= 95.0 && health.ErrorRate < 5.0 {
		health.Status = HealthStatusDegraded
	} else {
		health.Status = HealthStatusUnhealthy
	}

	// Generate mock response history for sparkline
	for i := 0; i < 20; i++ {
		health.ResponseHistory = append(health.ResponseHistory, float64(40+i*2))
	}

	_ = start // Would use for actual timing

	return health
}

// Helper functions

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return s[:max-3] + "..."
}

func formatDuration(d time.Duration) string {
	if d < time.Millisecond {
		return fmt.Sprintf("%dµs", d.Microseconds())
	}
	if d < time.Second {
		return fmt.Sprintf("%dms", d.Milliseconds())
	}
	return fmt.Sprintf("%.1fs", d.Seconds())
}

// Dashboard interface implementation

func (d *ServicesDashboard) ID() string           { return d.id }
func (d *ServicesDashboard) Title() string        { return "Services Health" }
func (d *ServicesDashboard) Focus()               { d.focused = true }
func (d *ServicesDashboard) Blur()                { d.focused = false }
func (d *ServicesDashboard) IsFocused() bool      { return d.focused }

func (d *ServicesDashboard) Resize(width, height int) {
	d.width = width
	d.height = height
}
