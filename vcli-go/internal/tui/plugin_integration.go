package tui

import (
	"context"
	"time"

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
func (pmw *PluginManagerWrapper) LoadPluginCmd(nameOrPath string) tea.Cmd {
	return func() tea.Msg {
		if err := pmw.manager.LoadPlugin(pmw.ctx, nameOrPath); err != nil {
			return PluginLoadedMsg{
				PluginName: nameOrPath,
				Success:    false,
				Error:      err,
			}
		}

		// Get plugin info
		info, err := pmw.manager.GetPlugin(nameOrPath)
		if err != nil {
			return PluginLoadedMsg{
				PluginName: nameOrPath,
				Success:    false,
				Error:      err,
			}
		}

		return PluginLoadedMsg{
			PluginName: info.Metadata.Name,
			Version:    info.Metadata.Version,
			Success:    true,
			Error:      nil,
		}
	}
}

// UnloadPluginCmd returns a command to unload a plugin
func (pmw *PluginManagerWrapper) UnloadPluginCmd(name string) tea.Cmd {
	return func() tea.Msg {
		if err := pmw.manager.UnloadPlugin(pmw.ctx, name); err != nil {
			return PluginUnloadedMsg{
				PluginName: name,
				Success:    false,
				Error:      err,
			}
		}

		return PluginUnloadedMsg{
			PluginName: name,
			Success:    true,
			Error:      nil,
		}
	}
}

// StartPluginCmd returns a command to start a plugin
func (pmw *PluginManagerWrapper) StartPluginCmd(name string) tea.Cmd {
	return func() tea.Msg {
		if err := pmw.manager.StartPlugin(pmw.ctx, name); err != nil {
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

// HealthCheckCmd returns a command to check plugin health
func (pmw *PluginManagerWrapper) HealthCheckCmd(name string) tea.Cmd {
	return func() tea.Msg {
		health, err := pmw.manager.HealthCheck(pmw.ctx, name)
		if err != nil {
			return PluginHealthMsg{
				PluginName: name,
				Healthy:    false,
				Message:    err.Error(),
			}
		}

		return PluginHealthMsg{
			PluginName: name,
			Healthy:    health.Healthy,
			Message:    health.Message,
		}
	}
}

// ListPluginsCmd returns a command to list all plugins
func (pmw *PluginManagerWrapper) ListPluginsCmd() tea.Cmd {
	return func() tea.Msg {
		pluginInfos := pmw.manager.ListPlugins()

		// Convert to TUI message format
		pluginsList := make([]PluginInfo, 0, len(pluginInfos))
		for _, info := range pluginInfos {
			pluginsList = append(pluginsList, PluginInfo{
				Name:        info.Metadata.Name,
				Version:     info.Metadata.Version,
				Enabled:     info.Status == plugins.LoadStatusRunning,
				Healthy:     info.Health.Healthy,
				LoadedAt:    info.LoadedAt,
				LastHealth:  info.Health.LastCheck,
				ErrorCount:  info.ErrorCount,
				Description: info.Metadata.Description,
			})
		}

		return PluginListMsg{
			Plugins: pluginsList,
		}
	}
}

// SubscribeToEventsCmd subscribes to plugin events
func (pmw *PluginManagerWrapper) SubscribeToEventsCmd() tea.Cmd {
	return func() tea.Msg {
		select {
		case event := <-pmw.manager.Events():
			return PluginEventMsg{
				Type:       string(event.Type),
				PluginName: event.PluginName,
				Message:    event.Message,
				Timestamp:  event.Timestamp,
			}
		case <-time.After(100 * time.Millisecond):
			// No event, try again
			return nil
		}
	}
}

// GetPluginView returns the TUI view for a plugin
func (pmw *PluginManagerWrapper) GetPluginView(name string) (plugins.View, error) {
	info, err := pmw.manager.GetPlugin(name)
	if err != nil {
		return nil, err
	}

	return info.Instance.View(), nil
}

// GetPluginCommands returns CLI commands from a plugin
func (pmw *PluginManagerWrapper) GetPluginCommands(name string) ([]plugins.Command, error) {
	info, err := pmw.manager.GetPlugin(name)
	if err != nil {
		return nil, err
	}

	return info.Instance.Commands(), nil
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
	Timestamp  time.Time
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

// ExecutePluginCommand executes a plugin command
func (pmw *PluginManagerWrapper) ExecutePluginCommand(pluginName, command string, args []string) tea.Cmd {
	return func() tea.Msg {
		// Get plugin commands
		commands, err := pmw.GetPluginCommands(pluginName)
		if err != nil {
			return NewErrorMsg(err, "get plugin commands")
		}

		// Find command
		for _, cmd := range commands {
			if cmd.Name == command {
				if err := cmd.Handler(args); err != nil {
					return NewErrorMsg(err, "execute plugin command")
				}
				return PluginCommandExecutedMsg{
					PluginName: pluginName,
					Command:    command,
					Success:    true,
				}
			}

			// Check subcommands
			for _, subcmd := range cmd.Subcommands {
				if subcmd.Name == command {
					if err := subcmd.Handler(args); err != nil {
						return NewErrorMsg(err, "execute plugin command")
					}
					return PluginCommandExecutedMsg{
						PluginName: pluginName,
						Command:    command,
						Success:    true,
					}
				}
			}
		}

		return NewErrorMsg(
			plugins.NewPluginError(pluginName, "command not found", nil),
			"execute plugin command",
		)
	}
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
	return wpv.view.ID()
}

// Render renders the view
func (wpv *WrappedPluginView) Render() string {
	return wpv.view.Render()
}

// Update processes messages
func (wpv *WrappedPluginView) Update(msg tea.Msg) (PluginView, tea.Cmd) {
	updatedView, cmd := wpv.view.Update(msg)
	return &WrappedPluginView{view: updatedView}, cmd
}

// Focus sets focus
func (wpv *WrappedPluginView) Focus() {
	wpv.view.Focus()
}

// Blur removes focus
func (wpv *WrappedPluginView) Blur() {
	wpv.view.Blur()
}

// IsFocused returns focus state
func (wpv *WrappedPluginView) IsFocused() bool {
	return wpv.view.IsFocused()
}

// WrapPluginView wraps a plugin view
func WrapPluginView(view plugins.View) PluginView {
	return &WrappedPluginView{view: view}
}
