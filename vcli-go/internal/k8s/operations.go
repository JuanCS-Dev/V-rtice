package k8s

import (
	"context"
	"fmt"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// GetPods retrieves all pods in the specified namespace
// If namespace is empty string, retrieves pods from all namespaces
func (cm *ClusterManager) GetPods(namespace string) ([]Pod, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	// Empty string means all namespaces (don't default to "default")
	ctx := context.Background()
	podList, err := cm.clientset.CoreV1().Pods(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to list pods: %v", ErrOperationFailed, err)
	}

	pods := make([]Pod, len(podList.Items))
	for i, k8sPod := range podList.Items {
		pods[i] = convertPod(&k8sPod)
	}

	return pods, nil
}

// GetPod retrieves a specific pod by name in the specified namespace
func (cm *ClusterManager) GetPod(namespace, name string) (*Pod, error) {
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
	k8sPod, err := cm.clientset.CoreV1().Pods(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get pod %s: %v", ErrResourceNotFound, name, err)
	}

	pod := convertPod(k8sPod)
	return &pod, nil
}

// GetNamespaces retrieves all namespaces in the cluster
func (cm *ClusterManager) GetNamespaces() ([]Namespace, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	ctx := context.Background()
	nsList, err := cm.clientset.CoreV1().Namespaces().List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to list namespaces: %v", ErrOperationFailed, err)
	}

	namespaces := make([]Namespace, len(nsList.Items))
	for i, k8sNS := range nsList.Items {
		namespaces[i] = convertNamespace(&k8sNS)
	}

	return namespaces, nil
}

// GetNamespace retrieves a specific namespace by name
func (cm *ClusterManager) GetNamespace(name string) (*Namespace, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if name == "" {
		return nil, ErrResourceNameEmpty
	}

	ctx := context.Background()
	k8sNS, err := cm.clientset.CoreV1().Namespaces().Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get namespace %s: %v", ErrResourceNotFound, name, err)
	}

	ns := convertNamespace(k8sNS)
	return &ns, nil
}

// GetNodes retrieves all nodes in the cluster
func (cm *ClusterManager) GetNodes() ([]Node, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	ctx := context.Background()
	nodeList, err := cm.clientset.CoreV1().Nodes().List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to list nodes: %v", ErrOperationFailed, err)
	}

	nodes := make([]Node, len(nodeList.Items))
	for i, k8sNode := range nodeList.Items {
		nodes[i] = convertNode(&k8sNode)
	}

	return nodes, nil
}

// GetNode retrieves a specific node by name
func (cm *ClusterManager) GetNode(name string) (*Node, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if name == "" {
		return nil, ErrResourceNameEmpty
	}

	ctx := context.Background()
	k8sNode, err := cm.clientset.CoreV1().Nodes().Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get node %s: %v", ErrResourceNotFound, name, err)
	}

	node := convertNode(k8sNode)
	return &node, nil
}

// GetDeployments retrieves all deployments in the specified namespace
// If namespace is empty string, retrieves deployments from all namespaces
func (cm *ClusterManager) GetDeployments(namespace string) ([]Deployment, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	// Empty string means all namespaces (don't default to "default")
	ctx := context.Background()
	deployList, err := cm.clientset.AppsV1().Deployments(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to list deployments: %v", ErrOperationFailed, err)
	}

	deployments := make([]Deployment, len(deployList.Items))
	for i, k8sDeploy := range deployList.Items {
		deployments[i] = convertDeployment(&k8sDeploy)
	}

	return deployments, nil
}

// GetDeployment retrieves a specific deployment by name in the specified namespace
func (cm *ClusterManager) GetDeployment(namespace, name string) (*Deployment, error) {
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
	k8sDeploy, err := cm.clientset.AppsV1().Deployments(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get deployment %s: %v", ErrResourceNotFound, name, err)
	}

	deploy := convertDeployment(k8sDeploy)
	return &deploy, nil
}

// GetServices retrieves all services in the specified namespace
// If namespace is empty string, retrieves services from all namespaces
func (cm *ClusterManager) GetServices(namespace string) ([]Service, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	// Empty string means all namespaces (don't default to "default")
	ctx := context.Background()
	svcList, err := cm.clientset.CoreV1().Services(namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to list services: %v", ErrOperationFailed, err)
	}

	services := make([]Service, len(svcList.Items))
	for i, k8sService := range svcList.Items {
		services[i] = convertService(&k8sService)
	}

	return services, nil
}

// GetService retrieves a specific service by name in the specified namespace
func (cm *ClusterManager) GetService(namespace, name string) (*Service, error) {
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
	k8sService, err := cm.clientset.CoreV1().Services(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get service %s: %v", ErrResourceNotFound, name, err)
	}

	svc := convertService(k8sService)
	return &svc, nil
}

// GetConfigMaps retrieves all configmaps in the specified namespace
// If namespace is empty string, retrieves configmaps from all namespaces
func (cm *ClusterManager) GetConfigMaps(namespace string) ([]ConfigMap, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	// Use the existing ConfigMap operations
	listOpts := NewConfigMapListOptions()
	result, err := cm.ListConfigMaps(namespace, listOpts)
	if err != nil {
		return nil, fmt.Errorf("%w: failed to list configmaps: %v", ErrOperationFailed, err)
	}

	configmaps := make([]ConfigMap, len(result.Items))
	for i, k8sCM := range result.Items {
		configmaps[i] = convertConfigMap(&k8sCM)
	}

	return configmaps, nil
}

// GetConfigMapByName retrieves a specific configmap by name in the specified namespace
func (cm *ClusterManager) GetConfigMapByName(namespace, name string) (*ConfigMap, error) {
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

	// Use the existing ConfigMap operations
	k8sCM, err := cm.GetConfigMap(name, namespace)
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get configmap %s: %v", ErrResourceNotFound, name, err)
	}

	cm2 := convertConfigMap(k8sCM)
	return &cm2, nil
}

// GetSecrets retrieves all secrets in the specified namespace
// If namespace is empty string, retrieves secrets from all namespaces
func (cm *ClusterManager) GetSecrets(namespace string) ([]Secret, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	// Use the existing Secret operations
	listOpts := NewSecretListOptions()
	result, err := cm.ListSecrets(namespace, listOpts)
	if err != nil {
		return nil, fmt.Errorf("%w: failed to list secrets: %v", ErrOperationFailed, err)
	}

	secrets := make([]Secret, len(result.Items))
	for i, k8sSecret := range result.Items {
		secrets[i] = convertSecret(&k8sSecret)
	}

	return secrets, nil
}

// GetSecretByName retrieves a specific secret by name in the specified namespace
func (cm *ClusterManager) GetSecretByName(namespace, name string) (*Secret, error) {
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

	// Use the existing Secret operations
	k8sSecret, err := cm.GetSecret(name, namespace)
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get secret %s: %v", ErrResourceNotFound, name, err)
	}

	secret := convertSecret(k8sSecret)
	return &secret, nil
}
