package k8s

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// CreateConfigMap creates a ConfigMap
func (cm *ClusterManager) CreateConfigMap(name, namespace string, opts *ConfigMapOptions) (*corev1.ConfigMap, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if name == "" {
		return nil, fmt.Errorf("configmap name is required")
	}

	if namespace == "" {
		namespace = "default"
	}

	if opts == nil {
		opts = NewConfigMapOptions()
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// Build ConfigMap object
	configMap := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels:    opts.Labels,
		},
		Data:       opts.Data,
		BinaryData: opts.BinaryData,
	}

	// Create ConfigMap
	result, err := cm.clientset.CoreV1().ConfigMaps(namespace).Create(ctx, configMap, metav1.CreateOptions{
		DryRun:       convertDryRunToDryRunArray(opts.DryRun),
		FieldManager: "vcli",
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create configmap %s: %w", name, err)
	}

	return result, nil
}

// GetConfigMap retrieves a ConfigMap
func (cm *ClusterManager) GetConfigMap(name, namespace string) (*corev1.ConfigMap, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	configMap, err := cm.clientset.CoreV1().ConfigMaps(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get configmap %s: %w", name, err)
	}

	return configMap, nil
}

// UpdateConfigMap updates a ConfigMap
func (cm *ClusterManager) UpdateConfigMap(name, namespace string, opts *ConfigMapOptions) (*corev1.ConfigMap, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	if opts == nil {
		return nil, fmt.Errorf("options are required for update")
	}

	ctx := context.Background()

	// Get existing ConfigMap
	existing, err := cm.clientset.CoreV1().ConfigMaps(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get existing configmap: %w", err)
	}

	// Update fields
	if opts.Data != nil {
		existing.Data = opts.Data
	}
	if opts.BinaryData != nil {
		existing.BinaryData = opts.BinaryData
	}
	if opts.Labels != nil {
		existing.Labels = opts.Labels
	}

	// Update ConfigMap
	result, err := cm.clientset.CoreV1().ConfigMaps(namespace).Update(ctx, existing, metav1.UpdateOptions{
		DryRun:       convertDryRunToDryRunArray(opts.DryRun),
		FieldManager: "vcli",
	})
	if err != nil {
		return nil, fmt.Errorf("failed to update configmap %s: %w", name, err)
	}

	return result, nil
}

// DeleteConfigMap deletes a ConfigMap
func (cm *ClusterManager) DeleteConfigMap(name, namespace string) error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	err := cm.clientset.CoreV1().ConfigMaps(namespace).Delete(ctx, name, metav1.DeleteOptions{})
	if err != nil {
		return fmt.Errorf("failed to delete configmap %s: %w", name, err)
	}

	return nil
}

// ListConfigMaps lists ConfigMaps
func (cm *ClusterManager) ListConfigMaps(namespace string, opts *ConfigMapListOptions) (*corev1.ConfigMapList, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	listOpts := metav1.ListOptions{}
	if opts != nil {
		if len(opts.Labels) > 0 {
			listOpts.LabelSelector = formatLabelSelector(opts.Labels)
		}
		if opts.FieldSelector != "" {
			listOpts.FieldSelector = opts.FieldSelector
		}
	}

	configMaps, err := cm.clientset.CoreV1().ConfigMaps(namespace).List(ctx, listOpts)
	if err != nil {
		return nil, fmt.Errorf("failed to list configmaps: %w", err)
	}

	return configMaps, nil
}

// CreateConfigMapFromFiles creates a ConfigMap from files
func (cm *ClusterManager) CreateConfigMapFromFiles(name, namespace string, files []string, opts *ConfigMapOptions) (*corev1.ConfigMap, error) {
	if opts == nil {
		opts = NewConfigMapOptions()
	}

	// Initialize data map if nil
	if opts.Data == nil {
		opts.Data = make(map[string]string)
	}

	// Read files
	for _, file := range files {
		data, err := os.ReadFile(file)
		if err != nil {
			return nil, fmt.Errorf("failed to read file %s: %w", file, err)
		}

		// Use basename as key
		key := filepath.Base(file)
		opts.Data[key] = string(data)
	}

	return cm.CreateConfigMap(name, namespace, opts)
}

// CreateConfigMapFromLiterals creates a ConfigMap from literal values
func (cm *ClusterManager) CreateConfigMapFromLiterals(name, namespace string, literals map[string]string, opts *ConfigMapOptions) (*corev1.ConfigMap, error) {
	if opts == nil {
		opts = NewConfigMapOptions()
	}

	opts.Data = literals

	return cm.CreateConfigMap(name, namespace, opts)
}

// CreateConfigMapFromEnvFile creates a ConfigMap from an env file
func (cm *ClusterManager) CreateConfigMapFromEnvFile(name, namespace string, envFile string, opts *ConfigMapOptions) (*corev1.ConfigMap, error) {
	if opts == nil {
		opts = NewConfigMapOptions()
	}

	// Read env file
	content, err := os.ReadFile(envFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read env file: %w", err)
	}

	// Parse env file
	data := make(map[string]string)
	lines := strings.Split(string(content), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)
		if len(parts) == 2 {
			key := strings.TrimSpace(parts[0])
			value := strings.TrimSpace(parts[1])
			data[key] = value
		}
	}

	opts.Data = data

	return cm.CreateConfigMap(name, namespace, opts)
}

// ValidateConfigMapOptions validates ConfigMap options
func ValidateConfigMapOptions(opts *ConfigMapOptions) error {
	if opts == nil {
		return fmt.Errorf("configmap options are required")
	}

	if opts.Data == nil && opts.BinaryData == nil {
		return fmt.Errorf("at least one of data or binary data must be provided")
	}

	return nil
}

// convertDryRunToDryRunArray converts DryRunStrategy to string array
func convertDryRunToDryRunArray(dryRun DryRunStrategy) []string {
	if dryRun == DryRunNone {
		return nil
	}
	return []string{string(dryRun)}
}
