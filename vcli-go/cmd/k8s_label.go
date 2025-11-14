package cmd

import (
	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sLabelCmd represents the label command
var k8sLabelCmd = &cobra.Command{
	Use:   "label RESOURCE NAME KEY_1=VAL_1 ... KEY_N=VAL_N",
	Short: "Update labels on a resource",
	Long: `Update the labels on a resource.

Labels are key-value pairs attached to objects for identification and organization.

Examples:
  # Update pod 'my-pod' with label 'env=production'
  vcli k8s label pod my-pod env=production

  # Update pod 'my-pod' with multiple labels
  vcli k8s label pod my-pod tier=frontend app=nginx

  # Remove label 'env' from pod 'my-pod' (using minus suffix)
  vcli k8s label pod my-pod env-

  # Overwrite existing label value
  vcli k8s label pod my-pod env=staging --overwrite

  # Label a deployment
  vcli k8s label deployment my-deployment version=v1.2.3

  # Dry-run mode (show what would be changed)
  vcli k8s label pod my-pod env=dev --dry-run=client`,
	Args: cobra.MinimumNArgs(3),
	RunE: k8s.HandleLabel,
}

func init() {
	k8sCmd.AddCommand(k8sLabelCmd)

	// Add flags
	k8sLabelCmd.Flags().String("namespace", "", "Kubernetes namespace (defaults to 'default')")
	k8sLabelCmd.Flags().StringP("kubeconfig", "k", "", "Path to kubeconfig file")
	k8sLabelCmd.Flags().String("context", "", "Kubernetes context to use")
	k8sLabelCmd.Flags().Bool("overwrite", false, "Overwrite existing label values")
	k8sLabelCmd.Flags().String("dry-run", "", "Dry-run mode: 'none', 'client', or 'server' (default 'none')")
}
