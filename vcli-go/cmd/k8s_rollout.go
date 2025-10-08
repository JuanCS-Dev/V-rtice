package main

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sRolloutCmd represents the 'k8s rollout' command
var k8sRolloutCmd = &cobra.Command{
	Use:   "rollout SUBCOMMAND",
	Short: "Manage rollout of resources",
	Long: `Manage the rollout of Kubernetes resources.

The rollout command allows you to manage rollouts for deployments, statefulsets, and daemonsets.
Supported operations include viewing status, history, undoing, restarting, and pausing/resuming rollouts.

Available subcommands:
  status    Show rollout status
  history   View rollout history
  undo      Rollback to a previous revision
  restart   Restart a resource
  pause     Pause a rollout (deployments only)
  resume    Resume a paused rollout (deployments only)

Examples:
  # Check rollout status
  vcli k8s rollout status deployment/nginx

  # View rollout history
  vcli k8s rollout history deployment/nginx

  # Rollback to previous revision
  vcli k8s rollout undo deployment/nginx

  # Restart a deployment
  vcli k8s rollout restart deployment/nginx`,
}

// k8sRolloutStatusCmd represents the 'k8s rollout status' command
var k8sRolloutStatusCmd = &cobra.Command{
	Use:   "status (RESOURCE/NAME | RESOURCE NAME)",
	Short: "Show rollout status",
	Long: `Show the status of the rollout.

By default, returns immediately with the current rollout status.
Use --watch to monitor the rollout until it completes.

Examples:
  # View rollout status
  vcli k8s rollout status deployment/nginx
  vcli k8s rollout status deployment nginx

  # Watch rollout status
  vcli k8s rollout status deployment/nginx --watch`,
	RunE: handleK8sRolloutStatus,
}

// k8sRolloutHistoryCmd represents the 'k8s rollout history' command
var k8sRolloutHistoryCmd = &cobra.Command{
	Use:   "history (RESOURCE/NAME | RESOURCE NAME)",
	Short: "View rollout history",
	Long: `View previous rollout revisions and configurations.

Examples:
  # View all revisions
  vcli k8s rollout history deployment/nginx
  vcli k8s rollout history deployment nginx

  # View specific revision
  vcli k8s rollout history deployment/nginx --revision=3`,
	RunE: handleK8sRolloutHistory,
}

// k8sRolloutUndoCmd represents the 'k8s rollout undo' command
var k8sRolloutUndoCmd = &cobra.Command{
	Use:   "undo (RESOURCE/NAME | RESOURCE NAME)",
	Short: "Rollback to a previous revision",
	Long: `Rollback to a previous revision of a deployment, statefulset, or daemonset.

By default, rolls back to the previous revision.
Use --to-revision to rollback to a specific revision.

Examples:
  # Rollback to previous revision
  vcli k8s rollout undo deployment/nginx
  vcli k8s rollout undo deployment nginx

  # Rollback to specific revision
  vcli k8s rollout undo deployment/nginx --to-revision=3`,
	RunE: handleK8sRolloutUndo,
}

// k8sRolloutRestartCmd represents the 'k8s rollout restart' command
var k8sRolloutRestartCmd = &cobra.Command{
	Use:   "restart (RESOURCE/NAME | RESOURCE NAME)",
	Short: "Restart a resource",
	Long: `Restart a deployment, statefulset, or daemonset.

This triggers a new rollout by adding a restart annotation.

Examples:
  # Restart a deployment
  vcli k8s rollout restart deployment/nginx
  vcli k8s rollout restart deployment nginx

  # Restart a statefulset
  vcli k8s rollout restart statefulset/web`,
	RunE: handleK8sRolloutRestart,
}

// k8sRolloutPauseCmd represents the 'k8s rollout pause' command
var k8sRolloutPauseCmd = &cobra.Command{
	Use:   "pause (RESOURCE/NAME | RESOURCE NAME)",
	Short: "Pause a deployment rollout",
	Long: `Pause a deployment rollout (deployments only).

Pausing allows you to make multiple changes before resuming the rollout.

Examples:
  # Pause a deployment
  vcli k8s rollout pause deployment/nginx
  vcli k8s rollout pause deployment nginx`,
	RunE: handleK8sRolloutPause,
}

// k8sRolloutResumeCmd represents the 'k8s rollout resume' command
var k8sRolloutResumeCmd = &cobra.Command{
	Use:   "resume (RESOURCE/NAME | RESOURCE NAME)",
	Short: "Resume a paused deployment rollout",
	Long: `Resume a paused deployment rollout (deployments only).

Examples:
  # Resume a deployment
  vcli k8s rollout resume deployment/nginx
  vcli k8s rollout resume deployment nginx`,
	RunE: handleK8sRolloutResume,
}

// handleK8sRolloutStatus handles the rollout status command
func handleK8sRolloutStatus(cmd *cobra.Command, args []string) error {
	// Parse resource kind and name
	kind, name, err := parseResourceArg(args)
	if err != nil {
		return err
	}

	// Get flags
	watch, err := cmd.Flags().GetBool("watch")
	if err != nil {
		return fmt.Errorf("failed to get watch flag: %w", err)
	}

	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	// Get kubeconfig path
	kubeconfigPath, err := getKubeconfigPath(cmd)
	if err != nil {
		return err
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

	// Get rollout status
	result, err := manager.RolloutStatus(kind, name, namespace, watch)
	if err != nil {
		return fmt.Errorf("failed to get rollout status: %w", err)
	}

	// Print status
	fmt.Printf("%s\n", result.Message)
	fmt.Printf("\nRollout Status:\n")
	fmt.Printf("  Replicas:          %d desired | %d updated | %d available | %d ready\n",
		result.Replicas, result.UpdatedReplicas, result.AvailableReplicas, result.ReadyReplicas)

	if result.CurrentRevision > 0 {
		fmt.Printf("  Current Revision:  %d\n", result.CurrentRevision)
	}

	if len(result.Conditions) > 0 {
		fmt.Printf("\nConditions:\n")
		for _, cond := range result.Conditions {
			fmt.Printf("  %s\n", cond)
		}
	}

	return nil
}

// handleK8sRolloutHistory handles the rollout history command
func handleK8sRolloutHistory(cmd *cobra.Command, args []string) error {
	// Parse resource kind and name
	kind, name, err := parseResourceArg(args)
	if err != nil {
		return err
	}

	// Get flags
	revision, err := cmd.Flags().GetInt64("revision")
	if err != nil {
		return fmt.Errorf("failed to get revision flag: %w", err)
	}

	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	// Get kubeconfig path
	kubeconfigPath, err := getKubeconfigPath(cmd)
	if err != nil {
		return err
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

	// Get rollout history
	result, err := manager.RolloutHistory(kind, name, namespace, revision)
	if err != nil {
		return fmt.Errorf("failed to get rollout history: %w", err)
	}

	// Print history
	fmt.Printf("%s %s/%s\n", result.Kind, result.Namespace, result.Name)
	if len(result.Revisions) == 0 {
		fmt.Println("No revisions found")
		return nil
	}

	fmt.Printf("\nREVISION\tCHANGE-CAUSE\n")
	for _, rev := range result.Revisions {
		fmt.Printf("%d\t\t%s\n", rev.Revision, rev.ChangeCause)
	}

	return nil
}

// handleK8sRolloutUndo handles the rollout undo command
func handleK8sRolloutUndo(cmd *cobra.Command, args []string) error {
	// Parse resource kind and name
	kind, name, err := parseResourceArg(args)
	if err != nil {
		return err
	}

	// Get flags
	toRevision, err := cmd.Flags().GetInt64("to-revision")
	if err != nil {
		return fmt.Errorf("failed to get to-revision flag: %w", err)
	}

	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	// Get kubeconfig path
	kubeconfigPath, err := getKubeconfigPath(cmd)
	if err != nil {
		return err
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

	// Undo rollout
	result, err := manager.RolloutUndo(kind, name, namespace, toRevision)
	if err != nil {
		return fmt.Errorf("failed to undo rollout: %w", err)
	}

	// Print result
	fmt.Printf("%s\n", result.Message)

	return nil
}

// handleK8sRolloutRestart handles the rollout restart command
func handleK8sRolloutRestart(cmd *cobra.Command, args []string) error {
	// Parse resource kind and name
	kind, name, err := parseResourceArg(args)
	if err != nil {
		return err
	}

	// Get flags
	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	// Get kubeconfig path
	kubeconfigPath, err := getKubeconfigPath(cmd)
	if err != nil {
		return err
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

	// Restart rollout
	if err := manager.RolloutRestart(kind, name, namespace); err != nil {
		return fmt.Errorf("failed to restart rollout: %w", err)
	}

	// Print result
	fmt.Printf("%s/%s restarted\n", kind, name)

	return nil
}

// handleK8sRolloutPause handles the rollout pause command
func handleK8sRolloutPause(cmd *cobra.Command, args []string) error {
	// Parse resource kind and name
	kind, name, err := parseResourceArg(args)
	if err != nil {
		return err
	}

	// Get flags
	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	// Get kubeconfig path
	kubeconfigPath, err := getKubeconfigPath(cmd)
	if err != nil {
		return err
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

	// Pause rollout
	if err := manager.RolloutPause(kind, name, namespace); err != nil {
		return fmt.Errorf("failed to pause rollout: %w", err)
	}

	// Print result
	fmt.Printf("%s/%s paused\n", kind, name)

	return nil
}

// handleK8sRolloutResume handles the rollout resume command
func handleK8sRolloutResume(cmd *cobra.Command, args []string) error {
	// Parse resource kind and name
	kind, name, err := parseResourceArg(args)
	if err != nil {
		return err
	}

	// Get flags
	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	// Get kubeconfig path
	kubeconfigPath, err := getKubeconfigPath(cmd)
	if err != nil {
		return err
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

	// Resume rollout
	if err := manager.RolloutResume(kind, name, namespace); err != nil {
		return fmt.Errorf("failed to resume rollout: %w", err)
	}

	// Print result
	fmt.Printf("%s/%s resumed\n", kind, name)

	return nil
}

// parseResourceArg parses resource arguments in the format "kind/name" or "kind name"
func parseResourceArg(args []string) (string, string, error) {
	if len(args) == 0 {
		return "", "", fmt.Errorf("resource is required")
	}

	// Format: "kind/name"
	if len(args) == 1 {
		parts := splitResourceName(args[0])
		if len(parts) != 2 {
			return "", "", fmt.Errorf("invalid resource format (expected KIND/NAME or KIND NAME)")
		}
		return parts[0], parts[1], nil
	}

	// Format: "kind name"
	if len(args) == 2 {
		return args[0], args[1], nil
	}

	return "", "", fmt.Errorf("too many arguments")
}

// splitResourceName splits "kind/name" into [kind, name]
func splitResourceName(resourceName string) []string {
	for i, c := range resourceName {
		if c == '/' {
			return []string{resourceName[:i], resourceName[i+1:]}
		}
	}
	return []string{resourceName}
}

func init() {
	// Add rollout command to k8s
	k8sCmd.AddCommand(k8sRolloutCmd)

	// Add subcommands
	k8sRolloutCmd.AddCommand(k8sRolloutStatusCmd)
	k8sRolloutCmd.AddCommand(k8sRolloutHistoryCmd)
	k8sRolloutCmd.AddCommand(k8sRolloutUndoCmd)
	k8sRolloutCmd.AddCommand(k8sRolloutRestartCmd)
	k8sRolloutCmd.AddCommand(k8sRolloutPauseCmd)
	k8sRolloutCmd.AddCommand(k8sRolloutResumeCmd)

	// Status flags
	k8sRolloutStatusCmd.Flags().BoolP("watch", "w", false, "Watch rollout status until completion")

	// History flags
	k8sRolloutHistoryCmd.Flags().Int64("revision", 0, "View specific revision details")

	// Undo flags
	k8sRolloutUndoCmd.Flags().Int64("to-revision", 0, "Revision to rollback to (default: previous revision)")
}
