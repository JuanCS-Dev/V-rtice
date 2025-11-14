package bubbletea

import (
	"fmt"
	"os"

	vcliFs "github.com/verticedev/vcli-go/internal/fs"
	"github.com/verticedev/vcli-go/internal/k8s"
)

// getStatusline returns the K8s context statusline if available
func (m *Model) getStatusline() string {
	// Try to get K8s context
	kubeconfigPath := getKubeconfigPath()
	if kubeconfigPath == "" {
		return "" // No kubeconfig, no statusline
	}

	// Load kubeconfig to get context
	config, err := k8s.LoadKubeconfig(kubeconfigPath)
	if err != nil {
		return "" // Failed to load, skip statusline
	}

	// Get current context
	currentContext := config.GetCurrentContext()
	if currentContext == "" {
		return "" // No current context
	}

	// Get context info
	contextInfo, err := config.GetContextInfo(currentContext)
	if err != nil {
		return "" // Failed to get context info
	}

	// Format: ⎈ context | namespace
	return fmt.Sprintf("⎈ %s │ %s",
		m.styles.Accent.Render(currentContext),
		m.styles.Info.Render(contextInfo.Namespace))
}

// getKubeconfigPath returns the kubeconfig path from env or default location
func getKubeconfigPath() string {
	// Try KUBECONFIG env var first
	if kubeconfig := os.Getenv("KUBECONFIG"); kubeconfig != "" {
		return kubeconfig
	}

	// Default to ~/.kube/config using fs helper
	kubeconfigPath, err := vcliFs.GetKubeconfigPath()
	if err != nil {
		// Non-fatal: return empty string
		return ""
	}

	// Check if file exists
	if _, err := os.Stat(kubeconfigPath); err != nil {
		return "" // File doesn't exist
	}

	return kubeconfigPath
}

// updateStatusline updates the statusline (call this periodically or on demand)
func (m *Model) updateStatusline() {
	m.statusline = m.getStatusline()
}
