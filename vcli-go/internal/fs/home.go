// Package fs provides filesystem utilities for vcli-go
// Following Boris Cherny principles: "Make errors impossible to ignore"
package fs

import (
	"fmt"
	"os"
	"path/filepath"
)

// GetHomeDir returns the user's home directory with proper error handling
// This is a safer alternative to os.UserHomeDir() that wraps the error with context
func GetHomeDir() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get user home directory: %w", err)
	}

	// Normalize path - remove trailing slash if present
	home = filepath.Clean(home)

	return home, nil
}

// JoinHomePath joins path elements with the user's home directory
// Returns an absolute path: $HOME/pathElements[0]/pathElements[1]/...
// Example: JoinHomePath(".vcli", "config.yaml") -> "/home/user/.vcli/config.yaml"
func JoinHomePath(pathElements ...string) (string, error) {
	home, err := GetHomeDir()
	if err != nil {
		return "", err
	}

	// Build full path
	fullPath := filepath.Join(home, filepath.Join(pathElements...))

	return fullPath, nil
}

// GetVCLIConfigDir returns the vcli configuration directory path
// Typically ~/.vcli
func GetVCLIConfigDir() (string, error) {
	return JoinHomePath(".vcli")
}

// GetVCLIConfigFile returns the vcli configuration file path
// Typically ~/.vcli/config.yaml
func GetVCLIConfigFile() (string, error) {
	return JoinHomePath(".vcli", "config.yaml")
}

// GetVCLIWorkflowsDir returns the vcli workflows directory path
// Typically ~/.vcli/workflows
func GetVCLIWorkflowsDir() (string, error) {
	return JoinHomePath(".vcli", "workflows")
}

// GetVCLIPluginsDir returns the vcli plugins directory path
// Typically ~/.vcli/plugins
func GetVCLIPluginsDir() (string, error) {
	return JoinHomePath(".vcli", "plugins")
}

// GetKubeconfigPath returns the default kubeconfig file path
// Typically ~/.kube/config
func GetKubeconfigPath() (string, error) {
	return JoinHomePath(".kube", "config")
}

// EnsureVCLIConfigDir creates the vcli configuration directory if it doesn't exist
// Returns nil if directory already exists or was created successfully
func EnsureVCLIConfigDir() error {
	configDir, err := GetVCLIConfigDir()
	if err != nil {
		return err
	}

	// MkdirAll is idempotent - no error if already exists
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return fmt.Errorf("failed to create vcli config directory: %w", err)
	}

	return nil
}

// EnsureVCLIWorkflowsDir creates the vcli workflows directory if it doesn't exist
func EnsureVCLIWorkflowsDir() error {
	workflowsDir, err := GetVCLIWorkflowsDir()
	if err != nil {
		return err
	}

	if err := os.MkdirAll(workflowsDir, 0755); err != nil {
		return fmt.Errorf("failed to create vcli workflows directory: %w", err)
	}

	return nil
}

// EnsureVCLIPluginsDir creates the vcli plugins directory if it doesn't exist
func EnsureVCLIPluginsDir() error {
	pluginsDir, err := GetVCLIPluginsDir()
	if err != nil {
		return err
	}

	if err := os.MkdirAll(pluginsDir, 0755); err != nil {
		return fmt.Errorf("failed to create vcli plugins directory: %w", err)
	}

	return nil
}
