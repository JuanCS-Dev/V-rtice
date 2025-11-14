package cmd

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/spf13/cobra"
	vcliFs "github.com/verticedev/vcli-go/internal/fs"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sPortForwardCmd represents the 'k8s port-forward' command
var k8sPortForwardCmd = &cobra.Command{
	Use:   "port-forward",
	Short: "Forward local ports to pods",
	Long: `Forward one or more local ports to a pod.

The port-forward command forwards traffic from local ports to ports on a pod.
It supports kubectl-compatible syntax and behavior.

Examples:
  # Forward local port 8080 to pod port 80
  vcli k8s port-forward nginx-7848d4b86f-9xvzk 8080:80

  # Forward multiple ports
  vcli k8s port-forward nginx-7848d4b86f-9xvzk 8080:80 8443:443

  # Forward with namespace
  vcli k8s port-forward nginx-7848d4b86f-9xvzk 8080:80 --namespace=production

  # Forward to specific address
  vcli k8s port-forward nginx-7848d4b86f-9xvzk 8080:80 --address=0.0.0.0

  # Forward with custom timeout
  vcli k8s port-forward nginx-7848d4b86f-9xvzk 8080:80 --timeout=5m`,
	RunE: handleK8sPortForward,
}

// handleK8sPortForward handles the port-forward command execution
func handleK8sPortForward(cmd *cobra.Command, args []string) error {
	// Parse arguments
	if len(args) < 2 {
		return fmt.Errorf("pod name and at least one port mapping required (e.g., 'nginx 8080:80')")
	}

	podName := args[0]
	portStrs := args[1:]

	// Parse port mappings
	ports, err := k8s.ParsePortMappings(portStrs)
	if err != nil {
		return fmt.Errorf("failed to parse port mappings: %w", err)
	}

	// Get flags
	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	address, err := cmd.Flags().GetString("address")
	if err != nil {
		return fmt.Errorf("failed to get address flag: %w", err)
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

	// Prepare port forward options
	opts := k8s.NewPortForwardOptions(ports)
	opts.Address = address
	opts.Timeout = timeout

	// Validate options
	if err := k8s.ValidatePortForwardOptions(opts); err != nil {
		return fmt.Errorf("invalid port forward options: %w", err)
	}

	// Print info
	fmt.Printf("Forwarding from %s:%s -> %s/%s\n",
		address,
		k8s.FormatPortMappings(ports),
		namespace,
		podName)
	fmt.Println("Press Ctrl+C to stop forwarding")

	// Setup signal handling
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Start port forwarding asynchronously
	result, err := manager.PortForwardToPodAsync(podName, namespace, opts)
	if err != nil {
		return fmt.Errorf("failed to start port forward: %w", err)
	}

	// Wait for ready signal
	select {
	case <-opts.ReadyChannel:
		fmt.Println("Port forwarding is ready")
	case <-time.After(10 * time.Second):
		return fmt.Errorf("timeout waiting for port forward to be ready")
	}

	// Wait for interrupt signal
	<-sigChan
	fmt.Println("\nStopping port forward...")

	// Stop port forward
	if err := k8s.StopPortForward(result); err != nil {
		return fmt.Errorf("failed to stop port forward: %w", err)
	}

	fmt.Println("Port forward stopped")
	return nil
}

func init() {
	// Add port-forward command to k8s
	k8sCmd.AddCommand(k8sPortForwardCmd)

	// Flags
	k8sPortForwardCmd.Flags().String("address", "localhost", "Local address to bind to")
	k8sPortForwardCmd.Flags().Duration("timeout", 60*time.Second, "Timeout for establishing port forward")
}
