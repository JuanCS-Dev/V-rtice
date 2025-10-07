package main

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

// k8sWatchCmd represents the 'k8s watch' command
var k8sWatchCmd = &cobra.Command{
	Use:   "watch",
	Short: "Watch resources for changes",
	Long: `Watch Kubernetes resources for changes in real-time.

The watch command monitors resources and displays changes as they occur.
It supports kubectl-compatible syntax and behavior.

Examples:
  # Watch pods
  vcli k8s watch pods

  # Watch pods in specific namespace
  vcli k8s watch pods --namespace=production

  # Watch pods with label selector
  vcli k8s watch pods --selector=app=nginx

  # Watch deployments
  vcli k8s watch deployments

  # Watch all resource types
  vcli k8s watch pods,deployments,services

  # Watch with timeout
  vcli k8s watch pods --timeout=5m`,
	RunE: handleK8sWatch,
}

// handleK8sWatch handles the watch command execution
func handleK8sWatch(cmd *cobra.Command, args []string) error {
	// Parse arguments
	if len(args) < 1 {
		return fmt.Errorf("resource type is required (e.g., 'pods', 'deployments')")
	}

	resourceTypes := args[0]

	// Get flags
	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	selector, err := cmd.Flags().GetString("selector")
	if err != nil {
		return fmt.Errorf("failed to get selector flag: %w", err)
	}

	fieldSelector, err := cmd.Flags().GetString("field-selector")
	if err != nil {
		return fmt.Errorf("failed to get field-selector flag: %w", err)
	}

	timeout, err := cmd.Flags().GetDuration("timeout")
	if err != nil {
		return fmt.Errorf("failed to get timeout flag: %w", err)
	}

	outputFormat, err := cmd.Flags().GetString("output")
	if err != nil {
		return fmt.Errorf("failed to get output flag: %w", err)
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

	// Prepare watch options
	watchOpts := k8s.NewWatchOptions()
	if timeout > 0 {
		watchOpts.Timeout = timeout
	}

	// Parse selector
	if selector != "" {
		labels := make(map[string]string)
		// Simple parsing: app=nginx,tier=frontend
		for _, pair := range splitSelector(selector) {
			parts := splitPair(pair, '=')
			if len(parts) == 2 {
				labels[parts[0]] = parts[1]
			}
		}
		watchOpts.Labels = labels
	}

	if fieldSelector != "" {
		watchOpts.FieldSelector = fieldSelector
	}

	// Determine resource kind
	kind := normalizeResourceType(resourceTypes)

	fmt.Printf("Watching %s in namespace '%s'...\n", kind, namespace)
	fmt.Println("Press Ctrl+C to stop")

	// Watch with handler
	handler := func(event *k8s.WatchEvent) error {
		obj, ok := event.Object.(*unstructured.Unstructured)
		if !ok {
			return nil
		}

		timestamp := time.Now().Format("15:04:05")

		switch outputFormat {
		case "name":
			fmt.Printf("[%s] %s: %s/%s\n",
				timestamp,
				event.Type,
				obj.GetNamespace(),
				obj.GetName())
		case "wide":
			fmt.Printf("[%s] %s: %s/%s/%s (ResourceVersion: %s)\n",
				timestamp,
				event.Type,
				obj.GetKind(),
				obj.GetNamespace(),
				obj.GetName(),
				obj.GetResourceVersion())
		default: // default format
			fmt.Printf("[%s] %s: %s/%s\n",
				timestamp,
				event.Type,
				obj.GetNamespace(),
				obj.GetName())
		}

		return nil
	}

	return manager.WatchWithHandler(kind, namespace, handler, watchOpts)
}

// normalizeResourceType converts plural resource type to Kind
func normalizeResourceType(resourceType string) string {
	switch resourceType {
	case "pods", "pod", "po":
		return "Pod"
	case "deployments", "deployment", "deploy":
		return "Deployment"
	case "services", "service", "svc":
		return "Service"
	case "nodes", "node", "no":
		return "Node"
	case "namespaces", "namespace", "ns":
		return "Namespace"
	case "configmaps", "configmap", "cm":
		return "ConfigMap"
	case "secrets", "secret":
		return "Secret"
	case "jobs", "job":
		return "Job"
	case "cronjobs", "cronjob", "cj":
		return "CronJob"
	default:
		// Capitalize first letter
		if len(resourceType) > 0 {
			return string(resourceType[0]-32) + resourceType[1:]
		}
		return resourceType
	}
}

// splitSelector splits selector string by comma
func splitSelector(selector string) []string {
	result := []string{}
	current := ""
	for _, c := range selector {
		if c == ',' {
			if current != "" {
				result = append(result, current)
				current = ""
			}
		} else {
			current += string(c)
		}
	}
	if current != "" {
		result = append(result, current)
	}
	return result
}

// splitPair splits a string by delimiter
func splitPair(s string, delim rune) []string {
	result := []string{}
	current := ""
	for _, c := range s {
		if c == delim {
			result = append(result, current)
			current = ""
		} else {
			current += string(c)
		}
	}
	if current != "" {
		result = append(result, current)
	}
	return result
}

func init() {
	// Add watch command to k8s
	k8sCmd.AddCommand(k8sWatchCmd)

	// Flags
	k8sWatchCmd.Flags().StringP("selector", "l", "", "Label selector to filter resources")
	k8sWatchCmd.Flags().String("field-selector", "", "Field selector to filter resources")
	k8sWatchCmd.Flags().Duration("timeout", 0, "Watch timeout (0 = no timeout)")
	k8sWatchCmd.Flags().StringP("output", "o", "default", "Output format: default, name, wide")
}
