package main

import (
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// k8sDeleteCmd represents the 'k8s delete' command
var k8sDeleteCmd = &cobra.Command{
	Use:   "delete",
	Short: "Delete resources from the cluster",
	Long: `Delete Kubernetes resources from files, directories, or by name/selector.

The delete command removes resources from the cluster. It supports kubectl-compatible
syntax and behavior.

Examples:
  # Delete from file
  vcli k8s delete -f deployment.yaml

  # Delete multiple files
  vcli k8s delete -f deployment.yaml -f service.yaml

  # Delete all resources in a directory
  vcli k8s delete -f ./manifests/

  # Delete recursively
  vcli k8s delete -f ./manifests/ --recursive

  # Delete by resource name
  vcli k8s delete deployment nginx --namespace=default

  # Delete with grace period
  vcli k8s delete pod nginx --grace-period=30

  # Delete with cascade policy
  vcli k8s delete deployment nginx --cascade=foreground

  # Force delete
  vcli k8s delete pod nginx --force --grace-period=0

  # Dry-run
  vcli k8s delete -f deployment.yaml --dry-run=client

  # Delete with wait
  vcli k8s delete deployment nginx --wait

  # Delete with label selector (batch operation)
  vcli k8s delete pods --selector app=nginx
  vcli k8s delete deployments --selector tier=frontend,env=prod

  # Delete with field selector
  vcli k8s delete pods --field-selector status.phase=Failed

  # Combine selectors
  vcli k8s delete pods --selector app=nginx --field-selector status.phase=Running`,
	RunE: handleK8sDelete,
}

// handleK8sDelete handles the delete command execution
func handleK8sDelete(cmd *cobra.Command, args []string) error {
	// Get flags
	files, err := cmd.Flags().GetStringArray("filename")
	if err != nil {
		return fmt.Errorf("failed to get filename flag: %w", err)
	}

	recursive, err := cmd.Flags().GetBool("recursive")
	if err != nil {
		return fmt.Errorf("failed to get recursive flag: %w", err)
	}

	dryRunStr, err := cmd.Flags().GetString("dry-run")
	if err != nil {
		return fmt.Errorf("failed to get dry-run flag: %w", err)
	}

	force, err := cmd.Flags().GetBool("force")
	if err != nil {
		return fmt.Errorf("failed to get force flag: %w", err)
	}

	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	gracePeriod, err := cmd.Flags().GetInt64("grace-period")
	if err != nil {
		return fmt.Errorf("failed to get grace-period flag: %w", err)
	}

	cascade, err := cmd.Flags().GetString("cascade")
	if err != nil {
		return fmt.Errorf("failed to get cascade flag: %w", err)
	}

	wait, err := cmd.Flags().GetBool("wait")
	if err != nil {
		return fmt.Errorf("failed to get wait flag: %w", err)
	}

	timeout, err := cmd.Flags().GetDuration("timeout")
	if err != nil {
		return fmt.Errorf("failed to get timeout flag: %w", err)
	}

	// Get selector flags
	labelSelector, err := cmd.Flags().GetString("selector")
	if err != nil {
		return fmt.Errorf("failed to get selector flag: %w", err)
	}

	fieldSelector, err := cmd.Flags().GetString("field-selector")
	if err != nil {
		return fmt.Errorf("failed to get field-selector flag: %w", err)
	}

	// Validate inputs
	hasSelector := labelSelector != "" || fieldSelector != ""
	if len(files) == 0 && len(args) < 1 && !hasSelector {
		return fmt.Errorf("either file (-f), resource type and name, or selector must be specified")
	}

	// When selector is used, only resource type is required (not name)
	if hasSelector && len(args) < 1 {
		return fmt.Errorf("resource type is required when using selector")
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

	// Prepare delete options
	deleteOpts := k8s.NewDeleteOptions()
	deleteOpts.Force = force
	deleteOpts.Wait = wait
	deleteOpts.Timeout = timeout
	deleteOpts.WaitTimeout = timeout

	// Set grace period
	if gracePeriod >= 0 {
		deleteOpts.GracePeriodSeconds = &gracePeriod
	}

	// Set cascade policy
	if cascade != "" {
		deleteOpts.PropagationPolicy = k8s.PropagationPolicy(cascade)
	}

	// Set dry-run mode
	switch dryRunStr {
	case "none", "":
		deleteOpts.DryRun = k8s.DryRunNone
	case "client":
		deleteOpts.DryRun = k8s.DryRunClient
	case "server":
		deleteOpts.DryRun = k8s.DryRunServer
	default:
		return fmt.Errorf("invalid dry-run value: %s (must be 'none', 'client', or 'server')", dryRunStr)
	}

	// Handle delete by file, selector, or name
	if len(files) > 0 {
		return handleDeleteByFile(manager, files, recursive, namespace, deleteOpts)
	}

	// Handle delete by selector (batch operation)
	if hasSelector {
		kind := args[0]
		return handleDeleteBySelector(manager, kind, labelSelector, fieldSelector, namespace, deleteOpts)
	}

	return handleDeleteByName(manager, args, namespace, deleteOpts)
}

// handleDeleteByFile handles deletion from files
func handleDeleteByFile(manager *k8s.ClusterManager, files []string, recursive bool, namespace string, opts *k8s.DeleteOptions) error {
	totalSuccessful := 0
	totalFailed := 0
	totalSkipped := 0
	totalResources := 0

	for _, file := range files {
		// Check if file or directory
		info, err := os.Stat(file)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: failed to access %s: %v\n", file, err)
			totalFailed++
			continue
		}

		var result *k8s.BatchResult

		if info.IsDir() {
			// Delete directory
			result, err = manager.DeleteDirectory(file, recursive, opts)
		} else {
			// Delete file
			result, err = manager.DeleteFile(file, opts)
		}

		if err != nil {
			fmt.Fprintf(os.Stderr, "Error deleting %s: %v\n", file, err)
			totalFailed++
			continue
		}

		// Process results
		totalResources += result.Total
		totalSuccessful += result.Successful
		totalFailed += result.Failed
		totalSkipped += result.Skipped

		// Print individual resource results
		for _, res := range result.Results {
			deleteResult, ok := res.(*k8s.DeleteResult)
			if !ok {
				continue
			}

			identifier := fmt.Sprintf("%s/%s", deleteResult.Kind, deleteResult.Name)
			if deleteResult.Namespace != "" {
				identifier = fmt.Sprintf("%s/%s/%s", deleteResult.Kind, deleteResult.Namespace, deleteResult.Name)
			}

			switch deleteResult.Status {
			case k8s.DeleteStatusDeleted:
				if deleteResult.DryRun {
					fmt.Printf("%s deleted (dry run)\n", identifier)
				} else {
					fmt.Printf("%s deleted\n", identifier)
				}
			case k8s.DeleteStatusNotFound:
				fmt.Printf("%s not found (skipped)\n", identifier)
			case k8s.DeleteStatusFailed:
				fmt.Fprintf(os.Stderr, "%s failed: %s\n", identifier, deleteResult.Message)
			}
		}

		// Print errors
		for _, err := range result.Errors {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		}
	}

	// Print summary
	fmt.Printf("\n")
	fmt.Printf("Summary:\n")
	fmt.Printf("  Total resources: %d\n", totalResources)
	fmt.Printf("  Deleted: %d\n", totalSuccessful)
	fmt.Printf("  Skipped: %d\n", totalSkipped)
	fmt.Printf("  Failed: %d\n", totalFailed)

	if totalFailed > 0 {
		return fmt.Errorf("delete completed with %d error(s)", totalFailed)
	}

	return nil
}

// handleDeleteByName handles deletion by resource type and name
// handleDeleteBySelector handles batch deletion with label/field selectors
func handleDeleteBySelector(manager *k8s.ClusterManager, kind, labelSelector, fieldSelector, namespace string, opts *k8s.DeleteOptions) error {
	// Use namespace from flag if specified, otherwise use default
	if namespace == "" {
		namespace = "default"
	}

	// List resources matching selector
	listOpts := metav1.ListOptions{}
	if labelSelector != "" {
		listOpts.LabelSelector = labelSelector
	}
	if fieldSelector != "" {
		listOpts.FieldSelector = fieldSelector
	}

	fmt.Printf("Deleting %ss in namespace %s with selector: ", kind, namespace)
	if labelSelector != "" {
		fmt.Printf("labels=%s ", labelSelector)
	}
	if fieldSelector != "" {
		fmt.Printf("fields=%s ", fieldSelector)
	}
	fmt.Println()

	// Get matching resources
	var resourceNames []string

	switch strings.ToLower(kind) {
	case "pod", "pods", "po":
		pods, listErr := manager.Clientset().CoreV1().Pods(namespace).List(context.Background(), listOpts)
		if listErr != nil {
			return fmt.Errorf("failed to list pods: %w", listErr)
		}
		for _, pod := range pods.Items {
			resourceNames = append(resourceNames, pod.Name)
		}
	case "deployment", "deployments", "deploy":
		deployments, listErr := manager.Clientset().AppsV1().Deployments(namespace).List(context.Background(), listOpts)
		if listErr != nil {
			return fmt.Errorf("failed to list deployments: %w", listErr)
		}
		for _, deploy := range deployments.Items {
			resourceNames = append(resourceNames, deploy.Name)
		}
	case "service", "services", "svc":
		services, listErr := manager.Clientset().CoreV1().Services(namespace).List(context.Background(), listOpts)
		if listErr != nil {
			return fmt.Errorf("failed to list services: %w", listErr)
		}
		for _, svc := range services.Items {
			resourceNames = append(resourceNames, svc.Name)
		}
	case "configmap", "configmaps", "cm":
		configmaps, listErr := manager.Clientset().CoreV1().ConfigMaps(namespace).List(context.Background(), listOpts)
		if listErr != nil {
			return fmt.Errorf("failed to list configmaps: %w", listErr)
		}
		for _, cm := range configmaps.Items {
			resourceNames = append(resourceNames, cm.Name)
		}
	default:
		return fmt.Errorf("batch delete not yet supported for resource type: %s", kind)
	}

	if len(resourceNames) == 0 {
		fmt.Println("No resources found matching selector")
		return nil
	}

	fmt.Printf("Found %d resources to delete\n", len(resourceNames))

	// Batch delete
	succeeded := 0
	failed := 0

	for _, name := range resourceNames {
		result, deleteErr := manager.DeleteByName(kind, name, namespace, opts)
		if deleteErr != nil || result.Status == k8s.DeleteStatusFailed {
			fmt.Printf("✗ %s/%s: %v\n", kind, name, deleteErr)
			failed++
		} else {
			if result.DryRun {
				fmt.Printf("✓ %s/%s (dry run)\n", kind, name)
			} else {
				fmt.Printf("✓ %s/%s\n", kind, name)
			}
			succeeded++
		}
	}

	fmt.Printf("\nBatch delete complete: %d succeeded, %d failed\n", succeeded, failed)

	if failed > 0 {
		return fmt.Errorf("some deletions failed")
	}

	return nil
}

func handleDeleteByName(manager *k8s.ClusterManager, args []string, namespace string, opts *k8s.DeleteOptions) error {
	if len(args) < 2 {
		return fmt.Errorf("resource type and name are required")
	}

	kind := args[0]
	name := args[1]

	// Use namespace from flag if specified, otherwise use default
	if namespace == "" {
		namespace = "default"
	}

	result, err := manager.DeleteByName(kind, name, namespace, opts)
	if err != nil {
		return fmt.Errorf("failed to delete %s/%s: %w", kind, name, err)
	}

	identifier := fmt.Sprintf("%s/%s", kind, name)
	if namespace != "" {
		identifier = fmt.Sprintf("%s/%s/%s", kind, namespace, name)
	}

	switch result.Status {
	case k8s.DeleteStatusDeleted:
		if result.DryRun {
			fmt.Printf("%s deleted (dry run)\n", identifier)
		} else {
			fmt.Printf("%s deleted\n", identifier)
			if result.Duration > 0 {
				fmt.Printf("Duration: %v\n", result.Duration)
			}
		}
	case k8s.DeleteStatusNotFound:
		fmt.Printf("%s not found\n", identifier)
	case k8s.DeleteStatusFailed:
		return fmt.Errorf("%s: %s", identifier, result.Message)
	}

	return nil
}

func init() {
	// Add delete command to k8s
	k8sCmd.AddCommand(k8sDeleteCmd)

	// Flags
	k8sDeleteCmd.Flags().StringArrayP("filename", "f", []string{}, "Files or directories to delete (can be specified multiple times)")
	k8sDeleteCmd.Flags().BoolP("recursive", "R", false, "Process directories recursively")
	k8sDeleteCmd.Flags().String("dry-run", "none", "Dry-run mode: none, client, or server")
	k8sDeleteCmd.Flags().Bool("force", false, "Force delete (immediate deletion)")
	k8sDeleteCmd.Flags().Int64("grace-period", -1, "Grace period in seconds before deletion (-1 = default)")
	k8sDeleteCmd.Flags().String("cascade", "background", "Cascade deletion policy: background, foreground, or orphan")
	k8sDeleteCmd.Flags().Bool("wait", false, "Wait for deletion to complete")
	k8sDeleteCmd.Flags().Duration("timeout", 30*time.Second, "Timeout for delete operation")

	// Namespace flag
	k8sDeleteCmd.Flags().StringP("namespace", "n", "", "Kubernetes namespace (default: default)")

	// Batch operation flags
	k8sDeleteCmd.Flags().StringP("selector", "l", "", "Label selector for batch deletion (e.g., app=nginx,tier=frontend)")
	k8sDeleteCmd.Flags().String("field-selector", "", "Field selector for batch deletion (e.g., status.phase=Failed)")
}
