package integration

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// TestIntegration_ClusterConnection tests connecting to the kind cluster
func TestIntegration_ClusterConnection(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	kubeconfigPath := getTestKubeconfigPath(t)

	manager, err := k8s.NewClusterManager(kubeconfigPath)
	require.NoError(t, err, "should create cluster manager")
	require.NotNil(t, manager, "manager should not be nil")

	err = manager.Connect()
	require.NoError(t, err, "should connect to cluster")
	defer manager.Disconnect()

	// Verify health check
	err = manager.HealthCheck()
	assert.NoError(t, err, "cluster should be healthy")
}

// TestIntegration_GetNamespaces tests listing namespaces
func TestIntegration_GetNamespaces(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	namespaces, err := manager.GetNamespaces()
	require.NoError(t, err, "should get namespaces")
	require.NotEmpty(t, namespaces, "should have namespaces")

	// Verify required namespaces exist
	namespaceNames := make(map[string]bool)
	for _, ns := range namespaces {
		namespaceNames[ns.Name] = true
	}

	assert.True(t, namespaceNames["default"], "should have default namespace")
	assert.True(t, namespaceNames["kube-system"], "should have kube-system namespace")
	assert.True(t, namespaceNames["test-namespace"], "should have test-namespace")
	assert.True(t, namespaceNames["production"], "should have production namespace")
	assert.True(t, namespaceNames["staging"], "should have staging namespace")
}

// TestIntegration_GetNamespace tests getting a single namespace
func TestIntegration_GetNamespace(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	ns, err := manager.GetNamespace("default")
	require.NoError(t, err, "should get default namespace")
	assert.Equal(t, "default", ns.Name, "namespace name should match")
	assert.Equal(t, "Active", ns.Status, "namespace should be active")
	assert.NotZero(t, ns.CreatedAt, "namespace should have creation time")
}

// TestIntegration_GetPodsInNamespace tests listing pods in a namespace
func TestIntegration_GetPodsInNamespace(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	// Get pods in default namespace
	pods, err := manager.GetPods("default")
	require.NoError(t, err, "should get pods in default namespace")
	require.NotEmpty(t, pods, "should have pods in default namespace")

	// Verify nginx deployment pods exist
	found := false
	for _, pod := range pods {
		if pod.Namespace == "default" && pod.Phase == "Running" {
			found = true
			assert.NotEmpty(t, pod.Name, "pod should have name")
			assert.NotEmpty(t, pod.NodeName, "pod should be scheduled on node")
			assert.NotEmpty(t, pod.PodIP, "running pod should have IP")
			break
		}
	}
	assert.True(t, found, "should find at least one running pod in default namespace")
}

// TestIntegration_GetPodsAllNamespaces tests listing pods across all namespaces
func TestIntegration_GetPodsAllNamespaces(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	// Get pods across all namespaces (empty string means all)
	pods, err := manager.GetPods("")
	require.NoError(t, err, "should get pods across all namespaces")
	require.NotEmpty(t, pods, "should have pods")

	// Count pods in different namespaces
	namespaces := make(map[string]int)
	for _, pod := range pods {
		namespaces[pod.Namespace]++
	}

	// We should have pods in multiple namespaces
	assert.GreaterOrEqual(t, len(namespaces), 3, "should have pods in at least 3 namespaces")
	assert.Greater(t, namespaces["default"], 0, "should have pods in default")
	assert.Greater(t, namespaces["test-namespace"], 0, "should have pods in test-namespace")
	assert.Greater(t, namespaces["production"], 0, "should have pods in production")
}

// TestIntegration_GetPod tests getting a single pod
func TestIntegration_GetPod(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	// First get all pods to find a name
	pods, err := manager.GetPods("default")
	require.NoError(t, err, "should get pods")
	require.NotEmpty(t, pods, "should have pods")

	// Get the first pod
	podName := pods[0].Name
	pod, err := manager.GetPod("default", podName)
	require.NoError(t, err, "should get pod")
	assert.Equal(t, podName, pod.Name, "pod name should match")
	assert.Equal(t, "default", pod.Namespace, "pod namespace should match")
	assert.NotEmpty(t, pod.Phase, "pod should have phase")
}

// TestIntegration_GetNodes tests listing nodes
func TestIntegration_GetNodes(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	nodes, err := manager.GetNodes()
	require.NoError(t, err, "should get nodes")
	require.NotEmpty(t, nodes, "should have at least one node")

	// Verify node properties
	node := nodes[0]
	assert.NotEmpty(t, node.Name, "node should have name")
	assert.NotEmpty(t, node.Status, "node should have status")
	assert.NotEmpty(t, node.Version, "node should have version")
	assert.NotZero(t, node.CreatedAt, "node should have creation time")
}

// TestIntegration_GetNode tests getting a single node
func TestIntegration_GetNode(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	// First get all nodes to find a name
	nodes, err := manager.GetNodes()
	require.NoError(t, err, "should get nodes")
	require.NotEmpty(t, nodes, "should have nodes")

	// Get the first node
	nodeName := nodes[0].Name
	node, err := manager.GetNode(nodeName)
	require.NoError(t, err, "should get node")
	assert.Equal(t, nodeName, node.Name, "node name should match")
	assert.NotEmpty(t, node.Status, "node should have status")
}

// TestIntegration_GetDeploymentsInNamespace tests listing deployments in a namespace
func TestIntegration_GetDeploymentsInNamespace(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	// Get deployments in test-namespace
	deployments, err := manager.GetDeployments("test-namespace")
	require.NoError(t, err, "should get deployments in test-namespace")
	require.NotEmpty(t, deployments, "should have deployments in test-namespace")

	// Verify api-deployment exists
	found := false
	for _, deploy := range deployments {
		if deploy.Name == "api-deployment" && deploy.Namespace == "test-namespace" {
			found = true
			assert.Equal(t, int32(3), deploy.Replicas, "should have 3 replicas")
			assert.Equal(t, int32(3), deploy.ReadyReplicas, "all replicas should be ready")
			break
		}
	}
	assert.True(t, found, "should find api-deployment in test-namespace")
}

// TestIntegration_GetDeploymentsAllNamespaces tests listing deployments across all namespaces
func TestIntegration_GetDeploymentsAllNamespaces(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	// Get deployments across all namespaces
	deployments, err := manager.GetDeployments("")
	require.NoError(t, err, "should get deployments across all namespaces")
	require.NotEmpty(t, deployments, "should have deployments")

	// Count deployments in different namespaces
	namespaces := make(map[string]int)
	for _, deploy := range deployments {
		namespaces[deploy.Namespace]++
	}

	// We should have deployments in multiple namespaces
	assert.Greater(t, namespaces["default"], 0, "should have deployments in default")
	assert.Greater(t, namespaces["test-namespace"], 0, "should have deployments in test-namespace")
	assert.Greater(t, namespaces["production"], 0, "should have deployments in production")
}

// TestIntegration_GetDeployment tests getting a single deployment
func TestIntegration_GetDeployment(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	deployment, err := manager.GetDeployment("default", "nginx-deployment")
	require.NoError(t, err, "should get nginx-deployment")
	assert.Equal(t, "nginx-deployment", deployment.Name, "deployment name should match")
	assert.Equal(t, "default", deployment.Namespace, "deployment namespace should match")
	assert.Equal(t, int32(2), deployment.Replicas, "should have 2 replicas")
}

// TestIntegration_GetServicesInNamespace tests listing services in a namespace
func TestIntegration_GetServicesInNamespace(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	// Get services in default namespace
	services, err := manager.GetServices("default")
	require.NoError(t, err, "should get services in default namespace")
	require.NotEmpty(t, services, "should have services in default namespace")

	// Verify nginx-service exists
	found := false
	for _, svc := range services {
		if svc.Name == "nginx-service" && svc.Namespace == "default" {
			found = true
			assert.Equal(t, "ClusterIP", string(svc.Type), "should be ClusterIP type")
			assert.NotEmpty(t, svc.ClusterIP, "should have cluster IP")
			assert.NotEmpty(t, svc.Ports, "should have ports")
			break
		}
	}
	assert.True(t, found, "should find nginx-service in default namespace")
}

// TestIntegration_GetServicesAllNamespaces tests listing services across all namespaces
func TestIntegration_GetServicesAllNamespaces(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	// Get services across all namespaces
	services, err := manager.GetServices("")
	require.NoError(t, err, "should get services across all namespaces")
	require.NotEmpty(t, services, "should have services")

	// Count services in different namespaces
	namespaces := make(map[string]int)
	for _, svc := range services {
		namespaces[svc.Namespace]++
	}

	// We should have services in multiple namespaces
	assert.Greater(t, namespaces["default"], 0, "should have services in default")
	assert.Greater(t, namespaces["test-namespace"], 0, "should have services in test-namespace")
	assert.Greater(t, namespaces["production"], 0, "should have services in production")
}

// TestIntegration_GetService tests getting a single service
func TestIntegration_GetService(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	service, err := manager.GetService("test-namespace", "api-service")
	require.NoError(t, err, "should get api-service")
	assert.Equal(t, "api-service", service.Name, "service name should match")
	assert.Equal(t, "test-namespace", service.Namespace, "service namespace should match")
	assert.Equal(t, "NodePort", string(service.Type), "should be NodePort type")
	assert.NotEmpty(t, service.ClusterIP, "should have cluster IP")
}

// TestIntegration_ContextManagement tests context operations
func TestIntegration_ContextManagement(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	kubeconfigPath := getTestKubeconfigPath(t)

	manager, err := k8s.NewClusterManager(kubeconfigPath)
	require.NoError(t, err, "should create cluster manager")

	// Get current context
	currentContext, err := manager.GetCurrentContext()
	require.NoError(t, err, "should get current context")
	assert.NotEmpty(t, currentContext, "current context should not be empty")
	assert.Equal(t, "kind-vcli-test", currentContext, "context should be kind-vcli-test")

	// List contexts
	contexts, err := manager.ListContexts()
	require.NoError(t, err, "should list contexts")
	require.NotEmpty(t, contexts, "should have at least one context")
	assert.Contains(t, contexts, "kind-vcli-test", "should contain kind-vcli-test context")
}

// Test_Integration_ErrorHandling tests error conditions
func TestIntegration_ErrorHandling(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	manager := setupTestCluster(t)
	defer manager.Disconnect()

	t.Run("get non-existent pod", func(t *testing.T) {
		_, err := manager.GetPod("default", "non-existent-pod")
		assert.Error(t, err, "should error on non-existent pod")
	})

	t.Run("get non-existent namespace", func(t *testing.T) {
		_, err := manager.GetNamespace("non-existent-namespace")
		assert.Error(t, err, "should error on non-existent namespace")
	})

	t.Run("get non-existent deployment", func(t *testing.T) {
		_, err := manager.GetDeployment("default", "non-existent-deployment")
		assert.Error(t, err, "should error on non-existent deployment")
	})

	t.Run("get non-existent service", func(t *testing.T) {
		_, err := manager.GetService("default", "non-existent-service")
		assert.Error(t, err, "should error on non-existent service")
	})
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

// setupTestCluster creates and connects to the test cluster
func setupTestCluster(t *testing.T) *k8s.ClusterManager {
	t.Helper()

	kubeconfigPath := getTestKubeconfigPath(t)

	manager, err := k8s.NewClusterManager(kubeconfigPath)
	require.NoError(t, err, "should create cluster manager")

	err = manager.Connect()
	require.NoError(t, err, "should connect to cluster")

	return manager
}

// getTestKubeconfigPath returns the path to the test kubeconfig
func getTestKubeconfigPath(t *testing.T) string {
	t.Helper()

	// Get the test kubeconfig path relative to the test file
	kubeconfigPath := filepath.Join("kubeconfig")

	// Check if file exists
	if _, err := os.Stat(kubeconfigPath); os.IsNotExist(err) {
		t.Fatalf("test kubeconfig not found at %s. Run integration setup first.", kubeconfigPath)
	}

	absPath, err := filepath.Abs(kubeconfigPath)
	require.NoError(t, err, "should get absolute path")

	return absPath
}
