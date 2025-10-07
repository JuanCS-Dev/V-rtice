package k8s

import (
	"context"
	"fmt"
	"strings"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/types"
)

// LabelOperation represents a label operation type
type LabelOperation string

const (
	// LabelOperationAdd adds or updates a label
	LabelOperationAdd LabelOperation = "add"
	// LabelOperationRemove removes a label
	LabelOperationRemove LabelOperation = "remove"
)

// LabelChange represents a change to labels or annotations
type LabelChange struct {
	Key       string
	Value     string
	Operation LabelOperation
}

// LabelAnnotateOptions contains options for label/annotate operations
type LabelAnnotateOptions struct {
	// Changes to apply
	Changes []LabelChange
	// Overwrite existing values
	Overwrite bool
	// DryRun mode
	DryRun DryRunStrategy
	// Target all resources of this type
	All bool
	// Label selector for filtering
	Selector string
}

// NewLabelAnnotateOptions creates default options
func NewLabelAnnotateOptions() *LabelAnnotateOptions {
	return &LabelAnnotateOptions{
		Changes:   make([]LabelChange, 0),
		Overwrite: false,
		DryRun:    DryRunNone,
		All:       false,
	}
}

// UpdateLabels updates labels on a resource
func (cm *ClusterManager) UpdateLabels(kind, name, namespace string, opts *LabelAnnotateOptions) error {
	if opts == nil {
		opts = NewLabelAnnotateOptions()
	}

	return cm.updateMetadata(kind, name, namespace, opts, true)
}

// UpdateAnnotations updates annotations on a resource
func (cm *ClusterManager) UpdateAnnotations(kind, name, namespace string, opts *LabelAnnotateOptions) error {
	if opts == nil {
		opts = NewLabelAnnotateOptions()
	}

	return cm.updateMetadata(kind, name, namespace, opts, false)
}

// updateMetadata is the internal implementation for updating labels or annotations
func (cm *ClusterManager) updateMetadata(kind, name, namespace string, opts *LabelAnnotateOptions, isLabel bool) error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return ErrNotConnected
	}

	if name == "" {
		return ErrResourceNameEmpty
	}

	if len(opts.Changes) == 0 {
		return fmt.Errorf("no changes specified")
	}

	// Create a minimal unstructured object for GVR lookup
	obj := &unstructured.Unstructured{}
	obj.SetKind(kind)
	obj.SetName(name)
	obj.SetNamespace(namespace)

	// Get GVR
	gvr, err := cm.getGVR(obj)
	if err != nil {
		return fmt.Errorf("failed to get resource GVR for kind %s: %w", kind, err)
	}

	resourceInterface := cm.getDynamicResourceInterface(gvr, namespace)

	// Get current resource
	ctx := context.Background()
	current, err := resourceInterface.Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get resource %s/%s: %w", kind, name, err)
	}

	// Get current labels or annotations
	var currentMap map[string]string
	if isLabel {
		currentMap = current.GetLabels()
	} else {
		currentMap = current.GetAnnotations()
	}

	if currentMap == nil {
		currentMap = make(map[string]string)
	}

	// Apply changes
	newMap := make(map[string]string)
	for k, v := range currentMap {
		newMap[k] = v
	}

	for _, change := range opts.Changes {
		switch change.Operation {
		case LabelOperationAdd:
			// Check if key exists and overwrite is false
			if _, exists := newMap[change.Key]; exists && !opts.Overwrite {
				return fmt.Errorf("key '%s' already exists (use --overwrite to replace)", change.Key)
			}
			newMap[change.Key] = change.Value

		case LabelOperationRemove:
			delete(newMap, change.Key)
		}
	}

	// Handle dry-run
	if opts.DryRun != DryRunNone {
		return nil
	}

	// Create patch
	var patchData string
	if isLabel {
		patchData = fmt.Sprintf(`{"metadata":{"labels":%s}}`, mapToJSON(newMap))
	} else {
		patchData = fmt.Sprintf(`{"metadata":{"annotations":%s}}`, mapToJSON(newMap))
	}

	// Apply patch
	_, err = resourceInterface.Patch(ctx, name, types.MergePatchType, []byte(patchData), metav1.PatchOptions{})
	if err != nil {
		return fmt.Errorf("failed to patch resource: %w", err)
	}

	return nil
}

// ParseLabelChanges parses label/annotation change strings
// Format: "key=value" (add), "key-" (remove)
func ParseLabelChanges(changes []string) ([]LabelChange, error) {
	result := make([]LabelChange, 0, len(changes))

	for _, change := range changes {
		if strings.HasSuffix(change, "-") {
			// Remove operation
			key := strings.TrimSuffix(change, "-")
			if key == "" {
				return nil, fmt.Errorf("invalid remove syntax: %s", change)
			}
			result = append(result, LabelChange{
				Key:       key,
				Operation: LabelOperationRemove,
			})
		} else if strings.Contains(change, "=") {
			// Add operation
			parts := strings.SplitN(change, "=", 2)
			if len(parts) != 2 {
				return nil, fmt.Errorf("invalid add syntax: %s", change)
			}
			key := parts[0]
			value := parts[1]
			if key == "" {
				return nil, fmt.Errorf("empty key in: %s", change)
			}
			result = append(result, LabelChange{
				Key:       key,
				Value:     value,
				Operation: LabelOperationAdd,
			})
		} else {
			return nil, fmt.Errorf("invalid syntax: %s (expected 'key=value' or 'key-')", change)
		}
	}

	return result, nil
}

// mapToJSON converts a map to JSON string
func mapToJSON(m map[string]string) string {
	if len(m) == 0 {
		return "{}"
	}

	var parts []string
	for k, v := range m {
		// Escape quotes in key and value
		k = strings.ReplaceAll(k, `"`, `\"`)
		v = strings.ReplaceAll(v, `"`, `\"`)
		parts = append(parts, fmt.Sprintf(`"%s":"%s"`, k, v))
	}

	return "{" + strings.Join(parts, ",") + "}"
}

// ValidateLabelKey validates a label key according to Kubernetes rules
func ValidateLabelKey(key string) error {
	if key == "" {
		return fmt.Errorf("label key cannot be empty")
	}

	// Check length
	if len(key) > 253 {
		return fmt.Errorf("label key too long (max 253 characters)")
	}

	// Kubernetes label key validation would go here
	// For simplicity, we'll accept most keys
	return nil
}

// ValidateLabelValue validates a label value according to Kubernetes rules
func ValidateLabelValue(value string) error {
	// Check length
	if len(value) > 63 {
		return fmt.Errorf("label value too long (max 63 characters)")
	}

	// Kubernetes label value validation would go here
	return nil
}
