package k8s

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// CAN I TESTS
// ============================================================================

func TestCanI(t *testing.T) {
	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		_, err := cm.CanI("get", "pods", "default")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})

	t.Run("error when verb is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanI("", "pods", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "verb cannot be empty")
	})

	t.Run("error when resource is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanI("get", "", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "resource cannot be empty")
	})

	t.Run("allows empty namespace for cluster-scoped resources", func(t *testing.T) {
		cm := newTestClusterManager()

		// Note: With fake clientset, this will likely fail at API call
		// but validates that empty namespace is allowed (cluster-scoped)
		_, err := cm.CanI("get", "nodes", "")
		// We expect an error from fake client, but not from validation
		if err != nil {
			assert.NotContains(t, err.Error(), "namespace cannot be empty")
		}
	})
}

// ============================================================================
// CAN I WITH RESOURCE NAME TESTS
// ============================================================================

func TestCanIWithResourceName(t *testing.T) {
	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		_, err := cm.CanIWithResourceName("get", "pods", "my-pod", "default")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})

	t.Run("error when verb is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanIWithResourceName("", "pods", "my-pod", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "verb cannot be empty")
	})

	t.Run("error when resource is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanIWithResourceName("get", "", "my-pod", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "resource cannot be empty")
	})

	t.Run("allows empty resource name", func(t *testing.T) {
		cm := newTestClusterManager()

		// Empty resource name is valid (checks if can access any resource of that type)
		_, err := cm.CanIWithResourceName("get", "pods", "", "default")
		// May error from fake client, but not from validation
		if err != nil {
			assert.NotContains(t, err.Error(), "resource name cannot be empty")
		}
	})

	t.Run("allows empty namespace", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanIWithResourceName("get", "nodes", "my-node", "")
		// May error from fake client, but not from validation
		if err != nil {
			assert.NotContains(t, err.Error(), "namespace cannot be empty")
		}
	})
}

// ============================================================================
// CAN I WITH SUBRESOURCE TESTS
// ============================================================================

func TestCanIWithSubresource(t *testing.T) {
	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		_, err := cm.CanIWithSubresource("get", "pods", "log", "default")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})

	t.Run("error when verb is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanIWithSubresource("", "pods", "log", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "verb cannot be empty")
	})

	t.Run("error when resource is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanIWithSubresource("get", "", "log", "default")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "resource cannot be empty")
	})

	t.Run("allows empty subresource", func(t *testing.T) {
		cm := newTestClusterManager()

		// Empty subresource is valid
		_, err := cm.CanIWithSubresource("get", "pods", "", "default")
		// May error from fake client, but not from validation
		if err != nil {
			assert.NotContains(t, err.Error(), "subresource cannot be empty")
		}
	})

	t.Run("allows empty namespace", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanIWithSubresource("get", "nodes", "status", "")
		// May error from fake client, but not from validation
		if err != nil {
			assert.NotContains(t, err.Error(), "namespace cannot be empty")
		}
	})
}

// ============================================================================
// CAN I NON-RESOURCE TESTS
// ============================================================================

func TestCanINonResource(t *testing.T) {
	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		_, err := cm.CanINonResource("get", "/api")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})

	t.Run("error when verb is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanINonResource("", "/api")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "verb cannot be empty")
	})

	t.Run("error when non-resource URL is empty", func(t *testing.T) {
		cm := newTestClusterManager()

		_, err := cm.CanINonResource("get", "")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "non-resource URL cannot be empty")
	})

	t.Run("validates URL paths", func(t *testing.T) {
		cm := newTestClusterManager()

		testCases := []struct {
			name string
			url  string
		}{
			{"api path", "/api"},
			{"apis path", "/apis"},
			{"healthz path", "/healthz"},
			{"metrics path", "/metrics"},
			{"version path", "/version"},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				_, err := cm.CanINonResource("get", tc.url)
				// May error from fake client, but validates URL is accepted
				if err != nil {
					assert.NotContains(t, err.Error(), "invalid URL")
				}
			})
		}
	})
}

// ============================================================================
// WHO AM I TESTS
// ============================================================================

func TestWhoAmI(t *testing.T) {
	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}

		_, err := cm.WhoAmI()
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})

	// Note: Real tests with fake clientset would require mocking
	// AuthenticationV1 API which is complex. These tests cover validation
	// and error paths effectively.
}

// ============================================================================
// AUTH CHECK RESULT STRUCT TESTS
// ============================================================================

func TestAuthCheckResult(t *testing.T) {
	t.Run("create allowed result", func(t *testing.T) {
		result := &AuthCheckResult{
			Allowed:         true,
			Reason:          "policy allows",
			EvaluationError: "",
		}

		assert.True(t, result.Allowed)
		assert.Equal(t, "policy allows", result.Reason)
		assert.Empty(t, result.EvaluationError)
	})

	t.Run("create denied result", func(t *testing.T) {
		result := &AuthCheckResult{
			Allowed:         false,
			Reason:          "insufficient permissions",
			EvaluationError: "",
		}

		assert.False(t, result.Allowed)
		assert.Equal(t, "insufficient permissions", result.Reason)
		assert.Empty(t, result.EvaluationError)
	})

	t.Run("create result with evaluation error", func(t *testing.T) {
		result := &AuthCheckResult{
			Allowed:         false,
			Reason:          "",
			EvaluationError: "policy evaluation failed",
		}

		assert.False(t, result.Allowed)
		assert.Empty(t, result.Reason)
		assert.Equal(t, "policy evaluation failed", result.EvaluationError)
	})
}

// ============================================================================
// USER INFO STRUCT TESTS
// ============================================================================

func TestUserInfo(t *testing.T) {
	t.Run("create user info with groups", func(t *testing.T) {
		userInfo := &UserInfo{
			Username: "admin",
			UID:      "12345",
			Groups:   []string{"system:masters", "developers"},
			Extra:    make(map[string][]string),
		}

		assert.Equal(t, "admin", userInfo.Username)
		assert.Equal(t, "12345", userInfo.UID)
		assert.Len(t, userInfo.Groups, 2)
		assert.Contains(t, userInfo.Groups, "system:masters")
		assert.Contains(t, userInfo.Groups, "developers")
	})

	t.Run("create user info with extra fields", func(t *testing.T) {
		userInfo := &UserInfo{
			Username: "user",
			UID:      "67890",
			Groups:   []string{"developers"},
			Extra: map[string][]string{
				"scopes": {"read", "write"},
				"roles":  {"admin"},
			},
		}

		assert.Equal(t, "user", userInfo.Username)
		assert.NotNil(t, userInfo.Extra)
		assert.Equal(t, []string{"read", "write"}, userInfo.Extra["scopes"])
		assert.Equal(t, []string{"admin"}, userInfo.Extra["roles"])
	})

	t.Run("create minimal user info", func(t *testing.T) {
		userInfo := &UserInfo{
			Username: "serviceaccount",
			UID:      "sa-123",
			Groups:   []string{},
			Extra:    make(map[string][]string),
		}

		assert.Equal(t, "serviceaccount", userInfo.Username)
		assert.Equal(t, "sa-123", userInfo.UID)
		assert.Empty(t, userInfo.Groups)
		assert.Empty(t, userInfo.Extra)
	})
}

// ============================================================================
// VALIDATION EDGE CASES TESTS
// ============================================================================

func TestAuthValidationEdgeCases(t *testing.T) {
	t.Run("CanI validation order", func(t *testing.T) {
		cm := newTestClusterManager()

		// Test that connected check comes before parameter validation
		disconnectedCM := &ClusterManager{connected: false}
		_, err := disconnectedCM.CanI("", "", "")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected) // Should fail on connection first

		// Test verb validation before resource validation
		_, err = cm.CanI("", "", "")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "verb") // Should fail on verb first
	})

	t.Run("CanIWithResourceName validation order", func(t *testing.T) {
		cm := newTestClusterManager()

		disconnectedCM := &ClusterManager{connected: false}
		_, err := disconnectedCM.CanIWithResourceName("", "", "", "")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)

		_, err = cm.CanIWithResourceName("", "", "", "")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "verb")
	})

	t.Run("CanIWithSubresource validation order", func(t *testing.T) {
		cm := newTestClusterManager()

		disconnectedCM := &ClusterManager{connected: false}
		_, err := disconnectedCM.CanIWithSubresource("", "", "", "")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)

		_, err = cm.CanIWithSubresource("", "", "", "")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "verb")
	})

	t.Run("CanINonResource validation order", func(t *testing.T) {
		cm := newTestClusterManager()

		disconnectedCM := &ClusterManager{connected: false}
		_, err := disconnectedCM.CanINonResource("", "")
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)

		_, err = cm.CanINonResource("", "")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "verb")
	})
}

// ============================================================================
// COMMON VERBS AND RESOURCES TESTS
// ============================================================================

func TestCommonK8sVerbs(t *testing.T) {
	cm := newTestClusterManager()

	verbs := []string{"get", "list", "watch", "create", "update", "patch", "delete", "deletecollection"}

	for _, verb := range verbs {
		t.Run("validates verb "+verb, func(t *testing.T) {
			_, err := cm.CanI(verb, "pods", "default")
			// Should not fail on verb validation
			if err != nil {
				assert.NotContains(t, err.Error(), "verb cannot be empty")
			}
		})
	}
}

func TestCommonK8sResources(t *testing.T) {
	cm := newTestClusterManager()

	resources := []string{"pods", "services", "deployments", "configmaps", "secrets", "nodes", "namespaces"}

	for _, resource := range resources {
		t.Run("validates resource "+resource, func(t *testing.T) {
			_, err := cm.CanI("get", resource, "default")
			// Should not fail on resource validation
			if err != nil {
				assert.NotContains(t, err.Error(), "resource cannot be empty")
			}
		})
	}
}

func TestCommonSubresources(t *testing.T) {
	cm := newTestClusterManager()

	subresources := []string{"status", "scale", "log", "exec", "portforward"}

	for _, subresource := range subresources {
		t.Run("validates subresource "+subresource, func(t *testing.T) {
			_, err := cm.CanIWithSubresource("get", "pods", subresource, "default")
			// Should not fail on validation
			if err != nil {
				assert.NotContains(t, err.Error(), "cannot be empty")
			}
		})
	}
}
