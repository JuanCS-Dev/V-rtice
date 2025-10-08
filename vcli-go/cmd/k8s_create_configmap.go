package main

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sCreateConfigMapCmd represents the 'k8s create configmap' command
var k8sCreateConfigMapCmd = &cobra.Command{
	Use:   "configmap NAME [--from-file=FILE] [--from-literal=KEY=VALUE] [--from-env-file=FILE]",
	Short: "Create a ConfigMap from files, literals, or env files",
	Long: `Create a ConfigMap from local files, literal values, or env files.

The create configmap command creates a ConfigMap resource with data from various sources.
It supports kubectl-compatible syntax and behavior.

Examples:
  # Create a new configmap named my-config from a file
  vcli k8s create configmap my-config --from-file=config.yaml

  # Create a configmap from multiple files
  vcli k8s create configmap my-config --from-file=config1.yaml --from-file=config2.yaml

  # Create a configmap from a directory
  vcli k8s create configmap my-config --from-file=config-dir/

  # Create a configmap with literal values
  vcli k8s create configmap my-config --from-literal=key1=value1 --from-literal=key2=value2

  # Create a configmap from an env file
  vcli k8s create configmap my-config --from-env-file=.env

  # Create a configmap with labels
  vcli k8s create configmap my-config --from-file=config.yaml --labels=app=myapp,env=prod

  # Create in specific namespace
  vcli k8s create configmap my-config --from-file=config.yaml --namespace=production

  # Dry-run (client-side)
  vcli k8s create configmap my-config --from-file=config.yaml --dry-run=client

  # Dry-run (server-side) with output
  vcli k8s create configmap my-config --from-file=config.yaml --dry-run=server -o yaml`,
	RunE: handleK8sCreateConfigMap,
}

// handleK8sCreateConfigMap handles the create configmap command execution
func handleK8sCreateConfigMap(cmd *cobra.Command, args []string) error {
	// Validate arguments
	if len(args) != 1 {
		return fmt.Errorf("configmap name is required")
	}

	name := args[0]

	// Get flags
	fromFiles, err := cmd.Flags().GetStringArray("from-file")
	if err != nil {
		return fmt.Errorf("failed to get from-file flag: %w", err)
	}

	fromLiterals, err := cmd.Flags().GetStringArray("from-literal")
	if err != nil {
		return fmt.Errorf("failed to get from-literal flag: %w", err)
	}

	fromEnvFile, err := cmd.Flags().GetString("from-env-file")
	if err != nil {
		return fmt.Errorf("failed to get from-env-file flag: %w", err)
	}

	labelsStr, err := cmd.Flags().GetString("labels")
	if err != nil {
		return fmt.Errorf("failed to get labels flag: %w", err)
	}

	namespace, err := cmd.Flags().GetString("namespace")
	if err != nil {
		return fmt.Errorf("failed to get namespace flag: %w", err)
	}

	dryRunStr, err := cmd.Flags().GetString("dry-run")
	if err != nil {
		return fmt.Errorf("failed to get dry-run flag: %w", err)
	}

	output, err := cmd.Flags().GetString("output")
	if err != nil {
		return fmt.Errorf("failed to get output flag: %w", err)
	}

	timeout, err := cmd.Flags().GetDuration("timeout")
	if err != nil {
		return fmt.Errorf("failed to get timeout flag: %w", err)
	}

	// Validate inputs
	if len(fromFiles) == 0 && len(fromLiterals) == 0 && fromEnvFile == "" {
		return fmt.Errorf("at least one of --from-file, --from-literal, or --from-env-file must be specified")
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

	// Prepare ConfigMap options
	opts := k8s.NewConfigMapOptions()
	opts.Timeout = timeout

	// Set dry-run mode
	switch dryRunStr {
	case "none", "":
		opts.DryRun = k8s.DryRunNone
	case "client":
		opts.DryRun = k8s.DryRunClient
	case "server":
		opts.DryRun = k8s.DryRunServer
	default:
		return fmt.Errorf("invalid dry-run value: %s (must be 'none', 'client', or 'server')", dryRunStr)
	}

	// Parse labels
	if labelsStr != "" {
		labels, err := k8s.ParseLabels(labelsStr)
		if err != nil {
			return fmt.Errorf("failed to parse labels: %w", err)
		}
		opts.Labels = labels
	}

	// Initialize data maps
	if opts.Data == nil {
		opts.Data = make(map[string]string)
	}

	// Process --from-literal
	if len(fromLiterals) > 0 {
		literals := make(map[string]string)
		for _, literal := range fromLiterals {
			key, value, err := k8s.ParseLiteral(literal)
			if err != nil {
				return fmt.Errorf("invalid literal value %q: %w", literal, err)
			}
			literals[key] = value
		}

		for k, v := range literals {
			opts.Data[k] = v
		}
	}

	// Create ConfigMap based on source type
	var configMap interface{}

	if fromEnvFile != "" {
		// Create from env file
		configMap, err = manager.CreateConfigMapFromEnvFile(name, namespace, fromEnvFile, opts)
		if err != nil {
			return fmt.Errorf("failed to create configmap from env file: %w", err)
		}
	} else if len(fromFiles) > 0 {
		// Create from files
		configMap, err = manager.CreateConfigMapFromFiles(name, namespace, fromFiles, opts)
		if err != nil {
			return fmt.Errorf("failed to create configmap from files: %w", err)
		}
	} else {
		// Create from literals only
		configMap, err = manager.CreateConfigMap(name, namespace, opts)
		if err != nil {
			return fmt.Errorf("failed to create configmap: %w", err)
		}
	}

	// Format output
	if output != "" {
		// Output in specified format
		formatted, err := k8s.FormatOutput(configMap, output)
		if err != nil {
			return fmt.Errorf("failed to format output: %w", err)
		}
		fmt.Println(formatted)
	} else {
		// Default output
		if opts.DryRun != k8s.DryRunNone {
			fmt.Printf("configmap/%s created (dry run)\n", name)
		} else {
			fmt.Printf("configmap/%s created\n", name)
		}
	}

	return nil
}

func init() {
	// Add create configmap command to create
	k8sCreateCmd.AddCommand(k8sCreateConfigMapCmd)

	// Flags
	k8sCreateConfigMapCmd.Flags().StringArray("from-file", []string{}, "File or directory to read data from (can be specified multiple times)")
	k8sCreateConfigMapCmd.Flags().StringArray("from-literal", []string{}, "Literal key=value pairs (can be specified multiple times)")
	k8sCreateConfigMapCmd.Flags().String("from-env-file", "", "File to read environment variables from")
	k8sCreateConfigMapCmd.Flags().String("labels", "", "Labels to apply to the configmap (e.g., app=myapp,env=prod)")
	k8sCreateConfigMapCmd.Flags().String("dry-run", "none", "Dry-run mode: none, client, or server")
	k8sCreateConfigMapCmd.Flags().StringP("output", "o", "", "Output format: json, yaml, or wide")
	k8sCreateConfigMapCmd.Flags().Duration("timeout", 30*time.Second, "Timeout for create operation")
}
