package plugins

import (
	"context"
	"testing"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
)

// PluginManagerTestSuite is the test suite for PluginManager
type PluginManagerTestSuite struct {
	suite.Suite
	ctx     context.Context
	manager *PluginManager
	loader  *InMemoryLoader
	sandbox *NoopSandbox
	registry *LocalRegistry
}

// SetupTest runs before each test
func (s *PluginManagerTestSuite) SetupTest() {
	s.ctx = context.Background()
	s.loader = NewInMemoryLoader()
	s.sandbox = NewNoopSandbox()
	s.registry = NewLocalRegistry("/tmp/vcli-plugins")
	s.manager = NewPluginManager(s.loader, s.sandbox, s.registry)
}

// TearDownTest runs after each test
func (s *PluginManagerTestSuite) TearDownTest() {
	s.manager.Stop(s.ctx)
}

// TestManagerCreation tests manager creation
func (s *PluginManagerTestSuite) TestManagerCreation() {
	assert.NotNil(s.T(), s.manager)
	assert.NotNil(s.T(), s.manager.plugins)
	assert.NotNil(s.T(), s.manager.events)
	assert.Equal(s.T(), 30*time.Second, s.manager.healthCheckInterval)
	assert.Equal(s.T(), 5*time.Second, s.manager.resourceCheckInterval)
}

// TestLoadPlugin tests plugin loading
func (s *PluginManagerTestSuite) TestLoadPlugin() {
	// Create mock plugin
	mockPlugin := &MockPlugin{
		metadata: Metadata{
			Name:    "test-plugin",
			Version: "1.0.0",
		},
	}

	// Register plugin in loader
	s.loader.Register("test-plugin", mockPlugin)

	// Load plugin
	err := s.manager.LoadPlugin(s.ctx, "test-plugin")
	assert.NoError(s.T(), err)

	// Verify plugin is loaded
	info, err := s.manager.GetPlugin("test-plugin")
	assert.NoError(s.T(), err)
	assert.Equal(s.T(), "test-plugin", info.Metadata.Name)
	assert.Equal(s.T(), LoadStatusLoaded, info.Status)
}

// TestLoadPluginAlreadyLoaded tests loading already loaded plugin
func (s *PluginManagerTestSuite) TestLoadPluginAlreadyLoaded() {
	mockPlugin := &MockPlugin{
		metadata: Metadata{Name: "test", Version: "1.0.0"},
	}

	s.loader.Register("test", mockPlugin)

	// Load once
	err := s.manager.LoadPlugin(s.ctx, "test")
	assert.NoError(s.T(), err)

	// Try to load again
	err = s.manager.LoadPlugin(s.ctx, "test")
	assert.Error(s.T(), err)
	assert.Contains(s.T(), err.Error(), "already loaded")
}

// TestUnloadPlugin tests plugin unloading
func (s *PluginManagerTestSuite) TestUnloadPlugin() {
	mockPlugin := &MockPlugin{
		metadata: Metadata{Name: "test", Version: "1.0.0"},
	}

	s.loader.Register("test", mockPlugin)

	// Load plugin
	err := s.manager.LoadPlugin(s.ctx, "test")
	assert.NoError(s.T(), err)

	// Unload plugin
	err = s.manager.UnloadPlugin(s.ctx, "test")
	assert.NoError(s.T(), err)

	// Verify plugin is unloaded
	_, err = s.manager.GetPlugin("test")
	assert.Error(s.T(), err)
}

// TestStartStopPlugin tests plugin start/stop
func (s *PluginManagerTestSuite) TestStartStopPlugin() {
	mockPlugin := &MockPlugin{
		metadata: Metadata{Name: "test", Version: "1.0.0"},
	}

	s.loader.Register("test", mockPlugin)

	// Load plugin
	err := s.manager.LoadPlugin(s.ctx, "test")
	assert.NoError(s.T(), err)

	// Start plugin
	err = s.manager.StartPlugin(s.ctx, "test")
	assert.NoError(s.T(), err)

	info, _ := s.manager.GetPlugin("test")
	assert.Equal(s.T(), LoadStatusRunning, info.Status)
	assert.True(s.T(), mockPlugin.started)

	// Stop plugin
	err = s.manager.StopPlugin(s.ctx, "test")
	assert.NoError(s.T(), err)

	info, _ = s.manager.GetPlugin("test")
	assert.Equal(s.T(), LoadStatusStopped, info.Status)
	assert.True(s.T(), mockPlugin.stopped)
}

// TestListPlugins tests listing plugins
func (s *PluginManagerTestSuite) TestListPlugins() {
	// Load multiple plugins
	for i := 1; i <= 3; i++ {
		name := "plugin" + string(rune('0'+i))
		mockPlugin := &MockPlugin{
			metadata: Metadata{Name: name, Version: "1.0.0"},
		}
		s.loader.Register(name, mockPlugin)
		s.manager.LoadPlugin(s.ctx, name)
	}

	// List plugins
	plugins := s.manager.ListPlugins()
	assert.Len(s.T(), plugins, 3)
}

// TestHealthCheck tests plugin health check
func (s *PluginManagerTestSuite) TestHealthCheck() {
	mockPlugin := &MockPlugin{
		metadata: Metadata{Name: "test", Version: "1.0.0"},
		health: HealthStatus{
			Healthy: true,
			Message: "All good",
		},
	}

	s.loader.Register("test", mockPlugin)
	s.manager.LoadPlugin(s.ctx, "test")

	// Check health
	health, err := s.manager.HealthCheck(s.ctx, "test")
	assert.NoError(s.T(), err)
	assert.True(s.T(), health.Healthy)
	assert.Equal(s.T(), "All good", health.Message)
}

// TestPluginEvents tests plugin event emission
func (s *PluginManagerTestSuite) TestPluginEvents() {
	mockPlugin := &MockPlugin{
		metadata: Metadata{Name: "test", Version: "1.0.0"},
	}

	s.loader.Register("test", mockPlugin)

	// Start collecting events
	events := make([]Event, 0)
	go func() {
		for event := range s.manager.Events() {
			events = append(events, event)
		}
	}()

	// Load plugin (should emit event)
	s.manager.LoadPlugin(s.ctx, "test")

	// Give time for event to be emitted
	time.Sleep(10 * time.Millisecond)

	// Check events
	assert.GreaterOrEqual(s.T(), len(events), 1)
	assert.Equal(s.T(), EventTypeLoaded, events[0].Type)
}

// MockPlugin is a mock plugin for testing
type MockPlugin struct {
	metadata     Metadata
	health       HealthStatus
	initialized  bool
	started      bool
	stopped      bool
	capabilities []Capability
}

func (m *MockPlugin) Metadata() Metadata {
	return m.metadata
}

func (m *MockPlugin) Initialize(ctx context.Context, config map[string]interface{}) error {
	m.initialized = true
	return nil
}

func (m *MockPlugin) Start(ctx context.Context) error {
	m.started = true
	return nil
}

func (m *MockPlugin) Stop(ctx context.Context) error {
	m.stopped = true
	return nil
}

func (m *MockPlugin) Health() HealthStatus {
	return m.health
}

func (m *MockPlugin) Commands() []Command {
	return []Command{}
}

func (m *MockPlugin) View() View {
	return &MockView{}
}

func (m *MockPlugin) Capabilities() []Capability {
	if m.capabilities == nil {
		return []Capability{}
	}
	return m.capabilities
}

// MockView is a mock plugin view
type MockView struct{}

func (m *MockView) ID() string { return "mock" }
func (m *MockView) Render() string { return "Mock View" }
func (m *MockView) Update(msg tea.Msg) (View, tea.Cmd) { return m, nil }
func (m *MockView) Init() tea.Cmd { return nil }
func (m *MockView) Focus() {}
func (m *MockView) Blur() {}
func (m *MockView) IsFocused() bool { return false }

// Run the test suite
func TestPluginManagerSuite(t *testing.T) {
	suite.Run(t, new(PluginManagerTestSuite))
}

// Benchmarks

func BenchmarkLoadPlugin(b *testing.B) {
	ctx := context.Background()
	loader := NewInMemoryLoader()
	manager := NewPluginManager(loader, NewNoopSandbox(), NewLocalRegistry("/tmp"))

	mockPlugin := &MockPlugin{
		metadata: Metadata{Name: "bench", Version: "1.0.0"},
	}
	loader.Register("bench", mockPlugin)

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		manager.LoadPlugin(ctx, "bench")
		manager.UnloadPlugin(ctx, "bench")
	}
}

func BenchmarkHealthCheck(b *testing.B) {
	ctx := context.Background()
	loader := NewInMemoryLoader()
	manager := NewPluginManager(loader, NewNoopSandbox(), NewLocalRegistry("/tmp"))

	mockPlugin := &MockPlugin{
		metadata: Metadata{Name: "bench", Version: "1.0.0"},
		health: HealthStatus{Healthy: true},
	}
	loader.Register("bench", mockPlugin)
	manager.LoadPlugin(ctx, "bench")

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		manager.HealthCheck(ctx, "bench")
	}
}

func BenchmarkListPlugins(b *testing.B) {
	loader := NewInMemoryLoader()
	manager := NewPluginManager(loader, NewNoopSandbox(), NewLocalRegistry("/tmp"))

	// Load 10 plugins
	for i := 0; i < 10; i++ {
		name := "plugin" + string(rune('0'+i))
		mockPlugin := &MockPlugin{
			metadata: Metadata{Name: name, Version: "1.0.0"},
		}
		loader.Register(name, mockPlugin)
		manager.LoadPlugin(context.Background(), name)
	}

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		manager.ListPlugins()
	}
}
