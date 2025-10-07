package k8s

import (
	"context"
	"fmt"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
)

// DeleteResource deletes a single Kubernetes resource
func (cm *ClusterManager) DeleteResource(obj *unstructured.Unstructured, opts *DeleteOptions) (*DeleteResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if obj == nil {
		return nil, fmt.Errorf("resource object is nil")
	}

	if opts == nil {
		opts = NewDeleteOptions()
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
	existing, err := resourceInterface.Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return &DeleteResult{
			Name:      name,
			Namespace: obj.GetNamespace(),
			Kind:      obj.GetKind(),
			Status:    DeleteStatusNotFound,
			Message:   fmt.Sprintf("resource not found: %v", err),
		}, nil
	}

	// Handle dry-run
	if opts.DryRun != DryRunNone {
		return &DeleteResult{
			Name:      name,
			Namespace: obj.GetNamespace(),
			Kind:      obj.GetKind(),
			Status:    DeleteStatusDeleted,
			Message:   "resource would be deleted (dry run)",
			DryRun:    true,
		}, nil
	}

	// Prepare delete options
	deleteOpts := metav1.DeleteOptions{}

	if opts.GracePeriodSeconds != nil {
		deleteOpts.GracePeriodSeconds = opts.GracePeriodSeconds
	}

	if opts.PropagationPolicy != "" {
		policy := metav1.DeletionPropagation(opts.PropagationPolicy)
		deleteOpts.PropagationPolicy = &policy
	}

	// Delete the resource
	startTime := time.Now()
	err = resourceInterface.Delete(ctx, name, deleteOpts)
	duration := time.Since(startTime)

	if err != nil {
		return nil, fmt.Errorf("failed to delete resource %s: %w", ExtractResourceIdentifier(existing), err)
	}

	result := &DeleteResult{
		Name:      name,
		Namespace: obj.GetNamespace(),
		Kind:      obj.GetKind(),
		Status:    DeleteStatusDeleted,
		Message:   "resource deleted successfully",
		Duration:  duration,
	}

	// Wait for deletion if requested
	if opts.Wait {
		waitErr := cm.waitForDeletion(ctx, resourceInterface, name, opts.WaitTimeout)
		if waitErr != nil {
			result.Message = fmt.Sprintf("resource deleted but wait failed: %v", waitErr)
		} else {
			result.Message = "resource deleted and confirmed"
		}
	}

	return result, nil
}

// DeleteByName deletes a resource by name, kind, and namespace
func (cm *ClusterManager) DeleteByName(kind, name, namespace string, opts *DeleteOptions) (*DeleteResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if opts == nil {
		opts = NewDeleteOptions()
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
		return &DeleteResult{
			Name:      name,
			Namespace: namespace,
			Kind:      kind,
			Status:    DeleteStatusNotFound,
			Message:   fmt.Sprintf("resource not found: %v", err),
		}, nil
	}

	// Handle dry-run
	if opts.DryRun != DryRunNone {
		return &DeleteResult{
			Name:      name,
			Namespace: namespace,
			Kind:      kind,
			Status:    DeleteStatusDeleted,
			Message:   "resource would be deleted (dry run)",
			DryRun:    true,
		}, nil
	}

	// Prepare delete options
	deleteOpts := metav1.DeleteOptions{}

	if opts.GracePeriodSeconds != nil {
		deleteOpts.GracePeriodSeconds = opts.GracePeriodSeconds
	}

	if opts.PropagationPolicy != "" {
		policy := metav1.DeletionPropagation(opts.PropagationPolicy)
		deleteOpts.PropagationPolicy = &policy
	}

	// Delete the resource
	startTime := time.Now()
	err = resourceInterface.Delete(ctx, name, deleteOpts)
	duration := time.Since(startTime)

	if err != nil {
		return nil, fmt.Errorf("failed to delete %s/%s: %w", kind, name, err)
	}

	result := &DeleteResult{
		Name:      name,
		Namespace: namespace,
		Kind:      kind,
		Status:    DeleteStatusDeleted,
		Message:   "resource deleted successfully",
		Duration:  duration,
	}

	// Wait for deletion if requested
	if opts.Wait {
		waitErr := cm.waitForDeletion(ctx, resourceInterface, name, opts.WaitTimeout)
		if waitErr != nil {
			result.Message = fmt.Sprintf("resource deleted but wait failed: %v", waitErr)
		} else {
			result.Message = "resource deleted and confirmed"
		}
	}

	return result, nil
}

// DeleteResources deletes multiple resources in batch
func (cm *ClusterManager) DeleteResources(resources []*ParsedResource, opts *DeleteOptions) (*BatchResult, error) {
	if opts == nil {
		opts = NewDeleteOptions()
	}

	// Convert to batch options
	batchOpts := &BatchDeleteOptions{
		DeleteOptions:   opts,
		ContinueOnError: false,
		Parallel:        false,
	}

	return cm.DeleteResourcesBatch(resources, batchOpts)
}

// DeleteResourcesBatch deletes resources with batch options
func (cm *ClusterManager) DeleteResourcesBatch(resources []*ParsedResource, opts *BatchDeleteOptions) (*BatchResult, error) {
	if opts == nil {
		opts = NewBatchDeleteOptions()
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

	// Delete resources sequentially
	for _, resource := range resources {
		deleteResult, err := cm.DeleteResource(resource.Object, opts.DeleteOptions)

		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, err)

			if !opts.ContinueOnError {
				break
			}
			continue
		}

		if deleteResult.Status == DeleteStatusNotFound {
			result.Skipped++
		} else {
			result.Successful++
		}
		result.Results = append(result.Results, deleteResult)
	}

	result.Duration = time.Since(startTime)
	return result, nil
}

// DeleteFile deletes resources from a file
func (cm *ClusterManager) DeleteFile(filePath string, opts *DeleteOptions) (*BatchResult, error) {
	parser := NewResourceParser()

	// Parse file
	resources, err := parser.ParseFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to parse file %s: %w", filePath, err)
	}

	return cm.DeleteResources(resources, opts)
}

// DeleteDirectory deletes resources from a directory
func (cm *ClusterManager) DeleteDirectory(dirPath string, recursive bool, opts *DeleteOptions) (*BatchResult, error) {
	parser := NewResourceParser()

	// Parse directory
	resources, err := parser.ParseDirectory(dirPath, recursive)
	if err != nil {
		return nil, fmt.Errorf("failed to parse directory %s: %w", dirPath, err)
	}

	return cm.DeleteResources(resources, opts)
}

// DeleteString deletes resources from a YAML/JSON string
func (cm *ClusterManager) DeleteString(content string, opts *DeleteOptions) (*BatchResult, error) {
	parser := NewResourceParser()

	// Parse string
	resources, err := parser.ParseString(content)
	if err != nil {
		return nil, fmt.Errorf("failed to parse content: %w", err)
	}

	return cm.DeleteResources(resources, opts)
}

// DeleteBySelector deletes resources matching a selector
func (cm *ClusterManager) DeleteBySelector(selector *ResourceSelector, opts *DeleteOptions) (*BatchResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if selector == nil {
		return nil, fmt.Errorf("selector is nil")
	}

	if opts == nil {
		opts = NewDeleteOptions()
	}

	startTime := time.Now()
	result := &BatchResult{
		Total:      0,
		Successful: 0,
		Failed:     0,
		Skipped:    0,
		Results:    make([]interface{}, 0),
		Errors:     make([]error, 0),
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// Process each kind in selector
	for _, kind := range selector.Kinds {
		// Create minimal object for GVR lookup
		obj := &unstructured.Unstructured{}
		obj.SetKind(kind)

		gvr, err := cm.getGVR(obj)
		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, fmt.Errorf("failed to get GVR for kind %s: %w", kind, err))
			continue
		}

		resourceInterface := cm.getDynamicResourceInterface(gvr, selector.Namespace)

		// List resources
		listOpts := metav1.ListOptions{}
		if len(selector.Labels) > 0 {
			listOpts.LabelSelector = formatLabelSelector(selector.Labels)
		}
		if selector.FieldSelector != "" {
			listOpts.FieldSelector = selector.FieldSelector
		}

		list, err := resourceInterface.List(ctx, listOpts)
		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, fmt.Errorf("failed to list %s: %w", kind, err))
			continue
		}

		result.Total += len(list.Items)

		// Delete each resource
		for _, item := range list.Items {
			// Check if name matches (if Names filter specified)
			if len(selector.Names) > 0 && !contains(selector.Names, item.GetName()) {
				result.Skipped++
				continue
			}

			deleteResult, err := cm.DeleteResource(&item, opts)
			if err != nil {
				result.Failed++
				result.Errors = append(result.Errors, err)
				continue
			}

			if deleteResult.Status == DeleteStatusNotFound {
				result.Skipped++
			} else {
				result.Successful++
			}
			result.Results = append(result.Results, deleteResult)
		}
	}

	result.Duration = time.Since(startTime)
	return result, nil
}

// ========================================================================
// HELPER METHODS
// ========================================================================

// waitForDeletion waits for a resource to be fully deleted
func (cm *ClusterManager) waitForDeletion(ctx context.Context, resourceInterface interface{}, name string, timeout time.Duration) error {
	// Create wait context with timeout
	waitCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-waitCtx.Done():
			return fmt.Errorf("timeout waiting for resource deletion")
		case <-ticker.C:
			// Try to get the resource
			_, err := resourceInterface.(interface {
				Get(ctx context.Context, name string, opts metav1.GetOptions) (*unstructured.Unstructured, error)
			}).Get(waitCtx, name, metav1.GetOptions{})

			if err != nil {
				// Resource not found = successfully deleted
				return nil
			}
		}
	}
}

// formatLabelSelector formats a label map into a selector string
func formatLabelSelector(labels map[string]string) string {
	if len(labels) == 0 {
		return ""
	}

	selector := ""
	first := true
	for key, value := range labels {
		if !first {
			selector += ","
		}
		selector += fmt.Sprintf("%s=%s", key, value)
		first = false
	}
	return selector
}

// contains checks if a slice contains a string
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// getGVRForKind returns the GVR for a given kind string
func (cm *ClusterManager) getGVRForKind(kind string) (schema.GroupVersionResource, error) {
	// Create minimal object for GVR lookup
	obj := &unstructured.Unstructured{}
	obj.SetKind(kind)
	obj.SetAPIVersion("v1") // Default API version

	return cm.getGVR(obj)
}
