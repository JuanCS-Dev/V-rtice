package main

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sScaleCmd represents the 'k8s scale' command
var k8sScaleCmd = &cobra.Command{
	Use:   "scale",
	Short: "Scale resources in the cluster",
	Long: `Scale Kubernetes resources (Deployment, StatefulSet, ReplicaSet).

The scale command changes the number of replicas for scalable resources.
It supports kubectl-compatible syntax and behavior.

Examples:
  # Scale a deployment
  vcli k8s scale deployment nginx --replicas=3

  # Scale with namespace
  vcli k8s scale deployment nginx --replicas=5 --namespace=production

  # Scale and wait for completion
  vcli k8s scale deployment nginx --replicas=10 --wait

  # Scale with custom timeout
  vcli k8s scale statefulset database --replicas=3 --wait --timeout=5m

  # Dry-run
  vcli k8s scale deployment nginx --replicas=5 --dry-run=client

  # Get current scale
  vcli k8s scale deployment nginx --current-replicas`,
	RunE: handleK8sScale,
}

// handleK8sScale handles the scale command execution
func handleK8sScale(cmd *cobra.Command, args []string) error {
	// Validate args
	if len(args) < 2 {
		return fmt.Errorf("resource type and name are required (e.g., 'deployment nginx')")
	}

	kind := args[0]
	name := args[1]

	// Get flags
	replicas, err := cmd.Flags().GetInt32("replicas")
	if err != nil {
		return fmt.Errorf("failed to get replicas flag: %w", err)
	}

	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	wait, err := cmd.Flags().GetBool("wait")
	if err != nil {
		return fmt.Errorf("failed to get wait flag: %w", err)
	}

	timeout, err := cmd.Flags().GetDuration("timeout")
	if err != nil {
		return fmt.Errorf("failed to get timeout flag: %w", err)
	}

	dryRunStr, err := cmd.Flags().GetString("dry-run")
	if err != nil {
		return fmt.Errorf("failed to get dry-run flag: %w", err)
	}

	currentOnly, err := cmd.Flags().GetBool("current-replicas")
	if err != nil {
		return fmt.Errorf("failed to get current-replicas flag: %w", err)
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
		// Use default kubeconfig path
		home, err := os.UserHomeDir()
		if err == nil {
			kubeconfigPath = home + "/.kube/config"
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

	// Handle current-replicas flag (get scale info only)
	if currentOnly {
		return handleGetScale(manager, kind, name, namespace)
	}

	// Validate replicas flag
	if replicas < 0 {
		return fmt.Errorf("replicas must be specified and non-negative")
	}

	// Prepare scale options
	scaleOpts := k8s.NewScaleOptions()
	scaleOpts.Replicas = replicas
	scaleOpts.Wait = wait
	scaleOpts.Timeout = timeout
	scaleOpts.WaitTimeout = timeout

	// Set dry-run mode
	switch dryRunStr {
	case "none", "":
		scaleOpts.DryRun = k8s.DryRunNone
	case "client":
		scaleOpts.DryRun = k8s.DryRunClient
	case "server":
		scaleOpts.DryRun = k8s.DryRunServer
	default:
		return fmt.Errorf("invalid dry-run value: %s (must be 'none', 'client', or 'server')", dryRunStr)
	}

	// Scale the resource
	result, err := manager.ScaleResource(kind, name, namespace, scaleOpts)
	if err != nil {
		return fmt.Errorf("failed to scale %s/%s: %w", kind, name, err)
	}

	// Print result
	identifier := fmt.Sprintf("%s/%s", kind, name)
	if namespace != "" {
		identifier = fmt.Sprintf("%s/%s/%s", kind, namespace, name)
	}

	if result.DryRun {
		fmt.Printf("%s scaled to %d replicas (dry run)\n", identifier, result.DesiredReplicas)
	} else {
		switch result.Status {
		case k8s.ScaleStatusScaling:
			fmt.Printf("%s scaling from %d to %d replicas\n", identifier, result.PreviousReplicas, result.DesiredReplicas)
		case k8s.ScaleStatusScaled:
			fmt.Printf("%s scaled from %d to %d replicas\n", identifier, result.PreviousReplicas, result.DesiredReplicas)
			if result.Duration > 0 {
				fmt.Printf("Duration: %v\n", result.Duration)
			}
		case k8s.ScaleStatusFailed:
			return fmt.Errorf("%s: %s", identifier, result.Message)
		}
	}

	return nil
}

// handleGetScale handles getting current scale information
func handleGetScale(manager *k8s.ClusterManager, kind, name, namespace string) error {
	scaleInfo, err := manager.GetScale(kind, name, namespace)
	if err != nil {
		return fmt.Errorf("failed to get scale: %w", err)
	}

	identifier := fmt.Sprintf("%s/%s", kind, name)
	if namespace != "" {
		identifier = fmt.Sprintf("%s/%s/%s", kind, namespace, name)
	}

	fmt.Printf("Scale information for %s:\n", identifier)
	fmt.Printf("  Desired replicas: %d\n", scaleInfo.DesiredReplicas)
	fmt.Printf("  Current replicas: %d\n", scaleInfo.CurrentReplicas)
	if scaleInfo.Selector != "" {
		fmt.Printf("  Selector: %s\n", scaleInfo.Selector)
	}

	return nil
}

func init() {
	// Add scale command to k8s
	k8sCmd.AddCommand(k8sScaleCmd)

	// Flags
	k8sScaleCmd.Flags().Int32("replicas", -1, "Number of replicas to scale to (required)")
	k8sScaleCmd.Flags().Bool("wait", false, "Wait for scaling to complete")
	k8sScaleCmd.Flags().Duration("timeout", 5*time.Minute, "Timeout for scale operation")
	k8sScaleCmd.Flags().String("dry-run", "none", "Dry-run mode: none, client, or server")
	k8sScaleCmd.Flags().Bool("current-replicas", false, "Show current replica count only (no scaling)")
}
