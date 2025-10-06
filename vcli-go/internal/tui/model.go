package tui

import (
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/verticedev/vcli-go/internal/core"
)

// Model represents the complete application state for the TUI
// following the Bubble Tea MVU (Model-View-Update) pattern
type Model struct {
	// Core state reference
	state *core.State

	// UI State
	activeView ViewType
	windowSize tea.WindowSizeMsg
	focused    ComponentID
	ready      bool

	// Workspace State
	workspaces map[string]Workspace
	activeWS   string

	// Plugin State
	loadedPlugins map[string]PluginInfo
	pluginViews   map[string]PluginView

	// Configuration
	config ConfigHierarchy

	// Navigation
	navigation Navigation

	// Search
	search SearchState

	// Events
	events      []Event
	maxEvents   int
	eventFilter map[EventType]bool

	// Metrics
	metrics     MetricsData
	metricsHist []MetricsData
	maxHistory  int

	// Errors & Warnings
	errors   []Error
	warnings []Error
	maxErrors int

	// Loading State
	loading map[string]LoadingState

	// Notifications
	notifications []Notification
	maxNotifs     int

	// Offline Mode
	offlineMode    bool
	lastSync       time.Time
	syncInProgress bool
	queuedOps      int

	// User Context
	user UserContext

	// Theme
	theme Theme

	// Command Palette
	commandPaletteOpen bool
	commandFilter      string

	// Help
	helpOpen bool

	// Keyboard Shortcuts
	shortcuts map[string]KeyBinding

	// Version Info
	version   string
	buildTime time.Time
}

// PluginInfo holds metadata about a loaded plugin
type PluginInfo struct {
	Name        string
	Version     string
	Enabled     bool
	Healthy     bool
	LoadedAt    time.Time
	LastHealth  time.Time
	ErrorCount  int
	Description string
}

// Notification represents a UI notification
type Notification struct {
	ID        string
	Title     string
	Message   string
	Severity  Severity
	Timestamp time.Time
	Duration  time.Duration
	Dismissed bool
}

// NewModel creates and initializes a new TUI Model
func NewModel(state *core.State, version string) Model {
	return Model{
		state:   state,
		version: version,

		// UI State
		activeView: ViewTypeWorkspace,
		focused:    ComponentIDWorkspace,
		ready:      false,

		// Workspace State
		workspaces: make(map[string]Workspace),
		activeWS:   "",

		// Plugin State
		loadedPlugins: make(map[string]PluginInfo),
		pluginViews:   make(map[string]PluginView),

		// Navigation
		navigation: Navigation{
			History: make([]string, 0, 50),
			Current: -1,
		},

		// Search
		search: SearchState{
			Active:  false,
			Query:   "",
			Results: make([]SearchResult, 0),
		},

		// Events
		events:      make([]Event, 0, 1000),
		maxEvents:   1000,
		eventFilter: make(map[EventType]bool),

		// Metrics
		metrics:     MetricsData{},
		metricsHist: make([]MetricsData, 0, 100),
		maxHistory:  100,

		// Errors & Warnings
		errors:    make([]Error, 0, 100),
		warnings:  make([]Error, 0, 100),
		maxErrors: 100,

		// Loading State
		loading: make(map[string]LoadingState),

		// Notifications
		notifications: make([]Notification, 0, 20),
		maxNotifs:     20,

		// Offline Mode
		offlineMode:    false,
		lastSync:       time.Now(),
		syncInProgress: false,
		queuedOps:      0,

		// User Context
		user: UserContext{},

		// Theme
		theme: ThemeDark,

		// Command Palette
		commandPaletteOpen: false,
		commandFilter:      "",

		// Help
		helpOpen: false,

		// Keyboard Shortcuts
		shortcuts: initDefaultShortcuts(),

		// Version
		buildTime: time.Now(),
	}
}

// NewModelWithPlugins creates a new TUI Model with plugin manager integration
func NewModelWithPlugins(state *core.State, version string, pluginManager interface{}, ctx interface{}) Model {
	model := NewModel(state, version)

	// Note: Plugin manager integration is handled at the Update level
	// The plugin manager wrapper is created separately and used via commands
	// This allows the model to remain pure and the plugin system to be optional

	return model
}

// Init initializes the Model and returns initial commands
// This is called once when the program starts
func (m Model) Init() tea.Cmd {
	return tea.Batch(
		m.loadWorkspaces(),
		m.loadPlugins(),
		m.startMetricsTicker(),
		m.startTickTicker(),
	)
}

// GetActiveWorkspace returns the currently active workspace
func (m Model) GetActiveWorkspace() Workspace {
	if m.activeWS == "" {
		return nil
	}
	return m.workspaces[m.activeWS]
}

// SetActiveWorkspace changes the active workspace
func (m *Model) SetActiveWorkspace(wsID string) error {
	if _, exists := m.workspaces[wsID]; !exists {
		return NewModelError("workspace not found: " + wsID)
	}

	// Save current position in navigation history
	if m.activeWS != "" {
		m.navigation.History = append(m.navigation.History, m.activeWS)
		m.navigation.Current++
	}

	m.activeWS = wsID
	m.activeView = ViewTypeWorkspace

	return nil
}

// RegisterWorkspace registers a new workspace
func (m *Model) RegisterWorkspace(ws Workspace) {
	m.workspaces[ws.ID()] = ws
}

// UnregisterWorkspace removes a workspace
func (m *Model) UnregisterWorkspace(wsID string) {
	delete(m.workspaces, wsID)
	if m.activeWS == wsID {
		m.activeWS = ""
	}
}

// LoadPlugin loads a plugin into the model
func (m *Model) LoadPlugin(name, version string) {
	m.loadedPlugins[name] = PluginInfo{
		Name:       name,
		Version:    version,
		Enabled:    true,
		Healthy:    true,
		LoadedAt:   time.Now(),
		LastHealth: time.Now(),
		ErrorCount: 0,
	}
}

// UnloadPlugin removes a plugin from the model
func (m *Model) UnloadPlugin(name string) {
	delete(m.loadedPlugins, name)
	delete(m.pluginViews, name)
}

// UpdatePluginHealth updates plugin health status
func (m *Model) UpdatePluginHealth(name string, healthy bool) {
	if info, exists := m.loadedPlugins[name]; exists {
		info.Healthy = healthy
		info.LastHealth = time.Now()
		if !healthy {
			info.ErrorCount++
		}
		m.loadedPlugins[name] = info
	}
}

// AddEvent adds a new event to the event log
func (m *Model) AddEvent(event Event) {
	m.events = append(m.events, event)

	// Trim if exceeds max
	if len(m.events) > m.maxEvents {
		m.events = m.events[len(m.events)-m.maxEvents:]
	}
}

// ClearEvents clears events older than specified time
func (m *Model) ClearEvents(olderThan time.Time) {
	filtered := make([]Event, 0)
	for _, evt := range m.events {
		if evt.Timestamp.After(olderThan) {
			filtered = append(filtered, evt)
		}
	}
	m.events = filtered
}

// AddError adds an error to the error log
func (m *Model) AddError(err Error) {
	m.errors = append(m.errors, err)

	// Trim if exceeds max
	if len(m.errors) > m.maxErrors {
		m.errors = m.errors[len(m.errors)-m.maxErrors:]
	}
}

// AddWarning adds a warning to the warning log
func (m *Model) AddWarning(warning Error) {
	m.warnings = append(m.warnings, warning)

	// Trim if exceeds max
	if len(m.warnings) > m.maxErrors {
		m.warnings = m.warnings[len(m.warnings)-m.maxErrors:]
	}
}

// ClearErrors clears all errors
func (m *Model) ClearErrors() {
	m.errors = make([]Error, 0, m.maxErrors)
}

// ClearWarnings clears all warnings
func (m *Model) ClearWarnings() {
	m.warnings = make([]Error, 0, m.maxErrors)
}

// UpdateMetrics updates current metrics and adds to history
func (m *Model) UpdateMetrics(metrics MetricsData) {
	m.metrics = metrics

	// Add to history
	m.metricsHist = append(m.metricsHist, metrics)

	// Trim history if exceeds max
	if len(m.metricsHist) > m.maxHistory {
		m.metricsHist = m.metricsHist[len(m.metricsHist)-m.maxHistory:]
	}
}

// StartLoading starts a loading state
func (m *Model) StartLoading(id, message string) {
	m.loading[id] = LoadingState{
		Active:    true,
		Message:   message,
		StartTime: time.Now(),
	}
}

// StopLoading stops a loading state
func (m *Model) StopLoading(id string) {
	delete(m.loading, id)
}

// IsLoading checks if a loading state is active
func (m Model) IsLoading(id string) bool {
	if state, exists := m.loading[id]; exists {
		return state.Active
	}
	return false
}

// AddNotification adds a notification
func (m *Model) AddNotification(notif Notification) {
	notif.Timestamp = time.Now()
	notif.Dismissed = false
	m.notifications = append(m.notifications, notif)

	// Trim if exceeds max
	if len(m.notifications) > m.maxNotifs {
		m.notifications = m.notifications[1:]
	}
}

// DismissNotification dismisses a notification by ID
func (m *Model) DismissNotification(id string) {
	for i, notif := range m.notifications {
		if notif.ID == id {
			m.notifications[i].Dismissed = true
			break
		}
	}
}

// GetActiveNotifications returns non-dismissed notifications
func (m Model) GetActiveNotifications() []Notification {
	active := make([]Notification, 0)
	for _, notif := range m.notifications {
		if !notif.Dismissed {
			active = append(active, notif)
		}
	}
	return active
}

// SetOfflineMode sets offline mode status
func (m *Model) SetOfflineMode(enabled bool) {
	m.offlineMode = enabled
	if !enabled {
		m.lastSync = time.Now()
	}
}

// SetSyncInProgress sets sync in progress status
func (m *Model) SetSyncInProgress(inProgress bool) {
	m.syncInProgress = inProgress
	if !inProgress {
		m.lastSync = time.Now()
	}
}

// NavigateBack navigates to previous location
func (m *Model) NavigateBack() {
	if m.navigation.Current > 0 {
		m.navigation.Current--
		m.activeWS = m.navigation.History[m.navigation.Current]
		m.activeView = ViewTypeWorkspace
	}
}

// NavigateForward navigates to next location
func (m *Model) NavigateForward() {
	if m.navigation.Current < len(m.navigation.History)-1 {
		m.navigation.Current++
		m.activeWS = m.navigation.History[m.navigation.Current]
		m.activeView = ViewTypeWorkspace
	}
}

// ToggleCommandPalette toggles command palette visibility
func (m *Model) ToggleCommandPalette() {
	m.commandPaletteOpen = !m.commandPaletteOpen
}

// ToggleHelp toggles help visibility
func (m *Model) ToggleHelp() {
	m.helpOpen = !m.helpOpen
}

// SetTheme changes the UI theme
func (m *Model) SetTheme(theme Theme) {
	m.theme = theme
}

// loadWorkspaces returns a command to load available workspaces
// Note: Workspace discovery would scan workspace registry or config files.
// Current implementation initializes with default workspace.
func (m Model) loadWorkspaces() tea.Cmd {
	return func() tea.Msg {
		// Initialize with default workspace
		// Workspace discovery would use WorkspaceRegistry when integrated
		return WorkspaceInitializedMsg{
			WorkspaceID: "default",
		}
	}
}

// loadPlugins returns a command to load available plugins
// Note: Plugin discovery is handled by PluginManager when integrated (see root.go).
// This command initializes core plugin for standalone mode.
func (m Model) loadPlugins() tea.Cmd {
	return func() tea.Msg {
		// Initialize core plugin for standalone mode
		// Real plugin loading uses PluginManager (see NewModelWithPlugins)
		return PluginLoadedMsg{
			PluginName: "core",
			Version:    "1.0.0",
			Success:    true,
			Error:      nil,
		}
	}
}

// startMetricsTicker returns a command that sends metrics updates periodically
func (m Model) startMetricsTicker() tea.Cmd {
	return tea.Tick(5*time.Second, func(t time.Time) tea.Msg {
		return NewMetricsTickMsg()
	})
}

// startTickTicker returns a command that sends tick updates periodically
func (m Model) startTickTicker() tea.Cmd {
	return tea.Tick(100*time.Millisecond, func(t time.Time) tea.Msg {
		return NewTickMsg()
	})
}

// initDefaultShortcuts initializes default keyboard shortcuts
func initDefaultShortcuts() map[string]KeyBinding {
	return map[string]KeyBinding{
		"ctrl+p": {
			Key:  "ctrl+p",
			Help: "Open command palette",
			Handler: func() tea.Msg {
				return CommandPaletteToggleMsg{}
			},
		},
		"ctrl+w": {
			Key:  "ctrl+w",
			Help: "Switch workspace",
			Handler: func() tea.Msg {
				return ViewChangeMsg{NewView: ViewTypeList}
			},
		},
		"?": {
			Key:  "?",
			Help: "Toggle help",
			Handler: func() tea.Msg {
				return HelpToggleMsg{}
			},
		},
		"ctrl+r": {
			Key:  "ctrl+r",
			Help: "Refresh view",
			Handler: func() tea.Msg {
				return MetricsTickMsg{Timestamp: time.Now()}
			},
		},
	}
}

// ModelError represents a model error
type ModelError struct {
	message string
}

func (e ModelError) Error() string {
	return e.message
}

// NewModelError creates a new model error
func NewModelError(message string) ModelError {
	return ModelError{message: message}
}
