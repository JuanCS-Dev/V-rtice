package plugins

import (
	"context"
	"fmt"
	"runtime"
	"sync"
	"time"
)

// PluginSandbox enforces security restrictions on plugins
type PluginSandbox struct {
	mu sync.RWMutex

	// config holds sandbox configuration per plugin
	config map[string]SandboxConfig

	// monitors holds resource monitors per plugin
	monitors map[string]*resourceMonitor

	// violations tracks sandbox violations
	violations map[string][]violation
}

// resourceMonitor tracks plugin resource usage
type resourceMonitor struct {
	pluginName string

	// Resource tracking
	cpuPercent     float64
	memoryBytes    uint64
	goroutineCount int
	networkBytesIn uint64
	networkBytesOut uint64

	// Limits
	maxCPUPercent      float64
	maxMemoryBytes     uint64
	maxGoroutines      int
	maxNetworkBytesPerSec uint64

	// Tracking
	startTime       time.Time
	lastCheck       time.Time
	baseGoroutines  int
	violations      int
}

// violation represents a sandbox violation
type violation struct {
	Timestamp time.Time
	Type      string
	Message   string
	Value     interface{}
	Limit     interface{}
}

// NewPluginSandbox creates a new plugin sandbox
func NewPluginSandbox() *PluginSandbox {
	return &PluginSandbox{
		config:     make(map[string]SandboxConfig),
		monitors:   make(map[string]*resourceMonitor),
		violations: make(map[string][]violation),
	}
}

// Enforce enforces sandbox restrictions on plugin
func (ps *PluginSandbox) Enforce(ctx context.Context, plugin Plugin, config SandboxConfig) error {
	if !config.Enabled {
		return nil
	}

	metadata := plugin.Metadata()

	// Store config
	ps.mu.Lock()
	ps.config[metadata.Name] = config
	ps.mu.Unlock()

	// Validate capabilities
	if err := ps.validateCapabilities(plugin, config); err != nil {
		return fmt.Errorf("capability validation failed: %w", err)
	}

	// Create resource monitor
	monitor := &resourceMonitor{
		pluginName:         metadata.Name,
		maxCPUPercent:      config.MaxCPUPercent,
		maxMemoryBytes:     config.MaxMemoryBytes,
		maxGoroutines:      config.MaxGoroutines,
		maxNetworkBytesPerSec: config.MaxNetworkBytesPerSec,
		startTime:          time.Now(),
		lastCheck:          time.Now(),
		baseGoroutines:     runtime.NumGoroutine(),
	}

	ps.mu.Lock()
	ps.monitors[metadata.Name] = monitor
	ps.mu.Unlock()

	return nil
}

// CheckCapability checks if plugin has capability
func (ps *PluginSandbox) CheckCapability(plugin Plugin, capability Capability) bool {
	metadata := plugin.Metadata()

	// Check if plugin declares capability
	pluginCapabilities := plugin.Capabilities()
	for _, cap := range pluginCapabilities {
		if cap == capability {
			// Check if sandbox allows this capability
			ps.mu.RLock()
			config, exists := ps.config[metadata.Name]
			ps.mu.RUnlock()

			if !exists || !config.Enabled {
				return true // No sandbox, allow
			}

			// Check if capability is in allowed list
			for _, allowed := range config.AllowedCapabilities {
				if allowed == capability {
					return true
				}
			}

			return false
		}
	}

	return false
}

// MonitorResources monitors plugin resource usage
func (ps *PluginSandbox) MonitorResources(ctx context.Context, plugin Plugin) (ResourceUsage, error) {
	metadata := plugin.Metadata()

	ps.mu.RLock()
	monitor, exists := ps.monitors[metadata.Name]
	config, hasConfig := ps.config[metadata.Name]
	ps.mu.RUnlock()

	if !exists {
		return ResourceUsage{}, fmt.Errorf("no monitor for plugin: %s", metadata.Name)
	}

	// Update resource usage
	now := time.Now()

	// Get current goroutine count
	currentGoroutines := runtime.NumGoroutine()
	pluginGoroutines := currentGoroutines - monitor.baseGoroutines

	// Get memory stats
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)

	// Update monitor
	monitor.goroutineCount = pluginGoroutines
	monitor.memoryBytes = memStats.Alloc
	monitor.lastCheck = now

	// Check limits if sandbox is enabled
	if hasConfig && config.Enabled {
		if err := ps.checkLimits(monitor, config); err != nil {
			return ResourceUsage{}, err
		}
	}

	// Return usage
	usage := ResourceUsage{
		CPUPercent:      monitor.cpuPercent,
		MemoryBytes:     monitor.memoryBytes,
		GoroutineCount:  monitor.goroutineCount,
		NetworkBytesIn:  monitor.networkBytesIn,
		NetworkBytesOut: monitor.networkBytesOut,
		LastUpdated:     now,
	}

	return usage, nil
}

// Terminate terminates plugin if it violates sandbox
func (ps *PluginSandbox) Terminate(ctx context.Context, plugin Plugin, reason string) error {
	metadata := plugin.Metadata()

	// Record violation
	ps.recordViolation(metadata.Name, violation{
		Timestamp: time.Now(),
		Type:      "termination",
		Message:   reason,
	})

	// Stop plugin
	if err := plugin.Stop(ctx); err != nil {
		return fmt.Errorf("failed to terminate plugin: %w", err)
	}

	// Clean up
	ps.mu.Lock()
	delete(ps.monitors, metadata.Name)
	delete(ps.config, metadata.Name)
	ps.mu.Unlock()

	return nil
}

// GetViolations returns violations for plugin
func (ps *PluginSandbox) GetViolations(pluginName string) []violation {
	ps.mu.RLock()
	defer ps.mu.RUnlock()

	violations, exists := ps.violations[pluginName]
	if !exists {
		return []violation{}
	}

	// Return copy
	result := make([]violation, len(violations))
	copy(result, violations)
	return result
}

// validateCapabilities validates plugin capabilities against sandbox config
func (ps *PluginSandbox) validateCapabilities(plugin Plugin, config SandboxConfig) error {
	pluginCapabilities := plugin.Capabilities()

	for _, cap := range pluginCapabilities {
		allowed := false
		for _, allowedCap := range config.AllowedCapabilities {
			if cap == allowedCap {
				allowed = true
				break
			}
		}

		if !allowed {
			return fmt.Errorf("capability not allowed: %s", cap)
		}
	}

	return nil
}

// checkLimits checks if plugin exceeds resource limits
func (ps *PluginSandbox) checkLimits(monitor *resourceMonitor, config SandboxConfig) error {
	// Check CPU limit
	if config.MaxCPUPercent > 0 && monitor.cpuPercent > config.MaxCPUPercent {
		ps.recordViolation(monitor.pluginName, violation{
			Timestamp: time.Now(),
			Type:      "cpu_limit",
			Message:   fmt.Sprintf("CPU usage %.2f%% exceeds limit %.2f%%", monitor.cpuPercent, config.MaxCPUPercent),
			Value:     monitor.cpuPercent,
			Limit:     config.MaxCPUPercent,
		})
		return fmt.Errorf("CPU limit exceeded: %.2f%% > %.2f%%", monitor.cpuPercent, config.MaxCPUPercent)
	}

	// Check memory limit
	if config.MaxMemoryBytes > 0 && monitor.memoryBytes > config.MaxMemoryBytes {
		ps.recordViolation(monitor.pluginName, violation{
			Timestamp: time.Now(),
			Type:      "memory_limit",
			Message:   fmt.Sprintf("Memory usage %d bytes exceeds limit %d bytes", monitor.memoryBytes, config.MaxMemoryBytes),
			Value:     monitor.memoryBytes,
			Limit:     config.MaxMemoryBytes,
		})
		return fmt.Errorf("memory limit exceeded: %d > %d bytes", monitor.memoryBytes, config.MaxMemoryBytes)
	}

	// Check goroutine limit
	if config.MaxGoroutines > 0 && monitor.goroutineCount > config.MaxGoroutines {
		ps.recordViolation(monitor.pluginName, violation{
			Timestamp: time.Now(),
			Type:      "goroutine_limit",
			Message:   fmt.Sprintf("Goroutine count %d exceeds limit %d", monitor.goroutineCount, config.MaxGoroutines),
			Value:     monitor.goroutineCount,
			Limit:     config.MaxGoroutines,
		})
		return fmt.Errorf("goroutine limit exceeded: %d > %d", monitor.goroutineCount, config.MaxGoroutines)
	}

	return nil
}

// recordViolation records a sandbox violation
func (ps *PluginSandbox) recordViolation(pluginName string, v violation) {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	if ps.violations[pluginName] == nil {
		ps.violations[pluginName] = make([]violation, 0)
	}

	ps.violations[pluginName] = append(ps.violations[pluginName], v)

	// Limit violation history to last 100
	if len(ps.violations[pluginName]) > 100 {
		ps.violations[pluginName] = ps.violations[pluginName][len(ps.violations[pluginName])-100:]
	}
}

// NoopSandbox is a sandbox that doesn't enforce any restrictions (for testing)
type NoopSandbox struct{}

// NewNoopSandbox creates a no-op sandbox
func NewNoopSandbox() *NoopSandbox {
	return &NoopSandbox{}
}

// Enforce does nothing
func (ns *NoopSandbox) Enforce(ctx context.Context, plugin Plugin, config SandboxConfig) error {
	return nil
}

// CheckCapability always returns true
func (ns *NoopSandbox) CheckCapability(plugin Plugin, capability Capability) bool {
	return true
}

// MonitorResources returns zero usage
func (ns *NoopSandbox) MonitorResources(ctx context.Context, plugin Plugin) (ResourceUsage, error) {
	return ResourceUsage{
		LastUpdated: time.Now(),
	}, nil
}

// Terminate does nothing
func (ns *NoopSandbox) Terminate(ctx context.Context, plugin Plugin, reason string) error {
	return nil
}
