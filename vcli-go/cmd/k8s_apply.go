package main

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sApplyCmd represents the 'k8s apply' command
var k8sApplyCmd = &cobra.Command{
	Use:   "apply",
	Short: "Apply resources to the cluster",
	Long: `Apply Kubernetes resources from files, directories, or stdin.

The apply command creates or updates resources in the cluster based on YAML or JSON
manifests. It supports kubectl-compatible syntax and behavior.

Examples:
  # Apply a single file
  vcli k8s apply -f deployment.yaml

  # Apply multiple files
  vcli k8s apply -f deployment.yaml -f service.yaml

  # Apply all files in a directory
  vcli k8s apply -f ./manifests/

  # Apply recursively
  vcli k8s apply -f ./manifests/ --recursive

  # Dry-run (client-side)
  vcli k8s apply -f deployment.yaml --dry-run=client

  # Dry-run (server-side)
  vcli k8s apply -f deployment.yaml --dry-run=server

  # Server-side apply
  vcli k8s apply -f deployment.yaml --server-side

  # Force apply (replace resource)
  vcli k8s apply -f deployment.yaml --force

  # Apply with custom namespace
  vcli k8s apply -f deployment.yaml --namespace=production`,
	RunE: handleK8sApply,
}

// handleK8sApply handles the apply command execution
func handleK8sApply(cmd *cobra.Command, args []string) error {
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

	serverSide, err := cmd.Flags().GetBool("server-side")
	if err != nil {
		return fmt.Errorf("failed to get server-side flag: %w", err)
	}

	force, err := cmd.Flags().GetBool("force")
	if err != nil {
		return fmt.Errorf("failed to get force flag: %w", err)
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
	if len(files) == 0 {
		return fmt.Errorf("at least one file or directory must be specified with -f")
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

	// Prepare apply options
	applyOpts := k8s.NewApplyOptions()
	applyOpts.ServerSide = serverSide
	applyOpts.Force = force
	applyOpts.Namespace = namespace
	applyOpts.Timeout = timeout

	// Set dry-run mode
	switch dryRunStr {
	case "none", "":
		applyOpts.DryRun = k8s.DryRunNone
	case "client":
		applyOpts.DryRun = k8s.DryRunClient
	case "server":
		applyOpts.DryRun = k8s.DryRunServer
	default:
		return fmt.Errorf("invalid dry-run value: %s (must be 'none', 'client', or 'server')", dryRunStr)
	}

	// Apply each file/directory
	totalSuccessful := 0
	totalFailed := 0
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
			// Apply directory
			result, err = manager.ApplyDirectory(file, recursive, applyOpts)
		} else {
			// Apply file
			result, err = manager.ApplyFile(file, applyOpts)
		}

		if err != nil {
			fmt.Fprintf(os.Stderr, "Error applying %s: %v\n", file, err)
			totalFailed++
			continue
		}

		// Process results
		totalResources += result.Total
		totalSuccessful += result.Successful
		totalFailed += result.Failed

		// Print individual resource results
		for _, res := range result.Results {
			applyResult, ok := res.(*k8s.ApplyResult)
			if !ok {
				continue
			}

			identifier := k8s.ExtractResourceIdentifier(applyResult.Object)
			action := applyResult.Action

			if applyResult.DryRun {
				fmt.Printf("%s %s (dry run)\n", identifier, action)
			} else {
				fmt.Printf("%s %s\n", identifier, action)
			}

			// Print warnings if any
			for _, warning := range applyResult.Warnings {
				fmt.Fprintf(os.Stderr, "Warning: %s\n", warning)
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
	fmt.Printf("  Successful: %d\n", totalSuccessful)
	fmt.Printf("  Failed: %d\n", totalFailed)

	if totalFailed > 0 {
		return fmt.Errorf("apply completed with %d error(s)", totalFailed)
	}

	return nil
}

func init() {
	// Add apply command to k8s
	k8sCmd.AddCommand(k8sApplyCmd)

	// Flags
	k8sApplyCmd.Flags().StringArrayP("filename", "f", []string{}, "Files or directories to apply (can be specified multiple times)")
	k8sApplyCmd.Flags().BoolP("recursive", "R", false, "Process directories recursively")
	k8sApplyCmd.Flags().String("dry-run", "none", "Dry-run mode: none, client, or server")
	k8sApplyCmd.Flags().Bool("server-side", false, "Use server-side apply")
	k8sApplyCmd.Flags().Bool("force", false, "Force apply (replace resource)")
	k8sApplyCmd.Flags().Duration("timeout", 30*time.Second, "Timeout for apply operation")

	// Mark required flags
	k8sApplyCmd.MarkFlagRequired("filename")
}
