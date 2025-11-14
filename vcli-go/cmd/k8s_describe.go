package cmd

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	vcliFs "github.com/verticedev/vcli-go/internal/fs"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sDescribeCmd represents the 'k8s describe' command
var k8sDescribeCmd = &cobra.Command{
	Use:   "describe",
	Short: "Show detailed information about resources",
	Long: `Show detailed information about Kubernetes resources.

The describe command provides detailed information about resources including
metadata, spec, status, and related events.

Examples:
  # Describe a pod
  vcli k8s describe pod nginx-7848d4b86f-9xvzk

  # Describe a deployment
  vcli k8s describe deployment nginx

  # Describe a service
  vcli k8s describe service nginx-service

  # Describe with namespace
  vcli k8s describe pod nginx-7848d4b86f-9xvzk --namespace=production

  # Describe without events
  vcli k8s describe pod nginx-7848d4b86f-9xvzk --show-events=false

  # Describe node
  vcli k8s describe node worker-node-1

  # Describe with managed fields
  vcli k8s describe deployment nginx --show-managed-fields`,
	RunE: handleK8sDescribe,
}

// handleK8sDescribe handles the describe command execution
func handleK8sDescribe(cmd *cobra.Command, args []string) error {
	// Parse arguments
	if len(args) < 2 {
		return fmt.Errorf("resource type and name are required (e.g., 'pod nginx')")
	}

	kind := args[0]
	name := args[1]

	// Get flags
	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	showEvents, err := cmd.Flags().GetBool("show-events")
	if err != nil {
		return fmt.Errorf("failed to get show-events flag: %w", err)
	}

	showManagedFields, err := cmd.Flags().GetBool("show-managed-fields")
	if err != nil {
		return fmt.Errorf("failed to get show-managed-fields flag: %w", err)
	}

	timeout, err := cmd.Flags().GetDuration("timeout")
	if err != nil {
		return fmt.Errorf("failed to get timeout flag: %w", err)
	}

	// Use namespace from flag if specified, otherwise use default
	if namespace == "" {
		namespace = "default"
	}

	// Get kubeconfig path
	kubeconfigPath, err := cmd.Flags().GetString("kubeconfig")
	if err != nil {
		return fmt.Errorf("failed to get kubeconfig flag: %w", err)
	}

	if kubeconfigPath == "" {
		// Use default kubeconfig path with proper error handling
		kubeconfigPath, err = vcliFs.GetKubeconfigPath()
		if err != nil {
			return fmt.Errorf("failed to get kubeconfig path: %w", err)
		}
		// Check KUBECONFIG env var
		if envPath := os.Getenv("KUBECONFIG"); envPath != "" {
			kubeconfigPath = envPath
		}
	}

	// Create cluster manager
	manager, err := k8s.NewClusterManager(kubeconfigPath)
	if err != nil {
		return fmt.Errorf("failed to create cluster manager: %w", err)
	}

	// Connect to cluster
	if err := manager.Connect(); err != nil {
		return fmt.Errorf("failed to connect to cluster: %w", err)
	}
	defer manager.Disconnect()

	// Prepare describe options
	describeOpts := k8s.NewDescribeOptions()
	describeOpts.ShowEvents = showEvents
	describeOpts.ShowManagedFields = showManagedFields
	describeOpts.Timeout = timeout

	// Describe resource
	result, err := manager.DescribeResource(kind, name, namespace, describeOpts)
	if err != nil {
		return fmt.Errorf("failed to describe %s/%s: %w", kind, name, err)
	}

	// Print description
	fmt.Print(result.Description)

	// Print events
	if showEvents && len(result.Events) > 0 {
		fmt.Print(k8s.FormatEvents(result.Events))
	}

	return nil
}

func init() {
	// Add describe command to k8s
	k8sCmd.AddCommand(k8sDescribeCmd)

	// Flags
	k8sDescribeCmd.Flags().Bool("show-events", true, "Show events related to the resource")
	k8sDescribeCmd.Flags().Bool("show-managed-fields", false, "Show managed fields in description")
	k8sDescribeCmd.Flags().Duration("timeout", 30*time.Second, "Timeout for describe operation")
}
