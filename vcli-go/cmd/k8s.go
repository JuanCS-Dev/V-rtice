package main

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sCmd represents the k8s command
var k8sCmd = &cobra.Command{
	Use:   "k8s",
	Short: "Kubernetes cluster management",
	Long: `Manage Kubernetes clusters and resources.

The k8s command provides kubectl-style operations for managing Kubernetes
resources including pods, deployments, services, nodes, and namespaces.

Examples:
  # List pods in default namespace
  vcli k8s get pods

  # List pods in specific namespace
  vcli k8s get pods --namespace kube-system

  # List pods across all namespaces
  vcli k8s get pods --all-namespaces

  # Get pods in JSON format
  vcli k8s get pods --output json

  # Get single pod details
  vcli k8s get pod nginx-7848d4b86f-9xvzk

  # List all nodes
  vcli k8s get nodes

  # Get current context
  vcli k8s config get-context

  # Switch context
  vcli k8s config use-context production`,
}

// ============================================================================
// GET COMMAND
// ============================================================================

// k8sGetCmd represents the 'k8s get' command
var k8sGetCmd = &cobra.Command{
	Use:   "get [resource]",
	Short: "Get Kubernetes resources",
	Long: `Get one or many Kubernetes resources.

Supported resources:
  - pods (po)
  - namespaces (ns)
  - nodes (no)
  - deployments (deploy)
  - services (svc)

Examples:
  vcli k8s get pods
  vcli k8s get namespaces
  vcli k8s get nodes
  vcli k8s get deployments
  vcli k8s get services`,
}

// ============================================================================
// GET POD COMMANDS
// ============================================================================

// getPodsCmd gets all pods in a namespace
var getPodsCmd = &cobra.Command{
	Use:     "pods",
	Aliases: []string{"pod", "po"},
	Short:   "Get pods",
	Long: `Get all pods in a namespace or across all namespaces.

Examples:
  # List all pods in default namespace
  vcli k8s get pods

  # List all pods in kube-system namespace
  vcli k8s get pods --namespace kube-system

  # List all pods across all namespaces
  vcli k8s get pods --all-namespaces

  # Output in JSON format
  vcli k8s get pods --output json

  # Output in YAML format
  vcli k8s get pods --output yaml`,
	RunE: k8s.HandleGetPods,
}

// getPodCmd gets a single pod
var getPodCmd = &cobra.Command{
	Use:   "pod [name]",
	Short: "Get a specific pod",
	Long: `Get details of a specific pod by name.

Examples:
  # Get pod details
  vcli k8s get pod nginx-7848d4b86f-9xvzk

  # Get pod in specific namespace
  vcli k8s get pod nginx-7848d4b86f-9xvzk --namespace production

  # Get pod details in JSON format
  vcli k8s get pod nginx-7848d4b86f-9xvzk --output json`,
	Args: cobra.ExactArgs(1),
	RunE: k8s.HandleGetPod,
}

// ============================================================================
// GET NAMESPACE COMMANDS
// ============================================================================

// getNamespacesCmd gets all namespaces
var getNamespacesCmd = &cobra.Command{
	Use:     "namespaces",
	Aliases: []string{"namespace", "ns"},
	Short:   "Get namespaces",
	Long: `Get all namespaces in the cluster.

Examples:
  # List all namespaces
  vcli k8s get namespaces

  # Output in JSON format
  vcli k8s get namespaces --output json

  # Output in YAML format
  vcli k8s get namespaces --output yaml`,
	RunE: k8s.HandleGetNamespaces,
}

// getNamespaceCmd gets a single namespace
var getNamespaceCmd = &cobra.Command{
	Use:   "namespace [name]",
	Short: "Get a specific namespace",
	Long: `Get details of a specific namespace by name.

Examples:
  # Get namespace details
  vcli k8s get namespace kube-system

  # Get namespace in JSON format
  vcli k8s get namespace default --output json`,
	Args: cobra.ExactArgs(1),
	RunE: k8s.HandleGetNamespace,
}

// ============================================================================
// GET NODE COMMANDS
// ============================================================================

// getNodesCmd gets all nodes
var getNodesCmd = &cobra.Command{
	Use:     "nodes",
	Aliases: []string{"node", "no"},
	Short:   "Get nodes",
	Long: `Get all nodes in the cluster.

Examples:
  # List all nodes
  vcli k8s get nodes

  # Output in JSON format
  vcli k8s get nodes --output json

  # Output in YAML format
  vcli k8s get nodes --output yaml`,
	RunE: k8s.HandleGetNodes,
}

// getNodeCmd gets a single node
var getNodeCmd = &cobra.Command{
	Use:   "node [name]",
	Short: "Get a specific node",
	Long: `Get details of a specific node by name.

Examples:
  # Get node details
  vcli k8s get node worker-node-1

  # Get node in JSON format
  vcli k8s get node master-node --output json`,
	Args: cobra.ExactArgs(1),
	RunE: k8s.HandleGetNode,
}

// ============================================================================
// GET DEPLOYMENT COMMANDS
// ============================================================================

// getDeploymentsCmd gets all deployments
var getDeploymentsCmd = &cobra.Command{
	Use:     "deployments",
	Aliases: []string{"deployment", "deploy"},
	Short:   "Get deployments",
	Long: `Get all deployments in a namespace or across all namespaces.

Examples:
  # List all deployments in default namespace
  vcli k8s get deployments

  # List deployments in specific namespace
  vcli k8s get deployments --namespace production

  # List all deployments across all namespaces
  vcli k8s get deployments --all-namespaces

  # Output in JSON format
  vcli k8s get deployments --output json`,
	RunE: k8s.HandleGetDeployments,
}

// getDeploymentCmd gets a single deployment
var getDeploymentCmd = &cobra.Command{
	Use:   "deployment [name]",
	Short: "Get a specific deployment",
	Long: `Get details of a specific deployment by name.

Examples:
  # Get deployment details
  vcli k8s get deployment nginx-deployment

  # Get deployment in specific namespace
  vcli k8s get deployment api-server --namespace production

  # Get deployment in JSON format
  vcli k8s get deployment web-app --output json`,
	Args: cobra.ExactArgs(1),
	RunE: k8s.HandleGetDeployment,
}

// ============================================================================
// GET SERVICE COMMANDS
// ============================================================================

// getServicesCmd gets all services
var getServicesCmd = &cobra.Command{
	Use:     "services",
	Aliases: []string{"service", "svc"},
	Short:   "Get services",
	Long: `Get all services in a namespace or across all namespaces.

Examples:
  # List all services in default namespace
  vcli k8s get services

  # List services in specific namespace
  vcli k8s get services --namespace kube-system

  # List all services across all namespaces
  vcli k8s get services --all-namespaces

  # Output in JSON format
  vcli k8s get services --output json`,
	RunE: k8s.HandleGetServices,
}

// getServiceCmd gets a single service
var getServiceCmd = &cobra.Command{
	Use:   "service [name]",
	Short: "Get a specific service",
	Long: `Get details of a specific service by name.

Examples:
  # Get service details
  vcli k8s get service kubernetes

  # Get service in specific namespace
  vcli k8s get service nginx-service --namespace default

  # Get service in JSON format
  vcli k8s get service api-gateway --output json`,
	Args: cobra.ExactArgs(1),
	RunE: k8s.HandleGetService,
}

// ============================================================================
// CONFIG COMMAND
// ============================================================================

// k8sConfigCmd represents the 'k8s config' command
var k8sConfigCmd = &cobra.Command{
	Use:   "config",
	Short: "Manage kubeconfig contexts",
	Long: `Manage kubeconfig contexts and cluster connections.

Examples:
  # Get current context
  vcli k8s config get-context

  # List all contexts
  vcli k8s config get-contexts

  # Switch to a different context
  vcli k8s config use-context production`,
}

// getCurrentContextCmd gets the current context
var getCurrentContextCmd = &cobra.Command{
	Use:   "get-context",
	Short: "Get current context",
	Long: `Display the current kubeconfig context.

Examples:
  # Get current context
  vcli k8s config get-context

  # Get current context from custom kubeconfig
  vcli k8s config get-context --kubeconfig /custom/kubeconfig`,
	RunE: k8s.HandleGetCurrentContext,
}

// getContextsCmd lists all contexts
var getContextsCmd = &cobra.Command{
	Use:     "get-contexts",
	Aliases: []string{"contexts"},
	Short:   "List all contexts",
	Long: `List all available kubeconfig contexts.

The current context is marked with an asterisk (*).

Examples:
  # List all contexts
  vcli k8s config get-contexts

  # List contexts from custom kubeconfig
  vcli k8s config get-contexts --kubeconfig /custom/kubeconfig`,
	RunE: k8s.HandleListContexts,
}

// useContextCmd switches to a different context
var useContextCmd = &cobra.Command{
	Use:   "use-context [name]",
	Short: "Switch to a different context",
	Long: `Switch the current kubeconfig context to the specified context.

Examples:
  # Switch to production context
  vcli k8s config use-context production

  # Switch context in custom kubeconfig
  vcli k8s config use-context staging --kubeconfig /custom/kubeconfig`,
	Args: cobra.ExactArgs(1),
	RunE: k8s.HandleUseContext,
}

// ============================================================================
// INITIALIZATION
// ============================================================================

func init() {
	// Add k8s command to root
	rootCmd.AddCommand(k8sCmd)

	// Add get command to k8s
	k8sCmd.AddCommand(k8sGetCmd)

	// Add resource commands to 'get'
	k8sGetCmd.AddCommand(getPodsCmd)
	k8sGetCmd.AddCommand(getPodCmd)
	k8sGetCmd.AddCommand(getNamespacesCmd)
	k8sGetCmd.AddCommand(getNamespaceCmd)
	k8sGetCmd.AddCommand(getNodesCmd)
	k8sGetCmd.AddCommand(getNodeCmd)
	k8sGetCmd.AddCommand(getDeploymentsCmd)
	k8sGetCmd.AddCommand(getDeploymentCmd)
	k8sGetCmd.AddCommand(getServicesCmd)
	k8sGetCmd.AddCommand(getServiceCmd)

	// Add config command to k8s
	k8sCmd.AddCommand(k8sConfigCmd)
	k8sConfigCmd.AddCommand(getCurrentContextCmd)
	k8sConfigCmd.AddCommand(getContextsCmd)
	k8sConfigCmd.AddCommand(useContextCmd)

	// ========================================================================
	// GLOBAL FLAGS (apply to all k8s commands)
	// ========================================================================

	k8sCmd.PersistentFlags().String("kubeconfig", "", "Path to kubeconfig file (default: $KUBECONFIG or ~/.kube/config)")

	// ========================================================================
	// GET COMMAND FLAGS
	// ========================================================================

	// Namespace flag for resource commands
	k8sGetCmd.PersistentFlags().StringP("namespace", "n", "default", "Kubernetes namespace")
	k8sGetCmd.PersistentFlags().BoolP("all-namespaces", "A", false, "List resources across all namespaces")

	// Output format flag
	k8sGetCmd.PersistentFlags().StringP("output", "o", "table", "Output format: table, json, yaml")
}

// validateK8sCommands performs validation checks on k8s commands
func validateK8sCommands() error {
	// Validate that all resource commands have proper flags
	requiredFlags := []string{"namespace", "output"}

	for _, flag := range requiredFlags {
		if !k8sGetCmd.PersistentFlags().HasFlags() {
			return fmt.Errorf("missing required flag: %s", flag)
		}
	}

	return nil
}
