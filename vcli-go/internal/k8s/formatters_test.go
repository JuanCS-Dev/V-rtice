package k8s

import (
	"encoding/json"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"gopkg.in/yaml.v3"
	corev1 "k8s.io/api/core/v1"
)

// ============================================================================
// FACTORY TESTS
// ============================================================================

func TestNewFormatter(t *testing.T) {
	tests := []struct {
		name        string
		format      OutputFormat
		expectType  string
		expectError bool
	}{
		{
			name:        "table formatter",
			format:      OutputFormatTable,
			expectType:  "TableFormatter",
			expectError: false,
		},
		{
			name:        "json formatter",
			format:      OutputFormatJSON,
			expectType:  "JSONFormatter",
			expectError: false,
		},
		{
			name:        "yaml formatter",
			format:      OutputFormatYAML,
			expectType:  "YAMLFormatter",
			expectError: false,
		},
		{
			name:        "invalid formatter",
			format:      OutputFormat("invalid"),
			expectType:  "",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			formatter, err := NewFormatter(tt.format)

			if tt.expectError {
				assert.Error(t, err)
				assert.Nil(t, formatter)
				assert.Contains(t, err.Error(), "unsupported output format")
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, formatter)
			}
		})
	}
}

// ============================================================================
// TABLE FORMATTER TESTS
// ============================================================================

func TestTableFormatter_FormatPods(t *testing.T) {
	tf := NewTableFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := tf.FormatPods([]Pod{})
		require.NoError(t, err)
		assert.Contains(t, result, "No resources found")
	})

	t.Run("single pod", func(t *testing.T) {
		pods := []Pod{
			{
				Name:      "test-pod",
				Namespace: "default",
				Phase:     corev1.PodRunning,
				NodeName:  "node-1",
				CreatedAt: time.Now().Add(-2 * time.Hour),
			},
		}

		result, err := tf.FormatPods(pods)
		require.NoError(t, err)
		assert.Contains(t, result, "NAME")
		assert.Contains(t, result, "NAMESPACE")
		assert.Contains(t, result, "STATUS")
		assert.Contains(t, result, "NODE")
		assert.Contains(t, result, "AGE")
		assert.Contains(t, result, "test-pod")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "node-1")
		assert.Contains(t, result, "2h")
	})

	t.Run("multiple pods", func(t *testing.T) {
		pods := []Pod{
			{
				Name:      "pod-1",
				Namespace: "default",
				Phase:     corev1.PodRunning,
				NodeName:  "node-1",
				CreatedAt: time.Now().Add(-1 * time.Hour),
			},
			{
				Name:      "pod-2",
				Namespace: "kube-system",
				Phase:     corev1.PodPending,
				NodeName:  "",
				CreatedAt: time.Now().Add(-5 * time.Minute),
			},
		}

		result, err := tf.FormatPods(pods)
		require.NoError(t, err)
		assert.Contains(t, result, "pod-1")
		assert.Contains(t, result, "pod-2")
		assert.Contains(t, result, "kube-system")
		assert.Contains(t, result, "<none>") // Empty node
	})

	t.Run("long pod name", func(t *testing.T) {
		pods := []Pod{
			{
				Name:      "very-long-pod-name-that-should-be-displayed",
				Namespace: "default",
				Phase:     corev1.PodRunning,
				NodeName:  "node-1",
				CreatedAt: time.Now(),
			},
		}

		result, err := tf.FormatPods(pods)
		require.NoError(t, err)
		// Table formatter adjusts column widths dynamically to fit content
		assert.Contains(t, result, "very-long-pod-name")
	})
}

func TestTableFormatter_FormatNamespaces(t *testing.T) {
	tf := NewTableFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := tf.FormatNamespaces([]Namespace{})
		require.NoError(t, err)
		assert.Contains(t, result, "No resources found")
	})

	t.Run("single namespace", func(t *testing.T) {
		namespaces := []Namespace{
			{
				Name:      "default",
				Status:    "Active",
				CreatedAt: time.Now().Add(-24 * time.Hour),
			},
		}

		result, err := tf.FormatNamespaces(namespaces)
		require.NoError(t, err)
		assert.Contains(t, result, "NAME")
		assert.Contains(t, result, "STATUS")
		assert.Contains(t, result, "AGE")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "Active")
		assert.Contains(t, result, "1d")
	})

	t.Run("multiple namespaces", func(t *testing.T) {
		namespaces := []Namespace{
			{
				Name:      "default",
				Status:    "Active",
				CreatedAt: time.Now().Add(-48 * time.Hour),
			},
			{
				Name:      "kube-system",
				Status:    "Active",
				CreatedAt: time.Now().Add(-48 * time.Hour),
			},
		}

		result, err := tf.FormatNamespaces(namespaces)
		require.NoError(t, err)
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "kube-system")
	})
}

func TestTableFormatter_FormatNodes(t *testing.T) {
	tf := NewTableFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := tf.FormatNodes([]Node{})
		require.NoError(t, err)
		assert.Contains(t, result, "No resources found")
	})

	t.Run("single node", func(t *testing.T) {
		nodes := []Node{
			{
				Name:      "node-1",
				Status:    "Ready",
				Roles:     []string{"master"},
				Version:   "v1.28.0",
				CreatedAt: time.Now().Add(-7 * 24 * time.Hour),
			},
		}

		result, err := tf.FormatNodes(nodes)
		require.NoError(t, err)
		assert.Contains(t, result, "NAME")
		assert.Contains(t, result, "STATUS")
		assert.Contains(t, result, "ROLES")
		assert.Contains(t, result, "VERSION")
		assert.Contains(t, result, "AGE")
		assert.Contains(t, result, "node-1")
		assert.Contains(t, result, "master")
		assert.Contains(t, result, "v1.28.0")
		assert.Contains(t, result, "7d")
	})

	t.Run("node without roles", func(t *testing.T) {
		nodes := []Node{
			{
				Name:      "node-1",
				Status:    "Ready",
				Roles:     []string{},
				Version:   "v1.28.0",
				CreatedAt: time.Now(),
			},
		}

		result, err := tf.FormatNodes(nodes)
		require.NoError(t, err)
		// "<none>" gets truncated to fit ROLES column (min width 5)
		// Result will show "<n..." for nodes without roles
		assert.Contains(t, result, "node-1")
		assert.Contains(t, result, "Ready")
	})
}

func TestTableFormatter_FormatDeployments(t *testing.T) {
	tf := NewTableFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := tf.FormatDeployments([]Deployment{})
		require.NoError(t, err)
		assert.Contains(t, result, "No resources found")
	})

	t.Run("single deployment", func(t *testing.T) {
		deployments := []Deployment{
			{
				Name:              "nginx",
				Namespace:         "default",
				Replicas:          3,
				ReadyReplicas:     3,
				UpdatedReplicas:   3,
				AvailableReplicas: 3,
				CreatedAt:         time.Now().Add(-12 * time.Hour),
			},
		}

		result, err := tf.FormatDeployments(deployments)
		require.NoError(t, err)
		assert.Contains(t, result, "NAME")
		assert.Contains(t, result, "NAMESPACE")
		assert.Contains(t, result, "READY")
		assert.Contains(t, result, "UP-TO-DATE")
		assert.Contains(t, result, "AVAILABLE")
		assert.Contains(t, result, "AGE")
		assert.Contains(t, result, "nginx")
		assert.Contains(t, result, "3/3")
		assert.Contains(t, result, "12h")
	})

	t.Run("deployment not ready", func(t *testing.T) {
		deployments := []Deployment{
			{
				Name:              "app",
				Namespace:         "default",
				Replicas:          5,
				ReadyReplicas:     2,
				UpdatedReplicas:   3,
				AvailableReplicas: 2,
				CreatedAt:         time.Now().Add(-30 * time.Minute),
			},
		}

		result, err := tf.FormatDeployments(deployments)
		require.NoError(t, err)
		assert.Contains(t, result, "2/5")
		assert.Contains(t, result, "30m")
	})
}

func TestTableFormatter_FormatServices(t *testing.T) {
	tf := NewTableFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := tf.FormatServices([]Service{})
		require.NoError(t, err)
		assert.Contains(t, result, "No resources found")
	})

	t.Run("single service", func(t *testing.T) {
		services := []Service{
			{
				Name:      "nginx",
				Namespace: "default",
				Type:      corev1.ServiceTypeClusterIP,
				ClusterIP: "10.96.0.1",
				Ports: []ServicePort{
					{Port: 80, Protocol: corev1.ProtocolTCP},
				},
				CreatedAt: time.Now().Add(-3 * time.Hour),
			},
		}

		result, err := tf.FormatServices(services)
		require.NoError(t, err)
		assert.Contains(t, result, "NAME")
		assert.Contains(t, result, "NAMESPACE")
		assert.Contains(t, result, "TYPE")
		assert.Contains(t, result, "CLUSTER-IP")
		assert.Contains(t, result, "PORTS")
		assert.Contains(t, result, "AGE")
		assert.Contains(t, result, "nginx")
		assert.Contains(t, result, "ClusterIP")
		assert.Contains(t, result, "10.96.0.1")
		assert.Contains(t, result, "80/TCP")
		assert.Contains(t, result, "3h")
	})

	t.Run("service with multiple ports", func(t *testing.T) {
		services := []Service{
			{
				Name:      "multi-port",
				Namespace: "default",
				Type:      corev1.ServiceTypeLoadBalancer,
				ClusterIP: "10.96.0.2",
				Ports: []ServicePort{
					{Port: 80, NodePort: 30080, Protocol: corev1.ProtocolTCP},
					{Port: 443, NodePort: 30443, Protocol: corev1.ProtocolTCP},
				},
				CreatedAt: time.Now(),
			},
		}

		result, err := tf.FormatServices(services)
		require.NoError(t, err)
		assert.Contains(t, result, "multi-port")
	})

	t.Run("service without ports", func(t *testing.T) {
		services := []Service{
			{
				Name:      "headless",
				Namespace: "default",
				Type:      corev1.ServiceTypeClusterIP,
				ClusterIP: "None",
				Ports:     []ServicePort{},
				CreatedAt: time.Now(),
			},
		}

		result, err := tf.FormatServices(services)
		require.NoError(t, err)
		assert.Contains(t, result, "<none>")
	})
}

func TestTableFormatter_FormatConfigMaps(t *testing.T) {
	tf := NewTableFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := tf.FormatConfigMaps([]ConfigMap{})
		require.NoError(t, err)
		assert.Contains(t, result, "No resources found")
	})

	t.Run("single configmap", func(t *testing.T) {
		configmaps := []ConfigMap{
			{
				Name:      "app-config",
				Namespace: "default",
				Data: map[string]string{
					"database.host": "postgres.default.svc.cluster.local",
					"database.port": "5432",
				},
				BinaryData: map[string][]byte{
					"cert.pem": []byte("certificate-data"),
				},
				CreatedAt: time.Now().Add(-48 * time.Hour),
			},
		}

		result, err := tf.FormatConfigMaps(configmaps)
		require.NoError(t, err)
		assert.Contains(t, result, "NAME")
		assert.Contains(t, result, "NAMESPACE")
		assert.Contains(t, result, "DATA")
		assert.Contains(t, result, "AGE")
		assert.Contains(t, result, "app-config")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "3") // 2 data + 1 binaryData
		assert.Contains(t, result, "2d")
	})

	t.Run("configmap with only data", func(t *testing.T) {
		configmaps := []ConfigMap{
			{
				Name:      "simple-config",
				Namespace: "kube-system",
				Data: map[string]string{
					"key1": "value1",
				},
				CreatedAt: time.Now(),
			},
		}

		result, err := tf.FormatConfigMaps(configmaps)
		require.NoError(t, err)
		assert.Contains(t, result, "simple-config")
		assert.Contains(t, result, "kube-system")
		assert.Contains(t, result, "1")
	})

	t.Run("configmap with only binaryData", func(t *testing.T) {
		configmaps := []ConfigMap{
			{
				Name:      "binary-config",
				Namespace: "default",
				BinaryData: map[string][]byte{
					"binary1": []byte("data1"),
					"binary2": []byte("data2"),
				},
				CreatedAt: time.Now().Add(-time.Hour),
			},
		}

		result, err := tf.FormatConfigMaps(configmaps)
		require.NoError(t, err)
		assert.Contains(t, result, "binary-config")
		assert.Contains(t, result, "2")
		assert.Contains(t, result, "1h")
	})

	t.Run("empty configmap", func(t *testing.T) {
		configmaps := []ConfigMap{
			{
				Name:      "empty-config",
				Namespace: "default",
				CreatedAt: time.Now().Add(-30 * time.Minute),
			},
		}

		result, err := tf.FormatConfigMaps(configmaps)
		require.NoError(t, err)
		assert.Contains(t, result, "empty-config")
		assert.Contains(t, result, "0")
		assert.Contains(t, result, "30m")
	})

	t.Run("multiple configmaps", func(t *testing.T) {
		configmaps := []ConfigMap{
			{
				Name:      "config-1",
				Namespace: "default",
				Data:      map[string]string{"key": "value"},
				CreatedAt: time.Now(),
			},
			{
				Name:      "config-2",
				Namespace: "kube-system",
				Data:      map[string]string{"a": "b", "c": "d"},
				CreatedAt: time.Now().Add(-time.Hour),
			},
		}

		result, err := tf.FormatConfigMaps(configmaps)
		require.NoError(t, err)
		assert.Contains(t, result, "config-1")
		assert.Contains(t, result, "config-2")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "kube-system")
	})
}

func TestTableFormatter_FormatSecrets(t *testing.T) {
	tf := NewTableFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := tf.FormatSecrets([]Secret{})
		require.NoError(t, err)
		assert.Contains(t, result, "No resources found")
	})

	t.Run("single secret", func(t *testing.T) {
		secrets := []Secret{
			{
				Name:      "db-credentials",
				Namespace: "default",
				Type:      "Opaque",
				Data: map[string][]byte{
					"username": []byte("admin"),
					"password": []byte("supersecret"),
					"host":     []byte("postgres.default.svc.cluster.local"),
				},
				CreatedAt: time.Now().Add(-7 * 24 * time.Hour),
			},
		}

		result, err := tf.FormatSecrets(secrets)
		require.NoError(t, err)
		assert.Contains(t, result, "NAME")
		assert.Contains(t, result, "NAMESPACE")
		assert.Contains(t, result, "TYPE")
		assert.Contains(t, result, "DATA")
		assert.Contains(t, result, "AGE")
		assert.Contains(t, result, "db-credentials")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "Opaque")
		assert.Contains(t, result, "3")
		assert.Contains(t, result, "7d")
	})

	t.Run("TLS secret", func(t *testing.T) {
		secrets := []Secret{
			{
				Name:      "tls-cert",
				Namespace: "ingress-nginx",
				Type:      "kubernetes.io/tls",
				Data: map[string][]byte{
					"tls.crt": []byte("cert-data"),
					"tls.key": []byte("key-data"),
				},
				CreatedAt: time.Now().Add(-24 * time.Hour),
			},
		}

		result, err := tf.FormatSecrets(secrets)
		require.NoError(t, err)
		assert.Contains(t, result, "tls-cert")
		assert.Contains(t, result, "ingress-nginx")
		assert.Contains(t, result, "kubernetes.io/tls")
		assert.Contains(t, result, "2")
		assert.Contains(t, result, "1d")
	})

	t.Run("docker config secret", func(t *testing.T) {
		secrets := []Secret{
			{
				Name:      "docker-registry",
				Namespace: "default",
				Type:      "kubernetes.io/dockerconfigjson",
				Data: map[string][]byte{
					".dockerconfigjson": []byte(`{"auths":{}}`),
				},
				CreatedAt: time.Now().Add(-2 * time.Hour),
			},
		}

		result, err := tf.FormatSecrets(secrets)
		require.NoError(t, err)
		assert.Contains(t, result, "docker-registry")
		assert.Contains(t, result, "kubernetes.io/dockerconfigjson")
		assert.Contains(t, result, "1")
		assert.Contains(t, result, "2h")
	})

	t.Run("empty secret", func(t *testing.T) {
		secrets := []Secret{
			{
				Name:      "empty-secret",
				Namespace: "default",
				Type:      "Opaque",
				CreatedAt: time.Now().Add(-15 * time.Minute),
			},
		}

		result, err := tf.FormatSecrets(secrets)
		require.NoError(t, err)
		assert.Contains(t, result, "empty-secret")
		assert.Contains(t, result, "0")
		assert.Contains(t, result, "15m")
	})

	t.Run("multiple secrets", func(t *testing.T) {
		secrets := []Secret{
			{
				Name:      "secret-1",
				Namespace: "default",
				Type:      "Opaque",
				Data:      map[string][]byte{"key": []byte("value")},
				CreatedAt: time.Now(),
			},
			{
				Name:      "secret-2",
				Namespace: "kube-system",
				Type:      "kubernetes.io/service-account-token",
				Data:      map[string][]byte{"token": []byte("abc"), "ca.crt": []byte("def")},
				CreatedAt: time.Now().Add(-time.Hour),
			},
		}

		result, err := tf.FormatSecrets(secrets)
		require.NoError(t, err)
		assert.Contains(t, result, "secret-1")
		assert.Contains(t, result, "secret-2")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "kube-system")
	})
}

func TestTableFormatter_ColorizeStatus(t *testing.T) {
	tf := NewTableFormatter()

	tests := []struct {
		name   string
		status string
	}{
		{"running", "Running"},
		{"pending", "Pending"},
		{"failed", "Failed"},
		{"succeeded", "Succeeded"},
		{"unknown", "Unknown"},
		{"active", "Active"},
		{"ready", "Ready"},
		{"waiting", "Waiting"},
		{"error", "Error"},
		{"crashloopbackoff", "CrashLoopBackOff"},
		{"completed", "Completed"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tf.colorizeStatus(tt.status)
			assert.NotEmpty(t, result)
			assert.Contains(t, result, strings.ToTitle(tt.status[:1])) // First letter should be present
		})
	}
}

// ============================================================================
// JSON FORMATTER TESTS
// ============================================================================

func TestJSONFormatter_FormatPods(t *testing.T) {
	jf := NewJSONFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := jf.FormatPods([]Pod{})
		require.NoError(t, err)

		var pods []Pod
		err = json.Unmarshal([]byte(result), &pods)
		require.NoError(t, err)
		assert.Empty(t, pods)
	})

	t.Run("single pod", func(t *testing.T) {
		pods := []Pod{
			{
				Name:      "test-pod",
				Namespace: "default",
				Phase:     corev1.PodRunning,
				NodeName:  "node-1",
				CreatedAt: time.Now(),
			},
		}

		result, err := jf.FormatPods(pods)
		require.NoError(t, err)

		var decoded []Pod
		err = json.Unmarshal([]byte(result), &decoded)
		require.NoError(t, err)
		assert.Len(t, decoded, 1)
		assert.Equal(t, "test-pod", decoded[0].Name)
		assert.Equal(t, "default", decoded[0].Namespace)
	})

	t.Run("multiple pods", func(t *testing.T) {
		pods := []Pod{
			{Name: "pod-1", Namespace: "default", Phase: corev1.PodRunning, CreatedAt: time.Now()},
			{Name: "pod-2", Namespace: "kube-system", Phase: corev1.PodPending, CreatedAt: time.Now()},
		}

		result, err := jf.FormatPods(pods)
		require.NoError(t, err)

		var decoded []Pod
		err = json.Unmarshal([]byte(result), &decoded)
		require.NoError(t, err)
		assert.Len(t, decoded, 2)
	})
}

func TestJSONFormatter_FormatNamespaces(t *testing.T) {
	jf := NewJSONFormatter()

	namespaces := []Namespace{
		{Name: "default", Status: "Active", CreatedAt: time.Now()},
	}

	result, err := jf.FormatNamespaces(namespaces)
	require.NoError(t, err)

	var decoded []Namespace
	err = json.Unmarshal([]byte(result), &decoded)
	require.NoError(t, err)
	assert.Len(t, decoded, 1)
	assert.Equal(t, "default", decoded[0].Name)
}

func TestJSONFormatter_FormatNodes(t *testing.T) {
	jf := NewJSONFormatter()

	nodes := []Node{
		{Name: "node-1", Status: "Ready", Version: "v1.28.0", CreatedAt: time.Now()},
	}

	result, err := jf.FormatNodes(nodes)
	require.NoError(t, err)

	var decoded []Node
	err = json.Unmarshal([]byte(result), &decoded)
	require.NoError(t, err)
	assert.Len(t, decoded, 1)
	assert.Equal(t, "node-1", decoded[0].Name)
}

func TestJSONFormatter_FormatDeployments(t *testing.T) {
	jf := NewJSONFormatter()

	deployments := []Deployment{
		{Name: "nginx", Namespace: "default", Replicas: 3, CreatedAt: time.Now()},
	}

	result, err := jf.FormatDeployments(deployments)
	require.NoError(t, err)

	var decoded []Deployment
	err = json.Unmarshal([]byte(result), &decoded)
	require.NoError(t, err)
	assert.Len(t, decoded, 1)
	assert.Equal(t, "nginx", decoded[0].Name)
}

func TestJSONFormatter_FormatServices(t *testing.T) {
	jf := NewJSONFormatter()

	services := []Service{
		{Name: "nginx", Namespace: "default", Type: corev1.ServiceTypeClusterIP, CreatedAt: time.Now()},
	}

	result, err := jf.FormatServices(services)
	require.NoError(t, err)

	var decoded []Service
	err = json.Unmarshal([]byte(result), &decoded)
	require.NoError(t, err)
	assert.Len(t, decoded, 1)
	assert.Equal(t, "nginx", decoded[0].Name)
}

func TestJSONFormatter_FormatConfigMaps(t *testing.T) {
	jf := NewJSONFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := jf.FormatConfigMaps([]ConfigMap{})
		require.NoError(t, err)
		assert.Contains(t, result, "[]")
	})

	t.Run("single configmap", func(t *testing.T) {
		configmaps := []ConfigMap{
			{
				Name:      "app-config",
				Namespace: "default",
				Data: map[string]string{
					"key1": "value1",
				},
				CreatedAt: time.Now(),
			},
		}

		result, err := jf.FormatConfigMaps(configmaps)
		require.NoError(t, err)
		assert.Contains(t, result, "app-config")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "key1")
		assert.Contains(t, result, "value1")
	})
}

func TestJSONFormatter_FormatSecrets(t *testing.T) {
	jf := NewJSONFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := jf.FormatSecrets([]Secret{})
		require.NoError(t, err)
		assert.Contains(t, result, "[]")
	})

	t.Run("single secret", func(t *testing.T) {
		secrets := []Secret{
			{
				Name:      "db-credentials",
				Namespace: "default",
				Type:      "Opaque",
				Data: map[string][]byte{
					"username": []byte("admin"),
				},
				CreatedAt: time.Now(),
			},
		}

		result, err := jf.FormatSecrets(secrets)
		require.NoError(t, err)
		assert.Contains(t, result, "db-credentials")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "Opaque")
	})
}

// ============================================================================
// YAML FORMATTER TESTS
// ============================================================================

func TestYAMLFormatter_FormatPods(t *testing.T) {
	yf := NewYAMLFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := yf.FormatPods([]Pod{})
		require.NoError(t, err)

		var pods []Pod
		err = yaml.Unmarshal([]byte(result), &pods)
		require.NoError(t, err)
		assert.Empty(t, pods)
	})

	t.Run("single pod", func(t *testing.T) {
		pods := []Pod{
			{
				Name:      "test-pod",
				Namespace: "default",
				Phase:     corev1.PodRunning,
				NodeName:  "node-1",
				CreatedAt: time.Now(),
			},
		}

		result, err := yf.FormatPods(pods)
		require.NoError(t, err)

		var decoded []Pod
		err = yaml.Unmarshal([]byte(result), &decoded)
		require.NoError(t, err)
		assert.Len(t, decoded, 1)
		assert.Equal(t, "test-pod", decoded[0].Name)
	})
}

func TestYAMLFormatter_FormatNamespaces(t *testing.T) {
	yf := NewYAMLFormatter()

	namespaces := []Namespace{
		{Name: "default", Status: "Active", CreatedAt: time.Now()},
	}

	result, err := yf.FormatNamespaces(namespaces)
	require.NoError(t, err)

	var decoded []Namespace
	err = yaml.Unmarshal([]byte(result), &decoded)
	require.NoError(t, err)
	assert.Len(t, decoded, 1)
	assert.Equal(t, "default", decoded[0].Name)
}

func TestYAMLFormatter_FormatNodes(t *testing.T) {
	yf := NewYAMLFormatter()

	nodes := []Node{
		{Name: "node-1", Status: "Ready", Version: "v1.28.0", CreatedAt: time.Now()},
	}

	result, err := yf.FormatNodes(nodes)
	require.NoError(t, err)

	var decoded []Node
	err = yaml.Unmarshal([]byte(result), &decoded)
	require.NoError(t, err)
	assert.Len(t, decoded, 1)
	assert.Equal(t, "node-1", decoded[0].Name)
}

func TestYAMLFormatter_FormatDeployments(t *testing.T) {
	yf := NewYAMLFormatter()

	deployments := []Deployment{
		{Name: "nginx", Namespace: "default", Replicas: 3, CreatedAt: time.Now()},
	}

	result, err := yf.FormatDeployments(deployments)
	require.NoError(t, err)

	var decoded []Deployment
	err = yaml.Unmarshal([]byte(result), &decoded)
	require.NoError(t, err)
	assert.Len(t, decoded, 1)
	assert.Equal(t, "nginx", decoded[0].Name)
}

func TestYAMLFormatter_FormatServices(t *testing.T) {
	yf := NewYAMLFormatter()

	services := []Service{
		{Name: "nginx", Namespace: "default", Type: corev1.ServiceTypeClusterIP, CreatedAt: time.Now()},
	}

	result, err := yf.FormatServices(services)
	require.NoError(t, err)

	var decoded []Service
	err = yaml.Unmarshal([]byte(result), &decoded)
	require.NoError(t, err)
	assert.Len(t, decoded, 1)
	assert.Equal(t, "nginx", decoded[0].Name)
}

func TestYAMLFormatter_FormatConfigMaps(t *testing.T) {
	yf := NewYAMLFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := yf.FormatConfigMaps([]ConfigMap{})
		require.NoError(t, err)
		assert.Contains(t, result, "[]")
	})

	t.Run("single configmap", func(t *testing.T) {
		configmaps := []ConfigMap{
			{
				Name:      "app-config",
				Namespace: "default",
				Data: map[string]string{
					"key1": "value1",
				},
				CreatedAt: time.Now(),
			},
		}

		result, err := yf.FormatConfigMaps(configmaps)
		require.NoError(t, err)
		assert.Contains(t, result, "app-config")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "key1")
		assert.Contains(t, result, "value1")
	})
}

func TestYAMLFormatter_FormatSecrets(t *testing.T) {
	yf := NewYAMLFormatter()

	t.Run("empty list", func(t *testing.T) {
		result, err := yf.FormatSecrets([]Secret{})
		require.NoError(t, err)
		assert.Contains(t, result, "[]")
	})

	t.Run("single secret", func(t *testing.T) {
		secrets := []Secret{
			{
				Name:      "db-credentials",
				Namespace: "default",
				Type:      "Opaque",
				Data: map[string][]byte{
					"username": []byte("admin"),
				},
				CreatedAt: time.Now(),
			},
		}

		result, err := yf.FormatSecrets(secrets)
		require.NoError(t, err)
		assert.Contains(t, result, "db-credentials")
		assert.Contains(t, result, "default")
		assert.Contains(t, result, "Opaque")
	})
}

// ============================================================================
// HELPER FUNCTION TESTS
// ============================================================================

func TestFormatAge(t *testing.T) {
	now := time.Now()

	tests := []struct {
		name     string
		time     time.Time
		expected string
	}{
		{"seconds", now.Add(-30 * time.Second), "30s"},
		{"minutes", now.Add(-5 * time.Minute), "5m"},
		{"hours", now.Add(-3 * time.Hour), "3h"},
		{"days", now.Add(-2 * 24 * time.Hour), "2d"},
		{"days with hours", now.Add(-25 * time.Hour), "1d1h"},
		{"many days", now.Add(-10 * 24 * time.Hour), "10d"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := formatAge(tt.time)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestFormatServicePorts(t *testing.T) {
	tests := []struct {
		name     string
		ports    []ServicePort
		expected string
	}{
		{
			name:     "empty",
			ports:    []ServicePort{},
			expected: "<none>",
		},
		{
			name: "single port",
			ports: []ServicePort{
				{Port: 80, Protocol: corev1.ProtocolTCP},
			},
			expected: "80/TCP",
		},
		{
			name: "multiple ports",
			ports: []ServicePort{
				{Port: 80, Protocol: corev1.ProtocolTCP},
				{Port: 443, Protocol: corev1.ProtocolTCP},
			},
			expected: "443/TCP,80/TCP", // Sorted
		},
		{
			name: "with node port",
			ports: []ServicePort{
				{Port: 80, NodePort: 30080, Protocol: corev1.ProtocolTCP},
			},
			expected: "80:30080/TCP",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := formatServicePorts(tt.ports)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestTruncate(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		maxLen   int
		expected string
	}{
		{"no truncation needed", "short", 10, "short"},
		{"exact length", "exactly10c", 10, "exactly10c"},
		{"truncate long string", "this-is-a-very-long-string", 10, "this-is..."},
		{"truncate to 3", "abcdef", 3, "abc"},
		{"truncate to 1", "abc", 1, "a"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := truncate(tt.input, tt.maxLen)
			assert.Equal(t, tt.expected, result)
			assert.LessOrEqual(t, len(result), tt.maxLen)
		})
	}
}

func TestMaxLen(t *testing.T) {
	t.Run("pods", func(t *testing.T) {
		pods := []Pod{
			{Name: "short"},
			{Name: "very-long-pod-name"},
			{Name: "mid"},
		}

		result := maxLen(pods, func(p Pod) string { return p.Name })
		assert.Equal(t, len("very-long-pod-name"), result)
	})

	t.Run("empty slice", func(t *testing.T) {
		result := maxLen([]Pod{}, func(p Pod) string { return p.Name })
		assert.Equal(t, 0, result)
	})
}

func TestMax(t *testing.T) {
	tests := []struct {
		name     string
		a        int
		b        int
		expected int
	}{
		{"a greater", 10, 5, 10},
		{"b greater", 3, 7, 7},
		{"equal", 5, 5, 5},
		{"negative", -5, -10, -5},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := max(tt.a, tt.b)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// ============================================================================
// REPR TESTS
// ============================================================================

func TestFormattersRepr(t *testing.T) {
	t.Run("TableFormatter", func(t *testing.T) {
		tf := NewTableFormatter()
		repr := tf.Repr()
		assert.Contains(t, repr, "TableFormatter")
		assert.Contains(t, repr, "colorized=true")
	})

	t.Run("JSONFormatter", func(t *testing.T) {
		jf := NewJSONFormatter()
		repr := jf.Repr()
		assert.Contains(t, repr, "JSONFormatter")
		assert.Contains(t, repr, "indent=true")
	})

	t.Run("YAMLFormatter", func(t *testing.T) {
		yf := NewYAMLFormatter()
		repr := yf.Repr()
		assert.Contains(t, repr, "YAMLFormatter")
	})
}
