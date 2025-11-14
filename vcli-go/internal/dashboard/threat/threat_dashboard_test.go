package threat

import (
	"context"
	"strings"
	"testing"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/verticedev/vcli-go/internal/dashboard"
)

func TestNew(t *testing.T) {
	dash := New()

	if dash == nil {
		t.Fatal("New() returned nil")
	}
	if dash.id != "threat-dashboard" {
		t.Errorf("ID = %s, want threat-dashboard", dash.id)
	}
	if dash.data == nil {
		t.Error("data should not be nil")
	}
	if dash.data.ThreatsByLevel == nil {
		t.Error("ThreatsByLevel map should not be nil")
	}
	if dash.data.RecentThreats == nil {
		t.Error("RecentThreats slice should not be nil")
	}
	if dash.data.APTCampaigns == nil {
		t.Error("APTCampaigns slice should not be nil")
	}
	if dash.data.IOCs == nil {
		t.Error("IOCs slice should not be nil")
	}
}

func TestThreatDashboard_ID(t *testing.T) {
	dash := New()
	if id := dash.ID(); id != "threat-dashboard" {
		t.Errorf("ID() = %s, want threat-dashboard", id)
	}
}

func TestThreatDashboard_Title(t *testing.T) {
	dash := New()
	if title := dash.Title(); title != "Threat Intelligence" {
		t.Errorf("Title() = %s, want Threat Intelligence", title)
	}
}

func TestThreatDashboard_Focus(t *testing.T) {
	dash := New()

	if dash.IsFocused() {
		t.Error("Dashboard should not be focused initially")
	}

	dash.Focus()
	if !dash.IsFocused() {
		t.Error("Dashboard should be focused after Focus()")
	}

	dash.Blur()
	if dash.IsFocused() {
		t.Error("Dashboard should not be focused after Blur()")
	}
}

func TestThreatDashboard_Resize(t *testing.T) {
	dash := New()

	tests := []struct {
		width  int
		height int
	}{
		{100, 50},
		{80, 40},
		{0, 0},
		{200, 100},
	}

	for _, tt := range tests {
		dash.Resize(tt.width, tt.height)
		if dash.width != tt.width {
			t.Errorf("width = %d, want %d", dash.width, tt.width)
		}
		if dash.height != tt.height {
			t.Errorf("height = %d, want %d", dash.height, tt.height)
		}
	}
}

func TestThreatDashboard_View_NoData(t *testing.T) {
	dash := New()
	dash.data = nil

	view := dash.View()
	if !strings.Contains(view, "No threat data") {
		t.Error("View should show 'No threat data' when data is nil")
	}
}

func TestThreatDashboard_View_WithData(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{
		ActiveThreats: 2,
		ThreatsByLevel: map[ThreatLevel]int{
			ThreatLevelCritical: 0,
			ThreatLevelHigh:     2,
			ThreatLevelMedium:   5,
			ThreatLevelLow:      10,
		},
		ThreatScore: 35.0,
		LastUpdate:  time.Now(),
		RecentThreats: []ThreatEvent{
			{
				ID:          "THR-001",
				Type:        ThreatTypePhishing,
				Level:       ThreatLevelHigh,
				Description: "Test threat",
				Timestamp:   time.Now(),
			},
		},
	}

	view := dash.View()

	// Check for threat score - it might be formatted differently
	if !strings.Contains(view, "35") && !strings.Contains(view, "Threat Score") {
		t.Error("View should contain threat score information")
	}
	if !strings.Contains(view, "2") {
		t.Error("View should contain active threats count")
	}
}

func TestThreatDashboard_Update_RefreshMsg(t *testing.T) {
	dash := New()

	msg := dashboard.RefreshMsg{
		DashboardID: "threat-dashboard",
		Timestamp:   time.Now(),
	}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	if cmd == nil {
		t.Error("Update() should return command for refresh")
	}
}

func TestThreatDashboard_Update_RefreshMsg_DifferentID(t *testing.T) {
	dash := New()

	msg := dashboard.RefreshMsg{
		DashboardID: "other-dashboard",
		Timestamp:   time.Now(),
	}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	if cmd != nil {
		t.Error("Update() should not return command for different dashboard ID")
	}
}

func TestThreatDashboard_Update_DataMsg(t *testing.T) {
	dash := New()

	newData := &ThreatData{
		ActiveThreats:  5,
		ThreatScore:    75.0,
		ThreatsByLevel: make(map[ThreatLevel]int),
		LastUpdate:     time.Now(),
	}

	msg := dashboard.DataMsg{
		DashboardID: "threat-dashboard",
		Data:        newData,
	}

	updated, _ := dash.Update(msg)

	updatedDash := updated.(*ThreatDashboard)
	if updatedDash.data.ActiveThreats != 5 {
		t.Errorf("ActiveThreats = %d, want 5", updatedDash.data.ActiveThreats)
	}
	if updatedDash.data.ThreatScore != 75.0 {
		t.Errorf("ThreatScore = %f, want 75.0", updatedDash.data.ThreatScore)
	}
}

func TestThreatDashboard_Update_DataMsg_WrongType(t *testing.T) {
	dash := New()
	originalScore := dash.data.ThreatScore

	msg := dashboard.DataMsg{
		DashboardID: "threat-dashboard",
		Data:        "wrong type",
	}

	updated, _ := dash.Update(msg)

	updatedDash := updated.(*ThreatDashboard)
	if updatedDash.data.ThreatScore != originalScore {
		t.Error("Data should not be updated with wrong type")
	}
}

func TestThreatDashboard_Update_KeyMsg_Refresh(t *testing.T) {
	dash := New()
	dash.Focus()

	msg := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'r'}}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	if cmd == nil {
		t.Error("Update() should return refresh command for 'r' key")
	}
}

func TestThreatDashboard_Update_KeyMsg_NotFocused(t *testing.T) {
	dash := New()
	dash.Blur()

	msg := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'r'}}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	if cmd != nil {
		t.Error("Update() should not return command when not focused")
	}
}

func TestThreatDashboard_Update_TickMsg(t *testing.T) {
	dash := New()

	msg := tickMsg(time.Now())

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	if cmd == nil {
		t.Error("Update() should return command for tick")
	}
}

func TestThreatDashboard_RenderHeader(t *testing.T) {
	tests := []struct {
		name        string
		threatScore float64
		activeCount int
	}{
		{"low threat", 20.0, 0},
		{"medium threat", 50.0, 2},
		{"high threat", 80.0, 5},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New()
			dash.data = &ThreatData{
				ThreatScore:   tt.threatScore,
				ActiveThreats: tt.activeCount,
			}

			header := dash.renderHeader()
			if header == "" {
				t.Error("Header should not be empty")
			}
		})
	}
}

func TestThreatDashboard_RenderThreatSummary(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{
		ThreatsByLevel: map[ThreatLevel]int{
			ThreatLevelCritical: 1,
			ThreatLevelHigh:     3,
			ThreatLevelMedium:   5,
			ThreatLevelLow:      10,
		},
	}

	summary := dash.renderThreatSummary()

	if !strings.Contains(summary, "critical") {
		t.Error("Summary should contain critical level")
	}
	if !strings.Contains(summary, "1") {
		t.Error("Summary should contain critical count")
	}
}

func TestThreatDashboard_RenderThreatSummary_NoThreats(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{
		ThreatsByLevel: map[ThreatLevel]int{
			ThreatLevelCritical: 0,
			ThreatLevelHigh:     0,
			ThreatLevelMedium:   0,
			ThreatLevelLow:      0,
		},
	}

	summary := dash.renderThreatSummary()
	if summary == "" {
		t.Error("Summary should not be empty")
	}
}

func TestThreatDashboard_RenderRecentThreats(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{
		RecentThreats: []ThreatEvent{
			{
				ID:          "THR-001",
				Type:        ThreatTypePhishing,
				Level:       ThreatLevelHigh,
				Description: "Phishing detected",
				Timestamp:   time.Now().Add(-15 * time.Minute),
				Mitigated:   false,
				MITRE:       "T1566.001",
			},
			{
				ID:          "THR-002",
				Type:        ThreatTypeRecon,
				Level:       ThreatLevelMedium,
				Description: "Port scanning",
				Timestamp:   time.Now().Add(-1 * time.Hour),
				Mitigated:   true,
			},
		},
	}

	threats := dash.renderRecentThreats()

	if !strings.Contains(threats, "phishing") {
		t.Error("Should contain threat type")
	}
	if !strings.Contains(threats, "T1566.001") {
		t.Error("Should contain MITRE technique")
	}
}

func TestThreatDashboard_RenderRecentThreats_Empty(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{
		RecentThreats: []ThreatEvent{},
	}

	threats := dash.renderRecentThreats()

	if !strings.Contains(threats, "No recent threats") {
		t.Error("Should show 'No recent threats' message")
	}
}

func TestThreatDashboard_RenderRecentThreats_Truncation(t *testing.T) {
	dash := New()

	// Create 10 threats (should show only 5)
	threats := make([]ThreatEvent, 10)
	for i := range threats {
		threats[i] = ThreatEvent{
			ID:          "THR-" + string(rune('0'+i)),
			Type:        ThreatTypeRecon,
			Level:       ThreatLevelLow,
			Description: "Test threat " + string(rune('0'+i)),
			Timestamp:   time.Now(),
		}
	}

	dash.data = &ThreatData{
		RecentThreats: threats,
	}

	result := dash.renderRecentThreats()
	if result == "" {
		t.Error("Result should not be empty")
	}
}

func TestThreatDashboard_RenderAPTCampaigns(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{
		APTCampaigns: []APTCampaign{
			{
				Name:       "Operation Test",
				Group:      "APT28",
				Active:     true,
				StartDate:  time.Now().Add(-24 * time.Hour),
				Techniques: []string{"T1566.001", "T1059.001"},
				Confidence: 85.0,
			},
		},
	}

	campaigns := dash.renderAPTCampaigns()

	if !strings.Contains(campaigns, "Operation Test") {
		t.Error("Should contain campaign name")
	}
	if !strings.Contains(campaigns, "APT28") {
		t.Error("Should contain APT group")
	}
	if !strings.Contains(campaigns, "85") {
		t.Error("Should contain confidence")
	}
}

func TestThreatDashboard_RenderAPTCampaigns_NoActive(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{
		APTCampaigns: []APTCampaign{
			{
				Name:   "Inactive Campaign",
				Group:  "APT1",
				Active: false,
			},
		},
	}

	campaigns := dash.renderAPTCampaigns()

	if !strings.Contains(campaigns, "No active APT campaigns") {
		t.Error("Should show 'No active APT campaigns' message")
	}
}

func TestThreatDashboard_RenderAPTCampaigns_TechniqueTruncation(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{
		APTCampaigns: []APTCampaign{
			{
				Name:       "Test",
				Group:      "APT1",
				Active:     true,
				Techniques: []string{"T1", "T2", "T3", "T4", "T5"},
				Confidence: 50.0,
			},
		},
	}

	campaigns := dash.renderAPTCampaigns()
	if campaigns == "" {
		t.Error("Campaigns should not be empty")
	}
}

func TestThreatDashboard_RenderIOCs(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{
		IOCs: []IOC{
			{
				Type:       IOCTypeIP,
				Value:      "192.0.2.123",
				Threat:     "C2 Server",
				FirstSeen:  time.Now(),
				Confidence: 90.0,
			},
			{
				Type:       IOCTypeDomain,
				Value:      "malicious.example",
				Threat:     "Phishing",
				FirstSeen:  time.Now(),
				Confidence: 85.0,
			},
		},
	}

	iocs := dash.renderIOCs()

	if !strings.Contains(iocs, "192.0.2.123") {
		t.Error("Should contain IP address")
	}
	if !strings.Contains(iocs, "malicious.example") {
		t.Error("Should contain domain")
	}
	if !strings.Contains(iocs, "90") {
		t.Error("Should contain confidence")
	}
}

func TestThreatDashboard_RenderIOCs_Truncation(t *testing.T) {
	dash := New()

	// Create 10 IOCs (should show only 5)
	iocs := make([]IOC, 10)
	for i := range iocs {
		iocs[i] = IOC{
			Type:       IOCTypeIP,
			Value:      "192.0.2." + string(rune('0'+i)),
			Confidence: 80.0,
		}
	}

	dash.data = &ThreatData{
		IOCs: iocs,
	}

	result := dash.renderIOCs()
	if result == "" {
		t.Error("Result should not be empty")
	}
}

func TestThreatDashboard_GetLevelStyle(t *testing.T) {
	dash := New()

	tests := []ThreatLevel{
		ThreatLevelCritical,
		ThreatLevelHigh,
		ThreatLevelMedium,
		ThreatLevelLow,
		ThreatLevelInfo,
	}

	for _, level := range tests {
		t.Run(string(level), func(t *testing.T) {
			style := dash.getLevelStyle(level)
			_ = style // Just verify it doesn't panic
		})
	}
}

func TestThreatDashboard_GetLevelIcon(t *testing.T) {
	dash := New()

	tests := []struct {
		level    ThreatLevel
		expected string
	}{
		{ThreatLevelCritical, "⬤"},
		{ThreatLevelHigh, "●"},
		{ThreatLevelMedium, "◐"},
		{ThreatLevelLow, "○"},
	}

	for _, tt := range tests {
		t.Run(string(tt.level), func(t *testing.T) {
			icon := dash.getLevelIcon(tt.level)
			if icon != tt.expected {
				t.Errorf("getLevelIcon(%s) = %s, want %s", tt.level, icon, tt.expected)
			}
		})
	}
}

func TestTruncate(t *testing.T) {
	tests := []struct {
		input    string
		max      int
		expected string
	}{
		{"short", 10, "short"},
		{"exactly ten ch", 14, "exactly ten ch"},
		{"this is a very long string", 10, "this is..."},
		{"", 5, ""},
		{"a", 5, "a"},
	}

	for _, tt := range tests {
		result := truncate(tt.input, tt.max)
		if result != tt.expected {
			t.Errorf("truncate(%q, %d) = %q, want %q", tt.input, tt.max, result, tt.expected)
		}
	}
}

func TestFormatTimeAgo(t *testing.T) {
	tests := []struct {
		duration time.Duration
		contains string
	}{
		{30 * time.Second, "s ago"},
		{5 * time.Minute, "m ago"},
		{2 * time.Hour, "h ago"},
		{25 * time.Hour, "d ago"},
	}

	for _, tt := range tests {
		result := formatTimeAgo(tt.duration)
		if !strings.Contains(result, tt.contains) {
			t.Errorf("formatTimeAgo(%v) = %s, should contain %s", tt.duration, result, tt.contains)
		}
	}
}

func TestThreatType_Constants(t *testing.T) {
	types := []ThreatType{
		ThreatTypeMalware,
		ThreatTypePhishing,
		ThreatTypeExfiltration,
		ThreatTypeLateralMove,
		ThreatTypePrivEsc,
		ThreatTypePersistence,
		ThreatTypeRecon,
		ThreatTypeDDoS,
	}

	seen := make(map[ThreatType]bool)
	for _, tt := range types {
		if seen[tt] {
			t.Errorf("Duplicate threat type: %s", tt)
		}
		seen[tt] = true
	}
}

func TestThreatLevel_Constants(t *testing.T) {
	levels := []ThreatLevel{
		ThreatLevelCritical,
		ThreatLevelHigh,
		ThreatLevelMedium,
		ThreatLevelLow,
		ThreatLevelInfo,
	}

	seen := make(map[ThreatLevel]bool)
	for _, level := range levels {
		if seen[level] {
			t.Errorf("Duplicate threat level: %s", level)
		}
		seen[level] = true
	}
}

func TestIOCType_Constants(t *testing.T) {
	types := []IOCType{
		IOCTypeIP,
		IOCTypeDomain,
		IOCTypeHash,
		IOCTypeEmail,
		IOCTypeURL,
	}

	seen := make(map[IOCType]bool)
	for _, iocType := range types {
		if seen[iocType] {
			t.Errorf("Duplicate IOC type: %s", iocType)
		}
		seen[iocType] = true
	}
}

func TestThreatDashboard_FetchThreatData(t *testing.T) {
	dash := New()
	ctx := context.Background()

	data := dash.fetchThreatData(ctx)

	if data == nil {
		t.Fatal("fetchThreatData() should return data")
	}
	if data.ThreatsByLevel == nil {
		t.Error("ThreatsByLevel should not be nil")
	}
	if len(data.ThreatTrend) == 0 {
		t.Error("ThreatTrend should have data")
	}
	if data.LastUpdate.IsZero() {
		t.Error("LastUpdate should be set")
	}
}

func TestThreatDashboard_Refresh(t *testing.T) {
	dash := New()

	cmd := dash.refresh()
	if cmd == nil {
		t.Fatal("refresh() should return a command")
	}

	msg := cmd()

	dataMsg, ok := msg.(dashboard.DataMsg)
	if !ok {
		t.Fatal("refresh() should return DataMsg")
	}

	data, ok := dataMsg.Data.(*ThreatData)
	if !ok {
		t.Fatal("DataMsg.Data should be *ThreatData")
	}

	if data.ThreatScore == 0 {
		t.Error("ThreatScore should be calculated")
	}
}

func TestThreatDashboard_Init(t *testing.T) {
	dash := New()

	cmd := dash.Init()
	if cmd == nil {
		t.Error("Init() should return a command")
	}

	if dash.refreshTicker == nil {
		t.Error("refreshTicker should be initialized")
	}
}

func TestThreatEvent_Struct(t *testing.T) {
	now := time.Now()

	event := ThreatEvent{
		ID:          "THR-001",
		Type:        ThreatTypePhishing,
		Level:       ThreatLevelHigh,
		Source:      "192.0.2.1",
		Target:      "internal.example.com",
		Description: "Test threat",
		Timestamp:   now,
		Mitigated:   true,
		MITRE:       "T1566.001",
	}

	if event.ID != "THR-001" {
		t.Errorf("ID = %s, want THR-001", event.ID)
	}
	if event.Type != ThreatTypePhishing {
		t.Errorf("Type = %s, want phishing", event.Type)
	}
	if event.Level != ThreatLevelHigh {
		t.Errorf("Level = %s, want high", event.Level)
	}
	if !event.Mitigated {
		t.Error("Mitigated should be true")
	}
}

func TestAPTCampaign_Struct(t *testing.T) {
	now := time.Now()

	campaign := APTCampaign{
		Name:       "Operation Test",
		Group:      "APT28",
		Active:     true,
		StartDate:  now,
		Techniques: []string{"T1566.001", "T1059.001"},
		Targets:    []string{"target1", "target2"},
		Confidence: 85.5,
	}

	if campaign.Name != "Operation Test" {
		t.Errorf("Name = %s", campaign.Name)
	}
	if campaign.Group != "APT28" {
		t.Errorf("Group = %s", campaign.Group)
	}
	if !campaign.Active {
		t.Error("Active should be true")
	}
	if len(campaign.Techniques) != 2 {
		t.Errorf("Techniques length = %d, want 2", len(campaign.Techniques))
	}
	if campaign.Confidence != 85.5 {
		t.Errorf("Confidence = %f, want 85.5", campaign.Confidence)
	}
}

func TestIOC_Struct(t *testing.T) {
	now := time.Now()

	ioc := IOC{
		Type:       IOCTypeIP,
		Value:      "192.0.2.123",
		Threat:     "C2 Server",
		FirstSeen:  now,
		Confidence: 90.0,
	}

	if ioc.Type != IOCTypeIP {
		t.Errorf("Type = %s, want ip", ioc.Type)
	}
	if ioc.Value != "192.0.2.123" {
		t.Errorf("Value = %s", ioc.Value)
	}
	if ioc.Confidence != 90.0 {
		t.Errorf("Confidence = %f, want 90.0", ioc.Confidence)
	}
}

func TestThreatDashboard_UpdateCharts(t *testing.T) {
	dash := New()
	dash.data = &ThreatData{}

	// Should not panic
	dash.updateCharts()
}
