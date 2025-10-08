package main

import (
	"github.com/spf13/cobra"
)

// k8sCreateCmd represents the 'k8s create' command
var k8sCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create Kubernetes resources",
	Long: `Create Kubernetes resources from command line.

The create command provides imperative commands for creating common Kubernetes resources
such as ConfigMaps, Secrets, and more.

Available subcommands:
  configmap    Create a ConfigMap from files, literals, or env files
  secret       Create a Secret from files, literals, or specific secret types

Examples:
  # Create a configmap
  vcli k8s create configmap my-config --from-file=config.yaml

  # Create a secret
  vcli k8s create secret generic my-secret --from-literal=password=secret123

  # Create a TLS secret
  vcli k8s create secret tls tls-secret --cert=cert.pem --key=key.pem`,
}

func init() {
	// Add create command to k8s
	k8sCmd.AddCommand(k8sCreateCmd)
}
