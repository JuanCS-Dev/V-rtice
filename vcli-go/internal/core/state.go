package core

import (
	"sync"
	"time"
)

// State represents the global application state
// Following MVU (Model-View-Update) pattern
type State struct {
	mu sync.RWMutex

	// Application metadata
	Version   string
	StartTime time.Time

	// Active workspace
	ActiveWorkspace string

	// Loaded plugins
	Plugins map[string]PluginInfo

	// Configuration
	Config Configuration

	// User context
	User UserContext

	// System state
	Online       bool
	LastSync     time.Time
	ErrorCount   int
	WarningCount int
}

// PluginInfo holds metadata about a loaded plugin
type PluginInfo struct {
	Name    string
	Version string
	Enabled bool
	LoadedAt time.Time
}

// Configuration represents application configuration
type Configuration struct {
	LogLevel      string
	CacheEnabled  bool
	OfflineMode   bool
	TelemetryEnabled bool
}

// UserContext holds user-specific information
type UserContext struct {
	ID          string
	Name        string
	Role        string
	Permissions []string
}

// NewState creates a new application state with defaults
func NewState(version string) *State {
	return &State{
		Version:   version,
		StartTime: time.Now(),
		Plugins:   make(map[string]PluginInfo),
		Config: Configuration{
			LogLevel:     "info",
			CacheEnabled: true,
			OfflineMode:  false,
			TelemetryEnabled: true,
		},
		User: UserContext{
			Permissions: make([]string, 0),
		},
		Online: true,
	}
}

// GetActiveWorkspace returns the active workspace name (thread-safe)
func (s *State) GetActiveWorkspace() string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.ActiveWorkspace
}

// SetActiveWorkspace sets the active workspace (thread-safe)
func (s *State) SetActiveWorkspace(workspace string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.ActiveWorkspace = workspace
}

// LoadPlugin registers a plugin in the state (thread-safe)
func (s *State) LoadPlugin(name, version string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Plugins[name] = PluginInfo{
		Name:     name,
		Version:  version,
		Enabled:  true,
		LoadedAt: time.Now(),
	}
}

// UnloadPlugin removes a plugin from the state (thread-safe)
func (s *State) UnloadPlugin(name string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.Plugins, name)
}

// GetPluginInfo returns plugin information (thread-safe)
func (s *State) GetPluginInfo(name string) (PluginInfo, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	info, exists := s.Plugins[name]
	return info, exists
}

// ListPlugins returns all loaded plugins (thread-safe)
func (s *State) ListPlugins() []PluginInfo {
	s.mu.RLock()
	defer s.mu.RUnlock()

	plugins := make([]PluginInfo, 0, len(s.Plugins))
	for _, info := range s.Plugins {
		plugins = append(plugins, info)
	}
	return plugins
}

// SetOnline sets the online status (thread-safe)
func (s *State) SetOnline(online bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Online = online
	if online {
		s.LastSync = time.Now()
	}
}

// IsOnline returns the online status (thread-safe)
func (s *State) IsOnline() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.Online
}

// IncrementErrorCount increments error counter (thread-safe)
func (s *State) IncrementErrorCount() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.ErrorCount++
}

// IncrementWarningCount increments warning counter (thread-safe)
func (s *State) IncrementWarningCount() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.WarningCount++
}

// GetStats returns current statistics (thread-safe)
func (s *State) GetStats() (errors, warnings int, uptime time.Duration) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.ErrorCount, s.WarningCount, time.Since(s.StartTime)
}

// Clone creates a deep copy of the state (thread-safe)
func (s *State) Clone() *State {
	s.mu.RLock()
	defer s.mu.RUnlock()

	cloned := &State{
		Version:      s.Version,
		StartTime:    s.StartTime,
		ActiveWorkspace: s.ActiveWorkspace,
		Plugins:      make(map[string]PluginInfo, len(s.Plugins)),
		Config:       s.Config,
		User:         s.User,
		Online:       s.Online,
		LastSync:     s.LastSync,
		ErrorCount:   s.ErrorCount,
		WarningCount: s.WarningCount,
	}

	// Deep copy plugins map
	for k, v := range s.Plugins {
		cloned.Plugins[k] = v
	}

	return cloned
}
