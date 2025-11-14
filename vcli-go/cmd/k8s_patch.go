package cmd

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	vcliFs "github.com/verticedev/vcli-go/internal/fs"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sPatchCmd represents the 'k8s patch' command
var k8sPatchCmd = &cobra.Command{
	Use:   "patch",
	Short: "Patch resources in the cluster",
	Long: `Patch Kubernetes resources using various patch strategies.

The patch command updates resources using JSON Patch, Merge Patch, Strategic Merge Patch,
or Server-Side Apply. It supports kubectl-compatible syntax and behavior.

Patch Types:
  json       - JSON Patch (RFC 6902) for precise modifications
  merge      - JSON Merge Patch (RFC 7386) for simple updates
  strategic  - Strategic Merge Patch (Kubernetes-specific, default)
  apply      - Server-Side Apply

Examples:
  # Patch using JSON Patch
  vcli k8s patch deployment nginx --type=json -p '[{"op":"replace","path":"/spec/replicas","value":5}]'

  # Patch using Merge Patch
  vcli k8s patch deployment nginx --type=merge -p '{"spec":{"replicas":3}}'

  # Patch using Strategic Merge Patch (default)
  vcli k8s patch deployment nginx -p '{"spec":{"replicas":3}}'

  # Patch from file
  vcli k8s patch -f deployment.yaml --type=merge -p '{"spec":{"replicas":5}}'

  # Patch with namespace
  vcli k8s patch deployment nginx --namespace=production -p '{"spec":{"replicas":10}}'

  # Dry-run
  vcli k8s patch deployment nginx --dry-run=client -p '{"spec":{"replicas":5}}'

  # Patch from file with inline patch
  vcli k8s patch -f patch.json --type=json`,
	RunE: handleK8sPatch,
}

// handleK8sPatch handles the patch command execution
func handleK8sPatch(cmd *cobra.Command, args []string) error {
	// Get flags
	files, err := cmd.Flags().GetStringArray("filename")
	if err != nil {
		return fmt.Errorf("failed to get filename flag: %w", err)
	}

	patchStr, err := cmd.Flags().GetString("patch")
	if err != nil {
		return fmt.Errorf("failed to get patch flag: %w", err)
	}

	patchTypeStr, err := cmd.Flags().GetString("type")
	if err != nil {
		return fmt.Errorf("failed to get type flag: %w", err)
	}

	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	dryRunStr, err := cmd.Flags().GetString("dry-run")
	if err != nil {
		return fmt.Errorf("failed to get dry-run flag: %w", err)
	}

	force, err := cmd.Flags().GetBool("force")
	if err != nil {
		return fmt.Errorf("failed to get force flag: %w", err)
	}

	timeout, err := cmd.Flags().GetDuration("timeout")
	if err != nil {
		return fmt.Errorf("failed to get timeout flag: %w", err)
	}

	// Validate inputs
	if len(files) == 0 && len(args) < 2 {
		return fmt.Errorf("either file (-f) or resource type and name must be specified")
	}

	if patchStr == "" {
		return fmt.Errorf("patch data must be specified with -p or --patch")
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

	// Prepare patch options
	patchOpts := k8s.NewPatchOptions()
	patchOpts.Patch = []byte(patchStr)
	patchOpts.Force = force
	patchOpts.Timeout = timeout

	// Set patch type
	switch patchTypeStr {
	case "json":
		patchOpts.PatchType = k8s.PatchTypeJSON
	case "merge":
		patchOpts.PatchType = k8s.PatchTypeMerge
	case "strategic":
		patchOpts.PatchType = k8s.PatchTypeStrategic
	case "apply":
		patchOpts.PatchType = k8s.PatchTypeApply
	default:
		return fmt.Errorf("invalid patch type: %s (must be 'json', 'merge', 'strategic', or 'apply')", patchTypeStr)
	}

	// Set dry-run mode
	switch dryRunStr {
	case "none", "":
		patchOpts.DryRun = k8s.DryRunNone
	case "client":
		patchOpts.DryRun = k8s.DryRunClient
	case "server":
		patchOpts.DryRun = k8s.DryRunServer
	default:
		return fmt.Errorf("invalid dry-run value: %s (must be 'none', 'client', or 'server')", dryRunStr)
	}

	// Validate patch
	if err := k8s.ValidatePatch(patchOpts.Patch, patchOpts.PatchType); err != nil {
		return fmt.Errorf("patch validation failed: %w", err)
	}

	// Handle patch by file or by name
	if len(files) > 0 {
		return handlePatchByFile(manager, files, patchOpts)
	}

	return handlePatchByName(manager, args, namespace, patchOpts)
}

// handlePatchByFile handles patching from files
func handlePatchByFile(manager *k8s.ClusterManager, files []string, opts *k8s.PatchOptions) error {
	totalSuccessful := 0
	totalFailed := 0
	totalResources := 0

	for _, file := range files {
		result, err := manager.PatchFile(file, opts)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error patching %s: %v\n", file, err)
			totalFailed++
			continue
		}

		// Process results
		totalResources += result.Total
		totalSuccessful += result.Successful
		totalFailed += result.Failed

		// Print individual resource results
		for _, res := range result.Results {
			patchResult, ok := res.(*k8s.PatchResult)
			if !ok {
				continue
			}

			identifier := k8s.ExtractResourceIdentifier(patchResult.Object)

			if patchResult.DryRun {
				fmt.Printf("%s patched (dry run)\n", identifier)
			} else {
				fmt.Printf("%s patched\n", identifier)
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
	fmt.Printf("  Patched: %d\n", totalSuccessful)
	fmt.Printf("  Failed: %d\n", totalFailed)

	if totalFailed > 0 {
		return fmt.Errorf("patch completed with %d error(s)", totalFailed)
	}

	return nil
}

// handlePatchByName handles patching by resource type and name
func handlePatchByName(manager *k8s.ClusterManager, args []string, namespace string, opts *k8s.PatchOptions) error {
	if len(args) < 2 {
		return fmt.Errorf("resource type and name are required")
	}

	kind := args[0]
	name := args[1]

	// Use namespace from flag if specified, otherwise use default
	if namespace == "" {
		namespace = "default"
	}

	result, err := manager.PatchByName(kind, name, namespace, opts)
	if err != nil {
		return fmt.Errorf("failed to patch %s/%s: %w", kind, name, err)
	}

	identifier := k8s.ExtractResourceIdentifier(result.Object)

	if result.DryRun {
		fmt.Printf("%s patched (dry run)\n", identifier)
	} else {
		fmt.Printf("%s patched\n", identifier)
		if result.Duration > 0 {
			fmt.Printf("Duration: %v\n", result.Duration)
		}
	}

	return nil
}

func init() {
	// Add patch command to k8s
	k8sCmd.AddCommand(k8sPatchCmd)

	// Flags
	k8sPatchCmd.Flags().StringArrayP("filename", "f", []string{}, "Files to patch (can be specified multiple times)")
	k8sPatchCmd.Flags().StringP("patch", "p", "", "Patch data in JSON format (required)")
	k8sPatchCmd.Flags().String("type", "strategic", "Patch type: json, merge, strategic, or apply")
	k8sPatchCmd.Flags().String("dry-run", "none", "Dry-run mode: none, client, or server")
	k8sPatchCmd.Flags().Bool("force", false, "Force patch")
	k8sPatchCmd.Flags().Duration("timeout", 30*time.Second, "Timeout for patch operation")

	// Mark required flags
	k8sPatchCmd.MarkFlagRequired("patch")
}
