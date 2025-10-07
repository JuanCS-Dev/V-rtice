package k8s

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes/scheme"
	"k8s.io/client-go/tools/remotecommand"
)

// ExecInPod executes a command in a pod
func (cm *ClusterManager) ExecInPod(podName, namespace string, opts *ExecOptions) (*ExecResult, error) {
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

	if opts == nil || len(opts.Command) == 0 {
		return nil, fmt.Errorf("command is required")
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// If no container specified, get first container
	container := opts.Container
	if container == "" {
		containers, err := cm.ListPodContainers(podName, namespace)
		if err != nil {
			return nil, fmt.Errorf("failed to get containers: %w", err)
		}
		if len(containers) == 0 {
			return nil, fmt.Errorf("no containers found in pod")
		}
		container = containers[0]
	}

	// Prepare exec request
	req := cm.clientset.CoreV1().RESTClient().Post().
		Resource("pods").
		Name(podName).
		Namespace(namespace).
		SubResource("exec")

	req.VersionedParams(&corev1.PodExecOptions{
		Container: container,
		Command:   opts.Command,
		Stdin:     opts.Stdin,
		Stdout:    opts.Stdout,
		Stderr:    opts.Stderr,
		TTY:       opts.TTY,
	}, scheme.ParameterCodec)

	// Create executor
	exec, err := remotecommand.NewSPDYExecutor(cm.config, "POST", req.URL())
	if err != nil {
		return nil, fmt.Errorf("failed to create executor: %w", err)
	}

	// Prepare streams
	var stdout, stderr bytes.Buffer
	var stdin io.Reader

	startTime := time.Now()

	// Execute command
	err = exec.StreamWithContext(ctx, remotecommand.StreamOptions{
		Stdin:  stdin,
		Stdout: &stdout,
		Stderr: &stderr,
		Tty:    opts.TTY,
	})

	duration := time.Since(startTime)

	result := &ExecResult{
		PodName:   podName,
		Namespace: namespace,
		Container: container,
		Command:   opts.Command,
		Stdout:    stdout.String(),
		Stderr:    stderr.String(),
		Duration:  duration,
		Error:     err,
	}

	if err != nil {
		result.ExitCode = 1
		return result, nil
	}

	result.ExitCode = 0
	return result, nil
}

// ExecInPodWithStreams executes a command with custom streams
func (cm *ClusterManager) ExecInPodWithStreams(podName, namespace string, opts *ExecOptions, stdin io.Reader, stdout, stderr io.Writer) error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return ErrNotConnected
	}

	if podName == "" {
		return fmt.Errorf("pod name is required")
	}

	if namespace == "" {
		namespace = "default"
	}

	if opts == nil || len(opts.Command) == 0 {
		return fmt.Errorf("command is required")
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// If no container specified, get first container
	container := opts.Container
	if container == "" {
		containers, err := cm.ListPodContainers(podName, namespace)
		if err != nil {
			return fmt.Errorf("failed to get containers: %w", err)
		}
		if len(containers) == 0 {
			return fmt.Errorf("no containers found in pod")
		}
		container = containers[0]
	}

	// Prepare exec request
	req := cm.clientset.CoreV1().RESTClient().Post().
		Resource("pods").
		Name(podName).
		Namespace(namespace).
		SubResource("exec")

	req.VersionedParams(&corev1.PodExecOptions{
		Container: container,
		Command:   opts.Command,
		Stdin:     opts.Stdin,
		Stdout:    opts.Stdout,
		Stderr:    opts.Stderr,
		TTY:       opts.TTY,
	}, scheme.ParameterCodec)

	// Create executor
	exec, err := remotecommand.NewSPDYExecutor(cm.config, "POST", req.URL())
	if err != nil {
		return fmt.Errorf("failed to create executor: %w", err)
	}

	// Execute command with provided streams
	err = exec.StreamWithContext(ctx, remotecommand.StreamOptions{
		Stdin:  stdin,
		Stdout: stdout,
		Stderr: stderr,
		Tty:    opts.TTY,
	})

	if err != nil {
		return fmt.Errorf("exec failed: %w", err)
	}

	return nil
}

// ExecCommand is a convenience method to execute a simple command and get output
func (cm *ClusterManager) ExecCommand(podName, namespace, container string, command []string) (string, error) {
	opts := NewExecOptions(command)
	opts.Container = container
	opts.Stdout = true
	opts.Stderr = true

	result, err := cm.ExecInPod(podName, namespace, opts)
	if err != nil {
		return "", err
	}

	if result.Error != nil {
		return "", fmt.Errorf("command failed: %w (stderr: %s)", result.Error, result.Stderr)
	}

	if result.ExitCode != 0 {
		return "", fmt.Errorf("command exited with code %d (stderr: %s)", result.ExitCode, result.Stderr)
	}

	return result.Stdout, nil
}

// ExecInteractive executes a command with interactive TTY
func (cm *ClusterManager) ExecInteractive(podName, namespace, container string, command []string) error {
	opts := NewExecOptions(command)
	opts.Container = container
	opts.Stdin = true
	opts.Stdout = true
	opts.Stderr = true
	opts.TTY = true

	// Note: For true interactive TTY, stdin/stdout/stderr should be connected to os.Stdin/Stdout/Stderr
	// This is typically handled by the CLI layer
	result, err := cm.ExecInPod(podName, namespace, opts)
	if err != nil {
		return err
	}

	if result.Error != nil {
		return fmt.Errorf("interactive exec failed: %w", result.Error)
	}

	return nil
}

// ValidateExecOptions validates exec options
func ValidateExecOptions(opts *ExecOptions) error {
	if opts == nil {
		return fmt.Errorf("exec options are required")
	}

	if len(opts.Command) == 0 {
		return fmt.Errorf("command is required")
	}

	if opts.Timeout <= 0 {
		return fmt.Errorf("timeout must be positive")
	}

	return nil
}
