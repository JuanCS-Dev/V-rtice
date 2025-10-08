package k8s

import (
	"context"
	"fmt"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/watch"
)

// WatchResources watches resources for changes
func (cm *ClusterManager) WatchResources(kind, namespace string, opts *WatchOptions) (watch.Interface, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if kind == "" {
		return nil, fmt.Errorf("resource kind is required")
	}

	if opts == nil {
		opts = NewWatchOptions()
	}

	// Get GVR for the resource
	obj := &unstructured.Unstructured{}
	obj.SetKind(kind)
	gvr, err := cm.getGVR(obj)
	if err != nil {
		return nil, fmt.Errorf("failed to get GVR for kind %s: %w", kind, err)
	}

	// Get resource interface
	resourceInterface := cm.getDynamicResourceInterface(gvr, namespace)

	// Prepare list options
	listOpts := metav1.ListOptions{
		Watch:           true,
		ResourceVersion: opts.ResourceVersion,
	}

	if len(opts.Labels) > 0 {
		listOpts.LabelSelector = formatLabelSelector(opts.Labels)
	}

	if opts.FieldSelector != "" {
		listOpts.FieldSelector = opts.FieldSelector
	}

	if opts.TimeoutSeconds > 0 {
		timeout := int64(opts.TimeoutSeconds)
		listOpts.TimeoutSeconds = &timeout
	}

	// Start watching
	watcher, err := resourceInterface.Watch(context.Background(), listOpts)
	if err != nil {
		return nil, fmt.Errorf("failed to start watching %s: %w", kind, err)
	}

	return watcher, nil
}

// WatchPods watches pods for changes
func (cm *ClusterManager) WatchPods(namespace string, opts *WatchOptions) (watch.Interface, error) {
	return cm.WatchResources("Pod", namespace, opts)
}

// WatchDeployments watches deployments for changes
func (cm *ClusterManager) WatchDeployments(namespace string, opts *WatchOptions) (watch.Interface, error) {
	return cm.WatchResources("Deployment", namespace, opts)
}

// WatchServices watches services for changes
func (cm *ClusterManager) WatchServices(namespace string, opts *WatchOptions) (watch.Interface, error) {
	return cm.WatchResources("Service", namespace, opts)
}

// WatchNodes watches nodes for changes
func (cm *ClusterManager) WatchNodes(opts *WatchOptions) (watch.Interface, error) {
	return cm.WatchResources("Node", "", opts)
}

// WatchWithHandler watches resources and calls handler for each event
func (cm *ClusterManager) WatchWithHandler(kind, namespace string, handler WatchEventHandler, opts *WatchOptions) error {
	watcher, err := cm.WatchResources(kind, namespace, opts)
	if err != nil {
		return err
	}
	defer watcher.Stop()

	// Create context with timeout if specified
	var ctx context.Context
	var cancel context.CancelFunc

	if opts != nil && opts.Timeout > 0 {
		ctx, cancel = context.WithTimeout(context.Background(), opts.Timeout)
		defer cancel()
	} else {
		ctx = context.Background()
	}

	// Process events
	for {
		select {
		case event, ok := <-watcher.ResultChan():
			if !ok {
				return fmt.Errorf("watch channel closed")
			}

			// Convert to unstructured
			obj, ok := event.Object.(*unstructured.Unstructured)
			if !ok {
				continue
			}

			// Call handler
			watchEvent := &WatchEvent{
				Type:   WatchEventType(event.Type),
				Object: obj,
			}

			if err := handler(watchEvent); err != nil {
				return fmt.Errorf("watch handler error: %w", err)
			}

			// Check if handler wants to stop
			if watchEvent.Stop {
				return nil
			}

		case <-ctx.Done():
			return ctx.Err()
		}
	}
}

// WatchUntilCondition watches resources until a condition is met
func (cm *ClusterManager) WatchUntilCondition(kind, namespace string, condition WatchCondition, opts *WatchOptions) (*unstructured.Unstructured, error) {
	watcher, err := cm.WatchResources(kind, namespace, opts)
	if err != nil {
		return nil, err
	}
	defer watcher.Stop()

	// Create context with timeout
	var ctx context.Context
	var cancel context.CancelFunc

	if opts != nil && opts.Timeout > 0 {
		ctx, cancel = context.WithTimeout(context.Background(), opts.Timeout)
		defer cancel()
	} else {
		ctx, cancel = context.WithTimeout(context.Background(), 5*time.Minute)
		defer cancel()
	}

	// Process events until condition is met
	for {
		select {
		case event, ok := <-watcher.ResultChan():
			if !ok {
				return nil, fmt.Errorf("watch channel closed")
			}

			// Convert to unstructured
			obj, ok := event.Object.(*unstructured.Unstructured)
			if !ok {
				continue
			}

			// Check condition
			met, err := condition(&WatchEvent{
				Type:   WatchEventType(event.Type),
				Object: obj,
			})
			if err != nil {
				return nil, fmt.Errorf("condition check error: %w", err)
			}

			if met {
				return obj, nil
			}

		case <-ctx.Done():
			return nil, fmt.Errorf("timeout waiting for condition")
		}
	}
}

// WatchMultipleResources watches multiple resource types simultaneously
func (cm *ClusterManager) WatchMultipleResources(kinds []string, namespace string, handler WatchEventHandler, opts *WatchOptions) error {
	if len(kinds) == 0 {
		return fmt.Errorf("at least one resource kind is required")
	}

	// Create error channel
	errChan := make(chan error, len(kinds))

	// Start watching each kind
	for _, kind := range kinds {
		go func(k string) {
			err := cm.WatchWithHandler(k, namespace, handler, opts)
			if err != nil {
				errChan <- fmt.Errorf("watch error for %s: %w", k, err)
			}
		}(kind)
	}

	// Wait for first error
	return <-errChan
}

// FormatWatchEvent formats a watch event for display
func FormatWatchEvent(event *WatchEvent) string {
	if event == nil || event.Object == nil {
		return "<invalid event>"
	}

	obj, ok := event.Object.(*unstructured.Unstructured)
	if !ok {
		return "<invalid object>"
	}

	return fmt.Sprintf("[%s] %s/%s/%s",
		event.Type,
		obj.GetKind(),
		obj.GetNamespace(),
		obj.GetName())
}

// ValidateWatchOptions validates watch options
func ValidateWatchOptions(opts *WatchOptions) error {
	if opts == nil {
		return fmt.Errorf("watch options are required")
	}

	if opts.TimeoutSeconds < 0 {
		return fmt.Errorf("timeout seconds must be non-negative")
	}

	return nil
}
