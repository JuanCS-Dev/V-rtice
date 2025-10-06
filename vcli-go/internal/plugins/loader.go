package plugins

import (
	"context"
	"fmt"
	"os"
	"plugin"
	"strings"
)

// PluginLoader loads plugins from .so files
type PluginLoader struct {
	// loadedModules tracks loaded plugin modules
	loadedModules map[string]*plugin.Plugin

	// vcliVersion is the vCLI version for compatibility checking
	vcliVersion string
}

// NewPluginLoader creates a new plugin loader
func NewPluginLoader(vcliVersion string) *PluginLoader {
	return &PluginLoader{
		loadedModules: make(map[string]*plugin.Plugin),
		vcliVersion:   vcliVersion,
	}
}

// Load loads a plugin from path
func (pl *PluginLoader) Load(ctx context.Context, path string) (Plugin, error) {
	// Check if file exists
	if _, err := os.Stat(path); err != nil {
		return nil, fmt.Errorf("plugin file not found: %w", err)
	}

	// Open plugin
	p, err := plugin.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open plugin: %w", err)
	}

	// Look up NewPlugin symbol
	newPluginSym, err := p.Lookup("NewPlugin")
	if err != nil {
		return nil, fmt.Errorf("plugin missing NewPlugin function: %w", err)
	}

	// Type assert to plugin constructor
	newPluginFunc, ok := newPluginSym.(func() Plugin)
	if !ok {
		return nil, fmt.Errorf("NewPlugin has incorrect signature")
	}

	// Create plugin instance
	pluginInstance := newPluginFunc()

	// Store module reference
	pl.loadedModules[path] = p

	return pluginInstance, nil
}

// Unload unloads a plugin
func (pl *PluginLoader) Unload(ctx context.Context, plugin Plugin) error {
	// Note: Go doesn't support unloading plugins
	// We can only release our reference
	// The plugin will remain in memory until process exit

	metadata := plugin.Metadata()

	// Find and remove module reference
	for path, module := range pl.loadedModules {
		if module != nil {
			// Check if this module contains our plugin
			// (Simple heuristic: check path contains plugin name)
			if strings.Contains(path, metadata.Name) {
				delete(pl.loadedModules, path)
				break
			}
		}
	}

	return nil
}

// Reload reloads a plugin
func (pl *PluginLoader) Reload(ctx context.Context, plugin Plugin) error {
	// Note: Go's plugin system doesn't support unloading/reloading
	// This is a fundamental limitation - plugins stay in memory until process exit
	// Workaround: Use process restart or hot-reload via new binary

	return fmt.Errorf("plugin reload not supported (Go limitation: plugins cannot be unloaded)")
}

// Validate validates plugin compatibility
func (pl *PluginLoader) Validate(ctx context.Context, path string) error {
	// Check file exists
	if _, err := os.Stat(path); err != nil {
		return fmt.Errorf("plugin file not found: %w", err)
	}

	// Check file extension
	if !strings.HasSuffix(path, ".so") {
		return fmt.Errorf("invalid plugin file extension (expected .so)")
	}

	// Try to open plugin (validation only, we close immediately)
	p, err := plugin.Open(path)
	if err != nil {
		return fmt.Errorf("failed to validate plugin: %w", err)
	}

	// Check for required symbols
	if _, err := p.Lookup("NewPlugin"); err != nil {
		return fmt.Errorf("plugin missing NewPlugin function: %w", err)
	}

	// Additional validation could check:
	// - Plugin metadata
	// - Version compatibility
	// - Dependency requirements
	// - Security signatures

	return nil
}

// ValidateMetadata validates plugin metadata for compatibility
func (pl *PluginLoader) ValidateMetadata(metadata Metadata) error {
	// Check required fields
	if metadata.Name == "" {
		return fmt.Errorf("plugin name is required")
	}

	if metadata.Version == "" {
		return fmt.Errorf("plugin version is required")
	}

	// Check version compatibility
	if metadata.MinVCLIVersion != "" {
		if !pl.isVersionCompatible(pl.vcliVersion, metadata.MinVCLIVersion, metadata.MaxVCLIVersion) {
			return fmt.Errorf("plugin requires vCLI version %s-%s, current: %s",
				metadata.MinVCLIVersion,
				metadata.MaxVCLIVersion,
				pl.vcliVersion,
			)
		}
	}

	return nil
}

// isVersionCompatible checks if current version is compatible with min/max
func (pl *PluginLoader) isVersionCompatible(current, min, max string) bool {
	// Simple lexicographic comparison
	// Note: For semantic versioning, consider github.com/Masterminds/semver
	// This implementation works for simple version strings (e.g., "1.0.0")

	// Check if current >= min
	if min != "" && compareVersions(current, min) < 0 {
		return false
	}

	// Check if current <= max (if specified)
	if max != "" && compareVersions(current, max) > 0 {
		return false
	}

	return true
}

// compareVersions compares two version strings lexicographically
// Returns: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
// Note: This is a simple comparison suitable for basic version strings
func compareVersions(v1, v2 string) int {
	if v1 < v2 {
		return -1
	}
	if v1 > v2 {
		return 1
	}
	return 0
}

// InMemoryLoader is a simple in-memory plugin loader for testing
type InMemoryLoader struct {
	plugins map[string]Plugin
}

// NewInMemoryLoader creates a new in-memory loader
func NewInMemoryLoader() *InMemoryLoader {
	return &InMemoryLoader{
		plugins: make(map[string]Plugin),
	}
}

// Register registers a plugin instance
func (iml *InMemoryLoader) Register(name string, plugin Plugin) {
	iml.plugins[name] = plugin
}

// Load loads a registered plugin by name
func (iml *InMemoryLoader) Load(ctx context.Context, path string) (Plugin, error) {
	plugin, exists := iml.plugins[path]
	if !exists {
		return nil, fmt.Errorf("plugin not found: %s", path)
	}
	return plugin, nil
}

// Unload unloads a plugin
func (iml *InMemoryLoader) Unload(ctx context.Context, plugin Plugin) error {
	metadata := plugin.Metadata()
	delete(iml.plugins, metadata.Name)
	return nil
}

// Reload reloads a plugin
func (iml *InMemoryLoader) Reload(ctx context.Context, plugin Plugin) error {
	// In-memory plugins don't need reloading
	return nil
}

// Validate validates a plugin
func (iml *InMemoryLoader) Validate(ctx context.Context, path string) error {
	_, exists := iml.plugins[path]
	if !exists {
		return fmt.Errorf("plugin not found: %s", path)
	}
	return nil
}
