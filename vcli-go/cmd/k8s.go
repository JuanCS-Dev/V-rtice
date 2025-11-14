package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/help"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sCmd represents the k8s command
var k8sCmd = &cobra.Command{
	Use:   "k8s",
	Short: "Kubernetes cluster management",
	Long: `Manage Kubernetes clusters and resources.

The k8s command provides kubectl-style operations for managing Kubernetes
resources including pods, deployments, services, nodes, and namespaces.`,
	Example: help.BuildCobraExample(help.K8sGetExamples, help.K8sLogsExamples),
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
  - configmaps (cm)
  - secrets`,
	Example: help.BuildCobraExample(help.K8sGetExamples),
}

// ============================================================================
// GET POD COMMANDS
// ============================================================================

// getPodsCmd gets all pods in a namespace
var getPodsCmd = &cobra.Command{
	Use:     "pods",
	Aliases: []string{"po"},
	Short:   "Get pods",
	Long:    `Get all pods in a namespace or across all namespaces.`,
	Example: help.BuildCobraExample(help.K8sGetExamples),
	RunE:    k8s.HandleGetPods,
}

// getPodCmd gets a single pod or lists all pods if no name provided
var getPodCmd = &cobra.Command{
	Use:   "pod [name]",
	Short: "Get a specific pod or list all pods",
	Long: `Get details of a specific pod by name, or list all pods if no name provided.

Examples:
  # List all pods (same as 'get pods')
  vcli k8s get pod

  # Get pod details
  vcli k8s get pod nginx-7848d4b86f-9xvzk

  # Get pod in specific namespace
  vcli k8s get pod nginx-7848d4b86f-9xvzk --namespace production

  # Get pod details in JSON format
  vcli k8s get pod nginx-7848d4b86f-9xvzk --output json`,
	Args: cobra.MaximumNArgs(1),
	RunE: k8s.HandleGetPod,
}

// ============================================================================
// GET NAMESPACE COMMANDS
// ============================================================================

// getNamespacesCmd gets all namespaces
var getNamespacesCmd = &cobra.Command{
	Use:     "namespaces",
	Aliases: []string{"ns"},
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

// getNamespaceCmd gets a single namespace or lists all namespaces if no name provided
var getNamespaceCmd = &cobra.Command{
	Use:   "namespace [name]",
	Short: "Get a specific namespace or list all namespaces",
	Long: `Get details of a specific namespace by name, or list all namespaces if no name provided.

Examples:
  # List all namespaces (same as 'get namespaces')
  vcli k8s get namespace

  # Get namespace details
  vcli k8s get namespace kube-system

  # Get namespace in JSON format
  vcli k8s get namespace default --output json`,
	Args: cobra.MaximumNArgs(1),
	RunE: k8s.HandleGetNamespace,
}

// ============================================================================
// GET NODE COMMANDS
// ============================================================================

// getNodesCmd gets all nodes
var getNodesCmd = &cobra.Command{
	Use:     "nodes",
	Aliases: []string{"no"},
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

// getNodeCmd gets a single node or lists all nodes if no name provided
var getNodeCmd = &cobra.Command{
	Use:   "node [name]",
	Short: "Get a specific node or list all nodes",
	Long: `Get details of a specific node by name, or list all nodes if no name provided.

Examples:
  # List all nodes (same as 'get nodes')
  vcli k8s get node

  # Get node details
  vcli k8s get node worker-node-1

  # Get node in JSON format
  vcli k8s get node master-node --output json`,
	Args: cobra.MaximumNArgs(1),
	RunE: k8s.HandleGetNode,
}

// ============================================================================
// GET DEPLOYMENT COMMANDS
// ============================================================================

// getDeploymentsCmd gets all deployments
var getDeploymentsCmd = &cobra.Command{
	Use:     "deployments",
	Aliases: []string{"deploy"},
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

// getDeploymentCmd gets a single deployment or lists all deployments if no name provided
var getDeploymentCmd = &cobra.Command{
	Use:   "deployment [name]",
	Short: "Get a specific deployment or list all deployments",
	Long: `Get details of a specific deployment by name, or list all deployments if no name provided.

Examples:
  # List all deployments (same as 'get deployments')
  vcli k8s get deployment

  # Get deployment details
  vcli k8s get deployment nginx-deployment

  # Get deployment in specific namespace
  vcli k8s get deployment api-server --namespace production

  # Get deployment in JSON format
  vcli k8s get deployment web-app --output json`,
	Args: cobra.MaximumNArgs(1),
	RunE: k8s.HandleGetDeployment,
}

// ============================================================================
// GET SERVICE COMMANDS
// ============================================================================

// getServicesCmd gets all services
var getServicesCmd = &cobra.Command{
	Use:     "services",
	Aliases: []string{"svc"},
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

// getServiceCmd gets a single service or lists all services if no name provided
var getServiceCmd = &cobra.Command{
	Use:   "service [name]",
	Short: "Get a specific service or list all services",
	Long: `Get details of a specific service by name, or list all services if no name provided.

Examples:
  # List all services (same as 'get services')
  vcli k8s get service

  # Get service details
  vcli k8s get service kubernetes

  # Get service in specific namespace
  vcli k8s get service nginx-service --namespace default

  # Get service in JSON format
  vcli k8s get service api-gateway --output json`,
	Args: cobra.MaximumNArgs(1),
	RunE: k8s.HandleGetService,
}

// ============================================================================
// GET CONFIGMAP COMMANDS
// ============================================================================

// getConfigMapsCmd gets all configmaps
var getConfigMapsCmd = &cobra.Command{
	Use:     "configmaps",
	Aliases: []string{"cm"},
	Short:   "Get configmaps",
	Long: `Get all configmaps in a namespace or across all namespaces.

Examples:
  # List all configmaps in default namespace
  vcli k8s get configmaps

  # List configmaps in specific namespace
  vcli k8s get configmaps --namespace kube-system

  # List all configmaps across all namespaces
  vcli k8s get configmaps --all-namespaces

  # Output in JSON format
  vcli k8s get configmaps --output json`,
	RunE: k8s.HandleGetConfigMaps,
}

// getConfigMapCmd gets a single configmap or lists all configmaps if no name provided
var getConfigMapCmd = &cobra.Command{
	Use:   "configmap [name]",
	Short: "Get a specific configmap or list all configmaps",
	Long: `Get details of a specific configmap by name, or list all configmaps if no name provided.

Examples:
  # List all configmaps (same as 'get configmaps')
  vcli k8s get configmap

  # Get configmap details
  vcli k8s get configmap app-config

  # Get configmap in specific namespace
  vcli k8s get configmap database-config --namespace production

  # Get configmap in JSON format
  vcli k8s get configmap nginx-config --output json`,
	Args: cobra.MaximumNArgs(1),
	RunE: k8s.HandleGetConfigMap,
}

// ============================================================================
// GET SECRET COMMANDS
// ============================================================================

// getSecretsCmd gets all secrets
var getSecretsCmd = &cobra.Command{
	Use:   "secrets",
	Short: "Get secrets",
	Long: `Get all secrets in a namespace or across all namespaces.

Examples:
  # List all secrets in default namespace
  vcli k8s get secrets

  # List secrets in specific namespace
  vcli k8s get secrets --namespace kube-system

  # List all secrets across all namespaces
  vcli k8s get secrets --all-namespaces

  # Output in JSON format
  vcli k8s get secrets --output json`,
	RunE: k8s.HandleGetSecrets,
}

// getSecretCmd gets a single secret or lists all secrets if no name provided
var getSecretCmd = &cobra.Command{
	Use:   "secret [name]",
	Short: "Get a specific secret or list all secrets",
	Long: `Get details of a specific secret by name, or list all secrets if no name provided.

Examples:
  # List all secrets (same as 'get secrets')
  vcli k8s get secret

  # Get secret details
  vcli k8s get secret api-token

  # Get secret in specific namespace
  vcli k8s get secret database-password --namespace production

  # Get secret in JSON format
  vcli k8s get secret tls-cert --output json`,
	Args: cobra.MaximumNArgs(1),
	RunE: k8s.HandleGetSecret,
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
	k8sGetCmd.AddCommand(getConfigMapsCmd)
	k8sGetCmd.AddCommand(getConfigMapCmd)
	k8sGetCmd.AddCommand(getSecretsCmd)
	k8sGetCmd.AddCommand(getSecretCmd)

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
