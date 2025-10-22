package main

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/help"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sLogsCmd represents the 'k8s logs' command
var k8sLogsCmd = &cobra.Command{
	Use:   "logs",
	Short: "Get logs from pods",
	Long: `Get logs from pods in the cluster.

The logs command retrieves container logs from pods. It supports following logs
in real-time, getting logs from previous container instances, and filtering by time.`,
	Example: help.BuildCobraExample(help.K8sLogsExamples),
	RunE:    handleK8sLogs,
}

// handleK8sLogs handles the logs command execution
func handleK8sLogs(cmd *cobra.Command, args []string) error {
	// Validate args
	if len(args) < 1 {
		return fmt.Errorf("pod name is required")
	}

	podName := args[0]

	// Get flags
	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	container, err := cmd.Flags().GetString("container")
	if err != nil {
		return fmt.Errorf("failed to get container flag: %w", err)
	}

	follow, err := cmd.Flags().GetBool("follow")
	if err != nil {
		return fmt.Errorf("failed to get follow flag: %w", err)
	}

	previous, err := cmd.Flags().GetBool("previous")
	if err != nil {
		return fmt.Errorf("failed to get previous flag: %w", err)
	}

	timestamps, err := cmd.Flags().GetBool("timestamps")
	if err != nil {
		return fmt.Errorf("failed to get timestamps flag: %w", err)
	}

	tail, err := cmd.Flags().GetInt("tail")
	if err != nil {
		return fmt.Errorf("failed to get tail flag: %w", err)
	}

	sinceStr, err := cmd.Flags().GetString("since")
	if err != nil {
		return fmt.Errorf("failed to get since flag: %w", err)
	}

	sinceTimeStr, err := cmd.Flags().GetString("since-time")
	if err != nil {
		return fmt.Errorf("failed to get since-time flag: %w", err)
	}

	allContainers, err := cmd.Flags().GetBool("all-containers")
	if err != nil {
		return fmt.Errorf("failed to get all-containers flag: %w", err)
	}

	limitBytes, err := cmd.Flags().GetInt("limit-bytes")
	if err != nil {
		return fmt.Errorf("failed to get limit-bytes flag: %w", err)
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

	// Prepare log options
	logOpts := k8s.NewLogOptions()
	logOpts.Container = container
	logOpts.Follow = follow
	logOpts.Previous = previous
	logOpts.Timestamps = timestamps
	logOpts.TailLines = tail
	logOpts.LimitBytes = limitBytes

	// Parse since duration
	if sinceStr != "" {
		duration, err := time.ParseDuration(sinceStr)
		if err != nil {
			return fmt.Errorf("invalid since duration: %w", err)
		}
		logOpts.SinceSeconds = int(duration.Seconds())
	}

	// Parse since time
	if sinceTimeStr != "" {
		sinceTime, err := time.Parse(time.RFC3339, sinceTimeStr)
		if err != nil {
			return fmt.Errorf("invalid since-time format (use RFC3339): %w", err)
		}
		logOpts.SinceTime = &sinceTime
	}

	// Handle all-containers flag
	if allContainers {
		return handleAllContainerLogs(manager, podName, namespace, logOpts)
	}

	// Get logs
	if follow {
		return manager.FollowPodLogs(podName, namespace, os.Stdout, logOpts)
	}

	return manager.StreamPodLogs(podName, namespace, os.Stdout, logOpts)
}

// handleAllContainerLogs gets logs from all containers in a pod
func handleAllContainerLogs(manager *k8s.ClusterManager, podName, namespace string, opts *k8s.LogOptions) error {
	// List containers
	containers, err := manager.ListPodContainers(podName, namespace)
	if err != nil {
		return fmt.Errorf("failed to list containers: %w", err)
	}

	if len(containers) == 0 {
		return fmt.Errorf("no containers found in pod %s", podName)
	}

	// Get logs from each container
	for _, container := range containers {
		fmt.Printf("=== Container: %s ===\n", container)

		containerOpts := *opts
		containerOpts.Container = container
		containerOpts.Follow = false // Don't follow for all-containers

		if err := manager.StreamPodLogs(podName, namespace, os.Stdout, &containerOpts); err != nil {
			fmt.Fprintf(os.Stderr, "Warning: failed to get logs from container %s: %v\n", container, err)
			continue
		}

		fmt.Println()
	}

	return nil
}

func init() {
	// Add logs command to k8s
	k8sCmd.AddCommand(k8sLogsCmd)

	// Flags
	k8sLogsCmd.Flags().StringP("container", "c", "", "Container name (default: first container)")
	k8sLogsCmd.Flags().BoolP("follow", "f", false, "Follow log output")
	k8sLogsCmd.Flags().Bool("previous", false, "Get logs from previous container instance")
	k8sLogsCmd.Flags().Bool("timestamps", false, "Include timestamps in log output")
	k8sLogsCmd.Flags().Int("tail", -1, "Number of lines to show from end of logs (-1 = all)")
	k8sLogsCmd.Flags().String("since", "", "Get logs since duration (e.g., 1h, 30m, 10s)")
	k8sLogsCmd.Flags().String("since-time", "", "Get logs since RFC3339 time (e.g., 2025-01-01T00:00:00Z)")
	k8sLogsCmd.Flags().Bool("all-containers", false, "Get logs from all containers in pod")
	k8sLogsCmd.Flags().Int("limit-bytes", 0, "Limit log output to N bytes (0 = no limit)")
}
