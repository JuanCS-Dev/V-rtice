package config

import (
	"fmt"
	"sync"
)

var (
	globalConfig *Config
	globalMutex  sync.RWMutex
	loaded       bool
)

// Get returns the global configuration, loading it if necessary
func Get() (*Config, error) {
	globalMutex.RLock()
	if loaded && globalConfig != nil {
		defer globalMutex.RUnlock()
		return globalConfig, nil
	}
	globalMutex.RUnlock()

	globalMutex.Lock()
	defer globalMutex.Unlock()

	// Double-check after acquiring write lock
	if loaded && globalConfig != nil {
		return globalConfig, nil
	}

	loader := NewLoader()
	cfg, err := loader.Load()
	if err != nil {
		// If loading fails, use defaults
		cfg = DefaultConfig()
	}

	globalConfig = cfg
	loaded = true
	return globalConfig, nil
}

// GetEndpoint returns the endpoint for a service from global config
func GetEndpoint(service string) string {
	cfg, err := Get()
	if err != nil {
		// Fallback to default
		return DefaultConfig().Endpoints[service]
	}

	if endpoint, ok := cfg.Endpoints[service]; ok && endpoint != "" {
		return endpoint
	}

	// Fallback to default
	return DefaultConfig().Endpoints[service]
}

// Set sets the global configuration (useful for testing)
func Set(cfg *Config) {
	globalMutex.Lock()
	defer globalMutex.Unlock()
	globalConfig = cfg
	loaded = true
}

// Reset resets the global configuration
func Reset() {
	globalMutex.Lock()
	defer globalMutex.Unlock()
	globalConfig = nil
	loaded = false
}

// OverrideEndpoint overrides an endpoint at runtime (from flags)
func OverrideEndpoint(service, endpoint string) error {
	globalMutex.Lock()
	defer globalMutex.Unlock()

	if globalConfig == nil {
		globalConfig = DefaultConfig()
	}

	if globalConfig.Endpoints == nil {
		globalConfig.Endpoints = make(map[string]string)
	}

	globalConfig.Endpoints[service] = endpoint
	return nil
}

// GetWithSource returns the effective config value and its source
func GetWithSource(key string) (interface{}, Source, error) {
	cfg, err := Get()
	if err != nil {
		return nil, SourceDefault, err
	}

	// Parse key (e.g., "endpoints.maximus", "api.timeout")
	// For now, return basic implementation
	switch key {
	case "api.timeout":
		return cfg.API.Timeout, SourceDefault, nil
	case "api.retry":
		return cfg.API.Retry, SourceDefault, nil
	case "auth.token":
		return cfg.Auth.Token, SourceDefault, nil
	case "output.format":
		return cfg.Output.Format, SourceDefault, nil
	default:
		return nil, SourceDefault, fmt.Errorf("unknown config key: %s", key)
	}
}
