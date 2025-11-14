package k8s

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// NEW LABEL ANNOTATE OPTIONS TESTS
// ============================================================================

func TestNewLabelAnnotateOptions(t *testing.T) {
	t.Run("creates options with defaults", func(t *testing.T) {
		opts := NewLabelAnnotateOptions()

		require.NotNil(t, opts)
		assert.NotNil(t, opts.Changes)
		assert.Len(t, opts.Changes, 0)
		assert.False(t, opts.Overwrite)
		assert.Equal(t, DryRunNone, opts.DryRun)
		assert.False(t, opts.All)
		assert.Equal(t, "", opts.Selector)
	})
}

// ============================================================================
// PARSE LABEL CHANGES TESTS
// ============================================================================

func TestParseLabelChanges(t *testing.T) {
	t.Run("parse add operation", func(t *testing.T) {
		changes, err := ParseLabelChanges([]string{"env=prod"})
		require.NoError(t, err)
		require.Len(t, changes, 1)

		assert.Equal(t, "env", changes[0].Key)
		assert.Equal(t, "prod", changes[0].Value)
		assert.Equal(t, LabelOperationAdd, changes[0].Operation)
	})

	t.Run("parse remove operation", func(t *testing.T) {
		changes, err := ParseLabelChanges([]string{"oldlabel-"})
		require.NoError(t, err)
		require.Len(t, changes, 1)

		assert.Equal(t, "oldlabel", changes[0].Key)
		assert.Equal(t, LabelOperationRemove, changes[0].Operation)
	})

	t.Run("parse multiple changes", func(t *testing.T) {
		changes, err := ParseLabelChanges([]string{"env=prod", "team=backend", "temp-"})
		require.NoError(t, err)
		require.Len(t, changes, 3)

		assert.Equal(t, "env", changes[0].Key)
		assert.Equal(t, "prod", changes[0].Value)
		assert.Equal(t, LabelOperationAdd, changes[0].Operation)

		assert.Equal(t, "team", changes[1].Key)
		assert.Equal(t, "backend", changes[1].Value)
		assert.Equal(t, LabelOperationAdd, changes[1].Operation)

		assert.Equal(t, "temp", changes[2].Key)
		assert.Equal(t, LabelOperationRemove, changes[2].Operation)
	})

	t.Run("parse value with equals sign", func(t *testing.T) {
		changes, err := ParseLabelChanges([]string{"url=https://example.com"})
		require.NoError(t, err)
		require.Len(t, changes, 1)

		assert.Equal(t, "url", changes[0].Key)
		assert.Equal(t, "https://example.com", changes[0].Value)
	})

	t.Run("parse empty value", func(t *testing.T) {
		changes, err := ParseLabelChanges([]string{"empty="})
		require.NoError(t, err)
		require.Len(t, changes, 1)

		assert.Equal(t, "empty", changes[0].Key)
		assert.Equal(t, "", changes[0].Value)
	})

	t.Run("error on invalid syntax", func(t *testing.T) {
		_, err := ParseLabelChanges([]string{"invalid"})
		require.Error(t, err)
		assert.Contains(t, err.Error(), "invalid syntax")
	})

	t.Run("error on empty key in add", func(t *testing.T) {
		_, err := ParseLabelChanges([]string{"=value"})
		require.Error(t, err)
		assert.Contains(t, err.Error(), "empty key")
	})

	t.Run("error on empty key in remove", func(t *testing.T) {
		_, err := ParseLabelChanges([]string{"-"})
		require.Error(t, err)
		assert.Contains(t, err.Error(), "invalid remove syntax")
	})

	t.Run("parse empty slice", func(t *testing.T) {
		changes, err := ParseLabelChanges([]string{})
		require.NoError(t, err)
		assert.Len(t, changes, 0)
	})
}

// ============================================================================
// MAP TO JSON TESTS
// ============================================================================

func TestMapToJSON(t *testing.T) {
	t.Run("empty map", func(t *testing.T) {
		result := mapToJSON(map[string]string{})
		assert.Equal(t, "{}", result)
	})

	t.Run("single entry", func(t *testing.T) {
		result := mapToJSON(map[string]string{"key": "value"})
		assert.Equal(t, `{"key":"value"}`, result)
	})

	t.Run("multiple entries", func(t *testing.T) {
		result := mapToJSON(map[string]string{"env": "prod", "team": "backend"})
		// Order is not guaranteed, so check for both possible orderings
		assert.Contains(t, result, `"env":"prod"`)
		assert.Contains(t, result, `"team":"backend"`)
		assert.True(t, result[0] == '{' && result[len(result)-1] == '}')
	})

	t.Run("escape quotes in key", func(t *testing.T) {
		result := mapToJSON(map[string]string{`key"with"quotes`: "value"})
		assert.Contains(t, result, `key\"with\"quotes`)
	})

	t.Run("escape quotes in value", func(t *testing.T) {
		result := mapToJSON(map[string]string{"key": `value"with"quotes`})
		assert.Contains(t, result, `value\"with\"quotes`)
	})

	t.Run("nil map", func(t *testing.T) {
		result := mapToJSON(nil)
		assert.Equal(t, "{}", result)
	})
}

// ============================================================================
// VALIDATE LABEL KEY TESTS
// ============================================================================

func TestValidateLabelKey(t *testing.T) {
	t.Run("valid key", func(t *testing.T) {
		err := ValidateLabelKey("env")
		assert.NoError(t, err)
	})

	t.Run("valid key with prefix", func(t *testing.T) {
		err := ValidateLabelKey("example.com/app")
		assert.NoError(t, err)
	})

	t.Run("error on empty key", func(t *testing.T) {
		err := ValidateLabelKey("")
		require.Error(t, err)
		assert.Contains(t, err.Error(), "cannot be empty")
	})

	t.Run("error on too long key", func(t *testing.T) {
		longKey := string(make([]byte, 254))
		for i := range longKey {
			longKey = string(append([]byte(longKey[:i]), 'a'))
		}
		err := ValidateLabelKey(longKey)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "too long")
	})

	t.Run("max length key accepted", func(t *testing.T) {
		maxKey := string(make([]byte, 253))
		for i := 0; i < 253; i++ {
			maxKey = string(append([]byte(maxKey[:i]), 'a'))
		}
		err := ValidateLabelKey(maxKey)
		assert.NoError(t, err)
	})
}

// ============================================================================
// VALIDATE LABEL VALUE TESTS
// ============================================================================

func TestValidateLabelValue(t *testing.T) {
	t.Run("valid value", func(t *testing.T) {
		err := ValidateLabelValue("production")
		assert.NoError(t, err)
	})

	t.Run("empty value is valid", func(t *testing.T) {
		err := ValidateLabelValue("")
		assert.NoError(t, err)
	})

	t.Run("error on too long value", func(t *testing.T) {
		longValue := string(make([]byte, 64))
		for i := 0; i < 64; i++ {
			longValue = string(append([]byte(longValue[:i]), 'a'))
		}
		err := ValidateLabelValue(longValue)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "too long")
	})

	t.Run("max length value accepted", func(t *testing.T) {
		maxValue := string(make([]byte, 63))
		for i := 0; i < 63; i++ {
			maxValue = string(append([]byte(maxValue[:i]), 'a'))
		}
		err := ValidateLabelValue(maxValue)
		assert.NoError(t, err)
	})
}

// ============================================================================
// UPDATE LABELS TESTS (Integration with fake clientset)
// ============================================================================

func TestUpdateLabels(t *testing.T) {
	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}
		opts := NewLabelAnnotateOptions()
		opts.Changes = []LabelChange{{Key: "env", Value: "prod", Operation: LabelOperationAdd}}

		err := cm.UpdateLabels("Pod", "test-pod", "default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewLabelAnnotateOptions()
		opts.Changes = []LabelChange{{Key: "env", Value: "prod", Operation: LabelOperationAdd}}

		err := cm.UpdateLabels("Pod", "", "default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrResourceNameEmpty)
	})

	t.Run("error when no changes specified", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewLabelAnnotateOptions()

		err := cm.UpdateLabels("Pod", "test-pod", "default", opts)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "no changes specified")
	})

	t.Run("uses default options when nil", func(t *testing.T) {
		cm := newTestClusterManager()

		// With nil opts, should fail with "no changes specified"
		err := cm.UpdateLabels("Pod", "test-pod", "default", nil)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "no changes specified")
	})
}

// ============================================================================
// UPDATE ANNOTATIONS TESTS (Integration with fake clientset)
// ============================================================================

func TestUpdateAnnotations(t *testing.T) {
	t.Run("error when not connected", func(t *testing.T) {
		cm := &ClusterManager{connected: false}
		opts := NewLabelAnnotateOptions()
		opts.Changes = []LabelChange{{Key: "description", Value: "test", Operation: LabelOperationAdd}}

		err := cm.UpdateAnnotations("Pod", "test-pod", "default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrNotConnected)
	})

	t.Run("error when name is empty", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewLabelAnnotateOptions()
		opts.Changes = []LabelChange{{Key: "description", Value: "test", Operation: LabelOperationAdd}}

		err := cm.UpdateAnnotations("Pod", "", "default", opts)
		require.Error(t, err)
		assert.ErrorIs(t, err, ErrResourceNameEmpty)
	})

	t.Run("error when no changes specified", func(t *testing.T) {
		cm := newTestClusterManager()
		opts := NewLabelAnnotateOptions()

		err := cm.UpdateAnnotations("Pod", "test-pod", "default", opts)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "no changes specified")
	})

	t.Run("uses default options when nil", func(t *testing.T) {
		cm := newTestClusterManager()

		err := cm.UpdateAnnotations("Pod", "test-pod", "default", nil)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "no changes specified")
	})
}

// ============================================================================
// LABEL OPERATIONS ENUM TESTS
// ============================================================================

func TestLabelOperation(t *testing.T) {
	t.Run("label operation constants", func(t *testing.T) {
		assert.Equal(t, LabelOperation("add"), LabelOperationAdd)
		assert.Equal(t, LabelOperation("remove"), LabelOperationRemove)
	})
}

// ============================================================================
// LABEL CHANGE STRUCT TESTS
// ============================================================================

func TestLabelChange(t *testing.T) {
	t.Run("create label change for add", func(t *testing.T) {
		change := LabelChange{
			Key:       "env",
			Value:     "prod",
			Operation: LabelOperationAdd,
		}

		assert.Equal(t, "env", change.Key)
		assert.Equal(t, "prod", change.Value)
		assert.Equal(t, LabelOperationAdd, change.Operation)
	})

	t.Run("create label change for remove", func(t *testing.T) {
		change := LabelChange{
			Key:       "temp",
			Operation: LabelOperationRemove,
		}

		assert.Equal(t, "temp", change.Key)
		assert.Equal(t, "", change.Value)
		assert.Equal(t, LabelOperationRemove, change.Operation)
	})
}

// ============================================================================
// LABEL ANNOTATE OPTIONS TESTS
// ============================================================================

func TestLabelAnnotateOptions(t *testing.T) {
	t.Run("modify options after creation", func(t *testing.T) {
		opts := NewLabelAnnotateOptions()

		opts.Changes = append(opts.Changes, LabelChange{
			Key:       "env",
			Value:     "dev",
			Operation: LabelOperationAdd,
		})
		opts.Overwrite = true
		opts.DryRun = DryRunServer
		opts.All = true
		opts.Selector = "app=web"

		assert.Len(t, opts.Changes, 1)
		assert.True(t, opts.Overwrite)
		assert.Equal(t, DryRunServer, opts.DryRun)
		assert.True(t, opts.All)
		assert.Equal(t, "app=web", opts.Selector)
	})
}

// NOTE: UpdateMetadata integration tests with dynamic client are complex
// and require proper GVR/discovery setup. The pure function tests above
// provide good coverage for ParseLabelChanges, mapToJSON, and validation.
// Full integration tests would require a real K8s cluster or complex mocking.
