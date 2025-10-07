package main

import (
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sAnnotateCmd represents the annotate command
var k8sAnnotateCmd = &cobra.Command{
	Use:   "annotate RESOURCE NAME KEY_1=VAL_1 ... KEY_N=VAL_N",
	Short: "Update annotations on a resource",
	Long: `Update the annotations on a resource.

Annotations are key-value pairs for storing arbitrary non-identifying metadata.
Unlike labels, annotations are not used for selection but can store larger data.

Examples:
  # Add annotation to pod 'my-pod'
  vcli k8s annotate pod my-pod description="Main application pod"

  # Add multiple annotations
  vcli k8s annotate pod my-pod owner=team-a contact=admin@example.com

  # Remove annotation 'description' from pod 'my-pod' (using minus suffix)
  vcli k8s annotate pod my-pod description-

  # Overwrite existing annotation value
  vcli k8s annotate pod my-pod description="Updated description" --overwrite

  # Annotate a service
  vcli k8s annotate service my-service prometheus.io/scrape=true

  # Dry-run mode (show what would be changed)
  vcli k8s annotate pod my-pod version=v2.0 --dry-run=client`,
	Args: cobra.MinimumNArgs(3),
	RunE: k8s.HandleAnnotate,
}

func init() {
	k8sCmd.AddCommand(k8sAnnotateCmd)

	// Add flags
	k8sAnnotateCmd.Flags().String("namespace", "", "Kubernetes namespace (defaults to 'default')")
	k8sAnnotateCmd.Flags().StringP("kubeconfig", "k", "", "Path to kubeconfig file")
	k8sAnnotateCmd.Flags().String("context", "", "Kubernetes context to use")
	k8sAnnotateCmd.Flags().Bool("overwrite", false, "Overwrite existing annotation values")
	k8sAnnotateCmd.Flags().String("dry-run", "", "Dry-run mode: 'none', 'client', or 'server' (default 'none')")
}
