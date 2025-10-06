package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/verticedev/vcli-go/internal/plugins"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

// KubernetesPlugin is a plugin for Kubernetes integration
type KubernetesPlugin struct {
	// Configuration
	kubeconfig  string
	namespace   string
	context     string

	// Kubernetes client
	clientset *kubernetes.Clientset
	config    *rest.Config

	// State
	initialized bool
	running     bool
	healthy     bool
	lastError   error

	// Metrics
	podCount        int
	deploymentCount int
	serviceCount    int
}

// NewPlugin is the plugin constructor (required by plugin system)
func NewPlugin() plugins.Plugin {
	return &KubernetesPlugin{
		namespace: "default",
	}
}

// Metadata returns plugin metadata
func (k *KubernetesPlugin) Metadata() plugins.Metadata {
	return plugins.Metadata{
		Name:        "kubernetes",
		Version:     "1.0.0",
		Description: "Kubernetes cluster management and monitoring",
		Author:      "vCLI Team",
		License:     "MIT",
		Homepage:    "https://github.com/verticedev/vcli-go/plugins/kubernetes",
		Tags:        []string{"kubernetes", "k8s", "orchestration", "containers"},
		Dependencies: []plugins.Dependency{
			{
				Name:       "kubectl",
				MinVersion: "1.28.0",
				Optional:   false,
			},
		},
		MinVCLIVersion: "0.1.0",
		LoadTime:       time.Now(),
	}
}

// Initialize initializes the plugin and connects to Kubernetes cluster
func (k *KubernetesPlugin) Initialize(ctx context.Context, config map[string]interface{}) error {
	// Load configuration
	if kubeconfig, ok := config["kubeconfig"].(string); ok {
		k.kubeconfig = kubeconfig
	}

	if namespace, ok := config["namespace"].(string); ok {
		k.namespace = namespace
	}

	if contextName, ok := config["context"].(string); ok {
		k.context = contextName
	}

	// Build Kubernetes client configuration
	var err error
	k.config, err = k.buildConfig()
	if err != nil {
		k.lastError = fmt.Errorf("failed to build K8s config: %w", err)
		k.healthy = false
		return k.lastError
	}

	// Create Kubernetes clientset
	k.clientset, err = kubernetes.NewForConfig(k.config)
	if err != nil {
		k.lastError = fmt.Errorf("failed to create K8s client: %w", err)
		k.healthy = false
		return k.lastError
	}

	// Verify connectivity by listing namespaces
	_, err = k.clientset.CoreV1().Namespaces().List(ctx, metav1.ListOptions{Limit: 1})
	if err != nil {
		k.lastError = fmt.Errorf("failed to connect to K8s cluster: %w", err)
		k.healthy = false
		return k.lastError
	}

	k.initialized = true
	k.healthy = true
	k.lastError = nil

	return nil
}

// buildConfig builds Kubernetes client configuration
func (k *KubernetesPlugin) buildConfig() (*rest.Config, error) {
	// If kubeconfig is explicitly provided, use it
	if k.kubeconfig != "" {
		return clientcmd.BuildConfigFromFlags("", k.kubeconfig)
	}

	// Try in-cluster config first (for when running inside K8s)
	config, err := rest.InClusterConfig()
	if err == nil {
		return config, nil
	}

	// Fall back to default kubeconfig location
	kubeconfigPath := filepath.Join(os.Getenv("HOME"), ".kube", "config")
	if _, err := os.Stat(kubeconfigPath); err == nil {
		return clientcmd.BuildConfigFromFlags("", kubeconfigPath)
	}

	return nil, fmt.Errorf("no kubeconfig found")
}

// Start starts the plugin
func (k *KubernetesPlugin) Start(ctx context.Context) error {
	if !k.initialized {
		return fmt.Errorf("plugin not initialized")
	}

	// Start background monitoring
	go k.monitorCluster(ctx)

	k.running = true
	return nil
}

// Stop stops the plugin
func (k *KubernetesPlugin) Stop(ctx context.Context) error {
	k.running = false
	return nil
}

// Health returns plugin health status
func (k *KubernetesPlugin) Health() plugins.HealthStatus {
	status := plugins.HealthStatus{
		Healthy:   k.healthy,
		LastCheck: time.Now(),
		Metrics: map[string]interface{}{
			"pods":        k.podCount,
			"deployments": k.deploymentCount,
			"services":    k.serviceCount,
		},
	}

	if k.lastError != nil {
		status.Healthy = false
		status.Message = k.lastError.Error()
	} else {
		status.Message = "Connected to Kubernetes cluster"
	}

	return status
}

// Commands returns CLI commands provided by this plugin
func (k *KubernetesPlugin) Commands() []plugins.Command {
	return []plugins.Command{
		{
			Name:    "k8s",
			Aliases: []string{"kubectl"},
			Short:   "Kubernetes cluster operations",
			Long:    "Manage and monitor Kubernetes clusters",
			Example: "vcli k8s get pods",
			Handler: k.handleCommand,
			Subcommands: []plugins.Command{
				{
					Name:    "get",
					Short:   "Get Kubernetes resources",
					Handler: k.handleGet,
				},
				{
					Name:    "describe",
					Short:   "Describe Kubernetes resources",
					Handler: k.handleDescribe,
				},
				{
					Name:    "logs",
					Short:   "Get pod logs",
					Handler: k.handleLogs,
				},
			},
		},
	}
}

// View returns the plugin's TUI view component
func (k *KubernetesPlugin) View() plugins.View {
	return &KubernetesView{
		plugin: k,
	}
}

// Capabilities returns plugin capabilities
func (k *KubernetesPlugin) Capabilities() []plugins.Capability {
	return []plugins.Capability{
		plugins.CapabilityNetwork,    // Need network for K8s API
		plugins.CapabilityKubernetes, // K8s-specific capability
		plugins.CapabilityTUI,         // Provide TUI view
		plugins.CapabilityCLI,         // Provide CLI commands
	}
}

// monitorCluster monitors the Kubernetes cluster and updates metrics
func (k *KubernetesPlugin) monitorCluster(ctx context.Context) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	// Update immediately on start
	k.updateMetrics(ctx)

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			k.updateMetrics(ctx)
		}
	}
}

// updateMetrics queries Kubernetes API and updates resource counts
func (k *KubernetesPlugin) updateMetrics(ctx context.Context) {
	if k.clientset == nil {
		k.healthy = false
		k.lastError = fmt.Errorf("clientset not initialized")
		return
	}

	// Query pod count
	pods, err := k.clientset.CoreV1().Pods(k.namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		k.healthy = false
		k.lastError = fmt.Errorf("failed to list pods: %w", err)
		return
	}
	k.podCount = len(pods.Items)

	// Query deployment count
	deployments, err := k.clientset.AppsV1().Deployments(k.namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		k.healthy = false
		k.lastError = fmt.Errorf("failed to list deployments: %w", err)
		return
	}
	k.deploymentCount = len(deployments.Items)

	// Query service count
	services, err := k.clientset.CoreV1().Services(k.namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		k.healthy = false
		k.lastError = fmt.Errorf("failed to list services: %w", err)
		return
	}
	k.serviceCount = len(services.Items)

	// All queries successful
	k.healthy = true
	k.lastError = nil
}

// handleCommand handles the k8s command
func (k *KubernetesPlugin) handleCommand(args []string) error {
	if len(args) == 0 {
		fmt.Println("Kubernetes Plugin v1.0.0")
		fmt.Println("Usage: vcli k8s <command>")
		return nil
	}
	return fmt.Errorf("unknown command: %s", args[0])
}

// handleGet handles the get command and queries Kubernetes API
func (k *KubernetesPlugin) handleGet(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("resource type required")
	}

	if k.clientset == nil {
		return fmt.Errorf("kubernetes client not initialized")
	}

	resourceType := args[0]
	ctx := context.Background()

	switch resourceType {
	case "pods", "pod", "po":
		return k.getPods(ctx)
	case "deployments", "deployment", "deploy":
		return k.getDeployments(ctx)
	case "services", "service", "svc":
		return k.getServices(ctx)
	default:
		return fmt.Errorf("unsupported resource type: %s (supported: pods, deployments, services)", resourceType)
	}
}

// getPods lists pods in the namespace
func (k *KubernetesPlugin) getPods(ctx context.Context) error {
	pods, err := k.clientset.CoreV1().Pods(k.namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return fmt.Errorf("failed to list pods: %w", err)
	}

	fmt.Printf("Namespace: %s\n\n", k.namespace)
	fmt.Printf("NAME                          READY   STATUS    RESTARTS   AGE\n")

	for _, pod := range pods.Items {
		readyCount := 0
		totalCount := len(pod.Status.ContainerStatuses)
		for _, cs := range pod.Status.ContainerStatuses {
			if cs.Ready {
				readyCount++
			}
		}

		restarts := int32(0)
		for _, cs := range pod.Status.ContainerStatuses {
			restarts += cs.RestartCount
		}

		age := time.Since(pod.CreationTimestamp.Time).Truncate(time.Second)
		fmt.Printf("%-30s %d/%d     %-9s %d          %v\n",
			pod.Name,
			readyCount,
			totalCount,
			pod.Status.Phase,
			restarts,
			age,
		)
	}

	return nil
}

// getDeployments lists deployments in the namespace
func (k *KubernetesPlugin) getDeployments(ctx context.Context) error {
	deployments, err := k.clientset.AppsV1().Deployments(k.namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return fmt.Errorf("failed to list deployments: %w", err)
	}

	fmt.Printf("Namespace: %s\n\n", k.namespace)
	fmt.Printf("NAME                    READY   UP-TO-DATE   AVAILABLE   AGE\n")

	for _, deploy := range deployments.Items {
		age := time.Since(deploy.CreationTimestamp.Time).Truncate(time.Second)
		fmt.Printf("%-24s %d/%d     %d            %d           %v\n",
			deploy.Name,
			deploy.Status.ReadyReplicas,
			deploy.Status.Replicas,
			deploy.Status.UpdatedReplicas,
			deploy.Status.AvailableReplicas,
			age,
		)
	}

	return nil
}

// getServices lists services in the namespace
func (k *KubernetesPlugin) getServices(ctx context.Context) error {
	services, err := k.clientset.CoreV1().Services(k.namespace).List(ctx, metav1.ListOptions{})
	if err != nil {
		return fmt.Errorf("failed to list services: %w", err)
	}

	fmt.Printf("Namespace: %s\n\n", k.namespace)
	fmt.Printf("NAME                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE\n")

	for _, svc := range services.Items {
		externalIP := "<none>"
		if len(svc.Status.LoadBalancer.Ingress) > 0 {
			if svc.Status.LoadBalancer.Ingress[0].IP != "" {
				externalIP = svc.Status.LoadBalancer.Ingress[0].IP
			}
		}

		ports := ""
		for i, port := range svc.Spec.Ports {
			if i > 0 {
				ports += ","
			}
			ports += fmt.Sprintf("%d/%s", port.Port, port.Protocol)
		}

		age := time.Since(svc.CreationTimestamp.Time).Truncate(time.Second)
		fmt.Printf("%-20s %-11s %-15s %-13s %-14s %v\n",
			svc.Name,
			svc.Spec.Type,
			svc.Spec.ClusterIP,
			externalIP,
			ports,
			age,
		)
	}

	return nil
}

// handleDescribe handles the describe command and shows detailed resource information
func (k *KubernetesPlugin) handleDescribe(args []string) error {
	if len(args) < 2 {
		return fmt.Errorf("resource type and name required")
	}

	if k.clientset == nil {
		return fmt.Errorf("kubernetes client not initialized")
	}

	resourceType := args[0]
	resourceName := args[1]
	ctx := context.Background()

	switch resourceType {
	case "pod", "po":
		return k.describePod(ctx, resourceName)
	case "deployment", "deploy":
		return k.describeDeployment(ctx, resourceName)
	case "service", "svc":
		return k.describeService(ctx, resourceName)
	default:
		return fmt.Errorf("unsupported resource type: %s (supported: pod, deployment, service)", resourceType)
	}
}

// describePod shows detailed pod information
func (k *KubernetesPlugin) describePod(ctx context.Context, name string) error {
	pod, err := k.clientset.CoreV1().Pods(k.namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get pod: %w", err)
	}

	fmt.Printf("Name:         %s\n", pod.Name)
	fmt.Printf("Namespace:    %s\n", pod.Namespace)
	fmt.Printf("Status:       %s\n", pod.Status.Phase)
	fmt.Printf("IP:           %s\n", pod.Status.PodIP)
	fmt.Printf("Node:         %s\n", pod.Spec.NodeName)
	fmt.Printf("Start Time:   %s\n", pod.Status.StartTime.Format(time.RFC3339))
	fmt.Printf("\nContainers:\n")

	for _, container := range pod.Spec.Containers {
		fmt.Printf("  %s:\n", container.Name)
		fmt.Printf("    Image:   %s\n", container.Image)

		for _, cs := range pod.Status.ContainerStatuses {
			if cs.Name == container.Name {
				fmt.Printf("    Ready:   %v\n", cs.Ready)
				fmt.Printf("    Restarts: %d\n", cs.RestartCount)
				fmt.Printf("    State:   %v\n", cs.State)
			}
		}
	}

	return nil
}

// describeDeployment shows detailed deployment information
func (k *KubernetesPlugin) describeDeployment(ctx context.Context, name string) error {
	deployment, err := k.clientset.AppsV1().Deployments(k.namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get deployment: %w", err)
	}

	fmt.Printf("Name:               %s\n", deployment.Name)
	fmt.Printf("Namespace:          %s\n", deployment.Namespace)
	fmt.Printf("Replicas:           %d desired | %d updated | %d total | %d available\n",
		*deployment.Spec.Replicas,
		deployment.Status.UpdatedReplicas,
		deployment.Status.Replicas,
		deployment.Status.AvailableReplicas)
	fmt.Printf("Strategy:           %s\n", deployment.Spec.Strategy.Type)
	fmt.Printf("Selector:           %v\n", deployment.Spec.Selector.MatchLabels)

	return nil
}

// describeService shows detailed service information
func (k *KubernetesPlugin) describeService(ctx context.Context, name string) error {
	service, err := k.clientset.CoreV1().Services(k.namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get service: %w", err)
	}

	fmt.Printf("Name:         %s\n", service.Name)
	fmt.Printf("Namespace:    %s\n", service.Namespace)
	fmt.Printf("Type:         %s\n", service.Spec.Type)
	fmt.Printf("Cluster IP:   %s\n", service.Spec.ClusterIP)
	fmt.Printf("Ports:\n")

	for _, port := range service.Spec.Ports {
		fmt.Printf("  %s: %d/%s -> %d\n", port.Name, port.Port, port.Protocol, port.TargetPort.IntVal)
	}

	fmt.Printf("Selector:     %v\n", service.Spec.Selector)

	return nil
}

// handleLogs handles the logs command and streams pod logs from Kubernetes API
func (k *KubernetesPlugin) handleLogs(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("pod name required")
	}

	if k.clientset == nil {
		return fmt.Errorf("kubernetes client not initialized")
	}

	podName := args[0]
	ctx := context.Background()

	// Get pod to verify it exists
	pod, err := k.clientset.CoreV1().Pods(k.namespace).Get(ctx, podName, metav1.GetOptions{})
	if err != nil {
		return fmt.Errorf("failed to get pod: %w", err)
	}

	// Determine container name
	containerName := ""
	if len(args) > 1 {
		containerName = args[1]
	} else if len(pod.Spec.Containers) == 1 {
		containerName = pod.Spec.Containers[0].Name
	} else {
		fmt.Printf("Pod has multiple containers. Please specify container name:\n")
		for _, c := range pod.Spec.Containers {
			fmt.Printf("  - %s\n", c.Name)
		}
		return fmt.Errorf("container name required")
	}

	// Get logs
	logOptions := &corev1.PodLogOptions{
		Container: containerName,
		Follow:    false,
		TailLines: int64Ptr(100),
	}

	req := k.clientset.CoreV1().Pods(k.namespace).GetLogs(podName, logOptions)
	logs, err := req.Stream(ctx)
	if err != nil {
		return fmt.Errorf("failed to get logs: %w", err)
	}
	defer logs.Close()

	fmt.Printf("Logs for pod %s (container: %s):\n\n", podName, containerName)

	// Stream logs to stdout
	buf := make([]byte, 4096)
	for {
		n, err := logs.Read(buf)
		if n > 0 {
			fmt.Print(string(buf[:n]))
		}
		if err != nil {
			break
		}
	}

	return nil
}

// int64Ptr returns pointer to int64
func int64Ptr(i int64) *int64 {
	return &i
}

// KubernetesView is the TUI view for Kubernetes plugin
type KubernetesView struct {
	plugin  *KubernetesPlugin
	focused bool
}

func (kv *KubernetesView) ID() string {
	return "kubernetes-view"
}

func (kv *KubernetesView) Render() string {
	var (
		titleStyle = lipgloss.NewStyle().
				Bold(true).
				Foreground(lipgloss.Color("#7D56F4")).
				Padding(0, 1)

		boxStyle = lipgloss.NewStyle().
				Border(lipgloss.RoundedBorder()).
				BorderForeground(lipgloss.Color("#7D56F4")).
				Padding(1, 2).
				Margin(1, 0)

		labelStyle = lipgloss.NewStyle().
				Bold(true).
				Foreground(lipgloss.Color("#00BFFF"))

		valueStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#FAFAFA"))
	)

	// Title
	title := titleStyle.Render("☸ Kubernetes Cluster")

	// Cluster info
	var content string
	content += labelStyle.Render("Namespace:") + "   " + valueStyle.Render(kv.plugin.namespace) + "\n"
	content += labelStyle.Render("Context:") + "     " + valueStyle.Render(kv.plugin.context) + "\n"
	content += "\n"

	// Resource counts
	content += labelStyle.Render("Resources:") + "\n"
	content += fmt.Sprintf("  Pods:        %s\n", valueStyle.Render(fmt.Sprintf("%d", kv.plugin.podCount)))
	content += fmt.Sprintf("  Deployments: %s\n", valueStyle.Render(fmt.Sprintf("%d", kv.plugin.deploymentCount)))
	content += fmt.Sprintf("  Services:    %s\n", valueStyle.Render(fmt.Sprintf("%d", kv.plugin.serviceCount)))
	content += "\n"

	// Health status
	healthIcon := "✓"
	healthColor := "#00FF00"
	if !kv.plugin.healthy {
		healthIcon = "✗"
		healthColor = "#FF0000"
	}

	healthStyle := lipgloss.NewStyle().Foreground(lipgloss.Color(healthColor))
	content += labelStyle.Render("Status:") + "      " + healthStyle.Render(healthIcon+" "+kv.plugin.Health().Message) + "\n"

	box := boxStyle.Render(content)

	return title + "\n" + box
}

func (kv *KubernetesView) Update(msg tea.Msg) (plugins.View, tea.Cmd) {
	// Handle view-specific updates
	return kv, nil
}

func (kv *KubernetesView) Init() tea.Cmd {
	return nil
}

func (kv *KubernetesView) Focus() {
	kv.focused = true
}

func (kv *KubernetesView) Blur() {
	kv.focused = false
}

func (kv *KubernetesView) IsFocused() bool {
	return kv.focused
}

// This allows the plugin to be built as a .so file:
// go build -buildmode=plugin -o kubernetes.so kubernetes.go
