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

// HandleGetPod handles the 'get pod <name>' command
func HandleGetPod(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("pod name is required")
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

// HandleGetNamespace handles the 'get namespace <name>' command
func HandleGetNamespace(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("namespace name is required")
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

// HandleGetNode handles the 'get node <name>' command
func HandleGetNode(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("node name is required")
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

// HandleGetDeployment handles the 'get deployment <name>' command
func HandleGetDeployment(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("deployment name is required")
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

// HandleGetService handles the 'get service <name>' command
func HandleGetService(cmd *cobra.Command, args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("service name is required")
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
