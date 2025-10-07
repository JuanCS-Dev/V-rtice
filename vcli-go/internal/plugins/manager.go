package plugins

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// PluginManager manages plugin lifecycle
type PluginManager struct {
	mu sync.RWMutex

	// plugins holds loaded plugins by name
	plugins map[string]*PluginInfo

	// loader is the plugin loader
	loader Loader

	// sandbox is the security sandbox
	sandbox Sandbox

	// registry is the plugin registry
	registry Registry

	// events is the event channel
	events chan Event

	// healthCheckInterval is how often to check health
	healthCheckInterval time.Duration

	// resourceCheckInterval is how often to check resources
	resourceCheckInterval time.Duration

	// stopChan signals shutdown
	stopChan chan struct{}

	// wg tracks background goroutines
	wg sync.WaitGroup
}

// NewPluginManager creates a new plugin manager
func NewPluginManager(loader Loader, sandbox Sandbox, registry Registry) *PluginManager {
	return &PluginManager{
		plugins:               make(map[string]*PluginInfo),
		loader:                loader,
		sandbox:               sandbox,
		registry:              registry,
		events:                make(chan Event, 100),
		healthCheckInterval:   30 * time.Second,
		resourceCheckInterval: 5 * time.Second,
		stopChan:              make(chan struct{}),
	}
}

// Start starts the plugin manager background tasks
func (pm *PluginManager) Start(ctx context.Context) error {
	// Start health check loop
	pm.wg.Add(1)
	go pm.healthCheckLoop(ctx)

	// Start resource monitoring loop
	pm.wg.Add(1)
	go pm.resourceCheckLoop(ctx)

	return nil
}

// Stop stops the plugin manager
func (pm *PluginManager) Stop(ctx context.Context) error {
	close(pm.stopChan)
	pm.wg.Wait()

	// Stop all plugins
	pm.mu.RLock()
	pluginNames := make([]string, 0, len(pm.plugins))
	for name := range pm.plugins {
		pluginNames = append(pluginNames, name)
	}
	pm.mu.RUnlock()

	for _, name := range pluginNames {
		if err := pm.StopPlugin(ctx, name); err != nil {
			// Log error but continue stopping others
		}
	}

	close(pm.events)
	return nil
}

// LoadPlugin loads a plugin by name or path
func (pm *PluginManager) LoadPlugin(ctx context.Context, nameOrPath string) error {
	// Check if already loaded
	pm.mu.RLock()
	if _, exists := pm.plugins[nameOrPath]; exists {
		pm.mu.RUnlock()
		return fmt.Errorf("plugin already loaded: %s", nameOrPath)
	}
	pm.mu.RUnlock()

	// Resolve path (check if it's a registry name or file path)
	path := nameOrPath

	// If it looks like a registry name, try to download
	if !isFilePath(path) {
		entry, err := pm.registry.Get(ctx, nameOrPath)
		if err == nil {
			// Download from registry
			downloadPath, err := pm.registry.Download(ctx, entry.Name, entry.LatestVersion)
			if err != nil {
				return fmt.Errorf("failed to download plugin: %w", err)
			}
			path = downloadPath
		}
	}

	// Validate plugin
	if err := pm.loader.Validate(ctx, path); err != nil {
		return fmt.Errorf("plugin validation failed: %w", err)
	}

	// Load plugin
	plugin, err := pm.loader.Load(ctx, path)
	if err != nil {
		return fmt.Errorf("failed to load plugin: %w", err)
	}

	metadata := plugin.Metadata()

	// Create plugin info
	info := &PluginInfo{
		Metadata:  metadata,
		Status:    LoadStatusLoading,
		Instance:  plugin,
		LoadedAt:  time.Now(),
		Config:    make(map[string]interface{}),
		Resources: ResourceUsage{LastUpdated: time.Now()},
	}

	// Store plugin
	pm.mu.Lock()
	pm.plugins[metadata.Name] = info
	pm.mu.Unlock()

	// Initialize plugin
	if err := plugin.Initialize(ctx, info.Config); err != nil {
		pm.mu.Lock()
		delete(pm.plugins, metadata.Name)
		pm.mu.Unlock()
		return fmt.Errorf("plugin initialization failed: %w", err)
	}

	// Update status
	pm.mu.Lock()
	info.Status = LoadStatusLoaded
	pm.mu.Unlock()

	// Emit event
	pm.emitEvent(Event{
		Type:       EventTypeLoaded,
		PluginName: metadata.Name,
		Timestamp:  time.Now(),
		Message:    fmt.Sprintf("Plugin %s v%s loaded", metadata.Name, metadata.Version),
	})

	return nil
}

// UnloadPlugin unloads a plugin by name
func (pm *PluginManager) UnloadPlugin(ctx context.Context, name string) error {
	pm.mu.RLock()
	info, exists := pm.plugins[name]
	pm.mu.RUnlock()

	if !exists {
		return fmt.Errorf("plugin not found: %s", name)
	}

	// Stop plugin if running
	if info.Status == LoadStatusRunning {
		if err := pm.StopPlugin(ctx, name); err != nil {
			return fmt.Errorf("failed to stop plugin before unload: %w", err)
		}
	}

	// Unload plugin
	if err := pm.loader.Unload(ctx, info.Instance); err != nil {
		return fmt.Errorf("failed to unload plugin: %w", err)
	}

	// Remove from map
	pm.mu.Lock()
	delete(pm.plugins, name)
	pm.mu.Unlock()

	// Emit event
	pm.emitEvent(Event{
		Type:       EventTypeUnloaded,
		PluginName: name,
		Timestamp:  time.Now(),
		Message:    fmt.Sprintf("Plugin %s unloaded", name),
	})

	return nil
}

// ReloadPlugin reloads a plugin by name
func (pm *PluginManager) ReloadPlugin(ctx context.Context, name string) error {
	pm.mu.RLock()
	info, exists := pm.plugins[name]
	pm.mu.RUnlock()

	if !exists {
		return fmt.Errorf("plugin not found: %s", name)
	}

	// Store config
	config := info.Config

	// Unload
	if err := pm.UnloadPlugin(ctx, name); err != nil {
		return fmt.Errorf("failed to unload during reload: %w", err)
	}

	// Load again
	if err := pm.LoadPlugin(ctx, name); err != nil {
		return fmt.Errorf("failed to load during reload: %w", err)
	}

	// Restore config
	pm.mu.Lock()
	if reloadedInfo, exists := pm.plugins[name]; exists {
		reloadedInfo.Config = config
	}
	pm.mu.Unlock()

	return nil
}

// StartPlugin starts a plugin by name
func (pm *PluginManager) StartPlugin(ctx context.Context, name string) error {
	pm.mu.RLock()
	info, exists := pm.plugins[name]
	pm.mu.RUnlock()

	if !exists {
		return fmt.Errorf("plugin not found: %s", name)
	}

	if info.Status == LoadStatusRunning {
		return fmt.Errorf("plugin already running: %s", name)
	}

	// Start plugin
	if err := info.Instance.Start(ctx); err != nil {
		pm.mu.Lock()
		info.Status = LoadStatusFailed
		info.LastError = err.Error()
		info.ErrorCount++
		pm.mu.Unlock()
		return fmt.Errorf("failed to start plugin: %w", err)
	}

	// Update status
	pm.mu.Lock()
	info.Status = LoadStatusRunning
	info.StartedAt = time.Now()
	pm.mu.Unlock()

	// Emit event
	pm.emitEvent(Event{
		Type:       EventTypeStarted,
		PluginName: name,
		Timestamp:  time.Now(),
		Message:    fmt.Sprintf("Plugin %s started", name),
	})

	return nil
}

// StopPlugin stops a plugin by name
func (pm *PluginManager) StopPlugin(ctx context.Context, name string) error {
	pm.mu.RLock()
	info, exists := pm.plugins[name]
	pm.mu.RUnlock()

	if !exists {
		return fmt.Errorf("plugin not found: %s", name)
	}

	if info.Status != LoadStatusRunning {
		return fmt.Errorf("plugin not running: %s", name)
	}

	// Update status
	pm.mu.Lock()
	info.Status = LoadStatusStopping
	pm.mu.Unlock()

	// Stop plugin
	if err := info.Instance.Stop(ctx); err != nil {
		pm.mu.Lock()
		info.Status = LoadStatusFailed
		info.LastError = err.Error()
		info.ErrorCount++
		pm.mu.Unlock()
		return fmt.Errorf("failed to stop plugin: %w", err)
	}

	// Update status
	pm.mu.Lock()
	info.Status = LoadStatusStopped
	info.StoppedAt = time.Now()
	pm.mu.Unlock()

	// Emit event
	pm.emitEvent(Event{
		Type:       EventTypeStopped,
		PluginName: name,
		Timestamp:  time.Now(),
		Message:    fmt.Sprintf("Plugin %s stopped", name),
	})

	return nil
}

// GetPlugin gets plugin info by name
func (pm *PluginManager) GetPlugin(name string) (*PluginInfo, error) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	info, exists := pm.plugins[name]
	if !exists {
		return nil, fmt.Errorf("plugin not found: %s", name)
	}

	// Return copy
	infoCopy := *info
	return &infoCopy, nil
}

// ListPlugins lists all loaded plugins
func (pm *PluginManager) ListPlugins() []PluginInfo {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	plugins := make([]PluginInfo, 0, len(pm.plugins))
	for _, info := range pm.plugins {
		plugins = append(plugins, *info)
	}

	return plugins
}

// HealthCheck performs health check on plugin
func (pm *PluginManager) HealthCheck(ctx context.Context, name string) (HealthStatus, error) {
	pm.mu.RLock()
	info, exists := pm.plugins[name]
	pm.mu.RUnlock()

	if !exists {
		return HealthStatus{}, fmt.Errorf("plugin not found: %s", name)
	}

	// Get health status from plugin
	health := info.Instance.Health()
	health.LastCheck = time.Now()

	// Update stored health
	pm.mu.Lock()
	info.Health = health
	pm.mu.Unlock()

	// Emit event if health changed
	if !health.Healthy {
		pm.emitEvent(Event{
			Type:       EventTypeUnhealthy,
			PluginName: name,
			Timestamp:  time.Now(),
			Message:    health.Message,
		})
	}

	return health, nil
}

// UpdateResources updates resource usage for plugin
func (pm *PluginManager) UpdateResources(name string) error {
	pm.mu.RLock()
	info, exists := pm.plugins[name]
	pm.mu.RUnlock()

	if !exists {
		return fmt.Errorf("plugin not found: %s", name)
	}

	// Get resource usage from sandbox
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	usage, err := pm.sandbox.MonitorResources(ctx, info.Instance)
	if err != nil {
		return fmt.Errorf("failed to monitor resources: %w", err)
	}

	// Update stored usage
	pm.mu.Lock()
	info.Resources = usage
	pm.mu.Unlock()

	return nil
}

// Events returns the event channel
func (pm *PluginManager) Events() <-chan Event {
	return pm.events
}

// healthCheckLoop performs periodic health checks
func (pm *PluginManager) healthCheckLoop(ctx context.Context) {
	defer pm.wg.Done()

	ticker := time.NewTicker(pm.healthCheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-pm.stopChan:
			return
		case <-ticker.C:
			pm.performHealthChecks(ctx)
		}
	}
}

// performHealthChecks checks health of all plugins
func (pm *PluginManager) performHealthChecks(ctx context.Context) {
	pm.mu.RLock()
	pluginNames := make([]string, 0, len(pm.plugins))
	for name := range pm.plugins {
		pluginNames = append(pluginNames, name)
	}
	pm.mu.RUnlock()

	for _, name := range pluginNames {
		if _, err := pm.HealthCheck(ctx, name); err != nil {
			// Log error but continue
		}
	}
}

// resourceCheckLoop performs periodic resource checks
func (pm *PluginManager) resourceCheckLoop(ctx context.Context) {
	defer pm.wg.Done()

	ticker := time.NewTicker(pm.resourceCheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-pm.stopChan:
			return
		case <-ticker.C:
			pm.performResourceChecks()
		}
	}
}

// performResourceChecks checks resources of all plugins
func (pm *PluginManager) performResourceChecks() {
	pm.mu.RLock()
	pluginNames := make([]string, 0, len(pm.plugins))
	for name := range pm.plugins {
		pluginNames = append(pluginNames, name)
	}
	pm.mu.RUnlock()

	for _, name := range pluginNames {
		if err := pm.UpdateResources(name); err != nil {
			// Log error but continue
		}
	}
}

// emitEvent emits an event to the channel
func (pm *PluginManager) emitEvent(event Event) {
	select {
	case pm.events <- event:
	default:
		// Channel full, drop event
	}
}

// isFilePath checks if string looks like a file path
func isFilePath(s string) bool {
	// Simple heuristic: contains / or \ or ends with .so
	return len(s) > 0 && (s[0] == '/' || s[0] == '.' || s[len(s)-3:] == ".so")
}
