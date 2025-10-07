package k8s

import (
	"context"
	"fmt"
	"strings"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/dynamic"
)

// ApplyResource applies a single Kubernetes resource
func (cm *ClusterManager) ApplyResource(obj *unstructured.Unstructured, opts *ApplyOptions) (*ApplyResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if obj == nil {
		return nil, fmt.Errorf("resource object is nil")
	}

	if opts == nil {
		opts = NewApplyOptions()
	}

	// Validate resource before applying
	if err := ValidateResourceForApply(obj); err != nil {
		return nil, fmt.Errorf("resource validation failed: %w", err)
	}

	// Override namespace if specified in options
	if opts.Namespace != "" {
		obj.SetNamespace(opts.Namespace)
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

	// Determine apply strategy
	if opts.ServerSide {
		return cm.applyServerSide(ctx, resourceInterface, obj, opts)
	}

	return cm.applyClientSide(ctx, resourceInterface, obj, opts)
}

// applyClientSide performs client-side apply (create or update)
func (cm *ClusterManager) applyClientSide(ctx context.Context, resourceInterface dynamic.ResourceInterface, obj *unstructured.Unstructured, opts *ApplyOptions) (*ApplyResult, error) {
	name := obj.GetName()

	// Check if resource exists
	existing, err := resourceInterface.Get(ctx, name, metav1.GetOptions{})
	resourceExists := err == nil

	// Handle dry-run
	dryRunOpts := []string{}
	if opts.DryRun == DryRunClient || opts.DryRun == DryRunServer {
		dryRunOpts = append(dryRunOpts, string(opts.DryRun))
	}

	var result *unstructured.Unstructured
	var action ApplyAction

	if !resourceExists {
		// Resource doesn't exist - CREATE
		if opts.DryRun == DryRunClient {
			// Client-side dry-run - just validate and return
			result = obj.DeepCopy()
			action = ApplyActionCreated
		} else {
			createOpts := metav1.CreateOptions{
				DryRun:       dryRunOpts,
				FieldManager: opts.FieldManager,
			}
			result, err = resourceInterface.Create(ctx, obj, createOpts)
			if err != nil {
				return nil, fmt.Errorf("failed to create resource %s: %w", ExtractResourceIdentifier(obj), err)
			}
			action = ApplyActionCreated
		}
	} else {
		// Resource exists - UPDATE
		if opts.Force {
			// Force update - replace entire resource
			obj.SetResourceVersion(existing.GetResourceVersion())

			if opts.DryRun == DryRunClient {
				result = obj.DeepCopy()
				action = ApplyActionConfigured
			} else {
				updateOpts := metav1.UpdateOptions{
					DryRun:       dryRunOpts,
					FieldManager: opts.FieldManager,
				}
				result, err = resourceInterface.Update(ctx, obj, updateOpts)
				if err != nil {
					return nil, fmt.Errorf("failed to update resource %s: %w", ExtractResourceIdentifier(obj), err)
				}
				action = ApplyActionConfigured
			}
		} else {
			// Merge update - only update changed fields
			if opts.DryRun == DryRunClient {
				result = obj.DeepCopy()
				action = ApplyActionConfigured
			} else {
				// For non-force updates, use Patch with merge strategy
				patchData, err := obj.MarshalJSON()
				if err != nil {
					return nil, fmt.Errorf("failed to marshal resource: %w", err)
				}

				patchOpts := metav1.PatchOptions{
					DryRun:       dryRunOpts,
					FieldManager: opts.FieldManager,
					Force:        &opts.Force,
				}

				result, err = resourceInterface.Patch(ctx, name, types.MergePatchType, patchData, patchOpts)
				if err != nil {
					return nil, fmt.Errorf("failed to patch resource %s: %w", ExtractResourceIdentifier(obj), err)
				}
				action = ApplyActionConfigured
			}
		}
	}

	return &ApplyResult{
		Object:   result,
		Action:   action,
		Warnings: []string{},
		DryRun:   opts.DryRun != DryRunNone,
	}, nil
}

// applyServerSide performs server-side apply
func (cm *ClusterManager) applyServerSide(ctx context.Context, resourceInterface dynamic.ResourceInterface, obj *unstructured.Unstructured, opts *ApplyOptions) (*ApplyResult, error) {
	name := obj.GetName()

	// Prepare patch data
	patchData, err := obj.MarshalJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to marshal resource: %w", err)
	}

	// Handle dry-run
	dryRunOpts := []string{}
	if opts.DryRun == DryRunClient || opts.DryRun == DryRunServer {
		dryRunOpts = append(dryRunOpts, string(opts.DryRun))
	}

	// Server-side apply options
	patchOpts := metav1.PatchOptions{
		DryRun:       dryRunOpts,
		FieldManager: opts.FieldManager,
		Force:        &opts.Force,
	}

	result, err := resourceInterface.Patch(ctx, name, types.ApplyPatchType, patchData, patchOpts)
	if err != nil {
		return nil, fmt.Errorf("server-side apply failed for %s: %w", ExtractResourceIdentifier(obj), err)
	}

	return &ApplyResult{
		Object:   result,
		Action:   ApplyActionServerSideApplied,
		Warnings: []string{},
		DryRun:   opts.DryRun != DryRunNone,
	}, nil
}

// ApplyFile applies resources from a file
func (cm *ClusterManager) ApplyFile(filePath string, opts *ApplyOptions) (*BatchResult, error) {
	parser := NewResourceParser()

	// Parse file
	resources, err := parser.ParseFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to parse file %s: %w", filePath, err)
	}

	return cm.ApplyResources(resources, opts)
}

// ApplyDirectory applies all resources from a directory
func (cm *ClusterManager) ApplyDirectory(dirPath string, recursive bool, opts *ApplyOptions) (*BatchResult, error) {
	parser := NewResourceParser()

	// Parse directory
	resources, err := parser.ParseDirectory(dirPath, recursive)
	if err != nil {
		return nil, fmt.Errorf("failed to parse directory %s: %w", dirPath, err)
	}

	return cm.ApplyResources(resources, opts)
}

// ApplyString applies resources from a YAML/JSON string
func (cm *ClusterManager) ApplyString(content string, opts *ApplyOptions) (*BatchResult, error) {
	parser := NewResourceParser()

	// Parse string
	resources, err := parser.ParseString(content)
	if err != nil {
		return nil, fmt.Errorf("failed to parse content: %w", err)
	}

	return cm.ApplyResources(resources, opts)
}

// ApplyResources applies multiple resources in batch
func (cm *ClusterManager) ApplyResources(resources []*ParsedResource, opts *ApplyOptions) (*BatchResult, error) {
	if opts == nil {
		opts = NewApplyOptions()
	}

	// Convert to batch options
	batchOpts := &BatchApplyOptions{
		ApplyOptions:    opts,
		ContinueOnError: false,
		Parallel:        false,
		MaxParallel:     1,
	}

	return cm.ApplyResourcesBatch(resources, batchOpts)
}

// ApplyResourcesBatch applies resources with batch options
func (cm *ClusterManager) ApplyResourcesBatch(resources []*ParsedResource, opts *BatchApplyOptions) (*BatchResult, error) {
	if opts == nil {
		opts = NewBatchApplyOptions()
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

	// Apply resources sequentially (parallel implementation would be future enhancement)
	for _, resource := range resources {
		applyResult, err := cm.ApplyResource(resource.Object, opts.ApplyOptions)

		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, err)

			if !opts.ContinueOnError {
				// Stop on first error
				break
			}
			continue
		}

		result.Successful++
		result.Results = append(result.Results, applyResult)
	}

	result.Duration = time.Since(startTime)
	return result, nil
}

// ValidateBeforeApply validates a resource before applying
func (cm *ClusterManager) ValidateBeforeApply(obj *unstructured.Unstructured) (*ValidationResult, error) {
	result := NewValidationResult()

	// Basic structure validation
	if err := ValidateResourceForApply(obj); err != nil {
		result.AddError("resource", err.Error(), ValidationErrorTypeInvalid)
		return result, nil
	}

	// Check if resource kind is supported by cluster
	gvr, err := cm.getGVR(obj)
	if err != nil {
		result.AddError("kind", fmt.Sprintf("unsupported resource kind: %s", obj.GetKind()), ValidationErrorTypeNotSupported)
		return result, nil
	}

	// Validate namespace requirements
	if !cm.isClusterScoped(gvr) && obj.GetNamespace() == "" {
		result.AddError("metadata.namespace", "namespace is required for namespaced resources", ValidationErrorTypeRequired)
	}

	return result, nil
}

// ========================================================================
// HELPER METHODS
// ========================================================================

// getGVR returns the GroupVersionResource for a given object
func (cm *ClusterManager) getGVR(obj *unstructured.Unstructured) (schema.GroupVersionResource, error) {
	gvk := obj.GroupVersionKind()

	// Map common resource kinds to their GVR
	// This is a simplified mapping - production code would use discovery client
	kind := gvk.Kind
	group := gvk.Group
	version := gvk.Version

	// Determine resource name (plural form)
	var resource string
	switch kind {
	case "Pod":
		resource = "pods"
	case "Service":
		resource = "services"
	case "Deployment":
		resource = "deployments"
	case "StatefulSet":
		resource = "statefulsets"
	case "DaemonSet":
		resource = "daemonsets"
	case "ReplicaSet":
		resource = "replicasets"
	case "Job":
		resource = "jobs"
	case "CronJob":
		resource = "cronjobs"
	case "ConfigMap":
		resource = "configmaps"
	case "Secret":
		resource = "secrets"
	case "Namespace":
		resource = "namespaces"
	case "Node":
		resource = "nodes"
	case "PersistentVolume":
		resource = "persistentvolumes"
	case "PersistentVolumeClaim":
		resource = "persistentvolumeclaims"
	case "Ingress":
		resource = "ingresses"
	case "NetworkPolicy":
		resource = "networkpolicies"
	case "ServiceAccount":
		resource = "serviceaccounts"
	default:
		// Try lowercase + s as fallback
		resource = strings.ToLower(kind) + "s"
	}

	return schema.GroupVersionResource{
		Group:    group,
		Version:  version,
		Resource: resource,
	}, nil
}

// getDynamicResourceInterface returns the appropriate resource interface
func (cm *ClusterManager) getDynamicResourceInterface(gvr schema.GroupVersionResource, namespace string) dynamic.ResourceInterface {
	if namespace != "" {
		return cm.dynamicClient.Resource(gvr).Namespace(namespace)
	}
	return cm.dynamicClient.Resource(gvr)
}

// isClusterScoped checks if a resource is cluster-scoped
func (cm *ClusterManager) isClusterScoped(gvr schema.GroupVersionResource) bool {
	// Common cluster-scoped resources
	clusterScopedResources := map[string]bool{
		"namespaces":              true,
		"nodes":                   true,
		"persistentvolumes":       true,
		"clusterroles":            true,
		"clusterrolebindings":     true,
		"customresourcedefinitions": true,
		"storageclasses":          true,
	}

	return clusterScopedResources[gvr.Resource]
}

// CompareResources compares two resources to determine if they differ
func CompareResources(obj1, obj2 *unstructured.Unstructured) bool {
	if obj1 == nil || obj2 == nil {
		return false
	}

	// Compare key fields
	if obj1.GetAPIVersion() != obj2.GetAPIVersion() {
		return false
	}
	if obj1.GetKind() != obj2.GetKind() {
		return false
	}
	if obj1.GetNamespace() != obj2.GetNamespace() {
		return false
	}
	if obj1.GetName() != obj2.GetName() {
		return false
	}

	// Deep comparison of spec (simplified - production would compare more fields)
	spec1, ok1, _ := unstructured.NestedMap(obj1.Object, "spec")
	spec2, ok2, _ := unstructured.NestedMap(obj2.Object, "spec")

	if ok1 != ok2 {
		return false
	}

	if ok1 && ok2 {
		// Simple comparison - in production, would do deep comparison
		return fmt.Sprintf("%v", spec1) == fmt.Sprintf("%v", spec2)
	}

	return true
}
