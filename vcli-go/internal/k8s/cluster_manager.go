package k8s

import (
	"fmt"
	"sync"

	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	metricsv1beta1 "k8s.io/metrics/pkg/client/clientset/versioned"
)

// ClusterManager manages connections and operations for Kubernetes clusters
type ClusterManager struct {
	// Kubernetes clients
	clientset     kubernetes.Interface // Changed to interface for better testability
	dynamicClient dynamic.Interface
	metricsClient *metricsv1beta1.Clientset
	config        *rest.Config

	// Configuration
	kubeconfigPath string
	kubeconfig     *Kubeconfig
	currentContext string

	// State
	connected bool
	mu        sync.RWMutex
}

// NewClusterManager creates a new ClusterManager instance
func NewClusterManager(kubeconfigPath string) (*ClusterManager, error) {
	if kubeconfigPath == "" {
		return nil, ErrKubeconfigPathEmpty
	}

	cm := &ClusterManager{
		kubeconfigPath: kubeconfigPath,
		connected:      false,
	}

	// Load kubeconfig
	kubeconfig, err := LoadKubeconfig(kubeconfigPath)
	if err != nil {
		return nil, fmt.Errorf("failed to load kubeconfig: %w", err)
	}
	cm.kubeconfig = kubeconfig
	cm.currentContext = kubeconfig.GetCurrentContext()

	return cm, nil
}

// Connect establishes connection to the Kubernetes cluster
func (cm *ClusterManager) Connect() error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if cm.connected {
		return nil // Already connected
	}

	// Build REST config from kubeconfig
	config, err := cm.kubeconfig.BuildRESTConfig(cm.currentContext)
	if err != nil {
		return fmt.Errorf("failed to build REST config: %w", err)
	}
	cm.config = config

	// Create Kubernetes clientset
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		return fmt.Errorf("failed to create clientset: %w", err)
	}
	cm.clientset = clientset

	// Create dynamic client for apply operations
	dynamicClient, err := dynamic.NewForConfig(config)
	if err != nil {
		return fmt.Errorf("failed to create dynamic client: %w", err)
	}
	cm.dynamicClient = dynamicClient

	// Create metrics client for top operations
	metricsClient, err := metricsv1beta1.NewForConfig(config)
	if err != nil {
		return fmt.Errorf("failed to create metrics client: %w", err)
	}
	cm.metricsClient = metricsClient

	// Verify connectivity with health check
	if err := cm.healthCheck(); err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	cm.connected = true
	return nil
}

// Disconnect closes the connection to the Kubernetes cluster
func (cm *ClusterManager) Disconnect() error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if !cm.connected {
		return nil // Already disconnected
	}

	// Kubernetes client-go doesn't require explicit disconnect
	// Just clear references
	cm.clientset = nil
	cm.config = nil
	cm.connected = false

	return nil
}

// HealthCheck verifies connectivity to the Kubernetes API server
func (cm *ClusterManager) HealthCheck() error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return ErrNotConnected
	}

	return cm.healthCheck()
}

// healthCheck performs the actual health check (requires lock held)
func (cm *ClusterManager) healthCheck() error {
	if cm.clientset == nil {
		return ErrClientsetNil
	}

	// Try to get server version as a health check
	_, err := cm.clientset.Discovery().ServerVersion()
	if err != nil {
		return fmt.Errorf("failed to reach Kubernetes API server: %w", err)
	}

	return nil
}

// GetCurrentContext returns the current Kubernetes context
func (cm *ClusterManager) GetCurrentContext() (string, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if cm.kubeconfig == nil {
		return "", ErrKubeconfigNil
	}

	return cm.currentContext, nil
}

// SetCurrentContext switches to a different Kubernetes context
func (cm *ClusterManager) SetCurrentContext(contextName string) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if cm.kubeconfig == nil {
		return ErrKubeconfigNil
	}

	// Verify context exists
	if !cm.kubeconfig.HasContext(contextName) {
		return fmt.Errorf("%w: %s", ErrContextNotFound, contextName)
	}

	// If connected, disconnect first
	if cm.connected {
		cm.clientset = nil
		cm.config = nil
		cm.connected = false
	}

	cm.currentContext = contextName

	return nil
}

// ListContexts returns all available Kubernetes contexts
func (cm *ClusterManager) ListContexts() ([]string, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if cm.kubeconfig == nil {
		return nil, ErrKubeconfigNil
	}

	return cm.kubeconfig.ListContexts(), nil
}

// IsConnected returns whether the manager is currently connected
func (cm *ClusterManager) IsConnected() bool {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	return cm.connected
}

// Clientset returns the underlying Kubernetes clientset (for advanced operations)
func (cm *ClusterManager) Clientset() kubernetes.Interface {
	return cm.clientset
}
