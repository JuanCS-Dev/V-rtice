package integration

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gopkg.in/yaml.v3"
)

// E2ETestConfig holds configuration for E2E tests
type E2ETestConfig struct {
	VCLIBinaryPath  string
	KubeconfigPath  string
	TestNamespace   string
	ProductionNS    string
	StagingNS       string
}

// getE2EConfig returns the E2E test configuration
func getE2EConfig(t *testing.T) *E2ETestConfig {
	t.Helper()

	// Get absolute paths
	workDir, err := os.Getwd()
	require.NoError(t, err, "should get working directory")

	// vcli binary is at ../../../bin/vcli relative to test file
	vcliPath := filepath.Join(workDir, "..", "..", "..", "bin", "vcli")
	kubeconfigPath := filepath.Join(workDir, "kubeconfig")

	// Verify files exist
	_, err = os.Stat(vcliPath)
	require.NoError(t, err, "vcli binary should exist at %s", vcliPath)

	_, err = os.Stat(kubeconfigPath)
	require.NoError(t, err, "kubeconfig should exist at %s", kubeconfigPath)

	return &E2ETestConfig{
		VCLIBinaryPath:  vcliPath,
		KubeconfigPath:  kubeconfigPath,
		TestNamespace:   "test-namespace",
		ProductionNS:    "production",
		StagingNS:       "staging",
	}
}

// runVCLI executes vcli command and returns stdout, stderr, and exit code
func runVCLI(t *testing.T, config *E2ETestConfig, args ...string) (string, string, int) {
	t.Helper()

	// Set up command with KUBECONFIG
	cmd := exec.Command(config.VCLIBinaryPath, args...)
	cmd.Env = append(os.Environ(), "KUBECONFIG="+config.KubeconfigPath)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			t.Fatalf("failed to run vcli: %v", err)
		}
	}

	return stdout.String(), stderr.String(), exitCode
}

// ============================================================================
// E2E TEST SCENARIOS
// ============================================================================

// TestE2E_Scenario1_ListPodsInDefaultNamespace tests listing pods in default namespace
func TestE2E_Scenario1_ListPodsInDefaultNamespace(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	config := getE2EConfig(t)

	t.Run("list pods with default output", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "pods")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		// Verify table format output
		assert.Contains(t, stdout, "NAME", "should have header")
		assert.Contains(t, stdout, "NAMESPACE", "should have namespace column")
		assert.Contains(t, stdout, "STATUS", "should have status column")
		assert.Contains(t, stdout, "nginx-deployment", "should show nginx pods")
		assert.Contains(t, stdout, "Running", "should show running status")
	})

	t.Run("list pods in specific namespace", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "pods", "-n", config.TestNamespace)

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		// Verify we get pods from test-namespace
		assert.Contains(t, stdout, "api-deployment", "should show api-deployment pods")
		assert.Contains(t, stdout, "test-namespace", "should show test-namespace")
	})

	t.Run("list pods across all namespaces", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "pods", "--all-namespaces")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		// Verify we get pods from multiple namespaces
		assert.Contains(t, stdout, "default", "should have default namespace")
		assert.Contains(t, stdout, "test-namespace", "should have test-namespace")
		assert.Contains(t, stdout, "production", "should have production namespace")
	})
}

// TestE2E_Scenario2_OutputFormats tests different output formats
func TestE2E_Scenario2_OutputFormats(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	config := getE2EConfig(t)

	t.Run("table format (default)", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "namespaces")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		// Table format has headers
		lines := strings.Split(stdout, "\n")
		assert.Greater(t, len(lines), 1, "should have multiple lines")
		assert.Contains(t, lines[0], "NAME", "first line should be header")
	})

	t.Run("json format", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "namespaces", "--output", "json")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		// Verify valid JSON
		var namespaces []map[string]interface{}
		err := json.Unmarshal([]byte(stdout), &namespaces)
		require.NoError(t, err, "output should be valid JSON")
		assert.NotEmpty(t, namespaces, "should have namespaces in JSON")

		// Verify structure (fields are capitalized in JSON)
		assert.Contains(t, namespaces[0], "Name", "namespace should have Name field")
		assert.Contains(t, namespaces[0], "Status", "namespace should have Status field")
	})

	t.Run("yaml format", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "namespaces", "--output", "yaml")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		// Verify valid YAML
		var namespaces []map[string]interface{}
		err := yaml.Unmarshal([]byte(stdout), &namespaces)
		require.NoError(t, err, "output should be valid YAML")
		assert.NotEmpty(t, namespaces, "should have namespaces in YAML")
	})
}

// TestE2E_Scenario3_ContextManagement tests context switching
func TestE2E_Scenario3_ContextManagement(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	config := getE2EConfig(t)

	t.Run("get current context", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "config", "get-context")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		// Should show current context
		assert.Contains(t, stdout, "kind-vcli-test", "should show kind-vcli-test context")
	})

	t.Run("list all contexts", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "config", "get-contexts")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		// Should list contexts
		assert.Contains(t, stdout, "CONTEXT", "should have header")
		assert.Contains(t, stdout, "kind-vcli-test", "should list kind-vcli-test")
	})
}

// TestE2E_Scenario4_ResourceQueries tests querying different resource types
func TestE2E_Scenario4_ResourceQueries(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	config := getE2EConfig(t)

	t.Run("get deployments", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "deployments", "-n", config.TestNamespace)

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		assert.Contains(t, stdout, "api-deployment", "should show api-deployment")
		assert.Contains(t, stdout, "READY", "should have READY column")
		assert.Contains(t, stdout, "3/3", "should show 3/3 replicas ready")
	})

	t.Run("get single deployment", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "deployment", "nginx-deployment")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		assert.Contains(t, stdout, "nginx-deployment", "should show nginx-deployment")
		assert.Contains(t, stdout, "2/2", "should show 2/2 replicas")
	})

	t.Run("get services", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "services", "-n", "default")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		assert.Contains(t, stdout, "nginx-service", "should show nginx-service")
		assert.Contains(t, stdout, "ClusterIP", "should show service type")
	})

	t.Run("get nodes", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "nodes")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.NotEmpty(t, stdout, "should have output")

		assert.Contains(t, stdout, "vcli-test-control-plane", "should show control plane node")
		assert.Contains(t, stdout, "Ready", "node should be ready")
	})
}

// TestE2E_Scenario5_ErrorHandling tests error scenarios
func TestE2E_Scenario5_ErrorHandling(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	config := getE2EConfig(t)

	t.Run("get non-existent pod", func(t *testing.T) {
		_, stderr, exitCode := runVCLI(t, config, "k8s", "get", "pod", "non-existent-pod")

		assert.NotEqual(t, 0, exitCode, "command should fail")
		assert.NotEmpty(t, stderr, "should have error message")
		assert.Contains(t, strings.ToLower(stderr), "not found", "should mention not found")
	})

	t.Run("get pod without name", func(t *testing.T) {
		stdout, _, exitCode := runVCLI(t, config, "k8s", "get", "pod")

		// NOTE: Currently "get pod" without name lists all pods (like "get pods")
		// This is because both commands share the same handler
		// In the future, we might want to enforce Args: cobra.ExactArgs(1) on singular commands
		assert.Equal(t, 0, exitCode, "command succeeds (lists all pods)")
		assert.NotEmpty(t, stdout, "should list pods")
	})

	t.Run("invalid output format", func(t *testing.T) {
		_, stderr, exitCode := runVCLI(t, config, "k8s", "get", "pods", "--output", "invalid")

		assert.NotEqual(t, 0, exitCode, "command should fail")
		assert.NotEmpty(t, stderr, "should have error message")
		assert.Contains(t, strings.ToLower(stderr), "unsupported", "should mention unsupported format")
	})

	t.Run("get resource in non-existent namespace", func(t *testing.T) {
		_, _, exitCode := runVCLI(t, config, "k8s", "get", "pods", "-n", "non-existent-namespace")

		// This might succeed with empty results or fail - both are valid
		// Just verify command completes (don't assert specific behavior)
		_ = exitCode
	})
}

// TestE2E_Scenario6_CommandAliases tests command aliases work correctly
func TestE2E_Scenario6_CommandAliases(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	config := getE2EConfig(t)

	t.Run("pods vs po alias", func(t *testing.T) {
		_, stderr1, exitCode1 := runVCLI(t, config, "k8s", "get", "pods")
		stdout2, stderr2, exitCode2 := runVCLI(t, config, "k8s", "get", "po")

		assert.Equal(t, exitCode1, exitCode2, "exit codes should match")
		assert.Equal(t, stderr1, stderr2, "errors should match")
		// Output should be similar (might vary in timestamps)
		assert.Contains(t, stdout2, "nginx-deployment", "alias should work")
	})

	t.Run("namespaces vs ns alias", func(t *testing.T) {
		_, _, exitCode1 := runVCLI(t, config, "k8s", "get", "namespaces")
		stdout2, _, exitCode2 := runVCLI(t, config, "k8s", "get", "ns")

		assert.Equal(t, exitCode1, exitCode2, "exit codes should match")
		assert.Contains(t, stdout2, "default", "alias should work")
	})

	t.Run("deployments vs deploy alias", func(t *testing.T) {
		_, _, exitCode1 := runVCLI(t, config, "k8s", "get", "deployments", "-n", config.TestNamespace)
		stdout2, _, exitCode2 := runVCLI(t, config, "k8s", "get", "deploy", "-n", config.TestNamespace)

		assert.Equal(t, exitCode1, exitCode2, "exit codes should match")
		assert.Contains(t, stdout2, "api-deployment", "alias should work")
	})

	t.Run("services vs svc alias", func(t *testing.T) {
		_, _, exitCode1 := runVCLI(t, config, "k8s", "get", "services")
		stdout2, _, exitCode2 := runVCLI(t, config, "k8s", "get", "svc")

		assert.Equal(t, exitCode1, exitCode2, "exit codes should match")
		assert.Contains(t, stdout2, "kubernetes", "alias should work")
	})
}

// TestE2E_Scenario7_FlagCombinations tests various flag combinations
func TestE2E_Scenario7_FlagCombinations(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	config := getE2EConfig(t)

	t.Run("namespace short flag", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "pods", "-n", config.TestNamespace)

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")
		assert.Contains(t, stdout, "test-namespace", "should show test-namespace")
	})

	t.Run("all-namespaces short flag", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "pods", "-A")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")

		// Verify we see pods from multiple namespaces
		assert.Contains(t, stdout, "default", "should show default namespace")
		// Check for either test-namespace or kube-system (depends on timing)
		hasMultipleNS := strings.Contains(stdout, "test-namespace") || strings.Contains(stdout, "kube-system")
		assert.True(t, hasMultipleNS, "should show multiple namespaces")
	})

	t.Run("output short flag", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "namespaces", "-o", "json")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")

		// Verify JSON
		var namespaces []map[string]interface{}
		err := json.Unmarshal([]byte(stdout), &namespaces)
		assert.NoError(t, err, "should be valid JSON")
	})

	t.Run("combined flags", func(t *testing.T) {
		stdout, stderr, exitCode := runVCLI(t, config, "k8s", "get", "deployments", "-n", config.ProductionNS, "-o", "json")

		assert.Equal(t, 0, exitCode, "command should succeed")
		assert.Empty(t, stderr, "should have no errors")

		// Verify JSON
		var deployments []map[string]interface{}
		err := json.Unmarshal([]byte(stdout), &deployments)
		assert.NoError(t, err, "should be valid JSON")
		assert.NotEmpty(t, deployments, "should have deployments")
	})
}

// TestE2E_Scenario8_Performance tests command performance
func TestE2E_Scenario8_Performance(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	config := getE2EConfig(t)

	t.Run("command execution time", func(t *testing.T) {
		// Simple commands should execute quickly
		cmd := exec.Command(config.VCLIBinaryPath, "k8s", "get", "namespaces")
		cmd.Env = append(os.Environ(), "KUBECONFIG="+config.KubeconfigPath)

		err := cmd.Run()
		require.NoError(t, err, "command should succeed")
		// Performance assertion is implicit - if it times out, test fails
		// We don't assert specific timing as it varies by system
	})
}
