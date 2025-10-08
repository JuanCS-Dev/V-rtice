package main

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sExecCmd represents the 'k8s exec' command
var k8sExecCmd = &cobra.Command{
	Use:   "exec",
	Short: "Execute commands in pods",
	Long: `Execute commands in containers running in pods.

The exec command runs commands in containers and returns the output.
It supports kubectl-compatible syntax and behavior.

Examples:
  # Execute a command in a pod
  vcli k8s exec nginx-7848d4b86f-9xvzk -- ls /app

  # Execute a command in a specific container
  vcli k8s exec nginx-7848d4b86f-9xvzk -c nginx -- ps aux

  # Execute multiple commands
  vcli k8s exec nginx-7848d4b86f-9xvzk -- sh -c "ls -la && pwd"

  # Execute with namespace
  vcli k8s exec nginx-7848d4b86f-9xvzk --namespace=production -- date

  # Execute interactive shell (TTY)
  vcli k8s exec nginx-7848d4b86f-9xvzk -it -- /bin/sh

  # Execute with custom timeout
  vcli k8s exec nginx-7848d4b86f-9xvzk --timeout=5m -- long-running-command`,
	RunE: handleK8sExec,
}

// handleK8sExec handles the exec command execution
func handleK8sExec(cmd *cobra.Command, args []string) error {
	// Parse arguments
	if len(args) < 1 {
		return fmt.Errorf("pod name is required")
	}

	podName := args[0]
	var command []string

	// Find -- separator
	for i, arg := range args {
		if arg == "--" {
			if i+1 >= len(args) {
				return fmt.Errorf("command is required after --")
			}
			command = args[i+1:]
			break
		}
	}

	if len(command) == 0 {
		return fmt.Errorf("command is required (use -- to separate: vcli k8s exec POD -- COMMAND)")
	}

	// Get flags
	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	container, err := cmd.Flags().GetString("container")
	if err != nil {
		return fmt.Errorf("failed to get container flag: %w", err)
	}

	stdin, err := cmd.Flags().GetBool("stdin")
	if err != nil {
		return fmt.Errorf("failed to get stdin flag: %w", err)
	}

	tty, err := cmd.Flags().GetBool("tty")
	if err != nil {
		return fmt.Errorf("failed to get tty flag: %w", err)
	}

	timeout, err := cmd.Flags().GetDuration("timeout")
	if err != nil {
		return fmt.Errorf("failed to get timeout flag: %w", err)
	}

	quiet, err := cmd.Flags().GetBool("quiet")
	if err != nil {
		return fmt.Errorf("failed to get quiet flag: %w", err)
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

	// Prepare exec options
	execOpts := k8s.NewExecOptions(command)
	execOpts.Container = container
	execOpts.Stdin = stdin
	execOpts.Stdout = true
	execOpts.Stderr = !quiet
	execOpts.TTY = tty
	execOpts.Timeout = timeout

	// Handle interactive mode (TTY + stdin)
	if stdin && tty {
		// For interactive mode, use custom streams
		err := manager.ExecInPodWithStreams(
			podName,
			namespace,
			execOpts,
			os.Stdin,
			os.Stdout,
			os.Stderr,
		)
		if err != nil {
			return fmt.Errorf("exec failed: %w", err)
		}
		return nil
	}

	// Non-interactive mode
	result, err := manager.ExecInPod(podName, namespace, execOpts)
	if err != nil {
		return fmt.Errorf("exec failed: %w", err)
	}

	// Print stdout
	if result.Stdout != "" {
		fmt.Print(result.Stdout)
	}

	// Print stderr if not quiet
	if result.Stderr != "" && !quiet {
		fmt.Fprint(os.Stderr, result.Stderr)
	}

	// Check for errors
	if result.Error != nil {
		return fmt.Errorf("command failed: %w", result.Error)
	}

	if result.ExitCode != 0 {
		return fmt.Errorf("command exited with code %d", result.ExitCode)
	}

	return nil
}

func init() {
	// Add exec command to k8s
	k8sCmd.AddCommand(k8sExecCmd)

	// Flags
	k8sExecCmd.Flags().StringP("container", "c", "", "Container name (default: first container)")
	k8sExecCmd.Flags().BoolP("stdin", "i", false, "Pass stdin to the container")
	k8sExecCmd.Flags().BoolP("tty", "t", false, "Allocate a TTY")
	k8sExecCmd.Flags().Duration("timeout", 60*time.Second, "Timeout for exec operation")
	k8sExecCmd.Flags().BoolP("quiet", "q", false, "Suppress stderr output")
}
