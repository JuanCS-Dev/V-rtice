package tui

import (
	"time"

	tea "github.com/charmbracelet/bubbletea"
)

// ViewType represents different view modes in the TUI
type ViewType string

const (
	// ViewTypeWorkspace displays a specific workspace
	ViewTypeWorkspace ViewType = "workspace"

	// ViewTypeList displays a list of items
	ViewTypeList ViewType = "list"

	// ViewTypeDetails displays detailed information
	ViewTypeDetails ViewType = "details"

	// ViewTypeHelp displays help information
	ViewTypeHelp ViewType = "help"

	// ViewTypeCommandPalette displays command palette
	ViewTypeCommandPalette ViewType = "command_palette"
)

// ComponentID identifies a UI component
type ComponentID string

const (
	// ComponentIDHeader identifies the header component
	ComponentIDHeader ComponentID = "header"

	// ComponentIDWorkspace identifies the workspace component
	ComponentIDWorkspace ComponentID = "workspace"

	// ComponentIDStatusBar identifies the status bar component
	ComponentIDStatusBar ComponentID = "status_bar"

	// ComponentIDSidebar identifies the sidebar component
	ComponentIDSidebar ComponentID = "sidebar"
)

// Workspace represents a TUI workspace interface
// Each workspace implements specific functionality (Governance, Investigation, etc.)
type Workspace interface {
	// ID returns the unique identifier of the workspace
	ID() string

	// Name returns the display name of the workspace
	Name() string

	// Description returns a brief description of the workspace
	Description() string

	// Icon returns the icon/emoji for the workspace
	Icon() string

	// Init initializes the workspace
	Init() tea.Cmd

	// Update processes messages and returns updated workspace
	Update(msg tea.Msg) (Workspace, tea.Cmd)

	// View renders the workspace
	View() string

	// IsInitialized returns whether the workspace has been initialized
	IsInitialized() bool

	// Shortcuts returns keyboard shortcuts specific to this workspace
	Shortcuts() []Shortcut
}

// Shortcut represents a keyboard shortcut
type Shortcut struct {
	Key         string
	Description string
	Action      func() tea.Msg
}

// Event represents a system event
type Event struct {
	Type      EventType
	Timestamp time.Time
	Source    string
	Data      interface{}
	Severity  Severity
}

// EventType categorizes events
type EventType string

const (
	EventTypeInfo      EventType = "info"
	EventTypeWarning   EventType = "warning"
	EventTypeError     EventType = "error"
	EventTypeSuccess   EventType = "success"
	EventTypeMetric    EventType = "metric"
	EventTypeDecision  EventType = "decision"
)

// Severity levels for events
type Severity string

const (
	SeverityLow      Severity = "low"
	SeverityMedium   Severity = "medium"
	SeverityHigh     Severity = "high"
	SeverityCritical Severity = "critical"
)

// MetricsData holds system metrics
type MetricsData struct {
	Timestamp     time.Time
	CPU           float64
	Memory        float64
	Disk          float64
	NetworkIn     float64
	NetworkOut    float64
	PluginsLoaded int
	Errors        int
	Warnings      int
}

// Error represents an application error
type Error struct {
	Code      string
	Message   string
	Timestamp time.Time
	Context   string
	Severity  Severity
}

// PluginView represents a plugin's TUI component
type PluginView interface {
	// ID returns the plugin view identifier
	ID() string

	// Render returns the view as a string
	Render() string

	// Update processes messages
	Update(msg tea.Msg) (PluginView, tea.Cmd)

	// Focus sets focus on the view
	Focus()

	// Blur removes focus from the view
	Blur()

	// IsFocused returns whether the view is focused
	IsFocused() bool
}

// Position represents a component position
type Position struct {
	X int
	Y int
}

// Size represents a component size
type Size struct {
	Width  int
	Height int
}

// Theme represents UI color theme
type Theme string

const (
	ThemeDark  Theme = "dark"
	ThemeLight Theme = "light"
)

// KeyBinding represents a keyboard binding
type KeyBinding struct {
	Key     string
	Help    string
	Handler func() tea.Msg
}

// LoadingState tracks loading status
type LoadingState struct {
	Active    bool
	Message   string
	StartTime time.Time
}

// UserContext holds user information
type UserContext struct {
	ID          string
	Name        string
	Role        string
	Permissions []string
	SessionID   string
}

// PermissionSet represents user permissions
type PermissionSet map[string]bool

// ConfigHierarchy represents merged configuration
type ConfigHierarchy struct {
	Global  GlobalConfig
	UI      UIConfig
	Plugins PluginConfigs
	User    UserConfig
}

// GlobalConfig holds global settings
type GlobalConfig struct {
	LogLevel      string
	CacheEnabled  bool
	OfflineMode   bool
	DefaultWorkspace string
}

// UIConfig holds UI-specific settings
type UIConfig struct {
	Theme           Theme
	RefreshRate     time.Duration
	ShowLineNumbers bool
	ShowHelp        bool
	CompactMode     bool
}

// PluginConfigs holds plugin configurations
type PluginConfigs map[string]PluginConfig

// PluginConfig holds a single plugin's configuration
type PluginConfig struct {
	Enabled  bool
	Priority int
	Settings map[string]interface{}
}

// UserConfig holds user-specific settings
type UserConfig struct {
	RecentWorkspaces []string
	Favorites        []string
	CustomShortcuts  []KeyBinding
}

// WindowState tracks window dimensions
type WindowState struct {
	Width   int
	Height  int
	Changed bool
}

// Navigation tracks navigation history
type Navigation struct {
	History []string
	Current int
}

// SearchState tracks search functionality
type SearchState struct {
	Active bool
	Query  string
	Results []SearchResult
}

// SearchResult represents a search result
type SearchResult struct {
	Title       string
	Description string
	Score       float64
	Action      func() tea.Msg
}
