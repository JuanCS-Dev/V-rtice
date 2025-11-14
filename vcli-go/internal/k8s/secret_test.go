package k8s

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// ============================================================================
// CREATE SECRET TESTS
// ============================================================================

func TestCreateSecret(t *testing.T) {
	t.Run("create basic secret successfully", func(t *testing.T) {
		cm := newTestClusterManager()

		opts := NewSecretOptions()
		opts.Data["username"] = "admin"
		opts.Data["password"] = "secret123"
		opts.Labels["app"] = "test"

		secret, err := cm.CreateSecret("test-secret", "default", opts)
		require.NoError(t, err)
		require.NotNil(t, secret)

		assert.Equal(t, "test-secret", secret.Name)
		assert.Equal(t, "default", secret.Namespace)
		assert.Equal(t, "admin", secret.StringData["username"])
		assert.Equal(t, "secret123", secret.StringData["password"])
		assert.Equal(t, "test", secret.Labels["app"])
	})

	t.Run("create secret with binary data", func(t *testing.T) {
		cm := newTestClusterManager()

		opts := NewSecretOptions()
		opts.Data["text"] = "hello"
		opts.BinaryData["binary"] = []byte("binary secret data")

		secret, err := cm.CreateSecret("test-secret", "default", opts)
		require.NoError(t, err)
		assert.Equal(t, "hello", secret.StringData["text"])
		assert.Equal(t, []byte("binary secret data"), secret.Data["binary"])
	})

	t.Run("create secret with specific type", func(t *testing.T) {
		cm := newTestClusterManager()

		opts := NewSecretOptions()
		opts.Type = SecretTypeTLS
		opts.Data["tls.crt"] = "CERTIFICATE DATA"
		opts.Data["tls.key"] = "PRIVATE KEY DATA"

		secret, err := cm.CreateSecret("tls-secret", "default", opts)
		require.NoError(t, err)
		assert.Equal(t, corev1.SecretType(SecretTypeTLS), secret.Type)
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewSecretOptions()

		_, err := cm.CreateSecret("", "default", opts)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "secret name is required")
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewSecretOptions()
		opts.Data["key"] = "value"

		secret, err := cm.CreateSecret("test-secret", "", opts)
		require.NoError(t, err)
		assert.Equal(t, "default", secret.Namespace)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}
		opts := NewSecretOptions()

		_, err := cm.CreateSecret("test-secret", "default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// GET SECRET TESTS
// ============================================================================

func TestGetSecret(t *testing.T) {
	t.Run("get existing secret", func(t *testing.T) {
		existing := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-secret",
				Namespace: "default",
			},
			StringData: map[string]string{
				"password": "secret123",
			},
		}

		cm := newTestClusterManager(existing)

		secret, err := cm.GetSecret("test-secret", "default")
		require.NoError(t, err)
		require.NotNil(t, secret)
		assert.Equal(t, "test-secret", secret.Name)
	})

	t.Run("error when secret not found", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.GetSecret("nonexistent", "default")
		require.Error(t, err)
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.GetSecret("", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get secret")
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		existing := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-secret",
				Namespace: "default",
			},
		}
		cm := newTestClusterManager(existing)

		secret, err := cm.GetSecret("test-secret", "")
		require.NoError(t, err)
		assert.Equal(t, "test-secret", secret.Name)
		assert.Equal(t, "default", secret.Namespace)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		_, err := cm.GetSecret("test-secret", "default")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// UPDATE SECRET TESTS
// ============================================================================

func TestUpdateSecret(t *testing.T) {
	t.Run("update existing secret", func(t *testing.T) {
		existing := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-secret",
				Namespace: "default",
			},
			StringData: map[string]string{
				"password": "old-password",
			},
		}

		cm := newTestClusterManager(existing)

		opts := NewSecretOptions()
		opts.Data["password"] = "new-password"
		opts.Data["username"] = "admin"

		secret, err := cm.UpdateSecret("test-secret", "default", opts)
		require.NoError(t, err)
		require.NotNil(t, secret)
		assert.Equal(t, "new-password", secret.StringData["password"])
		assert.Equal(t, "admin", secret.StringData["username"])
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewSecretOptions()

		_, err := cm.UpdateSecret("", "default", opts)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to get existing secret")
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		existing := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-secret",
				Namespace: "default",
			},
			StringData: map[string]string{"old": "value"},
		}
		cm := newTestClusterManager(existing)
		opts := NewSecretOptions()
		opts.Data["new"] = "value"

		secret, err := cm.UpdateSecret("test-secret", "", opts)
		require.NoError(t, err)
		assert.Equal(t, "default", secret.Namespace)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}
		opts := NewSecretOptions()

		_, err := cm.UpdateSecret("test-secret", "default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// DELETE SECRET TESTS
// ============================================================================

func TestDeleteSecret(t *testing.T) {
	t.Run("delete existing secret", func(t *testing.T) {
		existing := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-secret",
				Namespace: "default",
			},
		}

		cm := newTestClusterManager(existing)

		err := cm.DeleteSecret("test-secret", "default")
		require.NoError(t, err)

		// Verify it's deleted
		_, err = cm.GetSecret("test-secret", "default")
		require.Error(t, err)
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		err := cm.DeleteSecret("", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to delete secret")
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		existing := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-secret",
				Namespace: "default",
			},
		}
		cm := newTestClusterManager(existing)

		err := cm.DeleteSecret("test-secret", "")
		require.NoError(t, err)
	})

	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		err := cm.DeleteSecret("test-secret", "default")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// LIST SECRETS TESTS
// ============================================================================

func TestListSecrets(t *testing.T) {
	t.Run("list all secrets in namespace", func(t *testing.T) {
		s1 := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "secret1",
				Namespace: "default",
			},
		}
		s2 := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "secret2",
				Namespace: "default",
			},
		}

		mgr := newTestClusterManager(s1, s2)

		opts := NewSecretListOptions()
		list, err := mgr.ListSecrets("default", opts)
		require.NoError(t, err)
		require.NotNil(t, list)
		assert.Len(t, list.Items, 2)
	})

	t.Run("list secrets with label selector", func(t *testing.T) {
		s1 := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "secret1",
				Namespace: "default",
				Labels:    map[string]string{"app": "web"},
			},
		}
		s2 := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "secret2",
				Namespace: "default",
				Labels:    map[string]string{"app": "api"},
			},
		}

		mgr := newTestClusterManager(s1, s2)

		opts := NewSecretListOptions()
		opts.Labels["app"] = "web"
		list, err := mgr.ListSecrets("default", opts)
		require.NoError(t, err)
		require.NotNil(t, list)
	})

	t.Run("list secrets by type", func(t *testing.T) {
		s1 := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "tls-secret",
				Namespace: "default",
			},
			Type: corev1.SecretTypeTLS,
		}
		s2 := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "opaque-secret",
				Namespace: "default",
			},
			Type: corev1.SecretTypeOpaque,
		}

		mgr := newTestClusterManager(s1, s2)

		opts := NewSecretListOptions()
		opts.Type = SecretTypeTLS
		list, err := mgr.ListSecrets("default", opts)
		require.NoError(t, err)
		require.NotNil(t, list)
	})

	t.Run("empty list when no secrets", func(t *testing.T) {
		mgr := newTestClusterManager()

		opts := NewSecretListOptions()
		list, err := mgr.ListSecrets("default", opts)
		require.NoError(t, err)
		require.NotNil(t, list)
		assert.Len(t, list.Items, 0)
	})

	t.Run("namespace defaults to default when empty", func(t *testing.T) {
		s1 := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "secret1",
				Namespace: "default",
			},
		}
		mgr := newTestClusterManager(s1)
		opts := NewSecretListOptions()

		list, err := mgr.ListSecrets("", opts)
		require.NoError(t, err)
		require.NotNil(t, list)
		assert.Len(t, list.Items, 1)
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}
		opts := NewSecretListOptions()

		_, err := mgr.ListSecrets("default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// CREATE FROM LITERALS TESTS
// ============================================================================

func TestCreateSecretFromLiterals(t *testing.T) {
	t.Run("create from literals successfully", func(t *testing.T) {
		mgr := newTestClusterManager()

		literals := map[string]string{
			"username": "admin",
			"password": "supersecret",
		}

		opts := NewSecretOptions()
		secret, err := mgr.CreateSecretFromLiterals("app-secret", "default", literals, opts)
		require.NoError(t, err)
		require.NotNil(t, secret)

		assert.Equal(t, "admin", secret.StringData["username"])
		assert.Equal(t, "supersecret", secret.StringData["password"])
	})

	t.Run("replaces data with literals", func(t *testing.T) {
		mgr := newTestClusterManager()

		literals := map[string]string{
			"key1": "value1",
		}

		opts := NewSecretOptions()
		opts.Data["existing"] = "data"
		opts.Labels["env"] = "prod"

		secret, err := mgr.CreateSecretFromLiterals("app-secret", "default", literals, opts)
		require.NoError(t, err)

		assert.Equal(t, "value1", secret.StringData["key1"])
		assert.NotContains(t, secret.StringData, "existing")
		assert.Equal(t, "prod", secret.Labels["env"])
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}

		literals := map[string]string{"key": "value"}
		opts := NewSecretOptions()

		_, err := mgr.CreateSecretFromLiterals("app-secret", "default", literals, opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// CREATE BASIC AUTH SECRET TESTS
// ============================================================================

func TestCreateBasicAuthSecret(t *testing.T) {
	t.Run("create basic auth secret successfully", func(t *testing.T) {
		mgr := newTestClusterManager()

		opts := NewSecretOptions()
		secret, err := mgr.CreateBasicAuthSecret("auth-secret", "default", "admin", "password123", opts)
		require.NoError(t, err)
		require.NotNil(t, secret)

		assert.Equal(t, "auth-secret", secret.Name)
		assert.Equal(t, corev1.SecretType(SecretTypeBasicAuth), secret.Type)
		assert.Equal(t, "admin", secret.StringData["username"])
		assert.Equal(t, "password123", secret.StringData["password"])
	})

	t.Run("create with empty username", func(t *testing.T) {
		mgr := newTestClusterManager()
		opts := NewSecretOptions()

		secret, err := mgr.CreateBasicAuthSecret("auth-secret", "default", "", "password", opts)
		require.NoError(t, err) // No validation, empty username is allowed
		assert.Equal(t, "", secret.StringData["username"])
		assert.Equal(t, "password", secret.StringData["password"])
	})

	t.Run("create with empty password", func(t *testing.T) {
		mgr := newTestClusterManager()
		opts := NewSecretOptions()

		secret, err := mgr.CreateBasicAuthSecret("auth-secret", "default", "admin", "", opts)
		require.NoError(t, err) // No validation, empty password is allowed
		assert.Equal(t, "admin", secret.StringData["username"])
		assert.Equal(t, "", secret.StringData["password"])
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}
		opts := NewSecretOptions()

		_, err := mgr.CreateBasicAuthSecret("auth-secret", "default", "admin", "password", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// CREATE DOCKER REGISTRY SECRET TESTS
// ============================================================================

func TestCreateDockerRegistrySecret(t *testing.T) {
	t.Run("create docker registry secret successfully", func(t *testing.T) {
		mgr := newTestClusterManager()

		opts := NewSecretOptions()
		secret, err := mgr.CreateDockerRegistrySecret(
			"docker-secret",
			"default",
			"docker.io",
			"myuser",
			"mypass",
			"user@example.com",
			opts,
		)
		require.NoError(t, err)
		require.NotNil(t, secret)

		assert.Equal(t, "docker-secret", secret.Name)
		assert.Equal(t, corev1.SecretType(SecretTypeDockerConfigJson), secret.Type)
		assert.Contains(t, secret.StringData, ".dockerconfigjson")
	})

	t.Run("create with empty server", func(t *testing.T) {
		mgr := newTestClusterManager()
		opts := NewSecretOptions()

		secret, err := mgr.CreateDockerRegistrySecret("docker-secret", "default", "", "user", "pass", "email", opts)
		require.NoError(t, err) // No validation, empty server is allowed
		require.NotNil(t, secret)
		assert.Contains(t, secret.StringData, ".dockerconfigjson")
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}
		opts := NewSecretOptions()

		_, err := mgr.CreateDockerRegistrySecret("docker-secret", "default", "server", "user", "pass", "email", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// OPERATIONS.GO WRAPPER TESTS
// ============================================================================

func TestGetSecrets(t *testing.T) {
	t.Run("get secrets from namespace", func(t *testing.T) {
		s1 := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "secret1",
				Namespace: "default",
			},
			StringData: map[string]string{"key": "value"},
		}

		mgr := newTestClusterManager(s1)

		secrets, err := mgr.GetSecrets("default")
		require.NoError(t, err)
		assert.Len(t, secrets, 1)
		assert.Equal(t, "secret1", secrets[0].Name)
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}

		_, err := mgr.GetSecrets("default")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

func TestGetSecretByName(t *testing.T) {
	t.Run("get secret by name", func(t *testing.T) {
		s1 := &corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{
				Name:      "test-secret",
				Namespace: "default",
			},
			StringData: map[string]string{"key": "value"},
		}

		mgr := newTestClusterManager(s1)

		secret, err := mgr.GetSecretByName("default", "test-secret")
		require.NoError(t, err)
		require.NotNil(t, secret)
		assert.Equal(t, "test-secret", secret.Name)
	})

	t.Run("error when not found", func(t *testing.T) {
		mgr := newTestClusterManager()

		_, err := mgr.GetSecretByName("default", "nonexistent")
		require.Error(t, err)
	})

	t.Run("error when not connected", func(t *testing.T) {
		mgr := &ClusterManager{connected: false}

		_, err := mgr.GetSecretByName("default", "test-secret")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})
}

// ============================================================================
// HELPER FUNCTION: Reuses newTestClusterManager from operations_test.go
// ============================================================================
