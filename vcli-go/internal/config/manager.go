package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

// Config represents the complete vCLI configuration
type Config struct {
	// Profile settings
	CurrentProfile string             `yaml:"current_profile"`
	Profiles       map[string]Profile `yaml:"profiles"`

	// Global settings
	Global GlobalConfig `yaml:"global"`

	// Service endpoints
	Endpoints EndpointsConfig `yaml:"endpoints"`

	// Cache settings
	Cache CacheConfig `yaml:"cache"`

	// Plugin settings
	Plugins PluginConfig `yaml:"plugins"`
}

// Profile represents a configuration profile
type Profile struct {
	Name        string          `yaml:"name"`
	Description string          `yaml:"description"`
	Endpoints   EndpointsConfig `yaml:"endpoints"`
	Auth        AuthConfig      `yaml:"auth"`
}

// GlobalConfig contains global settings
type GlobalConfig struct {
	Debug      bool   `yaml:"debug"`
	Offline    bool   `yaml:"offline"`
	Telemetry  bool   `yaml:"telemetry"`
	OutputFormat string `yaml:"output_format"` // json, table, yaml
	ColorOutput bool   `yaml:"color_output"`
}

// EndpointsConfig contains service endpoints
type EndpointsConfig struct {
	MAXIMUS    string `yaml:"maximus"`
	Immune     string `yaml:"immune"`
	Gateway    string `yaml:"gateway"`
	Prometheus string `yaml:"prometheus"`
	KafkaProxy string `yaml:"kafka_proxy"`
}

// AuthConfig contains authentication settings
type AuthConfig struct {
	Method    string `yaml:"method"`     // jwt, mtls, api-key
	TokenFile string `yaml:"token_file"` // Path to JWT token
	APIKey    string `yaml:"api_key"`
	CertFile  string `yaml:"cert_file"`  // mTLS cert
	KeyFile   string `yaml:"key_file"`   // mTLS key
}

// CacheConfig contains cache settings
type CacheConfig struct {
	Enabled    bool   `yaml:"enabled"`
	Path       string `yaml:"path"`
	MaxSizeMB  int    `yaml:"max_size_mb"`
	DefaultTTL string `yaml:"default_ttl"` // 5m, 1h, 24h
}

// PluginConfig contains plugin settings
type PluginConfig struct {
	Enabled     bool     `yaml:"enabled"`
	Path        string   `yaml:"path"`
	Autoload    []string `yaml:"autoload"`
	Disabled    []string `yaml:"disabled"`
}

// Manager manages configuration loading and precedence
type Manager struct {
	config     *Config
	configPath string
}

// NewManager creates a new config manager
func NewManager(configPath string) (*Manager, error) {
	m := &Manager{
		configPath: configPath,
		config:     getDefaultConfig(),
	}

	// Load config file if exists
	if err := m.Load(); err != nil {
		// Config file doesn't exist is OK, use defaults
		if !os.IsNotExist(err) {
			return nil, err
		}
	}

	// Override with environment variables
	m.applyEnvOverrides()

	return m, nil
}

// Load loads configuration from file
func (m *Manager) Load() error {
	data, err := os.ReadFile(m.configPath)
	if err != nil {
		return err
	}

	var config Config
	if err := yaml.Unmarshal(data, &config); err != nil {
		return fmt.Errorf("failed to parse config: %w", err)
	}

	m.config = &config
	return nil
}

// Save saves configuration to file
func (m *Manager) Save() error {
	// Create directory if doesn't exist
	dir := filepath.Dir(m.configPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	data, err := yaml.Marshal(m.config)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(m.configPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

// Get returns the current configuration
func (m *Manager) Get() *Config {
	return m.config
}

// GetProfile returns a specific profile
func (m *Manager) GetProfile(name string) (*Profile, error) {
	profile, ok := m.config.Profiles[name]
	if !ok {
		return nil, fmt.Errorf("profile not found: %s", name)
	}
	return &profile, nil
}

// GetCurrentProfile returns the current active profile
func (m *Manager) GetCurrentProfile() (*Profile, error) {
	return m.GetProfile(m.config.CurrentProfile)
}

// SetProfile sets the current active profile
func (m *Manager) SetProfile(name string) error {
	if _, ok := m.config.Profiles[name]; !ok {
		return fmt.Errorf("profile not found: %s", name)
	}
	m.config.CurrentProfile = name
	return m.Save()
}

// AddProfile adds a new profile
func (m *Manager) AddProfile(profile Profile) error {
	if m.config.Profiles == nil {
		m.config.Profiles = make(map[string]Profile)
	}
	m.config.Profiles[profile.Name] = profile
	return m.Save()
}

// DeleteProfile removes a profile
func (m *Manager) DeleteProfile(name string) error {
	delete(m.config.Profiles, name)
	if m.config.CurrentProfile == name {
		m.config.CurrentProfile = "default"
	}
	return m.Save()
}

// applyEnvOverrides applies environment variable overrides
func (m *Manager) applyEnvOverrides() {
	// Global settings
	if val := os.Getenv("VCLI_DEBUG"); val != "" {
		m.config.Global.Debug = val == "true" || val == "1"
	}
	if val := os.Getenv("VCLI_OFFLINE"); val != "" {
		m.config.Global.Offline = val == "true" || val == "1"
	}
	if val := os.Getenv("VCLI_OUTPUT_FORMAT"); val != "" {
		m.config.Global.OutputFormat = val
	}

	// Endpoints
	if val := os.Getenv("VCLI_MAXIMUS_ENDPOINT"); val != "" {
		m.config.Endpoints.MAXIMUS = val
	}
	if val := os.Getenv("VCLI_IMMUNE_ENDPOINT"); val != "" {
		m.config.Endpoints.Immune = val
	}
	if val := os.Getenv("VCLI_GATEWAY_ENDPOINT"); val != "" {
		m.config.Endpoints.Gateway = val
	}
	if val := os.Getenv("VCLI_PROMETHEUS_ENDPOINT"); val != "" {
		m.config.Endpoints.Prometheus = val
	}
	if val := os.Getenv("VCLI_KAFKA_PROXY_ENDPOINT"); val != "" {
		m.config.Endpoints.KafkaProxy = val
	}

	// Auth
	if val := os.Getenv("VCLI_TOKEN_FILE"); val != "" {
		if profile, err := m.GetCurrentProfile(); err == nil {
			profile.Auth.TokenFile = val
		}
	}
	if val := os.Getenv("VCLI_API_KEY"); val != "" {
		if profile, err := m.GetCurrentProfile(); err == nil {
			profile.Auth.APIKey = val
		}
	}

	// Cache
	if val := os.Getenv("VCLI_CACHE_ENABLED"); val != "" {
		m.config.Cache.Enabled = val == "true" || val == "1"
	}
	if val := os.Getenv("VCLI_CACHE_PATH"); val != "" {
		m.config.Cache.Path = val
	}
}

// GetEndpoint returns the endpoint for a service
func (m *Manager) GetEndpoint(service string) (string, error) {
	// Try current profile first
	if profile, err := m.GetCurrentProfile(); err == nil {
		switch strings.ToLower(service) {
		case "maximus":
			if profile.Endpoints.MAXIMUS != "" {
				return profile.Endpoints.MAXIMUS, nil
			}
		case "immune":
			if profile.Endpoints.Immune != "" {
				return profile.Endpoints.Immune, nil
			}
		case "gateway":
			if profile.Endpoints.Gateway != "" {
				return profile.Endpoints.Gateway, nil
			}
		case "prometheus":
			if profile.Endpoints.Prometheus != "" {
				return profile.Endpoints.Prometheus, nil
			}
		case "kafka_proxy", "kafka-proxy":
			if profile.Endpoints.KafkaProxy != "" {
				return profile.Endpoints.KafkaProxy, nil
			}
		}
	}

	// Fall back to global endpoints
	switch strings.ToLower(service) {
	case "maximus":
		return m.config.Endpoints.MAXIMUS, nil
	case "immune":
		return m.config.Endpoints.Immune, nil
	case "gateway":
		return m.config.Endpoints.Gateway, nil
	case "prometheus":
		return m.config.Endpoints.Prometheus, nil
	case "kafka_proxy", "kafka-proxy":
		return m.config.Endpoints.KafkaProxy, nil
	default:
		return "", fmt.Errorf("unknown service: %s", service)
	}
}

// getDefaultConfig returns default configuration
func getDefaultConfig() *Config {
	home, _ := os.UserHomeDir()

	return &Config{
		CurrentProfile: "default",
		Profiles: map[string]Profile{
			"default": {
				Name:        "default",
				Description: "Default profile",
				Endpoints: EndpointsConfig{
					MAXIMUS:    "localhost:50051",
					Immune:     "localhost:50052",
					Gateway:    "http://localhost:8080",
					Prometheus: "http://localhost:9090",
					KafkaProxy: "localhost:50053",
				},
				Auth: AuthConfig{
					Method:    "jwt",
					TokenFile: filepath.Join(home, ".vcli", "token"),
				},
			},
		},
		Global: GlobalConfig{
			Debug:        false,
			Offline:      false,
			Telemetry:    true,
			OutputFormat: "table",
			ColorOutput:  true,
		},
		Endpoints: EndpointsConfig{
			MAXIMUS:    "localhost:50051",
			Immune:     "localhost:50052",
			Gateway:    "http://localhost:8080",
			Prometheus: "http://localhost:9090",
			KafkaProxy: "localhost:50053",
		},
		Cache: CacheConfig{
			Enabled:    true,
			Path:       filepath.Join(home, ".vcli", "cache"),
			MaxSizeMB:  500,
			DefaultTTL: "5m",
		},
		Plugins: PluginConfig{
			Enabled:  true,
			Path:     filepath.Join(home, ".vcli", "plugins"),
			Autoload: []string{},
			Disabled: []string{},
		},
	}
}
