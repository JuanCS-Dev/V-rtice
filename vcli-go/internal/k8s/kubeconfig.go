package k8s

import (
	"fmt"
	"os"

	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	clientcmdapi "k8s.io/client-go/tools/clientcmd/api"
)

// Kubeconfig represents a parsed Kubernetes configuration
type Kubeconfig struct {
	rawConfig      *clientcmdapi.Config
	clientConfig   clientcmd.ClientConfig
	kubeconfigPath string
}

// LoadKubeconfig loads and parses a kubeconfig file
func LoadKubeconfig(path string) (*Kubeconfig, error) {
	// Check if file exists
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return nil, fmt.Errorf("%w: %s", ErrKubeconfigFileNotFound, path)
	}

	// Load kubeconfig using client-go
	loadingRules := &clientcmd.ClientConfigLoadingRules{
		ExplicitPath: path,
	}

	configOverrides := &clientcmd.ConfigOverrides{}

	clientConfig := clientcmd.NewNonInteractiveDeferredLoadingClientConfig(
		loadingRules,
		configOverrides,
	)

	// Load raw config
	rawConfig, err := clientConfig.RawConfig()
	if err != nil {
		return nil, fmt.Errorf("%w: %v", ErrKubeconfigParseFailed, err)
	}

	// Validate config
	if err := validateKubeconfig(&rawConfig); err != nil {
		return nil, err
	}

	kc := &Kubeconfig{
		rawConfig:      &rawConfig,
		clientConfig:   clientConfig,
		kubeconfigPath: path,
	}

	return kc, nil
}

// validateKubeconfig validates the kubeconfig structure
func validateKubeconfig(config *clientcmdapi.Config) error {
	if config == nil {
		return ErrKubeconfigInvalid
	}

	// Check if there's at least one context
	if len(config.Contexts) == 0 {
		return fmt.Errorf("%w: no contexts defined", ErrKubeconfigInvalid)
	}

	// Check if there's a current context
	if config.CurrentContext == "" {
		return ErrNoCurrentContext
	}

	// Verify current context exists
	if _, exists := config.Contexts[config.CurrentContext]; !exists {
		return fmt.Errorf("%w: %s", ErrContextNotFound, config.CurrentContext)
	}

	return nil
}

// BuildRESTConfig builds a REST config for the specified context
func (kc *Kubeconfig) BuildRESTConfig(contextName string) (*rest.Config, error) {
	if kc.rawConfig == nil {
		return nil, ErrKubeconfigNil
	}

	// Verify context exists
	context, exists := kc.rawConfig.Contexts[contextName]
	if !exists {
		return nil, fmt.Errorf("%w: %s", ErrContextNotFound, contextName)
	}

	// Verify cluster exists
	if _, exists := kc.rawConfig.Clusters[context.Cluster]; !exists {
		return nil, fmt.Errorf("%w: %s", ErrClusterNotFound, context.Cluster)
	}

	// Verify user exists
	if _, exists := kc.rawConfig.AuthInfos[context.AuthInfo]; !exists {
		return nil, fmt.Errorf("%w: %s", ErrUserNotFound, context.AuthInfo)
	}

	// Build config using client-go
	configOverrides := &clientcmd.ConfigOverrides{
		CurrentContext: contextName,
	}

	clientConfig := clientcmd.NewNonInteractiveDeferredLoadingClientConfig(
		&clientcmd.ClientConfigLoadingRules{ExplicitPath: kc.kubeconfigPath},
		configOverrides,
	)

	config, err := clientConfig.ClientConfig()
	if err != nil {
		return nil, fmt.Errorf("failed to build client config: %w", err)
	}

	return config, nil
}

// HasContext checks if a context exists in the kubeconfig
func (kc *Kubeconfig) HasContext(contextName string) bool {
	if kc.rawConfig == nil {
		return false
	}

	_, exists := kc.rawConfig.Contexts[contextName]
	return exists
}

// ListContexts returns all available context names
func (kc *Kubeconfig) ListContexts() []string {
	if kc.rawConfig == nil {
		return []string{}
	}

	contexts := make([]string, 0, len(kc.rawConfig.Contexts))
	for name := range kc.rawConfig.Contexts {
		contexts = append(contexts, name)
	}

	return contexts
}

// GetCurrentContext returns the current context name
func (kc *Kubeconfig) GetCurrentContext() string {
	if kc.rawConfig == nil {
		return ""
	}

	return kc.rawConfig.CurrentContext
}

// GetContextInfo returns detailed information about a context
func (kc *Kubeconfig) GetContextInfo(contextName string) (*ContextInfo, error) {
	if kc.rawConfig == nil {
		return nil, ErrKubeconfigNil
	}

	context, exists := kc.rawConfig.Contexts[contextName]
	if !exists {
		return nil, fmt.Errorf("%w: %s", ErrContextNotFound, contextName)
	}

	cluster, exists := kc.rawConfig.Clusters[context.Cluster]
	if !exists {
		return nil, fmt.Errorf("%w: %s", ErrClusterNotFound, context.Cluster)
	}

	user, exists := kc.rawConfig.AuthInfos[context.AuthInfo]
	if !exists {
		return nil, fmt.Errorf("%w: %s", ErrUserNotFound, context.AuthInfo)
	}

	info := &ContextInfo{
		Name:           contextName,
		ClusterName:    context.Cluster,
		ClusterServer:  cluster.Server,
		UserName:       context.AuthInfo,
		Namespace:      context.Namespace,
		HasCertificate: len(user.ClientCertificateData) > 0 || user.ClientCertificate != "",
		HasToken:       user.Token != "",
	}

	// Set default namespace if not specified
	if info.Namespace == "" {
		info.Namespace = "default"
	}

	return info, nil
}

// ContextInfo contains information about a Kubernetes context
type ContextInfo struct {
	Name           string
	ClusterName    string
	ClusterServer  string
	UserName       string
	Namespace      string
	HasCertificate bool
	HasToken       bool
}

// CurrentContext is a convenience property for the current context
var CurrentContext = ""
