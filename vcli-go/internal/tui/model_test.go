package tui

import (
	"testing"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
	"github.com/verticedev/vcli-go/internal/core"
)

// ModelTestSuite is the test suite for Model
type ModelTestSuite struct {
	suite.Suite
	state *core.State
	model Model
}

// SetupTest runs before each test
func (s *ModelTestSuite) SetupTest() {
	s.state = core.NewState("1.0.0")
	s.model = NewModel(s.state, "1.0.0")
}

// TestModelCreation tests model creation
func (s *ModelTestSuite) TestModelCreation() {
	assert.NotNil(s.T(), s.model.state)
	assert.Equal(s.T(), "1.0.0", s.model.version)
	assert.Equal(s.T(), ViewTypeWorkspace, s.model.activeView)
	assert.Equal(s.T(), ComponentIDWorkspace, s.model.focused)
	assert.False(s.T(), s.model.ready)
	assert.NotNil(s.T(), s.model.workspaces)
	assert.NotNil(s.T(), s.model.loadedPlugins)
	assert.NotNil(s.T(), s.model.shortcuts)
}

// TestModelInit tests model initialization
func (s *ModelTestSuite) TestModelInit() {
	cmd := s.model.Init()
	assert.NotNil(s.T(), cmd)

	// Init returns a batch command with workspace/plugin loading and ticker commands
	// Note: Batch command verification would require tea.Batch introspection (not currently exposed)
}

// TestSetActiveWorkspace tests workspace switching
func (s *ModelTestSuite) TestSetActiveWorkspace() {
	// Create a mock workspace
	ws := &MockWorkspace{
		id:          "test",
		name:        "Test Workspace",
		description: "Test Description",
		initialized: true,
	}

	// Register workspace
	s.model.RegisterWorkspace(ws)

	// Switch to workspace
	err := s.model.SetActiveWorkspace("test")
	assert.NoError(s.T(), err)
	assert.Equal(s.T(), "test", s.model.activeWS)
	assert.Equal(s.T(), ViewTypeWorkspace, s.model.activeView)

	// Try to switch to non-existent workspace
	err = s.model.SetActiveWorkspace("nonexistent")
	assert.Error(s.T(), err)
}

// TestGetActiveWorkspace tests getting active workspace
func (s *ModelTestSuite) TestGetActiveWorkspace() {
	// No active workspace
	ws := s.model.GetActiveWorkspace()
	assert.Nil(s.T(), ws)

	// Set active workspace
	mockWS := &MockWorkspace{id: "test", name: "Test"}
	s.model.RegisterWorkspace(mockWS)
	s.model.SetActiveWorkspace("test")

	ws = s.model.GetActiveWorkspace()
	assert.NotNil(s.T(), ws)
	assert.Equal(s.T(), "test", ws.ID())
}

// TestRegisterUnregisterWorkspace tests workspace registration
func (s *ModelTestSuite) TestRegisterUnregisterWorkspace() {
	ws := &MockWorkspace{id: "test", name: "Test"}

	// Register
	s.model.RegisterWorkspace(ws)
	assert.Contains(s.T(), s.model.workspaces, "test")

	// Unregister
	s.model.UnregisterWorkspace("test")
	assert.NotContains(s.T(), s.model.workspaces, "test")
}

// TestLoadPlugin tests plugin loading
func (s *ModelTestSuite) TestLoadPlugin() {
	s.model.LoadPlugin("kubernetes", "1.0.0")

	assert.Contains(s.T(), s.model.loadedPlugins, "kubernetes")
	assert.Equal(s.T(), "kubernetes", s.model.loadedPlugins["kubernetes"].Name)
	assert.Equal(s.T(), "1.0.0", s.model.loadedPlugins["kubernetes"].Version)
	assert.True(s.T(), s.model.loadedPlugins["kubernetes"].Enabled)
	assert.True(s.T(), s.model.loadedPlugins["kubernetes"].Healthy)
}

// TestUnloadPlugin tests plugin unloading
func (s *ModelTestSuite) TestUnloadPlugin() {
	s.model.LoadPlugin("kubernetes", "1.0.0")
	assert.Contains(s.T(), s.model.loadedPlugins, "kubernetes")

	s.model.UnloadPlugin("kubernetes")
	assert.NotContains(s.T(), s.model.loadedPlugins, "kubernetes")
}

// TestUpdatePluginHealth tests plugin health updates
func (s *ModelTestSuite) TestUpdatePluginHealth() {
	s.model.LoadPlugin("kubernetes", "1.0.0")

	// Mark as unhealthy
	s.model.UpdatePluginHealth("kubernetes", false)
	assert.False(s.T(), s.model.loadedPlugins["kubernetes"].Healthy)
	assert.Equal(s.T(), 1, s.model.loadedPlugins["kubernetes"].ErrorCount)

	// Mark as healthy
	s.model.UpdatePluginHealth("kubernetes", true)
	assert.True(s.T(), s.model.loadedPlugins["kubernetes"].Healthy)
}

// TestAddEvent tests event addition
func (s *ModelTestSuite) TestAddEvent() {
	event := Event{
		Type:      EventTypeInfo,
		Timestamp: time.Now(),
		Source:    "test",
		Data:      "test data",
		Severity:  SeverityLow,
	}

	s.model.AddEvent(event)
	assert.Len(s.T(), s.model.events, 1)
	assert.Equal(s.T(), EventTypeInfo, s.model.events[0].Type)
}

// TestClearEvents tests event clearing
func (s *ModelTestSuite) TestClearEvents() {
	// Add events with different timestamps
	now := time.Now()
	old := now.Add(-2 * time.Hour)

	s.model.AddEvent(Event{Timestamp: old})
	s.model.AddEvent(Event{Timestamp: now})

	// Clear old events
	s.model.ClearEvents(now.Add(-1 * time.Hour))

	assert.Len(s.T(), s.model.events, 1)
	assert.Equal(s.T(), now.Unix(), s.model.events[0].Timestamp.Unix())
}

// TestAddError tests error addition
func (s *ModelTestSuite) TestAddError() {
	err := Error{
		Code:      "TEST_ERROR",
		Message:   "Test error message",
		Timestamp: time.Now(),
		Context:   "test",
		Severity:  SeverityHigh,
	}

	s.model.AddError(err)
	assert.Len(s.T(), s.model.errors, 1)
	assert.Equal(s.T(), "TEST_ERROR", s.model.errors[0].Code)
}

// TestAddWarning tests warning addition
func (s *ModelTestSuite) TestAddWarning() {
	warning := Error{
		Code:      "TEST_WARNING",
		Message:   "Test warning message",
		Timestamp: time.Now(),
		Context:   "test",
		Severity:  SeverityMedium,
	}

	s.model.AddWarning(warning)
	assert.Len(s.T(), s.model.warnings, 1)
	assert.Equal(s.T(), "TEST_WARNING", s.model.warnings[0].Code)
}

// TestClearErrors tests error clearing
func (s *ModelTestSuite) TestClearErrors() {
	s.model.AddError(Error{Code: "ERR1"})
	s.model.AddError(Error{Code: "ERR2"})

	s.model.ClearErrors()
	assert.Len(s.T(), s.model.errors, 0)
}

// TestUpdateMetrics tests metrics update
func (s *ModelTestSuite) TestUpdateMetrics() {
	metrics := MetricsData{
		Timestamp:     time.Now(),
		CPU:           45.5,
		Memory:        60.2,
		Disk:          30.1,
		PluginsLoaded: 3,
		Errors:        2,
		Warnings:      1,
	}

	s.model.UpdateMetrics(metrics)
	assert.Equal(s.T(), 45.5, s.model.metrics.CPU)
	assert.Len(s.T(), s.model.metricsHist, 1)
}

// TestLoading tests loading state management
func (s *ModelTestSuite) TestLoading() {
	// Start loading
	s.model.StartLoading("test", "Loading test...")
	assert.True(s.T(), s.model.IsLoading("test"))

	// Stop loading
	s.model.StopLoading("test")
	assert.False(s.T(), s.model.IsLoading("test"))
}

// TestNotifications tests notification management
func (s *ModelTestSuite) TestNotifications() {
	notif := Notification{
		ID:       "test1",
		Title:    "Test",
		Message:  "Test message",
		Severity: SeverityLow,
		Duration: 3 * time.Second,
	}

	// Add notification
	s.model.AddNotification(notif)
	assert.Len(s.T(), s.model.notifications, 1)

	// Get active notifications
	active := s.model.GetActiveNotifications()
	assert.Len(s.T(), active, 1)

	// Dismiss notification
	s.model.DismissNotification("test1")
	active = s.model.GetActiveNotifications()
	assert.Len(s.T(), active, 0)
}

// TestOfflineMode tests offline mode management
func (s *ModelTestSuite) TestOfflineMode() {
	// Enable offline mode
	s.model.SetOfflineMode(true)
	assert.True(s.T(), s.model.offlineMode)

	// Disable offline mode
	s.model.SetOfflineMode(false)
	assert.False(s.T(), s.model.offlineMode)
}

// TestNavigation tests navigation
func (s *ModelTestSuite) TestNavigation() {
	// Setup workspaces
	ws1 := &MockWorkspace{id: "ws1", name: "WS1"}
	ws2 := &MockWorkspace{id: "ws2", name: "WS2"}
	s.model.RegisterWorkspace(ws1)
	s.model.RegisterWorkspace(ws2)

	// Navigate to ws1
	s.model.SetActiveWorkspace("ws1")
	assert.Equal(s.T(), "ws1", s.model.activeWS)

	// Navigate to ws2
	s.model.SetActiveWorkspace("ws2")
	assert.Equal(s.T(), "ws2", s.model.activeWS)

	// Navigate back
	s.model.NavigateBack()
	assert.Equal(s.T(), "ws1", s.model.activeWS)

	// Navigate forward
	s.model.NavigateForward()
	assert.Equal(s.T(), "ws2", s.model.activeWS)
}

// TestToggleCommandPalette tests command palette toggle
func (s *ModelTestSuite) TestToggleCommandPalette() {
	assert.False(s.T(), s.model.commandPaletteOpen)

	s.model.ToggleCommandPalette()
	assert.True(s.T(), s.model.commandPaletteOpen)

	s.model.ToggleCommandPalette()
	assert.False(s.T(), s.model.commandPaletteOpen)
}

// TestToggleHelp tests help toggle
func (s *ModelTestSuite) TestToggleHelp() {
	assert.False(s.T(), s.model.helpOpen)

	s.model.ToggleHelp()
	assert.True(s.T(), s.model.helpOpen)

	s.model.ToggleHelp()
	assert.False(s.T(), s.model.helpOpen)
}

// TestSetTheme tests theme change
func (s *ModelTestSuite) TestSetTheme() {
	assert.Equal(s.T(), ThemeDark, s.model.theme)

	s.model.SetTheme(ThemeLight)
	assert.Equal(s.T(), ThemeLight, s.model.theme)
}

// MockWorkspace is a mock workspace for testing
type MockWorkspace struct {
	id          string
	name        string
	description string
	icon        string
	initialized bool
	shortcuts   []Shortcut
}

func (w *MockWorkspace) ID() string                   { return w.id }
func (w *MockWorkspace) Name() string                 { return w.name }
func (w *MockWorkspace) Description() string          { return w.description }
func (w *MockWorkspace) Icon() string                 { return w.icon }
func (w *MockWorkspace) IsInitialized() bool          { return w.initialized }
func (w *MockWorkspace) Shortcuts() []Shortcut        { return w.shortcuts }
func (w *MockWorkspace) Init() tea.Cmd                { return nil }
func (w *MockWorkspace) Update(msg tea.Msg) (Workspace, tea.Cmd) { return w, nil }
func (w *MockWorkspace) View() string                 { return "Mock Workspace View" }

// Run the test suite
func TestModelSuite(t *testing.T) {
	suite.Run(t, new(ModelTestSuite))
}

// Benchmarks

func BenchmarkModelCreation(b *testing.B) {
	state := core.NewState("1.0.0")
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_ = NewModel(state, "1.0.0")
	}
}

func BenchmarkLoadPlugin(b *testing.B) {
	state := core.NewState("1.0.0")
	model := NewModel(state, "1.0.0")
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		model.LoadPlugin("plugin", "1.0.0")
	}
}

func BenchmarkAddEvent(b *testing.B) {
	state := core.NewState("1.0.0")
	model := NewModel(state, "1.0.0")
	event := Event{
		Type:      EventTypeInfo,
		Timestamp: time.Now(),
		Source:    "test",
	}
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		model.AddEvent(event)
	}
}

func BenchmarkUpdateMetrics(b *testing.B) {
	state := core.NewState("1.0.0")
	model := NewModel(state, "1.0.0")
	metrics := MetricsData{
		Timestamp: time.Now(),
		CPU:       50.0,
		Memory:    60.0,
	}
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		model.UpdateMetrics(metrics)
	}
}
