package k8s

import (
	"context"
	"fmt"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// GetNodeMetrics retrieves metrics for all nodes in the cluster
func (cm *ClusterManager) GetNodeMetrics() ([]NodeMetrics, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	ctx := context.Background()
	metricsList, err := cm.metricsClient.MetricsV1beta1().NodeMetricses().List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to list node metrics: %v", ErrOperationFailed, err)
	}

	metrics := make([]NodeMetrics, len(metricsList.Items))
	for i, k8sMetrics := range metricsList.Items {
		// Convert CPU and Memory
		cpuQuantity := k8sMetrics.Usage.Cpu()
		memQuantity := k8sMetrics.Usage.Memory()

		metrics[i] = NodeMetrics{
			Name:         k8sMetrics.Name,
			CPUUsage:     cpuQuantity.MilliValue(),
			MemoryUsage:  memQuantity.Value(),
			Timestamp:    k8sMetrics.Timestamp.Time,
			// Capacity is not provided by metrics API, would need to get from Node API
		}
	}

	return metrics, nil
}

// GetNodeMetricsByName retrieves metrics for a specific node
func (cm *ClusterManager) GetNodeMetricsByName(name string) (*NodeMetrics, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if name == "" {
		return nil, ErrResourceNameEmpty
	}

	ctx := context.Background()
	k8sMetrics, err := cm.metricsClient.MetricsV1beta1().NodeMetricses().Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get node metrics for %s: %v", ErrResourceNotFound, name, err)
	}

	// Convert CPU and Memory
	cpuQuantity := k8sMetrics.Usage.Cpu()
	memQuantity := k8sMetrics.Usage.Memory()

	metrics := NodeMetrics{
		Name:        k8sMetrics.Name,
		CPUUsage:    cpuQuantity.MilliValue(),
		MemoryUsage: memQuantity.Value(),
		Timestamp:   k8sMetrics.Timestamp.Time,
	}

	return &metrics, nil
}

// GetPodMetrics retrieves metrics for all pods in the specified namespace
// If namespace is empty string, retrieves metrics from all namespaces
func (cm *ClusterManager) GetPodMetrics(namespace string) ([]PodMetrics, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	// Empty string means all namespaces
	ctx := context.Background()
	metricsList, err := cm.metricsClient.MetricsV1beta1().PodMetricses(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to list pod metrics: %v", ErrOperationFailed, err)
	}

	metrics := make([]PodMetrics, len(metricsList.Items))
	for i, k8sMetrics := range metricsList.Items {
		// Convert container metrics
		containers := make([]ContainerMetrics, len(k8sMetrics.Containers))
		totalCPU := int64(0)
		totalMem := int64(0)

		for j, container := range k8sMetrics.Containers {
			cpuQuantity := container.Usage.Cpu()
			memQuantity := container.Usage.Memory()

			containers[j] = ContainerMetrics{
				Name:        container.Name,
				CPUUsage:    cpuQuantity.MilliValue(),
				MemoryUsage: memQuantity.Value(),
			}

			totalCPU += cpuQuantity.MilliValue()
			totalMem += memQuantity.Value()
		}

		metrics[i] = PodMetrics{
			Name:        k8sMetrics.Name,
			Namespace:   k8sMetrics.Namespace,
			CPUUsage:    totalCPU,
			MemoryUsage: totalMem,
			Containers:  containers,
			Timestamp:   k8sMetrics.Timestamp.Time,
		}
	}

	return metrics, nil
}

// GetPodMetricsByName retrieves metrics for a specific pod
func (cm *ClusterManager) GetPodMetricsByName(namespace, name string) (*PodMetrics, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	if name == "" {
		return nil, ErrResourceNameEmpty
	}

	ctx := context.Background()
	k8sMetrics, err := cm.metricsClient.MetricsV1beta1().PodMetricses(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get pod metrics for %s: %v", ErrResourceNotFound, name, err)
	}

	// Convert container metrics
	containers := make([]ContainerMetrics, len(k8sMetrics.Containers))
	totalCPU := int64(0)
	totalMem := int64(0)

	for i, container := range k8sMetrics.Containers {
		cpuQuantity := container.Usage.Cpu()
		memQuantity := container.Usage.Memory()

		containers[i] = ContainerMetrics{
			Name:        container.Name,
			CPUUsage:    cpuQuantity.MilliValue(),
			MemoryUsage: memQuantity.Value(),
		}

		totalCPU += cpuQuantity.MilliValue()
		totalMem += memQuantity.Value()
	}

	metrics := PodMetrics{
		Name:        k8sMetrics.Name,
		Namespace:   k8sMetrics.Namespace,
		CPUUsage:    totalCPU,
		MemoryUsage: totalMem,
		Containers:  containers,
		Timestamp:   k8sMetrics.Timestamp.Time,
	}

	return &metrics, nil
}
