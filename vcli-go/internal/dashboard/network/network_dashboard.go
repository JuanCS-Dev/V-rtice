package network

import (
	"context"
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/dashboard"
)

// NetworkDashboard monitors network metrics and connections
type NetworkDashboard struct {
	id               string
	focused          bool
	width            int
	height           int
	styles           dashboard.DashboardStyles
	data             *NetworkData
	refreshTicker    *time.Ticker
}

// NetworkData holds network metrics
type NetworkData struct {
	// Bandwidth (Mbps)
	InboundBandwidth  float64
	OutboundBandwidth float64
	TotalBandwidth    float64
	BandwidthHistory  []BandwidthSample

	// Connections
	ActiveConnections    int
	EstablishedConns     int
	ListeningPorts       int
	TimeWaitConns        int
	TopConnections       []Connection

	// Latency
	AverageLatency    time.Duration
	MinLatency        time.Duration
	MaxLatency        time.Duration
	PacketLoss        float64
	LatencyHistory    []float64

	// Traffic
	BytesReceived     uint64
	BytesSent         uint64
	PacketsReceived   uint64
	PacketsSent       uint64

	// Errors
	DroppedPackets    uint64
	ErrorCount        uint64

	LastUpdate        time.Time
}

// BandwidthSample represents bandwidth at a point in time
type BandwidthSample struct {
	Timestamp time.Time
	Inbound   float64
	Outbound  float64
}

// Connection represents network connection
type Connection struct {
	LocalAddr   string
	RemoteAddr  string
	State       string
	Protocol    string
	BytesSent   uint64
	BytesRecv   uint64
	Duration    time.Duration
}

// New creates a new network monitor dashboard
func New() *NetworkDashboard {
	return &NetworkDashboard{
		id:     "network-dashboard",
		styles: dashboard.DefaultStyles(),
		data: &NetworkData{
			BandwidthHistory: make([]BandwidthSample, 0),
			TopConnections:   make([]Connection, 0),
			LatencyHistory:   make([]float64, 0),
		},
	}
}

// Init initializes the dashboard
func (d *NetworkDashboard) Init() tea.Cmd {
	// Start refresh ticker (every 2 seconds for network metrics)
	d.refreshTicker = time.NewTicker(2 * time.Second)

	return tea.Batch(
		d.refresh(),
		d.tickRefresh(),
	)
}

// Update handles messages
func (d *NetworkDashboard) Update(msg tea.Msg) (dashboard.Dashboard, tea.Cmd) {
	switch msg := msg.(type) {
	case dashboard.RefreshMsg:
		if msg.DashboardID == d.id {
			return d, d.refresh()
		}

	case dashboard.DataMsg:
		if msg.DashboardID == d.id {
			if data, ok := msg.Data.(*NetworkData); ok {
				d.data = data
				d.updateCharts()
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

type tickMsg time.Time

func (d *NetworkDashboard) tickRefresh() tea.Cmd {
	return func() tea.Msg {
		time.Sleep(2 * time.Second)
		return tickMsg(time.Now())
	}
}

// View renders the dashboard
func (d *NetworkDashboard) View() string {
	if d.data == nil {
		return d.styles.Error.Render("No network data")
	}

	var b strings.Builder

	// Bandwidth overview
	b.WriteString(d.renderBandwidth())
	b.WriteString("\n\n")

	// Connections summary
	b.WriteString(d.renderConnections())
	b.WriteString("\n\n")

	// Latency and packet loss
	b.WriteString(d.renderLatency())
	b.WriteString("\n\n")

	// Top connections
	b.WriteString(d.renderTopConnections())
	b.WriteString("\n")

	b.WriteString(d.styles.Label.Render(fmt.Sprintf("Last update: %s", d.data.LastUpdate.Format("15:04:05"))))

	return b.String()
}

// renderBandwidth renders bandwidth metrics
func (d *NetworkDashboard) renderBandwidth() string {
	var b strings.Builder

	b.WriteString(d.styles.Title.Render("Bandwidth"))
	b.WriteString("\n")

	// Inbound
	inStyle := d.getBandwidthStyle(d.data.InboundBandwidth)
	b.WriteString(d.styles.Label.Render("↓ In:  "))
	b.WriteString(inStyle.Render(fmt.Sprintf("%7.2f Mbps", d.data.InboundBandwidth)))
	b.WriteString("\n")

	// Outbound
	outStyle := d.getBandwidthStyle(d.data.OutboundBandwidth)
	b.WriteString(d.styles.Label.Render("↑ Out: "))
	b.WriteString(outStyle.Render(fmt.Sprintf("%7.2f Mbps", d.data.OutboundBandwidth)))
	b.WriteString("\n")

	// Total traffic
	b.WriteString(d.styles.Label.Render("Total: "))
	b.WriteString(d.styles.Value.Render(fmt.Sprintf("%7.2f Mbps", d.data.TotalBandwidth)))
	b.WriteString("\n\n")

	// Data transferred
	b.WriteString(d.styles.Label.Render(fmt.Sprintf("RX: %s  TX: %s",
		formatBytes(d.data.BytesReceived),
		formatBytes(d.data.BytesSent),
	)))

	return b.String()
}

// renderConnections renders connection metrics
func (d *NetworkDashboard) renderConnections() string {
	var b strings.Builder

	b.WriteString(d.styles.Title.Render("Connections"))
	b.WriteString("\n")

	// Active connections
	b.WriteString(d.styles.Label.Render("Active:      "))
	connStyle := d.styles.Value
	if d.data.ActiveConnections > 1000 {
		connStyle = d.styles.Warning
	}
	if d.data.ActiveConnections > 5000 {
		connStyle = d.styles.Error
	}
	b.WriteString(connStyle.Render(fmt.Sprintf("%d", d.data.ActiveConnections)))
	b.WriteString("\n")

	// Established
	b.WriteString(d.styles.Label.Render("Established: "))
	b.WriteString(d.styles.Value.Render(fmt.Sprintf("%d", d.data.EstablishedConns)))
	b.WriteString("\n")

	// Listening
	b.WriteString(d.styles.Label.Render("Listening:   "))
	b.WriteString(d.styles.Value.Render(fmt.Sprintf("%d", d.data.ListeningPorts)))
	b.WriteString("\n")

	// TIME_WAIT
	b.WriteString(d.styles.Label.Render("TIME_WAIT:   "))
	waitStyle := d.styles.Value
	if d.data.TimeWaitConns > 500 {
		waitStyle = d.styles.Warning
	}
	b.WriteString(waitStyle.Render(fmt.Sprintf("%d", d.data.TimeWaitConns)))

	return b.String()
}

// renderLatency renders latency and packet loss
func (d *NetworkDashboard) renderLatency() string {
	var b strings.Builder

	b.WriteString(d.styles.Title.Render("Latency & Quality"))
	b.WriteString("\n")

	// Average latency
	latencyStyle := d.styles.Success
	if d.data.AverageLatency > 100*time.Millisecond {
		latencyStyle = d.styles.Warning
	}
	if d.data.AverageLatency > 500*time.Millisecond {
		latencyStyle = d.styles.Error
	}

	b.WriteString(d.styles.Label.Render("Avg:  "))
	b.WriteString(latencyStyle.Render(fmt.Sprintf("%6s", formatLatency(d.data.AverageLatency))))
	b.WriteString("  ")

	// Min/Max
	b.WriteString(d.styles.Label.Render(fmt.Sprintf("[%s - %s]",
		formatLatency(d.data.MinLatency),
		formatLatency(d.data.MaxLatency),
	)))
	b.WriteString("\n")

	// Packet loss
	lossStyle := d.styles.Success
	if d.data.PacketLoss > 1.0 {
		lossStyle = d.styles.Warning
	}
	if d.data.PacketLoss > 5.0 {
		lossStyle = d.styles.Error
	}

	b.WriteString(d.styles.Label.Render("Loss: "))
	b.WriteString(lossStyle.Render(fmt.Sprintf("%5.2f%%", d.data.PacketLoss)))
	b.WriteString("\n")

	// Errors
	if d.data.ErrorCount > 0 || d.data.DroppedPackets > 0 {
		b.WriteString(d.styles.Label.Render("Errors:  "))
		b.WriteString(d.styles.Error.Render(fmt.Sprintf("%d", d.data.ErrorCount)))
		b.WriteString("  ")
		b.WriteString(d.styles.Label.Render("Dropped: "))
		b.WriteString(d.styles.Error.Render(fmt.Sprintf("%d", d.data.DroppedPackets)))
	}

	return b.String()
}

// renderTopConnections renders top active connections
func (d *NetworkDashboard) renderTopConnections() string {
	var b strings.Builder

	b.WriteString(d.styles.Title.Render("Top Connections"))
	b.WriteString("\n")

	if len(d.data.TopConnections) == 0 {
		b.WriteString(d.styles.Label.Render("No active connections"))
		return b.String()
	}

	// Show top 5 connections
	maxDisplay := 5
	if len(d.data.TopConnections) < maxDisplay {
		maxDisplay = len(d.data.TopConnections)
	}

	for i := 0; i < maxDisplay; i++ {
		conn := d.data.TopConnections[i]

		// Protocol icon
		protocolIcon := "●"
		if conn.Protocol == "udp" {
			protocolIcon = "◇"
		}

		// State indicator
		stateStyle := d.styles.Success
		if conn.State == "TIME_WAIT" || conn.State == "CLOSE_WAIT" {
			stateStyle = d.styles.Warning
		}

		b.WriteString(fmt.Sprintf("%s %s %-25s → %-25s %s %s\n",
			d.styles.Label.Render(protocolIcon),
			d.styles.Value.Render(fmt.Sprintf("%-4s", conn.Protocol)),
			truncate(conn.LocalAddr, 25),
			truncate(conn.RemoteAddr, 25),
			stateStyle.Render(fmt.Sprintf("%-11s", conn.State)),
			d.styles.Label.Render(formatBytes(conn.BytesSent+conn.BytesRecv)),
		))
	}

	return b.String()
}

// updateCharts updates chart data
func (d *NetworkDashboard) updateCharts() {
	// Charts removed - no-op for now
}

// refresh fetches new network data
func (d *NetworkDashboard) refresh() tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()

		data := d.fetchNetworkData(ctx)

		return dashboard.DataMsg{
			DashboardID: d.id,
			Data:        data,
		}
	}
}

// fetchNetworkData fetches network metrics (mock data)
func (d *NetworkDashboard) fetchNetworkData(ctx context.Context) *NetworkData {
	// In production, would query actual network interfaces and netstat
	// For now, generate realistic mock data

	data := &NetworkData{
		LastUpdate: time.Now(),
	}

	// Mock bandwidth (simulate varying traffic)
	baseIn := 45.5
	baseOut := 23.2
	variation := float64(time.Now().Unix()%10) * 5.0

	data.InboundBandwidth = baseIn + variation
	data.OutboundBandwidth = baseOut + variation/2
	data.TotalBandwidth = data.InboundBandwidth + data.OutboundBandwidth

	// Mock bandwidth history (last 20 samples)
	for i := 0; i < 20; i++ {
		sample := BandwidthSample{
			Timestamp: time.Now().Add(-time.Duration(20-i) * 2 * time.Second),
			Inbound:   baseIn + float64(i)*2.0,
			Outbound:  baseOut + float64(i)*1.0,
		}
		data.BandwidthHistory = append(data.BandwidthHistory, sample)
	}

	// Mock connections
	data.ActiveConnections = 234
	data.EstablishedConns = 187
	data.ListeningPorts = 45
	data.TimeWaitConns = 23

	// Mock latency
	data.AverageLatency = 45 * time.Millisecond
	data.MinLatency = 12 * time.Millisecond
	data.MaxLatency = 234 * time.Millisecond
	data.PacketLoss = 0.2

	// Mock latency history
	for i := 0; i < 30; i++ {
		data.LatencyHistory = append(data.LatencyHistory, float64(30+i*2))
	}

	// Mock traffic
	data.BytesReceived = 15_234_567_890
	data.BytesSent = 8_123_456_789
	data.PacketsReceived = 12_345_678
	data.PacketsSent = 9_876_543

	// Mock errors
	data.DroppedPackets = 12
	data.ErrorCount = 3

	// Mock top connections
	data.TopConnections = []Connection{
		{
			LocalAddr:  "10.0.1.50:443",
			RemoteAddr: "172.16.34.12:52341",
			State:      "ESTABLISHED",
			Protocol:   "tcp",
			BytesSent:  1_234_567,
			BytesRecv:  8_765_432,
			Duration:   15 * time.Minute,
		},
		{
			LocalAddr:  "10.0.1.50:8080",
			RemoteAddr: "192.168.1.100:48392",
			State:      "ESTABLISHED",
			Protocol:   "tcp",
			BytesSent:  987_654,
			BytesRecv:  2_345_678,
			Duration:   8 * time.Minute,
		},
		{
			LocalAddr:  "10.0.1.50:9090",
			RemoteAddr: "10.0.2.25:39201",
			State:      "TIME_WAIT",
			Protocol:   "tcp",
			BytesSent:  45_678,
			BytesRecv:  123_456,
			Duration:   1 * time.Minute,
		},
	}

	_ = ctx // Would use for actual system calls

	return data
}

// Helper functions

func (d *NetworkDashboard) getBandwidthStyle(bandwidth float64) lipgloss.Style {
	if bandwidth > 80.0 {
		return d.styles.Warning
	}
	return d.styles.Value
}

func formatBytes(bytes uint64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := uint64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

func formatLatency(d time.Duration) string {
	if d < time.Millisecond {
		return fmt.Sprintf("%dµs", d.Microseconds())
	}
	if d < time.Second {
		return fmt.Sprintf("%dms", d.Milliseconds())
	}
	return fmt.Sprintf("%.1fs", d.Seconds())
}

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return s[:max-3] + "..."
}

// Dashboard interface implementation

func (d *NetworkDashboard) ID() string      { return d.id }
func (d *NetworkDashboard) Title() string   { return "Network Monitor" }
func (d *NetworkDashboard) Focus()          { d.focused = true }
func (d *NetworkDashboard) Blur()           { d.focused = false }
func (d *NetworkDashboard) IsFocused() bool { return d.focused }

func (d *NetworkDashboard) Resize(width, height int) {
	d.width = width
	d.height = height
}
