package k8s

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes/fake"
)

// ============================================================================
// TEST HELPERS
// ============================================================================

// newTestClusterManager creates a ClusterManager with a fake clientset for testing
func newTestClusterManager(objects ...runtime.Object) *ClusterManager {
	fakeClientset := fake.NewSimpleClientset(objects...)

	return &ClusterManager{
		clientset: fakeClientset, // Now works directly since clientset is kubernetes.Interface
		connected: true,
	}
}

// createTestPod creates a test pod object
func createTestPod(name, namespace, phase string) *corev1.Pod {
	return &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels: map[string]string{
				"app": "test",
			},
		},
		Spec: corev1.PodSpec{
			NodeName: "test-node",
			Containers: []corev1.Container{
				{
					Name:  "nginx",
					Image: "nginx:latest",
				},
			},
		},
		Status: corev1.PodStatus{
			Phase:  corev1.PodPhase(phase),
			PodIP:  "10.0.0.1",
			HostIP: "192.168.1.1",
			ContainerStatuses: []corev1.ContainerStatus{
				{
					Name:  "nginx",
					Image: "nginx:latest",
					Ready: phase == "Running",
					State: corev1.ContainerState{
						Running: &corev1.ContainerStateRunning{},
					},
				},
			},
		},
	}
}

// createTestNamespace creates a test namespace object
func createTestNamespace(name string) *corev1.Namespace {
	return &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name: name,
			Labels: map[string]string{
				"env": "test",
			},
		},
		Status: corev1.NamespaceStatus{
			Phase: corev1.NamespaceActive,
		},
	}
}

// createTestNode creates a test node object
func createTestNode(name string, ready bool) *corev1.Node {
	condition := corev1.ConditionTrue
	if !ready {
		condition = corev1.ConditionFalse
	}

	return &corev1.Node{
		ObjectMeta: metav1.ObjectMeta{
			Name: name,
			Labels: map[string]string{
				"node-role.kubernetes.io/worker": "",
			},
		},
		Status: corev1.NodeStatus{
			Conditions: []corev1.NodeCondition{
				{
					Type:   corev1.NodeReady,
					Status: condition,
				},
			},
			NodeInfo: corev1.NodeSystemInfo{
				KubeletVersion:          "v1.28.0",
				OSImage:                 "Ubuntu 22.04",
				KernelVersion:           "5.15.0",
				ContainerRuntimeVersion: "containerd://1.7.2",
			},
		},
	}
}

// createTestDeployment creates a test deployment object
func createTestDeployment(name, namespace string, replicas int32) *appsv1.Deployment {
	return &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels: map[string]string{
				"app": "test",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{
					"app": "test",
				},
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						"app": "test",
					},
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "nginx",
							Image: "nginx:latest",
						},
					},
				},
			},
		},
		Status: appsv1.DeploymentStatus{
			Replicas:          replicas,
			ReadyReplicas:     replicas,
			UpdatedReplicas:   replicas,
			AvailableReplicas: replicas,
		},
	}
}

// createTestService creates a test service object
func createTestService(name, namespace string) *corev1.Service {
	return &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels: map[string]string{
				"app": "test",
			},
		},
		Spec: corev1.ServiceSpec{
			Type:      corev1.ServiceTypeClusterIP,
			ClusterIP: "10.96.0.1",
			Selector: map[string]string{
				"app": "test",
			},
			Ports: []corev1.ServicePort{
				{
					Name:     "http",
					Protocol: corev1.ProtocolTCP,
					Port:     80,
				},
			},
		},
	}
}

// createTestConfigMap creates a test configmap object
func createTestConfigMap(name, namespace string) *corev1.ConfigMap {
	return &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels: map[string]string{
				"app": "test",
			},
		},
		Data: map[string]string{
			"key1": "value1",
			"key2": "value2",
		},
	}
}

// createTestSecret creates a test secret object
func createTestSecret(name, namespace string) *corev1.Secret {
	return &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels: map[string]string{
				"app": "test",
			},
		},
		Type: corev1.SecretTypeOpaque,
		Data: map[string][]byte{
			"username": []byte("admin"),
			"password": []byte("secret"),
		},
	}
}

// ============================================================================
// PODS TESTS
// ============================================================================

func TestGetPods(t *testing.T) {
	t.Run("get pods from specific namespace", func(t *testing.T) {
		pod1 := createTestPod("pod-1", "default", "Running")
		pod2 := createTestPod("pod-2", "default", "Pending")
		pod3 := createTestPod("pod-3", "kube-system", "Running")

		cm := newTestClusterManager(pod1, pod2, pod3)

		pods, err := cm.GetPods("default")
		require.NoError(t, err)
		assert.Len(t, pods, 2)
		assert.Equal(t, "pod-1", pods[0].Name)
		assert.Equal(t, "pod-2", pods[1].Name)
	})

	t.Run("get pods from all namespaces", func(t *testing.T) {
		pod1 := createTestPod("pod-1", "default", "Running")
		pod2 := createTestPod("pod-2", "kube-system", "Running")

		cm := newTestClusterManager(pod1, pod2)

		pods, err := cm.GetPods("") // Empty namespace means all
		require.NoError(t, err)
		assert.Len(t, pods, 2)
	})

	t.Run("no pods found", func(t *testing.T) {
		cm := newTestClusterManager()

		pods, err := cm.GetPods("default")
		require.NoError(t, err)
		assert.Len(t, pods, 0)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		pods, err := cm.GetPods("default")
		assert.Error(t, err)
		assert.Nil(t, pods)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

func TestGetPod(t *testing.T) {
	t.Run("get existing pod", func(t *testing.T) {
		pod := createTestPod("test-pod", "default", "Running")
		cm := newTestClusterManager(pod)

		result, err := cm.GetPod("default", "test-pod")
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "test-pod", result.Name)
		assert.Equal(t, "default", result.Namespace)
		assert.Equal(t, "Running", result.Status)
	})

	t.Run("pod not found", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetPod("default", "nonexistent")
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("empty namespace defaults to default", func(t *testing.T) {
		pod := createTestPod("test-pod", "default", "Running")
		cm := newTestClusterManager(pod)

		result, err := cm.GetPod("", "test-pod")
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "test-pod", result.Name)
	})

	t.Run("empty name returns error", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetPod("default", "")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrResourceNameEmpty)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		result, err := cm.GetPod("default", "test-pod")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// NAMESPACES TESTS
// ============================================================================

func TestGetNamespaces(t *testing.T) {
	t.Run("get all namespaces", func(t *testing.T) {
		ns1 := createTestNamespace("default")
		ns2 := createTestNamespace("kube-system")
		ns3 := createTestNamespace("kube-public")

		cm := newTestClusterManager(ns1, ns2, ns3)

		namespaces, err := cm.GetNamespaces()
		require.NoError(t, err)
		assert.Len(t, namespaces, 3)
	})

	t.Run("no namespaces found", func(t *testing.T) {
		cm := newTestClusterManager()

		namespaces, err := cm.GetNamespaces()
		require.NoError(t, err)
		assert.Len(t, namespaces, 0)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		namespaces, err := cm.GetNamespaces()
		assert.Error(t, err)
		assert.Nil(t, namespaces)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

func TestGetNamespace(t *testing.T) {
	t.Run("get existing namespace", func(t *testing.T) {
		ns := createTestNamespace("production")
		cm := newTestClusterManager(ns)

		result, err := cm.GetNamespace("production")
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "production", result.Name)
		assert.Equal(t, "Active", result.Status)
	})

	t.Run("namespace not found", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetNamespace("nonexistent")
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("empty name returns error", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetNamespace("")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrResourceNameEmpty)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		result, err := cm.GetNamespace("default")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// NODES TESTS
// ============================================================================

func TestGetNodes(t *testing.T) {
	t.Run("get all nodes", func(t *testing.T) {
		node1 := createTestNode("worker-1", true)
		node2 := createTestNode("worker-2", true)
		node3 := createTestNode("worker-3", false)

		cm := newTestClusterManager(node1, node2, node3)

		nodes, err := cm.GetNodes()
		require.NoError(t, err)
		assert.Len(t, nodes, 3)

		// Check that ready nodes are marked as Ready
		readyCount := 0
		for _, node := range nodes {
			if node.Status == "Ready" {
				readyCount++
			}
		}
		assert.Equal(t, 2, readyCount)
	})

	t.Run("no nodes found", func(t *testing.T) {
		cm := newTestClusterManager()

		nodes, err := cm.GetNodes()
		require.NoError(t, err)
		assert.Len(t, nodes, 0)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		nodes, err := cm.GetNodes()
		assert.Error(t, err)
		assert.Nil(t, nodes)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

func TestGetNode(t *testing.T) {
	t.Run("get existing node", func(t *testing.T) {
		node := createTestNode("worker-1", true)
		cm := newTestClusterManager(node)

		result, err := cm.GetNode("worker-1")
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "worker-1", result.Name)
		assert.Equal(t, "Ready", result.Status)
		assert.Equal(t, "v1.28.0", result.Version)
	})

	t.Run("node not found", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetNode("nonexistent")
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("empty name returns error", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetNode("")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrResourceNameEmpty)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		result, err := cm.GetNode("worker-1")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// DEPLOYMENTS TESTS
// ============================================================================

func TestGetDeployments(t *testing.T) {
	t.Run("get deployments from specific namespace", func(t *testing.T) {
		deploy1 := createTestDeployment("nginx", "default", 3)
		deploy2 := createTestDeployment("redis", "default", 1)
		deploy3 := createTestDeployment("postgres", "database", 1)

		cm := newTestClusterManager(deploy1, deploy2, deploy3)

		deployments, err := cm.GetDeployments("default")
		require.NoError(t, err)
		assert.Len(t, deployments, 2)
	})

	t.Run("get deployments from all namespaces", func(t *testing.T) {
		deploy1 := createTestDeployment("nginx", "default", 3)
		deploy2 := createTestDeployment("postgres", "database", 1)

		cm := newTestClusterManager(deploy1, deploy2)

		deployments, err := cm.GetDeployments("")
		require.NoError(t, err)
		assert.Len(t, deployments, 2)
	})

	t.Run("no deployments found", func(t *testing.T) {
		cm := newTestClusterManager()

		deployments, err := cm.GetDeployments("default")
		require.NoError(t, err)
		assert.Len(t, deployments, 0)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		deployments, err := cm.GetDeployments("default")
		assert.Error(t, err)
		assert.Nil(t, deployments)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

func TestGetDeployment(t *testing.T) {
	t.Run("get existing deployment", func(t *testing.T) {
		deploy := createTestDeployment("nginx", "default", 3)
		cm := newTestClusterManager(deploy)

		result, err := cm.GetDeployment("default", "nginx")
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "nginx", result.Name)
		assert.Equal(t, "default", result.Namespace)
		assert.Equal(t, int32(3), result.Replicas)
	})

	t.Run("deployment not found", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetDeployment("default", "nonexistent")
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("empty namespace defaults to default", func(t *testing.T) {
		deploy := createTestDeployment("nginx", "default", 3)
		cm := newTestClusterManager(deploy)

		result, err := cm.GetDeployment("", "nginx")
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "nginx", result.Name)
	})

	t.Run("empty name returns error", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetDeployment("default", "")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrResourceNameEmpty)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		result, err := cm.GetDeployment("default", "nginx")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// SERVICES TESTS
// ============================================================================

func TestGetServices(t *testing.T) {
	t.Run("get services from specific namespace", func(t *testing.T) {
		svc1 := createTestService("nginx", "default")
		svc2 := createTestService("redis", "default")
		svc3 := createTestService("postgres", "database")

		cm := newTestClusterManager(svc1, svc2, svc3)

		services, err := cm.GetServices("default")
		require.NoError(t, err)
		assert.Len(t, services, 2)
	})

	t.Run("get services from all namespaces", func(t *testing.T) {
		svc1 := createTestService("nginx", "default")
		svc2 := createTestService("postgres", "database")

		cm := newTestClusterManager(svc1, svc2)

		services, err := cm.GetServices("")
		require.NoError(t, err)
		assert.Len(t, services, 2)
	})

	t.Run("no services found", func(t *testing.T) {
		cm := newTestClusterManager()

		services, err := cm.GetServices("default")
		require.NoError(t, err)
		assert.Len(t, services, 0)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		services, err := cm.GetServices("default")
		assert.Error(t, err)
		assert.Nil(t, services)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

func TestGetService(t *testing.T) {
	t.Run("get existing service", func(t *testing.T) {
		svc := createTestService("nginx", "default")
		cm := newTestClusterManager(svc)

		result, err := cm.GetService("default", "nginx")
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "nginx", result.Name)
		assert.Equal(t, "default", result.Namespace)
		assert.Equal(t, "10.96.0.1", result.ClusterIP)
	})

	t.Run("service not found", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetService("default", "nonexistent")
		assert.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("empty namespace defaults to default", func(t *testing.T) {
		svc := createTestService("nginx", "default")
		cm := newTestClusterManager(svc)

		result, err := cm.GetService("", "nginx")
		require.NoError(t, err)
		assert.NotNil(t, result)
		assert.Equal(t, "nginx", result.Name)
	})

	t.Run("empty name returns error", func(t *testing.T) {
		cm := newTestClusterManager()

		result, err := cm.GetService("default", "")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrResourceNameEmpty)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		result, err := cm.GetService("default", "nginx")
		assert.Error(t, err)
		assert.Nil(t, result)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}
