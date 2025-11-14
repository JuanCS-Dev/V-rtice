package network

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
	if dash.id != "network-dashboard" {
		t.Errorf("ID = %s, want network-dashboard", dash.id)
	}
	if dash.data == nil {
		t.Error("data should not be nil")
	}
	if dash.data.BandwidthHistory == nil {
		t.Error("BandwidthHistory should not be nil")
	}
	if dash.data.TopConnections == nil {
		t.Error("TopConnections should not be nil")
	}
	if dash.data.LatencyHistory == nil {
		t.Error("LatencyHistory should not be nil")
	}
}

func TestNetworkDashboard_ID(t *testing.T) {
	dash := New()
	if id := dash.ID(); id != "network-dashboard" {
		t.Errorf("ID() = %s, want network-dashboard", id)
	}
}

func TestNetworkDashboard_Title(t *testing.T) {
	dash := New()
	if title := dash.Title(); title != "Network Monitor" {
		t.Errorf("Title() = %s, want Network Monitor", title)
	}
}

func TestNetworkDashboard_Focus(t *testing.T) {
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

func TestNetworkDashboard_Resize(t *testing.T) {
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

func TestNetworkDashboard_View_NoData(t *testing.T) {
	dash := New()
	dash.data = nil

	view := dash.View()
	if !strings.Contains(view, "No network data") {
		t.Error("View should show 'No network data' when data is nil")
	}
}

func TestNetworkDashboard_View_WithData(t *testing.T) {
	dash := New()
	dash.data = &NetworkData{
		InboundBandwidth:  45.5,
		OutboundBandwidth: 23.2,
		TotalBandwidth:    68.7,
		ActiveConnections: 234,
		EstablishedConns:  187,
		AverageLatency:    45 * time.Millisecond,
		PacketLoss:        0.2,
		BytesReceived:     1024 * 1024 * 1024,
		BytesSent:         512 * 1024 * 1024,
		LastUpdate:        time.Now(),
	}

	view := dash.View()

	if !strings.Contains(view, "45") {
		t.Error("View should contain bandwidth metrics")
	}
	if !strings.Contains(view, "234") {
		t.Error("View should contain active connections")
	}
}

func TestNetworkDashboard_Update_RefreshMsg(t *testing.T) {
	dash := New()

	msg := dashboard.RefreshMsg{
		DashboardID: "network-dashboard",
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

func TestNetworkDashboard_Update_RefreshMsg_DifferentID(t *testing.T) {
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

func TestNetworkDashboard_Update_DataMsg(t *testing.T) {
	dash := New()

	newData := &NetworkData{
		InboundBandwidth:  100.0,
		OutboundBandwidth: 50.0,
		ActiveConnections: 500,
		LastUpdate:        time.Now(),
	}

	msg := dashboard.DataMsg{
		DashboardID: "network-dashboard",
		Data:        newData,
	}

	updated, _ := dash.Update(msg)

	updatedDash := updated.(*NetworkDashboard)
	if updatedDash.data.InboundBandwidth != 100.0 {
		t.Errorf("InboundBandwidth = %f, want 100.0", updatedDash.data.InboundBandwidth)
	}
	if updatedDash.data.ActiveConnections != 500 {
		t.Errorf("ActiveConnections = %d, want 500", updatedDash.data.ActiveConnections)
	}
}

func TestNetworkDashboard_Update_DataMsg_WrongType(t *testing.T) {
	dash := New()
	originalBandwidth := dash.data.InboundBandwidth

	msg := dashboard.DataMsg{
		DashboardID: "network-dashboard",
		Data:        "wrong type",
	}

	updated, _ := dash.Update(msg)

	updatedDash := updated.(*NetworkDashboard)
	if updatedDash.data.InboundBandwidth != originalBandwidth {
		t.Error("Data should not be updated with wrong type")
	}
}

func TestNetworkDashboard_Update_KeyMsg_Refresh(t *testing.T) {
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

func TestNetworkDashboard_Update_KeyMsg_NotFocused(t *testing.T) {
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

func TestNetworkDashboard_Update_TickMsg(t *testing.T) {
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

func TestNetworkDashboard_RenderBandwidth(t *testing.T) {
	tests := []struct {
		name     string
		inbound  float64
		outbound float64
	}{
		{"low bandwidth", 10.5, 5.2},
		{"medium bandwidth", 50.0, 25.0},
		{"high bandwidth", 95.0, 85.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New()
			dash.data = &NetworkData{
				InboundBandwidth:  tt.inbound,
				OutboundBandwidth: tt.outbound,
				TotalBandwidth:    tt.inbound + tt.outbound,
				BytesReceived:     1024,
				BytesSent:         512,
			}

			bandwidth := dash.renderBandwidth()
			if bandwidth == "" {
				t.Error("Bandwidth render should not be empty")
			}
		})
	}
}

func TestNetworkDashboard_RenderConnections(t *testing.T) {
	tests := []struct {
		name   string
		active int
		wait   int
	}{
		{"low connections", 100, 10},
		{"medium connections", 1500, 200},
		{"high connections", 6000, 600},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New()
			dash.data = &NetworkData{
				ActiveConnections: tt.active,
				EstablishedConns:  tt.active - 50,
				ListeningPorts:    45,
				TimeWaitConns:     tt.wait,
			}

			connections := dash.renderConnections()
			if connections == "" {
				t.Error("Connections render should not be empty")
			}
		})
	}
}

func TestNetworkDashboard_RenderLatency(t *testing.T) {
	tests := []struct {
		name    string
		latency time.Duration
		loss    float64
	}{
		{"good latency", 20 * time.Millisecond, 0.1},
		{"medium latency", 150 * time.Millisecond, 2.0},
		{"high latency", 600 * time.Millisecond, 8.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New()
			dash.data = &NetworkData{
				AverageLatency: tt.latency,
				MinLatency:     tt.latency / 2,
				MaxLatency:     tt.latency * 2,
				PacketLoss:     tt.loss,
				ErrorCount:     5,
				DroppedPackets: 10,
			}

			latency := dash.renderLatency()
			if latency == "" {
				t.Error("Latency render should not be empty")
			}
		})
	}
}

func TestNetworkDashboard_RenderLatency_NoErrors(t *testing.T) {
	dash := New()
	dash.data = &NetworkData{
		AverageLatency: 20 * time.Millisecond,
		MinLatency:     10 * time.Millisecond,
		MaxLatency:     40 * time.Millisecond,
		PacketLoss:     0.1,
		ErrorCount:     0,
		DroppedPackets: 0,
	}

	latency := dash.renderLatency()
	if latency == "" {
		t.Error("Latency render should not be empty")
	}
}

func TestNetworkDashboard_RenderTopConnections(t *testing.T) {
	dash := New()
	dash.data = &NetworkData{
		TopConnections: []Connection{
			{
				LocalAddr:  "10.0.1.50:443",
				RemoteAddr: "172.16.34.12:52341",
				State:      "ESTABLISHED",
				Protocol:   "tcp",
				BytesSent:  1024,
				BytesRecv:  2048,
				Duration:   15 * time.Minute,
			},
			{
				LocalAddr:  "10.0.1.50:8080",
				RemoteAddr: "192.168.1.100:48392",
				State:      "TIME_WAIT",
				Protocol:   "udp",
				BytesSent:  512,
				BytesRecv:  1024,
				Duration:   1 * time.Minute,
			},
		},
	}

	connections := dash.renderTopConnections()

	if !strings.Contains(connections, "10.0.1.50") {
		t.Error("Should contain local address")
	}
	if !strings.Contains(connections, "ESTABLISHED") {
		t.Error("Should contain connection state")
	}
}

func TestNetworkDashboard_RenderTopConnections_Empty(t *testing.T) {
	dash := New()
	dash.data = &NetworkData{
		TopConnections: []Connection{},
	}

	connections := dash.renderTopConnections()

	if !strings.Contains(connections, "No active connections") {
		t.Error("Should show 'No active connections' message")
	}
}

func TestNetworkDashboard_RenderTopConnections_Truncation(t *testing.T) {
	dash := New()

	// Create 10 connections (should show only 5)
	conns := make([]Connection, 10)
	for i := range conns {
		conns[i] = Connection{
			LocalAddr:  "10.0.0.1:8080",
			RemoteAddr: "192.168.1.1:1234",
			State:      "ESTABLISHED",
			Protocol:   "tcp",
		}
	}

	dash.data = &NetworkData{
		TopConnections: conns,
	}

	result := dash.renderTopConnections()
	if result == "" {
		t.Error("Result should not be empty")
	}
}

func TestNetworkDashboard_GetBandwidthStyle(t *testing.T) {
	dash := New()

	tests := []struct {
		bandwidth float64
		name      string
	}{
		{50.0, "normal"},
		{85.0, "high"},
		{95.0, "very high"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			style := dash.getBandwidthStyle(tt.bandwidth)
			_ = style // Just verify it doesn't panic
		})
	}
}

func TestFormatBytes(t *testing.T) {
	tests := []struct {
		bytes    uint64
		contains string
	}{
		{512, "B"},
		{1024, "K"},
		{1024 * 1024, "M"},
		{1024 * 1024 * 1024, "G"},
		{1024 * 1024 * 1024 * 1024, "T"},
	}

	for _, tt := range tests {
		result := formatBytes(tt.bytes)
		if !strings.Contains(result, tt.contains) {
			t.Errorf("formatBytes(%d) = %s, should contain %s", tt.bytes, result, tt.contains)
		}
	}
}

func TestFormatLatency(t *testing.T) {
	tests := []struct {
		duration time.Duration
		contains string
	}{
		{500 * time.Microsecond, "µs"},
		{50 * time.Millisecond, "ms"},
		{1500 * time.Millisecond, "s"},
	}

	for _, tt := range tests {
		result := formatLatency(tt.duration)
		if !strings.Contains(result, tt.contains) {
			t.Errorf("formatLatency(%v) = %s, should contain %s", tt.duration, result, tt.contains)
		}
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

func TestBandwidthSample_Struct(t *testing.T) {
	now := time.Now()
	sample := BandwidthSample{
		Timestamp: now,
		Inbound:   45.5,
		Outbound:  23.2,
	}

	if !sample.Timestamp.Equal(now) {
		t.Error("Timestamp mismatch")
	}
	if sample.Inbound != 45.5 {
		t.Errorf("Inbound = %f, want 45.5", sample.Inbound)
	}
	if sample.Outbound != 23.2 {
		t.Errorf("Outbound = %f, want 23.2", sample.Outbound)
	}
}

func TestConnection_Struct(t *testing.T) {
	conn := Connection{
		LocalAddr:  "10.0.0.1:8080",
		RemoteAddr: "192.168.1.1:1234",
		State:      "ESTABLISHED",
		Protocol:   "tcp",
		BytesSent:  1024,
		BytesRecv:  2048,
		Duration:   10 * time.Minute,
	}

	if conn.LocalAddr != "10.0.0.1:8080" {
		t.Errorf("LocalAddr = %s", conn.LocalAddr)
	}
	if conn.RemoteAddr != "192.168.1.1:1234" {
		t.Errorf("RemoteAddr = %s", conn.RemoteAddr)
	}
	if conn.State != "ESTABLISHED" {
		t.Errorf("State = %s", conn.State)
	}
	if conn.Protocol != "tcp" {
		t.Errorf("Protocol = %s", conn.Protocol)
	}
	if conn.BytesSent != 1024 {
		t.Errorf("BytesSent = %d, want 1024", conn.BytesSent)
	}
	if conn.BytesRecv != 2048 {
		t.Errorf("BytesRecv = %d, want 2048", conn.BytesRecv)
	}
	if conn.Duration != 10*time.Minute {
		t.Errorf("Duration = %v", conn.Duration)
	}
}

func TestNetworkData_Struct(t *testing.T) {
	now := time.Now()
	history := []BandwidthSample{{Timestamp: now, Inbound: 10, Outbound: 5}}
	conns := []Connection{{LocalAddr: "test", State: "ESTABLISHED"}}
	latencyHist := []float64{10, 20, 30}

	data := NetworkData{
		InboundBandwidth:     45.5,
		OutboundBandwidth:    23.2,
		TotalBandwidth:       68.7,
		BandwidthHistory:     history,
		ActiveConnections:    234,
		EstablishedConns:     187,
		ListeningPorts:       45,
		TimeWaitConns:        23,
		TopConnections:       conns,
		AverageLatency:       45 * time.Millisecond,
		MinLatency:           12 * time.Millisecond,
		MaxLatency:           234 * time.Millisecond,
		PacketLoss:           0.2,
		LatencyHistory:       latencyHist,
		BytesReceived:        1024,
		BytesSent:            512,
		PacketsReceived:      100,
		PacketsSent:          50,
		DroppedPackets:       2,
		ErrorCount:           1,
		LastUpdate:           now,
	}

	if data.InboundBandwidth != 45.5 {
		t.Errorf("InboundBandwidth = %f", data.InboundBandwidth)
	}
	if data.ActiveConnections != 234 {
		t.Errorf("ActiveConnections = %d", data.ActiveConnections)
	}
	if len(data.BandwidthHistory) != 1 {
		t.Error("BandwidthHistory length mismatch")
	}
	if len(data.TopConnections) != 1 {
		t.Error("TopConnections length mismatch")
	}
	if len(data.LatencyHistory) != 3 {
		t.Error("LatencyHistory length mismatch")
	}
}

func TestNetworkDashboard_FetchNetworkData(t *testing.T) {
	dash := New()
	ctx := context.Background()

	data := dash.fetchNetworkData(ctx)

	if data == nil {
		t.Fatal("fetchNetworkData() should return data")
	}
	if data.InboundBandwidth == 0 {
		t.Error("InboundBandwidth should be set")
	}
	if data.ActiveConnections == 0 {
		t.Error("ActiveConnections should be set")
	}
	if len(data.BandwidthHistory) == 0 {
		t.Error("BandwidthHistory should have data")
	}
	if len(data.TopConnections) == 0 {
		t.Error("TopConnections should have data")
	}
	if data.LastUpdate.IsZero() {
		t.Error("LastUpdate should be set")
	}
}

func TestNetworkDashboard_Refresh(t *testing.T) {
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

	data, ok := dataMsg.Data.(*NetworkData)
	if !ok {
		t.Fatal("DataMsg.Data should be *NetworkData")
	}

	if data.TotalBandwidth == 0 {
		t.Error("TotalBandwidth should be calculated")
	}
}

func TestNetworkDashboard_Init(t *testing.T) {
	dash := New()

	cmd := dash.Init()
	if cmd == nil {
		t.Error("Init() should return a command")
	}

	if dash.refreshTicker == nil {
		t.Error("refreshTicker should be initialized")
	}
}

func TestNetworkDashboard_TickRefresh(t *testing.T) {
	dash := New()

	cmd := dash.tickRefresh()
	if cmd == nil {
		t.Error("tickRefresh() should return a command")
	}
}

func TestNetworkDashboard_UpdateCharts(t *testing.T) {
	dash := New()
	dash.data = &NetworkData{}

	// Should not panic
	dash.updateCharts()
}

func TestNetworkDashboard_View_FormattingEdgeCases(t *testing.T) {
	tests := []struct {
		name string
		data *NetworkData
	}{
		{
			name: "zero values",
			data: &NetworkData{
				LastUpdate: time.Now(),
			},
		},
		{
			name: "high connection count",
			data: &NetworkData{
				ActiveConnections: 10000,
				EstablishedConns:  9000,
				LastUpdate:        time.Now(),
			},
		},
		{
			name: "high packet loss",
			data: &NetworkData{
				PacketLoss: 15.5,
				LastUpdate: time.Now(),
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New()
			dash.data = tt.data

			view := dash.View()
			if view == "" {
				t.Error("View should not be empty")
			}
		})
	}
}
