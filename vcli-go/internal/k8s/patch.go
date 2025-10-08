package k8s

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/types"
)

// PatchResource patches a single Kubernetes resource
func (cm *ClusterManager) PatchResource(obj *unstructured.Unstructured, opts *PatchOptions) (*PatchResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if obj == nil {
		return nil, fmt.Errorf("resource object is nil")
	}

	if opts == nil {
		return nil, fmt.Errorf("patch options are required")
	}

	// Validate patch data
	if len(opts.Patch) == 0 {
		return nil, fmt.Errorf("patch data is empty")
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// Get dynamic resource interface
	gvr, err := cm.getGVR(obj)
	if err != nil {
		return nil, fmt.Errorf("failed to get resource GVR: %w", err)
	}

	resourceInterface := cm.getDynamicResourceInterface(gvr, obj.GetNamespace())
	name := obj.GetName()

	// Check if resource exists
	_, err = resourceInterface.Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("resource not found: %w", err)
	}

	// Handle dry-run
	dryRunOpts := []string{}
	if opts.DryRun == DryRunClient || opts.DryRun == DryRunServer {
		dryRunOpts = append(dryRunOpts, string(opts.DryRun))
	}

	// Prepare patch options
	patchOpts := metav1.PatchOptions{
		DryRun:       dryRunOpts,
		FieldManager: opts.FieldManager,
		Force:        &opts.Force,
	}

	// Apply patch based on type
	var patchType types.PatchType
	switch opts.PatchType {
	case PatchTypeJSON:
		patchType = types.JSONPatchType
	case PatchTypeMerge:
		patchType = types.MergePatchType
	case PatchTypeStrategic:
		patchType = types.StrategicMergePatchType
	case PatchTypeApply:
		patchType = types.ApplyPatchType
	default:
		return nil, fmt.Errorf("unsupported patch type: %s", opts.PatchType)
	}

	// Execute patch
	startTime := time.Now()
	result, err := resourceInterface.Patch(ctx, name, patchType, opts.Patch, patchOpts)
	duration := time.Since(startTime)

	if err != nil {
		return nil, fmt.Errorf("failed to patch resource %s: %w", ExtractResourceIdentifier(obj), err)
	}

	return &PatchResult{
		Object:     result,
		PatchType:  opts.PatchType,
		Applied:    true,
		Message:    "resource patched successfully",
		Duration:   duration,
		DryRun:     opts.DryRun != DryRunNone,
	}, nil
}

// PatchByName patches a resource by name, kind, and namespace
func (cm *ClusterManager) PatchByName(kind, name, namespace string, opts *PatchOptions) (*PatchResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if opts == nil {
		return nil, fmt.Errorf("patch options are required")
	}

	if len(opts.Patch) == 0 {
		return nil, fmt.Errorf("patch data is empty")
	}

	// Create a minimal unstructured object for GVR lookup
	obj := &unstructured.Unstructured{}
	obj.SetKind(kind)
	obj.SetName(name)
	obj.SetNamespace(namespace)

	// Get GVR
	gvr, err := cm.getGVR(obj)
	if err != nil {
		return nil, fmt.Errorf("failed to get resource GVR for kind %s: %w", kind, err)
	}

	resourceInterface := cm.getDynamicResourceInterface(gvr, namespace)

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// Check if resource exists
	_, err = resourceInterface.Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("resource not found: %w", err)
	}

	// Handle dry-run
	dryRunOpts := []string{}
	if opts.DryRun == DryRunClient || opts.DryRun == DryRunServer {
		dryRunOpts = append(dryRunOpts, string(opts.DryRun))
	}

	// Prepare patch options
	patchOpts := metav1.PatchOptions{
		DryRun:       dryRunOpts,
		FieldManager: opts.FieldManager,
		Force:        &opts.Force,
	}

	// Apply patch based on type
	var patchType types.PatchType
	switch opts.PatchType {
	case PatchTypeJSON:
		patchType = types.JSONPatchType
	case PatchTypeMerge:
		patchType = types.MergePatchType
	case PatchTypeStrategic:
		patchType = types.StrategicMergePatchType
	case PatchTypeApply:
		patchType = types.ApplyPatchType
	default:
		return nil, fmt.Errorf("unsupported patch type: %s", opts.PatchType)
	}

	// Execute patch
	startTime := time.Now()
	result, err := resourceInterface.Patch(ctx, name, patchType, opts.Patch, patchOpts)
	duration := time.Since(startTime)

	if err != nil {
		return nil, fmt.Errorf("failed to patch %s/%s: %w", kind, name, err)
	}

	return &PatchResult{
		Object:     result,
		PatchType:  opts.PatchType,
		Applied:    true,
		Message:    "resource patched successfully",
		Duration:   duration,
		DryRun:     opts.DryRun != DryRunNone,
	}, nil
}

// PatchFile patches resources from a file
func (cm *ClusterManager) PatchFile(filePath string, opts *PatchOptions) (*BatchResult, error) {
	parser := NewResourceParser()

	// Parse file
	resources, err := parser.ParseFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to parse file %s: %w", filePath, err)
	}

	return cm.PatchResources(resources, opts)
}

// PatchResources patches multiple resources in batch
func (cm *ClusterManager) PatchResources(resources []*ParsedResource, opts *PatchOptions) (*BatchResult, error) {
	if opts == nil {
		return nil, fmt.Errorf("patch options are required")
	}

	startTime := time.Now()
	result := &BatchResult{
		Total:      len(resources),
		Successful: 0,
		Failed:     0,
		Skipped:    0,
		Results:    make([]interface{}, 0),
		Errors:     make([]error, 0),
	}

	// Patch resources sequentially
	for _, resource := range resources {
		patchResult, err := cm.PatchResource(resource.Object, opts)

		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, err)
			continue
		}

		result.Successful++
		result.Results = append(result.Results, patchResult)
	}

	result.Duration = time.Since(startTime)
	return result, nil
}

// GenerateJSONPatch generates a JSON patch from old and new objects
func GenerateJSONPatch(oldObj, newObj *unstructured.Unstructured) ([]byte, error) {
	if oldObj == nil || newObj == nil {
		return nil, fmt.Errorf("both old and new objects are required")
	}

	// Marshal both objects
	oldJSON, err := oldObj.MarshalJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to marshal old object: %w", err)
	}

	newJSON, err := newObj.MarshalJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to marshal new object: %w", err)
	}

	// Compare and generate patch operations
	var oldData, newData map[string]interface{}
	if err := json.Unmarshal(oldJSON, &oldData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal old JSON: %w", err)
	}
	if err := json.Unmarshal(newJSON, &newData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal new JSON: %w", err)
	}

	// Generate patch operations (simplified - full implementation would use jsonpatch library)
	patches := []map[string]interface{}{}

	// For simplicity, generate replace operations for changed fields
	for key, newValue := range newData {
		if key == "metadata" || key == "status" {
			continue
		}

		oldValue, exists := oldData[key]
		if !exists || fmt.Sprintf("%v", oldValue) != fmt.Sprintf("%v", newValue) {
			patches = append(patches, map[string]interface{}{
				"op":    "replace",
				"path":  "/" + key,
				"value": newValue,
			})
		}
	}

	return json.Marshal(patches)
}

// GenerateMergePatch generates a merge patch from old and new objects
func GenerateMergePatch(oldObj, newObj *unstructured.Unstructured) ([]byte, error) {
	if oldObj == nil || newObj == nil {
		return nil, fmt.Errorf("both old and new objects are required")
	}

	// For merge patch, just return the new object's spec
	newJSON, err := newObj.MarshalJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to marshal new object: %w", err)
	}

	var newData map[string]interface{}
	if err := json.Unmarshal(newJSON, &newData); err != nil {
		return nil, fmt.Errorf("failed to unmarshal new JSON: %w", err)
	}

	// Extract only the fields to merge
	mergePatch := make(map[string]interface{})
	if spec, ok := newData["spec"]; ok {
		mergePatch["spec"] = spec
	}
	if metadata, ok := newData["metadata"]; ok {
		if metadataMap, ok := metadata.(map[string]interface{}); ok {
			// Only include labels and annotations from metadata
			filteredMetadata := make(map[string]interface{})
			if labels, ok := metadataMap["labels"]; ok {
				filteredMetadata["labels"] = labels
			}
			if annotations, ok := metadataMap["annotations"]; ok {
				filteredMetadata["annotations"] = annotations
			}
			if len(filteredMetadata) > 0 {
				mergePatch["metadata"] = filteredMetadata
			}
		}
	}

	return json.Marshal(mergePatch)
}

// ValidatePatch validates patch data
func ValidatePatch(patchData []byte, patchType PatchType) error {
	if len(patchData) == 0 {
		return fmt.Errorf("patch data is empty")
	}

	switch patchType {
	case PatchTypeJSON:
		// Validate JSON patch format
		var patches []map[string]interface{}
		if err := json.Unmarshal(patchData, &patches); err != nil {
			return fmt.Errorf("invalid JSON patch format: %w", err)
		}
		// Validate each operation
		for i, patch := range patches {
			op, ok := patch["op"].(string)
			if !ok {
				return fmt.Errorf("patch operation %d missing 'op' field", i)
			}
			if op != "add" && op != "remove" && op != "replace" && op != "move" && op != "copy" && op != "test" {
				return fmt.Errorf("patch operation %d has invalid op: %s", i, op)
			}
			if _, ok := patch["path"]; !ok {
				return fmt.Errorf("patch operation %d missing 'path' field", i)
			}
		}

	case PatchTypeMerge, PatchTypeStrategic, PatchTypeApply:
		// Validate JSON object format
		var data map[string]interface{}
		if err := json.Unmarshal(patchData, &data); err != nil {
			return fmt.Errorf("invalid patch format: %w", err)
		}

	default:
		return fmt.Errorf("unsupported patch type: %s", patchType)
	}

	return nil
}
