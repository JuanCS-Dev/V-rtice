package k8s

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"
)

// HandlerConfig holds configuration for K8s command handlers
type HandlerConfig struct {
	KubeconfigPath string
	Namespace      string
	AllNamespaces  bool
	OutputFormat   OutputFormat
}

// NewHandlerConfig creates a new HandlerConfig with default values
func NewHandlerConfig() *HandlerConfig {
	return &HandlerConfig{
		KubeconfigPath: getDefaultKubeconfigPath(),
		Namespace:      "default",
		AllNamespaces:  false,
		OutputFormat:   OutputFormatTable,
	}
}

// getDefaultKubeconfigPath returns the default kubeconfig path
func getDefaultKubeconfigPath() string {
	// Try KUBECONFIG env var first
	if kubeconfig := os.Getenv("KUBECONFIG"); kubeconfig != "" {
		return kubeconfig
	}
	// Default to ~/.kube/config
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".kube", "config")
}

// parseCommonFlags extracts common flags from a command
func parseCommonFlags(cmd *cobra.Command) (*HandlerConfig, error) {
	config := NewHandlerConfig()

	// Parse kubeconfig path
	if cmd.Flags().Changed("kubeconfig") {
		kubeconfig, err := cmd.Flags().GetString("kubeconfig")
		if err != nil {
			return nil, fmt.Errorf("failed to parse kubeconfig flag: %w", err)
		}
		config.KubeconfigPath = kubeconfig
	}

	// Parse namespace
	if cmd.Flags().Changed("namespace") {
		namespace, err := cmd.Flags().GetString("namespace")
		if err != nil {
			return nil, fmt.Errorf("failed to parse namespace flag: %w", err)
		}
		config.Namespace = namespace
	}

	// Parse all-namespaces
	if cmd.Flags().Changed("all-namespaces") {
		allNamespaces, err := cmd.Flags().GetBool("all-namespaces")
		if err != nil {
			return nil, fmt.Errorf("failed to parse all-namespaces flag: %w", err)
		}
		config.AllNamespaces = allNamespaces
	}

	// Parse output format
	if cmd.Flags().Changed("output") {
		output, err := cmd.Flags().GetString("output")
		if err != nil {
			return nil, fmt.Errorf("failed to parse output flag: %w", err)
		}
		config.OutputFormat = OutputFormat(output)
	}

	return config, nil
}

// initClusterManager initializes and connects to a Kubernetes cluster
func initClusterManager(kubeconfigPath string) (*ClusterManager, error) {
	if kubeconfigPath == "" {
		return nil, fmt.Errorf("kubeconfig path is required")
	}

	// Create cluster manager
	manager, err := NewClusterManager(kubeconfigPath)
	if err != nil {
		return nil, fmt.Errorf("failed to create cluster manager: %w", err)
	}

	// Connect to cluster
	if err := manager.Connect(); err != nil {
		return nil, fmt.Errorf("failed to connect to cluster: %w", err)
	}

	return manager, nil
}

// formatAndPrint formats resources and prints them to stdout
func formatAndPrint(formatter Formatter, format func() (string, error)) error {
	output, err := format()
	if err != nil {
		return fmt.Errorf("failed to format output: %w", err)
	}

	fmt.Print(output)
	return nil
}

// ============================================================================
// GET POD HANDLERS
// ============================================================================

// HandleGetPods handles the 'get pods' command
func HandleGetPods(cmd *cobra.Command, args []string) error {
	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get pods
	namespace := config.Namespace
	if config.AllNamespaces {
		namespace = "" // Empty string means all namespaces
	}

	pods, err := manager.GetPods(namespace)
	if err != nil {
		return fmt.Errorf("failed to get pods: %w", err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatPods(pods)
	})
}

// HandleGetPod handles the 'get pod [name]' command
// If no name is provided, delegates to HandleGetPods to list all pods
func HandleGetPod(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		// No name provided - list all pods like 'get pods'
		return HandleGetPods(cmd, args)
	}

	podName := args[0]

	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get single pod
	pod, err := manager.GetPod(config.Namespace, podName)
	if err != nil {
		return fmt.Errorf("failed to get pod %s: %w", podName, err)
	}

	// Format and print (wrap in slice for formatters)
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatPods([]Pod{*pod})
	})
}

// ============================================================================
// GET NAMESPACE HANDLERS
// ============================================================================

// HandleGetNamespaces handles the 'get namespaces' command
func HandleGetNamespaces(cmd *cobra.Command, args []string) error {
	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get namespaces
	namespaces, err := manager.GetNamespaces()
	if err != nil {
		return fmt.Errorf("failed to get namespaces: %w", err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatNamespaces(namespaces)
	})
}

// HandleGetNamespace handles the 'get namespace [name]' command
// If no name is provided, delegates to HandleGetNamespaces to list all namespaces
func HandleGetNamespace(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		// No name provided - list all namespaces like 'get namespaces'
		return HandleGetNamespaces(cmd, args)
	}

	namespaceName := args[0]

	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get single namespace
	ns, err := manager.GetNamespace(namespaceName)
	if err != nil {
		return fmt.Errorf("failed to get namespace %s: %w", namespaceName, err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatNamespaces([]Namespace{*ns})
	})
}

// ============================================================================
// GET NODE HANDLERS
// ============================================================================

// HandleGetNodes handles the 'get nodes' command
func HandleGetNodes(cmd *cobra.Command, args []string) error {
	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get nodes
	nodes, err := manager.GetNodes()
	if err != nil {
		return fmt.Errorf("failed to get nodes: %w", err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatNodes(nodes)
	})
}

// HandleGetNode handles the 'get node [name]' command
// If no name is provided, delegates to HandleGetNodes to list all nodes
func HandleGetNode(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		// No name provided - list all nodes like 'get nodes'
		return HandleGetNodes(cmd, args)
	}

	nodeName := args[0]

	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get single node
	node, err := manager.GetNode(nodeName)
	if err != nil {
		return fmt.Errorf("failed to get node %s: %w", nodeName, err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatNodes([]Node{*node})
	})
}

// ============================================================================
// GET DEPLOYMENT HANDLERS
// ============================================================================

// HandleGetDeployments handles the 'get deployments' command
func HandleGetDeployments(cmd *cobra.Command, args []string) error {
	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get deployments
	namespace := config.Namespace
	if config.AllNamespaces {
		namespace = "" // Empty string means all namespaces
	}

	deployments, err := manager.GetDeployments(namespace)
	if err != nil {
		return fmt.Errorf("failed to get deployments: %w", err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatDeployments(deployments)
	})
}

// HandleGetDeployment handles the 'get deployment [name]' command
// If no name is provided, delegates to HandleGetDeployments to list all deployments
func HandleGetDeployment(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		// No name provided - list all deployments like 'get deployments'
		return HandleGetDeployments(cmd, args)
	}

	deploymentName := args[0]

	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get single deployment
	deployment, err := manager.GetDeployment(config.Namespace, deploymentName)
	if err != nil {
		return fmt.Errorf("failed to get deployment %s: %w", deploymentName, err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatDeployments([]Deployment{*deployment})
	})
}

// ============================================================================
// GET SERVICE HANDLERS
// ============================================================================

// HandleGetServices handles the 'get services' command
func HandleGetServices(cmd *cobra.Command, args []string) error {
	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get services
	namespace := config.Namespace
	if config.AllNamespaces {
		namespace = "" // Empty string means all namespaces
	}

	services, err := manager.GetServices(namespace)
	if err != nil {
		return fmt.Errorf("failed to get services: %w", err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatServices(services)
	})
}

// HandleGetService handles the 'get service [name]' command
// If no name is provided, delegates to HandleGetServices to list all services
func HandleGetService(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		// No name provided - list all services like 'get services'
		return HandleGetServices(cmd, args)
	}

	serviceName := args[0]

	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get single service
	service, err := manager.GetService(config.Namespace, serviceName)
	if err != nil {
		return fmt.Errorf("failed to get service %s: %w", serviceName, err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatServices([]Service{*service})
	})
}

// ============================================================================
// CONFIG HANDLERS
// ============================================================================

// HandleGetCurrentContext handles the 'config get-context' command
func HandleGetCurrentContext(cmd *cobra.Command, args []string) error {
	// Parse kubeconfig path
	kubeconfigPath := getDefaultKubeconfigPath()
	if cmd.Flags().Changed("kubeconfig") {
		path, err := cmd.Flags().GetString("kubeconfig")
		if err != nil {
			return err
		}
		kubeconfigPath = path
	}

	// Initialize cluster manager
	manager, err := NewClusterManager(kubeconfigPath)
	if err != nil {
		return err
	}

	// Get current context
	context, err := manager.GetCurrentContext()
	if err != nil {
		return err
	}

	fmt.Printf("Current context: %s\n", context)
	return nil
}

// HandleUseContext handles the 'config use-context <name>' command
func HandleUseContext(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("context name is required")
	}

	contextName := args[0]

	// Parse kubeconfig path
	kubeconfigPath := getDefaultKubeconfigPath()
	if cmd.Flags().Changed("kubeconfig") {
		path, err := cmd.Flags().GetString("kubeconfig")
		if err != nil {
			return err
		}
		kubeconfigPath = path
	}

	// Initialize cluster manager
	manager, err := NewClusterManager(kubeconfigPath)
	if err != nil {
		return err
	}

	// Set context
	if err := manager.SetCurrentContext(contextName); err != nil {
		return err
	}

	fmt.Printf("Switched to context: %s\n", contextName)
	return nil
}

// HandleListContexts handles the 'config get-contexts' command
func HandleListContexts(cmd *cobra.Command, args []string) error {
	// Parse kubeconfig path
	kubeconfigPath := getDefaultKubeconfigPath()
	if cmd.Flags().Changed("kubeconfig") {
		path, err := cmd.Flags().GetString("kubeconfig")
		if err != nil {
			return err
		}
		kubeconfigPath = path
	}

	// Initialize cluster manager
	manager, err := NewClusterManager(kubeconfigPath)
	if err != nil {
		return err
	}

	// List contexts
	contexts, err := manager.ListContexts()
	if err != nil {
		return err
	}

	// Get current context
	currentContext, err := manager.GetCurrentContext()
	if err != nil {
		return err
	}

	// Print contexts
	fmt.Println("CONTEXT")
	for _, ctx := range contexts {
		if ctx == currentContext {
			fmt.Printf("* %s (current)\n", ctx)
		} else {
			fmt.Printf("  %s\n", ctx)
		}
	}

	return nil
}

// ============================================================================
// CONFIGMAP HANDLERS
// ============================================================================

// HandleGetConfigMaps handles the 'get configmaps' command
func HandleGetConfigMaps(cmd *cobra.Command, args []string) error {
	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get configmaps
	namespace := config.Namespace
	if config.AllNamespaces {
		namespace = "" // Empty string means all namespaces
	}

	configmaps, err := manager.GetConfigMaps(namespace)
	if err != nil {
		return fmt.Errorf("failed to get configmaps: %w", err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatConfigMaps(configmaps)
	})
}

// HandleGetConfigMap handles the 'get configmap [name]' command
// If no name is provided, delegates to HandleGetConfigMaps to list all configmaps
func HandleGetConfigMap(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		// No name provided - list all configmaps like 'get configmaps'
		return HandleGetConfigMaps(cmd, args)
	}

	configmapName := args[0]

	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get single configmap
	configmap, err := manager.GetConfigMapByName(config.Namespace, configmapName)
	if err != nil {
		return fmt.Errorf("failed to get configmap %s: %w", configmapName, err)
	}

	// Format and print (wrap in slice for formatters)
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatConfigMaps([]ConfigMap{*configmap})
	})
}

// ============================================================================
// SECRET HANDLERS
// ============================================================================

// HandleGetSecrets handles the 'get secrets' command
func HandleGetSecrets(cmd *cobra.Command, args []string) error {
	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get secrets
	namespace := config.Namespace
	if config.AllNamespaces {
		namespace = "" // Empty string means all namespaces
	}

	secrets, err := manager.GetSecrets(namespace)
	if err != nil {
		return fmt.Errorf("failed to get secrets: %w", err)
	}

	// Format and print
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatSecrets(secrets)
	})
}

// HandleGetSecret handles the 'get secret [name]' command
// If no name is provided, delegates to HandleGetSecrets to list all secrets
func HandleGetSecret(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		// No name provided - list all secrets like 'get secrets'
		return HandleGetSecrets(cmd, args)
	}

	secretName := args[0]

	// Parse flags
	config, err := parseCommonFlags(cmd)
	if err != nil {
		return err
	}

	// Initialize cluster manager
	manager, err := initClusterManager(config.KubeconfigPath)
	if err != nil {
		return err
	}
	defer manager.Disconnect()

	// Get single secret
	secret, err := manager.GetSecretByName(config.Namespace, secretName)
	if err != nil {
		return fmt.Errorf("failed to get secret %s: %w", secretName, err)
	}

	// Format and print (wrap in slice for formatters)
	formatter, err := NewFormatter(config.OutputFormat)
	if err != nil {
		return err
	}

	return formatAndPrint(formatter, func() (string, error) {
		return formatter.FormatSecrets([]Secret{*secret})
	})
}
