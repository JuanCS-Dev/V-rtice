package config

import (
	"fmt"
	"os"
	"strings"

	vcliFs "github.com/verticedev/vcli-go/internal/fs"
	"gopkg.in/yaml.v3"
)

// Loader handles loading configuration from various sources
type Loader struct {
	config *Config
}

// NewLoader creates a new configuration loader
func NewLoader() *Loader {
	return &Loader{
		config: DefaultConfig(),
	}
}

// Load loads configuration from all sources in precedence order
func (l *Loader) Load() (*Config, error) {
	// Start with defaults
	cfg := DefaultConfig()

	// Load user config (~/.vcli/config.yaml)
	if userCfg, err := l.loadUserConfig(); err == nil {
		cfg = l.merge(cfg, userCfg)
	}

	// Load project config (VCLI.md)
	if projectCfg, err := l.loadProjectConfig(); err == nil {
		cfg = l.merge(cfg, projectCfg)
	}

	// Load from environment variables
	cfg = l.loadFromEnv(cfg)

	// Validate
	if err := l.validate(cfg); err != nil {
		return nil, fmt.Errorf("config validation failed: %w", err)
	}

	l.config = cfg
	return cfg, nil
}

// loadUserConfig loads ~/.vcli/config.yaml
func (l *Loader) loadUserConfig() (*Config, error) {
	// Use fs helper for proper error handling
	configPath, err := vcliFs.GetVCLIConfigFile()
	if err != nil {
		return nil, fmt.Errorf("failed to get config file path: %w", err)
	}
	return l.loadYAMLFile(configPath)
}

// loadProjectConfig loads VCLI.md from project root
func (l *Loader) loadProjectConfig() (*Config, error) {
	// Try ./VCLI.md first
	if cfg, err := l.loadVCLIMD("VCLI.md"); err == nil {
		return cfg, nil
	}

	// Try ./.vcli/VCLI.md
	if cfg, err := l.loadVCLIMD(".vcli/VCLI.md"); err == nil {
		return cfg, nil
	}

	return nil, fmt.Errorf("no VCLI.md found")
}

// loadVCLIMD loads a VCLI.md file with YAML frontmatter
func (l *Loader) loadVCLIMD(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	// Extract YAML frontmatter
	content := string(data)
	if !strings.HasPrefix(content, "---\n") {
		return nil, fmt.Errorf("VCLI.md missing YAML frontmatter")
	}

	// Find end of frontmatter
	parts := strings.SplitN(content[4:], "\n---\n", 2)
	if len(parts) < 1 {
		return nil, fmt.Errorf("VCLI.md invalid frontmatter")
	}

	yamlContent := parts[0]

	var cfg Config
	if err := yaml.Unmarshal([]byte(yamlContent), &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse VCLI.md frontmatter: %w", err)
	}

	return &cfg, nil
}

// loadYAMLFile loads a YAML configuration file
func (l *Loader) loadYAMLFile(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse %s: %w", path, err)
	}

	return &cfg, nil
}

// loadFromEnv loads configuration from environment variables
func (l *Loader) loadFromEnv(cfg *Config) *Config {
	// Auth token
	if token := os.Getenv("VCLI_TOKEN"); token != "" {
		cfg.Auth.Token = token
	}

	// API timeout
	if timeout := os.Getenv("VCLI_TIMEOUT"); timeout != "" {
		// Parse timeout (e.g., "30s", "1m")
		// For now, keep existing value
	}

	// Endpoints - check for service-specific env vars
	for service := range cfg.Endpoints {
		envVar := "VCLI_" + strings.ToUpper(service) + "_ENDPOINT"
		if endpoint := os.Getenv(envVar); endpoint != "" {
			cfg.Endpoints[service] = endpoint
		}
	}

	// Output format
	if format := os.Getenv("VCLI_OUTPUT_FORMAT"); format != "" {
		cfg.Output.Format = format
	}

	if color := os.Getenv("VCLI_OUTPUT_COLOR"); color != "" {
		cfg.Output.Color = color
	}

	if verbose := os.Getenv("VCLI_VERBOSE"); verbose == "true" || verbose == "1" {
		cfg.Output.Verbose = true
	}

	return cfg
}

// merge merges two configs, with the second taking precedence
func (l *Loader) merge(base, override *Config) *Config {
	result := *base

	// Merge API config
	if override.API.Timeout > 0 {
		result.API.Timeout = override.API.Timeout
	}
	if override.API.Retry > 0 {
		result.API.Retry = override.API.Retry
	}

	// Merge endpoints
	if result.Endpoints == nil {
		result.Endpoints = make(map[string]string)
	}
	for k, v := range override.Endpoints {
		if v != "" {
			result.Endpoints[k] = v
		}
	}

	// Merge auth
	if override.Auth.Token != "" {
		result.Auth.Token = override.Auth.Token
	}
	if override.Auth.Method != "" {
		result.Auth.Method = override.Auth.Method
	}

	// Merge output
	if override.Output.Format != "" {
		result.Output.Format = override.Output.Format
	}
	if override.Output.Color != "" {
		result.Output.Color = override.Output.Color
	}
	if override.Output.Verbose {
		result.Output.Verbose = override.Output.Verbose
	}

	// Merge profiles
	if result.Profiles == nil {
		result.Profiles = make(map[string]ProfileConfig)
	}
	for k, v := range override.Profiles {
		result.Profiles[k] = v
	}

	return &result
}

// validate validates the configuration
func (l *Loader) validate(cfg *Config) error {
	// Validate API timeout
	if cfg.API.Timeout <= 0 {
		return fmt.Errorf("api.timeout must be positive")
	}

	// Validate retry count
	if cfg.API.Retry < 0 {
		return fmt.Errorf("api.retry must be non-negative")
	}

	// Validate output format
	validFormats := map[string]bool{"json": true, "yaml": true, "table": true, "text": true}
	if !validFormats[cfg.Output.Format] {
		return fmt.Errorf("invalid output.format: %s (must be json, yaml, table, or text)", cfg.Output.Format)
	}

	// Validate color setting
	validColors := map[string]bool{"auto": true, "always": true, "never": true}
	if !validColors[cfg.Output.Color] {
		return fmt.Errorf("invalid output.color: %s (must be auto, always, or never)", cfg.Output.Color)
	}

	return nil
}

// GetEndpoint returns the endpoint for a service
func (l *Loader) GetEndpoint(service string) string {
	if l.config == nil {
		return ""
	}
	return l.config.Endpoints[service]
}
