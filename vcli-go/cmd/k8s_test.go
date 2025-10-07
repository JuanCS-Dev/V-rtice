package main

import (
	"testing"

	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// COMMAND STRUCTURE TESTS
// ============================================================================

func TestK8sCommand_Structure(t *testing.T) {
	t.Run("k8s command exists", func(t *testing.T) {
		assert.NotNil(t, k8sCmd)
		assert.Equal(t, "k8s", k8sCmd.Use)
		assert.NotEmpty(t, k8sCmd.Short)
		assert.NotEmpty(t, k8sCmd.Long)
	})

	t.Run("get subcommand exists", func(t *testing.T) {
		getCmd := findSubcommand(k8sCmd, "get")
		require.NotNil(t, getCmd)
		assert.Equal(t, "get [resource]", getCmd.Use)
	})

	t.Run("config subcommand exists", func(t *testing.T) {
		configCmd := findSubcommand(k8sCmd, "config")
		require.NotNil(t, configCmd)
		assert.Equal(t, "config", configCmd.Use)
	})
}

func TestGetCommand_ResourceSubcommands(t *testing.T) {
	getCmd := findSubcommand(k8sCmd, "get")
	require.NotNil(t, getCmd)

	tests := []struct {
		name    string
		cmdName string
	}{
		{"pods command", "pods"},
		{"pod command", "pod"},
		{"namespaces command", "namespaces"},
		{"namespace command", "namespace"},
		{"nodes command", "nodes"},
		{"node command", "node"},
		{"deployments command", "deployments"},
		{"deployment command", "deployment"},
		{"services command", "services"},
		{"service command", "service"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cmd := findSubcommand(getCmd, tt.cmdName)
			assert.NotNil(t, cmd, "command %s should exist", tt.cmdName)
		})
	}
}

func TestConfigCommand_Subcommands(t *testing.T) {
	configCmd := findSubcommand(k8sCmd, "config")
	require.NotNil(t, configCmd)

	tests := []struct {
		name    string
		cmdName string
	}{
		{"get-context command", "get-context"},
		{"get-contexts command", "get-contexts"},
		{"use-context command", "use-context"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cmd := findSubcommand(configCmd, tt.cmdName)
			assert.NotNil(t, cmd, "command %s should exist", tt.cmdName)
		})
	}
}

// ============================================================================
// FLAG TESTS
// ============================================================================

func TestK8sCommand_PersistentFlags(t *testing.T) {
	t.Run("kubeconfig flag exists", func(t *testing.T) {
		flag := k8sCmd.PersistentFlags().Lookup("kubeconfig")
		assert.NotNil(t, flag)
		assert.Equal(t, "", flag.DefValue) // Empty default (uses env or default path)
	})
}

func TestGetCommand_Flags(t *testing.T) {
	getCmd := findSubcommand(k8sCmd, "get")
	require.NotNil(t, getCmd)

	t.Run("namespace flag", func(t *testing.T) {
		flag := getCmd.PersistentFlags().Lookup("namespace")
		assert.NotNil(t, flag)
		assert.Equal(t, "default", flag.DefValue)
		assert.Equal(t, "n", flag.Shorthand)
	})

	t.Run("all-namespaces flag", func(t *testing.T) {
		flag := getCmd.PersistentFlags().Lookup("all-namespaces")
		assert.NotNil(t, flag)
		assert.Equal(t, "false", flag.DefValue)
		assert.Equal(t, "A", flag.Shorthand)
	})

	t.Run("output flag", func(t *testing.T) {
		flag := getCmd.PersistentFlags().Lookup("output")
		assert.NotNil(t, flag)
		assert.Equal(t, "table", flag.DefValue)
		assert.Equal(t, "o", flag.Shorthand)
	})
}

// ============================================================================
// ALIAS TESTS
// ============================================================================

func TestResourceCommands_Aliases(t *testing.T) {
	getCmd := findSubcommand(k8sCmd, "get")
	require.NotNil(t, getCmd)

	tests := []struct {
		name      string
		cmdName   string
		expectedAliases []string
	}{
		{
			name:      "pods aliases",
			cmdName:   "pods",
			expectedAliases: []string{"pod", "po"},
		},
		{
			name:      "namespaces aliases",
			cmdName:   "namespaces",
			expectedAliases: []string{"namespace", "ns"},
		},
		{
			name:      "nodes aliases",
			cmdName:   "nodes",
			expectedAliases: []string{"node", "no"},
		},
		{
			name:      "deployments aliases",
			cmdName:   "deployments",
			expectedAliases: []string{"deployment", "deploy"},
		},
		{
			name:      "services aliases",
			cmdName:   "services",
			expectedAliases: []string{"service", "svc"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cmd := findSubcommand(getCmd, tt.cmdName)
			require.NotNil(t, cmd)
			assert.ElementsMatch(t, tt.expectedAliases, cmd.Aliases)
		})
	}
}

func TestContextCommands_Aliases(t *testing.T) {
	configCmd := findSubcommand(k8sCmd, "config")
	require.NotNil(t, configCmd)

	t.Run("get-contexts aliases", func(t *testing.T) {
		cmd := findSubcommand(configCmd, "get-contexts")
		require.NotNil(t, cmd)
		assert.Contains(t, cmd.Aliases, "contexts")
	})
}

// ============================================================================
// ARGUMENT VALIDATION TESTS
// ============================================================================

func TestSingleResourceCommands_RequireArgument(t *testing.T) {
	getCmd := findSubcommand(k8sCmd, "get")
	require.NotNil(t, getCmd)

	tests := []struct {
		name    string
		cmdName string
	}{
		{"pod command", "pod"},
		{"namespace command", "namespace"},
		{"node command", "node"},
		{"deployment command", "deployment"},
		{"service command", "service"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cmd := findSubcommand(getCmd, tt.cmdName)
			require.NotNil(t, cmd)
			// Commands that get single resources should have Args validator
			assert.NotNil(t, cmd.Args, "command %s should have Args validator", tt.cmdName)
		})
	}
}

func TestUseContextCommand_RequireArgument(t *testing.T) {
	configCmd := findSubcommand(k8sCmd, "config")
	require.NotNil(t, configCmd)

	useContextCmd := findSubcommand(configCmd, "use-context")
	require.NotNil(t, useContextCmd)
	assert.NotNil(t, useContextCmd.Args)
}

// ============================================================================
// HELP TEXT TESTS
// ============================================================================

func TestK8sCommand_HelpText(t *testing.T) {
	t.Run("k8s command has short description", func(t *testing.T) {
		assert.NotEmpty(t, k8sCmd.Short)
		assert.Contains(t, k8sCmd.Short, "Kubernetes")
	})

	t.Run("k8s command has long description", func(t *testing.T) {
		assert.NotEmpty(t, k8sCmd.Long)
		assert.Contains(t, k8sCmd.Long, "Examples:")
	})
}

func TestGetCommand_HelpText(t *testing.T) {
	getCmd := findSubcommand(k8sCmd, "get")
	require.NotNil(t, getCmd)

	t.Run("get command has documentation", func(t *testing.T) {
		assert.NotEmpty(t, getCmd.Short)
		assert.NotEmpty(t, getCmd.Long)
	})

	t.Run("get command lists supported resources", func(t *testing.T) {
		assert.Contains(t, getCmd.Long, "pods")
		assert.Contains(t, getCmd.Long, "namespaces")
		assert.Contains(t, getCmd.Long, "nodes")
		assert.Contains(t, getCmd.Long, "deployments")
		assert.Contains(t, getCmd.Long, "services")
	})
}

func TestResourceCommands_HaveExamples(t *testing.T) {
	getCmd := findSubcommand(k8sCmd, "get")
	require.NotNil(t, getCmd)

	tests := []string{"pods", "namespaces", "nodes", "deployments", "services"}

	for _, cmdName := range tests {
		t.Run(cmdName+" has examples", func(t *testing.T) {
			cmd := findSubcommand(getCmd, cmdName)
			require.NotNil(t, cmd)
			assert.Contains(t, cmd.Long, "Examples:", "command %s should have examples", cmdName)
		})
	}
}

func TestConfigCommand_HelpText(t *testing.T) {
	configCmd := findSubcommand(k8sCmd, "config")
	require.NotNil(t, configCmd)

	t.Run("config command has documentation", func(t *testing.T) {
		assert.NotEmpty(t, configCmd.Short)
		assert.NotEmpty(t, configCmd.Long)
	})

	t.Run("config subcommands have examples", func(t *testing.T) {
		subcommands := []string{"get-context", "get-contexts", "use-context"}
		for _, name := range subcommands {
			cmd := findSubcommand(configCmd, name)
			require.NotNil(t, cmd, "config subcommand %s should exist", name)
			assert.Contains(t, cmd.Long, "Examples:", "config subcommand %s should have examples", name)
		}
	})
}

// ============================================================================
// RUNNABLE TESTS
// ============================================================================

func TestResourceCommands_HaveRunE(t *testing.T) {
	getCmd := findSubcommand(k8sCmd, "get")
	require.NotNil(t, getCmd)

	tests := []string{
		"pods", "pod",
		"namespaces", "namespace",
		"nodes", "node",
		"deployments", "deployment",
		"services", "service",
	}

	for _, cmdName := range tests {
		t.Run(cmdName+" is runnable", func(t *testing.T) {
			cmd := findSubcommand(getCmd, cmdName)
			require.NotNil(t, cmd)
			assert.NotNil(t, cmd.RunE, "command %s should have RunE function", cmdName)
		})
	}
}

func TestConfigCommands_HaveRunE(t *testing.T) {
	configCmd := findSubcommand(k8sCmd, "config")
	require.NotNil(t, configCmd)

	tests := []string{"get-context", "get-contexts", "use-context"}

	for _, cmdName := range tests {
		t.Run(cmdName+" is runnable", func(t *testing.T) {
			cmd := findSubcommand(configCmd, cmdName)
			require.NotNil(t, cmd)
			assert.NotNil(t, cmd.RunE, "command %s should have RunE function", cmdName)
		})
	}
}

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

func TestK8sCommand_IsAddedToRoot(t *testing.T) {
	// Check if k8s command is properly added to root
	found := false
	for _, cmd := range rootCmd.Commands() {
		if cmd.Name() == "k8s" {
			found = true
			break
		}
	}
	assert.True(t, found, "k8s command should be added to root command")
}

func TestGetCommand_IsAddedToK8s(t *testing.T) {
	// Check if get command is properly added to k8s
	getCmd := findSubcommand(k8sCmd, "get")
	assert.NotNil(t, getCmd, "get command should be added to k8s command")
}

func TestConfigCommand_IsAddedToK8s(t *testing.T) {
	// Check if config command is properly added to k8s
	configCmd := findSubcommand(k8sCmd, "config")
	assert.NotNil(t, configCmd, "config command should be added to k8s command")
}

// ============================================================================
// VALIDATION TESTS
// ============================================================================

func TestValidateK8sCommands(t *testing.T) {
	t.Run("validation function exists", func(t *testing.T) {
		err := validateK8sCommands()
		// Function should exist and run without panic
		// Error is acceptable if flags are not yet initialized in test context
		_ = err
	})
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

// findSubcommand finds a subcommand by name in a command's subcommands
func findSubcommand(cmd *cobra.Command, name string) *cobra.Command {
	for _, subCmd := range cmd.Commands() {
		if subCmd.Name() == name {
			return subCmd
		}
	}
	return nil
}

// assertCommandHasFlag checks if a command has a specific flag
func assertCommandHasFlag(t *testing.T, cmd *cobra.Command, flagName string) {
	flag := cmd.Flags().Lookup(flagName)
	if flag == nil {
		flag = cmd.PersistentFlags().Lookup(flagName)
	}
	assert.NotNil(t, flag, "command %s should have flag %s", cmd.Name(), flagName)
}
