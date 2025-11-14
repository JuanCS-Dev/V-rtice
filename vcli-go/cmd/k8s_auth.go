package cmd

import (
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sAuthCmd represents the 'k8s auth' command
var k8sAuthCmd = &cobra.Command{
	Use:   "auth",
	Short: "Inspect authorization",
	Long: `Inspect authorization and user information.

The auth command group provides tools for checking permissions and viewing
user information in the Kubernetes cluster.`,
}

// authCanICmd represents the 'auth can-i' command
var authCanICmd = &cobra.Command{
	Use:   "can-i VERB RESOURCE [RESOURCENAME]",
	Short: "Check whether an action is allowed",
	Long: `Check whether the current user can perform a specific action.

This command checks if the current user has permission to perform a specific
verb on a resource. It returns 'yes' if allowed, 'no' otherwise.

Examples:
  # Check if you can create pods
  vcli k8s auth can-i create pods

  # Check if you can list deployments
  vcli k8s auth can-i list deployments

  # Check if you can get a specific pod
  vcli k8s auth can-i get pods my-pod

  # Check in a specific namespace
  vcli k8s auth can-i delete pods --namespace kube-system

  # Check across all namespaces
  vcli k8s auth can-i list pods --all-namespaces

  # Check if you can access pod logs (subresource)
  vcli k8s auth can-i get pods --subresource=log

  # Common verbs: get, list, create, update, patch, delete, watch`,
	Args: cobra.MinimumNArgs(2),
	RunE: k8s.HandleCanI,
}

// authWhoAmICmd represents the 'auth whoami' command
var authWhoAmICmd = &cobra.Command{
	Use:   "whoami",
	Short: "Display information about the current user",
	Long: `Display information about the current user authenticated to the cluster.

This command shows the username, UID, groups, and additional authentication
information for the current user.

Examples:
  # Display current user information
  vcli k8s auth whoami

  # Display as JSON
  vcli k8s auth whoami --output json

  # Display as YAML
  vcli k8s auth whoami --output yaml`,
	Args: cobra.NoArgs,
	RunE: k8s.HandleWhoAmI,
}

func init() {
	// Add auth command to k8s command
	k8sCmd.AddCommand(k8sAuthCmd)

	// Add subcommands to auth
	k8sAuthCmd.AddCommand(authCanICmd)
	k8sAuthCmd.AddCommand(authWhoAmICmd)

	// Flags for can-i command
	authCanICmd.Flags().String("namespace", "", "Kubernetes namespace")
	authCanICmd.Flags().Bool("all-namespaces", false, "Check across all namespaces")
	authCanICmd.Flags().String("subresource", "", "SubResource such as pod/log or deployment/scale")
	authCanICmd.Flags().StringP("kubeconfig", "k", "", "Path to kubeconfig file")
	authCanICmd.Flags().String("context", "", "Kubernetes context to use")

	// Flags for whoami command
	authWhoAmICmd.Flags().StringP("output", "o", "", "Output format: json, yaml, or table (default)")
	authWhoAmICmd.Flags().StringP("kubeconfig", "k", "", "Path to kubeconfig file")
	authWhoAmICmd.Flags().String("context", "", "Kubernetes context to use")
}
