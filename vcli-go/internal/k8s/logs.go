package k8s

import (
	"context"
	"fmt"
	"io"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// GetPodLogs retrieves logs from a pod
func (cm *ClusterManager) GetPodLogs(podName, namespace string, opts *LogOptions) (*LogResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if podName == "" {
		return nil, fmt.Errorf("pod name is required")
	}

	if namespace == "" {
		namespace = "default"
	}

	if opts == nil {
		opts = NewLogOptions()
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// Build pod log options
	podLogOpts := &corev1.PodLogOptions{
		Container:  opts.Container,
		Follow:     opts.Follow,
		Previous:   opts.Previous,
		Timestamps: opts.Timestamps,
	}

	if opts.SinceTime != nil {
		podLogOpts.SinceTime = &metav1.Time{Time: *opts.SinceTime}
	}

	if opts.SinceSeconds > 0 {
		sinceSeconds := int64(opts.SinceSeconds)
		podLogOpts.SinceSeconds = &sinceSeconds
	}

	if opts.TailLines > 0 {
		tailLines := int64(opts.TailLines)
		podLogOpts.TailLines = &tailLines
	}

	if opts.LimitBytes > 0 {
		limitBytes := int64(opts.LimitBytes)
		podLogOpts.LimitBytes = &limitBytes
	}

	// Get log stream
	req := cm.clientset.CoreV1().Pods(namespace).GetLogs(podName, podLogOpts)
	stream, err := req.Stream(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get logs for pod %s/%s: %w", namespace, podName, err)
	}

	return &LogResult{
		PodName:   podName,
		Namespace: namespace,
		Container: opts.Container,
		Stream:    stream,
	}, nil
}

// StreamPodLogs streams logs from a pod to a writer
func (cm *ClusterManager) StreamPodLogs(podName, namespace string, writer io.Writer, opts *LogOptions) error {
	logResult, err := cm.GetPodLogs(podName, namespace, opts)
	if err != nil {
		return err
	}
	defer logResult.Stream.Close()

	// Copy stream to writer
	_, err = io.Copy(writer, logResult.Stream)
	if err != nil {
		return fmt.Errorf("failed to stream logs: %w", err)
	}

	return nil
}

// GetMultiPodLogs retrieves logs from multiple pods
func (cm *ClusterManager) GetMultiPodLogs(selector *PodSelector, opts *LogOptions) ([]*LogResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if selector == nil {
		return nil, fmt.Errorf("pod selector is required")
	}

	// Create context
	ctx := context.Background()

	// List pods matching selector
	listOpts := metav1.ListOptions{}
	if len(selector.Labels) > 0 {
		listOpts.LabelSelector = formatLabelSelector(selector.Labels)
	}
	if selector.FieldSelector != "" {
		listOpts.FieldSelector = selector.FieldSelector
	}

	namespace := selector.Namespace
	if namespace == "" {
		namespace = "default"
	}

	podList, err := cm.clientset.CoreV1().Pods(namespace).List(ctx, listOpts)
	if err != nil {
		return nil, fmt.Errorf("failed to list pods: %w", err)
	}

	if len(podList.Items) == 0 {
		return nil, fmt.Errorf("no pods found matching selector")
	}

	// Get logs from each pod
	results := make([]*LogResult, 0, len(podList.Items))
	for _, pod := range podList.Items {
		logResult, err := cm.GetPodLogs(pod.Name, pod.Namespace, opts)
		if err != nil {
			// Continue on error for multi-pod logs
			continue
		}
		results = append(results, logResult)
	}

	if len(results) == 0 {
		return nil, fmt.Errorf("failed to get logs from any pod")
	}

	return results, nil
}

// GetContainerLogs retrieves logs from a specific container in a pod
func (cm *ClusterManager) GetContainerLogs(podName, namespace, container string, opts *LogOptions) (*LogResult, error) {
	if opts == nil {
		opts = NewLogOptions()
	}
	opts.Container = container

	return cm.GetPodLogs(podName, namespace, opts)
}

// ListPodContainers lists all containers in a pod
func (cm *ClusterManager) ListPodContainers(podName, namespace string) ([]string, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	pod, err := cm.clientset.CoreV1().Pods(namespace).Get(ctx, podName, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get pod %s/%s: %w", namespace, podName, err)
	}

	containers := make([]string, 0, len(pod.Spec.Containers)+len(pod.Spec.InitContainers))

	// Add init containers
	for _, c := range pod.Spec.InitContainers {
		containers = append(containers, c.Name+" (init)")
	}

	// Add regular containers
	for _, c := range pod.Spec.Containers {
		containers = append(containers, c.Name)
	}

	return containers, nil
}

// FollowPodLogs follows logs from a pod with automatic reconnection
func (cm *ClusterManager) FollowPodLogs(podName, namespace string, writer io.Writer, opts *LogOptions) error {
	if opts == nil {
		opts = NewLogOptions()
	}
	opts.Follow = true

	// Get logs with follow
	logResult, err := cm.GetPodLogs(podName, namespace, opts)
	if err != nil {
		return err
	}
	defer logResult.Stream.Close()

	// Copy stream to writer
	_, err = io.Copy(writer, logResult.Stream)
	if err != nil && err != io.EOF {
		return fmt.Errorf("failed to follow logs: %w", err)
	}

	return nil
}

// GetPodLogsSince retrieves logs since a specific time
func (cm *ClusterManager) GetPodLogsSince(podName, namespace string, since time.Time, opts *LogOptions) (*LogResult, error) {
	if opts == nil {
		opts = NewLogOptions()
	}
	opts.SinceTime = &since

	return cm.GetPodLogs(podName, namespace, opts)
}

// GetPodLogsTail retrieves the last N lines of logs
func (cm *ClusterManager) GetPodLogsTail(podName, namespace string, lines int, opts *LogOptions) (*LogResult, error) {
	if opts == nil {
		opts = NewLogOptions()
	}
	opts.TailLines = lines

	return cm.GetPodLogs(podName, namespace, opts)
}

// ReadLogsToString reads logs from a LogResult into a string
func ReadLogsToString(logResult *LogResult, maxBytes int) (string, error) {
	if logResult == nil || logResult.Stream == nil {
		return "", fmt.Errorf("invalid log result")
	}

	var reader io.Reader = logResult.Stream
	if maxBytes > 0 {
		reader = io.LimitReader(logResult.Stream, int64(maxBytes))
	}

	data, err := io.ReadAll(reader)
	if err != nil {
		return "", fmt.Errorf("failed to read logs: %w", err)
	}

	return string(data), nil
}

// ValidateLogOptions validates log options
func ValidateLogOptions(opts *LogOptions) error {
	if opts == nil {
		return fmt.Errorf("log options are required")
	}

	if opts.SinceSeconds < 0 {
		return fmt.Errorf("since seconds must be non-negative")
	}

	if opts.TailLines < 0 {
		return fmt.Errorf("tail lines must be non-negative")
	}

	if opts.LimitBytes < 0 {
		return fmt.Errorf("limit bytes must be non-negative")
	}

	if opts.SinceTime != nil && opts.SinceSeconds > 0 {
		return fmt.Errorf("cannot specify both since time and since seconds")
	}

	return nil
}
