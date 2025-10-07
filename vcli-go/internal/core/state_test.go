package core

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/suite"
)

// StateSuite is a test suite for State
type StateSuite struct {
	suite.Suite
	state *State
}

// SetupTest runs before each test
func (s *StateSuite) SetupTest() {
	s.state = NewState("1.0.0-test")
}

// TestStateCreation tests state initialization
func (s *StateSuite) TestStateCreation() {
	assert.NotNil(s.T(), s.state)
	assert.Equal(s.T(), "1.0.0-test", s.state.Version)
	assert.NotZero(s.T(), s.state.StartTime)
	assert.True(s.T(), s.state.Online)
	assert.Empty(s.T(), s.state.Plugins)
	assert.Equal(s.T(), "info", s.state.Config.LogLevel)
}

// TestWorkspaceManagement tests workspace get/set
func (s *StateSuite) TestWorkspaceManagement() {
	// Initially empty
	assert.Empty(s.T(), s.state.GetActiveWorkspace())

	// Set workspace
	s.state.SetActiveWorkspace("governance")
	assert.Equal(s.T(), "governance", s.state.GetActiveWorkspace())

	// Change workspace
	s.state.SetActiveWorkspace("investigation")
	assert.Equal(s.T(), "investigation", s.state.GetActiveWorkspace())
}

// TestPluginManagement tests plugin load/unload
func (s *StateSuite) TestPluginManagement() {
	// Load plugin
	s.state.LoadPlugin("kubernetes", "1.0.0")

	// Verify plugin exists
	info, exists := s.state.GetPluginInfo("kubernetes")
	assert.True(s.T(), exists)
	assert.Equal(s.T(), "kubernetes", info.Name)
	assert.Equal(s.T(), "1.0.0", info.Version)
	assert.True(s.T(), info.Enabled)
	assert.NotZero(s.T(), info.LoadedAt)

	// List plugins
	plugins := s.state.ListPlugins()
	assert.Len(s.T(), plugins, 1)
	assert.Equal(s.T(), "kubernetes", plugins[0].Name)

	// Unload plugin
	s.state.UnloadPlugin("kubernetes")
	_, exists = s.state.GetPluginInfo("kubernetes")
	assert.False(s.T(), exists)
	assert.Empty(s.T(), s.state.ListPlugins())
}

// TestMultiplePlugins tests multiple plugin management
func (s *StateSuite) TestMultiplePlugins() {
	// Load multiple plugins
	s.state.LoadPlugin("kubernetes", "1.0.0")
	s.state.LoadPlugin("prometheus", "2.0.0")
	s.state.LoadPlugin("git", "1.5.0")

	// Verify all loaded
	plugins := s.state.ListPlugins()
	assert.Len(s.T(), plugins, 3)

	// Verify each exists
	for _, name := range []string{"kubernetes", "prometheus", "git"} {
		_, exists := s.state.GetPluginInfo(name)
		assert.True(s.T(), exists, "Plugin %s should exist", name)
	}
}

// TestOnlineStatus tests online/offline state
func (s *StateSuite) TestOnlineStatus() {
	// Initially online
	assert.True(s.T(), s.state.IsOnline())

	// Set offline
	s.state.SetOnline(false)
	assert.False(s.T(), s.state.IsOnline())

	// Set back online (should update LastSync)
	beforeSync := s.state.LastSync
	time.Sleep(10 * time.Millisecond)
	s.state.SetOnline(true)
	assert.True(s.T(), s.state.IsOnline())
	assert.True(s.T(), s.state.LastSync.After(beforeSync))
}

// TestErrorWarningCounters tests error/warning tracking
func (s *StateSuite) TestErrorWarningCounters() {
	// Initially zero
	errors, warnings, _ := s.state.GetStats()
	assert.Equal(s.T(), 0, errors)
	assert.Equal(s.T(), 0, warnings)

	// Increment errors
	s.state.IncrementErrorCount()
	s.state.IncrementErrorCount()
	errors, warnings, _ = s.state.GetStats()
	assert.Equal(s.T(), 2, errors)
	assert.Equal(s.T(), 0, warnings)

	// Increment warnings
	s.state.IncrementWarningCount()
	errors, warnings, _ = s.state.GetStats()
	assert.Equal(s.T(), 2, errors)
	assert.Equal(s.T(), 1, warnings)
}

// TestUptimeTracking tests uptime calculation
func (s *StateSuite) TestUptimeTracking() {
	time.Sleep(50 * time.Millisecond)
	_, _, uptime := s.state.GetStats()
	assert.True(s.T(), uptime >= 50*time.Millisecond)
}

// TestClone tests state cloning
func (s *StateSuite) TestClone() {
	// Setup original state
	s.state.SetActiveWorkspace("governance")
	s.state.LoadPlugin("kubernetes", "1.0.0")
	s.state.IncrementErrorCount()
	s.state.SetOnline(false)

	// Clone
	cloned := s.state.Clone()

	// Verify clone matches original
	assert.Equal(s.T(), s.state.Version, cloned.Version)
	assert.Equal(s.T(), s.state.ActiveWorkspace, cloned.ActiveWorkspace)
	assert.Equal(s.T(), s.state.ErrorCount, cloned.ErrorCount)
	assert.Equal(s.T(), s.state.Online, cloned.Online)
	assert.Len(s.T(), cloned.Plugins, len(s.state.Plugins))

	// Verify independence (modifying clone shouldn't affect original)
	cloned.SetActiveWorkspace("investigation")
	assert.Equal(s.T(), "governance", s.state.GetActiveWorkspace())
	assert.Equal(s.T(), "investigation", cloned.GetActiveWorkspace())
}

// TestConcurrentAccess tests thread-safety
func (s *StateSuite) TestConcurrentAccess() {
	done := make(chan bool, 3)

	// Goroutine 1: Load plugins
	go func() {
		for i := 0; i < 100; i++ {
			s.state.LoadPlugin("plugin", "1.0.0")
		}
		done <- true
	}()

	// Goroutine 2: Change workspace
	go func() {
		for i := 0; i < 100; i++ {
			s.state.SetActiveWorkspace("workspace")
		}
		done <- true
	}()

	// Goroutine 3: Increment counters
	go func() {
		for i := 0; i < 100; i++ {
			s.state.IncrementErrorCount()
			s.state.IncrementWarningCount()
		}
		done <- true
	}()

	// Wait for all goroutines
	for i := 0; i < 3; i++ {
		<-done
	}

	// Verify no race conditions (test should pass with -race flag)
	errors, warnings, _ := s.state.GetStats()
	assert.Equal(s.T(), 100, errors)
	assert.Equal(s.T(), 100, warnings)
}

// TestStateSuite runs the test suite
func TestStateSuite(t *testing.T) {
	suite.Run(t, new(StateSuite))
}

// Benchmark state operations
func BenchmarkStateSetWorkspace(b *testing.B) {
	state := NewState("1.0.0")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		state.SetActiveWorkspace("test")
	}
}

func BenchmarkStateLoadPlugin(b *testing.B) {
	state := NewState("1.0.0")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		state.LoadPlugin("plugin", "1.0.0")
	}
}

func BenchmarkStateClone(b *testing.B) {
	state := NewState("1.0.0")
	state.LoadPlugin("k8s", "1.0")
	state.LoadPlugin("prometheus", "2.0")
	state.SetActiveWorkspace("governance")
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = state.Clone()
	}
}
