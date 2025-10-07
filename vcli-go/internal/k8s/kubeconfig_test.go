package k8s

import (
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestLoadKubeconfig_Success tests successful kubeconfig loading
func TestLoadKubeconfig_Success(t *testing.T) {
	kubeconfigPath := createValidKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	require.NoError(t, err)
	assert.NotNil(t, kc)
	assert.NotNil(t, kc.rawConfig)
	assert.NotNil(t, kc.clientConfig)
	assert.Equal(t, kubeconfigPath, kc.kubeconfigPath)
}

// TestLoadKubeconfig_FileNotFound tests error for missing file
func TestLoadKubeconfig_FileNotFound(t *testing.T) {
	kc, err := LoadKubeconfig("/nonexistent/kubeconfig")
	assert.Error(t, err)
	assert.Nil(t, kc)
	assert.ErrorIs(t, err, ErrKubeconfigFileNotFound)
}

// TestLoadKubeconfig_InvalidYAML tests error for invalid YAML
func TestLoadKubeconfig_InvalidYAML(t *testing.T) {
	kubeconfigPath := createInvalidKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	assert.Error(t, err)
	assert.Nil(t, kc)
}

// TestLoadKubeconfig_NoContexts tests error for kubeconfig without contexts
func TestLoadKubeconfig_NoContexts(t *testing.T) {
	kubeconfigPath := createNoContextsKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	assert.Error(t, err)
	assert.Nil(t, kc)
	assert.ErrorIs(t, err, ErrKubeconfigInvalid)
}

// TestLoadKubeconfig_NoCurrentContext tests error for missing current-context
func TestLoadKubeconfig_NoCurrentContext(t *testing.T) {
	kubeconfigPath := createNoCurrentContextKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	assert.Error(t, err)
	assert.Nil(t, kc)
	assert.ErrorIs(t, err, ErrNoCurrentContext)
}

// TestHasContext tests context existence check
func TestHasContext(t *testing.T) {
	kubeconfigPath := createMultiContextKubeconfigForTest(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	require.NoError(t, err)

	assert.True(t, kc.HasContext("context1"))
	assert.True(t, kc.HasContext("context2"))
	assert.False(t, kc.HasContext("nonexistent"))
}

// TestKubeconfig_ListContexts tests listing all contexts
func TestKubeconfig_ListContexts(t *testing.T) {
	kubeconfigPath := createMultiContextKubeconfigForTest(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	require.NoError(t, err)

	contexts := kc.ListContexts()
	assert.Len(t, contexts, 2)
	assert.Contains(t, contexts, "context1")
	assert.Contains(t, contexts, "context2")
}

// TestKubeconfig_GetCurrentContext tests getting current context
func TestKubeconfig_GetCurrentContext(t *testing.T) {
	kubeconfigPath := createValidKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	require.NoError(t, err)

	currentContext := kc.GetCurrentContext()
	assert.Equal(t, "test-context", currentContext)
}

// TestBuildRESTConfig_Success tests successful REST config building
func TestBuildRESTConfig_Success(t *testing.T) {
	kubeconfigPath := createValidKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	require.NoError(t, err)

	config, err := kc.BuildRESTConfig("test-context")
	require.NoError(t, err)
	assert.NotNil(t, config)
	assert.Equal(t, "https://127.0.0.1:6443", config.Host)
}

// TestBuildRESTConfig_ContextNotFound tests error for missing context
func TestBuildRESTConfig_ContextNotFound(t *testing.T) {
	kubeconfigPath := createValidKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	require.NoError(t, err)

	config, err := kc.BuildRESTConfig("nonexistent")
	assert.Error(t, err)
	assert.Nil(t, config)
	assert.ErrorIs(t, err, ErrContextNotFound)
}

// TestGetContextInfo_Success tests getting context information
func TestGetContextInfo_Success(t *testing.T) {
	kubeconfigPath := createValidKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	require.NoError(t, err)

	info, err := kc.GetContextInfo("test-context")
	require.NoError(t, err)
	assert.NotNil(t, info)
	assert.Equal(t, "test-context", info.Name)
	assert.Equal(t, "test-cluster", info.ClusterName)
	assert.Equal(t, "https://127.0.0.1:6443", info.ClusterServer)
	assert.Equal(t, "test-user", info.UserName)
	assert.Equal(t, "default", info.Namespace)
	assert.True(t, info.HasToken)
	assert.False(t, info.HasCertificate)
}

// TestGetContextInfo_ContextNotFound tests error for missing context
func TestGetContextInfo_ContextNotFound(t *testing.T) {
	kubeconfigPath := createValidKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	require.NoError(t, err)

	info, err := kc.GetContextInfo("nonexistent")
	assert.Error(t, err)
	assert.Nil(t, info)
	assert.ErrorIs(t, err, ErrContextNotFound)
}

// TestGetContextInfo_DefaultNamespace tests default namespace assignment
func TestGetContextInfo_DefaultNamespace(t *testing.T) {
	kubeconfigPath := createNoNamespaceKubeconfig(t)
	defer os.Remove(kubeconfigPath)

	kc, err := LoadKubeconfig(kubeconfigPath)
	require.NoError(t, err)

	info, err := kc.GetContextInfo("test-context")
	require.NoError(t, err)
	assert.Equal(t, "default", info.Namespace) // Should default to "default"
}

// Helper: Create valid kubeconfig
func createValidKubeconfig(t *testing.T) string {
	t.Helper()

	content := `apiVersion: v1
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
    token: test-token-12345
`

	tmpFile, err := os.CreateTemp("", "kubeconfig-valid-*.yaml")
	require.NoError(t, err)
	_, err = tmpFile.WriteString(content)
	require.NoError(t, err)
	tmpFile.Close()
	return tmpFile.Name()
}

// Helper: Create invalid YAML kubeconfig
func createInvalidKubeconfig(t *testing.T) string {
	t.Helper()

	content := `invalid: yaml: content:
  - this is not
  valid YAML
    structure
`

	tmpFile, err := os.CreateTemp("", "kubeconfig-invalid-*.yaml")
	require.NoError(t, err)
	_, err = tmpFile.WriteString(content)
	require.NoError(t, err)
	tmpFile.Close()
	return tmpFile.Name()
}

// Helper: Create kubeconfig without contexts
func createNoContextsKubeconfig(t *testing.T) string {
	t.Helper()

	content := `apiVersion: v1
kind: Config
clusters:
- name: test-cluster
  cluster:
    server: https://127.0.0.1:6443
users:
- name: test-user
  user:
    token: test-token
`

	tmpFile, err := os.CreateTemp("", "kubeconfig-nocontexts-*.yaml")
	require.NoError(t, err)
	_, err = tmpFile.WriteString(content)
	require.NoError(t, err)
	tmpFile.Close()
	return tmpFile.Name()
}

// Helper: Create kubeconfig without current-context
func createNoCurrentContextKubeconfig(t *testing.T) string {
	t.Helper()

	content := `apiVersion: v1
kind: Config
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

	tmpFile, err := os.CreateTemp("", "kubeconfig-nocurrent-*.yaml")
	require.NoError(t, err)
	_, err = tmpFile.WriteString(content)
	require.NoError(t, err)
	tmpFile.Close()
	return tmpFile.Name()
}

// Helper: Create multi-context kubeconfig
func createMultiContextKubeconfigForTest(t *testing.T) string {
	t.Helper()

	content := `apiVersion: v1
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
	_, err = tmpFile.WriteString(content)
	require.NoError(t, err)
	tmpFile.Close()
	return tmpFile.Name()
}

// Helper: Create kubeconfig without namespace
func createNoNamespaceKubeconfig(t *testing.T) string {
	t.Helper()

	content := `apiVersion: v1
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

	tmpFile, err := os.CreateTemp("", "kubeconfig-nonamespace-*.yaml")
	require.NoError(t, err)
	_, err = tmpFile.WriteString(content)
	require.NoError(t, err)
	tmpFile.Close()
	return tmpFile.Name()
}
