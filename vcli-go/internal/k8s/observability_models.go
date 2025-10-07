package k8s

import (
	"fmt"
	"io"
	"time"
)

// ========================================================================
// LOG OPERATION MODELS
// ========================================================================

// LogOptions configures log retrieval operations
type LogOptions struct {
	// Container specifies which container to get logs from
	Container string
	// Follow streams logs in real-time
	Follow bool
	// Previous gets logs from previous container instance
	Previous bool
	// Timestamps includes timestamps in logs
	Timestamps bool
	// SinceTime gets logs since this time
	SinceTime *time.Time
	// SinceSeconds gets logs from last N seconds
	SinceSeconds int
	// TailLines gets last N lines of logs
	TailLines int
	// LimitBytes limits the amount of log data
	LimitBytes int
	// Timeout for log operation
	Timeout time.Duration
}

// NewLogOptions creates default log options
func NewLogOptions() *LogOptions {
	return &LogOptions{
		Container:    "",
		Follow:       false,
		Previous:     false,
		Timestamps:   false,
		SinceTime:    nil,
		SinceSeconds: 0,
		TailLines:    0,
		LimitBytes:   0,
		Timeout:      60 * time.Second,
	}
}

// LogResult represents the result of a log operation
type LogResult struct {
	// PodName is the pod name
	PodName string
	// Namespace is the pod namespace
	Namespace string
	// Container is the container name
	Container string
	// Stream is the log stream
	Stream io.ReadCloser
}

// PodSelector selects pods for operations
type PodSelector struct {
	// Namespace is the target namespace
	Namespace string
	// Labels are label selectors
	Labels map[string]string
	// FieldSelector is a field selector query
	FieldSelector string
	// Names are specific pod names
	Names []string
}

// NewPodSelector creates a new pod selector
func NewPodSelector(namespace string) *PodSelector {
	return &PodSelector{
		Namespace:     namespace,
		Labels:        make(map[string]string),
		FieldSelector: "",
		Names:         []string{},
	}
}

// ========================================================================
// EXEC OPERATION MODELS
// ========================================================================

// ExecOptions configures command execution in pods
type ExecOptions struct {
	// Container specifies which container to exec into
	Container string
	// Command is the command to execute
	Command []string
	// Stdin enables stdin
	Stdin bool
	// Stdout enables stdout
	Stdout bool
	// Stderr enables stderr
	Stderr bool
	// TTY allocates a TTY
	TTY bool
	// Timeout for exec operation
	Timeout time.Duration
}

// NewExecOptions creates default exec options
func NewExecOptions(command []string) *ExecOptions {
	return &ExecOptions{
		Container: "",
		Command:   command,
		Stdin:     false,
		Stdout:    true,
		Stderr:    true,
		TTY:       false,
		Timeout:   60 * time.Second,
	}
}

// ExecResult represents the result of an exec operation
type ExecResult struct {
	// PodName is the pod name
	PodName string
	// Namespace is the pod namespace
	Namespace string
	// Container is the container name
	Container string
	// Command is the executed command
	Command []string
	// ExitCode is the command exit code
	ExitCode int
	// Stdout is the captured stdout
	Stdout string
	// Stderr is the captured stderr
	Stderr string
	// Duration is how long the command took
	Duration time.Duration
	// Error contains any execution error
	Error error
}

// ========================================================================
// PORT-FORWARD OPERATION MODELS
// ========================================================================

// PortForwardOptions configures port forwarding
type PortForwardOptions struct {
	// Ports are the port mappings (local:remote)
	Ports []PortMapping
	// StopChannel can be used to stop port forwarding
	StopChannel chan struct{}
	// ReadyChannel signals when port forwarding is ready
	ReadyChannel chan struct{}
	// Address is the local address to bind to
	Address string
	// Timeout for establishing port forward
	Timeout time.Duration
}

// PortMapping represents a port mapping
type PortMapping struct {
	// Local is the local port
	Local int
	// Remote is the remote (pod) port
	Remote int
}

// NewPortForwardOptions creates default port forward options
func NewPortForwardOptions(ports []PortMapping) *PortForwardOptions {
	return &PortForwardOptions{
		Ports:        ports,
		StopChannel:  make(chan struct{}, 1),
		ReadyChannel: make(chan struct{}, 1),
		Address:      "localhost",
		Timeout:      60 * time.Second,
	}
}

// PortForwardResult represents the result of a port forward operation
type PortForwardResult struct {
	// PodName is the pod name
	PodName string
	// Namespace is the pod namespace
	Namespace string
	// Ports are the forwarded ports
	Ports []PortMapping
	// Status is the port forward status
	Status PortForwardStatus
	// Message provides additional information
	Message string
	// StopChannel can be used to stop the forward
	StopChannel chan struct{}
}

// PortForwardStatus represents port forward status
type PortForwardStatus string

const (
	// PortForwardStatusReady indicates port forward is ready
	PortForwardStatusReady PortForwardStatus = "ready"
	// PortForwardStatusRunning indicates port forward is running
	PortForwardStatusRunning PortForwardStatus = "running"
	// PortForwardStatusStopped indicates port forward stopped
	PortForwardStatusStopped PortForwardStatus = "stopped"
	// PortForwardStatusFailed indicates port forward failed
	PortForwardStatusFailed PortForwardStatus = "failed"
)

// ========================================================================
// DESCRIBE OPERATION MODELS
// ========================================================================

// DescribeOptions configures resource description
type DescribeOptions struct {
	// ShowEvents includes events in description
	ShowEvents bool
	// ShowManagedFields includes managed fields
	ShowManagedFields bool
	// Timeout for describe operation
	Timeout time.Duration
}

// NewDescribeOptions creates default describe options
func NewDescribeOptions() *DescribeOptions {
	return &DescribeOptions{
		ShowEvents:        true,
		ShowManagedFields: false,
		Timeout:           30 * time.Second,
	}
}

// DescribeResult represents the result of a describe operation
type DescribeResult struct {
	// Kind is the resource kind
	Kind string
	// Name is the resource name
	Name string
	// Namespace is the resource namespace
	Namespace string
	// Description is the formatted description
	Description string
	// Events are related events
	Events []Event
	// Raw is the raw resource data
	Raw map[string]interface{}
}

// Event represents a Kubernetes event
type Event struct {
	// Type is the event type (Normal, Warning)
	Type string
	// Reason is the event reason
	Reason string
	// Message is the event message
	Message string
	// Count is how many times this event occurred
	Count int32
	// FirstTimestamp is when the event first occurred
	FirstTimestamp time.Time
	// LastTimestamp is when the event last occurred
	LastTimestamp time.Time
	// Source is the event source
	Source string
}

// ========================================================================
// METRICS OPERATION MODELS
// ========================================================================

// MetricsOptions configures resource metrics retrieval
type MetricsOptions struct {
	// AllNamespaces gets metrics from all namespaces
	AllNamespaces bool
	// Selector filters resources by labels
	Selector map[string]string
	// Timeout for metrics operation
	Timeout time.Duration
}

// NewMetricsOptions creates default metrics options
func NewMetricsOptions() *MetricsOptions {
	return &MetricsOptions{
		AllNamespaces: false,
		Selector:      make(map[string]string),
		Timeout:       30 * time.Second,
	}
}

// PodMetrics represents pod resource metrics
type PodMetrics struct {
	// Name is the pod name
	Name string
	// Namespace is the pod namespace
	Namespace string
	// CPU usage in millicores
	CPUUsage int64
	// Memory usage in bytes
	MemoryUsage int64
	// Containers contains per-container metrics
	Containers []ContainerMetrics
	// Timestamp when metrics were collected
	Timestamp time.Time
}

// ContainerMetrics represents container resource metrics
type ContainerMetrics struct {
	// Name is the container name
	Name string
	// CPU usage in millicores
	CPUUsage int64
	// Memory usage in bytes
	MemoryUsage int64
}

// NodeMetrics represents node resource metrics
type NodeMetrics struct {
	// Name is the node name
	Name string
	// CPU usage in millicores
	CPUUsage int64
	// CPU capacity in millicores
	CPUCapacity int64
	// Memory usage in bytes
	MemoryUsage int64
	// Memory capacity in bytes
	MemoryCapacity int64
	// Timestamp when metrics were collected
	Timestamp time.Time
}

// FormatCPU formats CPU in human-readable format
func FormatCPU(millicores int64) string {
	if millicores < 1000 {
		return fmt.Sprintf("%dm", millicores)
	}
	return fmt.Sprintf("%.2f", float64(millicores)/1000.0)
}

// FormatMemory formats memory in human-readable format
func FormatMemory(bytes int64) string {
	const (
		KB = 1024
		MB = 1024 * KB
		GB = 1024 * MB
	)

	if bytes < KB {
		return fmt.Sprintf("%dB", bytes)
	} else if bytes < MB {
		return fmt.Sprintf("%dKi", bytes/KB)
	} else if bytes < GB {
		return fmt.Sprintf("%dMi", bytes/MB)
	}
	return fmt.Sprintf("%.2fGi", float64(bytes)/float64(GB))
}

// ========================================================================
// WATCH OPERATION MODELS
// ========================================================================

// WatchOptions configures watch operations
type WatchOptions struct {
	// ResourceVersion to start watching from
	ResourceVersion string
	// Labels filters resources by labels
	Labels map[string]string
	// FieldSelector filters resources by fields
	FieldSelector string
	// TimeoutSeconds is the watch timeout in seconds
	TimeoutSeconds int
	// Timeout is the overall operation timeout
	Timeout time.Duration
}

// NewWatchOptions creates default watch options
func NewWatchOptions() *WatchOptions {
	return &WatchOptions{
		ResourceVersion: "",
		Labels:          make(map[string]string),
		FieldSelector:   "",
		TimeoutSeconds:  0,
		Timeout:         0,
	}
}

// WatchEvent represents a watch event
type WatchEvent struct {
	// Type is the event type (ADDED, MODIFIED, DELETED)
	Type WatchEventType
	// Object is the resource object
	Object interface{}
	// Stop signals to stop watching
	Stop bool
}

// WatchEventType represents the type of watch event
type WatchEventType string

const (
	// WatchEventTypeAdded indicates resource was added
	WatchEventTypeAdded WatchEventType = "ADDED"
	// WatchEventTypeModified indicates resource was modified
	WatchEventTypeModified WatchEventType = "MODIFIED"
	// WatchEventTypeDeleted indicates resource was deleted
	WatchEventTypeDeleted WatchEventType = "DELETED"
	// WatchEventTypeError indicates an error occurred
	WatchEventTypeError WatchEventType = "ERROR"
	// WatchEventTypeBookmark indicates a bookmark event
	WatchEventTypeBookmark WatchEventType = "BOOKMARK"
)

// WatchEventHandler is a function that handles watch events
type WatchEventHandler func(event *WatchEvent) error

// WatchCondition is a function that checks if a condition is met
type WatchCondition func(event *WatchEvent) (bool, error)
