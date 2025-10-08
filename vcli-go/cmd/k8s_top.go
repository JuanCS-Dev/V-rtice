package main

import (
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sTopCmd represents the 'k8s top' command
var k8sTopCmd = &cobra.Command{
	Use:   "top",
	Short: "Display resource (CPU/Memory) usage",
	Long: `Display resource (CPU/Memory) usage of nodes or pods.

The top command allows you to see the resource consumption of nodes or pods.
This command requires the metrics-server to be running in your cluster.

Available subcommands:
  nodes     Display resource usage of nodes
  node      Display resource usage of a specific node
  pods      Display resource usage of pods
  pod       Display resource usage of a specific pod

Examples:
  # Show metrics for all nodes
  vcli k8s top nodes

  # Show metrics for a specific node
  vcli k8s top node worker-1

  # Show metrics for all pods in default namespace
  vcli k8s top pods

  # Show metrics for pods across all namespaces
  vcli k8s top pods --all-namespaces

  # Show metrics for a specific pod
  vcli k8s top pod nginx-pod

  # Show metrics for all containers in pods
  vcli k8s top pods --containers`,
}

// topNodesCmd represents the 'top nodes' command
var topNodesCmd = &cobra.Command{
	Use:   "nodes",
	Short: "Display resource usage of nodes",
	Long: `Display resource (CPU/Memory) usage of nodes in the cluster.

Shows metrics for all nodes including CPU and memory consumption.

Examples:
  # Show metrics for all nodes
  vcli k8s top nodes

  # Show metrics in JSON format
  vcli k8s top nodes --output json`,
	RunE: k8s.HandleTopNodes,
}

// topNodeCmd represents the 'top node' command
var topNodeCmd = &cobra.Command{
	Use:   "node [name]",
	Short: "Display resource usage of a specific node or all nodes",
	Long: `Display resource (CPU/Memory) usage of a specific node by name,
or all nodes if no name is provided.

Examples:
  # Show metrics for all nodes (same as 'top nodes')
  vcli k8s top node

  # Show metrics for a specific node
  vcli k8s top node worker-1

  # Show metrics in YAML format
  vcli k8s top node master-1 --output yaml`,
	Args: cobra.MaximumNArgs(1),
	RunE: k8s.HandleTopNode,
}

// topPodsCmd represents the 'top pods' command
var topPodsCmd = &cobra.Command{
	Use:   "pods",
	Short: "Display resource usage of pods",
	Long: `Display resource (CPU/Memory) usage of pods in a namespace.

Shows metrics for all pods including CPU and memory consumption.
Use --containers to show metrics for individual containers.

Examples:
  # Show metrics for pods in default namespace
  vcli k8s top pods

  # Show metrics for pods in specific namespace
  vcli k8s top pods --namespace kube-system

  # Show metrics across all namespaces
  vcli k8s top pods --all-namespaces

  # Show container-level metrics
  vcli k8s top pods --containers

  # Show metrics in JSON format
  vcli k8s top pods --output json`,
	RunE: k8s.HandleTopPods,
}

// topPodCmd represents the 'top pod' command
var topPodCmd = &cobra.Command{
	Use:   "pod [name]",
	Short: "Display resource usage of a specific pod or all pods",
	Long: `Display resource (CPU/Memory) usage of a specific pod by name,
or all pods if no name is provided.

Use --containers to show metrics for individual containers within the pod.

Examples:
  # Show metrics for all pods (same as 'top pods')
  vcli k8s top pod

  # Show metrics for a specific pod
  vcli k8s top pod nginx-7848d4b86f-9xvzk

  # Show container-level metrics for a specific pod
  vcli k8s top pod nginx-7848d4b86f-9xvzk --containers

  # Show metrics in YAML format
  vcli k8s top pod web-app --output yaml`,
	Args: cobra.MaximumNArgs(1),
	RunE: k8s.HandleTopPod,
}

func init() {
	// Add top command to k8s
	k8sCmd.AddCommand(k8sTopCmd)

	// Add subcommands
	k8sTopCmd.AddCommand(topNodesCmd)
	k8sTopCmd.AddCommand(topNodeCmd)
	k8sTopCmd.AddCommand(topPodsCmd)
	k8sTopCmd.AddCommand(topPodCmd)

	// Pod-specific flags
	topPodsCmd.Flags().Bool("containers", false, "Show metrics for all containers in pods")
	topPodCmd.Flags().Bool("containers", false, "Show metrics for all containers in the pod")
}
