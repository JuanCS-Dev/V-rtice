package k8s

import (
	"context"
	"fmt"
	"strings"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/watch"
)

// WaitForResource waits for a resource to reach a specific condition
func (cm *ClusterManager) WaitForResource(kind, name, namespace string, condition WaitCondition, timeout time.Duration) (*WaitResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	startTime := time.Now()

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// Get GVR
	gvr, err := cm.getGVRForKind(kind)
	if err != nil {
		return &WaitResult{
			Success:   false,
			Condition: condition,
			Message:   fmt.Sprintf("failed to resolve resource type: %v", err),
			Duration:  time.Since(startTime),
			TimedOut:  false,
		}, err
	}

	// Handle different conditions
	switch condition {
	case WaitConditionDeleted:
		return cm.waitForResourceDeletion(ctx, gvr, name, namespace, condition, startTime)
	case WaitConditionExists:
		return cm.waitForExistence(ctx, gvr, name, namespace, condition, startTime)
	case WaitConditionReady:
		return cm.waitForReadyCondition(ctx, gvr, name, namespace, "Ready", condition, startTime)
	case WaitConditionAvailable:
		return cm.waitForReadyCondition(ctx, gvr, name, namespace, "Available", condition, startTime)
	default:
		return &WaitResult{
			Success:   false,
			Condition: condition,
			Message:   fmt.Sprintf("unsupported condition: %s", condition),
			Duration:  time.Since(startTime),
			TimedOut:  false,
		}, fmt.Errorf("unsupported condition")
	}
}

// WaitForConditionWithSelector waits for multiple resources to reach a specific condition
func (cm *ClusterManager) WaitForConditionWithSelector(kind, namespace string, selector string, condition WaitCondition, timeout time.Duration) (*WaitResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	startTime := time.Now()

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// Get GVR
	gvr, err := cm.getGVRForKind(kind)
	if err != nil {
		return &WaitResult{
			Success:   false,
			Condition: condition,
			Message:   fmt.Sprintf("failed to resolve resource type: %v", err),
			Duration:  time.Since(startTime),
			TimedOut:  false,
		}, err
	}

	// List resources
	listOpts := metav1.ListOptions{}
	if selector != "" {
		listOpts.LabelSelector = selector
	}

	var list *unstructured.UnstructuredList
	if namespace != "" {
		list, err = cm.dynamicClient.Resource(gvr).Namespace(namespace).List(ctx, listOpts)
	} else {
		list, err = cm.dynamicClient.Resource(gvr).List(ctx, listOpts)
	}

	if err != nil {
		return &WaitResult{
			Success:   false,
			Condition: condition,
			Message:   fmt.Sprintf("failed to list resources: %v", err),
			Duration:  time.Since(startTime),
			TimedOut:  false,
		}, err
	}

	if len(list.Items) == 0 {
		return &WaitResult{
			Success:   false,
			Condition: condition,
			Message:   "no resources found matching selector",
			Duration:  time.Since(startTime),
			TimedOut:  false,
		}, fmt.Errorf("no resources found")
	}

	// Wait for all resources to meet condition
	for _, item := range list.Items {
		result, err := cm.WaitForResource(kind, item.GetName(), item.GetNamespace(), condition, timeout)
		if err != nil || !result.Success {
			return result, err
		}
	}

	return &WaitResult{
		Success:   true,
		Condition: condition,
		Message:   fmt.Sprintf("all resources met condition: %s", condition),
		Duration:  time.Since(startTime),
		TimedOut:  false,
	}, nil
}

// waitForExistence waits for a resource to exist
func (cm *ClusterManager) waitForExistence(ctx context.Context, gvr schema.GroupVersionResource, name, namespace string, condition WaitCondition, startTime time.Time) (*WaitResult, error) {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return &WaitResult{
				Success:   false,
				Condition: condition,
				Message:   fmt.Sprintf("timeout waiting for %s/%s to exist", namespace, name),
				Duration:  time.Since(startTime),
				TimedOut:  true,
			}, fmt.Errorf("timeout")

		case <-ticker.C:
			var err error
			if namespace != "" {
				_, err = cm.dynamicClient.Resource(gvr).Namespace(namespace).Get(ctx, name, metav1.GetOptions{})
			} else {
				_, err = cm.dynamicClient.Resource(gvr).Get(ctx, name, metav1.GetOptions{})
			}

			if err == nil {
				return &WaitResult{
					Success:   true,
					Condition: condition,
					Message:   fmt.Sprintf("%s/%s exists", namespace, name),
					Duration:  time.Since(startTime),
					TimedOut:  false,
				}, nil
			}
		}
	}
}

// waitForResourceDeletion waits for a resource to be deleted
func (cm *ClusterManager) waitForResourceDeletion(ctx context.Context, gvr schema.GroupVersionResource, name, namespace string, condition WaitCondition, startTime time.Time) (*WaitResult, error) {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return &WaitResult{
				Success:   false,
				Condition: condition,
				Message:   fmt.Sprintf("timeout waiting for %s/%s to be deleted", namespace, name),
				Duration:  time.Since(startTime),
				TimedOut:  true,
			}, fmt.Errorf("timeout")

		case <-ticker.C:
			var err error
			if namespace != "" {
				_, err = cm.dynamicClient.Resource(gvr).Namespace(namespace).Get(ctx, name, metav1.GetOptions{})
			} else {
				_, err = cm.dynamicClient.Resource(gvr).Get(ctx, name, metav1.GetOptions{})
			}

			// Resource not found means it's been deleted
			if err != nil && strings.Contains(err.Error(), "not found") {
				return &WaitResult{
					Success:   true,
					Condition: condition,
					Message:   fmt.Sprintf("%s/%s deleted", namespace, name),
					Duration:  time.Since(startTime),
					TimedOut:  false,
				}, nil
			}
		}
	}
}

// waitForReadyCondition waits for a resource to meet a ready/available condition
func (cm *ClusterManager) waitForReadyCondition(ctx context.Context, gvr schema.GroupVersionResource, name, namespace string, conditionType string, condition WaitCondition, startTime time.Time) (*WaitResult, error) {
	// Use watch API for efficient condition checking
	watchOpts := metav1.ListOptions{
		FieldSelector:   fmt.Sprintf("metadata.name=%s", name),
		Watch:           true,
		ResourceVersion: "",
	}

	var watcher watch.Interface
	var err error

	if namespace != "" {
		watcher, err = cm.dynamicClient.Resource(gvr).Namespace(namespace).Watch(ctx, watchOpts)
	} else {
		watcher, err = cm.dynamicClient.Resource(gvr).Watch(ctx, watchOpts)
	}

	if err != nil {
		// Fallback to polling if watch not supported
		return cm.waitForReadyConditionPolling(ctx, gvr, name, namespace, conditionType, condition, startTime)
	}
	defer watcher.Stop()

	// Check initial state
	var obj *unstructured.Unstructured
	if namespace != "" {
		obj, err = cm.dynamicClient.Resource(gvr).Namespace(namespace).Get(ctx, name, metav1.GetOptions{})
	} else {
		obj, err = cm.dynamicClient.Resource(gvr).Get(ctx, name, metav1.GetOptions{})
	}

	if err == nil {
		if checkReadyCondition(obj, conditionType) {
			return &WaitResult{
				Success:   true,
				Condition: condition,
				Message:   fmt.Sprintf("%s/%s is %s", namespace, name, conditionType),
				Duration:  time.Since(startTime),
				TimedOut:  false,
			}, nil
		}
	}

	// Watch for changes
	for {
		select {
		case <-ctx.Done():
			return &WaitResult{
				Success:   false,
				Condition: condition,
				Message:   fmt.Sprintf("timeout waiting for %s/%s to be %s", namespace, name, conditionType),
				Duration:  time.Since(startTime),
				TimedOut:  true,
			}, fmt.Errorf("timeout")

		case event, ok := <-watcher.ResultChan():
			if !ok {
				// Channel closed, retry with polling
				return cm.waitForReadyConditionPolling(ctx, gvr, name, namespace, conditionType, condition, startTime)
			}

			if event.Type == watch.Error {
				continue
			}

			obj, ok := event.Object.(*unstructured.Unstructured)
			if !ok {
				continue
			}

			if checkReadyCondition(obj, conditionType) {
				return &WaitResult{
					Success:   true,
					Condition: condition,
					Message:   fmt.Sprintf("%s/%s is %s", namespace, name, conditionType),
					Duration:  time.Since(startTime),
					TimedOut:  false,
				}, nil
			}
		}
	}
}

// waitForReadyConditionPolling polls for a condition (fallback when watch is not available)
func (cm *ClusterManager) waitForReadyConditionPolling(ctx context.Context, gvr schema.GroupVersionResource, name, namespace string, conditionType string, condition WaitCondition, startTime time.Time) (*WaitResult, error) {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return &WaitResult{
				Success:   false,
				Condition: condition,
				Message:   fmt.Sprintf("timeout waiting for %s/%s to be %s", namespace, name, conditionType),
				Duration:  time.Since(startTime),
				TimedOut:  true,
			}, fmt.Errorf("timeout")

		case <-ticker.C:
			var obj *unstructured.Unstructured
			var err error

			if namespace != "" {
				obj, err = cm.dynamicClient.Resource(gvr).Namespace(namespace).Get(ctx, name, metav1.GetOptions{})
			} else {
				obj, err = cm.dynamicClient.Resource(gvr).Get(ctx, name, metav1.GetOptions{})
			}

			if err != nil {
				continue
			}

			if checkReadyCondition(obj, conditionType) {
				return &WaitResult{
					Success:   true,
					Condition: condition,
					Message:   fmt.Sprintf("%s/%s is %s", namespace, name, conditionType),
					Duration:  time.Since(startTime),
					TimedOut:  false,
				}, nil
			}
		}
	}
}

// checkReadyCondition checks if a resource meets a ready condition
func checkReadyCondition(obj *unstructured.Unstructured, conditionType string) bool {
	// Check Kubernetes status conditions
	conditions, found, err := unstructured.NestedSlice(obj.Object, "status", "conditions")
	if err != nil || !found {
		return false
	}

	for _, c := range conditions {
		condMap, ok := c.(map[string]interface{})
		if !ok {
			continue
		}

		cType, found := condMap["type"]
		if !found {
			continue
		}

		cStatus, found := condMap["status"]
		if !found {
			continue
		}

		if fmt.Sprintf("%v", cType) == conditionType && fmt.Sprintf("%v", cStatus) == "True" {
			return true
		}
	}
	return false
}

// WaitForPodReady waits for a pod to be ready
func (cm *ClusterManager) WaitForPodReady(podName, namespace string, timeout time.Duration) (*WaitResult, error) {
	return cm.WaitForResource("pod", podName, namespace, WaitConditionReady, timeout)
}

// WaitForDeploymentReady waits for a deployment to be ready
func (cm *ClusterManager) WaitForDeploymentReady(deploymentName, namespace string, timeout time.Duration) (*WaitResult, error) {
	return cm.WaitForResource("deployment", deploymentName, namespace, WaitConditionAvailable, timeout)
}

// WaitForResourceDeletion waits for a resource to be deleted
func (cm *ClusterManager) WaitForResourceDeletion(kind, name, namespace string, timeout time.Duration) (*WaitResult, error) {
	return cm.WaitForResource(kind, name, namespace, WaitConditionDeleted, timeout)
}
