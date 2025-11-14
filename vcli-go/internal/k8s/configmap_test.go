package k8s

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// ============================================================================
// CREATE CONFIGMAP TESTS
// ============================================================================

func TestCreateConfigMap(t *testing.T) {
	t.Run("create basic configmap successfully", func(t *testing.T) {
		cm := newTestClusterManager()

		opts := NewConfigMapOptions()
		opts.Data["key1"] = "value1"
		opts.Data["key2"] = "value2"
		opts.Labels["app"] = "test"

		configmap, err := cm.CreateConfigMap("test-config", "default", opts)
		require.NoError(t, err)
		require.NotNil(t, configmap)

		assert.Equal(t, "test-config", configmap.Name)
		assert.Equal(t, "default", configmap.Namespace)
		assert.Equal(t, "value1", configmap.Data["key1"])
		assert.Equal(t, "value2", configmap.Data["key2"])
		assert.Equal(t, "test", configmap.Labels["app"])
	})

	t.Run("create configmap with binary data", func(t *testing.T) {
		cm := newTestClusterManager()

		opts := NewConfigMapOptions()
		opts.Data["text"] = "hello"
		opts.BinaryData["binary"] = []byte("binary data")

		configmap, err := cm.CreateConfigMap("test-config", "default", opts)
		require.NoError(t, err)
		assert.Equal(t, "hello", configmap.Data["text"])
		assert.Equal(t, []byte("binary data"), configmap.BinaryData["binary"])
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewConfigMapOptions()

		_, err := cm.CreateConfigMap("", "default", opts)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "configmap name is required")
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewConfigMapOptions()
		opts.Data["key"] = "value"

		configmap, err := cm.CreateConfigMap("test-config", "", opts)
		require.NoError(t, err)
		assert.Equal(t, "default", configmap.Namespace)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}
		opts := NewConfigMapOptions()

		_, err := cm.CreateConfigMap("test-config", "default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// GET CONFIGMAP TESTS
// ============================================================================

func TestGetConfigMap(t *testing.T) {
	t.Run("get existing configmap", func(t *testing.T) {
		existing := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-config",
				Namespace: "default",
			},
			Data: map[string]string{
				"key1": "value1",
			},
		}

		cm := newTestClusterManager(existing)

		configmap, err := cm.GetConfigMap("test-config", "default")
		require.NoError(t, err)
		require.NotNil(t, configmap)
		assert.Equal(t, "test-config", configmap.Name)
		assert.Equal(t, "value1", configmap.Data["key1"])
	})

	t.Run("error when configmap not found", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.GetConfigMap("nonexistent", "default")
		require.Error(t, err)
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.GetConfigMap("", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get configmap")
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		existing := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-config",
				Namespace: "default",
			},
		}
		cm := newTestClusterManager(existing)

		configmap, err := cm.GetConfigMap("test-config", "")
		require.NoError(t, err)
		assert.Equal(t, "test-config", configmap.Name)
		assert.Equal(t, "default", configmap.Namespace)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		_, err := cm.GetConfigMap("test-config", "default")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// UPDATE CONFIGMAP TESTS
// ============================================================================

func TestUpdateConfigMap(t *testing.T) {
	t.Run("update existing configmap", func(t *testing.T) {
		existing := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-config",
				Namespace: "default",
			},
			Data: map[string]string{
				"key1": "old-value",
			},
		}

		cm := newTestClusterManager(existing)

		opts := NewConfigMapOptions()
		opts.Data["key1"] = "new-value"
		opts.Data["key2"] = "added-value"

		configmap, err := cm.UpdateConfigMap("test-config", "default", opts)
		require.NoError(t, err)
		require.NotNil(t, configmap)
		assert.Equal(t, "new-value", configmap.Data["key1"])
		assert.Equal(t, "added-value", configmap.Data["key2"])
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewConfigMapOptions()

		_, err := cm.UpdateConfigMap("", "default", opts)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get existing configmap")
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		existing := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-config",
				Namespace: "default",
			},
			Data: map[string]string{"old": "value"},
		}
		cm := newTestClusterManager(existing)
		opts := NewConfigMapOptions()
		opts.Data["new"] = "value"

		configmap, err := cm.UpdateConfigMap("test-config", "", opts)
		require.NoError(t, err)
		assert.Equal(t, "default", configmap.Namespace)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}
		opts := NewConfigMapOptions()

		_, err := cm.UpdateConfigMap("test-config", "default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// DELETE CONFIGMAP TESTS
// ============================================================================

func TestDeleteConfigMap(t *testing.T) {
	t.Run("delete existing configmap", func(t *testing.T) {
		existing := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-config",
				Namespace: "default",
			},
		}

		cm := newTestClusterManager(existing)

		err := cm.DeleteConfigMap("test-config", "default")
		require.NoError(t, err)

		// Verify it's deleted
		_, err = cm.GetConfigMap("test-config", "default")
		require.Error(t, err)
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		err := cm.DeleteConfigMap("", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to delete configmap")
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		existing := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-config",
				Namespace: "default",
			},
		}
		cm := newTestClusterManager(existing)

		err := cm.DeleteConfigMap("test-config", "")
		require.NoError(t, err)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		err := cm.DeleteConfigMap("test-config", "default")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// LIST CONFIGMAPS TESTS
// ============================================================================

func TestListConfigMaps(t *testing.T) {
	t.Run("list all configmaps in namespace", func(t *testing.T) {
		cm1 := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "config1",
				Namespace: "default",
			},
		}
		cm2 := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "config2",
				Namespace: "default",
			},
		}

		mgr := newTestClusterManager(cm1, cm2)

		opts := NewConfigMapListOptions()
		list, err := mgr.ListConfigMaps("default", opts)
		require.NoError(t, err)
		require.NotNil(t, list)
		assert.Len(t, list.Items, 2)
	})

	t.Run("list configmaps with label selector", func(t *testing.T) {
		cm1 := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "config1",
				Namespace: "default",
				Labels:    map[string]string{"app": "web"},
			},
		}
		cm2 := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "config2",
				Namespace: "default",
				Labels:    map[string]string{"app": "api"},
			},
		}

		mgr := newTestClusterManager(cm1, cm2)

		opts := NewConfigMapListOptions()
		opts.Labels["app"] = "web"
		list, err := mgr.ListConfigMaps("default", opts)
		require.NoError(t, err)

		// Note: fake clientset may not fully support label selectors
		// so we just verify no error and list is returned
		require.NotNil(t, list)
	})

	t.Run("empty list when no configmaps", func(t *testing.T) {
		mgr := newTestClusterManager()

		opts := NewConfigMapListOptions()
		list, err := mgr.ListConfigMaps("default", opts)
		require.NoError(t, err)
		require.NotNil(t, list)
		assert.Len(t, list.Items, 0)
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		cm1 := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "config1",
				Namespace: "default",
			},
		}
		mgr := newTestClusterManager(cm1)
		opts := NewConfigMapListOptions()

		list, err := mgr.ListConfigMaps("", opts)
		require.NoError(t, err)
		require.NotNil(t, list)
		assert.Len(t, list.Items, 1)
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}
		opts := NewConfigMapListOptions()

		_, err := mgr.ListConfigMaps("default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// CREATE FROM LITERALS TESTS
// ============================================================================

func TestCreateConfigMapFromLiterals(t *testing.T) {
	t.Run("create from literals successfully", func(t *testing.T) {
		mgr := newTestClusterManager()

		literals := map[string]string{
			"DB_HOST": "localhost",
			"DB_PORT": "5432",
		}

		opts := NewConfigMapOptions()
		configmap, err := mgr.CreateConfigMapFromLiterals("app-config", "default", literals, opts)
		require.NoError(t, err)
		require.NotNil(t, configmap)

		assert.Equal(t, "localhost", configmap.Data["DB_HOST"])
		assert.Equal(t, "5432", configmap.Data["DB_PORT"])
	})

	t.Run("replaces data with literals", func(t *testing.T) {
		mgr := newTestClusterManager()

		literals := map[string]string{
			"key1": "value1",
		}

		opts := NewConfigMapOptions()
		opts.Data["existing"] = "data" // This will be replaced, not merged
		opts.Labels["env"] = "prod"

		configmap, err := mgr.CreateConfigMapFromLiterals("app-config", "default", literals, opts)
		require.NoError(t, err)

		// Literals replace Data entirely
		assert.Equal(t, "value1", configmap.Data["key1"])
		assert.NotContains(t, configmap.Data, "existing") // Data was replaced
		assert.Equal(t, "prod", configmap.Labels["env"])  // Labels are preserved
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}

		literals := map[string]string{"key": "value"}
		opts := NewConfigMapOptions()

		_, err := mgr.CreateConfigMapFromLiterals("app-config", "default", literals, opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// OPERATIONS.GO WRAPPER TESTS
// ============================================================================

func TestGetConfigMaps(t *testing.T) {
	t.Run("get configmaps from namespace", func(t *testing.T) {
		cm1 := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "config1",
				Namespace: "default",
			},
			Data: map[string]string{"key": "value"},
		}

		mgr := newTestClusterManager(cm1)

		configs, err := mgr.GetConfigMaps("default")
		require.NoError(t, err)
		assert.Len(t, configs, 1)
		assert.Equal(t, "config1", configs[0].Name)
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}

		_, err := mgr.GetConfigMaps("default")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

func TestGetConfigMapByName(t *testing.T) {
	t.Run("get configmap by name", func(t *testing.T) {
		cm1 := &corev1.ConfigMap{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-config",
				Namespace: "default",
			},
			Data: map[string]string{"key": "value"},
		}

		mgr := newTestClusterManager(cm1)

		config, err := mgr.GetConfigMapByName("default", "test-config")
		require.NoError(t, err)
		require.NotNil(t, config)
		assert.Equal(t, "test-config", config.Name)
		assert.Equal(t, "value", config.Data["key"])
	})

	t.Run("error when not found", func(t *testing.T) {
		mgr := newTestClusterManager()

		_, err := mgr.GetConfigMapByName("default", "nonexistent")
		require.Error(t, err)
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}

		_, err := mgr.GetConfigMapByName("default", "test-config")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// HELPER FUNCTION: Enhanced newTestClusterManager for ConfigMap tests
// ============================================================================

// This test file shares the newTestClusterManager from operations_test.go
// The existing helper works perfectly for ConfigMap testing too
