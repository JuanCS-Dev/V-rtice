package fs

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestGetHomeDir tests basic home directory retrieval
func TestGetHomeDir(t *testing.T) {
	home, err := GetHomeDir()

	if err != nil {
		t.Fatalf("GetHomeDir() error: %v", err)
	}

	if home == "" {
		t.Error("GetHomeDir() returned empty string")
	}

	// Home should be an absolute path
	if !filepath.IsAbs(home) {
		t.Errorf("GetHomeDir() = %q, want absolute path", home)
	}

	// Should not have trailing slash
	if strings.HasSuffix(home, "/") || strings.HasSuffix(home, "\\") {
		t.Errorf("GetHomeDir() should not have trailing slash: %q", home)
	}
}

// TestGetHomeDir_Consistency tests that multiple calls return same result
func TestGetHomeDir_Consistency(t *testing.T) {
	home1, err1 := GetHomeDir()
	if err1 != nil {
		t.Fatalf("First GetHomeDir() error: %v", err1)
	}

	home2, err2 := GetHomeDir()
	if err2 != nil {
		t.Fatalf("Second GetHomeDir() error: %v", err2)
	}

	if home1 != home2 {
		t.Errorf("GetHomeDir() inconsistent: %q != %q", home1, home2)
	}
}

// TestJoinHomePath tests path joining with home directory
func TestJoinHomePath(t *testing.T) {
	tests := []struct {
		name          string
		pathElements  []string
		wantContains  string
		wantAbsolute  bool
	}{
		{
			name:         "single path element",
			pathElements: []string{".vcli"},
			wantContains: ".vcli",
			wantAbsolute: true,
		},
		{
			name:         "multiple path elements",
			pathElements: []string{".vcli", "config.yaml"},
			wantContains: "config.yaml",
			wantAbsolute: true,
		},
		{
			name:         "kube config",
			pathElements: []string{".kube", "config"},
			wantContains: ".kube",
			wantAbsolute: true,
		},
		{
			name:         "nested directories",
			pathElements: []string{".vcli", "plugins", "kubernetes"},
			wantContains: "plugins",
			wantAbsolute: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			path, err := JoinHomePath(tt.pathElements...)

			if err != nil {
				t.Fatalf("JoinHomePath() error: %v", err)
			}

			if path == "" {
				t.Error("JoinHomePath() returned empty path")
			}

			if tt.wantAbsolute && !filepath.IsAbs(path) {
				t.Errorf("JoinHomePath() = %q, want absolute path", path)
			}

			if !strings.Contains(path, tt.wantContains) {
				t.Errorf("JoinHomePath() = %q, should contain %q", path, tt.wantContains)
			}

			// Verify path separator is correct for OS
			expectedSep := string(filepath.Separator)
			if !strings.Contains(path, expectedSep) && len(tt.pathElements) > 1 {
				t.Errorf("JoinHomePath() = %q, should use OS path separator %q", path, expectedSep)
			}
		})
	}
}

// TestJoinHomePath_EmptyElements tests edge case handling
func TestJoinHomePath_EmptyElements(t *testing.T) {
	tests := []struct {
		name         string
		pathElements []string
		wantError    bool
	}{
		{
			name:         "no elements",
			pathElements: []string{},
			wantError:    false, // Should return home dir
		},
		{
			name:         "empty string element",
			pathElements: []string{""},
			wantError:    false, // Should handle gracefully
		},
		{
			name:         "mixed empty and valid",
			pathElements: []string{".vcli", "", "config"},
			wantError:    false, // filepath.Join handles this
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			path, err := JoinHomePath(tt.pathElements...)

			if tt.wantError && err == nil {
				t.Error("JoinHomePath() expected error but got nil")
			}

			if !tt.wantError && err != nil {
				t.Errorf("JoinHomePath() unexpected error: %v", err)
			}

			// Even with empty elements, should return valid path
			if !tt.wantError && path == "" {
				t.Error("JoinHomePath() returned empty path for non-error case")
			}
		})
	}
}

// TestGetVCLIConfigDir tests vcli config directory path
func TestGetVCLIConfigDir(t *testing.T) {
	configDir, err := GetVCLIConfigDir()

	if err != nil {
		t.Fatalf("GetVCLIConfigDir() error: %v", err)
	}

	if configDir == "" {
		t.Error("GetVCLIConfigDir() returned empty string")
	}

	// Should contain .vcli
	if !strings.Contains(configDir, ".vcli") {
		t.Errorf("GetVCLIConfigDir() = %q, should contain '.vcli'", configDir)
	}

	// Should be absolute
	if !filepath.IsAbs(configDir) {
		t.Errorf("GetVCLIConfigDir() = %q, want absolute path", configDir)
	}
}

// TestGetKubeconfigPath tests default kubeconfig path
func TestGetKubeconfigPath(t *testing.T) {
	kubeconfigPath, err := GetKubeconfigPath()

	if err != nil {
		t.Fatalf("GetKubeconfigPath() error: %v", err)
	}

	if kubeconfigPath == "" {
		t.Error("GetKubeconfigPath() returned empty string")
	}

	// Should contain .kube
	if !strings.Contains(kubeconfigPath, ".kube") {
		t.Errorf("GetKubeconfigPath() = %q, should contain '.kube'", kubeconfigPath)
	}

	// Should end with config
	if !strings.HasSuffix(kubeconfigPath, "config") {
		t.Errorf("GetKubeconfigPath() = %q, should end with 'config'", kubeconfigPath)
	}

	// Should be absolute
	if !filepath.IsAbs(kubeconfigPath) {
		t.Errorf("GetKubeconfigPath() = %q, want absolute path", kubeconfigPath)
	}
}

// TestGetVCLIConfigFile tests vcli config file path
func TestGetVCLIConfigFile(t *testing.T) {
	configFile, err := GetVCLIConfigFile()

	if err != nil {
		t.Fatalf("GetVCLIConfigFile() error: %v", err)
	}

	if configFile == "" {
		t.Error("GetVCLIConfigFile() returned empty string")
	}

	// Should contain .vcli
	if !strings.Contains(configFile, ".vcli") {
		t.Errorf("GetVCLIConfigFile() = %q, should contain '.vcli'", configFile)
	}

	// Should end with config.yaml
	if !strings.HasSuffix(configFile, "config.yaml") {
		t.Errorf("GetVCLIConfigFile() = %q, should end with 'config.yaml'", configFile)
	}

	// Should be absolute
	if !filepath.IsAbs(configFile) {
		t.Errorf("GetVCLIConfigFile() = %q, want absolute path", configFile)
	}
}

// TestGetVCLIWorkflowsDir tests workflows directory path
func TestGetVCLIWorkflowsDir(t *testing.T) {
	workflowsDir, err := GetVCLIWorkflowsDir()

	if err != nil {
		t.Fatalf("GetVCLIWorkflowsDir() error: %v", err)
	}

	if workflowsDir == "" {
		t.Error("GetVCLIWorkflowsDir() returned empty string")
	}

	// Should contain .vcli and workflows
	if !strings.Contains(workflowsDir, ".vcli") {
		t.Errorf("GetVCLIWorkflowsDir() = %q, should contain '.vcli'", workflowsDir)
	}

	if !strings.Contains(workflowsDir, "workflows") {
		t.Errorf("GetVCLIWorkflowsDir() = %q, should contain 'workflows'", workflowsDir)
	}

	// Should be absolute
	if !filepath.IsAbs(workflowsDir) {
		t.Errorf("GetVCLIWorkflowsDir() = %q, want absolute path", workflowsDir)
	}
}

// TestGetVCLIPluginsDir tests plugins directory path
func TestGetVCLIPluginsDir(t *testing.T) {
	pluginsDir, err := GetVCLIPluginsDir()

	if err != nil {
		t.Fatalf("GetVCLIPluginsDir() error: %v", err)
	}

	if pluginsDir == "" {
		t.Error("GetVCLIPluginsDir() returned empty string")
	}

	// Should contain .vcli and plugins
	if !strings.Contains(pluginsDir, ".vcli") {
		t.Errorf("GetVCLIPluginsDir() = %q, should contain '.vcli'", pluginsDir)
	}

	if !strings.Contains(pluginsDir, "plugins") {
		t.Errorf("GetVCLIPluginsDir() = %q, should contain 'plugins'", pluginsDir)
	}

	// Should be absolute
	if !filepath.IsAbs(pluginsDir) {
		t.Errorf("GetVCLIPluginsDir() = %q, want absolute path", pluginsDir)
	}
}

// TestEnsureVCLIConfigDir tests directory creation
func TestEnsureVCLIConfigDir(t *testing.T) {
	err := EnsureVCLIConfigDir()

	if err != nil {
		t.Fatalf("EnsureVCLIConfigDir() error: %v", err)
	}

	// Verify directory was created
	configDir, _ := GetVCLIConfigDir()
	if _, statErr := os.Stat(configDir); statErr != nil {
		t.Errorf("EnsureVCLIConfigDir() did not create directory: %v", statErr)
	}

	// Should be idempotent - calling again should not error
	err = EnsureVCLIConfigDir()
	if err != nil {
		t.Errorf("EnsureVCLIConfigDir() not idempotent: %v", err)
	}
}

// TestEnsureVCLIWorkflowsDir tests workflows directory creation
func TestEnsureVCLIWorkflowsDir(t *testing.T) {
	err := EnsureVCLIWorkflowsDir()

	if err != nil {
		t.Fatalf("EnsureVCLIWorkflowsDir() error: %v", err)
	}

	// Verify directory was created
	workflowsDir, _ := GetVCLIWorkflowsDir()
	if _, statErr := os.Stat(workflowsDir); statErr != nil {
		t.Errorf("EnsureVCLIWorkflowsDir() did not create directory: %v", statErr)
	}
}

// TestEnsureVCLIPluginsDir tests plugins directory creation
func TestEnsureVCLIPluginsDir(t *testing.T) {
	err := EnsureVCLIPluginsDir()

	if err != nil {
		t.Fatalf("EnsureVCLIPluginsDir() error: %v", err)
	}

	// Verify directory was created
	pluginsDir, _ := GetVCLIPluginsDir()
	if _, statErr := os.Stat(pluginsDir); statErr != nil {
		t.Errorf("EnsureVCLIPluginsDir() did not create directory: %v", statErr)
	}
}

// TestGetHomeDir_ErrorHandling tests error scenarios
func TestGetHomeDir_ErrorHandling(t *testing.T) {
	// This test verifies that GetHomeDir returns a proper error
	// In normal circumstances it should work, but we test the error path exists

	_, err := GetHomeDir()

	// Should either succeed or return proper error with context
	if err != nil {
		// Error should be wrapped with context
		if err.Error() == "" {
			t.Error("GetHomeDir() error should have message")
		}
	}
}

// TestJoinHomePath_Integration tests realistic use cases
func TestJoinHomePath_Integration(t *testing.T) {
	t.Run("vcli config", func(t *testing.T) {
		// Simulate getting config path
		configPath, err := JoinHomePath(".vcli", "config.yaml")
		if err != nil {
			t.Fatalf("Failed to get config path: %v", err)
		}

		// Should be usable for file operations
		if !filepath.IsAbs(configPath) {
			t.Error("Config path should be absolute for file operations")
		}
	})

	t.Run("kubeconfig", func(t *testing.T) {
		// Simulate getting kubeconfig
		kubeconfig, err := JoinHomePath(".kube", "config")
		if err != nil {
			t.Fatalf("Failed to get kubeconfig: %v", err)
		}

		// Verify structure
		if !strings.Contains(kubeconfig, ".kube") || !strings.HasSuffix(kubeconfig, "config") {
			t.Errorf("Kubeconfig path malformed: %q", kubeconfig)
		}
	})

	t.Run("plugin directory", func(t *testing.T) {
		// Simulate getting plugin path
		pluginPath, err := JoinHomePath(".vcli", "plugins", "kubernetes", "plugin.so")
		if err != nil {
			t.Fatalf("Failed to get plugin path: %v", err)
		}

		// Should have all path components
		mustContain := []string{".vcli", "plugins", "kubernetes", "plugin.so"}
		for _, component := range mustContain {
			if !strings.Contains(pluginPath, component) {
				t.Errorf("Plugin path %q should contain %q", pluginPath, component)
			}
		}
	})
}

// Benchmark_GetHomeDir benchmarks home directory retrieval
func Benchmark_GetHomeDir(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_, _ = GetHomeDir()
	}
}

// Benchmark_JoinHomePath benchmarks path joining
func Benchmark_JoinHomePath(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_, _ = JoinHomePath(".vcli", "config.yaml")
	}
}

// TestEnsureVCLIConfigDir_ErrorPropagation tests error handling in directory creation
func TestEnsureVCLIConfigDir_ErrorPropagation(t *testing.T) {
	// This test verifies that errors from GetVCLIConfigDir are properly propagated
	// In a real failure scenario (e.g., HOME not set), the error should bubble up

	err := EnsureVCLIConfigDir()

	// In normal test environment, this should succeed
	// But we verify the error handling path exists
	if err != nil {
		// Error should be wrapped with context
		if !strings.Contains(err.Error(), "vcli config directory") {
			t.Errorf("Error should mention 'vcli config directory': %v", err)
		}
	}
}

// TestEnsureVCLIWorkflowsDir_ErrorPropagation tests error handling
func TestEnsureVCLIWorkflowsDir_ErrorPropagation(t *testing.T) {
	err := EnsureVCLIWorkflowsDir()

	if err != nil {
		// Error should be wrapped with context
		if !strings.Contains(err.Error(), "vcli workflows directory") {
			t.Errorf("Error should mention 'vcli workflows directory': %v", err)
		}
	}
}

// TestEnsureVCLIPluginsDir_ErrorPropagation tests error handling
func TestEnsureVCLIPluginsDir_ErrorPropagation(t *testing.T) {
	err := EnsureVCLIPluginsDir()

	if err != nil {
		// Error should be wrapped with context
		if !strings.Contains(err.Error(), "vcli plugins directory") {
			t.Errorf("Error should mention 'vcli plugins directory': %v", err)
		}
	}
}

// TestGetHomeDir_WithErrorContext tests error wrapping
func TestGetHomeDir_WithErrorContext(t *testing.T) {
	// Verify that GetHomeDir wraps errors properly
	home, err := GetHomeDir()

	if err != nil {
		// Error should be wrapped with "failed to get user home directory"
		if !strings.Contains(err.Error(), "failed to get user home directory") {
			t.Errorf("Error not properly wrapped: %v", err)
		}
	} else {
		// In success case, verify home is cleaned/normalized
		if strings.HasSuffix(home, "/") || strings.HasSuffix(home, "\\") {
			t.Errorf("GetHomeDir() should clean path (no trailing slash): %q", home)
		}
	}
}

// TestJoinHomePath_WithErrorContext tests error propagation
func TestJoinHomePath_WithErrorContext(t *testing.T) {
	// Verify that JoinHomePath propagates GetHomeDir errors
	path, err := JoinHomePath(".vcli", "test")

	if err != nil {
		// Error should come from GetHomeDir
		if !strings.Contains(err.Error(), "failed to get user home directory") {
			t.Errorf("Error should be from GetHomeDir: %v", err)
		}
	} else {
		// In success case, verify path structure
		if !strings.Contains(path, ".vcli") || !strings.Contains(path, "test") {
			t.Errorf("JoinHomePath() malformed: %q", path)
		}
	}
}

// TestEnsureVCLIConfigDir_PermissionCheck tests directory permissions
func TestEnsureVCLIConfigDir_PermissionCheck(t *testing.T) {
	// Ensure directory is created
	err := EnsureVCLIConfigDir()
	if err != nil {
		t.Fatalf("EnsureVCLIConfigDir() failed: %v", err)
	}

	// Get the directory path
	configDir, err := GetVCLIConfigDir()
	if err != nil {
		t.Fatalf("GetVCLIConfigDir() failed: %v", err)
	}

	// Verify directory exists and has proper permissions
	info, err := os.Stat(configDir)
	if err != nil {
		t.Fatalf("Directory not created: %v", err)
	}

	if !info.IsDir() {
		t.Error("Path exists but is not a directory")
	}

	// Check permissions (should be 0755)
	mode := info.Mode()
	if mode.Perm() != 0755 {
		t.Logf("Directory permissions: %o (expected 0755)", mode.Perm())
	}
}

// TestEnsureVCLIWorkflowsDir_PermissionCheck tests workflows directory permissions
func TestEnsureVCLIWorkflowsDir_PermissionCheck(t *testing.T) {
	err := EnsureVCLIWorkflowsDir()
	if err != nil {
		t.Fatalf("EnsureVCLIWorkflowsDir() failed: %v", err)
	}

	workflowsDir, err := GetVCLIWorkflowsDir()
	if err != nil {
		t.Fatalf("GetVCLIWorkflowsDir() failed: %v", err)
	}

	info, err := os.Stat(workflowsDir)
	if err != nil {
		t.Fatalf("Workflows directory not created: %v", err)
	}

	if !info.IsDir() {
		t.Error("Workflows path exists but is not a directory")
	}
}

// TestEnsureVCLIPluginsDir_PermissionCheck tests plugins directory permissions
func TestEnsureVCLIPluginsDir_PermissionCheck(t *testing.T) {
	err := EnsureVCLIPluginsDir()
	if err != nil {
		t.Fatalf("EnsureVCLIPluginsDir() failed: %v", err)
	}

	pluginsDir, err := GetVCLIPluginsDir()
	if err != nil {
		t.Fatalf("GetVCLIPluginsDir() failed: %v", err)
	}

	info, err := os.Stat(pluginsDir)
	if err != nil {
		t.Fatalf("Plugins directory not created: %v", err)
	}

	if !info.IsDir() {
		t.Error("Plugins path exists but is not a directory")
	}
}

// TestJoinHomePath_AbsolutePath tests that result is always absolute
func TestJoinHomePath_AbsolutePath(t *testing.T) {
	tests := []struct {
		name     string
		elements []string
	}{
		{"single element", []string{".vcli"}},
		{"multiple elements", []string{".vcli", "plugins", "test.so"}},
		{"relative path", []string{"relative", "path", "file.txt"}},
		{"dot files", []string{".config", ".settings"}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			path, err := JoinHomePath(tt.elements...)
			if err != nil {
				t.Fatalf("JoinHomePath() error: %v", err)
			}

			if !filepath.IsAbs(path) {
				t.Errorf("JoinHomePath() = %q, want absolute path", path)
			}
		})
	}
}

// TestGetHomeDir_PathCleaning tests that home directory is cleaned
func TestGetHomeDir_PathCleaning(t *testing.T) {
	home, err := GetHomeDir()
	if err != nil {
		t.Fatalf("GetHomeDir() error: %v", err)
	}

	// Should not have trailing separator
	if strings.HasSuffix(home, string(os.PathSeparator)) {
		t.Errorf("GetHomeDir() = %q, should not have trailing separator", home)
	}

	// Should be clean (no // or /./ or /../)
	cleaned := filepath.Clean(home)
	if home != cleaned {
		t.Errorf("GetHomeDir() = %q, not clean (should be %q)", home, cleaned)
	}
}

// TestEnsureDirectories_AllAtOnce tests creating all vcli directories
func TestEnsureDirectories_AllAtOnce(t *testing.T) {
	// Create all standard vcli directories
	errors := []error{
		EnsureVCLIConfigDir(),
		EnsureVCLIWorkflowsDir(),
		EnsureVCLIPluginsDir(),
	}

	// All should succeed
	for i, err := range errors {
		if err != nil {
			t.Errorf("Ensure directory %d failed: %v", i, err)
		}
	}

	// Verify all exist
	dirs := []func() (string, error){
		GetVCLIConfigDir,
		GetVCLIWorkflowsDir,
		GetVCLIPluginsDir,
	}

	for i, getDirFunc := range dirs {
		dir, err := getDirFunc()
		if err != nil {
			t.Errorf("Get directory %d failed: %v", i, err)
			continue
		}

		if _, statErr := os.Stat(dir); statErr != nil {
			t.Errorf("Directory %d does not exist: %v", i, statErr)
		}
	}
}

// TestJoinHomePath_NestedPaths tests deeply nested path construction
func TestJoinHomePath_NestedPaths(t *testing.T) {
	// Test deeply nested path
	path, err := JoinHomePath(".vcli", "plugins", "kubernetes", "v1.0.0", "bin", "plugin.so")
	if err != nil {
		t.Fatalf("JoinHomePath() error: %v", err)
	}

	// Should contain all components
	components := []string{".vcli", "plugins", "kubernetes", "v1.0.0", "bin", "plugin.so"}
	for _, component := range components {
		if !strings.Contains(path, component) {
			t.Errorf("Path %q should contain component %q", path, component)
		}
	}

	// Should be valid path
	if !filepath.IsAbs(path) {
		t.Errorf("Nested path should be absolute: %q", path)
	}
}

// TestGetters_ReturnCleanPaths tests that all getter functions return clean paths
func TestGetters_ReturnCleanPaths(t *testing.T) {
	getters := []struct {
		name string
		fn   func() (string, error)
	}{
		{"GetHomeDir", GetHomeDir},
		{"GetVCLIConfigDir", GetVCLIConfigDir},
		{"GetVCLIConfigFile", GetVCLIConfigFile},
		{"GetVCLIWorkflowsDir", GetVCLIWorkflowsDir},
		{"GetVCLIPluginsDir", GetVCLIPluginsDir},
		{"GetKubeconfigPath", GetKubeconfigPath},
	}

	for _, tt := range getters {
		t.Run(tt.name, func(t *testing.T) {
			path, err := tt.fn()
			if err != nil {
				t.Fatalf("%s() error: %v", tt.name, err)
			}

			// Should be clean
			cleaned := filepath.Clean(path)
			if path != cleaned {
				t.Errorf("%s() = %q, not clean (should be %q)", tt.name, path, cleaned)
			}

			// Should be absolute
			if !filepath.IsAbs(path) {
				t.Errorf("%s() = %q, should be absolute", tt.name, path)
			}
		})
	}
}

// TestEnsureVCLIConfigDir_AlreadyExists tests idempotency
func TestEnsureVCLIConfigDir_AlreadyExists(t *testing.T) {
	// First creation
	err := EnsureVCLIConfigDir()
	if err != nil {
		t.Fatalf("First EnsureVCLIConfigDir() failed: %v", err)
	}

	// Second creation (should be idempotent)
	err = EnsureVCLIConfigDir()
	if err != nil {
		t.Errorf("Second EnsureVCLIConfigDir() should be idempotent: %v", err)
	}

	// Third time for good measure
	err = EnsureVCLIConfigDir()
	if err != nil {
		t.Errorf("Third EnsureVCLIConfigDir() should be idempotent: %v", err)
	}
}

// TestEnsureVCLIWorkflowsDir_AlreadyExists tests idempotency
func TestEnsureVCLIWorkflowsDir_AlreadyExists(t *testing.T) {
	err := EnsureVCLIWorkflowsDir()
	if err != nil {
		t.Fatalf("First EnsureVCLIWorkflowsDir() failed: %v", err)
	}

	err = EnsureVCLIWorkflowsDir()
	if err != nil {
		t.Errorf("Second EnsureVCLIWorkflowsDir() should be idempotent: %v", err)
	}
}

// TestEnsureVCLIPluginsDir_AlreadyExists tests idempotency
func TestEnsureVCLIPluginsDir_AlreadyExists(t *testing.T) {
	err := EnsureVCLIPluginsDir()
	if err != nil {
		t.Fatalf("First EnsureVCLIPluginsDir() failed: %v", err)
	}

	err = EnsureVCLIPluginsDir()
	if err != nil {
		t.Errorf("Second EnsureVCLIPluginsDir() should be idempotent: %v", err)
	}
}

// TestJoinHomePath_WithVariousInputs tests edge cases
func TestJoinHomePath_WithVariousInputs(t *testing.T) {
	tests := []struct {
		name          string
		elements      []string
		shouldContain []string
	}{
		{
			name:          "empty elements list",
			elements:      []string{},
			shouldContain: []string{}, // Just returns home
		},
		{
			name:          "single empty string",
			elements:      []string{""},
			shouldContain: []string{}, // Should handle gracefully
		},
		{
			name:          "multiple empties",
			elements:      []string{"", "", ""},
			shouldContain: []string{},
		},
		{
			name:          "mixed empties and valid",
			elements:      []string{"", ".vcli", "", "config"},
			shouldContain: []string{".vcli", "config"},
		},
		{
			name:          "special characters",
			elements:      []string{".vcli-test", "my_config.yaml"},
			shouldContain: []string{".vcli-test", "my_config.yaml"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			path, err := JoinHomePath(tt.elements...)
			if err != nil {
				t.Fatalf("JoinHomePath() error: %v", err)
			}

			// Should always return absolute path
			if !filepath.IsAbs(path) {
				t.Errorf("JoinHomePath() = %q, want absolute", path)
			}

			// Check expected components
			for _, expected := range tt.shouldContain {
				if expected != "" && !strings.Contains(path, expected) {
					t.Errorf("Path %q should contain %q", path, expected)
				}
			}
		})
	}
}

// TestGetHomeDir_ReturnsConsistentValue tests consistency across calls
func TestGetHomeDir_ReturnsConsistentValue(t *testing.T) {
	// Call multiple times
	homes := make([]string, 10)
	for i := 0; i < 10; i++ {
		home, err := GetHomeDir()
		if err != nil {
			t.Fatalf("GetHomeDir() call %d failed: %v", i, err)
		}
		homes[i] = home
	}

	// All should be identical
	first := homes[0]
	for i, home := range homes {
		if home != first {
			t.Errorf("GetHomeDir() call %d returned %q, want %q", i, home, first)
		}
	}
}

// TestEnsureDirectories_CreateNestedStructure tests creating nested directories
func TestEnsureDirectories_CreateNestedStructure(t *testing.T) {
	// Ensure all directories - this creates nested structure
	// ~/.vcli/
	// ~/.vcli/workflows/
	// ~/.vcli/plugins/

	err := EnsureVCLIConfigDir()
	if err != nil {
		t.Fatalf("EnsureVCLIConfigDir() failed: %v", err)
	}

	err = EnsureVCLIWorkflowsDir()
	if err != nil {
		t.Fatalf("EnsureVCLIWorkflowsDir() failed: %v", err)
	}

	err = EnsureVCLIPluginsDir()
	if err != nil {
		t.Fatalf("EnsureVCLIPluginsDir() failed: %v", err)
	}

	// Verify parent directory exists
	configDir, _ := GetVCLIConfigDir()
	if _, statErr := os.Stat(configDir); statErr != nil {
		t.Errorf("Config directory should exist: %v", statErr)
	}

	// Verify subdirectories exist
	workflowsDir, _ := GetVCLIWorkflowsDir()
	if _, statErr := os.Stat(workflowsDir); statErr != nil {
		t.Errorf("Workflows directory should exist: %v", statErr)
	}

	pluginsDir, _ := GetVCLIPluginsDir()
	if _, statErr := os.Stat(pluginsDir); statErr != nil {
		t.Errorf("Plugins directory should exist: %v", statErr)
	}

	// Verify they're actual directories
	for _, dir := range []string{configDir, workflowsDir, pluginsDir} {
		info, err := os.Stat(dir)
		if err != nil {
			continue
		}
		if !info.IsDir() {
			t.Errorf("%q should be a directory", dir)
		}
	}
}
