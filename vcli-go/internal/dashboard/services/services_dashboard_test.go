package services

import (
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
	if dash.id != "services-dashboard" {
		t.Errorf("ID = %s, want services-dashboard", dash.id)
	}
	if dash.data == nil {
		t.Error("data should not be nil")
	}
	if dash.data.Services == nil {
		t.Error("Services slice should not be nil")
	}
	if dash.focused {
		t.Error("focused should be false initially")
	}
}

func TestServicesDashboard_ID(t *testing.T) {
	dash := New()
	if id := dash.ID(); id != "services-dashboard" {
		t.Errorf("ID() = %s, want services-dashboard", id)
	}
}

func TestServicesDashboard_Title(t *testing.T) {
	dash := New()
	if title := dash.Title(); title != "Services Health" {
		t.Errorf("Title() = %s, want Services Health", title)
	}
}

func TestServicesDashboard_Focus(t *testing.T) {
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

func TestServicesDashboard_Resize(t *testing.T) {
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

func TestServicesDashboard_View_NoData(t *testing.T) {
	dash := New()
	dash.data = nil

	view := dash.View()
	if !strings.Contains(view, "No data") {
		t.Error("View should show 'No data' when data is nil")
	}
}

func TestServicesDashboard_View_WithData(t *testing.T) {
	dash := New()
	dash.data = &ServicesData{
		TotalServices:  5,
		HealthyCount:   3,
		DegradedCount:  1,
		UnhealthyCount: 1,
		LastUpdate:     time.Now(),
		Services: []ServiceHealth{
			{
				Name:            "test-service",
				Status:          HealthStatusHealthy,
				ResponseTime:    50 * time.Millisecond,
				Uptime:          99.9,
				ErrorRate:       0.1,
				ResponseHistory: []float64{40, 45, 50},
			},
		},
	}

	view := dash.View()

	if !strings.Contains(view, "5") { // TotalServices
		t.Error("View should contain total services count")
	}
	if !strings.Contains(view, "3") { // HealthyCount
		t.Error("View should contain healthy count")
	}
	if !strings.Contains(view, "test-service") {
		t.Error("View should contain service name")
	}
}

func TestServicesDashboard_Update_RefreshMsg(t *testing.T) {
	dash := New()

	msg := dashboard.RefreshMsg{
		DashboardID: "services-dashboard",
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

func TestServicesDashboard_Update_RefreshMsg_DifferentID(t *testing.T) {
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

func TestServicesDashboard_Update_DataMsg(t *testing.T) {
	dash := New()

	newData := &ServicesData{
		TotalServices: 10,
		HealthyCount:  8,
		LastUpdate:    time.Now(),
		Services:      []ServiceHealth{},
	}

	msg := dashboard.DataMsg{
		DashboardID: "services-dashboard",
		Data:        newData,
	}

	updated, _ := dash.Update(msg)

	updatedDash := updated.(*ServicesDashboard)
	if updatedDash.data.TotalServices != 10 {
		t.Errorf("TotalServices = %d, want 10", updatedDash.data.TotalServices)
	}
	if updatedDash.data.HealthyCount != 8 {
		t.Errorf("HealthyCount = %d, want 8", updatedDash.data.HealthyCount)
	}
}

func TestServicesDashboard_Update_DataMsg_WrongType(t *testing.T) {
	dash := New()
	originalTotal := dash.data.TotalServices

	msg := dashboard.DataMsg{
		DashboardID: "services-dashboard",
		Data:        "wrong type",
	}

	updated, _ := dash.Update(msg)

	updatedDash := updated.(*ServicesDashboard)
	if updatedDash.data.TotalServices != originalTotal {
		t.Error("Data should not be updated with wrong type")
	}
}

func TestServicesDashboard_Update_KeyMsg_Refresh(t *testing.T) {
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

func TestServicesDashboard_Update_KeyMsg_NotFocused(t *testing.T) {
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

func TestServicesDashboard_Update_TickMsg(t *testing.T) {
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

func TestServicesDashboard_RenderHeader(t *testing.T) {
	dash := New()
	dash.data = &ServicesData{
		TotalServices:  10,
		HealthyCount:   7,
		DegradedCount:  2,
		UnhealthyCount: 1,
	}

	header := dash.renderHeader()

	if !strings.Contains(header, "10") {
		t.Error("Header should contain total services")
	}
	if !strings.Contains(header, "7") {
		t.Error("Header should contain healthy count")
	}
}

func TestServicesDashboard_RenderHeader_NoIssues(t *testing.T) {
	dash := New()
	dash.data = &ServicesData{
		TotalServices:  5,
		HealthyCount:   5,
		DegradedCount:  0,
		UnhealthyCount: 0,
	}

	header := dash.renderHeader()

	if !strings.Contains(header, "5") {
		t.Error("Header should contain counts")
	}
}

func TestServicesDashboard_GetStatusIcon(t *testing.T) {
	dash := New()

	tests := []struct {
		status   HealthStatus
		expected string
	}{
		{HealthStatusHealthy, "●"},
		{HealthStatusDegraded, "◐"},
		{HealthStatusUnhealthy, "○"},
		{HealthStatusUnknown, "?"},
	}

	for _, tt := range tests {
		t.Run(string(tt.status), func(t *testing.T) {
			icon := dash.getStatusIcon(tt.status)
			if icon != tt.expected {
				t.Errorf("getStatusIcon(%s) = %s, want %s", tt.status, icon, tt.expected)
			}
		})
	}
}

func TestServicesDashboard_RenderServiceGrid(t *testing.T) {
	dash := New()
	dash.data = &ServicesData{
		Services: []ServiceHealth{
			{
				Name:            "service1",
				Status:          HealthStatusHealthy,
				ResponseTime:    50 * time.Millisecond,
				Uptime:          99.9,
				ErrorRate:       0.1,
				ResponseHistory: []float64{40, 45, 50, 55, 60},
			},
			{
				Name:            "service2",
				Status:          HealthStatusDegraded,
				ResponseTime:    150 * time.Millisecond,
				Uptime:          97.5,
				ErrorRate:       2.5,
				ResponseHistory: []float64{100, 120, 140, 150, 160},
			},
		},
	}

	grid := dash.renderServiceGrid()

	if !strings.Contains(grid, "service1") {
		t.Error("Grid should contain service1")
	}
	if !strings.Contains(grid, "service2") {
		t.Error("Grid should contain service2")
	}
	if !strings.Contains(grid, "99.9%") {
		t.Error("Grid should contain uptime")
	}
}

func TestServicesDashboard_RenderSparkline(t *testing.T) {
	dash := New()

	tests := []struct {
		name    string
		history []float64
		minLen  int
	}{
		{
			name:    "normal history",
			history: []float64{10, 20, 30, 40, 50, 60, 70, 80, 90, 100},
			minLen:  10,
		},
		{
			name:    "short history",
			history: []float64{10, 20},
			minLen:  2,
		},
		{
			name:    "empty history",
			history: []float64{},
			minLen:  10,
		},
		{
			name:    "single value",
			history: []float64{50},
			minLen:  1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			sparkline := dash.renderSparkline(tt.history)
			if len(sparkline) < tt.minLen {
				t.Errorf("Sparkline length = %d, want at least %d", len(sparkline), tt.minLen)
			}
		})
	}
}

func TestServicesDashboard_RenderSparkline_SameValues(t *testing.T) {
	dash := New()

	// All same values (min == max)
	history := []float64{50, 50, 50, 50, 50}
	sparkline := dash.renderSparkline(history)

	if sparkline == "" {
		t.Error("Sparkline should not be empty")
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

func TestFormatDuration(t *testing.T) {
	tests := []struct {
		duration time.Duration
		contains string
	}{
		{500 * time.Microsecond, "µs"},
		{50 * time.Millisecond, "ms"},
		{1500 * time.Millisecond, "s"},
	}

	for _, tt := range tests {
		result := formatDuration(tt.duration)
		if !strings.Contains(result, tt.contains) {
			t.Errorf("formatDuration(%v) = %s, should contain %s", tt.duration, result, tt.contains)
		}
	}
}

func TestHealthStatus_Constants(t *testing.T) {
	statuses := []HealthStatus{
		HealthStatusHealthy,
		HealthStatusDegraded,
		HealthStatusUnhealthy,
		HealthStatusUnknown,
	}

	seen := make(map[HealthStatus]bool)
	for _, status := range statuses {
		if seen[status] {
			t.Errorf("Duplicate health status: %s", status)
		}
		seen[status] = true
	}
}

func TestServiceHealth_Struct(t *testing.T) {
	now := time.Now()
	history := []float64{10, 20, 30}

	health := ServiceHealth{
		Name:            "test-service",
		Status:          HealthStatusHealthy,
		ResponseTime:    50 * time.Millisecond,
		Uptime:          99.9,
		ErrorRate:       0.1,
		LastCheck:       now,
		Endpoint:        "http://example.com/health",
		Version:         "1.0.0",
		ResponseHistory: history,
	}

	if health.Name != "test-service" {
		t.Errorf("Name = %s, want test-service", health.Name)
	}
	if health.Status != HealthStatusHealthy {
		t.Errorf("Status = %s, want healthy", health.Status)
	}
	if health.ResponseTime != 50*time.Millisecond {
		t.Errorf("ResponseTime = %v, want 50ms", health.ResponseTime)
	}
	if health.Uptime != 99.9 {
		t.Errorf("Uptime = %f, want 99.9", health.Uptime)
	}
	if health.ErrorRate != 0.1 {
		t.Errorf("ErrorRate = %f, want 0.1", health.ErrorRate)
	}
	if !health.LastCheck.Equal(now) {
		t.Error("LastCheck mismatch")
	}
	if health.Endpoint != "http://example.com/health" {
		t.Errorf("Endpoint = %s", health.Endpoint)
	}
	if health.Version != "1.0.0" {
		t.Errorf("Version = %s, want 1.0.0", health.Version)
	}
	if len(health.ResponseHistory) != 3 {
		t.Errorf("ResponseHistory length = %d, want 3", len(health.ResponseHistory))
	}
}

func TestServicesData_Struct(t *testing.T) {
	now := time.Now()
	services := []ServiceHealth{
		{Name: "svc1", Status: HealthStatusHealthy},
		{Name: "svc2", Status: HealthStatusDegraded},
	}

	data := ServicesData{
		Services:       services,
		TotalServices:  2,
		HealthyCount:   1,
		DegradedCount:  1,
		UnhealthyCount: 0,
		LastUpdate:     now,
	}

	if len(data.Services) != 2 {
		t.Errorf("Services length = %d, want 2", len(data.Services))
	}
	if data.TotalServices != 2 {
		t.Errorf("TotalServices = %d, want 2", data.TotalServices)
	}
	if data.HealthyCount != 1 {
		t.Errorf("HealthyCount = %d, want 1", data.HealthyCount)
	}
	if data.DegradedCount != 1 {
		t.Errorf("DegradedCount = %d, want 1", data.DegradedCount)
	}
	if data.UnhealthyCount != 0 {
		t.Errorf("UnhealthyCount = %d, want 0", data.UnhealthyCount)
	}
	if !data.LastUpdate.Equal(now) {
		t.Error("LastUpdate mismatch")
	}
}

func TestServicesDashboard_Refresh(t *testing.T) {
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

	data, ok := dataMsg.Data.(*ServicesData)
	if !ok {
		t.Fatal("DataMsg.Data should be *ServicesData")
	}

	if data.TotalServices == 0 {
		t.Error("TotalServices should not be 0")
	}
	if len(data.Services) == 0 {
		t.Error("Services should not be empty")
	}
	if data.LastUpdate.IsZero() {
		t.Error("LastUpdate should be set")
	}
}

func TestServicesDashboard_RenderServiceGrid_ErrorRateColors(t *testing.T) {
	dash := New()

	tests := []struct {
		name      string
		errorRate float64
	}{
		{"low error rate", 0.5},
		{"medium error rate", 2.5},
		{"high error rate", 7.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash.data = &ServicesData{
				Services: []ServiceHealth{
					{
						Name:            "test",
						Status:          HealthStatusHealthy,
						ResponseTime:    50 * time.Millisecond,
						Uptime:          99.0,
						ErrorRate:       tt.errorRate,
						ResponseHistory: []float64{40, 50, 60},
					},
				},
			}

			grid := dash.renderServiceGrid()
			if grid == "" {
				t.Error("Grid should not be empty")
			}
		})
	}
}

func TestServicesDashboard_View_EmptyServices(t *testing.T) {
	dash := New()
	dash.data = &ServicesData{
		Services:      []ServiceHealth{},
		TotalServices: 0,
		LastUpdate:    time.Now(),
	}

	view := dash.View()
	if view == "" {
		t.Error("View should not be empty even with no services")
	}
}

func TestServicesDashboard_Init(t *testing.T) {
	dash := New()

	cmd := dash.Init()
	if cmd == nil {
		t.Error("Init() should return a command")
	}

	// Should initialize ticker
	if dash.refreshTicker == nil {
		t.Error("refreshTicker should be initialized")
	}
}

func TestServicesDashboard_TickRefresh(t *testing.T) {
	dash := New()

	cmd := dash.tickRefresh()
	if cmd == nil {
		t.Error("tickRefresh() should return a command")
	}
}

func TestServicesDashboard_GetStatusStyle(t *testing.T) {
	dash := New()

	tests := []HealthStatus{
		HealthStatusHealthy,
		HealthStatusDegraded,
		HealthStatusUnhealthy,
		HealthStatusUnknown,
	}

	for _, status := range tests {
		t.Run(string(status), func(t *testing.T) {
			style := dash.getStatusStyle(status)
			// Just verify it doesn't panic and returns a style
			_ = style
		})
	}
}
