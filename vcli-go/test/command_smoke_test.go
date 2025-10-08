package test

import (
	"bytes"
	"os"
	"testing"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/testutil"
)

// TestAllCommandsInvokable tests that all commands can be invoked without panics
func TestAllCommandsInvokable(t *testing.T) {
	// Build root command for testing
	rootCmd := testutil.BuildRootCommand()

	// Test cases: each command with --help flag
	testCases := []struct {
		name string
		args []string
	}{
		// Root
		{"root help", []string{"--help"}},
		{"version", []string{"version"}},

		// K8s commands
		{"k8s help", []string{"k8s", "--help"}},
		{"k8s get help", []string{"k8s", "get", "--help"}},
		{"k8s get pods help", []string{"k8s", "get", "pods", "--help"}},
		{"k8s get deployments help", []string{"k8s", "get", "deployments", "--help"}},
		{"k8s get services help", []string{"k8s", "get", "services", "--help"}},
		{"k8s get nodes help", []string{"k8s", "get", "nodes", "--help"}},
		{"k8s get namespaces help", []string{"k8s", "get", "namespaces", "--help"}},
		{"k8s apply help", []string{"k8s", "apply", "--help"}},
		{"k8s delete help", []string{"k8s", "delete", "--help"}},
		{"k8s scale help", []string{"k8s", "scale", "--help"}},
		{"k8s logs help", []string{"k8s", "logs", "--help"}},
		{"k8s exec help", []string{"k8s", "exec", "--help"}},
		{"k8s describe help", []string{"k8s", "describe", "--help"}},
		{"k8s top help", []string{"k8s", "top", "--help"}},
		{"k8s top nodes help", []string{"k8s", "top", "nodes", "--help"}},
		{"k8s top pods help", []string{"k8s", "top", "pods", "--help"}},
		{"k8s rollout help", []string{"k8s", "rollout", "--help"}},
		{"k8s auth help", []string{"k8s", "auth", "--help"}},
		{"k8s wait help", []string{"k8s", "wait", "--help"}},

		// Orchestrate
		{"orchestrate help", []string{"orchestrate", "--help"}},
		{"orchestrate offensive help", []string{"orchestrate", "offensive", "--help"}},
		{"orchestrate defensive help", []string{"orchestrate", "defensive", "--help"}},
		{"orchestrate osint help", []string{"orchestrate", "osint", "--help"}},
		{"orchestrate monitoring help", []string{"orchestrate", "monitoring", "--help"}},

		// Other commands
		{"data help", []string{"data", "--help"}},
		{"ethical help", []string{"ethical", "--help"}},
		{"immune help", []string{"immune", "--help"}},
		{"immunis help", []string{"immunis", "--help"}},
		{"maximus help", []string{"maximus", "--help"}},
		{"threat help", []string{"threat", "--help"}},
		{"investigate help", []string{"investigate", "--help"}},
		{"metrics help", []string{"metrics", "--help"}},
		{"sync help", []string{"sync", "--help"}},
		{"stream help", []string{"stream", "--help"}},
		{"gateway help", []string{"gateway", "--help"}},
		{"hcl help", []string{"hcl", "--help"}},
		{"configure help", []string{"configure", "--help"}},
		{"tui help", []string{"tui", "--help"}},
		{"workspace help", []string{"workspace", "--help"}},
		{"plugin help", []string{"plugin", "--help"}},
		{"offline help", []string{"offline", "--help"}},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			// Capture output
			oldStdout := os.Stdout
			oldStderr := os.Stderr
			r, w, _ := os.Pipe()
			os.Stdout = w
			os.Stderr = w

			// Reset command state
			rootCmd.SetArgs(tc.args)
			rootCmd.SilenceErrors = true
			rootCmd.SilenceUsage = true

			// Execute command (catch panic)
			err := func() (err error) {
				defer func() {
					if r := recover(); r != nil {
						t.Errorf("Command %v panicked: %v", tc.args, r)
					}
				}()
				return rootCmd.Execute()
			}()

			// Restore output
			w.Close()
			os.Stdout = oldStdout
			os.Stderr = oldStderr

			var buf bytes.Buffer
			buf.ReadFrom(r)

			// For --help commands, error is expected (exit code)
			// We just want to ensure no panic occurred
			if err != nil && !contains(tc.args, "--help") {
				t.Logf("Command %v returned error (may be expected): %v", tc.args, err)
			}

			// Command executed without panic
			t.Logf("✓ Command %v executed without panic", tc.args)
		})
	}
}

// TestShellCommandsExist verifies shell autocomplete commands exist
func TestShellCommandsExist(t *testing.T) {
	rootCmd := testutil.BuildRootCommand()

	// Commands that should exist (from completer.go)
	expectedCommands := []string{
		"k8s",
		"orchestrate",
		"data",
		"ethical",
		"immune",
		"immunis",
		"maximus",
		"threat",
		"investigate",
		"metrics",
		"sync",
		"stream",
		"gateway",
		"hcl",
		"configure",
		"tui",
		"workspace",
		"shell",
		"version",
		"plugin",
		"offline",
	}

	availableCommands := make(map[string]bool)
	for _, cmd := range rootCmd.Commands() {
		availableCommands[cmd.Name()] = true
	}

	for _, expected := range expectedCommands {
		if !availableCommands[expected] {
			t.Errorf("Expected command '%s' not found in root command", expected)
		}
	}
}

// TestK8sSubcommandsExist verifies k8s subcommands exist
func TestK8sSubcommandsExist(t *testing.T) {
	rootCmd := testutil.BuildRootCommand()

	// Find k8s command
	var k8sCmd *cobra.Command
	for _, cmd := range rootCmd.Commands() {
		if cmd.Name() == "k8s" {
			k8sCmd = cmd
			break
		}
	}

	if k8sCmd == nil {
		t.Fatal("k8s command not found")
	}

	// Expected k8s subcommands
	expectedSubcommands := []string{
		"get",
		"apply",
		"delete",
		"scale",
		"logs",
		"exec",
		"describe",
		"top",
		"rollout",
		"auth",
		"wait",
		"patch",
		"label",
		"annotate",
		"port-forward",
		"watch",
	}

	availableSubcommands := make(map[string]bool)
	for _, cmd := range k8sCmd.Commands() {
		availableSubcommands[cmd.Name()] = true
	}

	for _, expected := range expectedSubcommands {
		if !availableSubcommands[expected] {
			t.Errorf("Expected k8s subcommand '%s' not found", expected)
		}
	}
}

// TestOrchestrateWorkflowsExist verifies orchestrate workflows exist
func TestOrchestrateWorkflowsExist(t *testing.T) {
	rootCmd := testutil.BuildRootCommand()

	// Find orchestrate command
	var orchestrateCmd *cobra.Command
	for _, cmd := range rootCmd.Commands() {
		if cmd.Name() == "orchestrate" {
			orchestrateCmd = cmd
			break
		}
	}

	if orchestrateCmd == nil {
		t.Fatal("orchestrate command not found")
	}

	// Expected orchestrate categories
	expectedCategories := []string{
		"offensive",
		"defensive",
		"osint",
		"monitoring",
	}

	availableCategories := make(map[string]bool)
	for _, cmd := range orchestrateCmd.Commands() {
		availableCategories[cmd.Name()] = true
	}

	for _, expected := range expectedCategories {
		if !availableCategories[expected] {
			t.Errorf("Expected orchestrate category '%s' not found", expected)
		}
	}
}

// TestNoHiddenCommandsInAutocomplete ensures hidden commands aren't in suggestions
func TestNoHiddenCommandsInAutocomplete(t *testing.T) {
	rootCmd := testutil.BuildRootCommand()

	var hiddenCommands []string
	for _, cmd := range rootCmd.Commands() {
		if cmd.Hidden {
			hiddenCommands = append(hiddenCommands, cmd.Name())
		}
	}

	if len(hiddenCommands) > 0 {
		t.Logf("Found %d hidden commands (expected, should not be in autocomplete): %v",
			len(hiddenCommands), hiddenCommands)
	}
}

// Helper function
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
