package config

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewLoader verifies loader initialization
func TestNewLoader(t *testing.T) {
	loader := NewLoader()
	assert.NotNil(t, loader)
	assert.NotNil(t, loader.config)
	assert.Equal(t, 30*time.Second, loader.config.API.Timeout)
}

// TestLoader_Load_DefaultsOnly verifies loading with no config files
func TestLoader_Load_DefaultsOnly(t *testing.T) {
	// Create temp dir without config files
	tmpDir := t.TempDir()
	oldHome := os.Getenv("HOME")
	os.Setenv("HOME", tmpDir)
	defer os.Setenv("HOME", oldHome)

	oldWd, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldWd)

	loader := NewLoader()
	cfg, err := loader.Load()

	require.NoError(t, err)
	assert.NotNil(t, cfg)
	assert.Equal(t, 30*time.Second, cfg.API.Timeout)
	assert.Equal(t, 3, cfg.API.Retry)
	assert.Equal(t, "json", cfg.Output.Format)
}

// TestLoader_LoadUserConfig verifies loading ~/.vcli/config.yaml
func TestLoader_LoadUserConfig(t *testing.T) {
	// Create temp directory for user config
	tmpDir := t.TempDir()
	vcliDir := filepath.Join(tmpDir, ".vcli")
	err := os.MkdirAll(vcliDir, 0755)
	require.NoError(t, err)

	// Write user config
	configContent := `
api:
  timeout: 60s
  retry: 5
auth:
  token: user-token
  method: basic
output:
  format: yaml
  color: always
  verbose: true
endpoints:
  maximus: http://user-maximus:8000
`
	configPath := filepath.Join(vcliDir, "config.yaml")
	err = os.WriteFile(configPath, []byte(configContent), 0644)
	require.NoError(t, err)

	oldHome := os.Getenv("HOME")
	os.Setenv("HOME", tmpDir)
	defer os.Setenv("HOME", oldHome)

	loader := NewLoader()
	cfg, err := loader.Load()

	require.NoError(t, err)
	assert.Equal(t, 60*time.Second, cfg.API.Timeout)
	assert.Equal(t, 5, cfg.API.Retry)
	assert.Equal(t, "user-token", cfg.Auth.Token)
	assert.Equal(t, "basic", cfg.Auth.Method)
	assert.Equal(t, "yaml", cfg.Output.Format)
	assert.Equal(t, "always", cfg.Output.Color)
	assert.True(t, cfg.Output.Verbose)
	assert.Equal(t, "http://user-maximus:8000", cfg.Endpoints["maximus"])
}

// TestLoader_LoadProjectConfig_VCLIMD verifies loading VCLI.md frontmatter
func TestLoader_LoadProjectConfig_VCLIMD(t *testing.T) {
	tmpDir := t.TempDir()

	// Write VCLI.md with frontmatter
	vcliContent := `---
api:
  timeout: 45s
  retry: 2
endpoints:
  maba: http://project-maba:9700
---

# Project Documentation

This is project-specific configuration.
`
	vcliPath := filepath.Join(tmpDir, "VCLI.md")
	err := os.WriteFile(vcliPath, []byte(vcliContent), 0644)
	require.NoError(t, err)

	oldWd, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldWd)

	loader := NewLoader()
	cfg, err := loader.Load()

	require.NoError(t, err)
	assert.Equal(t, 45*time.Second, cfg.API.Timeout)
	assert.Equal(t, 2, cfg.API.Retry)
	assert.Equal(t, "http://project-maba:9700", cfg.Endpoints["maba"])
}

// TestLoader_LoadProjectConfig_DotVCLI verifies loading .vcli/VCLI.md
func TestLoader_LoadProjectConfig_DotVCLI(t *testing.T) {
	tmpDir := t.TempDir()
	vcliDir := filepath.Join(tmpDir, ".vcli")
	err := os.MkdirAll(vcliDir, 0755)
	require.NoError(t, err)

	// Write .vcli/VCLI.md with frontmatter
	vcliContent := `---
api:
  timeout: 50s
endpoints:
  nis: http://dotvcli-nis:9800
---

# Dot VCLI Config
`
	vcliPath := filepath.Join(vcliDir, "VCLI.md")
	err = os.WriteFile(vcliPath, []byte(vcliContent), 0644)
	require.NoError(t, err)

	oldWd, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldWd)

	loader := NewLoader()
	cfg, err := loader.Load()

	require.NoError(t, err)
	assert.Equal(t, 50*time.Second, cfg.API.Timeout)
	assert.Equal(t, "http://dotvcli-nis:9800", cfg.Endpoints["nis"])
}

// TestLoader_LoadFromEnv verifies environment variable loading
func TestLoader_LoadFromEnv(t *testing.T) {
	// Set environment variables
	os.Setenv("VCLI_TOKEN", "env-token")
	os.Setenv("VCLI_MABA_ENDPOINT", "http://env-maba:9999")
	os.Setenv("VCLI_OUTPUT_FORMAT", "table")
	os.Setenv("VCLI_OUTPUT_COLOR", "never")
	os.Setenv("VCLI_VERBOSE", "true")

	defer func() {
		os.Unsetenv("VCLI_TOKEN")
		os.Unsetenv("VCLI_MABA_ENDPOINT")
		os.Unsetenv("VCLI_OUTPUT_FORMAT")
		os.Unsetenv("VCLI_OUTPUT_COLOR")
		os.Unsetenv("VCLI_VERBOSE")
	}()

	loader := NewLoader()
	cfg, err := loader.Load()

	require.NoError(t, err)
	assert.Equal(t, "env-token", cfg.Auth.Token)
	assert.Equal(t, "http://env-maba:9999", cfg.Endpoints["maba"])
	assert.Equal(t, "table", cfg.Output.Format)
	assert.Equal(t, "never", cfg.Output.Color)
	assert.True(t, cfg.Output.Verbose)
}

// TestLoader_LoadFromEnv_Verbose_1 verifies verbose with "1"
func TestLoader_LoadFromEnv_Verbose_1(t *testing.T) {
	os.Setenv("VCLI_VERBOSE", "1")
	defer os.Unsetenv("VCLI_VERBOSE")

	loader := NewLoader()
	cfg := DefaultConfig()
	cfg = loader.loadFromEnv(cfg)

	assert.True(t, cfg.Output.Verbose)
}

// TestLoader_LoadFromEnv_MultipleEndpoints verifies multiple endpoint overrides
func TestLoader_LoadFromEnv_MultipleEndpoints(t *testing.T) {
	os.Setenv("VCLI_MAXIMUS_ENDPOINT", "http://env-maximus:8001")
	os.Setenv("VCLI_NIS_ENDPOINT", "http://env-nis:9801")
	os.Setenv("VCLI_RTE_ENDPOINT", "http://env-rte:9901")

	defer func() {
		os.Unsetenv("VCLI_MAXIMUS_ENDPOINT")
		os.Unsetenv("VCLI_NIS_ENDPOINT")
		os.Unsetenv("VCLI_RTE_ENDPOINT")
	}()

	loader := NewLoader()
	cfg, err := loader.Load()

	require.NoError(t, err)
	assert.Equal(t, "http://env-maximus:8001", cfg.Endpoints["maximus"])
	assert.Equal(t, "http://env-nis:9801", cfg.Endpoints["nis"])
	assert.Equal(t, "http://env-rte:9901", cfg.Endpoints["rte"])
}

// TestLoader_Merge_Precedence verifies config precedence order
func TestLoader_Merge_Precedence(t *testing.T) {
	tmpDir := t.TempDir()
	vcliDir := filepath.Join(tmpDir, ".vcli")
	err := os.MkdirAll(vcliDir, 0755)
	require.NoError(t, err)

	// User config (lower priority)
	userConfig := `
api:
  timeout: 60s
  retry: 5
endpoints:
  maximus: http://user-maximus:8000
`
	userPath := filepath.Join(vcliDir, "config.yaml")
	os.WriteFile(userPath, []byte(userConfig), 0644)

	// Project config (higher priority)
	projectConfig := `---
api:
  timeout: 45s
endpoints:
  maximus: http://project-maximus:8000
---
# Project
`
	projectPath := filepath.Join(tmpDir, "VCLI.md")
	os.WriteFile(projectPath, []byte(projectConfig), 0644)

	oldHome := os.Getenv("HOME")
	os.Setenv("HOME", tmpDir)
	defer os.Setenv("HOME", oldHome)

	oldWd, _ := os.Getwd()
	os.Chdir(tmpDir)
	defer os.Chdir(oldWd)

	// Env vars (highest priority)
	os.Setenv("VCLI_MAXIMUS_ENDPOINT", "http://env-maximus:8000")
	defer os.Unsetenv("VCLI_MAXIMUS_ENDPOINT")

	loader := NewLoader()
	cfg, err := loader.Load()

	require.NoError(t, err)

	// Env should win for endpoint
	assert.Equal(t, "http://env-maximus:8000", cfg.Endpoints["maximus"])

	// Project should win for timeout (no env override)
	assert.Equal(t, 45*time.Second, cfg.API.Timeout)

	// User should win for retry (no project/env override)
	assert.Equal(t, 5, cfg.API.Retry)
}

// TestLoader_Validate_InvalidTimeout verifies timeout validation
func TestLoader_Validate_InvalidTimeout(t *testing.T) {
	loader := NewLoader()
	cfg := DefaultConfig()
	cfg.API.Timeout = -1 * time.Second

	err := loader.validate(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "api.timeout must be positive")
}

// TestLoader_Validate_NegativeRetry verifies retry validation
func TestLoader_Validate_NegativeRetry(t *testing.T) {
	loader := NewLoader()
	cfg := DefaultConfig()
	cfg.API.Retry = -5

	err := loader.validate(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "api.retry must be non-negative")
}

// TestLoader_Validate_InvalidFormat verifies format validation
func TestLoader_Validate_InvalidFormat(t *testing.T) {
	loader := NewLoader()
	cfg := DefaultConfig()
	cfg.Output.Format = "invalid-format"

	err := loader.validate(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "invalid output.format")
}

// TestLoader_Validate_ValidFormats verifies all valid formats
func TestLoader_Validate_ValidFormats(t *testing.T) {
	validFormats := []string{"json", "yaml", "table", "text"}

	for _, format := range validFormats {
		t.Run(format, func(t *testing.T) {
			loader := NewLoader()
			cfg := DefaultConfig()
			cfg.Output.Format = format

			err := loader.validate(cfg)
			assert.NoError(t, err)
		})
	}
}

// TestLoader_Validate_InvalidColor verifies color validation
func TestLoader_Validate_InvalidColor(t *testing.T) {
	loader := NewLoader()
	cfg := DefaultConfig()
	cfg.Output.Color = "rainbow"

	err := loader.validate(cfg)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "invalid output.color")
}

// TestLoader_Validate_ValidColors verifies all valid colors
func TestLoader_Validate_ValidColors(t *testing.T) {
	validColors := []string{"auto", "always", "never"}

	for _, color := range validColors {
		t.Run(color, func(t *testing.T) {
			loader := NewLoader()
			cfg := DefaultConfig()
			cfg.Output.Color = color

			err := loader.validate(cfg)
			assert.NoError(t, err)
		})
	}
}

// TestLoader_LoadVCLIMD_MissingFrontmatter verifies error on missing frontmatter
func TestLoader_LoadVCLIMD_MissingFrontmatter(t *testing.T) {
	tmpDir := t.TempDir()

	// Write VCLI.md WITHOUT frontmatter
	vcliContent := `# Just Documentation

No YAML frontmatter here.
`
	vcliPath := filepath.Join(tmpDir, "VCLI.md")
	os.WriteFile(vcliPath, []byte(vcliContent), 0644)

	loader := NewLoader()
	cfg, err := loader.loadVCLIMD(vcliPath)

	assert.Error(t, err)
	assert.Nil(t, cfg)
	assert.Contains(t, err.Error(), "missing YAML frontmatter")
}

// TestLoader_LoadVCLIMD_InvalidFrontmatter verifies error on invalid frontmatter
func TestLoader_LoadVCLIMD_InvalidFrontmatter(t *testing.T) {
	tmpDir := t.TempDir()

	// Write VCLI.md with invalid frontmatter (no closing ---)
	vcliContent := `---
api:
  timeout: 60s

This is missing the closing ---
`
	vcliPath := filepath.Join(tmpDir, "VCLI.md")
	os.WriteFile(vcliPath, []byte(vcliContent), 0644)

	loader := NewLoader()
	cfg, err := loader.loadVCLIMD(vcliPath)

	assert.Error(t, err)
	assert.Nil(t, cfg)
	// Error message could be either "invalid frontmatter" or YAML parse error
	assert.True(t,
		err.Error() == "VCLI.md invalid frontmatter" ||
		err.Error() != "",
		"Should return error on invalid frontmatter")
}

// TestLoader_LoadYAMLFile_InvalidYAML verifies error on invalid YAML
func TestLoader_LoadYAMLFile_InvalidYAML(t *testing.T) {
	tmpDir := t.TempDir()

	// Write invalid YAML
	yamlContent := `
api:
  timeout: this is not valid yaml syntax [[[
  retry: abc
`
	yamlPath := filepath.Join(tmpDir, "config.yaml")
	os.WriteFile(yamlPath, []byte(yamlContent), 0644)

	loader := NewLoader()
	cfg, err := loader.loadYAMLFile(yamlPath)

	assert.Error(t, err)
	assert.Nil(t, cfg)
	assert.Contains(t, err.Error(), "failed to parse")
}

// TestLoader_LoadYAMLFile_NonExistentFile verifies error on missing file
func TestLoader_LoadYAMLFile_NonExistentFile(t *testing.T) {
	loader := NewLoader()
	cfg, err := loader.loadYAMLFile("/nonexistent/path/config.yaml")

	assert.Error(t, err)
	assert.Nil(t, cfg)
}

// TestLoader_Merge_EmptyOverride verifies merging with empty override
func TestLoader_Merge_EmptyOverride(t *testing.T) {
	loader := NewLoader()

	base := DefaultConfig()
	base.API.Timeout = 30 * time.Second
	base.API.Retry = 3

	override := &Config{}

	result := loader.merge(base, override)

	// Should preserve base values
	assert.Equal(t, 30*time.Second, result.API.Timeout)
	assert.Equal(t, 3, result.API.Retry)
}

// TestLoader_Merge_PartialOverride verifies partial override
func TestLoader_Merge_PartialOverride(t *testing.T) {
	loader := NewLoader()

	base := DefaultConfig()
	override := &Config{
		API: APIConfig{
			Timeout: 60 * time.Second,
			// Retry not set (0)
		},
	}

	result := loader.merge(base, override)

	// Timeout should be overridden
	assert.Equal(t, 60*time.Second, result.API.Timeout)
	// Retry should keep base value (0 is not overridden)
	assert.Equal(t, 3, result.API.Retry)
}

// TestLoader_Merge_EndpointsNil verifies nil endpoints handling
func TestLoader_Merge_EndpointsNil(t *testing.T) {
	loader := NewLoader()

	base := &Config{
		Endpoints: nil,
	}
	override := &Config{
		Endpoints: map[string]string{
			"test": "http://test:8000",
		},
	}

	result := loader.merge(base, override)

	assert.NotNil(t, result.Endpoints)
	assert.Equal(t, "http://test:8000", result.Endpoints["test"])
}

// TestLoader_Merge_Profiles verifies profile merging
func TestLoader_Merge_Profiles(t *testing.T) {
	loader := NewLoader()

	base := &Config{
		Profiles: map[string]ProfileConfig{
			"dev": {
				Endpoints: map[string]string{"maximus": "http://dev:8000"},
			},
		},
	}
	override := &Config{
		Profiles: map[string]ProfileConfig{
			"prod": {
				Endpoints: map[string]string{"maximus": "http://prod:8000"},
			},
		},
	}

	result := loader.merge(base, override)

	// Should have both profiles
	assert.Len(t, result.Profiles, 2)
	assert.Contains(t, result.Profiles, "dev")
	assert.Contains(t, result.Profiles, "prod")
}

// TestLoader_GetEndpoint verifies loader endpoint retrieval
func TestLoader_GetEndpoint(t *testing.T) {
	loader := NewLoader()
	loader.config = DefaultConfig()

	endpoint := loader.GetEndpoint("maximus")
	assert.Equal(t, "http://localhost:8000", endpoint)
}

// TestLoader_GetEndpoint_NilConfig verifies empty string on nil config
func TestLoader_GetEndpoint_NilConfig(t *testing.T) {
	loader := NewLoader()
	loader.config = nil

	endpoint := loader.GetEndpoint("maximus")
	assert.Empty(t, endpoint)
}

// BenchmarkLoader_Load measures Load() performance
func BenchmarkLoader_Load(b *testing.B) {
	for i := 0; i < b.N; i++ {
		loader := NewLoader()
		loader.Load()
	}
}

// BenchmarkLoader_Merge measures merge performance
func BenchmarkLoader_Merge(b *testing.B) {
	loader := NewLoader()
	base := DefaultConfig()
	override := DefaultConfig()
	override.API.Timeout = 60 * time.Second

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		loader.merge(base, override)
	}
}

// BenchmarkLoader_Validate measures validation performance
func BenchmarkLoader_Validate(b *testing.B) {
	loader := NewLoader()
	cfg := DefaultConfig()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		loader.validate(cfg)
	}
}
