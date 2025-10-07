package plugins

import (
	"context"
	"time"

	tea "github.com/charmbracelet/bubbletea"
)

// Plugin represents a vCLI plugin interface
// All plugins must implement this interface to be loaded into vCLI
type Plugin interface {
	// Metadata returns plugin metadata
	Metadata() Metadata

	// Initialize initializes the plugin with context and configuration
	Initialize(ctx context.Context, config map[string]interface{}) error

	// Start starts the plugin (async operations, background tasks)
	Start(ctx context.Context) error

	// Stop stops the plugin gracefully
	Stop(ctx context.Context) error

	// Health returns current health status
	Health() HealthStatus

	// Commands returns CLI commands provided by this plugin
	Commands() []Command

	// View returns the plugin's TUI view component (optional)
	View() View

	// Capabilities returns plugin capabilities
	Capabilities() []Capability
}

// Metadata contains plugin metadata
type Metadata struct {
	// Name is the unique plugin name
	Name string

	// Version is the semantic version
	Version string

	// Description is a brief description
	Description string

	// Author is the plugin author
	Author string

	// License is the software license
	License string

	// Homepage is the plugin homepage URL
	Homepage string

	// Tags are searchable tags
	Tags []string

	// Dependencies are required plugins
	Dependencies []Dependency

	// MinVCLIVersion is minimum vCLI version required
	MinVCLIVersion string

	// MaxVCLIVersion is maximum vCLI version supported (optional)
	MaxVCLIVersion string

	// LoadTime is when the plugin was loaded
	LoadTime time.Time
}

// Dependency represents a plugin dependency
type Dependency struct {
	// Name of the required plugin
	Name string

	// MinVersion is minimum version required
	MinVersion string

	// MaxVersion is maximum version supported (optional)
	MaxVersion string

	// Optional indicates if dependency is optional
	Optional bool
}

// HealthStatus represents plugin health status
type HealthStatus struct {
	// Healthy indicates if plugin is healthy
	Healthy bool

	// Message provides health status message
	Message string

	// LastCheck is when health was last checked
	LastCheck time.Time

	// Metrics contains health metrics
	Metrics map[string]interface{}
}

// Command represents a CLI command provided by plugin
type Command struct {
	// Name is the command name
	Name string

	// Aliases are command aliases
	Aliases []string

	// Short is brief description
	Short string

	// Long is detailed description
	Long string

	// Example shows usage example
	Example string

	// Handler is the command handler function
	Handler func(args []string) error

	// Subcommands are nested commands
	Subcommands []Command
}

// View represents a plugin's TUI view component
type View interface {
	// ID returns the view identifier
	ID() string

	// Render renders the view to string
	Render() string

	// Update processes Bubble Tea messages
	Update(msg tea.Msg) (View, tea.Cmd)

	// Init initializes the view
	Init() tea.Cmd

	// Focus sets focus on the view
	Focus()

	// Blur removes focus from the view
	Blur()

	// IsFocused returns if view is focused
	IsFocused() bool
}

// Capability represents a plugin capability
type Capability string

const (
	// CapabilityNetwork allows network access
	CapabilityNetwork Capability = "network"

	// CapabilityFilesystem allows filesystem access
	CapabilityFilesystem Capability = "filesystem"

	// CapabilityExec allows process execution
	CapabilityExec Capability = "exec"

	// CapabilityKubernetes allows Kubernetes API access
	CapabilityKubernetes Capability = "kubernetes"

	// CapabilityPrometheus allows Prometheus API access
	CapabilityPrometheus Capability = "prometheus"

	// CapabilityDatabase allows database access
	CapabilityDatabase Capability = "database"

	// CapabilityTUI allows TUI rendering
	CapabilityTUI Capability = "tui"

	// CapabilityCLI allows CLI commands
	CapabilityCLI Capability = "cli"
)

// LoadStatus represents plugin load status
type LoadStatus string

const (
	// LoadStatusUnloaded means plugin is not loaded
	LoadStatusUnloaded LoadStatus = "unloaded"

	// LoadStatusLoading means plugin is being loaded
	LoadStatusLoading LoadStatus = "loading"

	// LoadStatusLoaded means plugin is loaded and initialized
	LoadStatusLoaded LoadStatus = "loaded"

	// LoadStatusRunning means plugin is running
	LoadStatusRunning LoadStatus = "running"

	// LoadStatusStopping means plugin is stopping
	LoadStatusStopping LoadStatus = "stopping"

	// LoadStatusStopped means plugin is stopped
	LoadStatusStopped LoadStatus = "stopped"

	// LoadStatusFailed means plugin failed to load
	LoadStatusFailed LoadStatus = "failed"
)

// PluginInfo holds runtime plugin information
type PluginInfo struct {
	// Metadata is plugin metadata
	Metadata Metadata

	// Status is current load status
	Status LoadStatus

	// Health is current health status
	Health HealthStatus

	// Instance is the plugin instance
	Instance Plugin

	// LoadedAt is when plugin was loaded
	LoadedAt time.Time

	// StartedAt is when plugin was started
	StartedAt time.Time

	// StoppedAt is when plugin was stopped
	StoppedAt time.Time

	// ErrorCount is number of errors encountered
	ErrorCount int

	// LastError is the last error message
	LastError string

	// Config is plugin configuration
	Config map[string]interface{}

	// Resources tracks resource usage
	Resources ResourceUsage
}

// ResourceUsage tracks plugin resource usage
type ResourceUsage struct {
	// CPUPercent is CPU usage percentage
	CPUPercent float64

	// MemoryBytes is memory usage in bytes
	MemoryBytes uint64

	// GoroutineCount is number of goroutines
	GoroutineCount int

	// NetworkBytesIn is bytes received
	NetworkBytesIn uint64

	// NetworkBytesOut is bytes sent
	NetworkBytesOut uint64

	// LastUpdated is when usage was last updated
	LastUpdated time.Time
}

// RegistryEntry represents a plugin in the registry
type RegistryEntry struct {
	// Name is plugin name
	Name string

	// LatestVersion is latest available version
	LatestVersion string

	// Versions is list of available versions
	Versions []string

	// Description is brief description
	Description string

	// Author is plugin author
	Author string

	// Homepage is plugin homepage
	Homepage string

	// Tags are searchable tags
	Tags []string

	// Downloads is download count
	Downloads int

	// Rating is user rating (0-5)
	Rating float64

	// SourceURL is plugin source URL
	SourceURL string

	// Published is publication date
	Published time.Time

	// Updated is last update date
	Updated time.Time
}

// SandboxConfig configures plugin sandbox
type SandboxConfig struct {
	// Enabled indicates if sandbox is enabled
	Enabled bool

	// MaxCPUPercent is max CPU usage allowed
	MaxCPUPercent float64

	// MaxMemoryBytes is max memory allowed
	MaxMemoryBytes uint64

	// MaxGoroutines is max goroutines allowed
	MaxGoroutines int

	// MaxNetworkBytesPerSec is max network throughput
	MaxNetworkBytesPerSec uint64

	// AllowedCapabilities are allowed capabilities
	AllowedCapabilities []Capability

	// AllowedHosts are allowed network hosts (for network capability)
	AllowedHosts []string

	// AllowedPaths are allowed filesystem paths (for filesystem capability)
	AllowedPaths []string

	// Timeout is max execution time for operations
	Timeout time.Duration
}

// Loader is the plugin loader interface
type Loader interface {
	// Load loads a plugin from path
	Load(ctx context.Context, path string) (Plugin, error)

	// Unload unloads a plugin
	Unload(ctx context.Context, plugin Plugin) error

	// Reload reloads a plugin
	Reload(ctx context.Context, plugin Plugin) error

	// Validate validates plugin compatibility
	Validate(ctx context.Context, path string) error
}

// Registry is the plugin registry interface
type Registry interface {
	// Search searches for plugins
	Search(ctx context.Context, query string) ([]RegistryEntry, error)

	// Get gets plugin entry by name
	Get(ctx context.Context, name string) (*RegistryEntry, error)

	// List lists all plugins
	List(ctx context.Context) ([]RegistryEntry, error)

	// Download downloads plugin from registry
	Download(ctx context.Context, name, version string) (string, error)

	// Publish publishes plugin to registry (for plugin authors)
	Publish(ctx context.Context, path string, metadata Metadata) error
}

// Manager is the plugin manager interface
type Manager interface {
	// LoadPlugin loads a plugin by name or path
	LoadPlugin(ctx context.Context, nameOrPath string) error

	// UnloadPlugin unloads a plugin by name
	UnloadPlugin(ctx context.Context, name string) error

	// ReloadPlugin reloads a plugin by name
	ReloadPlugin(ctx context.Context, name string) error

	// StartPlugin starts a plugin by name
	StartPlugin(ctx context.Context, name string) error

	// StopPlugin stops a plugin by name
	StopPlugin(ctx context.Context, name string) error

	// GetPlugin gets plugin info by name
	GetPlugin(name string) (*PluginInfo, error)

	// ListPlugins lists all loaded plugins
	ListPlugins() []PluginInfo

	// HealthCheck performs health check on plugin
	HealthCheck(ctx context.Context, name string) (HealthStatus, error)

	// UpdateResources updates resource usage for plugin
	UpdateResources(name string) error
}

// Sandbox is the plugin sandbox interface
type Sandbox interface {
	// Enforce enforces sandbox restrictions on plugin
	Enforce(ctx context.Context, plugin Plugin, config SandboxConfig) error

	// CheckCapability checks if plugin has capability
	CheckCapability(plugin Plugin, capability Capability) bool

	// MonitorResources monitors plugin resource usage
	MonitorResources(ctx context.Context, plugin Plugin) (ResourceUsage, error)

	// Terminate terminates plugin if it violates sandbox
	Terminate(ctx context.Context, plugin Plugin, reason string) error
}

// Event represents a plugin system event
type Event struct {
	// Type is event type
	Type EventType

	// PluginName is plugin that triggered event
	PluginName string

	// Timestamp is when event occurred
	Timestamp time.Time

	// Message is event message
	Message string

	// Data is event data
	Data map[string]interface{}
}

// EventType represents plugin event type
type EventType string

const (
	// EventTypeLoaded means plugin was loaded
	EventTypeLoaded EventType = "loaded"

	// EventTypeUnloaded means plugin was unloaded
	EventTypeUnloaded EventType = "unloaded"

	// EventTypeStarted means plugin was started
	EventTypeStarted EventType = "started"

	// EventTypeStopped means plugin was stopped
	EventTypeStopped EventType = "stopped"

	// EventTypeHealthy means plugin became healthy
	EventTypeHealthy EventType = "healthy"

	// EventTypeUnhealthy means plugin became unhealthy
	EventTypeUnhealthy EventType = "unhealthy"

	// EventTypeError means plugin encountered error
	EventTypeError EventType = "error"

	// EventTypeResourceLimit means plugin hit resource limit
	EventTypeResourceLimit EventType = "resource_limit"
)

// PluginError represents a plugin error
type PluginError struct {
	// PluginName is the plugin that caused error
	PluginName string

	// Operation is the operation that failed
	Operation string

	// Err is the underlying error
	Err error

	// Timestamp is when error occurred
	Timestamp time.Time
}

// Error implements error interface
func (e PluginError) Error() string {
	return e.PluginName + ": " + e.Operation + ": " + e.Err.Error()
}

// Unwrap returns underlying error
func (e PluginError) Unwrap() error {
	return e.Err
}

// NewPluginError creates a new plugin error
func NewPluginError(pluginName, operation string, err error) PluginError {
	return PluginError{
		PluginName: pluginName,
		Operation:  operation,
		Err:        err,
		Timestamp:  time.Now(),
	}
}
