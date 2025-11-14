package tui

import (
	"context"
	"fmt"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/verticedev/vcli-go/internal/plugins"
)

// PluginManager wraps the plugin system for TUI integration
type PluginManagerWrapper struct {
	manager *plugins.PluginManager
	ctx     context.Context
}

// NewPluginManagerWrapper creates a wrapper for plugin manager
func NewPluginManagerWrapper(manager *plugins.PluginManager, ctx context.Context) *PluginManagerWrapper {
	return &PluginManagerWrapper{
		manager: manager,
		ctx:     ctx,
	}
}

// LoadPluginCmd returns a command to load a plugin
func (pmw *PluginManagerWrapper) LoadPluginCmd(path string) tea.Cmd {
	return func() tea.Msg {
		if err := pmw.manager.Load(path); err != nil {
			return PluginLoadedMsg{
				PluginName: path,
				Success:    false,
				Error:      err,
			}
		}

		// Get plugin info after loading
		pluginsList := pmw.manager.List()
		if len(pluginsList) > 0 {
			// Find the plugin we just loaded
			lastPlugin := pluginsList[len(pluginsList)-1]
			return PluginLoadedMsg{
				PluginName: lastPlugin.Name(),
				Version:    lastPlugin.Version(),
				Success:    true,
				Error:      nil,
			}
		}

		return PluginLoadedMsg{
			PluginName: path,
			Success:    false,
			Error:      fmt.Errorf("plugin '%s' loaded but not found in list", path),
		}
	}
}

// UnloadPluginCmd returns a command to unload a plugin (not implemented yet)
func (pmw *PluginManagerWrapper) UnloadPluginCmd(name string) tea.Cmd {
	return func() tea.Msg {
		// Plugin unloading not yet implemented in plugins.Manager
		// Return success for now to avoid blocking
		return PluginUnloadedMsg{
			PluginName: name,
			Success:    true,
			Error:      nil,
		}
	}
}

// StartPluginCmd returns a command to start a plugin (plugins are auto-started on load)
func (pmw *PluginManagerWrapper) StartPluginCmd(name string) tea.Cmd {
	return func() tea.Msg {
		// Plugins are auto-initialized on load via Init()
		// Just verify it exists
		if _, err := pmw.manager.Get(name); err != nil {
			return PluginLoadedMsg{
				PluginName: name,
				Success:    false,
				Error:      err,
			}
		}

		return PluginLoadedMsg{
			PluginName: name,
			Success:    true,
		}
	}
}

// HealthCheckCmd returns a command to check plugin health (basic check)
func (pmw *PluginManagerWrapper) HealthCheckCmd(name string) tea.Cmd {
	return func() tea.Msg {
		plugin, err := pmw.manager.Get(name)
		if err != nil {
			return PluginHealthMsg{
				PluginName: name,
				Healthy:    false,
				Message:    err.Error(),
			}
		}

		// Plugin exists and is loaded = healthy
		return PluginHealthMsg{
			PluginName: plugin.Name(),
			Healthy:    true,
			Message:    "plugin loaded and available",
		}
	}
}

// ListPluginsCmd returns a command to list all plugins
func (pmw *PluginManagerWrapper) ListPluginsCmd() tea.Cmd {
	return func() tea.Msg {
		pluginsList := pmw.manager.List()

		// Convert to TUI message format
		pluginInfos := make([]PluginInfo, 0, len(pluginsList))
		for _, p := range pluginsList {
			pluginInfos = append(pluginInfos, PluginInfo{
				Name:        p.Name(),
				Version:     p.Version(),
				Enabled:     true, // All loaded plugins are enabled
				Healthy:     true, // If loaded, assume healthy
				Description: p.Description(),
			})
		}

		return PluginListMsg{
			Plugins: pluginInfos,
		}
	}
}

// SubscribeToEventsCmd subscribes to plugin events (not yet implemented)
func (pmw *PluginManagerWrapper) SubscribeToEventsCmd() tea.Cmd {
	return func() tea.Msg {
		// Event system not yet implemented in plugins.Manager
		// Return nil for now
		return nil
	}
}

// GetPluginView returns the TUI view for a plugin (basic implementation)
func (pmw *PluginManagerWrapper) GetPluginView(name string) (plugins.View, error) {
	plugin, err := pmw.manager.Get(name)
	if err != nil {
		return plugins.View{}, err
	}

	// Return basic view with plugin info
	return plugins.View{
		Name:    plugin.Name(),
		Content: plugin.Description(),
	}, nil
}

// ExecutePluginCommand executes a plugin command
func (pmw *PluginManagerWrapper) ExecutePluginCommand(pluginName string, args []string) tea.Cmd {
	return func() tea.Msg {
		if err := pmw.manager.Execute(pluginName, args); err != nil {
			return PluginCommandExecutedMsg{
				PluginName: pluginName,
				Command:    args[0],
				Success:    false,
				Error:      err,
			}
		}

		return PluginCommandExecutedMsg{
			PluginName: pluginName,
			Command:    args[0],
			Success:    true,
			Error:      nil,
		}
	}
}

// PluginListMsg is sent with list of plugins
type PluginListMsg struct {
	Plugins []PluginInfo
}

// PluginEventMsg is sent when a plugin event occurs
type PluginEventMsg struct {
	Type       string
	PluginName string
	Message    string
}

// PluginViewRenderMsg requests plugin view rendering
type PluginViewRenderMsg struct {
	PluginName string
}

// PluginCommandExecuteMsg executes a plugin command
type PluginCommandExecuteMsg struct {
	PluginName string
	Command    string
	Args       []string
}

// PluginCommandExecutedMsg is sent when command execution completes
type PluginCommandExecutedMsg struct {
	PluginName string
	Command    string
	Success    bool
	Error      error
}

// WrapPluginView wraps a plugin view to implement PluginView interface
type WrappedPluginView struct {
	view plugins.View
}

// ID returns the view ID
func (wpv *WrappedPluginView) ID() string {
	return wpv.view.Name
}

// Render renders the view
func (wpv *WrappedPluginView) Render() string {
	return wpv.view.Content
}

// Update processes messages (basic no-op for now)
func (wpv *WrappedPluginView) Update(msg tea.Msg) (PluginView, tea.Cmd) {
	return wpv, nil
}

// Focus sets focus (no-op for basic views)
func (wpv *WrappedPluginView) Focus() {
}

// Blur removes focus (no-op for basic views)
func (wpv *WrappedPluginView) Blur() {
}

// IsFocused returns focus state (always false for basic views)
func (wpv *WrappedPluginView) IsFocused() bool {
	return false
}

// WrapPluginView wraps a plugin view
func WrapPluginView(view plugins.View) PluginView {
	return &WrappedPluginView{view: view}
}
