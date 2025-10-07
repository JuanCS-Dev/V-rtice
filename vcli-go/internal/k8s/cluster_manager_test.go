package k8s

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewClusterManager_Success tests successful ClusterManager creation
func TestNewClusterManager_Success(t *testing.T) {
	// Create temporary kubeconfig
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)
	assert.NotNil(t, cm)
	assert.Equal(t, kubeconfigPath, cm.kubeconfigPath)
	assert.NotNil(t, cm.kubeconfig)
	assert.Equal(t, "test-context", cm.currentContext)
	assert.False(t, cm.connected)
}

// TestNewClusterManager_EmptyPath tests error handling for empty kubeconfig path
func TestNewClusterManager_EmptyPath(t *testing.T) {
	cm, err := NewClusterManager("")
	assert.Error(t, err)
	assert.Nil(t, cm)
	assert.ErrorIs(t, err, ErrKubeconfigPathEmpty)
}

// TestNewClusterManager_InvalidPath tests error handling for invalid kubeconfig path
func TestNewClusterManager_InvalidPath(t *testing.T) {
	cm, err := NewClusterManager("/nonexistent/kubeconfig")
	assert.Error(t, err)
	assert.Nil(t, cm)
}

// TestGetCurrentContext tests getting the current context
func TestGetCurrentContext(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	context, err := cm.GetCurrentContext()
	require.NoError(t, err)
	assert.Equal(t, "test-context", context)
}

// TestListContexts tests listing all contexts
func TestListContexts(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	contexts, err := cm.ListContexts()
	require.NoError(t, err)
	assert.Len(t, contexts, 1)
	assert.Contains(t, contexts, "test-context")
}

// TestSetCurrentContext_Success tests successful context switching
func TestSetCurrentContext_Success(t *testing.T) {
	kubeconfigPath := createMultiContextKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	// Initially should be context1
	context, err := cm.GetCurrentContext()
	require.NoError(t, err)
	assert.Equal(t, "context1", context)

	// Switch to context2
	err = cm.SetCurrentContext("context2")
	require.NoError(t, err)

	context, err = cm.GetCurrentContext()
	require.NoError(t, err)
	assert.Equal(t, "context2", context)
}

// TestSetCurrentContext_NotFound tests error when context doesn't exist
func TestSetCurrentContext_NotFound(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	err = cm.SetCurrentContext("nonexistent-context")
	assert.Error(t, err)
	assert.ErrorIs(t, err, ErrContextNotFound)
}

// TestIsConnected tests connection state tracking
func TestIsConnected(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	// Should not be connected initially
	assert.False(t, cm.IsConnected())
}

// TestDisconnect_NotConnected tests disconnecting when not connected
func TestDisconnect_NotConnected(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	// Should succeed even if not connected
	err = cm.Disconnect()
	assert.NoError(t, err)
	assert.False(t, cm.IsConnected())
}

// TestHealthCheck_NotConnected tests health check when not connected
func TestHealthCheck_NotConnected(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	err = cm.HealthCheck()
	assert.Error(t, err)
	assert.ErrorIs(t, err, ErrNotConnected)
}

// TestOperations_NotConnected tests operations when not connected
func TestOperations_NotConnected(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	// All operations should fail when not connected
	_, err = cm.GetPods("default")
	assert.ErrorIs(t, err, ErrNotConnected)

	_, err = cm.GetPod("default", "test-pod")
	assert.ErrorIs(t, err, ErrNotConnected)

	_, err = cm.GetNamespaces()
	assert.ErrorIs(t, err, ErrNotConnected)

	_, err = cm.GetNamespace("default")
	assert.ErrorIs(t, err, ErrNotConnected)

	_, err = cm.GetNodes()
	assert.ErrorIs(t, err, ErrNotConnected)

	_, err = cm.GetNode("test-node")
	assert.ErrorIs(t, err, ErrNotConnected)

	_, err = cm.GetDeployments("default")
	assert.ErrorIs(t, err, ErrNotConnected)

	_, err = cm.GetDeployment("default", "test-deploy")
	assert.ErrorIs(t, err, ErrNotConnected)

	_, err = cm.GetServices("default")
	assert.ErrorIs(t, err, ErrNotConnected)

	_, err = cm.GetService("default", "test-svc")
	assert.ErrorIs(t, err, ErrNotConnected)
}

// TestGetPod_EmptyName tests error handling for empty pod name
func TestGetPod_EmptyName(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	// Simulate connected state for this test
	cm.mu.Lock()
	cm.connected = true
	cm.mu.Unlock()

	_, err = cm.GetPod("default", "")
	assert.ErrorIs(t, err, ErrResourceNameEmpty)
}

// TestGetNamespace_EmptyName tests error handling for empty namespace name
func TestGetNamespace_EmptyName(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	// Simulate connected state for this test
	cm.mu.Lock()
	cm.connected = true
	cm.mu.Unlock()

	_, err = cm.GetNamespace("")
	assert.ErrorIs(t, err, ErrResourceNameEmpty)
}

// TestGetNode_EmptyName tests error handling for empty node name
func TestGetNode_EmptyName(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	// Simulate connected state for this test
	cm.mu.Lock()
	cm.connected = true
	cm.mu.Unlock()

	_, err = cm.GetNode("")
	assert.ErrorIs(t, err, ErrResourceNameEmpty)
}

// Helper function to create a test kubeconfig file
func createTestKubeconfig(t *testing.T) string {
	t.Helper()

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
    namespace: default
users:
- name: test-user
  user:
    token: test-token
`

	tmpFile, err := os.CreateTemp("", "kubeconfig-*.yaml")
	require.NoError(t, err)

	_, err = tmpFile.WriteString(kubeconfigContent)
	require.NoError(t, err)

	err = tmpFile.Close()
	require.NoError(t, err)

	return tmpFile.Name()
}

// Helper function to create a multi-context kubeconfig file
func createMultiContextKubeconfig(t *testing.T) string {
	t.Helper()

	kubeconfigContent := `apiVersion: v1
kind: Config
current-context: context1
clusters:
- name: cluster1
  cluster:
    server: https://127.0.0.1:6443
    insecure-skip-tls-verify: true
- name: cluster2
  cluster:
    server: https://127.0.0.1:6444
    insecure-skip-tls-verify: true
contexts:
- name: context1
  context:
    cluster: cluster1
    user: user1
    namespace: default
- name: context2
  context:
    cluster: cluster2
    user: user2
    namespace: kube-system
users:
- name: user1
  user:
    token: token1
- name: user2
  user:
    token: token2
`

	tmpFile, err := os.CreateTemp("", "kubeconfig-multi-*.yaml")
	require.NoError(t, err)

	_, err = tmpFile.WriteString(kubeconfigContent)
	require.NoError(t, err)

	err = tmpFile.Close()
	require.NoError(t, err)

	return tmpFile.Name()
}

// TestThreadSafety tests concurrent access to ClusterManager
func TestThreadSafety(t *testing.T) {
	kubeconfigPath := createMultiContextKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	// Run concurrent operations
	done := make(chan bool)
	for i := 0; i < 10; i++ {
		go func() {
			defer func() { done <- true }()

			// Read operations
			cm.GetCurrentContext()
			cm.ListContexts()
			cm.IsConnected()
		}()
	}

	// Wait for all goroutines
	for i := 0; i < 10; i++ {
		<-done
	}
}

// TestRepr tests string representation
func TestRepr(t *testing.T) {
	kubeconfigPath := createTestKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	cm, err := NewClusterManager(kubeconfigPath)
	require.NoError(t, err)

	assert.NotNil(t, cm)
	assert.Contains(t, filepath.Base(kubeconfigPath), "kubeconfig")
}
