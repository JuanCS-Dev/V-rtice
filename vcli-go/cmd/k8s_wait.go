package cmd

import (
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"
	vcliFs "github.com/verticedev/vcli-go/internal/fs"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sWaitCmd represents the 'k8s wait' command
var k8sWaitCmd = &cobra.Command{
	Use:   "wait RESOURCE NAME [flags]",
	Short: "Wait for a resource to reach a specific condition",
	Long: `Wait for a Kubernetes resource to reach a specific condition.

The wait command blocks until the specified resource reaches the desired state
or the timeout is reached. This is useful for scripting and automation.

Supported conditions:
  - condition=Ready: Wait for resource to be ready
  - condition=Available: Wait for deployment to be available
  - delete: Wait for resource deletion

Examples:
  # Wait for pod to be ready
  vcli k8s wait pod nginx --for=condition=Ready --timeout=60s

  # Wait for deployment to be available
  vcli k8s wait deployment nginx --for=condition=Available --timeout=5m

  # Wait for pod deletion
  vcli k8s wait pod nginx --for=delete --timeout=60s

  # Wait for multiple pods (by selector)
  vcli k8s wait pods --selector=app=nginx --for=condition=Ready --timeout=5m

  # Wait in specific namespace
  vcli k8s wait pod nginx --for=condition=Ready --namespace=production --timeout=60s`,
	RunE: handleK8sWait,
}

// handleK8sWait handles the wait command execution
func handleK8sWait(cmd *cobra.Command, args []string) error {
	// Validate arguments
	if len(args) < 1 {
		return fmt.Errorf("resource type is required")
	}

	kind := args[0]
	var name string

	// If name is provided (single resource wait)
	if len(args) >= 2 {
		name = args[1]
	}

	// Get flags
	forCondition, err := cmd.Flags().GetString("for")
	if err != nil {
		return fmt.Errorf("failed to get for flag: %w", err)
	}

	selector, err := cmd.Flags().GetString("selector")
	if err != nil {
		return fmt.Errorf("failed to get selector flag: %w", err)
	}

	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	timeout, err := cmd.Flags().GetDuration("timeout")
	if err != nil {
		return fmt.Errorf("failed to get timeout flag: %w", err)
	}

	// Validate inputs
	if forCondition == "" {
		return fmt.Errorf("--for condition is required")
	}

	if name == "" && selector == "" {
		return fmt.Errorf("either resource name or --selector must be specified")
	}

	// Parse condition string to WaitCondition enum
	condition, err := parseWaitCondition(forCondition)
	if err != nil {
		return fmt.Errorf("invalid condition: %w", err)
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

	// Execute wait
	var result *k8s.WaitResult

	if name != "" {
		// Wait for single resource
		fmt.Printf("Waiting for %s/%s to meet condition: %s...\n", kind, name, forCondition)
		result, err = manager.WaitForResource(kind, name, namespace, condition, timeout)
	} else {
		// Wait for multiple resources by selector
		fmt.Printf("Waiting for %s (selector: %s) to meet condition: %s...\n", kind, selector, forCondition)
		result, err = manager.WaitForConditionWithSelector(kind, namespace, selector, condition, timeout)
	}

	if err != nil {
		if result != nil && result.TimedOut {
			return fmt.Errorf("timeout after %v: %s", result.Duration, result.Message)
		}
		return fmt.Errorf("wait failed: %w", err)
	}

	// Print result
	if result.Success {
		fmt.Printf("✓ %s (waited %v)\n", result.Message, result.Duration)
		return nil
	}

	return fmt.Errorf("wait failed: %s (waited %v)", result.Message, result.Duration)
}

// parseWaitCondition parses a --for condition string into a WaitCondition enum
func parseWaitCondition(forStr string) (k8s.WaitCondition, error) {
	// Handle different formats:
	// - "delete"
	// - "condition=Ready"
	// - "condition=Available"

	forStr = strings.TrimSpace(forStr)

	if forStr == "delete" {
		return k8s.WaitConditionDeleted, nil
	}

	if strings.HasPrefix(forStr, "condition=") {
		condValue := strings.TrimPrefix(forStr, "condition=")
		switch condValue {
		case "Ready":
			return k8s.WaitConditionReady, nil
		case "Available":
			return k8s.WaitConditionAvailable, nil
		default:
			return "", fmt.Errorf("unsupported condition: %s (supported: Ready, Available)", condValue)
		}
	}

	return "", fmt.Errorf("invalid format: %s (use 'delete' or 'condition=Ready' or 'condition=Available')", forStr)
}

func init() {
	// Add wait command to k8s
	k8sCmd.AddCommand(k8sWaitCmd)

	// Flags
	k8sWaitCmd.Flags().String("for", "", "Condition to wait for (e.g., condition=Ready, condition=Available, delete)")
	k8sWaitCmd.Flags().StringP("selector", "l", "", "Label selector to filter resources")
	k8sWaitCmd.Flags().Duration("timeout", 5*time.Minute, "Timeout for wait operation")

	// Mark required flags
	k8sWaitCmd.MarkFlagRequired("for")
}
