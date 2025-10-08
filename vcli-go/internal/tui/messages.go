package tui

import (
	"time"
)

// Message types for the MVU update cycle
// All messages implement tea.Msg interface (marker interface, no methods required)

// --- Workspace Messages ---

// WorkspaceSwitchMsg is sent when user switches workspace
type WorkspaceSwitchMsg struct {
	WorkspaceID string
	Force       bool // If true, switch even if unsaved changes
}

// WorkspaceLoadedMsg is sent when workspace data is loaded
type WorkspaceLoadedMsg struct {
	WorkspaceID string
	Success     bool
	Error       error
}

// WorkspaceInitializedMsg is sent when workspace initialization completes
type WorkspaceInitializedMsg struct {
	WorkspaceID string
}

// --- Plugin Messages ---

// PluginLoadMsg is sent to load a plugin
type PluginLoadMsg struct {
	PluginName string
	PluginPath string
}

// PluginLoadedMsg is sent when plugin load completes
type PluginLoadedMsg struct {
	PluginName string
	Version    string
	Success    bool
	Error      error
}

// PluginUnloadMsg is sent to unload a plugin
type PluginUnloadMsg struct {
	PluginName string
}

// PluginUnloadedMsg is sent when plugin unload completes
type PluginUnloadedMsg struct {
	PluginName string
	Success    bool
	Error      error
}

// PluginHealthMsg is sent with plugin health updates
type PluginHealthMsg struct {
	PluginName string
	Healthy    bool
	Message    string
}

// --- Configuration Messages ---

// ConfigUpdateMsg is sent when configuration changes
type ConfigUpdateMsg struct {
	Section string      // Which config section changed
	Key     string      // Which key changed
	Value   interface{} // New value
}

// ConfigReloadMsg is sent to trigger config reload
type ConfigReloadMsg struct {
	Source string // Which config source changed
}

// ConfigLoadedMsg is sent when config reload completes
type ConfigLoadedMsg struct {
	Success bool
	Error   error
}

// --- Offline Mode Messages ---

// OfflineModeMsg is sent to toggle offline mode
type OfflineModeMsg struct {
	Enabled bool
}

// OfflineSyncMsg is sent to trigger offline sync
type OfflineSyncMsg struct {
	Force bool
}

// OfflineSyncProgressMsg is sent during sync
type OfflineSyncProgressMsg struct {
	Total     int
	Processed int
	Current   string
}

// OfflineSyncCompletedMsg is sent when sync completes
type OfflineSyncCompletedMsg struct {
	Success   bool
	Synced    int
	Failed    int
	Conflicts int
	Error     error
}

// --- Metrics Messages ---

// MetricsUpdateMsg is sent with updated metrics
type MetricsUpdateMsg struct {
	Data MetricsData
}

// MetricsTickMsg is sent periodically to trigger metrics collection
type MetricsTickMsg struct {
	Timestamp time.Time
}

// --- Event Messages ---

// EventMsg wraps a system event
type EventMsg struct {
	Event Event
}

// EventClearMsg is sent to clear old events
type EventClearMsg struct {
	OlderThan time.Time
}

// --- Error Messages ---

// ErrorMsg is sent when an error occurs
type ErrorMsg struct {
	Error   error
	Context string
	Fatal   bool
}

// ErrorClearMsg is sent to clear errors
type ErrorClearMsg struct {
	All bool
}

// --- UI Messages ---

// ViewChangeMsg is sent to change the active view
type ViewChangeMsg struct {
	NewView ViewType
}

// FocusChangeMsg is sent to change component focus
type FocusChangeMsg struct {
	ComponentID ComponentID
}

// CommandPaletteToggleMsg toggles command palette
type CommandPaletteToggleMsg struct{}

// HelpToggleMsg toggles help display
type HelpToggleMsg struct{}

// ThemeChangeMsg changes the UI theme
type ThemeChangeMsg struct {
	Theme Theme
}

// --- Navigation Messages ---

// NavigateBackMsg navigates to previous view
type NavigateBackMsg struct{}

// NavigateForwardMsg navigates to next view
type NavigateForwardMsg struct{}

// NavigateToMsg navigates to specific location
type NavigateToMsg struct {
	Location string
	SaveHistory bool
}

// --- Search Messages ---

// SearchStartMsg starts a search
type SearchStartMsg struct {
	Query string
}

// SearchResultsMsg contains search results
type SearchResultsMsg struct {
	Query   string
	Results []SearchResult
}

// SearchClearMsg clears search state
type SearchClearMsg struct{}

// --- Loading Messages ---

// LoadingStartMsg indicates loading started
type LoadingStartMsg struct {
	ID      string
	Message string
}

// LoadingStopMsg indicates loading completed
type LoadingStopMsg struct {
	ID string
}

// --- Clipboard Messages ---

// ClipboardCopyMsg copies text to clipboard
type ClipboardCopyMsg struct {
	Text string
}

// ClipboardPasteMsg pastes from clipboard
type ClipboardPasteMsg struct {
	Text string
}

// --- Notification Messages ---

// NotificationMsg displays a notification
type NotificationMsg struct {
	Title    string
	Message  string
	Severity Severity
	Duration time.Duration
}

// NotificationDismissMsg dismisses a notification
type NotificationDismissMsg struct {
	ID string
}

// --- User Input Messages ---

// ConfirmMsg requests user confirmation
type ConfirmMsg struct {
	Title    string
	Message  string
	Callback func(confirmed bool) Msg
}

// InputRequestMsg requests user input
type InputRequestMsg struct {
	Prompt   string
	Default  string
	Callback func(input string) Msg
}

// --- Keyboard Shortcut Messages ---

// ShortcutExecuteMsg executes a keyboard shortcut
type ShortcutExecuteMsg struct {
	Key    string
	Action func() Msg
}

// --- Tick Messages ---

// TickMsg is sent periodically for animations/updates
type TickMsg struct {
	Timestamp time.Time
}

// --- Resize Messages ---

// ResizeMsg is sent when terminal is resized
// (Note: tea.WindowSizeMsg is built-in, but we may need custom handling)
type ResizeMsg struct {
	Width  int
	Height int
}

// --- State Snapshot Messages ---

// StateSnapshotSaveMsg saves current state
type StateSnapshotSaveMsg struct {
	ID string
}

// StateSnapshotRestoreMsg restores saved state
type StateSnapshotRestoreMsg struct {
	ID string
}

// --- Batch Messages ---

// BatchMsg wraps multiple messages to process together
type BatchMsg struct {
	Messages []Msg
}

// Msg is a marker interface for all messages
// (In Go, tea.Msg is interface{}, so any type satisfies it)
type Msg interface{}

// --- Helper Functions ---

// NewErrorMsg creates a new error message
func NewErrorMsg(err error, context string) ErrorMsg {
	return ErrorMsg{
		Error:   err,
		Context: context,
		Fatal:   false,
	}
}

// NewFatalErrorMsg creates a fatal error message
func NewFatalErrorMsg(err error, context string) ErrorMsg {
	return ErrorMsg{
		Error:   err,
		Context: context,
		Fatal:   true,
	}
}

// NewEventMsg creates a new event message
func NewEventMsg(eventType EventType, source string, data interface{}, severity Severity) EventMsg {
	return EventMsg{
		Event: Event{
			Type:      eventType,
			Timestamp: time.Now(),
			Source:    source,
			Data:      data,
			Severity:  severity,
		},
	}
}

// NewNotificationMsg creates a notification message
func NewNotificationMsg(title, message string, severity Severity, duration time.Duration) NotificationMsg {
	return NotificationMsg{
		Title:    title,
		Message:  message,
		Severity: severity,
		Duration: duration,
	}
}

// NewMetricsTickMsg creates a metrics tick message
func NewMetricsTickMsg() MetricsTickMsg {
	return MetricsTickMsg{
		Timestamp: time.Now(),
	}
}

// NewTickMsg creates a tick message
func NewTickMsg() TickMsg {
	return TickMsg{
		Timestamp: time.Now(),
	}
}
