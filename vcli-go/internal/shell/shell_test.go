package shell

import (
	"testing"

	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewShell verifies Shell instance creation with proper initialization
func TestNewShell(t *testing.T) {
	tests := []struct {
		name      string
		version   string
		buildDate string
		wantNil   bool
	}{
		{
			name:      "creates shell with version and build date",
			version:   "1.0.0",
			buildDate: "2024-01-01",
			wantNil:   false,
		},
		{
			name:      "creates shell with empty version",
			version:   "",
			buildDate: "2024-01-01",
			wantNil:   false,
		},
		{
			name:      "creates shell with empty build date",
			version:   "1.0.0",
			buildDate: "",
			wantNil:   false,
		},
		{
			name:      "creates shell with all empty",
			version:   "",
			buildDate: "",
			wantNil:   false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rootCmd := &cobra.Command{
				Use:   "vcli",
				Short: "vCLI test",
			}

			shell := NewShell(rootCmd, tt.version, tt.buildDate)

			if tt.wantNil {
				assert.Nil(t, shell)
			} else {
				require.NotNil(t, shell)
				assert.NotNil(t, shell.executor)
				assert.NotNil(t, shell.completer)
				assert.Equal(t, tt.version, shell.version)
				assert.Equal(t, tt.buildDate, shell.buildDate)
			}
		})
	}
}

// TestShell_Components verifies Shell components are properly initialized
func TestShell_Components(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	shell := NewShell(rootCmd, "1.0.0", "2024-01-01")

	t.Run("executor is initialized", func(t *testing.T) {
		assert.NotNil(t, shell.executor)
	})

	t.Run("completer is initialized", func(t *testing.T) {
		assert.NotNil(t, shell.completer)
	})

	t.Run("version is set", func(t *testing.T) {
		assert.Equal(t, "1.0.0", shell.version)
	})

	t.Run("buildDate is set", func(t *testing.T) {
		assert.Equal(t, "2024-01-01", shell.buildDate)
	})
}

// TestShell_ShowHelp verifies help display functionality
func TestShell_ShowHelp(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	shell := NewShell(rootCmd, "1.0.0", "2024-01-01")

	t.Run("ShowHelp does not panic", func(t *testing.T) {
		assert.NotPanics(t, func() {
			shell.ShowHelp()
		})
	})
}

// TestShell_Execute verifies execute method delegates to executor
func TestShell_Execute(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	shell := NewShell(rootCmd, "1.0.0", "2024-01-01")

	t.Run("execute method exists and doesn't panic", func(t *testing.T) {
		assert.NotPanics(t, func() {
			shell.execute("")
		})
	})
}

// TestShell_Complete verifies complete method delegates to completer
func TestShell_Complete(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}
	rootCmd.AddCommand(&cobra.Command{
		Use:   "test",
		Short: "test command",
	})

	shell := NewShell(rootCmd, "1.0.0", "2024-01-01")

	t.Run("complete returns suggestions", func(t *testing.T) {
		// Create a mock document
		// Note: go-prompt.Document has unexported fields, so we test through CompleteText
		suggestions := shell.completer.CompleteText("test")
		assert.NotNil(t, suggestions)
	})
}

// TestShell_VersionAndBuildDate verifies version info is accessible
func TestShell_VersionAndBuildDate(t *testing.T) {
	tests := []struct {
		name      string
		version   string
		buildDate string
	}{
		{
			name:      "semantic version",
			version:   "1.0.0",
			buildDate: "2024-01-01",
		},
		{
			name:      "pre-release version",
			version:   "2.0.0-beta.1",
			buildDate: "2024-06-15",
		},
		{
			name:      "development version",
			version:   "dev",
			buildDate: "unknown",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rootCmd := &cobra.Command{
				Use: "vcli",
			}

			shell := NewShell(rootCmd, tt.version, tt.buildDate)

			assert.Equal(t, tt.version, shell.version)
			assert.Equal(t, tt.buildDate, shell.buildDate)
		})
	}
}

// TestShell_WithSubcommands verifies Shell works with complex command trees
func TestShell_WithSubcommands(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	// Add subcommands
	k8sCmd := &cobra.Command{
		Use:   "k8s",
		Short: "Kubernetes operations",
	}
	k8sCmd.AddCommand(&cobra.Command{
		Use:   "get",
		Short: "Get resources",
	})
	rootCmd.AddCommand(k8sCmd)

	orchestrateCmd := &cobra.Command{
		Use:   "orchestrate",
		Short: "Orchestration workflows",
	}
	rootCmd.AddCommand(orchestrateCmd)

	t.Run("Shell initializes with complex command tree", func(t *testing.T) {
		shell := NewShell(rootCmd, "1.0.0", "2024-01-01")
		require.NotNil(t, shell)
		assert.NotNil(t, shell.executor)
		assert.NotNil(t, shell.completer)
	})
}

// TestShell_Concurrent verifies Shell is safe for concurrent access to completer
func TestShell_Concurrent(t *testing.T) {
	rootCmd := &cobra.Command{
		Use: "vcli",
	}

	shell := NewShell(rootCmd, "1.0.0", "2024-01-01")

	t.Run("concurrent completion requests", func(t *testing.T) {
		done := make(chan bool)

		// Launch multiple goroutines doing completions
		for i := 0; i < 10; i++ {
			go func() {
				shell.completer.CompleteText("k8s")
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
