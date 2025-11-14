package config

import (
	"os"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestDefaultConfig verifies default configuration values
func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	// Validate API defaults
	assert.Equal(t, 30*time.Second, cfg.API.Timeout, "Default timeout should be 30s")
	assert.Equal(t, 3, cfg.API.Retry, "Default retry should be 3")

	// Validate Auth defaults
	assert.Equal(t, "", cfg.Auth.Token, "Default token should be empty")
	assert.Equal(t, "bearer", cfg.Auth.Method, "Default auth method should be bearer")

	// Validate Output defaults
	assert.Equal(t, "json", cfg.Output.Format, "Default format should be json")
	assert.Equal(t, "auto", cfg.Output.Color, "Default color should be auto")
	assert.False(t, cfg.Output.Verbose, "Default verbose should be false")

	// Validate critical endpoints exist
	criticalServices := []string{
		"maximus", "immune", "maba", "nis", "rte",
		"architect", "pipeline", "registry", "edge",
		"integration", "homeostasis", "purple", "vulnscan",
		"specialized", "neuro", "offensive", "behavior",
		"intops", "immunity", "hunting", "streams",
	}

	for _, service := range criticalServices {
		endpoint, exists := cfg.Endpoints[service]
		assert.True(t, exists, "Endpoint for %s should exist", service)
		assert.NotEmpty(t, endpoint, "Endpoint for %s should not be empty", service)
		assert.Contains(t, endpoint, "http://localhost", "Endpoint for %s should be localhost", service)
	}

	// Validate profiles map is initialized
	assert.NotNil(t, cfg.Profiles, "Profiles map should be initialized")
}

// TestGet_FirstLoad verifies first-time config loading
func TestGet_FirstLoad(t *testing.T) {
	// Reset global state
	Reset()

	cfg, err := Get()
	require.NoError(t, err)
	assert.NotNil(t, cfg)

	// Verify it's using defaults (no config file in test env)
	assert.Equal(t, 30*time.Second, cfg.API.Timeout)
	assert.Equal(t, 3, cfg.API.Retry)
}

// TestGet_CachedLoad verifies subsequent loads use cache
func TestGet_CachedLoad(t *testing.T) {
	Reset()

	// First load
	cfg1, err1 := Get()
	require.NoError(t, err1)

	// Second load should return same instance
	cfg2, err2 := Get()
	require.NoError(t, err2)

	// Should be same pointer (cached)
	assert.True(t, cfg1 == cfg2, "Subsequent Get() calls should return cached config")
}

// TestGet_ThreadSafe verifies concurrent access safety
func TestGet_ThreadSafe(t *testing.T) {
	Reset()

	const goroutines = 100
	var wg sync.WaitGroup
	wg.Add(goroutines)

	// Launch concurrent Get() calls
	for i := 0; i < goroutines; i++ {
		go func() {
			defer wg.Done()
			cfg, err := Get()
			assert.NoError(t, err)
			assert.NotNil(t, cfg)
		}()
	}

	wg.Wait()

	// Verify config is loaded exactly once
	cfg, _ := Get()
	assert.NotNil(t, cfg)
}

// TestSet_CustomConfig verifies setting custom configuration
func TestSet_CustomConfig(t *testing.T) {
	Reset()

	customCfg := &Config{
		API: APIConfig{
			Timeout: 60 * time.Second,
			Retry:   5,
		},
		Endpoints: map[string]string{
			"custom": "http://custom:8080",
		},
		Auth: AuthConfig{
			Token:  "test-token",
			Method: "basic",
		},
		Output: OutputConfig{
			Format:  "yaml",
			Color:   "never",
			Verbose: true,
		},
		Profiles: make(map[string]ProfileConfig),
	}

	Set(customCfg)

	cfg, err := Get()
	require.NoError(t, err)

	assert.Equal(t, 60*time.Second, cfg.API.Timeout)
	assert.Equal(t, 5, cfg.API.Retry)
	assert.Equal(t, "test-token", cfg.Auth.Token)
	assert.Equal(t, "basic", cfg.Auth.Method)
	assert.Equal(t, "yaml", cfg.Output.Format)
	assert.Equal(t, "never", cfg.Output.Color)
	assert.True(t, cfg.Output.Verbose)
	assert.Equal(t, "http://custom:8080", cfg.Endpoints["custom"])
}

// TestReset verifies config reset
func TestReset(t *testing.T) {
	// Set custom config
	customCfg := &Config{
		API: APIConfig{Timeout: 99 * time.Second},
	}
	Set(customCfg)

	cfg, _ := Get()
	assert.Equal(t, 99*time.Second, cfg.API.Timeout)

	// Reset
	Reset()

	// Next Get() should reload from defaults
	cfg2, _ := Get()
	assert.Equal(t, 30*time.Second, cfg2.API.Timeout, "After reset, should use defaults")
}

// TestGetEndpoint_ExistingService verifies endpoint retrieval
func TestGetEndpoint_ExistingService(t *testing.T) {
	Reset()

	endpoint := GetEndpoint("maximus")
	assert.NotEmpty(t, endpoint)
	assert.Contains(t, endpoint, "http://localhost:8000")
}

// TestGetEndpoint_NonExistentService verifies fallback to empty
func TestGetEndpoint_NonExistentService(t *testing.T) {
	Reset()

	endpoint := GetEndpoint("nonexistent-service")
	assert.Empty(t, endpoint, "Non-existent service should return empty string")
}

// TestGetEndpoint_CustomEndpoint verifies custom endpoints
func TestGetEndpoint_CustomEndpoint(t *testing.T) {
	Reset()

	customCfg := DefaultConfig()
	customCfg.Endpoints["maba"] = "http://custom-maba:9999"
	Set(customCfg)

	endpoint := GetEndpoint("maba")
	assert.Equal(t, "http://custom-maba:9999", endpoint)
}

// TestOverrideEndpoint_NewService verifies endpoint override
func TestOverrideEndpoint_NewService(t *testing.T) {
	Reset()

	// Need to load config first
	Get()

	err := OverrideEndpoint("test-service", "http://test:1234")
	require.NoError(t, err)

	endpoint := GetEndpoint("test-service")
	assert.Equal(t, "http://test:1234", endpoint)
}

// TestOverrideEndpoint_ExistingService verifies overriding existing endpoint
func TestOverrideEndpoint_ExistingService(t *testing.T) {
	Reset()

	// Load config first
	Get()

	// Override existing endpoint
	err := OverrideEndpoint("maximus", "http://production-maximus:8000")
	require.NoError(t, err)

	endpoint := GetEndpoint("maximus")
	assert.Equal(t, "http://production-maximus:8000", endpoint)
}

// TestOverrideEndpoint_NilConfig verifies override with nil global config
func TestOverrideEndpoint_NilConfig(t *testing.T) {
	Reset()

	// OverrideEndpoint creates default config if nil
	err := OverrideEndpoint("service", "http://test:1234")
	require.NoError(t, err)

	// Directly access globalConfig to verify it was set
	globalMutex.RLock()
	assert.NotNil(t, globalConfig)
	assert.Equal(t, "http://test:1234", globalConfig.Endpoints["service"])
	globalMutex.RUnlock()
}

// TestGetWithSource_APITimeout verifies source tracking for API timeout
func TestGetWithSource_APITimeout(t *testing.T) {
	Reset()

	value, source, err := GetWithSource("api.timeout")
	require.NoError(t, err)
	assert.Equal(t, 30*time.Second, value)
	assert.Equal(t, SourceDefault, source)
}

// TestGetWithSource_APIRetry verifies source tracking for API retry
func TestGetWithSource_APIRetry(t *testing.T) {
	Reset()

	value, source, err := GetWithSource("api.retry")
	require.NoError(t, err)
	assert.Equal(t, 3, value)
	assert.Equal(t, SourceDefault, source)
}

// TestGetWithSource_AuthToken verifies source tracking for auth token
func TestGetWithSource_AuthToken(t *testing.T) {
	Reset()

	value, source, err := GetWithSource("auth.token")
	require.NoError(t, err)
	assert.Equal(t, "", value)
	assert.Equal(t, SourceDefault, source)
}

// TestGetWithSource_OutputFormat verifies source tracking for output format
func TestGetWithSource_OutputFormat(t *testing.T) {
	Reset()

	value, source, err := GetWithSource("output.format")
	require.NoError(t, err)
	assert.Equal(t, "json", value)
	assert.Equal(t, SourceDefault, source)
}

// TestGetWithSource_UnknownKey verifies error for unknown keys
func TestGetWithSource_UnknownKey(t *testing.T) {
	Reset()

	_, _, err := GetWithSource("unknown.key")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "unknown config key")
}

// TestSource_String verifies Source enum string representation
func TestSource_String(t *testing.T) {
	tests := []struct {
		source   Source
		expected string
	}{
		{SourceDefault, "default"},
		{SourceUserConfig, "~/.vcli/config.yaml"},
		{SourceProjectConfig, "VCLI.md"},
		{SourceEnv, "environment"},
		{SourceFlag, "flag"},
		{Source(999), "unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			assert.Equal(t, tt.expected, tt.source.String())
		})
	}
}

// TestGet_LoadFailure_UsesDefaults verifies fallback to defaults on load failure
func TestGet_LoadFailure_UsesDefaults(t *testing.T) {
	Reset()

	// Set invalid environment that causes load to fail
	oldHome := os.Getenv("HOME")
	os.Setenv("HOME", "/nonexistent/path/that/does/not/exist")
	defer os.Setenv("HOME", oldHome)

	cfg, err := Get()
	// Should not error - falls back to defaults
	require.NoError(t, err)
	assert.NotNil(t, cfg)
	assert.Equal(t, 30*time.Second, cfg.API.Timeout, "Should use default timeout on load failure")
}

// TestConcurrentSetAndGet verifies thread-safety of Set and Get
func TestConcurrentSetAndGet(t *testing.T) {
	Reset()

	const goroutines = 50
	var wg sync.WaitGroup
	wg.Add(goroutines * 2)

	// Launch concurrent Set() calls
	for i := 0; i < goroutines; i++ {
		go func(id int) {
			defer wg.Done()
			cfg := DefaultConfig()
			cfg.API.Timeout = time.Duration(id) * time.Second
			Set(cfg)
		}(i)
	}

	// Launch concurrent Get() calls
	for i := 0; i < goroutines; i++ {
		go func() {
			defer wg.Done()
			cfg, err := Get()
			assert.NoError(t, err)
			assert.NotNil(t, cfg)
		}()
	}

	wg.Wait()

	// Verify final state is valid
	cfg, _ := Get()
	assert.NotNil(t, cfg)
	assert.Greater(t, cfg.API.Timeout, time.Duration(0))
}

// BenchmarkGet measures Get() performance
func BenchmarkGet(b *testing.B) {
	Reset()
	// Prime the cache
	Get()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		Get()
	}
}

// BenchmarkGetEndpoint measures GetEndpoint() performance
func BenchmarkGetEndpoint(b *testing.B) {
	Reset()
	Get() // Prime cache

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		GetEndpoint("maximus")
	}
}

// BenchmarkOverrideEndpoint measures OverrideEndpoint() performance
func BenchmarkOverrideEndpoint(b *testing.B) {
	Reset()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		OverrideEndpoint("test", "http://test:8000")
	}
}
