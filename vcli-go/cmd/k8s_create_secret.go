package cmd

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"
	vcliFs "github.com/verticedev/vcli-go/internal/fs"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// k8sCreateSecretCmd represents the 'k8s create secret' command
var k8sCreateSecretCmd = &cobra.Command{
	Use:   "secret",
	Short: "Create a Secret",
	Long: `Create a Secret from various sources.

The create secret command creates Secret resources with different types:
  - generic: Create from files or literal values
  - tls: Create from TLS certificate and key files
  - docker-registry: Create for Docker registry authentication

Examples:
  # Create a generic secret from files
  vcli k8s create secret generic my-secret --from-file=ssh-privatekey=~/.ssh/id_rsa

  # Create a generic secret from literal values
  vcli k8s create secret generic my-secret --from-literal=username=admin --from-literal=password=secret

  # Create a TLS secret
  vcli k8s create secret tls tls-secret --cert=cert.pem --key=key.pem

  # Create a docker-registry secret
  vcli k8s create secret docker-registry regcred --docker-server=https://index.docker.io/v1/ --docker-username=myuser --docker-password=mypass --docker-email=myemail@example.com`,
}

// k8sCreateSecretGenericCmd represents the 'k8s create secret generic' command
var k8sCreateSecretGenericCmd = &cobra.Command{
	Use:   "generic NAME [--from-file=FILE] [--from-literal=KEY=VALUE]",
	Short: "Create a generic secret from files or literal values",
	Long: `Create a generic secret from local files or literal values.

Examples:
  # Create a secret from a file
  vcli k8s create secret generic my-secret --from-file=ssh-privatekey=~/.ssh/id_rsa

  # Create a secret from multiple files
  vcli k8s create secret generic my-secret --from-file=file1.txt --from-file=file2.txt

  # Create a secret from literal values
  vcli k8s create secret generic my-secret --from-literal=username=admin --from-literal=password=secret123

  # Create with labels
  vcli k8s create secret generic my-secret --from-literal=password=secret --labels=app=myapp

  # Dry-run
  vcli k8s create secret generic my-secret --from-literal=password=secret --dry-run=client`,
	RunE: handleK8sCreateSecretGeneric,
}

// k8sCreateSecretTLSCmd represents the 'k8s create secret tls' command
var k8sCreateSecretTLSCmd = &cobra.Command{
	Use:   "tls NAME --cert=CERT_FILE --key=KEY_FILE",
	Short: "Create a TLS secret",
	Long: `Create a TLS secret from certificate and key files.

The TLS secret type is for storing TLS certificates and private keys.

Examples:
  # Create a TLS secret
  vcli k8s create secret tls tls-secret --cert=cert.pem --key=key.pem

  # Create in specific namespace
  vcli k8s create secret tls tls-secret --cert=cert.pem --key=key.pem --namespace=production

  # Dry-run
  vcli k8s create secret tls tls-secret --cert=cert.pem --key=key.pem --dry-run=server`,
	RunE: handleK8sCreateSecretTLS,
}

// k8sCreateSecretDockerRegistryCmd represents the 'k8s create secret docker-registry' command
var k8sCreateSecretDockerRegistryCmd = &cobra.Command{
	Use:   "docker-registry NAME --docker-server=SERVER --docker-username=USER --docker-password=PASS --docker-email=EMAIL",
	Short: "Create a secret for Docker registry authentication",
	Long: `Create a secret for use with Docker registries.

The docker-registry secret type is for storing credentials to access a Docker registry.

Examples:
  # Create a docker-registry secret
  vcli k8s create secret docker-registry regcred --docker-server=https://index.docker.io/v1/ --docker-username=myuser --docker-password=mypass --docker-email=myemail@example.com

  # Create for private registry
  vcli k8s create secret docker-registry private-reg --docker-server=https://my-registry.com --docker-username=admin --docker-password=secret --docker-email=admin@example.com

  # Dry-run
  vcli k8s create secret docker-registry regcred --docker-server=https://index.docker.io/v1/ --docker-username=user --docker-password=pass --docker-email=email@example.com --dry-run=client`,
	RunE: handleK8sCreateSecretDockerRegistry,
}

// handleK8sCreateSecretGeneric handles the create secret generic command execution
func handleK8sCreateSecretGeneric(cmd *cobra.Command, args []string) error {
	// Validate arguments
	if len(args) != 1 {
		return fmt.Errorf("secret name is required")
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
	if len(fromFiles) == 0 && len(fromLiterals) == 0 {
		return fmt.Errorf("at least one of --from-file or --from-literal must be specified")
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

	// Prepare Secret options
	opts := k8s.NewSecretOptions()
	opts.Type = k8s.SecretTypeOpaque
	opts.Timeout = timeout

	// Set dry-run mode
	opts.DryRun, err = parseDryRunMode(dryRunStr)
	if err != nil {
		return err
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
		for _, literal := range fromLiterals {
			key, value, err := k8s.ParseLiteral(literal)
			if err != nil {
				return fmt.Errorf("invalid literal value %q: %w", literal, err)
			}
			opts.Data[key] = value
		}
	}

	// Create Secret
	var secret interface{}

	if len(fromFiles) > 0 {
		// Create from files
		secret, err = manager.CreateSecretFromFiles(name, namespace, fromFiles, opts)
		if err != nil {
			return fmt.Errorf("failed to create secret from files: %w", err)
		}
	} else {
		// Create from literals only
		secret, err = manager.CreateSecret(name, namespace, opts)
		if err != nil {
			return fmt.Errorf("failed to create secret: %w", err)
		}
	}

	// Format output
	if output != "" {
		// Output in specified format
		formatted, err := k8s.FormatOutput(secret, output)
		if err != nil {
			return fmt.Errorf("failed to format output: %w", err)
		}
		fmt.Println(formatted)
	} else {
		// Default output
		if opts.DryRun != k8s.DryRunNone {
			fmt.Printf("secret/%s created (dry run)\n", name)
		} else {
			fmt.Printf("secret/%s created\n", name)
		}
	}

	return nil
}

// handleK8sCreateSecretTLS handles the create secret tls command execution
func handleK8sCreateSecretTLS(cmd *cobra.Command, args []string) error {
	// Validate arguments
	if len(args) != 1 {
		return fmt.Errorf("secret name is required")
	}

	name := args[0]

	// Get flags
	certFile, err := cmd.Flags().GetString("cert")
	if err != nil {
		return fmt.Errorf("failed to get cert flag: %w", err)
	}

	keyFile, err := cmd.Flags().GetString("key")
	if err != nil {
		return fmt.Errorf("failed to get key flag: %w", err)
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
	if certFile == "" {
		return fmt.Errorf("--cert is required")
	}
	if keyFile == "" {
		return fmt.Errorf("--key is required")
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

	// Prepare Secret options
	opts := k8s.NewSecretOptions()
	opts.Timeout = timeout

	// Set dry-run mode
	opts.DryRun, err = parseDryRunMode(dryRunStr)
	if err != nil {
		return err
	}

	// Parse labels
	if labelsStr != "" {
		labels, err := k8s.ParseLabels(labelsStr)
		if err != nil {
			return fmt.Errorf("failed to parse labels: %w", err)
		}
		opts.Labels = labels
	}

	// Create TLS secret
	secret, err := manager.CreateTLSSecret(name, namespace, certFile, keyFile, opts)
	if err != nil {
		return fmt.Errorf("failed to create TLS secret: %w", err)
	}

	// Format output
	if output != "" {
		// Output in specified format
		formatted, err := k8s.FormatOutput(secret, output)
		if err != nil {
			return fmt.Errorf("failed to format output: %w", err)
		}
		fmt.Println(formatted)
	} else {
		// Default output
		if opts.DryRun != k8s.DryRunNone {
			fmt.Printf("secret/%s created (dry run)\n", name)
		} else {
			fmt.Printf("secret/%s created\n", name)
		}
	}

	return nil
}

// handleK8sCreateSecretDockerRegistry handles the create secret docker-registry command execution
func handleK8sCreateSecretDockerRegistry(cmd *cobra.Command, args []string) error {
	// Validate arguments
	if len(args) != 1 {
		return fmt.Errorf("secret name is required")
	}

	name := args[0]

	// Get flags
	server, err := cmd.Flags().GetString("docker-server")
	if err != nil {
		return fmt.Errorf("failed to get docker-server flag: %w", err)
	}

	username, err := cmd.Flags().GetString("docker-username")
	if err != nil {
		return fmt.Errorf("failed to get docker-username flag: %w", err)
	}

	password, err := cmd.Flags().GetString("docker-password")
	if err != nil {
		return fmt.Errorf("failed to get docker-password flag: %w", err)
	}

	email, err := cmd.Flags().GetString("docker-email")
	if err != nil {
		return fmt.Errorf("failed to get docker-email flag: %w", err)
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
	if server == "" {
		return fmt.Errorf("--docker-server is required")
	}
	if username == "" {
		return fmt.Errorf("--docker-username is required")
	}
	if password == "" {
		return fmt.Errorf("--docker-password is required")
	}
	if email == "" {
		return fmt.Errorf("--docker-email is required")
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

	// Prepare Secret options
	opts := k8s.NewSecretOptions()
	opts.Timeout = timeout

	// Set dry-run mode
	opts.DryRun, err = parseDryRunMode(dryRunStr)
	if err != nil {
		return err
	}

	// Parse labels
	if labelsStr != "" {
		labels, err := k8s.ParseLabels(labelsStr)
		if err != nil {
			return fmt.Errorf("failed to parse labels: %w", err)
		}
		opts.Labels = labels
	}

	// Create docker-registry secret
	secret, err := manager.CreateDockerRegistrySecret(name, namespace, server, username, password, email, opts)
	if err != nil {
		return fmt.Errorf("failed to create docker-registry secret: %w", err)
	}

	// Format output
	if output != "" {
		// Output in specified format
		formatted, err := k8s.FormatOutput(secret, output)
		if err != nil {
			return fmt.Errorf("failed to format output: %w", err)
		}
		fmt.Println(formatted)
	} else {
		// Default output
		if opts.DryRun != k8s.DryRunNone {
			fmt.Printf("secret/%s created (dry run)\n", name)
		} else {
			fmt.Printf("secret/%s created\n", name)
		}
	}

	return nil
}

// getKubeconfigPath retrieves the kubeconfig path from flags or environment
func getKubeconfigPath(cmd *cobra.Command) (string, error) {
	kubeconfigPath, err := cmd.Flags().GetString("kubeconfig")
	if err != nil {
		return "", fmt.Errorf("failed to get kubeconfig flag: %w", err)
	}

	if kubeconfigPath == "" {
		// Use default kubeconfig path with proper error handling
		kubeconfigPath, err = vcliFs.GetKubeconfigPath()
		if err != nil {
			return "", fmt.Errorf("failed to get kubeconfig path: %w", err)
		}
		// Check KUBECONFIG env var (takes precedence)
		if envPath := os.Getenv("KUBECONFIG"); envPath != "" {
			kubeconfigPath = envPath
		}
	}

	return kubeconfigPath, nil
}

// parseDryRunMode parses the dry-run flag value
func parseDryRunMode(dryRunStr string) (k8s.DryRunStrategy, error) {
	switch dryRunStr {
	case "none", "":
		return k8s.DryRunNone, nil
	case "client":
		return k8s.DryRunClient, nil
	case "server":
		return k8s.DryRunServer, nil
	default:
		return k8s.DryRunNone, fmt.Errorf("invalid dry-run value: %s (must be 'none', 'client', or 'server')", dryRunStr)
	}
}

func init() {
	// Add secret subcommands
	k8sCreateSecretCmd.AddCommand(k8sCreateSecretGenericCmd)
	k8sCreateSecretCmd.AddCommand(k8sCreateSecretTLSCmd)
	k8sCreateSecretCmd.AddCommand(k8sCreateSecretDockerRegistryCmd)

	// Add secret command to create
	k8sCreateCmd.AddCommand(k8sCreateSecretCmd)

	// Generic secret flags
	k8sCreateSecretGenericCmd.Flags().StringArray("from-file", []string{}, "File to read data from (can be specified multiple times)")
	k8sCreateSecretGenericCmd.Flags().StringArray("from-literal", []string{}, "Literal key=value pairs (can be specified multiple times)")
	k8sCreateSecretGenericCmd.Flags().String("labels", "", "Labels to apply to the secret (e.g., app=myapp,env=prod)")
	k8sCreateSecretGenericCmd.Flags().String("dry-run", "none", "Dry-run mode: none, client, or server")
	k8sCreateSecretGenericCmd.Flags().StringP("output", "o", "", "Output format: json, yaml, or wide")
	k8sCreateSecretGenericCmd.Flags().Duration("timeout", 30*time.Second, "Timeout for create operation")

	// TLS secret flags
	k8sCreateSecretTLSCmd.Flags().String("cert", "", "Path to TLS certificate file (required)")
	k8sCreateSecretTLSCmd.Flags().String("key", "", "Path to TLS private key file (required)")
	k8sCreateSecretTLSCmd.Flags().String("labels", "", "Labels to apply to the secret (e.g., app=myapp,env=prod)")
	k8sCreateSecretTLSCmd.Flags().String("dry-run", "none", "Dry-run mode: none, client, or server")
	k8sCreateSecretTLSCmd.Flags().StringP("output", "o", "", "Output format: json, yaml, or wide")
	k8sCreateSecretTLSCmd.Flags().Duration("timeout", 30*time.Second, "Timeout for create operation")
	k8sCreateSecretTLSCmd.MarkFlagRequired("cert")
	k8sCreateSecretTLSCmd.MarkFlagRequired("key")

	// Docker-registry secret flags
	k8sCreateSecretDockerRegistryCmd.Flags().String("docker-server", "", "Docker registry server (required)")
	k8sCreateSecretDockerRegistryCmd.Flags().String("docker-username", "", "Docker registry username (required)")
	k8sCreateSecretDockerRegistryCmd.Flags().String("docker-password", "", "Docker registry password (required)")
	k8sCreateSecretDockerRegistryCmd.Flags().String("docker-email", "", "Docker registry email (required)")
	k8sCreateSecretDockerRegistryCmd.Flags().String("labels", "", "Labels to apply to the secret (e.g., app=myapp,env=prod)")
	k8sCreateSecretDockerRegistryCmd.Flags().String("dry-run", "none", "Dry-run mode: none, client, or server")
	k8sCreateSecretDockerRegistryCmd.Flags().StringP("output", "o", "", "Output format: json, yaml, or wide")
	k8sCreateSecretDockerRegistryCmd.Flags().Duration("timeout", 30*time.Second, "Timeout for create operation")
	k8sCreateSecretDockerRegistryCmd.MarkFlagRequired("docker-server")
	k8sCreateSecretDockerRegistryCmd.MarkFlagRequired("docker-username")
	k8sCreateSecretDockerRegistryCmd.MarkFlagRequired("docker-password")
	k8sCreateSecretDockerRegistryCmd.MarkFlagRequired("docker-email")
}
