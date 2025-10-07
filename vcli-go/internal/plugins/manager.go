package plugins

import (
	"fmt"
	"os"
	"path/filepath"
	"plugin"
	"strings"
)

// Plugin represents a vCLI plugin
type Plugin interface {
	Name() string
	Version() string
	Description() string
	Init() error
	Execute(args []string) error
}

// Manager manages plugin loading and execution
type Manager struct {
	pluginsPath string
	plugins     map[string]Plugin
	disabled    map[string]bool
}

// NewManager creates a new plugin manager
func NewManager(pluginsPath string, disabled []string) *Manager {
	disabledMap := make(map[string]bool)
	for _, name := range disabled {
		disabledMap[name] = true
	}

	return &Manager{
		pluginsPath: pluginsPath,
		plugins:     make(map[string]Plugin),
		disabled:    disabledMap,
	}
}

// LoadAll loads all plugins from the plugins directory
func (m *Manager) LoadAll() error {
	if err := os.MkdirAll(m.pluginsPath, 0755); err != nil {
		return fmt.Errorf("failed to create plugins directory: %w", err)
	}

	matches, err := filepath.Glob(filepath.Join(m.pluginsPath, "*.so"))
	if err != nil {
		return fmt.Errorf("failed to scan plugins directory: %w", err)
	}

	for _, path := range matches {
		if err := m.Load(path); err != nil {
			fmt.Fprintf(os.Stderr, "Warning: failed to load plugin %s: %v\n", path, err)
		}
	}

	return nil
}

// Load loads a specific plugin
func (m *Manager) Load(path string) error {
	pluginName := strings.TrimSuffix(filepath.Base(path), ".so")

	if m.disabled[pluginName] {
		return fmt.Errorf("plugin disabled: %s", pluginName)
	}

	p, err := plugin.Open(path)
	if err != nil {
		return fmt.Errorf("failed to open plugin: %w", err)
	}

	symPlugin, err := p.Lookup("NewPlugin")
	if err != nil {
		return fmt.Errorf("plugin missing NewPlugin function: %w", err)
	}

	newPluginFunc, ok := symPlugin.(func() Plugin)
	if !ok {
		return fmt.Errorf("invalid NewPlugin function signature")
	}

	pluginInstance := newPluginFunc()

	if err := pluginInstance.Init(); err != nil {
		return fmt.Errorf("failed to initialize plugin: %w", err)
	}

	m.plugins[pluginInstance.Name()] = pluginInstance
	return nil
}

// Get returns a plugin by name
func (m *Manager) Get(name string) (Plugin, error) {
	p, ok := m.plugins[name]
	if !ok {
		return nil, fmt.Errorf("plugin not found: %s", name)
	}
	return p, nil
}

// List returns all loaded plugins
func (m *Manager) List() []Plugin {
	plugins := make([]Plugin, 0, len(m.plugins))
	for _, p := range m.plugins {
		plugins = append(plugins, p)
	}
	return plugins
}

// Execute executes a plugin command
func (m *Manager) Execute(name string, args []string) error {
	p, err := m.Get(name)
	if err != nil {
		return err
	}
	return p.Execute(args)
}
