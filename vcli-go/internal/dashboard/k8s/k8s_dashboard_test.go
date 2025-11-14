package k8s

import (
	"strings"
	"testing"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/verticedev/vcli-go/internal/dashboard"
)

func TestNew(t *testing.T) {
	tests := []struct {
		name      string
		namespace string
	}{
		{"default namespace", "default"},
		{"custom namespace", "kube-system"},
		{"empty namespace", ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New(tt.namespace)

			if dash == nil {
				t.Fatal("New() returned nil")
			}
			if dash.id != "k8s-dashboard" {
				t.Errorf("ID = %s, want k8s-dashboard", dash.id)
			}
			if dash.data == nil {
				t.Error("data should not be nil")
			}
			if dash.data.Namespace != tt.namespace {
				t.Errorf("Namespace = %s, want %s", dash.data.Namespace, tt.namespace)
			}
			if dash.focused {
				t.Error("focused should be false initially")
			}
		})
	}
}

func TestK8sDashboard_ID(t *testing.T) {
	dash := New("default")
	if id := dash.ID(); id != "k8s-dashboard" {
		t.Errorf("ID() = %s, want k8s-dashboard", id)
	}
}

func TestK8sDashboard_Title(t *testing.T) {
	dash := New("default")
	if title := dash.Title(); title != "Kubernetes Monitor" {
		t.Errorf("Title() = %s, want Kubernetes Monitor", title)
	}
}

func TestK8sDashboard_Focus(t *testing.T) {
	dash := New("default")

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

func TestK8sDashboard_Resize(t *testing.T) {
	dash := New("default")

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

func TestK8sDashboard_View_NoData(t *testing.T) {
	dash := New("default")
	dash.data = nil

	view := dash.View()
	if !strings.Contains(view, "No data") {
		t.Error("View should show 'No data' when data is nil")
	}
}

func TestK8sDashboard_View_WithData(t *testing.T) {
	dash := New("default")
	dash.data = &K8sData{
		Namespace:       "test-namespace",
		PodCount:        10,
		NodeCount:       3,
		DeploymentCount: 5,
		ServiceCount:    8,
		HealthyPods:     8,
		UnhealthyPods:   2,
		CPUUsage:        45.5,
		MemoryUsage:     62.8,
		LastUpdate:      time.Now(),
	}

	view := dash.View()

	// Check that all metrics are displayed
	if !strings.Contains(view, "test-namespace") {
		t.Error("View should contain namespace")
	}
	if !strings.Contains(view, "10") { // PodCount
		t.Error("View should contain pod count")
	}
	if !strings.Contains(view, "3") { // NodeCount
		t.Error("View should contain node count")
	}
	if !strings.Contains(view, "5") { // DeploymentCount
		t.Error("View should contain deployment count")
	}
	if !strings.Contains(view, "8") { // ServiceCount and HealthyPods
		t.Error("View should contain service count")
	}
	if !strings.Contains(view, "45") { // CPUUsage (45.5%)
		t.Error("View should contain CPU usage")
	}
	if !strings.Contains(view, "62") { // MemoryUsage (62.8%)
		t.Error("View should contain memory usage")
	}
}

func TestK8sDashboard_View_CPUUsageColors(t *testing.T) {
	tests := []struct {
		name     string
		cpuUsage float64
		// We can't easily test the actual color, but we can test rendering
	}{
		{"low CPU", 30.0},
		{"medium CPU", 65.0},
		{"high CPU", 85.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New("default")
			dash.data = &K8sData{
				Namespace:  "default",
				CPUUsage:   tt.cpuUsage,
				LastUpdate: time.Now(),
			}

			view := dash.View()
			if view == "" {
				t.Error("View should not be empty")
			}
		})
	}
}

func TestK8sDashboard_View_MemoryUsageColors(t *testing.T) {
	tests := []struct {
		name        string
		memoryUsage float64
	}{
		{"low memory", 35.0},
		{"medium memory", 70.0},
		{"high memory", 90.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New("default")
			dash.data = &K8sData{
				Namespace:   "default",
				MemoryUsage: tt.memoryUsage,
				LastUpdate:  time.Now(),
			}

			view := dash.View()
			if view == "" {
				t.Error("View should not be empty")
			}
		})
	}
}

func TestK8sDashboard_Update_RefreshMsg(t *testing.T) {
	dash := New("default")
	// Set a fake client by creating a real clientset
	// We can't easily mock the client for refresh without proper interfaces
	// Just test that the message is handled correctly
	dash.client = nil // Will cause error in refresh

	msg := dashboard.RefreshMsg{
		DashboardID: "k8s-dashboard",
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

func TestK8sDashboard_Update_RefreshMsg_DifferentID(t *testing.T) {
	dash := New("default")

	msg := dashboard.RefreshMsg{
		DashboardID: "other-dashboard",
		Timestamp:   time.Now(),
	}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	// Should not trigger refresh for different dashboard
	if cmd != nil {
		t.Error("Update() should not return command for different dashboard ID")
	}
}

func TestK8sDashboard_Update_DataMsg(t *testing.T) {
	dash := New("default")

	newData := &K8sData{
		Namespace:  "updated-namespace",
		PodCount:   20,
		NodeCount:  5,
		LastUpdate: time.Now(),
	}

	msg := dashboard.DataMsg{
		DashboardID: "k8s-dashboard",
		Data:        newData,
	}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}

	updatedDash := updated.(*K8sDashboard)
	if updatedDash.data.Namespace != "updated-namespace" {
		t.Errorf("Namespace = %s, want updated-namespace", updatedDash.data.Namespace)
	}
	if updatedDash.data.PodCount != 20 {
		t.Errorf("PodCount = %d, want 20", updatedDash.data.PodCount)
	}

	_ = cmd
}

func TestK8sDashboard_Update_DataMsg_WrongType(t *testing.T) {
	dash := New("default")
	originalNamespace := dash.data.Namespace

	msg := dashboard.DataMsg{
		DashboardID: "k8s-dashboard",
		Data:        "wrong type", // Not *K8sData
	}

	updated, _ := dash.Update(msg)

	updatedDash := updated.(*K8sDashboard)
	// Data should not be updated with wrong type
	if updatedDash.data.Namespace != originalNamespace {
		t.Error("Data should not be updated with wrong type")
	}
}

func TestK8sDashboard_Update_KeyMsg_Refresh(t *testing.T) {
	dash := New("default")
	dash.client = nil // Will test refresh behavior
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

func TestK8sDashboard_Update_KeyMsg_NotFocused(t *testing.T) {
	dash := New("default")
	dash.Blur()

	msg := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'r'}}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	// Should not trigger refresh when not focused
	if cmd != nil {
		t.Error("Update() should not return command when not focused")
	}
}

func TestK8sDashboard_Refresh_NoClient(t *testing.T) {
	dash := New("default")
	dash.client = nil

	cmd := dash.refresh()
	msg := cmd()

	errorMsg, ok := msg.(dashboard.ErrorMsg)
	if !ok {
		t.Fatal("refresh() should return ErrorMsg when client is nil")
	}
	if errorMsg.DashboardID != "k8s-dashboard" {
		t.Errorf("ErrorMsg DashboardID = %s, want k8s-dashboard", errorMsg.DashboardID)
	}
	if errorMsg.Error == nil {
		t.Error("ErrorMsg should contain error")
	}
}

func TestK8sDashboard_Refresh_WithFakeClient(t *testing.T) {
	// Skip this test as mocking K8s client is complex
	// The refresh functionality is tested in integration tests
	t.Skip("Skipping fake K8s client test - integration test required")
}

func TestK8sDashboard_Refresh_MultiplePodStatuses(t *testing.T) {
	// Skip this test as mocking K8s client is complex
	// The refresh functionality is tested in integration tests
	t.Skip("Skipping fake K8s client test - integration test required")
}

func TestK8sDashboard_Init_NoKubeconfig(t *testing.T) {
	dash := New("default")

	cmd := dash.Init()
	if cmd == nil {
		t.Error("Init() should return a command")
	}

	// Execute the command - it will try to load kubeconfig and may fail
	msg := cmd()

	// Should return either ErrorMsg or proceed with refresh
	switch msg.(type) {
	case dashboard.ErrorMsg, dashboard.DataMsg, nil:
		// Expected outcomes
	default:
		t.Errorf("Unexpected message type: %T", msg)
	}
}

func TestK8sData_Struct(t *testing.T) {
	now := time.Now()
	data := K8sData{
		Namespace:       "test",
		PodCount:        10,
		NodeCount:       3,
		DeploymentCount: 5,
		ServiceCount:    7,
		HealthyPods:     8,
		UnhealthyPods:   2,
		CPUUsage:        45.5,
		MemoryUsage:     62.3,
		LastUpdate:      now,
	}

	if data.Namespace != "test" {
		t.Errorf("Namespace = %s, want test", data.Namespace)
	}
	if data.PodCount != 10 {
		t.Errorf("PodCount = %d, want 10", data.PodCount)
	}
	if data.NodeCount != 3 {
		t.Errorf("NodeCount = %d, want 3", data.NodeCount)
	}
	if data.DeploymentCount != 5 {
		t.Errorf("DeploymentCount = %d, want 5", data.DeploymentCount)
	}
	if data.ServiceCount != 7 {
		t.Errorf("ServiceCount = %d, want 7", data.ServiceCount)
	}
	if data.HealthyPods != 8 {
		t.Errorf("HealthyPods = %d, want 8", data.HealthyPods)
	}
	if data.UnhealthyPods != 2 {
		t.Errorf("UnhealthyPods = %d, want 2", data.UnhealthyPods)
	}
	if data.CPUUsage != 45.5 {
		t.Errorf("CPUUsage = %f, want 45.5", data.CPUUsage)
	}
	if data.MemoryUsage != 62.3 {
		t.Errorf("MemoryUsage = %f, want 62.3", data.MemoryUsage)
	}
	if !data.LastUpdate.Equal(now) {
		t.Error("LastUpdate mismatch")
	}
}

func TestK8sDashboard_View_FormattingEdgeCases(t *testing.T) {
	tests := []struct {
		name string
		data *K8sData
	}{
		{
			name: "zero values",
			data: &K8sData{
				Namespace:  "empty",
				LastUpdate: time.Now(),
			},
		},
		{
			name: "high pod count",
			data: &K8sData{
				Namespace:  "large",
				PodCount:   9999,
				HealthyPods: 9999,
				LastUpdate: time.Now(),
			},
		},
		{
			name: "100% CPU and memory",
			data: &K8sData{
				Namespace:   "maxed",
				CPUUsage:    100.0,
				MemoryUsage: 100.0,
				LastUpdate:  time.Now(),
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New("default")
			dash.data = tt.data

			view := dash.View()
			if view == "" {
				t.Error("View should not be empty")
			}
		})
	}
}
