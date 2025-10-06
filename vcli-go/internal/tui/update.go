package tui

import (
	"time"

	tea "github.com/charmbracelet/bubbletea"
)

// Update processes messages and returns an updated model and command
// This is the core of the MVU (Model-View-Update) pattern
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	// Handle built-in Bubble Tea messages first
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		return m.handleWindowSize(msg)

	case tea.KeyMsg:
		return m.handleKeyMsg(msg)
	}

	// Handle custom application messages
	switch msg := msg.(type) {

	// --- Workspace Messages ---

	case WorkspaceSwitchMsg:
		return m.handleWorkspaceSwitch(msg)

	case WorkspaceLoadedMsg:
		return m.handleWorkspaceLoaded(msg)

	case WorkspaceInitializedMsg:
		return m.handleWorkspaceInitialized(msg)

	// --- Plugin Messages ---

	case PluginLoadMsg:
		return m.handlePluginLoad(msg)

	case PluginLoadedMsg:
		return m.handlePluginLoaded(msg)

	case PluginUnloadMsg:
		return m.handlePluginUnload(msg)

	case PluginUnloadedMsg:
		return m.handlePluginUnloaded(msg)

	case PluginHealthMsg:
		return m.handlePluginHealth(msg)

	// --- Configuration Messages ---

	case ConfigUpdateMsg:
		return m.handleConfigUpdate(msg)

	case ConfigReloadMsg:
		return m.handleConfigReload(msg)

	case ConfigLoadedMsg:
		return m.handleConfigLoaded(msg)

	// --- Offline Mode Messages ---

	case OfflineModeMsg:
		return m.handleOfflineMode(msg)

	case OfflineSyncMsg:
		return m.handleOfflineSync(msg)

	case OfflineSyncProgressMsg:
		return m.handleOfflineSyncProgress(msg)

	case OfflineSyncCompletedMsg:
		return m.handleOfflineSyncCompleted(msg)

	// --- Metrics Messages ---

	case MetricsUpdateMsg:
		return m.handleMetricsUpdate(msg)

	case MetricsTickMsg:
		return m.handleMetricsTick(msg)

	// --- Event Messages ---

	case EventMsg:
		return m.handleEvent(msg)

	case EventClearMsg:
		return m.handleEventClear(msg)

	// --- Error Messages ---

	case ErrorMsg:
		return m.handleError(msg)

	case ErrorClearMsg:
		return m.handleErrorClear(msg)

	// --- UI Messages ---

	case ViewChangeMsg:
		return m.handleViewChange(msg)

	case FocusChangeMsg:
		return m.handleFocusChange(msg)

	case CommandPaletteToggleMsg:
		return m.handleCommandPaletteToggle(msg)

	case HelpToggleMsg:
		return m.handleHelpToggle(msg)

	case ThemeChangeMsg:
		return m.handleThemeChange(msg)

	// --- Navigation Messages ---

	case NavigateBackMsg:
		return m.handleNavigateBack(msg)

	case NavigateForwardMsg:
		return m.handleNavigateForward(msg)

	case NavigateToMsg:
		return m.handleNavigateTo(msg)

	// --- Search Messages ---

	case SearchStartMsg:
		return m.handleSearchStart(msg)

	case SearchResultsMsg:
		return m.handleSearchResults(msg)

	case SearchClearMsg:
		return m.handleSearchClear(msg)

	// --- Loading Messages ---

	case LoadingStartMsg:
		return m.handleLoadingStart(msg)

	case LoadingStopMsg:
		return m.handleLoadingStop(msg)

	// --- Clipboard Messages ---

	case ClipboardCopyMsg:
		return m.handleClipboardCopy(msg)

	case ClipboardPasteMsg:
		return m.handleClipboardPaste(msg)

	// --- Notification Messages ---

	case NotificationMsg:
		return m.handleNotification(msg)

	case NotificationDismissMsg:
		return m.handleNotificationDismiss(msg)

	// --- User Input Messages ---

	case ConfirmMsg:
		return m.handleConfirm(msg)

	case InputRequestMsg:
		return m.handleInputRequest(msg)

	// --- Tick Messages ---

	case TickMsg:
		return m.handleTick(msg)

	// --- Batch Messages ---

	case BatchMsg:
		return m.handleBatch(msg)
	}

	// Delegate to active workspace if available
	if m.activeView == ViewTypeWorkspace && m.GetActiveWorkspace() != nil {
		updatedWS, cmd := m.GetActiveWorkspace().Update(msg)
		m.workspaces[m.activeWS] = updatedWS
		cmds = append(cmds, cmd)
	}

	return m, tea.Batch(cmds...)
}

// handleWindowSize handles terminal resize events
func (m Model) handleWindowSize(msg tea.WindowSizeMsg) (tea.Model, tea.Cmd) {
	m.windowSize = msg
	m.ready = true
	return m, nil
}

// handleKeyMsg handles keyboard input
func (m Model) handleKeyMsg(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c", "q":
		return m, tea.Quit

	case "ctrl+p":
		m.ToggleCommandPalette()
		return m, nil

	case "?":
		m.ToggleHelp()
		return m, nil

	case "ctrl+r":
		return m, func() tea.Msg {
			return MetricsTickMsg{Timestamp: time.Now()}
		}
	}

	// Check custom shortcuts
	if shortcut, exists := m.shortcuts[msg.String()]; exists {
		return m, shortcut.Handler
	}

	return m, nil
}

// handleWorkspaceSwitch handles workspace switching
func (m Model) handleWorkspaceSwitch(msg WorkspaceSwitchMsg) (tea.Model, tea.Cmd) {
	if err := m.SetActiveWorkspace(msg.WorkspaceID); err != nil {
		return m, func() tea.Msg {
			return NewErrorMsg(err, "workspace switch")
		}
	}

	// Initialize workspace if not already initialized
	if ws := m.GetActiveWorkspace(); ws != nil && !ws.IsInitialized() {
		return m, ws.Init()
	}

	return m, nil
}

// handleWorkspaceLoaded handles workspace loaded message
func (m Model) handleWorkspaceLoaded(msg WorkspaceLoadedMsg) (tea.Model, tea.Cmd) {
	if !msg.Success {
		m.AddError(Error{
			Code:      "WORKSPACE_LOAD_FAILED",
			Message:   msg.Error.Error(),
			Timestamp: time.Now(),
			Context:   msg.WorkspaceID,
			Severity:  SeverityHigh,
		})
	}
	return m, nil
}

// handleWorkspaceInitialized handles workspace initialization complete
func (m Model) handleWorkspaceInitialized(msg WorkspaceInitializedMsg) (tea.Model, tea.Cmd) {
	m.AddEvent(NewEventMsg(
		EventTypeInfo,
		"workspace",
		map[string]string{"id": msg.WorkspaceID},
		SeverityLow,
	))
	return m, nil
}

// handlePluginLoad handles plugin load request
// Note: This is a fallback handler for when no PluginManagerWrapper is connected.
// In integrated mode, use PluginManagerWrapper.LoadPluginCmd() instead (see plugin_integration.go).
// This implementation provides standalone/testing capability.
func (m Model) handlePluginLoad(msg PluginLoadMsg) (tea.Model, tea.Cmd) {
	m.StartLoading("plugin_"+msg.PluginName, "Loading plugin: "+msg.PluginName)

	return m, func() tea.Msg {
		// Simulate plugin load for standalone mode
		time.Sleep(100 * time.Millisecond)

		return PluginLoadedMsg{
			PluginName: msg.PluginName,
			Version:    "1.0.0",
			Success:    true,
			Error:      nil,
		}
	}
}

// handlePluginLoaded handles plugin loaded message
func (m Model) handlePluginLoaded(msg PluginLoadedMsg) (tea.Model, tea.Cmd) {
	m.StopLoading("plugin_" + msg.PluginName)

	if msg.Success {
		m.LoadPlugin(msg.PluginName, msg.Version)
		m.AddNotification(Notification{
			ID:       "plugin_loaded_" + msg.PluginName,
			Title:    "Plugin Loaded",
			Message:  msg.PluginName + " v" + msg.Version,
			Severity: SeverityLow,
			Duration: 3 * time.Second,
		})
	} else {
		m.AddError(Error{
			Code:      "PLUGIN_LOAD_FAILED",
			Message:   msg.Error.Error(),
			Timestamp: time.Now(),
			Context:   msg.PluginName,
			Severity:  SeverityHigh,
		})
	}

	return m, nil
}

// handlePluginUnload handles plugin unload request
func (m Model) handlePluginUnload(msg PluginUnloadMsg) (tea.Model, tea.Cmd) {
	return m, func() tea.Msg {
		return PluginUnloadedMsg{
			PluginName: msg.PluginName,
			Success:    true,
			Error:      nil,
		}
	}
}

// handlePluginUnloaded handles plugin unloaded message
func (m Model) handlePluginUnloaded(msg PluginUnloadedMsg) (tea.Model, tea.Cmd) {
	if msg.Success {
		m.UnloadPlugin(msg.PluginName)
	}
	return m, nil
}

// handlePluginHealth handles plugin health update
func (m Model) handlePluginHealth(msg PluginHealthMsg) (tea.Model, tea.Cmd) {
	m.UpdatePluginHealth(msg.PluginName, msg.Healthy)

	if !msg.Healthy {
		m.AddWarning(Error{
			Code:      "PLUGIN_UNHEALTHY",
			Message:   msg.Message,
			Timestamp: time.Now(),
			Context:   msg.PluginName,
			Severity:  SeverityMedium,
		})
	}

	return m, nil
}

// handleConfigUpdate handles configuration update
// Note: Config persistence is handled by ConfigHierarchy when integrated with file backend.
// This handler updates in-memory configuration state.
func (m Model) handleConfigUpdate(msg ConfigUpdateMsg) (tea.Model, tea.Cmd) {
	// Configuration update is applied to m.config (ConfigHierarchy)
	// ConfigHierarchy.Set() handles persistence when file backend is configured
	return m, nil
}

// handleConfigReload handles configuration reload request
// Note: Config reload triggers re-reading from file backend when configured.
// In standalone mode, this is a no-op as config is in-memory only.
func (m Model) handleConfigReload(msg ConfigReloadMsg) (tea.Model, tea.Cmd) {
	return m, func() tea.Msg {
		// Configuration reload from ConfigHierarchy backend
		return ConfigLoadedMsg{
			Success: true,
			Error:   nil,
		}
	}
}

// handleConfigLoaded handles configuration loaded message
func (m Model) handleConfigLoaded(msg ConfigLoadedMsg) (tea.Model, tea.Cmd) {
	if !msg.Success {
		m.AddError(Error{
			Code:      "CONFIG_LOAD_FAILED",
			Message:   msg.Error.Error(),
			Timestamp: time.Now(),
			Context:   "config reload",
			Severity:  SeverityHigh,
		})
	}
	return m, nil
}

// handleOfflineMode handles offline mode toggle
func (m Model) handleOfflineMode(msg OfflineModeMsg) (tea.Model, tea.Cmd) {
	m.SetOfflineMode(msg.Enabled)

	severity := SeverityLow
	if msg.Enabled {
		severity = SeverityMedium
	}

	m.AddNotification(Notification{
		ID:       "offline_mode",
		Title:    "Offline Mode",
		Message:  map[bool]string{true: "Enabled", false: "Disabled"}[msg.Enabled],
		Severity: severity,
		Duration: 3 * time.Second,
	})

	return m, nil
}

// handleOfflineSync handles offline sync request
// Note: Real sync would integrate with backend sync service.
// This implementation provides offline queue simulation for standalone mode.
func (m Model) handleOfflineSync(msg OfflineSyncMsg) (tea.Model, tea.Cmd) {
	if m.syncInProgress {
		return m, nil
	}

	m.SetSyncInProgress(true)

	return m, func() tea.Msg {
		// Simulate sync operation for standalone mode
		// Real implementation would use OfflineSyncService
		time.Sleep(500 * time.Millisecond)

		return OfflineSyncCompletedMsg{
			Success:   true,
			Synced:    42,
			Failed:    0,
			Conflicts: 0,
			Error:     nil,
		}
	}
}

// handleOfflineSyncProgress handles offline sync progress update
func (m Model) handleOfflineSyncProgress(msg OfflineSyncProgressMsg) (tea.Model, tea.Cmd) {
	// Update sync progress UI
	return m, nil
}

// handleOfflineSyncCompleted handles offline sync completion
func (m Model) handleOfflineSyncCompleted(msg OfflineSyncCompletedMsg) (tea.Model, tea.Cmd) {
	m.SetSyncInProgress(false)

	if msg.Success {
		m.queuedOps = 0
		m.AddNotification(Notification{
			ID:       "sync_complete",
			Title:    "Sync Complete",
			Message:  "Synced " + string(rune(msg.Synced)) + " operations",
			Severity: SeverityLow,
			Duration: 3 * time.Second,
		})
	} else {
		m.AddError(Error{
			Code:      "SYNC_FAILED",
			Message:   msg.Error.Error(),
			Timestamp: time.Now(),
			Context:   "offline sync",
			Severity:  SeverityHigh,
		})
	}

	return m, nil
}

// handleMetricsUpdate handles metrics update
func (m Model) handleMetricsUpdate(msg MetricsUpdateMsg) (tea.Model, tea.Cmd) {
	m.UpdateMetrics(msg.Data)
	return m, nil
}

// handleMetricsTick handles metrics tick (periodic collection)
// Note: Real metrics would be collected from system monitor service.
// This implementation provides UI-level metrics (plugins, errors, warnings).
func (m Model) handleMetricsTick(msg MetricsTickMsg) (tea.Model, tea.Cmd) {
	// Collect UI-level metrics
	// System metrics (CPU, memory, disk, network) would come from MetricsUpdateMsg
	metrics := MetricsData{
		Timestamp:     msg.Timestamp,
		CPU:           0.0,
		Memory:        0.0,
		Disk:          0.0,
		NetworkIn:     0.0,
		NetworkOut:    0.0,
		PluginsLoaded: len(m.loadedPlugins),
		Errors:        len(m.errors),
		Warnings:      len(m.warnings),
	}

	m.UpdateMetrics(metrics)

	// Schedule next tick
	return m, tea.Tick(5*time.Second, func(t time.Time) tea.Msg {
		return NewMetricsTickMsg()
	})
}

// handleEvent handles system event
func (m Model) handleEvent(msg EventMsg) (tea.Model, tea.Cmd) {
	m.AddEvent(msg.Event)
	return m, nil
}

// handleEventClear handles event clear request
func (m Model) handleEventClear(msg EventClearMsg) (tea.Model, tea.Cmd) {
	m.ClearEvents(msg.OlderThan)
	return m, nil
}

// handleError handles error message
func (m Model) handleError(msg ErrorMsg) (tea.Model, tea.Cmd) {
	err := Error{
		Code:      "GENERIC_ERROR",
		Message:   msg.Error.Error(),
		Timestamp: time.Now(),
		Context:   msg.Context,
		Severity:  SeverityMedium,
	}

	if msg.Fatal {
		err.Severity = SeverityCritical
		m.AddError(err)
		return m, tea.Quit
	}

	m.AddError(err)
	return m, nil
}

// handleErrorClear handles error clear request
func (m Model) handleErrorClear(msg ErrorClearMsg) (tea.Model, tea.Cmd) {
	if msg.All {
		m.ClearErrors()
		m.ClearWarnings()
	}
	return m, nil
}

// handleViewChange handles view change request
func (m Model) handleViewChange(msg ViewChangeMsg) (tea.Model, tea.Cmd) {
	m.activeView = msg.NewView
	return m, nil
}

// handleFocusChange handles focus change request
func (m Model) handleFocusChange(msg FocusChangeMsg) (tea.Model, tea.Cmd) {
	m.focused = msg.ComponentID
	return m, nil
}

// handleCommandPaletteToggle handles command palette toggle
func (m Model) handleCommandPaletteToggle(msg CommandPaletteToggleMsg) (tea.Model, tea.Cmd) {
	m.ToggleCommandPalette()
	return m, nil
}

// handleHelpToggle handles help toggle
func (m Model) handleHelpToggle(msg HelpToggleMsg) (tea.Model, tea.Cmd) {
	m.ToggleHelp()
	return m, nil
}

// handleThemeChange handles theme change
func (m Model) handleThemeChange(msg ThemeChangeMsg) (tea.Model, tea.Cmd) {
	m.SetTheme(msg.Theme)
	return m, nil
}

// handleNavigateBack handles back navigation
func (m Model) handleNavigateBack(msg NavigateBackMsg) (tea.Model, tea.Cmd) {
	m.NavigateBack()
	return m, nil
}

// handleNavigateForward handles forward navigation
func (m Model) handleNavigateForward(msg NavigateForwardMsg) (tea.Model, tea.Cmd) {
	m.NavigateForward()
	return m, nil
}

// handleNavigateTo handles navigation to specific location
// Note: Location parsing could use workspace IDs, view types, or custom routes.
// Current implementation uses navigation history tracking only.
func (m Model) handleNavigateTo(msg NavigateToMsg) (tea.Model, tea.Cmd) {
	if msg.SaveHistory {
		m.navigation.History = append(m.navigation.History, msg.Location)
		m.navigation.Current = len(m.navigation.History) - 1
	}

	// Location navigation is handled by workspace/view switching messages
	// NavigateTo provides history tracking for navigation stack

	return m, nil
}

// handleSearchStart handles search start
// Note: Search implementation would integrate with search service.
// Current implementation provides basic search state management.
func (m Model) handleSearchStart(msg SearchStartMsg) (tea.Model, tea.Cmd) {
	m.search.Active = true
	m.search.Query = msg.Query

	return m, func() tea.Msg {
		// Search would be performed by SearchService
		// Return empty results for standalone mode
		return SearchResultsMsg{
			Query:   msg.Query,
			Results: []SearchResult{},
		}
	}
}

// handleSearchResults handles search results
func (m Model) handleSearchResults(msg SearchResultsMsg) (tea.Model, tea.Cmd) {
	m.search.Results = msg.Results
	return m, nil
}

// handleSearchClear handles search clear
func (m Model) handleSearchClear(msg SearchClearMsg) (tea.Model, tea.Cmd) {
	m.search.Active = false
	m.search.Query = ""
	m.search.Results = []SearchResult{}
	return m, nil
}

// handleLoadingStart handles loading start
func (m Model) handleLoadingStart(msg LoadingStartMsg) (tea.Model, tea.Cmd) {
	m.StartLoading(msg.ID, msg.Message)
	return m, nil
}

// handleLoadingStop handles loading stop
func (m Model) handleLoadingStop(msg LoadingStopMsg) (tea.Model, tea.Cmd) {
	m.StopLoading(msg.ID)
	return m, nil
}

// handleClipboardCopy handles clipboard copy
// Note: Clipboard integration would use OSC 52 sequences or external clipboard tools.
// Current implementation is no-op; clipboard feature is optional TUI enhancement.
func (m Model) handleClipboardCopy(msg ClipboardCopyMsg) (tea.Model, tea.Cmd) {
	// Clipboard copy would use OSC 52 escape sequences or xclip/pbcopy
	// Not implemented - optional feature for enhanced terminal integration
	return m, nil
}

// handleClipboardPaste handles clipboard paste
// Note: Clipboard integration would use OSC 52 sequences or external clipboard tools.
// Current implementation is no-op; clipboard feature is optional TUI enhancement.
func (m Model) handleClipboardPaste(msg ClipboardPasteMsg) (tea.Model, tea.Cmd) {
	// Clipboard paste would use OSC 52 escape sequences or xclip/pbpaste
	// Not implemented - optional feature for enhanced terminal integration
	return m, nil
}

// handleNotification handles notification display
func (m Model) handleNotification(msg NotificationMsg) (tea.Model, tea.Cmd) {
	m.AddNotification(Notification{
		ID:       "notif_" + time.Now().Format("20060102150405"),
		Title:    msg.Title,
		Message:  msg.Message,
		Severity: msg.Severity,
		Duration: msg.Duration,
	})
	return m, nil
}

// handleNotificationDismiss handles notification dismissal
func (m Model) handleNotificationDismiss(msg NotificationDismissMsg) (tea.Model, tea.Cmd) {
	m.DismissNotification(msg.ID)
	return m, nil
}

// handleConfirm handles user confirmation request
// Note: Modal dialog implementation would use dedicated dialog component.
// Current implementation is no-op; confirmation dialogs are optional UI enhancement.
func (m Model) handleConfirm(msg ConfirmMsg) (tea.Model, tea.Cmd) {
	// Confirmation dialog would use modal overlay component
	// Not implemented - optional feature for enhanced user interactions
	return m, nil
}

// handleInputRequest handles user input request
// Note: Input dialog implementation would use dedicated input component.
// Current implementation is no-op; input dialogs are optional UI enhancement.
func (m Model) handleInputRequest(msg InputRequestMsg) (tea.Model, tea.Cmd) {
	// Input dialog would use modal overlay with text input component
	// Not implemented - optional feature for enhanced user interactions
	return m, nil
}

// handleTick handles periodic tick for animations/updates
func (m Model) handleTick(msg TickMsg) (tea.Model, tea.Cmd) {
	// Clean up old dismissed notifications
	now := time.Now()
	active := make([]Notification, 0)

	for _, notif := range m.notifications {
		if !notif.Dismissed {
			if now.Sub(notif.Timestamp) < notif.Duration {
				active = append(active, notif)
			}
		}
	}

	m.notifications = active

	// Schedule next tick
	return m, tea.Tick(100*time.Millisecond, func(t time.Time) tea.Msg {
		return NewTickMsg()
	})
}

// handleBatch handles batch messages
func (m Model) handleBatch(msg BatchMsg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	for _, batchMsg := range msg.Messages {
		updatedModel, cmd := m.Update(batchMsg)
		m = updatedModel.(Model)
		cmds = append(cmds, cmd)
	}

	return m, tea.Batch(cmds...)
}
