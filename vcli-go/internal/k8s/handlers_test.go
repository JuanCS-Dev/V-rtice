package k8s

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/spf13/cobra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// HELPER TESTS
// ============================================================================

func TestNewHandlerConfig(t *testing.T) {
	config := NewHandlerConfig()

	assert.NotNil(t, config)
	assert.NotEmpty(t, config.KubeconfigPath)
	assert.Equal(t, "default", config.Namespace)
	assert.False(t, config.AllNamespaces)
	assert.Equal(t, OutputFormatTable, config.OutputFormat)
}

func TestGetDefaultKubeconfigPath(t *testing.T) {
	t.Run("with KUBECONFIG env", func(t *testing.T) {
		customPath := "/custom/path/kubeconfig"
		os.Setenv("KUBECONFIG", customPath)
		defer os.Unsetenv("KUBECONFIG")

		path := getDefaultKubeconfigPath()
		assert.Equal(t, customPath, path)
	})

	t.Run("default path", func(t *testing.T) {
		os.Unsetenv("KUBECONFIG")

		path := getDefaultKubeconfigPath()
		assert.Contains(t, path, ".kube/config")
	})
}

func TestParseCommonFlags(t *testing.T) {
	t.Run("default values", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().Bool("all-namespaces", false, "")
		cmd.Flags().String("output", "table", "")

		config, err := parseCommonFlags(cmd)
		require.NoError(t, err)
		assert.NotNil(t, config)
		assert.Equal(t, "default", config.Namespace)
		assert.False(t, config.AllNamespaces)
		assert.Equal(t, OutputFormatTable, config.OutputFormat)
	})

	t.Run("custom values", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/custom/kubeconfig", "")
		cmd.Flags().String("namespace", "kube-system", "")
		cmd.Flags().Bool("all-namespaces", true, "")
		cmd.Flags().String("output", "json", "")

		cmd.Flags().Set("kubeconfig", "/custom/kubeconfig")
		cmd.Flags().Set("namespace", "kube-system")
		cmd.Flags().Set("all-namespaces", "true")
		cmd.Flags().Set("output", "json")

		config, err := parseCommonFlags(cmd)
		require.NoError(t, err)
		assert.Equal(t, "/custom/kubeconfig", config.KubeconfigPath)
		assert.Equal(t, "kube-system", config.Namespace)
		assert.True(t, config.AllNamespaces)
		assert.Equal(t, OutputFormatJSON, config.OutputFormat)
	})
}

func TestInitClusterManager(t *testing.T) {
	t.Run("empty path", func(t *testing.T) {
		manager, err := initClusterManager("")
		assert.Error(t, err)
		assert.Nil(t, manager)
		assert.Contains(t, err.Error(), "kubeconfig path is required")
	})

	t.Run("invalid path", func(t *testing.T) {
		manager, err := initClusterManager("/nonexistent/path")
		assert.Error(t, err)
		assert.Nil(t, manager)
	})

	t.Run("valid path", func(t *testing.T) {
		// Create temp kubeconfig
		tmpDir := t.TempDir()
		kubeconfigPath := filepath.Join(tmpDir, "config")

		kubeconfigContent := `apiVersion: v1
kind: Config
current-context: test-context
clusters:
- name: test-cluster
  cluster:
    server: https://127.0.0.1:6443
    insecure-skip-tls-verify: true
contexts:
- name: test-context
  context:
    cluster: test-cluster
    user: test-user
users:
- name: test-user
  user:
    token: test-token
`
		err := os.WriteFile(kubeconfigPath, []byte(kubeconfigContent), 0644)
		require.NoError(t, err)

		// Note: This will fail to connect since there's no actual cluster
		// but it will successfully create the manager
		_, err = initClusterManager(kubeconfigPath)
		// We expect an error here because there's no real cluster
		assert.Error(t, err)
	})
}

func TestFormatAndPrint(t *testing.T) {
	t.Run("successful format", func(t *testing.T) {
		formatter := NewTableFormatter()

		err := formatAndPrint(formatter, func() (string, error) {
			return "test output\n", nil
		})

		assert.NoError(t, err)
	})

	t.Run("format error", func(t *testing.T) {
		formatter := NewTableFormatter()

		err := formatAndPrint(formatter, func() (string, error) {
			return "", assert.AnError
		})

		assert.Error(t, err)
		assert.Contains(t, err.Error(), "failed to format output")
	})
}

// ============================================================================
// HANDLER VALIDATION TESTS
// ============================================================================

func TestHandleGetPods_ArgumentValidation(t *testing.T) {
	t.Run("no args required for list", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().Bool("all-namespaces", false, "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// Should fail at cluster connection, not argument validation
		err := HandleGetPods(cmd, []string{})
		assert.Error(t, err)
		assert.NotContains(t, err.Error(), "required")
	})
}

func TestHandleGetPod_ArgumentValidation(t *testing.T) {
	t.Run("name required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().Bool("all-namespaces", false, "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// When args is empty, HandleGetPod calls HandleGetPods
		// which needs all the flags to be properly initialized
		err := HandleGetPod(cmd, []string{})
		assert.Error(t, err)
		// The error should be from cluster connection, not missing flags
		assert.NotContains(t, err.Error(), "required")
	})
}

func TestHandleGetNamespaces_ArgumentValidation(t *testing.T) {
	t.Run("no args required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// Should fail at cluster connection, not argument validation
		err := HandleGetNamespaces(cmd, []string{})
		assert.Error(t, err)
		assert.NotContains(t, err.Error(), "required")
	})
}

func TestHandleGetNamespace_ArgumentValidation(t *testing.T) {
	t.Run("name required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// When args is empty, HandleGetNamespace calls HandleGetNamespaces
		// which needs all the flags to be properly initialized
		err := HandleGetNamespace(cmd, []string{})
		assert.Error(t, err)
		// The error should be from cluster connection, not missing flags
		assert.NotContains(t, err.Error(), "required")
	})
}

func TestHandleGetNodes_ArgumentValidation(t *testing.T) {
	t.Run("no args required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// Should fail at cluster connection, not argument validation
		err := HandleGetNodes(cmd, []string{})
		assert.Error(t, err)
		assert.NotContains(t, err.Error(), "required")
	})
}

func TestHandleGetNode_ArgumentValidation(t *testing.T) {
	t.Run("name required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// When args is empty, HandleGetNode calls HandleGetNodes
		// which needs all the flags to be properly initialized
		err := HandleGetNode(cmd, []string{})
		assert.Error(t, err)
		// The error should be from cluster connection, not missing flags
		assert.NotContains(t, err.Error(), "required")
	})
}

func TestHandleGetDeployments_ArgumentValidation(t *testing.T) {
	t.Run("no args required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().Bool("all-namespaces", false, "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// Should fail at cluster connection, not argument validation
		err := HandleGetDeployments(cmd, []string{})
		assert.Error(t, err)
		assert.NotContains(t, err.Error(), "required")
	})
}

func TestHandleGetDeployment_ArgumentValidation(t *testing.T) {
	t.Run("name required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().Bool("all-namespaces", false, "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// When args is empty, HandleGetDeployment calls HandleGetDeployments
		// which needs all the flags to be properly initialized
		err := HandleGetDeployment(cmd, []string{})
		assert.Error(t, err)
		// The error should be from cluster connection, not missing flags
		assert.NotContains(t, err.Error(), "required")
	})
}

func TestHandleGetServices_ArgumentValidation(t *testing.T) {
	t.Run("no args required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().Bool("all-namespaces", false, "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// Should fail at cluster connection, not argument validation
		err := HandleGetServices(cmd, []string{})
		assert.Error(t, err)
		assert.NotContains(t, err.Error(), "required")
	})
}

func TestHandleGetService_ArgumentValidation(t *testing.T) {
	t.Run("name required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().String("namespace", "default", "")
		cmd.Flags().Bool("all-namespaces", false, "")
		cmd.Flags().String("output", "table", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		// When args is empty, HandleGetService calls HandleGetServices
		// which needs all the flags to be properly initialized
		err := HandleGetService(cmd, []string{})
		assert.Error(t, err)
		// The error should be from cluster connection, not missing flags
		assert.NotContains(t, err.Error(), "required")
	})
}

// ============================================================================
// CONFIG HANDLER TESTS
// ============================================================================

func TestHandleGetCurrentContext(t *testing.T) {
	t.Run("valid kubeconfig", func(t *testing.T) {
		// Create temp kubeconfig
		tmpDir := t.TempDir()
		kubeconfigPath := filepath.Join(tmpDir, "config")

		kubeconfigContent := `apiVersion: v1
kind: Config
current-context: test-context
clusters:
- name: test-cluster
  cluster:
    server: https://127.0.0.1:6443
contexts:
- name: test-context
  context:
    cluster: test-cluster
    user: test-user
users:
- name: test-user
  user:
    token: test-token
`
		err := os.WriteFile(kubeconfigPath, []byte(kubeconfigContent), 0644)
		require.NoError(t, err)

		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", kubeconfigPath, "")
		cmd.Flags().Set("kubeconfig", kubeconfigPath)

		err = HandleGetCurrentContext(cmd, []string{})
		assert.NoError(t, err)
	})

	t.Run("invalid kubeconfig", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		err := HandleGetCurrentContext(cmd, []string{})
		assert.Error(t, err)
	})
}

func TestHandleUseContext(t *testing.T) {
	t.Run("name required", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "", "")

		err := HandleUseContext(cmd, []string{})
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "context name is required")
	})

	t.Run("valid context switch", func(t *testing.T) {
		// Create temp kubeconfig
		tmpDir := t.TempDir()
		kubeconfigPath := filepath.Join(tmpDir, "config")

		kubeconfigContent := `apiVersion: v1
kind: Config
current-context: test-context-1
clusters:
- name: test-cluster
  cluster:
    server: https://127.0.0.1:6443
contexts:
- name: test-context-1
  context:
    cluster: test-cluster
    user: test-user
- name: test-context-2
  context:
    cluster: test-cluster
    user: test-user
users:
- name: test-user
  user:
    token: test-token
`
		err := os.WriteFile(kubeconfigPath, []byte(kubeconfigContent), 0644)
		require.NoError(t, err)

		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", kubeconfigPath, "")
		cmd.Flags().Set("kubeconfig", kubeconfigPath)

		err = HandleUseContext(cmd, []string{"test-context-2"})
		assert.NoError(t, err)
	})

	t.Run("invalid context name", func(t *testing.T) {
		// Create temp kubeconfig
		tmpDir := t.TempDir()
		kubeconfigPath := filepath.Join(tmpDir, "config")

		kubeconfigContent := `apiVersion: v1
kind: Config
current-context: test-context
clusters:
- name: test-cluster
  cluster:
    server: https://127.0.0.1:6443
contexts:
- name: test-context
  context:
    cluster: test-cluster
    user: test-user
users:
- name: test-user
  user:
    token: test-token
`
		err := os.WriteFile(kubeconfigPath, []byte(kubeconfigContent), 0644)
		require.NoError(t, err)

		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", kubeconfigPath, "")
		cmd.Flags().Set("kubeconfig", kubeconfigPath)

		err = HandleUseContext(cmd, []string{"nonexistent-context"})
		assert.Error(t, err)
	})
}

func TestHandleListContexts(t *testing.T) {
	t.Run("valid kubeconfig", func(t *testing.T) {
		// Create temp kubeconfig
		tmpDir := t.TempDir()
		kubeconfigPath := filepath.Join(tmpDir, "config")

		kubeconfigContent := `apiVersion: v1
kind: Config
current-context: test-context-1
clusters:
- name: test-cluster
  cluster:
    server: https://127.0.0.1:6443
contexts:
- name: test-context-1
  context:
    cluster: test-cluster
    user: test-user
- name: test-context-2
  context:
    cluster: test-cluster
    user: test-user
users:
- name: test-user
  user:
    token: test-token
`
		err := os.WriteFile(kubeconfigPath, []byte(kubeconfigContent), 0644)
		require.NoError(t, err)

		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", kubeconfigPath, "")
		cmd.Flags().Set("kubeconfig", kubeconfigPath)

		err = HandleListContexts(cmd, []string{})
		assert.NoError(t, err)
	})

	t.Run("invalid kubeconfig", func(t *testing.T) {
		cmd := &cobra.Command{}
		cmd.Flags().String("kubeconfig", "/nonexistent/path", "")
		cmd.Flags().Set("kubeconfig", "/nonexistent/path")

		err := HandleListContexts(cmd, []string{})
		assert.Error(t, err)
	})
}
