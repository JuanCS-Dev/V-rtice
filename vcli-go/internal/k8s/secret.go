package k8s

import (
	"context"
	"encoding/base64"
	"fmt"
	"os"
	"path/filepath"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// CreateSecret creates a Secret
func (cm *ClusterManager) CreateSecret(name, namespace string, opts *SecretOptions) (*corev1.Secret, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if name == "" {
		return nil, fmt.Errorf("secret name is required")
	}

	if namespace == "" {
		namespace = "default"
	}

	if opts == nil {
		opts = NewSecretOptions()
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// Convert string data to binary data (base64)
	stringData := opts.Data

	// Build Secret object
	secret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: namespace,
			Labels:    opts.Labels,
		},
		Type:       corev1.SecretType(opts.Type),
		StringData: stringData,
		Data:       opts.BinaryData,
	}

	// Create Secret
	result, err := cm.clientset.CoreV1().Secrets(namespace).Create(ctx, secret, metav1.CreateOptions{
		DryRun:       convertDryRunToDryRunArray(opts.DryRun),
		FieldManager: "vcli",
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create secret %s: %w", name, err)
	}

	return result, nil
}

// GetSecret retrieves a Secret
func (cm *ClusterManager) GetSecret(name, namespace string) (*corev1.Secret, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	secret, err := cm.clientset.CoreV1().Secrets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get secret %s: %w", name, err)
	}

	return secret, nil
}

// UpdateSecret updates a Secret
func (cm *ClusterManager) UpdateSecret(name, namespace string, opts *SecretOptions) (*corev1.Secret, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	if opts == nil {
		return nil, fmt.Errorf("options are required for update")
	}

	ctx := context.Background()

	// Get existing Secret
	existing, err := cm.clientset.CoreV1().Secrets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get existing secret: %w", err)
	}

	// Update fields
	if opts.Data != nil {
		existing.StringData = opts.Data
	}
	if opts.BinaryData != nil {
		existing.Data = opts.BinaryData
	}
	if opts.Labels != nil {
		existing.Labels = opts.Labels
	}
	if opts.Type != "" {
		existing.Type = corev1.SecretType(opts.Type)
	}

	// Update Secret
	result, err := cm.clientset.CoreV1().Secrets(namespace).Update(ctx, existing, metav1.UpdateOptions{
		DryRun:       convertDryRunToDryRunArray(opts.DryRun),
		FieldManager: "vcli",
	})
	if err != nil {
		return nil, fmt.Errorf("failed to update secret %s: %w", name, err)
	}

	return result, nil
}

// DeleteSecret deletes a Secret
func (cm *ClusterManager) DeleteSecret(name, namespace string) error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	err := cm.clientset.CoreV1().Secrets(namespace).Delete(ctx, name, metav1.DeleteOptions{})
	if err != nil {
		return fmt.Errorf("failed to delete secret %s: %w", name, err)
	}

	return nil
}

// ListSecrets lists Secrets
func (cm *ClusterManager) ListSecrets(namespace string, opts *SecretListOptions) (*corev1.SecretList, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	listOpts := metav1.ListOptions{}
	if opts != nil {
		if len(opts.Labels) > 0 {
			listOpts.LabelSelector = formatLabelSelector(opts.Labels)
		}
		if opts.FieldSelector != "" {
			listOpts.FieldSelector = opts.FieldSelector
		}
	}

	secrets, err := cm.clientset.CoreV1().Secrets(namespace).List(ctx, listOpts)
	if err != nil {
		return nil, fmt.Errorf("failed to list secrets: %w", err)
	}

	return secrets, nil
}

// CreateSecretFromFiles creates a Secret from files
func (cm *ClusterManager) CreateSecretFromFiles(name, namespace string, files []string, opts *SecretOptions) (*corev1.Secret, error) {
	if opts == nil {
		opts = NewSecretOptions()
	}

	// Initialize data map if nil
	if opts.Data == nil {
		opts.Data = make(map[string]string)
	}

	// Read files
	for _, file := range files {
		data, err := os.ReadFile(file)
		if err != nil {
			return nil, fmt.Errorf("failed to read file %s: %w", file, err)
		}

		// Use basename as key
		key := filepath.Base(file)
		opts.Data[key] = string(data)
	}

	return cm.CreateSecret(name, namespace, opts)
}

// CreateSecretFromLiterals creates a Secret from literal values
func (cm *ClusterManager) CreateSecretFromLiterals(name, namespace string, literals map[string]string, opts *SecretOptions) (*corev1.Secret, error) {
	if opts == nil {
		opts = NewSecretOptions()
	}

	opts.Data = literals

	return cm.CreateSecret(name, namespace, opts)
}

// CreateTLSSecret creates a TLS Secret
func (cm *ClusterManager) CreateTLSSecret(name, namespace, certFile, keyFile string, opts *SecretOptions) (*corev1.Secret, error) {
	if opts == nil {
		opts = NewSecretOptions()
	}

	// Read cert and key files
	cert, err := os.ReadFile(certFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read cert file: %w", err)
	}

	key, err := os.ReadFile(keyFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read key file: %w", err)
	}

	// Set type and data
	opts.Type = SecretTypeTLS
	opts.Data = map[string]string{
		"tls.crt": string(cert),
		"tls.key": string(key),
	}

	return cm.CreateSecret(name, namespace, opts)
}

// CreateDockerRegistrySecret creates a Docker registry Secret
func (cm *ClusterManager) CreateDockerRegistrySecret(name, namespace, server, username, password, email string, opts *SecretOptions) (*corev1.Secret, error) {
	if opts == nil {
		opts = NewSecretOptions()
	}

	// Build docker config JSON
	dockerConfig := fmt.Sprintf(`{
  "auths": {
    "%s": {
      "username": "%s",
      "password": "%s",
      "email": "%s",
      "auth": "%s"
    }
  }
}`, server, username, password, email, base64.StdEncoding.EncodeToString([]byte(username+":"+password)))

	// Set type and data
	opts.Type = SecretTypeDockerConfigJson
	opts.Data = map[string]string{
		".dockerconfigjson": dockerConfig,
	}

	return cm.CreateSecret(name, namespace, opts)
}

// CreateBasicAuthSecret creates a basic auth Secret
func (cm *ClusterManager) CreateBasicAuthSecret(name, namespace, username, password string, opts *SecretOptions) (*corev1.Secret, error) {
	if opts == nil {
		opts = NewSecretOptions()
	}

	// Set type and data
	opts.Type = SecretTypeBasicAuth
	opts.Data = map[string]string{
		"username": username,
		"password": password,
	}

	return cm.CreateSecret(name, namespace, opts)
}

// CreateSSHAuthSecret creates an SSH auth Secret
func (cm *ClusterManager) CreateSSHAuthSecret(name, namespace, privateKeyFile string, opts *SecretOptions) (*corev1.Secret, error) {
	if opts == nil {
		opts = NewSecretOptions()
	}

	// Read private key file
	privateKey, err := os.ReadFile(privateKeyFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read private key file: %w", err)
	}

	// Set type and data
	opts.Type = SecretTypeSSHAuth
	opts.Data = map[string]string{
		"ssh-privatekey": string(privateKey),
	}

	return cm.CreateSecret(name, namespace, opts)
}

// ValidateSecretOptions validates Secret options
func ValidateSecretOptions(opts *SecretOptions) error {
	if opts == nil {
		return fmt.Errorf("secret options are required")
	}

	if opts.Data == nil && opts.BinaryData == nil {
		return fmt.Errorf("at least one of data or binary data must be provided")
	}

	return nil
}

// DecodeSecretData decodes secret data from base64
func DecodeSecretData(data map[string][]byte) (map[string]string, error) {
	result := make(map[string]string)
	for key, value := range data {
		result[key] = string(value)
	}
	return result, nil
}
