package system

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
			if dash.id != "system-overview" {
				t.Errorf("ID = %s, want system-overview", dash.id)
			}
			if dash.focused {
				t.Error("focused should be false initially")
			}
		})
	}
}

func TestSystemOverview_ID(t *testing.T) {
	dash := New("default")
	if id := dash.ID(); id != "system-overview" {
		t.Errorf("ID() = %s, want system-overview", id)
	}
}

func TestSystemOverview_Title(t *testing.T) {
	dash := New("default")
	if title := dash.Title(); title != "System Overview" {
		t.Errorf("Title() = %s, want System Overview", title)
	}
}

func TestSystemOverview_Focus(t *testing.T) {
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

func TestSystemOverview_Resize(t *testing.T) {
	dash := New("default")
	dash.Init() // Initialize to create sub-dashboards

	tests := []struct {
		width  int
		height int
	}{
		{300, 150},
		{200, 100},
		{400, 200},
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

func TestSystemOverview_Resize_BeforeInit(t *testing.T) {
	dash := New("default")

	// Should not panic before Init
	dash.Resize(300, 150)

	if dash.width != 300 {
		t.Errorf("width = %d, want 300", dash.width)
	}
	if dash.height != 150 {
		t.Errorf("height = %d, want 150", dash.height)
	}
}

func TestSystemOverview_Init(t *testing.T) {
	dash := New("default")

	cmd := dash.Init()
	if cmd == nil {
		t.Error("Init() should return a command")
	}

	// Check that sub-dashboards are created
	if dash.k8sDash == nil {
		t.Error("k8sDash should be initialized")
	}
	if dash.servicesDash == nil {
		t.Error("servicesDash should be initialized")
	}
	if dash.threatDash == nil {
		t.Error("threatDash should be initialized")
	}
	if dash.networkDash == nil {
		t.Error("networkDash should be initialized")
	}
	if dash.layout == nil {
		t.Error("layout should be initialized")
	}
	if dash.refreshTicker == nil {
		t.Error("refreshTicker should be initialized")
	}
}

func TestSystemOverview_View_NotInitialized(t *testing.T) {
	dash := New("default")

	view := dash.View()
	if !strings.Contains(view, "not initialized") {
		t.Error("View should show 'not initialized' message when layout is nil")
	}
}

func TestSystemOverview_View_Initialized(t *testing.T) {
	dash := New("default")
	dash.width = 300
	dash.height = 150
	dash.Init()

	view := dash.View()

	// Should contain header
	if !strings.Contains(view, "System Overview") && !strings.Contains(view, "VÉRTICE") {
		t.Error("View should contain header")
	}

	// Should not be empty
	if view == "" {
		t.Error("View should not be empty after initialization")
	}
}

func TestSystemOverview_Update_RefreshMsg_AllDashboards(t *testing.T) {
	dash := New("default")
	dash.Init()

	msg := dashboard.RefreshMsg{
		DashboardID: "system-overview",
		Timestamp:   time.Now(),
	}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	// cmd may be nil if no sub-dashboards return commands
	_ = cmd
}

func TestSystemOverview_Update_RefreshMsg_EmptyID(t *testing.T) {
	dash := New("default")
	dash.Init()

	msg := dashboard.RefreshMsg{
		DashboardID: "", // Empty ID refreshes all
		Timestamp:   time.Now(),
	}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	// cmd may be nil if no sub-dashboards return commands
	_ = cmd
}

func TestSystemOverview_Update_KeyMsg_Refresh(t *testing.T) {
	dash := New("default")
	dash.Init()
	dash.Focus()

	msg := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'r'}}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	// cmd may be nil if no sub-dashboards return commands
	_ = cmd
}

func TestSystemOverview_Update_KeyMsg_FocusDashboards(t *testing.T) {
	tests := []struct {
		key          rune
		expectedFocus string
	}{
		{'1', "k8s"},
		{'2', "services"},
		{'3', "threat"},
		{'4', "network"},
	}

	for _, tt := range tests {
		t.Run(string(tt.key), func(t *testing.T) {
			dash := New("default")
			dash.Init()
			dash.Focus()

			msg := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{tt.key}}

			updated, _ := dash.Update(msg)

			if updated == nil {
				t.Error("Update() should return dashboard")
			}

			updatedDash := updated.(*SystemOverview)

			// Verify focus state
			switch tt.expectedFocus {
			case "k8s":
				if !updatedDash.k8sDash.IsFocused() {
					t.Error("k8sDash should be focused")
				}
			case "services":
				if !updatedDash.servicesDash.IsFocused() {
					t.Error("servicesDash should be focused")
				}
			case "threat":
				if !updatedDash.threatDash.IsFocused() {
					t.Error("threatDash should be focused")
				}
			case "network":
				if !updatedDash.networkDash.IsFocused() {
					t.Error("networkDash should be focused")
				}
			}
		})
	}
}

func TestSystemOverview_Update_KeyMsg_NotFocused(t *testing.T) {
	dash := New("default")
	dash.Init()
	dash.Blur()

	msg := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'r'}}

	updated, _ := dash.Update(msg)

	// Should still forward to layout
	if updated == nil {
		t.Error("Update() should return dashboard")
	}
}

func TestSystemOverview_Update_TickMsg(t *testing.T) {
	dash := New("default")
	dash.Init()

	msg := tickMsg(time.Now())

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	if cmd == nil {
		t.Error("Update() should return command for tick")
	}
}

func TestSystemOverview_Update_OtherMsg(t *testing.T) {
	dash := New("default")
	dash.Init()

	// Forward other messages to layout
	msg := dashboard.DataMsg{
		DashboardID: "some-dashboard",
		Data:        "test",
	}

	updated, cmd := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
	// cmd may or may not be nil
	_ = cmd
}

func TestSystemOverview_RenderHeader(t *testing.T) {
	dash := New("default")
	dash.width = 300

	header := dash.renderHeader()

	if header == "" {
		t.Error("Header should not be empty")
	}
	if !strings.Contains(header, "System Overview") && !strings.Contains(header, "VÉRTICE") {
		t.Error("Header should contain title")
	}
}

func TestSystemOverview_RenderGrid(t *testing.T) {
	dash := New("default")
	dash.width = 300
	dash.height = 150
	dash.Init()

	grid := dash.renderGrid()

	// Should not be empty
	if grid == "" {
		t.Error("Grid should not be empty")
	}
}

func TestSystemOverview_RenderGrid_NoLayout(t *testing.T) {
	dash := New("default")
	dash.layout = nil

	grid := dash.renderGrid()

	if grid != "" {
		t.Error("Grid should be empty when layout is nil")
	}
}

func TestSystemOverview_RenderCell(t *testing.T) {
	dash := New("default")
	dash.Init()

	// Test rendering a cell with one of the sub-dashboards
	cell := dash.renderCell(dash.k8sDash, 100, 50, "1")

	if cell == "" {
		t.Error("Cell should not be empty")
	}
}

func TestSystemOverview_RenderCell_Focused(t *testing.T) {
	dash := New("default")
	dash.Init()

	// Focus a dashboard
	dash.k8sDash.Focus()

	cell := dash.renderCell(dash.k8sDash, 100, 50, "1")

	if cell == "" {
		t.Error("Cell should not be empty")
	}
	// Border color should change when focused
}

func TestSystemOverview_RenderEmptyCell(t *testing.T) {
	dash := New("default")

	cell := dash.renderEmptyCell(100, 50, "Reserved")

	if cell == "" {
		t.Error("Empty cell should not be empty")
	}
	if !strings.Contains(cell, "Reserved") {
		t.Error("Empty cell should contain label")
	}
}

func TestSystemOverview_RenderFooter(t *testing.T) {
	dash := New("default")

	footer := dash.renderFooter()

	if footer == "" {
		t.Error("Footer should not be empty")
	}
	if !strings.Contains(footer, "Focus") || !strings.Contains(footer, "1-4") {
		t.Error("Footer should contain hotkey help")
	}
	if !strings.Contains(footer, "Refresh") || !strings.Contains(footer, "r") {
		t.Error("Footer should contain refresh help")
	}
	if !strings.Contains(footer, "Quit") || !strings.Contains(footer, "q") {
		t.Error("Footer should contain quit help")
	}
}

func TestSystemOverview_Resize_WithSubDashboards(t *testing.T) {
	dash := New("default")
	dash.Init()

	// Initial size
	dash.Resize(300, 150)

	if dash.width != 300 {
		t.Errorf("width = %d, want 300", dash.width)
	}
	if dash.height != 150 {
		t.Errorf("height = %d, want 150", dash.height)
	}

	// Change size
	dash.Resize(400, 200)

	if dash.width != 400 {
		t.Errorf("width = %d, want 400", dash.width)
	}
	if dash.height != 200 {
		t.Errorf("height = %d, want 200", dash.height)
	}
}

func TestSystemOverview_Init_CreatesGridLayout(t *testing.T) {
	dash := New("default")
	dash.Init()

	if dash.layout == nil {
		t.Fatal("layout should be created")
	}

	if dash.layout.Type != dashboard.LayoutTypeGrid {
		t.Errorf("Layout type = %v, want Grid", dash.layout.Type)
	}

	if dash.layout.Rows != 2 {
		t.Errorf("Layout rows = %d, want 2", dash.layout.Rows)
	}

	if dash.layout.Cols != 3 {
		t.Errorf("Layout cols = %d, want 3", dash.layout.Cols)
	}

	if len(dash.layout.Dashboards) != 4 {
		t.Errorf("Layout dashboards = %d, want 4", len(dash.layout.Dashboards))
	}
}

func TestSystemOverview_TickRefresh(t *testing.T) {
	dash := New("default")

	cmd := dash.tickRefresh()
	if cmd == nil {
		t.Error("tickRefresh() should return a command")
	}
}

func TestSystemOverview_FocusTransitions(t *testing.T) {
	dash := New("default")
	dash.Init()
	dash.Focus()

	// Focus k8s
	msg1 := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'1'}}
	dash.Update(msg1)
	if !dash.k8sDash.IsFocused() {
		t.Error("k8sDash should be focused")
	}
	if dash.servicesDash.IsFocused() || dash.threatDash.IsFocused() || dash.networkDash.IsFocused() {
		t.Error("Other dashboards should not be focused")
	}

	// Focus services
	msg2 := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'2'}}
	dash.Update(msg2)
	if !dash.servicesDash.IsFocused() {
		t.Error("servicesDash should be focused")
	}
	if dash.k8sDash.IsFocused() || dash.threatDash.IsFocused() || dash.networkDash.IsFocused() {
		t.Error("Other dashboards should not be focused")
	}

	// Focus threat
	msg3 := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'3'}}
	dash.Update(msg3)
	if !dash.threatDash.IsFocused() {
		t.Error("threatDash should be focused")
	}
	if dash.k8sDash.IsFocused() || dash.servicesDash.IsFocused() || dash.networkDash.IsFocused() {
		t.Error("Other dashboards should not be focused")
	}

	// Focus network
	msg4 := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'4'}}
	dash.Update(msg4)
	if !dash.networkDash.IsFocused() {
		t.Error("networkDash should be focused")
	}
	if dash.k8sDash.IsFocused() || dash.servicesDash.IsFocused() || dash.threatDash.IsFocused() {
		t.Error("Other dashboards should not be focused")
	}
}

func TestSystemOverview_View_WithDimensions(t *testing.T) {
	tests := []struct {
		name   string
		width  int
		height int
	}{
		{"small", 200, 100},
		{"medium", 300, 150},
		{"large", 400, 200},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dash := New("default")
			dash.width = tt.width
			dash.height = tt.height
			dash.Init()

			view := dash.View()
			if view == "" {
				t.Error("View should not be empty")
			}
		})
	}
}

func TestSystemOverview_Resize_NilSubDashboards(t *testing.T) {
	dash := New("default")
	dash.Init()

	// Manually set one to nil to test nil check
	originalK8s := dash.k8sDash
	dash.k8sDash = nil

	// Should not panic
	dash.Resize(300, 150)

	// Restore for other tests
	dash.k8sDash = originalK8s
}

func TestSystemOverview_Update_BeforeInit(t *testing.T) {
	dash := New("default")

	msg := tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'1'}}

	// Should handle messages even before Init
	// The layout will be nil but Update should handle it gracefully
	updated, _ := dash.Update(msg)

	if updated == nil {
		t.Error("Update() should return dashboard")
	}
}

func TestSystemOverview_MultipleUpdates(t *testing.T) {
	dash := New("default")
	dash.Init()
	dash.Focus()

	messages := []tea.Msg{
		tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'1'}},
		tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'r'}},
		dashboard.RefreshMsg{DashboardID: "", Timestamp: time.Now()},
		tickMsg(time.Now()),
	}

	for _, msg := range messages {
		updated, cmd := dash.Update(msg)
		if updated == nil {
			t.Error("Update() should always return dashboard")
		}
		_ = cmd
	}
}
