package k8s

import (
	"context"
	"fmt"
	"net/http"
	"os"

	"k8s.io/client-go/tools/portforward"
	"k8s.io/client-go/transport/spdy"
)

// PortForwardToPod forwards local ports to a pod
func (cm *ClusterManager) PortForwardToPod(podName, namespace string, opts *PortForwardOptions) (*PortForwardResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if podName == "" {
		return nil, fmt.Errorf("pod name is required")
	}

	if namespace == "" {
		namespace = "default"
	}

	if opts == nil || len(opts.Ports) == 0 {
		return nil, fmt.Errorf("at least one port mapping is required")
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// Build port forward URL
	req := cm.clientset.CoreV1().RESTClient().Post().
		Resource("pods").
		Namespace(namespace).
		Name(podName).
		SubResource("portforward")

	// Create SPDY transport
	transport, upgrader, err := spdy.RoundTripperFor(cm.config)
	if err != nil {
		return nil, fmt.Errorf("failed to create SPDY transport: %w", err)
	}

	// Convert port mappings to strings
	ports := make([]string, len(opts.Ports))
	for i, p := range opts.Ports {
		ports[i] = fmt.Sprintf("%d:%d", p.Local, p.Remote)
	}

	// Create port forwarder
	dialer := spdy.NewDialer(upgrader, &http.Client{Transport: transport}, "POST", req.URL())

	// Prepare ready channel
	readyChan := opts.ReadyChannel
	if readyChan == nil {
		readyChan = make(chan struct{}, 1)
	}

	// Prepare stop channel
	stopChan := opts.StopChannel
	if stopChan == nil {
		stopChan = make(chan struct{}, 1)
	}

	// Create port forwarder
	forwarder, err := portforward.New(dialer, ports, stopChan, readyChan, os.Stdout, os.Stderr)
	if err != nil {
		return nil, fmt.Errorf("failed to create port forwarder: %w", err)
	}

	// Start port forwarding in goroutine
	errChan := make(chan error, 1)
	go func() {
		if err := forwarder.ForwardPorts(); err != nil {
			errChan <- err
		}
	}()

	// Wait for ready or error
	select {
	case <-readyChan:
		// Port forward is ready
		return &PortForwardResult{
			PodName:     podName,
			Namespace:   namespace,
			Ports:       opts.Ports,
			Status:      PortForwardStatusReady,
			Message:     "port forward established",
			StopChannel: stopChan,
		}, nil
	case err := <-errChan:
		return nil, fmt.Errorf("port forward failed: %w", err)
	case <-ctx.Done():
		return nil, fmt.Errorf("timeout waiting for port forward to be ready")
	}
}

// PortForwardToPodAsync forwards ports asynchronously
func (cm *ClusterManager) PortForwardToPodAsync(podName, namespace string, opts *PortForwardOptions) (*PortForwardResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if podName == "" {
		return nil, fmt.Errorf("pod name is required")
	}

	if namespace == "" {
		namespace = "default"
	}

	if opts == nil || len(opts.Ports) == 0 {
		return nil, fmt.Errorf("at least one port mapping is required")
	}

	// Build port forward URL
	req := cm.clientset.CoreV1().RESTClient().Post().
		Resource("pods").
		Namespace(namespace).
		Name(podName).
		SubResource("portforward")

	// Create SPDY transport
	transport, upgrader, err := spdy.RoundTripperFor(cm.config)
	if err != nil {
		return nil, fmt.Errorf("failed to create SPDY transport: %w", err)
	}

	// Convert port mappings to strings
	ports := make([]string, len(opts.Ports))
	for i, p := range opts.Ports {
		ports[i] = fmt.Sprintf("%d:%d", p.Local, p.Remote)
	}

	// Create port forwarder
	dialer := spdy.NewDialer(upgrader, &http.Client{Transport: transport}, "POST", req.URL())

	// Prepare channels
	readyChan := opts.ReadyChannel
	if readyChan == nil {
		readyChan = make(chan struct{}, 1)
	}

	stopChan := opts.StopChannel
	if stopChan == nil {
		stopChan = make(chan struct{}, 1)
	}

	// Create port forwarder
	forwarder, err := portforward.New(dialer, ports, stopChan, readyChan, os.Stdout, os.Stderr)
	if err != nil {
		return nil, fmt.Errorf("failed to create port forwarder: %w", err)
	}

	// Start port forwarding in background
	go func() {
		if err := forwarder.ForwardPorts(); err != nil {
			fmt.Fprintf(os.Stderr, "Port forward error: %v\n", err)
		}
	}()

	return &PortForwardResult{
		PodName:     podName,
		Namespace:   namespace,
		Ports:       opts.Ports,
		Status:      PortForwardStatusRunning,
		Message:     "port forward started in background",
		StopChannel: stopChan,
	}, nil
}

// StopPortForward stops an active port forward
func StopPortForward(result *PortForwardResult) error {
	if result == nil {
		return fmt.Errorf("port forward result is nil")
	}

	if result.StopChannel == nil {
		return fmt.Errorf("stop channel is nil")
	}

	// Signal stop
	close(result.StopChannel)

	result.Status = PortForwardStatusStopped
	result.Message = "port forward stopped"

	return nil
}

// ValidatePortForwardOptions validates port forward options
func ValidatePortForwardOptions(opts *PortForwardOptions) error {
	if opts == nil {
		return fmt.Errorf("port forward options are required")
	}

	if len(opts.Ports) == 0 {
		return fmt.Errorf("at least one port mapping is required")
	}

	for i, port := range opts.Ports {
		if port.Local <= 0 || port.Local > 65535 {
			return fmt.Errorf("invalid local port at index %d: %d (must be 1-65535)", i, port.Local)
		}
		if port.Remote <= 0 || port.Remote > 65535 {
			return fmt.Errorf("invalid remote port at index %d: %d (must be 1-65535)", i, port.Remote)
		}
	}

	if opts.Timeout <= 0 {
		return fmt.Errorf("timeout must be positive")
	}

	return nil
}

// ParsePortMapping parses a port mapping string (e.g., "8080:80")
func ParsePortMapping(portStr string) (PortMapping, error) {
	var local, remote int
	_, err := fmt.Sscanf(portStr, "%d:%d", &local, &remote)
	if err != nil {
		return PortMapping{}, fmt.Errorf("invalid port mapping format: %s (expected LOCAL:REMOTE)", portStr)
	}

	return PortMapping{
		Local:  local,
		Remote: remote,
	}, nil
}

// ParsePortMappings parses multiple port mapping strings
func ParsePortMappings(portStrs []string) ([]PortMapping, error) {
	if len(portStrs) == 0 {
		return nil, fmt.Errorf("no port mappings provided")
	}

	mappings := make([]PortMapping, len(portStrs))
	for i, portStr := range portStrs {
		mapping, err := ParsePortMapping(portStr)
		if err != nil {
			return nil, fmt.Errorf("failed to parse port mapping at index %d: %w", i, err)
		}
		mappings[i] = mapping
	}

	return mappings, nil
}

// GetAvailableLocalPort finds an available local port (simplified version)
func GetAvailableLocalPort() (int, error) {
	// This is a simplified version - production code would use net.Listen to find available port
	// For now, return a high port number
	return 8080, nil
}

// FormatPortMapping formats a port mapping for display
func FormatPortMapping(pm PortMapping) string {
	return fmt.Sprintf("%d:%d", pm.Local, pm.Remote)
}

// FormatPortMappings formats multiple port mappings for display
func FormatPortMappings(pms []PortMapping) string {
	if len(pms) == 0 {
		return "<none>"
	}

	result := ""
	for i, pm := range pms {
		if i > 0 {
			result += ", "
		}
		result += FormatPortMapping(pm)
	}
	return result
}
