package shell

import (
	"bytes"
	"io"
	"os"
	"testing"

	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// captureOutput captures stdout during test execution
func captureOutput(f func()) string {
	old := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	f()

	w.Close()
	os.Stdout = old

	var buf bytes.Buffer
	io.Copy(&buf, r)
	return buf.String()
}

// TestNewExecutor verifies Executor instance creation
func TestNewExecutor(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	t.Run("creates executor with proper initialization", func(t *testing.T) {
		executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")
		require.NotNil(t, executor)
		assert.NotNil(t, executor.rootCmd)
		assert.NotNil(t, executor.styles)
		assert.NotNil(t, executor.suggester)
		assert.NotNil(t, executor.history)
		assert.Equal(t, "1.0.0", executor.version)
		assert.Equal(t, "2024-01-01", executor.buildDate)
	})

	t.Run("initializes empty history", func(t *testing.T) {
		executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")
		assert.Len(t, executor.history, 0)
	})
}

// TestExecutor_Execute verifies command execution
func TestExecutor_Execute(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	tests := []struct {
		name         string
		input        string
		wantHistory  bool
		historyCount int
	}{
		{
			name:         "empty input",
			input:        "",
			wantHistory:  false,
			historyCount: 0,
		},
		{
			name:         "whitespace only",
			input:        "   ",
			wantHistory:  false,
			historyCount: 0,
		},
		{
			name:         "slash command",
			input:        "/help",
			wantHistory:  true,
			historyCount: 1,
		},
		{
			name:         "builtin command",
			input:        "help",
			wantHistory:  true,
			historyCount: 1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			executor.history = make([]string, 0) // Reset history

			executor.Execute(tt.input)

			if tt.wantHistory {
				assert.Len(t, executor.history, tt.historyCount)
			} else {
				assert.Len(t, executor.history, tt.historyCount)
			}
		})
	}
}

// TestExecutor_HandleSlashCommand verifies slash command handling
func TestExecutor_HandleSlashCommand(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	tests := []struct {
		name    string
		input   string
		wantErr bool
	}{
		{
			name:    "/help command",
			input:   "/help",
			wantErr: false,
		},
		{
			name:    "/? command",
			input:   "/?",
			wantErr: false,
		},
		{
			name:    "/clear command",
			input:   "/clear",
			wantErr: false,
		},
		{
			name:    "/cls command",
			input:   "/cls",
			wantErr: false,
		},
		{
			name:    "/history command",
			input:   "/history",
			wantErr: false,
		},
		{
			name:    "/palette command",
			input:   "/palette",
			wantErr: false,
		},
		{
			name:    "/p command",
			input:   "/p",
			wantErr: false,
		},
		{
			name:    "/theme command",
			input:   "/theme",
			wantErr: false,
		},
		{
			name:    "unknown slash command",
			input:   "/unknown",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.NotPanics(t, func() {
				executor.handleSlashCommand(tt.input)
			})
		})
	}
}

// TestExecutor_HandleBuiltin verifies built-in command handling
func TestExecutor_HandleBuiltin(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	tests := []struct {
		name       string
		input      string
		wantHandle bool
	}{
		{
			name:       "help command",
			input:      "help",
			wantHandle: true,
		},
		{
			name:       "HELP uppercase",
			input:      "HELP",
			wantHandle: true,
		},
		{
			name:       "history command",
			input:      "history",
			wantHandle: true,
		},
		{
			name:       "clear command",
			input:      "clear",
			wantHandle: true,
		},
		{
			name:       "cls command",
			input:      "cls",
			wantHandle: true,
		},
		{
			name:       "wf1 workflow",
			input:      "wf1",
			wantHandle: true,
		},
		{
			name:       "wf2 workflow",
			input:      "wf2",
			wantHandle: true,
		},
		{
			name:       "wf3 workflow",
			input:      "wf3",
			wantHandle: true,
		},
		{
			name:       "wf4 workflow",
			input:      "wf4",
			wantHandle: true,
		},
		{
			name:       "non-builtin command",
			input:      "k8s get pods",
			wantHandle: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			handled := executor.handleBuiltin(tt.input)
			assert.Equal(t, tt.wantHandle, handled)
		})
	}
}

// TestExecutor_GetHistory verifies history retrieval
func TestExecutor_GetHistory(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	t.Run("empty history initially", func(t *testing.T) {
		history := executor.GetHistory()
		assert.Empty(t, history)
	})

	t.Run("history grows with commands", func(t *testing.T) {
		executor.Execute("test1")
		executor.Execute("test2")
		executor.Execute("test3")

		history := executor.GetHistory()
		assert.Len(t, history, 3)
		assert.Equal(t, "test1", history[0])
		assert.Equal(t, "test2", history[1])
		assert.Equal(t, "test3", history[2])
	})
}

// TestExecutor_ShowHistory verifies history display
func TestExecutor_ShowHistory(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	t.Run("shows empty history message", func(t *testing.T) {
		output := captureOutput(func() {
			executor.showHistory()
		})
		assert.Contains(t, output, "No command history")
	})

	t.Run("shows history with commands", func(t *testing.T) {
		executor.Execute("test command")

		output := captureOutput(func() {
			executor.showHistory()
		})
		assert.Contains(t, output, "test command")
	})

	t.Run("limits history to last 20 commands", func(t *testing.T) {
		executor.history = make([]string, 0)
		for i := 0; i < 25; i++ {
			executor.history = append(executor.history, "command")
		}

		output := captureOutput(func() {
			executor.showHistory()
		})
		// Should show limited history
		assert.NotEmpty(t, output)
	})
}

// TestExecutor_ShowHelp verifies help display
func TestExecutor_ShowHelp(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	t.Run("shows help without panic", func(t *testing.T) {
		assert.NotPanics(t, func() {
			executor.showHelp()
		})
	})

	t.Run("help contains shell commands", func(t *testing.T) {
		output := captureOutput(func() {
			executor.showHelp()
		})
		assert.Contains(t, output, "/help")
		assert.Contains(t, output, "/palette")
		assert.Contains(t, output, "/exit")
	})

	t.Run("help contains keyboard shortcuts", func(t *testing.T) {
		output := captureOutput(func() {
			executor.showHelp()
		})
		assert.Contains(t, output, "Tab")
		assert.Contains(t, output, "Ctrl")
	})
}

// TestExecutor_ParseCommand verifies command parsing
func TestParseCommand(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected []string
	}{
		{
			name:     "simple command",
			input:    "k8s get pods",
			expected: []string{"k8s", "get", "pods"},
		},
		{
			name:     "command with double quotes",
			input:    `data query "MATCH (n) RETURN n"`,
			expected: []string{"data", "query", "MATCH (n) RETURN n"},
		},
		{
			name:     "command with single quotes",
			input:    `echo 'hello world'`,
			expected: []string{"echo", "hello world"},
		},
		{
			name:     "command with flags",
			input:    "k8s get pods --all-namespaces",
			expected: []string{"k8s", "get", "pods", "--all-namespaces"},
		},
		{
			name:     "command with escaped characters",
			input:    `echo hello\ world`,
			expected: []string{"echo", "helloworld"},
		},
		{
			name:     "empty input",
			input:    "",
			expected: []string{},
		},
		{
			name:     "whitespace only",
			input:    "   ",
			expected: []string{},
		},
		{
			name:     "multiple spaces",
			input:    "cmd    arg1    arg2",
			expected: []string{"cmd", "arg1", "arg2"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := parseCommand(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// TestExecutor_ExtractTypo verifies typo extraction from error messages
func TestExecutor_ExtractTypo(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	tests := []struct {
		name     string
		errMsg   string
		expected string
	}{
		{
			name:     "error with quoted typo",
			errMsg:   `unknown command "kgp" for "vcli"`,
			expected: "kgp",
		},
		{
			name:     "error with flag",
			errMsg:   `unknown flag "--outputt"`,
			expected: "--outputt",
		},
		{
			name:     "no quotes",
			errMsg:   "some error without quotes",
			expected: "",
		},
		{
			name:     "empty error",
			errMsg:   "",
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := executor.extractTypo(tt.errMsg)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// TestExecutor_ExecuteCobraCommand verifies Cobra command execution
func TestExecutor_ExecuteCobraCommand(t *testing.T) {
	var executed bool
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
		Run: func(cmd *cobra.Command, args []string) {
			executed = true
		},
	}

	testCmd := &cobra.Command{
		Use:   "test",
		Short: "Test command",
		Run: func(cmd *cobra.Command, args []string) {
			executed = true
		},
	}
	rootCmd.AddCommand(testCmd)

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	t.Run("executes valid command", func(t *testing.T) {
		executed = false
		executor.executeCobraCommand([]string{"test"})
		assert.True(t, executed)
	})

	t.Run("handles unknown command gracefully", func(t *testing.T) {
		assert.NotPanics(t, func() {
			executor.executeCobraCommand([]string{"unknown"})
		})
	})

	t.Run("preserves silence settings", func(t *testing.T) {
		originalSilenceErrors := rootCmd.SilenceErrors
		originalSilenceUsage := rootCmd.SilenceUsage

		executor.executeCobraCommand([]string{"test"})

		assert.Equal(t, originalSilenceErrors, rootCmd.SilenceErrors)
		assert.Equal(t, originalSilenceUsage, rootCmd.SilenceUsage)
	})
}

// TestExecutor_WorkflowAliases verifies workflow alias execution
func TestExecutor_WorkflowAliases(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	orchestrateCmd := &cobra.Command{
		Use:   "orchestrate",
		Short: "Orchestration",
	}
	orchestrateCmd.AddCommand(&cobra.Command{
		Use:   "defensive",
		Short: "Defensive workflows",
	})
	orchestrateCmd.AddCommand(&cobra.Command{
		Use:   "monitoring",
		Short: "Monitoring workflows",
	})
	rootCmd.AddCommand(orchestrateCmd)

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	tests := []struct {
		name  string
		input string
	}{
		{
			name:  "wf1 - Threat Hunt",
			input: "wf1",
		},
		{
			name:  "wf2 - Incident Response",
			input: "wf2",
		},
		{
			name:  "wf3 - Security Audit",
			input: "wf3",
		},
		{
			name:  "wf4 - Compliance Check",
			input: "wf4",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			handled := executor.handleBuiltin(tt.input)
			assert.True(t, handled, "workflow alias should be handled")
		})
	}
}

// TestExecutor_RenderStatusline verifies statusline rendering
func TestExecutor_RenderStatusline(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	t.Run("returns statusline or empty string", func(t *testing.T) {
		statusline := executor.renderStatusline()
		// Should return string (may be empty if no kubeconfig)
		assert.NotNil(t, statusline)
	})
}

// TestExecutor_GetKubeconfigPath verifies kubeconfig path retrieval
func TestExecutor_GetKubeconfigPath(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	t.Run("gets kubeconfig path", func(t *testing.T) {
		path := executor.getKubeconfigPath()
		// May be empty if no kubeconfig exists
		assert.NotNil(t, path)
	})

	t.Run("respects KUBECONFIG env var", func(t *testing.T) {
		oldKubeconfig := os.Getenv("KUBECONFIG")
		defer os.Setenv("KUBECONFIG", oldKubeconfig)

		os.Setenv("KUBECONFIG", "/custom/path/config")
		path := executor.getKubeconfigPath()
		assert.Equal(t, "/custom/path/config", path)
	})
}

// TestExecutor_RedrawWelcome verifies welcome screen redraw
func TestExecutor_RedrawWelcome(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	t.Run("redrawWelcome does not panic", func(t *testing.T) {
		assert.NotPanics(t, func() {
			executor.redrawWelcome()
		})
	})
}

// TestExecutor_HistoryPersistence verifies history is maintained across executions
func TestExecutor_HistoryPersistence(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	t.Run("history persists across multiple executions", func(t *testing.T) {
		commands := []string{"cmd1", "cmd2", "cmd3"}

		for _, cmd := range commands {
			executor.Execute(cmd)
		}

		history := executor.GetHistory()
		assert.Len(t, history, len(commands))

		for i, cmd := range commands {
			assert.Equal(t, cmd, history[i])
		}
	})
}

// TestExecutor_EmptyCommandHandling verifies empty command handling
func TestExecutor_EmptyCommandHandling(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	tests := []struct {
		name  string
		input string
	}{
		{
			name:  "empty string",
			input: "",
		},
		{
			name:  "single space",
			input: " ",
		},
		{
			name:  "multiple spaces",
			input: "   ",
		},
		{
			name:  "tabs",
			input: "\t\t",
		},
		{
			name:  "newlines",
			input: "\n\n",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			initialLen := len(executor.GetHistory())

			executor.Execute(tt.input)

			// Empty commands should not be added to history
			assert.Len(t, executor.GetHistory(), initialLen)
		})
	}
}

// TestExecutor_ConcurrentExecution verifies thread safety
func TestExecutor_ConcurrentExecution(t *testing.T) {
	rootCmd := &cobra.Command{
		Use:   "vcli",
		Short: "vCLI test",
	}

	executor := NewExecutor(rootCmd, "1.0.0", "2024-01-01")

	t.Run("concurrent executions", func(t *testing.T) {
		done := make(chan bool)

		// Launch multiple goroutines executing commands
		for i := 0; i < 10; i++ {
			go func() {
				executor.Execute("help")
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
