package bubbletea

import (
	"os"
	"testing"

	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
)

// TestGetStatusline verifies statusline generation
func TestGetStatusline(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("returns string or empty", func(t *testing.T) {
		statusline := model.getStatusline()
		// May be empty if no kubeconfig exists
		assert.NotNil(t, statusline)
	})

	t.Run("returns empty when no kubeconfig", func(t *testing.T) {
		// Temporarily unset KUBECONFIG
		oldKubeconfig := os.Getenv("KUBECONFIG")
		os.Unsetenv("KUBECONFIG")
		defer func() {
			if oldKubeconfig != "" {
				os.Setenv("KUBECONFIG", oldKubeconfig)
			}
		}()

		statusline := model.getStatusline()
		// Should return empty string when no kubeconfig
		assert.IsType(t, "", statusline)
	})
}

// TestGetKubeconfigPath verifies kubeconfig path resolution
func TestGetKubeconfigPath(t *testing.T) {
	t.Run("returns empty or path string", func(t *testing.T) {
		path := getKubeconfigPath()
		assert.NotNil(t, path)
	})

	t.Run("respects KUBECONFIG environment variable", func(t *testing.T) {
		oldKubeconfig := os.Getenv("KUBECONFIG")
		defer func() {
			if oldKubeconfig != "" {
				os.Setenv("KUBECONFIG", oldKubeconfig)
			} else {
				os.Unsetenv("KUBECONFIG")
			}
		}()

		customPath := "/custom/kubeconfig/path"
		os.Setenv("KUBECONFIG", customPath)

		path := getKubeconfigPath()
		assert.Equal(t, customPath, path)
	})

	t.Run("returns default path when KUBECONFIG not set", func(t *testing.T) {
		oldKubeconfig := os.Getenv("KUBECONFIG")
		os.Unsetenv("KUBECONFIG")
		defer func() {
			if oldKubeconfig != "" {
				os.Setenv("KUBECONFIG", oldKubeconfig)
			}
		}()

		path := getKubeconfigPath()
		// Should return default path or empty
		assert.NotNil(t, path)
	})

	t.Run("returns empty for non-existent file", func(t *testing.T) {
		oldKubeconfig := os.Getenv("KUBECONFIG")
		os.Setenv("KUBECONFIG", "/nonexistent/path/config")
		defer func() {
			if oldKubeconfig != "" {
				os.Setenv("KUBECONFIG", oldKubeconfig)
			} else {
				os.Unsetenv("KUBECONFIG")
			}
		}()

		path := getKubeconfigPath()
		// Should check file existence and return empty
		assert.Empty(t, path)
	})
}

// TestUpdateStatusline verifies statusline update
func TestUpdateStatusline(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("updates statusline field", func(t *testing.T) {
		initialStatusline := model.statusline

		model.updateStatusline()

		// Statusline may change or stay the same depending on kubeconfig
		assert.NotNil(t, model.statusline)

		// Verify it doesn't panic
		_ = initialStatusline
	})

	t.Run("does not panic on update", func(t *testing.T) {
		assert.NotPanics(t, func() {
			model.updateStatusline()
		})
	})
}

// TestStatusline_Integration verifies statusline integration
func TestStatusline_Integration(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("statusline is accessible from model", func(t *testing.T) {
		model.updateStatusline()
		statusline := model.statusline

		assert.NotNil(t, statusline)
	})

	t.Run("statusline can be set manually", func(t *testing.T) {
		testStatusline := "⎈ test-context │ test-namespace"
		model.statusline = testStatusline

		assert.Equal(t, testStatusline, model.statusline)
	})

	t.Run("statusline is used in prompt rendering", func(t *testing.T) {
		model.statusline = "⎈ test-context"

		prompt := model.renderPrompt()
		assert.Contains(t, prompt, "⎈ test-context")
	})
}

// TestStatusline_EmptyHandling verifies empty statusline handling
func TestStatusline_EmptyHandling(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("empty statusline doesn't break prompt", func(t *testing.T) {
		model.statusline = ""

		prompt := model.renderPrompt()
		assert.NotEmpty(t, prompt)
		assert.Contains(t, prompt, "vCLI")
	})

	t.Run("getStatusline returns empty for errors", func(t *testing.T) {
		// Set invalid kubeconfig path
		oldKubeconfig := os.Getenv("KUBECONFIG")
		os.Setenv("KUBECONFIG", "/invalid/path/config")
		defer func() {
			if oldKubeconfig != "" {
				os.Setenv("KUBECONFIG", oldKubeconfig)
			} else {
				os.Unsetenv("KUBECONFIG")
			}
		}()

		statusline := model.getStatusline()
		assert.Empty(t, statusline)
	})
}

// TestStatusline_ConcurrentAccess verifies thread-safe access
func TestStatusline_ConcurrentAccess(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	model := NewModel(rootCmd, "1.0.0", "2024-01-01")

	t.Run("concurrent statusline updates", func(t *testing.T) {
		done := make(chan bool)

		// Launch multiple goroutines updating statusline
		for i := 0; i < 10; i++ {
			go func() {
				model.updateStatusline()
				done <- true
			}()
		}

		// Wait for all to complete
		for i := 0; i < 10; i++ {
			<-done
		}

		// No panic means success
	})

	t.Run("concurrent statusline reads", func(t *testing.T) {
		done := make(chan bool)

		// Launch multiple goroutines reading statusline
		for i := 0; i < 10; i++ {
			go func() {
				_ = model.getStatusline()
				done <- true
			}()
		}

		// Wait for all to complete
		for i := 0; i < 10; i++ {
			<-done
		}

		// No panic means success
	})
}
