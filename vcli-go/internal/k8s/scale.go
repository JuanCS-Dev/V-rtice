package k8s

import (
	"context"
	"fmt"
	"time"

	autoscalingv1 "k8s.io/api/autoscaling/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime/schema"
)

// ScaleResource scales a Kubernetes resource (Deployment, StatefulSet, ReplicaSet)
func (cm *ClusterManager) ScaleResource(kind, name, namespace string, opts *ScaleOptions) (*ScaleResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if opts == nil {
		opts = NewScaleOptions()
	}

	// Validate that the kind supports scaling
	_, err := cm.getScalableGVR(kind)
	if err != nil {
		return nil, fmt.Errorf("resource kind %s does not support scaling: %w", kind, err)
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// Get current scale
	currentScale, err := cm.getScaleSubresource(ctx, kind, name, namespace)
	if err != nil {
		return nil, fmt.Errorf("failed to get current scale: %w", err)
	}

	originalReplicas := currentScale.Spec.Replicas

	// Handle dry-run
	if opts.DryRun != DryRunNone {
		return &ScaleResult{
			Kind:             kind,
			Name:             name,
			Namespace:        namespace,
			PreviousReplicas: originalReplicas,
			DesiredReplicas:  opts.Replicas,
			CurrentReplicas:  originalReplicas,
			Status:           ScaleStatusScaled,
			Message:          "resource would be scaled (dry run)",
			DryRun:           true,
		}, nil
	}

	// Update scale
	startTime := time.Now()
	currentScale.Spec.Replicas = opts.Replicas

	updatedScale, err := cm.updateScaleSubresource(ctx, kind, name, namespace, currentScale)
	if err != nil {
		return nil, fmt.Errorf("failed to scale %s/%s: %w", kind, name, err)
	}

	duration := time.Since(startTime)

	result := &ScaleResult{
		Kind:             kind,
		Name:             name,
		Namespace:        namespace,
		PreviousReplicas: originalReplicas,
		DesiredReplicas:  opts.Replicas,
		CurrentReplicas:  updatedScale.Status.Replicas,
		Status:           ScaleStatusScaling,
		Message:          fmt.Sprintf("scaling from %d to %d replicas", originalReplicas, opts.Replicas),
		Duration:         duration,
	}

	// Wait for scale completion if requested
	if opts.Wait {
		waitErr := cm.waitForScale(ctx, kind, name, namespace, opts.Replicas, opts.WaitTimeout)
		if waitErr != nil {
			result.Message = fmt.Sprintf("scale initiated but wait failed: %v", waitErr)
			result.Status = ScaleStatusFailed
		} else {
			result.Status = ScaleStatusScaled
			result.Message = fmt.Sprintf("successfully scaled from %d to %d replicas", originalReplicas, opts.Replicas)
			// Get final replica count
			finalScale, err := cm.getScaleSubresource(ctx, kind, name, namespace)
			if err == nil {
				result.CurrentReplicas = finalScale.Status.Replicas
			}
		}
	}

	return result, nil
}

// GetScale returns the current scale information for a resource
func (cm *ClusterManager) GetScale(kind, name, namespace string) (*ScaleInfo, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	// Validate that the kind supports scaling
	_, err := cm.getScalableGVR(kind)
	if err != nil {
		return nil, fmt.Errorf("resource kind %s does not support scaling: %w", kind, err)
	}

	ctx := context.Background()

	scale, err := cm.getScaleSubresource(ctx, kind, name, namespace)
	if err != nil {
		return nil, fmt.Errorf("failed to get scale: %w", err)
	}

	return &ScaleInfo{
		Kind:            kind,
		Name:            name,
		Namespace:       namespace,
		DesiredReplicas: scale.Spec.Replicas,
		CurrentReplicas: scale.Status.Replicas,
		Selector:        scale.Status.Selector,
	}, nil
}

// ScaleBatch scales multiple resources
func (cm *ClusterManager) ScaleBatch(targets []ScaleTarget, opts *ScaleOptions) (*BatchResult, error) {
	if opts == nil {
		opts = NewScaleOptions()
	}

	startTime := time.Now()
	result := &BatchResult{
		Total:      len(targets),
		Successful: 0,
		Failed:     0,
		Skipped:    0,
		Results:    make([]interface{}, 0),
		Errors:     make([]error, 0),
	}

	// Scale resources sequentially
	for _, target := range targets {
		scaleOpts := &ScaleOptions{
			Replicas:    target.Replicas,
			Wait:        opts.Wait,
			WaitTimeout: opts.WaitTimeout,
			Timeout:     opts.Timeout,
			DryRun:      opts.DryRun,
		}

		scaleResult, err := cm.ScaleResource(target.Kind, target.Name, target.Namespace, scaleOpts)

		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, err)
			continue
		}

		result.Successful++
		result.Results = append(result.Results, scaleResult)
	}

	result.Duration = time.Since(startTime)
	return result, nil
}

// ========================================================================
// HELPER METHODS
// ========================================================================

// getScalableGVR returns the GVR for a scalable resource
func (cm *ClusterManager) getScalableGVR(kind string) (schema.GroupVersionResource, error) {
	var gvr schema.GroupVersionResource

	switch kind {
	case "Deployment":
		gvr = schema.GroupVersionResource{
			Group:    "apps",
			Version:  "v1",
			Resource: "deployments",
		}
	case "StatefulSet":
		gvr = schema.GroupVersionResource{
			Group:    "apps",
			Version:  "v1",
			Resource: "statefulsets",
		}
	case "ReplicaSet":
		gvr = schema.GroupVersionResource{
			Group:    "apps",
			Version:  "v1",
			Resource: "replicasets",
		}
	case "ReplicationController":
		gvr = schema.GroupVersionResource{
			Group:    "",
			Version:  "v1",
			Resource: "replicationcontrollers",
		}
	default:
		return gvr, fmt.Errorf("kind %s does not support scaling operations", kind)
	}

	return gvr, nil
}

// getScaleSubresource gets the scale subresource for a resource
func (cm *ClusterManager) getScaleSubresource(ctx context.Context, kind, name, namespace string) (*autoscalingv1.Scale, error) {
	gvr, err := cm.getScalableGVR(kind)
	if err != nil {
		return nil, err
	}

	var scale *autoscalingv1.Scale

	switch kind {
	case "Deployment":
		scale, err = cm.clientset.AppsV1().Deployments(namespace).GetScale(ctx, name, metav1.GetOptions{})
	case "StatefulSet":
		scale, err = cm.clientset.AppsV1().StatefulSets(namespace).GetScale(ctx, name, metav1.GetOptions{})
	case "ReplicaSet":
		scale, err = cm.clientset.AppsV1().ReplicaSets(namespace).GetScale(ctx, name, metav1.GetOptions{})
	case "ReplicationController":
		scale, err = cm.clientset.CoreV1().ReplicationControllers(namespace).GetScale(ctx, name, metav1.GetOptions{})
	default:
		return nil, fmt.Errorf("unsupported scalable kind: %s", kind)
	}

	if err != nil {
		return nil, err
	}

	// Store GVR info for later use
	_ = gvr

	return scale, nil
}

// updateScaleSubresource updates the scale subresource for a resource
func (cm *ClusterManager) updateScaleSubresource(ctx context.Context, kind, name, namespace string, scale *autoscalingv1.Scale) (*autoscalingv1.Scale, error) {
	var updatedScale *autoscalingv1.Scale
	var err error

	switch kind {
	case "Deployment":
		updatedScale, err = cm.clientset.AppsV1().Deployments(namespace).UpdateScale(ctx, name, scale, metav1.UpdateOptions{})
	case "StatefulSet":
		updatedScale, err = cm.clientset.AppsV1().StatefulSets(namespace).UpdateScale(ctx, name, scale, metav1.UpdateOptions{})
	case "ReplicaSet":
		updatedScale, err = cm.clientset.AppsV1().ReplicaSets(namespace).UpdateScale(ctx, name, scale, metav1.UpdateOptions{})
	case "ReplicationController":
		updatedScale, err = cm.clientset.CoreV1().ReplicationControllers(namespace).UpdateScale(ctx, name, scale, metav1.UpdateOptions{})
	default:
		return nil, fmt.Errorf("unsupported scalable kind: %s", kind)
	}

	return updatedScale, err
}

// waitForScale waits for a resource to reach the desired replica count
func (cm *ClusterManager) waitForScale(ctx context.Context, kind, name, namespace string, desiredReplicas int32, timeout time.Duration) error {
	// Create wait context with timeout
	waitCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-waitCtx.Done():
			return fmt.Errorf("timeout waiting for scale to complete")
		case <-ticker.C:
			scale, err := cm.getScaleSubresource(waitCtx, kind, name, namespace)
			if err != nil {
				return fmt.Errorf("failed to get scale status: %w", err)
			}

			// Check if desired replicas matches current replicas
			if scale.Status.Replicas == desiredReplicas {
				// Additional check for readiness (for deployments)
				if kind == "Deployment" {
					deployment, err := cm.clientset.AppsV1().Deployments(namespace).Get(waitCtx, name, metav1.GetOptions{})
					if err == nil {
						// Check if all replicas are ready
						if deployment.Status.ReadyReplicas == desiredReplicas {
							return nil
						}
					}
				} else {
					// For other scalable resources, just check replica count
					return nil
				}
			}
		}
	}
}
