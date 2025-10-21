vCLI 2.0 Implementation Blueprint - Complete Edition
Universal Distributed Operating System Interface - Technical Implementation Guide

Executive Summary
This complete blueprint provides a detailed implementation roadmap for vCLI 2.0, transforming it from a traditional CLI utility into a comprehensive distributed operating system interface. The implementation follows a three-phase approach prioritizing architectural foundation, distributed governance, and intelligent automation, with comprehensive enhancements for plugin architecture, configuration management, offline operations, and migration strategy.

Table of Contents
Architecture Overview
Technology Stack
Phase 1: Foundation & Interaction Kernel
Phase 2: Distribution & Governance
Phase 3: Intelligence & Automation
Plugin Architecture Enhancement
Configuration Management Hierarchy
Offline Mode Specification
Migration Strategy from Existing Tools
Security Framework
Performance Requirements
Testing Strategy
Deployment & Operations
Risk Assessment & Mitigation
Implementation Roadmap
Architecture Overview
Core Components
Code
┌─────────────────────────────────────────────────────────────────┐
│                    vCLI 2.0 Complete Architecture              │
├─────────────────────────────────────────────────────────────────┤
│  Terminal User Interface (TUI) - Bubble Tea/Go                 │
├─────────────────────────────────────────────────────────────────┤
│  Plugin System - Dynamic Loading & Extension                   │
│  ┌─────────────────┬─────────────────┬─────────────────────────┐ │
│  │ Core Plugins    │ Community Plugins│ Custom Plugins         │ │
│  └─────────────────┴─────────────────┴─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  State Core - ELM/MVU Pattern                                  │
│  ┌─────────────────┬─────────────────┬─────────────────────────┐ │
│  │ Model (State)   │ Actions/Msgs    │ Update Functions        │ │
│  └─────────────────┴─────────────────┴─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Configuration Layer - Hierarchical Config Management          │
│  ┌─────────────────┬─────────────────┬─────────────────────────┐ │
│  │ User Config     │ Cluster Config  │ Fleet Config            │ │
│  └─────────────────┴─────────────────┴─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Offline Mode - Local Cache & Queued Operations                │
│  ┌─────────────────┬─────────────────┬─────────────────────────┐ │
│  │ Local Storage   │ Sync Engine     │ Conflict Resolution     │ │
│  └─────────────────┴─────────────────┴─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Migration Framework - Tool Compatibility                      │
│  ┌─────────────────┬─────────────────┬─────────────────────────┐ │
│  │ kubectl Bridge  │ k9s Compat      │ Custom Tool Adapters    │ │
│  └─────────────────┴─────────────────┴─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Contextual Intelligence Layer - AIOps                         │
│  ┌─────────────────┬─────────────────┬─────────────────────────┐ │
│  │ Event Correlation│ Anomaly Detection│ SOAR Automation       │ │
│  └─────────────────┴─────────────────┴─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Orchestration Fabric - Hub-Spoke Model                        │
│  ┌─────────────────┬─────────────────┬─────────────────────────┐ │
│  │ Hub Cluster     │ Spoke Clusters  │ Multi-Cluster Services  │ │
│  └─────────────────┴─────────────────┴─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Zero Trust Security - Continuous Verification                 │
└─────────────────────────────────────────────────────────────────┘
Design Principles
Unidirectional Data Flow: All state changes flow through the MVU pattern
Zero Trust by Design: Continuous verification of all operations
Contextual Intelligence: Proactive assistance through AIOps
Declarative Management: GitOps-style infrastructure as code
Performance First: Sub-100ms response times for UI interactions
Extensibility: Plugin-based architecture for community contributions
Offline Resilience: Graceful degradation and local operation capability
Migration Friendly: Seamless transition from existing tools
Technology Stack
Core Technologies
Component	Technology	Justification
Language	Go 1.21+	Single binary, excellent concurrency, mature ecosystem
TUI Framework	Bubble Tea	MVU pattern enforcement, predictable state flow
State Management	Custom MVU	Unidirectional data flow, immutable state
API Framework	Gin/Echo	High performance HTTP routing
Database	ClickHouse	Time-series analytics, real-time queries
Message Queue	NATS	Cloud-native messaging, clustering support
Security	SPIFFE/SPIRE	Zero Trust identity framework
Observability	OpenTelemetry	Distributed tracing and metrics
Plugin System	Go Plugins	Dynamic loading, native performance
Config Management	Viper	Hierarchical configuration
Offline Storage	BadgerDB	Fast, embedded key-value store
Dependencies
Go
// Core dependencies
github.com/charmbracelet/bubbletea
github.com/charmbracelet/lipgloss
github.com/spf13/cobra
github.com/spf13/viper

// Plugin system
plugin
reflect
go/types
go/parser

// Kubernetes integration
k8s.io/client-go
k8s.io/apimachinery
sigs.k8s.io/controller-runtime

// Security
github.com/spiffe/go-spiffe/v2
github.com/golang-jwt/jwt/v5

// Observability
go.opentelemetry.io/otel
go.opentelemetry.io/otel/trace

// Offline storage
github.com/dgraph-io/badger/v3
github.com/vmihailenco/msgpack/v5

// Migration tools
github.com/mitchellh/mapstructure
gopkg.in/yaml.v3
Phase 1: Foundation & Interaction Kernel
Timeline: Q1-Q2 (6 months)
Objective: Establish core TUI, state management, plugin system, and basic security

1.1 Project Structure
Code
vcli/
├── cmd/                    # CLI commands and entry points
│   ├── root.go
│   ├── cluster.go
│   ├── plugin.go
│   ├── migrate.go
│   └── auth.go
├── internal/
│   ├── tui/               # Terminal UI components
│   │   ├── model.go       # State model definitions
│   │   ├── update.go      # Update functions
│   │   ├── view.go        # View rendering
│   │   └── components/    # Reusable UI components
│   ├── core/              # Core business logic
│   │   ├── state.go       # State management
│   │   ├── actions.go     # Action definitions
│   │   └── cluster.go     # Cluster operations
│   ├── plugins/           # Plugin management
│   │   ├── manager.go     # Plugin lifecycle
│   │   ├── loader.go      # Dynamic loading
│   │   ├── registry.go    # Plugin registry
│   │   └── sandbox.go     # Security sandbox
│   ├── config/            # Configuration management
│   │   ├── hierarchy.go   # Config layering
│   │   ├── resolver.go    # Value resolution
│   │   ├── watcher.go     # Config watching
│   │   └── merger.go      # Config merging
│   ├── offline/           # Offline mode
│   │   ├── cache.go       # Local caching
│   │   ├── queue.go       # Operation queuing
│   │   ├── sync.go        # Synchronization
│   │   └── conflict.go    # Conflict resolution
│   ├── migration/         # Migration tools
│   │   ├── kubectl.go     # kubectl migration
│   │   ├── k9s.go         # k9s compatibility
│   │   ├── helm.go        # helm integration
│   │   ├── docker.go      # docker compatibility
│   │   └── detector.go    # Tool detection
│   ├── auth/              # Authentication & authorization
│   │   ├── provider.go    # Auth provider interface
│   │   ├── oidc.go        # OIDC implementation
│   │   └── rbac.go        # RBAC enforcement
│   └── api/               # API clients
│       ├── kubernetes.go  # K8s client wrapper
│       └── metrics.go     # Metrics collection
├── pkg/                   # Public packages
│   ├── config/            # Configuration management
│   ├── types/             # Shared types
│   └── plugin/            # Plugin interfaces
├── plugins/               # Built-in plugins
│   ├── kubernetes/        # Kubernetes plugin
│   ├── prometheus/        # Prometheus plugin
│   ├── git/               # Git plugin
│   └── docker/            # Docker plugin
├── configs/               # Configuration files
├── docs/                  # Documentation
├── migrations/            # Migration configs
└── scripts/               # Build and deployment scripts
1.2 State Management Implementation
Core State Model
Go
// internal/tui/model.go
package tui

import (
    "time"
    tea "github.com/charmbracelet/bubbletea"
)

type Model struct {
    // UI State
    ActiveView    ViewType
    WindowSize    tea.WindowSizeMsg
    Focused       ComponentID
    
    // Cluster State
    Clusters      []ClusterInfo
    ActiveCluster string
    Resources     map[string][]Resource
    
    // Plugin State
    LoadedPlugins map[string]Plugin
    PluginViews   map[string]PluginView
    
    // Configuration State
    Config        ConfigHierarchy
    ConfigWatcher ConfigWatcher
    
    // Offline State
    OfflineMode   bool
    CachedData    CacheStorage
    QueuedOps     []QueuedOperation
    
    // Migration State
    MigrationStatus map[string]MigrationState
    ActiveMigration *MigrationSession
    
    // Real-time Data
    Metrics       MetricsData
    Events        []Event
    LastUpdate    time.Time
    
    // User Context
    User          UserInfo
    Permissions   PermissionSet
    
    // System State
    Loading       map[string]bool
    Errors        []Error
}

type Action interface {
    Type() ActionType
}

// Action definitions
type ClusterSelectAction struct {
    ClusterID string
}

type PluginLoadAction struct {
    PluginName string
    PluginPath string
}

type ConfigUpdateAction struct {
    Config ConfigUpdate
}

type OfflineModeAction struct {
    Enabled bool
}

type MigrationStartAction struct {
    SourceTool string
    TargetConfig MigrationConfig
}

type MetricsUpdateAction struct {
    Data MetricsData
}

type ErrorAction struct {
    Error error
    Context string
}
Update Function
Go
// internal/tui/update.go
package tui

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        return m.handleKeyPress(msg)
    case tea.WindowSizeMsg:
        return m.updateWindowSize(msg), nil
    case ClusterSelectAction:
        return m.selectCluster(msg.ClusterID), m.loadClusterResources(msg.ClusterID)
    case PluginLoadAction:
        return m.loadPlugin(msg.PluginName, msg.PluginPath), nil
    case ConfigUpdateAction:
        return m.updateConfig(msg.Config), nil
    case OfflineModeAction:
        return m.toggleOfflineMode(msg.Enabled), nil
    case MigrationStartAction:
        return m.startMigration(msg.SourceTool, msg.TargetConfig), nil
    case MetricsUpdateAction:
        return m.updateMetrics(msg.Data), m.scheduleNextMetricsUpdate()
    case ErrorAction:
        return m.addError(msg), nil
    }
    return m, nil
}

func (m Model) selectCluster(clusterID string) Model {
    newModel := m
    newModel.ActiveCluster = clusterID
    newModel.Loading["resources"] = true
    
    // Check offline mode
    if newModel.OfflineMode {
        newModel = newModel.loadFromCache(clusterID)
    }
    
    return newModel
}

func (m Model) startMigration(sourceTool string, config MigrationConfig) Model {
    newModel := m
    
    session := &MigrationSession{
        ID:         generateMigrationID(),
        SourceTool: sourceTool,
        Config:     config,
        Status:     MigrationStatusStarted,
        StartTime:  time.Now(),
    }
    
    newModel.ActiveMigration = session
    newModel.Loading["migration"] = true
    
    return newModel
}
1.3 Real-time Monitoring Implementation
Metrics Collection
Go
// internal/core/metrics.go
package core

type MetricsCollector struct {
    kubeClient kubernetes.Interface
    collectors map[string]Collector
    interval   time.Duration
    cache      MetricsCache
    offline    bool
}

func (mc *MetricsCollector) Start(ctx context.Context, updates chan<- MetricsData) {
    ticker := time.NewTicker(mc.interval)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            data := mc.collectAll(ctx)
            
            // Cache data for offline mode
            mc.cache.Store(data)
            
            select {
            case updates <- data:
            default:
                // Drop update if channel is full
            }
        }
    }
}

func (mc *MetricsCollector) collectAll(ctx context.Context) MetricsData {
    data := MetricsData{
        Timestamp: time.Now(),
        Clusters:  make(map[string]ClusterMetrics),
    }
    
    for clusterID, collector := range mc.collectors {
        var metrics ClusterMetrics
        var err error
        
        if mc.offline {
            metrics, err = mc.cache.Get(clusterID)
        } else {
            metrics, err = collector.Collect(ctx)
        }
        
        if err != nil {
            log.Error("Failed to collect metrics", "cluster", clusterID, "error", err)
            continue
        }
        data.Clusters[clusterID] = metrics
    }
    
    return data
}
Plugin Architecture Enhancement
6.1 Plugin System Design
Core Plugin Interface
Go
// pkg/plugin/interface.go
package plugin

import (
    "context"
    tea "github.com/charmbracelet/bubbletea"
)

type Plugin interface {
    // Metadata
    Name() string
    Version() string
    Description() string
    Author() string
    License() string
    
    // Lifecycle
    Initialize(ctx PluginContext) error
    Shutdown(ctx context.Context) error
    Health() HealthStatus
    
    // Capabilities
    Commands() []Command
    TUIComponents() []TUIComponent
    EventHandlers() []EventHandler
    ConfigSchema() ConfigSchema
    
    // Integration points
    RegisterHooks(hookRegistry HookRegistry) error
    HandleEvent(event Event) error
}

type PluginContext struct {
    Config       PluginConfig
    Logger       Logger
    StateManager StateManager
    APIClient    APIClient
    TUIManager   TUIManager
    Cache        CacheManager
    EventBus     EventBus
}

type Command struct {
    Name        string
    Description string
    Usage       string
    Flags       []Flag
    Handler     CommandHandler
    Aliases     []string
    Category    string
    Examples    []Example
}

type TUIComponent struct {
    ID          string
    Type        ComponentType
    Position    Position
    Size        Size
    Renderer    ComponentRenderer
    Handler     ComponentHandler
    Config      ComponentConfig
}

type EventHandler struct {
    EventType EventType
    Handler   func(Event) error
    Priority  int
}

type ConfigSchema struct {
    Properties map[string]PropertySchema
    Required   []string
    Default    map[string]interface{}
}
Plugin Manager Implementation
Go
// internal/plugins/manager.go
package plugins

type PluginManager struct {
    plugins      map[string]LoadedPlugin
    registry     PluginRegistry
    loader       PluginLoader
    sandbox      SecuritySandbox
    dependencies DependencyResolver
    hooks        HookRegistry
    eventBus     EventBus
    metrics      PluginMetrics
}

type LoadedPlugin struct {
    Plugin   Plugin
    Config   PluginConfig
    State    PluginState
    Metrics  PluginMetrics
    Security SecurityContext
    Health   HealthStatus
}

type PluginState string

const (
    PluginStateLoaded   PluginState = "loaded"
    PluginStateActive   PluginState = "active"
    PluginStateStopped  PluginState = "stopped"
    PluginStateError    PluginState = "error"
)

func NewPluginManager(config PluginManagerConfig) *PluginManager {
    return &PluginManager{
        plugins:      make(map[string]LoadedPlugin),
        registry:     NewPluginRegistry(config.RegistryURL),
        loader:       NewPluginLoader(config.LoaderConfig),
        sandbox:      NewSecuritySandbox(config.SandboxConfig),
        dependencies: NewDependencyResolver(),
        hooks:        NewHookRegistry(),
        eventBus:     NewEventBus(),
        metrics:      NewPluginMetrics(),
    }
}

func (pm *PluginManager) LoadPlugin(path string, config PluginConfig) error {
    // Validate plugin binary
    if err := pm.validatePluginBinary(path); err != nil {
        return fmt.Errorf("plugin validation failed: %w", err)
    }
    
    // Load plugin in sandbox
    plugin, err := pm.loader.Load(path)
    if err != nil {
        return fmt.Errorf("failed to load plugin: %w", err)
    }
    
    // Verify compatibility
    if err := pm.verifyCompatibility(plugin); err != nil {
        return fmt.Errorf("compatibility check failed: %w", err)
    }
    
    // Resolve dependencies
    if err := pm.dependencies.Resolve(plugin); err != nil {
        return fmt.Errorf("dependency resolution failed: %w", err)
    }
    
    // Initialize plugin context
    ctx := PluginContext{
        Config:       config,
        Logger:       pm.createPluginLogger(plugin.Name()),
        StateManager: pm.createPluginStateManager(plugin.Name()),
        APIClient:    pm.createPluginAPIClient(plugin.Name()),
        TUIManager:   pm.createPluginTUIManager(plugin.Name()),
        Cache:        pm.createPluginCache(plugin.Name()),
        EventBus:     pm.eventBus,
    }
    
    // Initialize plugin
    if err := plugin.Initialize(ctx); err != nil {
        return fmt.Errorf("plugin initialization failed: %w", err)
    }
    
    // Register hooks
    if err := plugin.RegisterHooks(pm.hooks); err != nil {
        return fmt.Errorf("hook registration failed: %w", err)
    }
    
    // Store loaded plugin
    pm.plugins[plugin.Name()] = LoadedPlugin{
        Plugin:   plugin,
        Config:   config,
        State:    PluginStateLoaded,
        Security: pm.createSecurityContext(plugin),
        Health:   HealthStatusHealthy,
    }
    
    // Start health monitoring
    go pm.monitorPluginHealth(plugin.Name())
    
    // Emit load event
    pm.eventBus.Emit(PluginLoadedEvent{
        PluginName: plugin.Name(),
        Version:    plugin.Version(),
        Timestamp:  time.Now(),
    })
    
    return nil
}

func (pm *PluginManager) ExecutePluginCommand(pluginName, commandName string, args []string) error {
    plugin, exists := pm.plugins[pluginName]
    if !exists {
        return fmt.Errorf("plugin %s not found", pluginName)
    }
    
    // Check plugin health
    if plugin.Health != HealthStatusHealthy {
        return fmt.Errorf("plugin %s is not healthy", pluginName)
    }
    
    // Find command
    var targetCommand *Command
    for _, cmd := range plugin.Plugin.Commands() {
        if cmd.Name == commandName {
            targetCommand = &cmd
            break
        }
    }
    
    if targetCommand == nil {
        return fmt.Errorf("command %s not found in plugin %s", commandName, pluginName)
    }
    
    // Execute in security context
    return pm.sandbox.Execute(func() error {
        return targetCommand.Handler(args)
    }, plugin.Security)
}

func (pm *PluginManager) monitorPluginHealth(pluginName string) {
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()
    
    for range ticker.C {
        plugin, exists := pm.plugins[pluginName]
        if !exists {
            return
        }
        
        health := plugin.Plugin.Health()
        if health != plugin.Health {
            pm.plugins[pluginName] = LoadedPlugin{
                Plugin:   plugin.Plugin,
                Config:   plugin.Config,
                State:    plugin.State,
                Security: plugin.Security,
                Health:   health,
            }
            
            pm.eventBus.Emit(PluginHealthChangedEvent{
                PluginName: pluginName,
                OldHealth:  plugin.Health,
                NewHealth:  health,
                Timestamp:  time.Now(),
            })
        }
    }
}
Plugin Discovery and Registry
Go
// internal/plugins/registry.go
package plugins

type PluginRegistry struct {
    store       PluginStore
    cache       PluginCache
    validator   PluginValidator
    indexer     PluginIndexer
    downloader  PluginDownloader
}

type PluginManifest struct {
    Name         string            `yaml:"name"`
    Version      string            `yaml:"version"`
    Description  string            `yaml:"description"`
    Author       string            `yaml:"author"`
    License      string            `yaml:"license"`
    Homepage     string            `yaml:"homepage"`
    Repository   string            `yaml:"repository"`
    Keywords     []string          `yaml:"keywords"`
    Dependencies []PluginDependency `yaml:"dependencies"`
    Permissions  []Permission      `yaml:"permissions"`
    Checksum     string            `yaml:"checksum"`
    Binary       BinaryInfo        `yaml:"binary"`
}

type PluginDependency struct {
    Name    string `yaml:"name"`
    Version string `yaml:"version"`
    Type    string `yaml:"type"` // plugin, system, library
}

type BinaryInfo struct {
    Platform string `yaml:"platform"`
    Arch     string `yaml:"arch"`
    Size     int64  `yaml:"size"`
    URL      string `yaml:"url"`
}

func (pr *PluginRegistry) DiscoverPlugins(searchPaths []string) ([]PluginManifest, error) {
    var manifests []PluginManifest
    
    for _, path := range searchPaths {
        found, err := pr.scanDirectory(path)
        if err != nil {
            log.Warn("Failed to scan directory", "path", path, "error", err)
            continue
        }
        manifests = append(manifests, found...)
    }
    
    // Validate and resolve dependencies
    resolved, err := pr.dependencies.Resolve(manifests)
    if err != nil {
        return nil, fmt.Errorf("dependency resolution failed: %w", err)
    }
    
    return resolved, nil
}

func (pr *PluginRegistry) SearchPlugins(query SearchQuery) ([]PluginManifest, error) {
    // Search in local store first
    local, err := pr.store.Search(query)
    if err != nil {
        log.Warn("Local search failed", "error", err)
    }
    
    // Search in remote registry
    remote, err := pr.searchRemote(query)
    if err != nil {
        log.Warn("Remote search failed", "error", err)
    }
    
    // Merge and deduplicate results
    return pr.mergeResults(local, remote), nil
}

func (pr *PluginRegistry) InstallPlugin(source PluginSource) error {
    // Download plugin
    plugin, err := pr.downloader.Download(source)
    if err != nil {
        return fmt.Errorf("download failed: %w", err)
    }
    
    // Validate checksum and signatures
    if err := pr.validator.ValidatePlugin(plugin); err != nil {
        return fmt.Errorf("plugin validation failed: %w", err)
    }
    
    // Check dependencies
    if err := pr.dependencies.CheckDependencies(plugin.Manifest); err != nil {
        return fmt.Errorf("dependency check failed: %w", err)
    }
    
    // Install to plugin directory
    installPath := pr.getInstallPath(plugin.Manifest.Name)
    if err := pr.installToPath(plugin, installPath); err != nil {
        return fmt.Errorf("installation failed: %w", err)
    }
    
    // Update registry
    pr.store.AddPlugin(plugin.Manifest)
    pr.indexer.IndexPlugin(plugin.Manifest)
    
    log.Info("Plugin installed successfully", 
        "name", plugin.Manifest.Name, 
        "version", plugin.Manifest.Version)
    
    return nil
}

func (pr *PluginRegistry) UninstallPlugin(name string) error {
    // Check if plugin is loaded
    if globalPluginManager.IsLoaded(name) {
        if err := globalPluginManager.UnloadPlugin(name); err != nil {
            return fmt.Errorf("failed to unload plugin: %w", err)
        }
    }
    
    // Remove plugin files
    pluginPath := pr.getInstallPath(name)
    if err := os.RemoveAll(pluginPath); err != nil {
        return fmt.Errorf("failed to remove plugin files: %w", err)
    }
    
    // Update registry
    pr.store.RemovePlugin(name)
    pr.indexer.UnindexPlugin(name)
    
    return nil
}
Security Sandbox
Go
// internal/plugins/sandbox.go
package plugins

type SecuritySandbox struct {
    namespaces    NamespaceManager
    permissions   PermissionManager
    resources     ResourceManager
    monitor       SecurityMonitor
    policies      SecurityPolicyEngine
}

type SecurityContext struct {
    Namespace   string
    Permissions []Permission
    Resources   ResourceLimits
    Policies    []SecurityPolicy
    Isolation   IsolationLevel
}

type ResourceLimits struct {
    MaxMemoryMB    int
    MaxCPUPercent  float64
    MaxGoroutines  int
    MaxFileHandles int
    NetworkAccess  []NetworkRule
    DiskQuotaMB    int
}

type IsolationLevel string

const (
    IsolationLevelNone   IsolationLevel = "none"
    IsolationLevelLight  IsolationLevel = "light"
    IsolationLevelStrict IsolationLevel = "strict"
)

func NewSecuritySandbox(config SandboxConfig) *SecuritySandbox {
    return &SecuritySandbox{
        namespaces:  NewNamespaceManager(),
        permissions: NewPermissionManager(),
        resources:   NewResourceManager(),
        monitor:     NewSecurityMonitor(),
        policies:    NewSecurityPolicyEngine(config.PoliciesPath),
    }
}

func (ss *SecuritySandbox) Execute(fn func() error, ctx SecurityContext) error {
    // Create isolated namespace
    namespace, err := ss.namespaces.Create(ctx.Namespace)
    if err != nil {
        return fmt.Errorf("failed to create namespace: %w", err)
    }
    defer ss.namespaces.Destroy(namespace)
    
    // Apply resource limits
    limiter := ss.resources.CreateLimiter(ctx.Resources)
    defer limiter.Release()
    
    // Start security monitoring
    monitor := ss.monitor.StartMonitoring(ctx)
    defer monitor.Stop()
    
    // Execute function with limits
    return limiter.Execute(func() error {
        return ss.executeWithPolicies(fn, ctx.Policies)
    })
}

func (ss *SecuritySandbox) ValidatePermission(pluginName string, permission Permission) error {
    plugin, exists := ss.getPluginContext(pluginName)
    if !exists {
        return fmt.Errorf("plugin %s not found", pluginName)
    }
    
    // Check if permission is granted
    for _, granted := range plugin.Permissions {
        if ss.permissions.Matches(granted, permission) {
            // Log permission usage
            ss.monitor.LogPermissionUsage(pluginName, permission)
            return nil
        }
    }
    
    // Log permission violation
    ss.monitor.LogPermissionViolation(pluginName, permission)
    
    return fmt.Errorf("permission %s not granted to plugin %s", permission.String(), pluginName)
}

func (ss *SecuritySandbox) executeWithPolicies(fn func() error, policies []SecurityPolicy) error {
    // Apply security policies
    for _, policy := range policies {
        if err := ss.policies.Apply(policy); err != nil {
            return fmt.Errorf("failed to apply security policy: %w", err)
        }
    }
    
    // Execute function
    err := fn()
    
    // Cleanup policies
    for _, policy := range policies {
        ss.policies.Cleanup(policy)
    }
    
    return err
}
6.2 Core Plugins
Kubernetes Plugin
Go
// plugins/kubernetes/plugin.go
package kubernetes

type KubernetesPlugin struct {
    client    kubernetes.Interface
    config    KubernetesConfig
    cache     ResourceCache
    watcher   ResourceWatcher
    discovery DiscoveryClient
}

func NewPlugin() plugin.Plugin {
    return &KubernetesPlugin{}
}

func (k *KubernetesPlugin) Name() string {
    return "kubernetes"
}

func (k *KubernetesPlugin) Version() string {
    return "1.0.0"
}

func (k *KubernetesPlugin) Description() string {
    return "Kubernetes cluster management and resource operations"
}

func (k *KubernetesPlugin) Commands() []plugin.Command {
    return []plugin.Command{
        {
            Name:        "get",
            Description: "Get Kubernetes resources",
            Usage:       "vcli kubernetes get <resource> [name] [flags]",
            Handler:     k.handleGet,
            Flags: []plugin.Flag{
                {Name: "namespace", Short: "n", Type: "string", Description: "Namespace to query"},
                {Name: "output", Short: "o", Type: "string", Description: "Output format"},
                {Name: "all-namespaces", Type: "bool", Description: "List across all namespaces"},
            },
            Examples: []plugin.Example{
                {Command: "vcli kubernetes get pods", Description: "List all pods in current namespace"},
                {Command: "vcli kubernetes get pods -n kube-system", Description: "List pods in kube-system namespace"},
            },
        },
        {
            Name:        "describe",
            Description: "Describe Kubernetes resources",
            Usage:       "vcli kubernetes describe <resource> <name> [flags]",
            Handler:     k.handleDescribe,
            Flags: []plugin.Flag{
                {Name: "namespace", Short: "n", Type: "string", Description: "Namespace of the resource"},
            },
        },
        {
            Name:        "logs",
            Description: "Get pod logs",
            Usage:       "vcli kubernetes logs <pod> [flags]",
            Handler:     k.handleLogs,
            Flags: []plugin.Flag{
                {Name: "follow", Short: "f", Type: "bool", Description: "Follow log output"},
                {Name: "tail", Type: "int", Description: "Number of lines to show from the end"},
                {Name: "container", Short: "c", Type: "string", Description: "Container name"},
            },
        },
        {
            Name:        "exec",
            Description: "Execute command in pod",
            Usage:       "vcli kubernetes exec <pod> -- <command>",
            Handler:     k.handleExec,
            Flags: []plugin.Flag{
                {Name: "interactive", Short: "i", Type: "bool", Description: "Pass stdin to container"},
                {Name: "tty", Short: "t", Type: "bool", Description: "Allocate a TTY"},
                {Name: "container", Short: "c", Type: "string", Description: "Container name"},
            },
        },
    }
}

func (k *KubernetesPlugin) TUIComponents() []plugin.TUIComponent {
    return []plugin.TUIComponent{
        {
            ID:   "resource-list",
            Type: plugin.ComponentTypeList,
            Config: plugin.ComponentConfig{
                Title:       "Kubernetes Resources",
                Keybindings: k.getResourceListKeybindings(),
                Refresh:     5 * time.Second,
            },
            Renderer: k.createResourceListRenderer(),
            Handler:  k.createResourceListHandler(),
        },
        {
            ID:   "pod-logs",
            Type: plugin.ComponentTypeViewer,
            Config: plugin.ComponentConfig{
                Title:       "Pod Logs",
                Keybindings: k.getLogViewerKeybindings(),
                AutoScroll:  true,
            },
            Renderer: k.createLogViewerRenderer(),
            Handler:  k.createLogViewerHandler(),
        },
        {
            ID:   "resource-details",
            Type: plugin.ComponentTypeDetails,
            Config: plugin.ComponentConfig{
                Title:       "Resource Details",
                Keybindings: k.getDetailsKeybindings(),
            },
            Renderer: k.createDetailsRenderer(),
            Handler:  k.createDetailsHandler(),
        },
    }
}

func (k *KubernetesPlugin) handleGet(args []string, flags map[string]interface{}) error {
    if len(args) < 1 {
        return fmt.Errorf("resource type is required")
    }
    
    resourceType := args[0]
    namespace := k.getNamespaceFromFlags(flags)
    output := k.getOutputFromFlags(flags)
    
    // Get resources from API or cache
    var resources []unstructured.Unstructured
    var err error
    
    if k.cache.IsValid(resourceType, namespace) && !k.shouldRefresh() {
        resources, err = k.cache.Get(resourceType, namespace)
    } else {
        resources, err = k.fetchResourcesFromAPI(resourceType, namespace)
        if err == nil {
            k.cache.Set(resourceType, namespace, resources)
        }
    }
    
    if err != nil {
        return fmt.Errorf("failed to get resources: %w", err)
    }
    
    // Format and display results
    return k.displayResources(resourceType, resources, output)
}

func (k *KubernetesPlugin) handleLogs(args []string, flags map[string]interface{}) error {
    if len(args) < 1 {
        return fmt.Errorf("pod name is required")
    }
    
    podName := args[0]
    namespace := k.getNamespaceFromFlags(flags)
    follow := k.getBoolFlag(flags, "follow")
    tail := k.getIntFlag(flags, "tail")
    container := k.getStringFlag(flags, "container")
    
    logOptions := &v1.PodLogOptions{
        Follow:    follow,
        Container: container,
    }
    
    if tail > 0 {
        tailLines := int64(tail)
        logOptions.TailLines = &tailLines
    }
    
    return k.streamPodLogs(podName, namespace, logOptions)
}
Prometheus Plugin
Go
// plugins/prometheus/plugin.go
package prometheus

type PrometheusPlugin struct {
    client    promapi.Client
    config    PrometheusConfig
    queries   QueryEngine
    dashboard DashboardManager
}

func NewPlugin() plugin.Plugin {
    return &PrometheusPlugin{}
}

func (p *PrometheusPlugin) Commands() []plugin.Command {
    return []plugin.Command{
        {
            Name:        "query",
            Description: "Execute Prometheus query",
            Usage:       "vcli prometheus query <query> [flags]",
            Handler:     p.handleQuery,
            Flags: []plugin.Flag{
                {Name: "time", Short: "t", Type: "string", Description: "Query time (RFC3339)"},
                {Name: "timeout", Type: "duration", Description: "Query timeout"},
                {Name: "output", Short: "o", Type: "string", Description: "Output format"},
            },
            Examples: []plugin.Example{
                {Command: "vcli prometheus query 'up'", Description: "Query target status"},
                {Command: "vcli prometheus query 'rate(http_requests_total[5m])'", Description: "Query request rate"},
            },
        },
        {
            Name:        "alerts",
            Description: "Show active alerts",
            Usage:       "vcli prometheus alerts [flags]",
            Handler:     p.handleAlerts,
            Flags: []plugin.Flag{
                {Name: "state", Type: "string", Description: "Filter by alert state"},
                {Name: "label", Type: "string", Description: "Filter by label selector"},
            },
        },
        {
            Name:        "rules",
            Description: "Show recording and alerting rules",
            Usage:       "vcli prometheus rules [flags]",
            Handler:     p.handleRules,
            Flags: []plugin.Flag{
                {Name: "type", Type: "string", Description: "Filter by rule type"},
            },
        },
    }
}

func (p *PrometheusPlugin) TUIComponents() []plugin.TUIComponent {
    return []plugin.TUIComponent{
        {
            ID:   "metrics-dashboard",
            Type: plugin.ComponentTypeDashboard,
            Config: plugin.ComponentConfig{
                Title:   "Metrics Dashboard",
                Refresh: 10 * time.Second,
            },
            Renderer: p.createDashboardRenderer(),
            Handler:  p.createDashboardHandler(),
        },
        {
            ID:   "alert-viewer",
            Type: plugin.ComponentTypeList,
            Config: plugin.ComponentConfig{
                Title:   "Active Alerts",
                Refresh: 30 * time.Second,
            },
            Renderer: p.createAlertViewerRenderer(),
            Handler:  p.createAlertViewerHandler(),
        },
        {
            ID:   "query-explorer",
            Type: plugin.ComponentTypeForm,
            Config: plugin.ComponentConfig{
                Title: "Query Explorer",
            },
            Renderer: p.createQueryExplorerRenderer(),
            Handler:  p.createQueryExplorerHandler(),
        },
    }
}

func (p *PrometheusPlugin) handleQuery(args []string, flags map[string]interface{}) error {
    if len(args) < 1 {
        return fmt.Errorf("query is required")
    }
    
    query := args[0]
    queryTime := p.getTimeFromFlags(flags)
    timeout := p.getTimeoutFromFlags(flags)
    output := p.getOutputFromFlags(flags)
    
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()
    
    result, warnings, err := p.client.Query(ctx, query, queryTime)
    if err != nil {
        return fmt.Errorf("query failed: %w", err)
    }
    
    if len(warnings) > 0 {
        for _, warning := range warnings {
            log.Warn("Query warning", "warning", warning)
        }
    }
    
    return p.displayQueryResult(result, output)
}
Configuration Management Hierarchy
7.1 Hierarchical Configuration Design
Configuration Layers
Go
// internal/config/hierarchy.go
package config

type ConfigurationHierarchy struct {
    layers []ConfigLayer
    merger ConfigMerger
    cache  ConfigCache
    watch  ConfigWatcher
    validator ConfigValidator
}

type ConfigLayer struct {
    Name     string
    Priority int
    Source   ConfigSource
    Config   Configuration
    Override bool
    Watch    bool
}

// Configuration precedence (highest to lowest):
// 1. Command Line Flags      (Priority: 100)
// 2. Environment Variables   (Priority: 90)
// 3. User Config            (Priority: 80)
// 4. Workspace Config       (Priority: 70)
// 5. Cluster Config         (Priority: 60)
// 6. Fleet Config           (Priority: 50)
// 7. Plugin Config          (Priority: 40)
// 8. Default Config         (Priority: 10)

const (
    PriorityCommandLine = 100
    PriorityEnvironment = 90
    PriorityUserConfig  = 80
    PriorityWorkspace   = 70
    PriorityClusterConfig = 60
    PriorityFleetConfig = 50
    PriorityPluginConfig = 40
    PriorityDefaultConfig = 10
)

type Configuration struct {
    Global    GlobalConfig    `yaml:"global" json:"global"`
    Clusters  []ClusterConfig `yaml:"clusters" json:"clusters"`
    Fleet     FleetConfig     `yaml:"fleet" json:"fleet"`
    Plugins   PluginConfigs   `yaml:"plugins" json:"plugins"`
    UI        UIConfig        `yaml:"ui" json:"ui"`
    Security  SecurityConfig  `yaml:"security" json:"security"`
    Telemetry TelemetryConfig `yaml:"telemetry" json:"telemetry"`
    Migration MigrationConfig `yaml:"migration" json:"migration"`
    Offline   OfflineConfig   `yaml:"offline" json:"offline"`
}

type GlobalConfig struct {
    DefaultCluster   string        `yaml:"defaultCluster" json:"defaultCluster"`
    LogLevel        string        `yaml:"logLevel" json:"logLevel"`
    LogFormat       string        `yaml:"logFormat" json:"logFormat"`
    CacheDir        string        `yaml:"cacheDir" json:"cacheDir"`
    ConfigDir       string        `yaml:"configDir" json:"configDir"`
    PluginDir       string        `yaml:"pluginDir" json:"pluginDir"`
    DataDir         string        `yaml:"dataDir" json:"dataDir"`
    UpdateInterval  time.Duration `yaml:"updateInterval" json:"updateInterval"`
    MaxConcurrency  int           `yaml:"maxConcurrency" json:"maxConcurrency"`
    Debug           bool          `yaml:"debug" json:"debug"`
    Profiling       bool          `yaml:"profiling" json:"profiling"`
}

type ClusterConfig struct {
    Name            string                 `yaml:"name" json:"name"`
    Context         string                 `yaml:"context" json:"context"`
    KubeConfig      string                 `yaml:"kubeconfig" json:"kubeconfig"`
    Namespace       string                 `yaml:"namespace" json:"namespace"`
    Alias           string                 `yaml:"alias" json:"alias"`
    AuthProvider    string                 `yaml:"authProvider" json:"authProvider"`
    TLSConfig       TLSConfig             `yaml:"tls" json:"tls"`
    Metadata        map[string]string     `yaml:"metadata" json:"metadata"`
    HealthCheck     HealthCheckConfig     `yaml:"healthCheck" json:"healthCheck"`
    Overrides       map[string]interface{} `yaml:"overrides" json:"overrides"`
    Plugins         []string              `yaml:"plugins" json:"plugins"`
    Resources       ResourceConfig        `yaml:"resources" json:"resources"`
}

type UIConfig struct {
    Theme           string          `yaml:"theme" json:"theme"`
    RefreshRate     time.Duration   `yaml:"refreshRate" json:"refreshRate"`
    Keybindings     KeybindingMap   `yaml:"keybindings" json:"keybindings"`
    Layouts         []LayoutConfig  `yaml:"layouts" json:"layouts"`
    DefaultView     string          `yaml:"defaultView" json:"defaultView"`
    ShowNamespaces  bool            `yaml:"showNamespaces" json:"showNamespaces"`
    ShowMetrics     bool            `yaml:"showMetrics" json:"showMetrics"`
    ShowLogs        bool            `yaml:"showLogs" json:"showLogs"`
    ColorScheme     ColorScheme     `yaml:"colorScheme" json:"colorScheme"`
    FontSize        int             `yaml:"fontSize" json:"fontSize"`
    ShowHelp        bool            `yaml:"showHelp" json:"showHelp"`
    AutoRefresh     bool            `yaml:"autoRefresh" json:"autoRefresh"`
}

type OfflineConfig struct {
    Enabled         bool          `yaml:"enabled" json:"enabled"`
    CacheSize       int64         `yaml:"cacheSize" json:"cacheSize"`
    CacheTTL        time.Duration `yaml:"cacheTTL" json:"cacheTTL"`
    QueueSize       int           `yaml:"queueSize" json:"queueSize"`
    SyncInterval    time.Duration `yaml:"syncInterval" json:"syncInterval"`
    ConflictStrategy string       `yaml:"conflictStrategy" json:"conflictStrategy"`
    AutoSync        bool          `yaml:"autoSync" json:"autoSync"`
}

type MigrationConfig struct {
    Enabled         bool              `yaml:"enabled" json:"enabled"`
    SourceTools     []string          `yaml:"sourceTools" json:"sourceTools"`
    ConfigPaths     map[string]string `yaml:"configPaths" json:"configPaths"`
    CreateBackups   bool              `yaml:"createBackups" json:"createBackups"`
    BackupDir       string            `yaml:"backupDir" json:"backupDir"`
    DryRun          bool              `yaml:"dryRun" json:"dryRun"`
}
Configuration Manager Implementation
Go
// internal/config/manager.go
package config

type ConfigManager struct {
    hierarchy    *ConfigurationHierarchy
    validators   []ConfigValidator
    transformers []ConfigTransformer
    persistence  ConfigPersistence
    encryption   ConfigEncryption
    watcher      ConfigWatcher
    cache        ConfigCache
}

func NewConfigManager(options ConfigManagerOptions) *ConfigManager {
    return &ConfigManager{
        hierarchy:    NewConfigurationHierarchy(),
        validators:   createDefaultValidators(),
        transformers: createDefaultTransformers(),
        persistence:  NewConfigPersistence(options.PersistenceConfig),
        encryption:   NewConfigEncryption(options.EncryptionConfig),
        watcher:      NewConfigWatcher(),
        cache:        NewConfigCache(),
    }
}

func (cm *ConfigManager) LoadConfiguration(ctx context.Context) (*Configuration, error) {
    // Check cache first
    if cached := cm.cache.Get("full-config"); cached != nil {
        return cached.(*Configuration), nil
    }
    
    // Load all configuration layers
    layers := []ConfigLayer{
        cm.loadDefaultConfig(),
        cm.loadPluginConfigs(),
        cm.loadFleetConfig(ctx),
        cm.loadClusterConfigs(ctx),
        cm.loadWorkspaceConfig(),
        cm.loadUserConfig(),
        cm.loadEnvironmentConfig(),
        cm.loadCommandLineConfig(),
    }
    
    // Merge configurations with precedence
    merged, err := cm.hierarchy.merger.Merge(layers)
    if err != nil {
        return nil, fmt.Errorf("configuration merge failed: %w", err)
    }
    
    // Validate merged configuration
    if err := cm.validateConfiguration(merged); err != nil {
        return nil, fmt.Errorf("configuration validation failed: %w", err)
    }
    
    // Apply transformations
    transformed, err := cm.applyTransformations(merged)
    if err != nil {
        return nil, fmt.Errorf("configuration transformation failed: %w", err)
    }
    
    // Cache result
    cm.cache.Set("full-config", transformed, 5*time.Minute)
    
    return transformed, nil
}

func (cm *ConfigManager) GetClusterConfig(clusterName string) (*ClusterConfig, error) {
    config, err := cm.LoadConfiguration(context.Background())
    if err != nil {
        return nil, err
    }
    
    // Find cluster configuration
    for _, cluster := range config.Clusters {
        if cluster.Name == clusterName || cluster.Alias == clusterName {
            // Apply global overrides
            enriched := cm.enrichClusterConfig(cluster, config.Global)
            return &enriched, nil
        }
    }
    
    return nil, fmt.Errorf("cluster configuration not found: %s", clusterName)
}

func (cm *ConfigManager) UpdateClusterConfig(clusterName string, updates ClusterConfig) error {
    // Load current configuration
    config, err := cm.LoadConfiguration(context.Background())
    if err != nil {
        return err
    }
    
    // Find and update cluster
    found := false
    for i, cluster := range config.Clusters {
        if cluster.Name == clusterName {
            // Merge updates
            config.Clusters[i] = cm.mergeClusterConfig(cluster, updates)
            found = true
            break
        }
    }
    
    if !found {
        // Add new cluster
        config.Clusters = append(config.Clusters, updates)
    }
    
    // Validate updated configuration
    if err := cm.validateConfiguration(config); err != nil {
        return fmt.Errorf("updated configuration is invalid: %w", err)
    }
    
    // Persist configuration
    if err := cm.persistence.SaveUserConfig(config); err != nil {
        return fmt.Errorf("failed to persist configuration: %w", err)
    }
    
    // Invalidate cache
    cm.cache.Invalidate("full-config")
    
    return nil
}

func (cm *ConfigManager) WatchConfiguration(ctx context.Context, callback func(ConfigChangeEvent)) error {
    return cm.watcher.Watch(ctx, callback)
}

func (cm *ConfigManager) validateConfiguration(config *Configuration) error {
    for _, validator := range cm.validators {
        if err := validator.Validate(config); err != nil {
            return err
        }
    }
    return nil
}
Configuration Merging Strategy
Go
// internal/config/merger.go
package config

type ConfigMerger struct {
    strategies map[string]MergeStrategy
    interpolator VariableInterpolator
}

type MergeStrategy interface {
    Merge(base, override interface{}) (interface{}, error)
}

type OverwriteMergeStrategy struct{}
type AppendMergeStrategy struct{}
type DeepMergeStrategy struct{}

func NewConfigMerger() *ConfigMerger {
    return &ConfigMerger{
        strategies: map[string]MergeStrategy{
            "overwrite": &OverwriteMergeStrategy{},
            "append":    &AppendMergeStrategy{},
            "deep":      &DeepMergeStrategy{},
        },
        interpolator: NewVariableInterpolator(),
    }
}

func (cm *ConfigMerger) Merge(layers []ConfigLayer) (*Configuration, error) {
    // Sort layers by priority (lowest first)
    sort.Slice(layers, func(i, j int) bool {
        return layers[i].Priority < layers[j].Priority
    })
    
    // Start with empty configuration
    result := &Configuration{}
    
    // Apply each layer
    for _, layer := range layers {
        merged, err := cm.mergeLayer(result, layer.Config, layer.Override)
        if err != nil {
            return nil, fmt.Errorf("failed to merge layer %s: %w", layer.Name, err)
        }
        result = merged
    }
    
    // Interpolate variables
    interpolated, err := cm.interpolator.Interpolate(result)
    if err != nil {
        return nil, fmt.Errorf("variable interpolation failed: %w", err)
    }
    
    return interpolated, nil
}

func (cm *ConfigMerger) mergeLayer(base *Configuration, overlay Configuration, override bool) (*Configuration, error) {
    result := base.DeepCopy()
    
    // Merge global configuration
    if overlay.Global != (GlobalConfig{}) {
        result.Global = cm.mergeGlobalConfig(result.Global, overlay.Global, override)
    }
    
    // Merge cluster configurations
    result.Clusters = cm.mergeClusterConfigs(result.Clusters, overlay.Clusters, override)
    
    // Merge UI configuration
    if overlay.UI != (UIConfig{}) {
        result.UI = cm.mergeUIConfig(result.UI, overlay.UI, override)
    }
    
    // Merge security configuration
    if overlay.Security != (SecurityConfig{}) {
        result.Security = cm.mergeSecurityConfig(result.Security, overlay.Security, override)
    }
    
    // Merge plugin configurations
    if len(overlay.Plugins) > 0 {
        result.Plugins = cm.mergePluginConfigs(result.Plugins, overlay.Plugins, override)
    }
    
    // Merge offline configuration
    if overlay.Offline != (OfflineConfig{}) {
        result.Offline = cm.mergeOfflineConfig(result.Offline, overlay.Offline, override)
    }
    
    // Merge migration configuration
    if overlay.Migration != (MigrationConfig{}) {
        result.Migration = cm.mergeMigrationConfig(result.Migration, overlay.Migration, override)
    }
    
    return result, nil
}

func (cm *ConfigMerger) mergeClusterConfigs(base []ClusterConfig, overlay []ClusterConfig, override bool) []ClusterConfig {
    result := make([]ClusterConfig, len(base))
    copy(result, base)
    
    for _, overlayCluster := range overlay {
        found := false
        for i, baseCluster := range result {
            if baseCluster.Name == overlayCluster.Name {
                if override {
                    result[i] = overlayCluster
                } else {
                    result[i] = cm.mergeClusterConfig(baseCluster, overlayCluster)
                }
                found = true
                break
            }
        }
        
        if !found {
            result = append(result, overlayCluster)
        }
    }
    
    return result
}
Dynamic Configuration Updates
Go
// internal/config/watcher.go
package config

type ConfigWatcher struct {
    watchers map[string]FileWatcher
    handlers map[string]ConfigChangeHandler
    debounce time.Duration
    eventBus EventBus
}

type ConfigChangeEvent struct {
    Source    string
    Path      string
    Type      ChangeType
    OldConfig *Configuration
    NewConfig *Configuration
    Timestamp time.Time
}

type ChangeType string

const (
    ChangeTypeCreate ChangeType = "create"
    ChangeTypeUpdate ChangeType = "update"
    ChangeTypeDelete ChangeType = "delete"
)

func NewConfigWatcher() *ConfigWatcher {
    return &ConfigWatcher{
        watchers: make(map[string]FileWatcher),
        handlers: make(map[string]ConfigChangeHandler),
        debounce: 500 * time.Millisecond,
        eventBus: NewEventBus(),
    }
}

func (cw *ConfigWatcher) Watch(ctx context.Context, handler ConfigChangeHandler) error {
    // Watch user config file
    userConfigPath := cw.getUserConfigPath()
    if err := cw.watchFile(ctx, "user", userConfigPath, handler); err != nil {
        return fmt.Errorf("failed to watch user config: %w", err)
    }
    
    // Watch cluster config directory
    clusterConfigDir := cw.getClusterConfigDir()
    if err := cw.watchDirectory(ctx, "cluster", clusterConfigDir, handler); err != nil {
        return fmt.Errorf("failed to watch cluster configs: %w", err)
    }
    
    // Watch workspace config
    workspaceConfigPath := cw.getWorkspaceConfigPath()
    if err := cw.watchFile(ctx, "workspace", workspaceConfigPath, handler); err != nil {
        log.Warn("Failed to watch workspace config", "error", err)
    }
    
    return nil
}

func (cw *ConfigWatcher) watchFile(ctx context.Context, source, path string, handler ConfigChangeHandler) error {
    watcher, err := NewFileWatcher(path)
    if err != nil {
        return err
    }
    
    cw.watchers[source] = watcher
    cw.handlers[source] = handler
    
    go cw.watchLoop(ctx, source, watcher, handler)
    
    return nil
}

func (cw *ConfigWatcher) watchDirectory(ctx context.Context, source, dir string, handler ConfigChangeHandler) error {
    watcher, err := NewDirectoryWatcher(dir)
    if err != nil {
        return err
    }
    
    cw.watchers[source] = watcher
    cw.handlers[source] = handler
    
    go cw.watchLoop(ctx, source, watcher, handler)
    
    return nil
}

func (cw *ConfigWatcher) watchLoop(ctx context.Context, source string, watcher FileWatcher, handler ConfigChangeHandler) {
    defer watcher.Close()
    
    var debounceTimer *time.Timer
    
    for {
        select {
        case <-ctx.Done():
            return
        case event := <-watcher.Events():
            // Debounce rapid changes
            if debounceTimer != nil {
                debounceTimer.Stop()
            }
            
            debounceTimer = time.AfterFunc(cw.debounce, func() {
                cw.handleConfigChange(source, event, handler)
            })
        case err := <-watcher.Errors():
            log.Error("Config watcher error", "source", source, "error", err)
        }
    }
}

func (cw *ConfigWatcher) handleConfigChange(source string, event FileEvent, handler ConfigChangeHandler) {
    // Load new configuration
    newConfig, err := cw.loadConfiguration(source, event.Path)
    if err != nil {
        log.Error("Failed to load configuration", "source", source, "path", event.Path, "error", err)
        return
    }
    
    // Get old configuration from cache
    oldConfig := cw.getCachedConfiguration(source)
    
    // Create change event
    changeEvent := ConfigChangeEvent{
        Source:    source,
        Path:      event.Path,
        Type:      ChangeType(event.Op.String()),
        OldConfig: oldConfig,
        NewConfig: newConfig,
        Timestamp: time.Now(),
    }
    
    // Notify handler
    handler(changeEvent)
    
    // Emit event on bus
    cw.eventBus.Emit(changeEvent)
    
    // Update cache
    cw.setCachedConfiguration(source, newConfig)
}
Variable Interpolation
Go
// internal/config/interpolation.go
package config

type VariableInterpolator struct {
    providers map[string]VariableProvider
    resolver  VariableResolver
}

type VariableProvider interface {
    GetValue(key string) (string, error)
    ListKeys() []string
}

type EnvironmentVariableProvider struct{}
type FileVariableProvider struct {
    FilePath string
}
type VaultVariableProvider struct {
    Client VaultClient
    Path   string
}

func NewVariableInterpolator() *VariableInterpolator {
    return &VariableInterpolator{
        providers: map[string]VariableProvider{
            "env":   &EnvironmentVariableProvider{},
            "file":  &FileVariableProvider{},
            "vault": &VaultVariableProvider{},
        },
        resolver: NewVariableResolver(),
    }
}

func (vi *VariableInterpolator) Interpolate(config *Configuration) (*Configuration, error) {
    configBytes, err := yaml.Marshal(config)
    if err != nil {
        return
