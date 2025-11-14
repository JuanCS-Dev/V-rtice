package threat

import (
	"context"
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/NimbleMarkets/ntcharts/barchart"
	"github.com/NimbleMarkets/ntcharts/linechart"
	"github.com/verticedev/vcli-go/internal/dashboard"
)

// ThreatDashboard displays threat intelligence and security metrics
type ThreatDashboard struct {
	id               string
	focused          bool
	width            int
	height           int
	styles           dashboard.DashboardStyles
	data             *ThreatData
	severityChart    *barchart.BarChart
	timelineChart    *linechart.LineChart
	refreshTicker    *time.Ticker
}

// ThreatData holds threat intelligence data
type ThreatData struct {
	ActiveThreats     int
	ThreatsByLevel    map[ThreatLevel]int
	RecentThreats     []ThreatEvent
	APTCampaigns      []APTCampaign
	IOCs              []IOC
	ThreatScore       float64
	LastUpdate        time.Time
	ThreatTrend       []float64 // Last 24 hours
}

// ThreatEvent represents a detected threat
type ThreatEvent struct {
	ID          string
	Type        ThreatType
	Level       ThreatLevel
	Source      string
	Target      string
	Description string
	Timestamp   time.Time
	Mitigated   bool
	MITRE       string // MITRE ATT&CK technique
}

// ThreatType categorizes threat types
type ThreatType string

const (
	ThreatTypeMalware       ThreatType = "malware"
	ThreatTypePhishing      ThreatType = "phishing"
	ThreatTypeExfiltration  ThreatType = "exfiltration"
	ThreatTypeLateralMove   ThreatType = "lateral_movement"
	ThreatTypePrivEsc       ThreatType = "privilege_escalation"
	ThreatTypePersistence   ThreatType = "persistence"
	ThreatTypeRecon         ThreatType = "reconnaissance"
	ThreatTypeDDoS          ThreatType = "ddos"
)

// ThreatLevel represents severity
type ThreatLevel string

const (
	ThreatLevelCritical ThreatLevel = "critical"
	ThreatLevelHigh     ThreatLevel = "high"
	ThreatLevelMedium   ThreatLevel = "medium"
	ThreatLevelLow      ThreatLevel = "low"
	ThreatLevelInfo     ThreatLevel = "info"
)

// APTCampaign represents Advanced Persistent Threat campaign
type APTCampaign struct {
	Name        string
	Group       string // APT group (e.g., APT28, Lazarus)
	Active      bool
	StartDate   time.Time
	Techniques  []string // MITRE ATT&CK techniques
	Targets     []string
	Confidence  float64 // 0-100
}

// IOC represents Indicator of Compromise
type IOC struct {
	Type       IOCType
	Value      string
	Threat     string
	FirstSeen  time.Time
	Confidence float64
}

// IOCType categorizes IOCs
type IOCType string

const (
	IOCTypeIP       IOCType = "ip"
	IOCTypeDomain   IOCType = "domain"
	IOCTypeHash     IOCType = "hash"
	IOCTypeEmail    IOCType = "email"
	IOCTypeURL      IOCType = "url"
)

// New creates a new threat intelligence dashboard
func New() *ThreatDashboard {
	return &ThreatDashboard{
		id:     "threat-dashboard",
		styles: dashboard.DefaultStyles(),
		data: &ThreatData{
			ThreatsByLevel: make(map[ThreatLevel]int),
			RecentThreats:  make([]ThreatEvent, 0),
			APTCampaigns:   make([]APTCampaign, 0),
			IOCs:           make([]IOC, 0),
			ThreatTrend:    make([]float64, 0),
		},
	}
}

// Init initializes the dashboard
func (d *ThreatDashboard) Init() tea.Cmd {
	// Initialize charts
	d.severityChart = barchart.New(d.width/2-4, d.height/3)
	d.timelineChart = linechart.New(d.width-4, d.height/4)

	// Start refresh ticker (every 10 seconds for threat intel)
	d.refreshTicker = time.NewTicker(10 * time.Second)

	return tea.Batch(
		d.refresh(),
		d.tickRefresh(),
	)
}

// Update handles messages
func (d *ThreatDashboard) Update(msg tea.Msg) (dashboard.Dashboard, tea.Cmd) {
	switch msg := msg.(type) {
	case dashboard.RefreshMsg:
		if msg.DashboardID == d.id {
			return d, d.refresh()
		}

	case dashboard.DataMsg:
		if msg.DashboardID == d.id {
			if data, ok := msg.Data.(*ThreatData); ok {
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

func (d *ThreatDashboard) tickRefresh() tea.Cmd {
	return func() tea.Msg {
		time.Sleep(10 * time.Second)
		return tickMsg(time.Now())
	}
}

// View renders the dashboard
func (d *ThreatDashboard) View() string {
	if d.data == nil {
		return d.styles.Error.Render("No threat data")
	}

	var b strings.Builder

	// Header - Threat score and summary
	b.WriteString(d.renderHeader())
	b.WriteString("\n\n")

	// Active threats by severity
	b.WriteString(d.renderThreatSummary())
	b.WriteString("\n\n")

	// Recent threat events
	b.WriteString(d.renderRecentThreats())
	b.WriteString("\n\n")

	// APT campaigns
	if len(d.data.APTCampaigns) > 0 {
		b.WriteString(d.renderAPTCampaigns())
		b.WriteString("\n\n")
	}

	// Critical IOCs
	if len(d.data.IOCs) > 0 {
		b.WriteString(d.renderIOCs())
		b.WriteString("\n")
	}

	b.WriteString(d.styles.Label.Render(fmt.Sprintf("Last update: %s", d.data.LastUpdate.Format("15:04:05"))))

	return b.String()
}

// renderHeader renders threat score and status
func (d *ThreatDashboard) renderHeader() string {
	var b strings.Builder

	// Threat score (0-100)
	scoreStyle := d.styles.Success
	scoreIcon := "●"
	if d.data.ThreatScore >= 70 {
		scoreStyle = d.styles.Error
		scoreIcon = "⬤"
	} else if d.data.ThreatScore >= 40 {
		scoreStyle = d.styles.Warning
		scoreIcon = "◐"
	}

	b.WriteString(d.styles.Label.Render("Threat Score: "))
	b.WriteString(scoreStyle.Render(fmt.Sprintf("%s %.0f/100", scoreIcon, d.data.ThreatScore)))
	b.WriteString("  ")

	// Active threats
	b.WriteString(d.styles.Label.Render("Active: "))
	activeStyle := d.styles.Value
	if d.data.ActiveThreats > 0 {
		activeStyle = d.styles.Error
	}
	b.WriteString(activeStyle.Render(fmt.Sprintf("%d", d.data.ActiveThreats)))

	return b.String()
}

// renderThreatSummary renders threats by severity
func (d *ThreatDashboard) renderThreatSummary() string {
	var b strings.Builder

	b.WriteString(d.styles.Title.Render("Threats by Severity"))
	b.WriteString("\n")

	levels := []ThreatLevel{
		ThreatLevelCritical,
		ThreatLevelHigh,
		ThreatLevelMedium,
		ThreatLevelLow,
	}

	for _, level := range levels {
		count := d.data.ThreatsByLevel[level]
		if count == 0 {
			continue
		}

		style := d.getLevelStyle(level)
		icon := d.getLevelIcon(level)

		b.WriteString(fmt.Sprintf("%s %s %s\n",
			style.Render(icon),
			d.styles.Label.Render(fmt.Sprintf("%-10s:", string(level))),
			style.Render(fmt.Sprintf("%d", count)),
		))
	}

	return b.String()
}

// renderRecentThreats renders recent threat events
func (d *ThreatDashboard) renderRecentThreats() string {
	var b strings.Builder

	b.WriteString(d.styles.Title.Render("Recent Threats"))
	b.WriteString("\n")

	if len(d.data.RecentThreats) == 0 {
		b.WriteString(d.styles.Success.Render("✓ No recent threats detected"))
		return b.String()
	}

	// Show last 5 threats
	maxDisplay := 5
	if len(d.data.RecentThreats) < maxDisplay {
		maxDisplay = len(d.data.RecentThreats)
	}

	for i := 0; i < maxDisplay; i++ {
		threat := d.data.RecentThreats[i]

		style := d.getLevelStyle(threat.Level)
		statusIcon := "●"
		if threat.Mitigated {
			statusIcon = "✓"
			style = d.styles.Success
		}

		// Time ago
		timeAgo := formatTimeAgo(time.Since(threat.Timestamp))

		// Build line
		b.WriteString(fmt.Sprintf("%s %s %s %s",
			style.Render(statusIcon),
			d.styles.Value.Render(fmt.Sprintf("%-15s", truncate(string(threat.Type), 15))),
			d.styles.Label.Render(truncate(threat.Description, 40)),
			d.styles.Label.Render(fmt.Sprintf("(%s)", timeAgo)),
		))

		if threat.MITRE != "" {
			b.WriteString(fmt.Sprintf(" [%s]", d.styles.Label.Render(threat.MITRE)))
		}

		b.WriteString("\n")
	}

	return b.String()
}

// renderAPTCampaigns renders active APT campaigns
func (d *ThreatDashboard) renderAPTCampaigns() string {
	var b strings.Builder

	b.WriteString(d.styles.Title.Render("APT Campaigns"))
	b.WriteString("\n")

	activeCampaigns := 0
	for _, campaign := range d.data.APTCampaigns {
		if !campaign.Active {
			continue
		}

		activeCampaigns++

		// Confidence indicator
		confStyle := d.styles.Success
		if campaign.Confidence >= 80 {
			confStyle = d.styles.Error
		} else if campaign.Confidence >= 50 {
			confStyle = d.styles.Warning
		}

		b.WriteString(fmt.Sprintf("%s %s %s %s\n",
			d.styles.Error.Render("⚠"),
			d.styles.Value.Render(fmt.Sprintf("%-20s", campaign.Name)),
			d.styles.Label.Render(fmt.Sprintf("Group: %s", campaign.Group)),
			confStyle.Render(fmt.Sprintf("Conf: %.0f%%", campaign.Confidence)),
		))

		// Techniques (first 3)
		if len(campaign.Techniques) > 0 {
			techniques := campaign.Techniques
			if len(techniques) > 3 {
				techniques = techniques[:3]
			}
			b.WriteString(fmt.Sprintf("  %s %s\n",
				d.styles.Label.Render("TTPs:"),
				d.styles.Label.Render(strings.Join(techniques, ", ")),
			))
		}
	}

	if activeCampaigns == 0 {
		b.WriteString(d.styles.Success.Render("✓ No active APT campaigns detected"))
	}

	return b.String()
}

// renderIOCs renders critical IOCs
func (d *ThreatDashboard) renderIOCs() string {
	var b strings.Builder

	b.WriteString(d.styles.Title.Render("Critical IOCs"))
	b.WriteString("\n")

	// Show top 5 IOCs by confidence
	maxDisplay := 5
	if len(d.data.IOCs) < maxDisplay {
		maxDisplay = len(d.data.IOCs)
	}

	for i := 0; i < maxDisplay; i++ {
		ioc := d.data.IOCs[i]

		confStyle := d.styles.Warning
		if ioc.Confidence >= 80 {
			confStyle = d.styles.Error
		}

		b.WriteString(fmt.Sprintf("%s %s %s %s\n",
			confStyle.Render("◆"),
			d.styles.Label.Render(fmt.Sprintf("%-8s", string(ioc.Type))),
			d.styles.Value.Render(truncate(ioc.Value, 30)),
			d.styles.Label.Render(fmt.Sprintf("%.0f%%", ioc.Confidence)),
		))
	}

	return b.String()
}

// updateCharts updates chart data
func (d *ThreatDashboard) updateCharts() {
	if d.severityChart != nil {
		d.severityChart.Clear()
		d.severityChart.Push("Critical", float64(d.data.ThreatsByLevel[ThreatLevelCritical]))
		d.severityChart.Push("High", float64(d.data.ThreatsByLevel[ThreatLevelHigh]))
		d.severityChart.Push("Medium", float64(d.data.ThreatsByLevel[ThreatLevelMedium]))
		d.severityChart.Push("Low", float64(d.data.ThreatsByLevel[ThreatLevelLow]))
	}

	if d.timelineChart != nil && len(d.data.ThreatTrend) > 0 {
		d.timelineChart.Clear()
		for _, val := range d.data.ThreatTrend {
			d.timelineChart.Push(val)
		}
	}
}

// refresh fetches new threat intelligence data
func (d *ThreatDashboard) refresh() tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		data := d.fetchThreatData(ctx)

		return dashboard.DataMsg{
			DashboardID: d.id,
			Data:        data,
		}
	}
}

// fetchThreatData fetches threat intelligence (mock data)
func (d *ThreatDashboard) fetchThreatData(ctx context.Context) *ThreatData {
	// In production, this would query threat intel services
	// For now, generate realistic mock data

	data := &ThreatData{
		LastUpdate:     time.Now(),
		ThreatsByLevel: make(map[ThreatLevel]int),
		RecentThreats:  make([]ThreatEvent, 0),
		APTCampaigns:   make([]APTCampaign, 0),
		IOCs:           make([]IOC, 0),
		ThreatTrend:    make([]float64, 24),
	}

	// Mock threat counts
	data.ThreatsByLevel[ThreatLevelCritical] = 0
	data.ThreatsByLevel[ThreatLevelHigh] = 2
	data.ThreatsByLevel[ThreatLevelMedium] = 5
	data.ThreatsByLevel[ThreatLevelLow] = 12

	data.ActiveThreats = data.ThreatsByLevel[ThreatLevelCritical] + data.ThreatsByLevel[ThreatLevelHigh]

	// Calculate threat score
	data.ThreatScore = float64(data.ThreatsByLevel[ThreatLevelCritical]*25 +
		data.ThreatsByLevel[ThreatLevelHigh]*10 +
		data.ThreatsByLevel[ThreatLevelMedium]*3 +
		data.ThreatsByLevel[ThreatLevelLow]*1)

	// Mock recent threats
	data.RecentThreats = []ThreatEvent{
		{
			ID:          "THR-001",
			Type:        ThreatTypePhishing,
			Level:       ThreatLevelHigh,
			Description: "Spear phishing campaign detected",
			Timestamp:   time.Now().Add(-15 * time.Minute),
			Mitigated:   false,
			MITRE:       "T1566.001",
		},
		{
			ID:          "THR-002",
			Type:        ThreatTypeRecon,
			Level:       ThreatLevelMedium,
			Description: "Port scanning from external IP",
			Timestamp:   time.Now().Add(-45 * time.Minute),
			Mitigated:   true,
			MITRE:       "T1046",
		},
	}

	// Mock APT campaign
	data.APTCampaigns = []APTCampaign{
		{
			Name:       "Operation ShadowSpy",
			Group:      "APT28",
			Active:     true,
			StartDate:  time.Now().Add(-72 * time.Hour),
			Techniques: []string{"T1566.001", "T1059.001", "T1071.001"},
			Confidence: 75.0,
		},
	}

	// Mock IOCs
	data.IOCs = []IOC{
		{
			Type:       IOCTypeIP,
			Value:      "192.0.2.123",
			Threat:     "Known C2 server",
			FirstSeen:  time.Now().Add(-2 * time.Hour),
			Confidence: 85.0,
		},
		{
			Type:       IOCTypeDomain,
			Value:      "malicious-domain.example",
			Threat:     "Phishing infrastructure",
			FirstSeen:  time.Now().Add(-6 * time.Hour),
			Confidence: 90.0,
		},
	}

	// Mock trend (last 24 hours)
	for i := 0; i < 24; i++ {
		data.ThreatTrend[i] = float64(15 + i%5)
	}

	_ = ctx // Would use for actual API calls

	return data
}

// Helper functions

func (d *ThreatDashboard) getLevelStyle(level ThreatLevel) dashboard.DashboardStyles {
	switch level {
	case ThreatLevelCritical:
		return d.styles
	case ThreatLevelHigh:
		return d.styles
	case ThreatLevelMedium:
		return d.styles
	default:
		return d.styles
	}
}

func (d *ThreatDashboard) getLevelIcon(level ThreatLevel) string {
	switch level {
	case ThreatLevelCritical:
		return "⬤"
	case ThreatLevelHigh:
		return "●"
	case ThreatLevelMedium:
		return "◐"
	default:
		return "○"
	}
}

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return s[:max-3] + "..."
}

func formatTimeAgo(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%ds ago", int(d.Seconds()))
	}
	if d < time.Hour {
		return fmt.Sprintf("%dm ago", int(d.Minutes()))
	}
	if d < 24*time.Hour {
		return fmt.Sprintf("%dh ago", int(d.Hours()))
	}
	return fmt.Sprintf("%dd ago", int(d.Hours()/24))
}

// Dashboard interface implementation

func (d *ThreatDashboard) ID() string      { return d.id }
func (d *ThreatDashboard) Title() string   { return "Threat Intelligence" }
func (d *ThreatDashboard) Focus()          { d.focused = true }
func (d *ThreatDashboard) Blur()           { d.focused = false }
func (d *ThreatDashboard) IsFocused() bool { return d.focused }

func (d *ThreatDashboard) Resize(width, height int) {
	d.width = width
	d.height = height
	if d.severityChart != nil {
		d.severityChart = barchart.New(width/2-4, height/3)
	}
	if d.timelineChart != nil {
		d.timelineChart = linechart.New(width-4, height/4)
	}
}
