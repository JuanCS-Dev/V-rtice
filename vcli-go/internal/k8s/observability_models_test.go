package k8s

import (
	"testing"
	"time"
)

// TestNewLogOptions tests the NewLogOptions constructor
func TestNewLogOptions(t *testing.T) {
	opts := NewLogOptions()

	if opts == nil {
		t.Fatal("NewLogOptions() returned nil")
	}

	if opts.Container != "" {
		t.Errorf("Container = %q, want empty string", opts.Container)
	}
	if opts.Follow {
		t.Error("Follow = true, want false")
	}
	if opts.Previous {
		t.Error("Previous = true, want false")
	}
	if opts.Timestamps {
		t.Error("Timestamps = true, want false")
	}
	if opts.SinceTime != nil {
		t.Error("SinceTime should be nil")
	}
	if opts.SinceSeconds != 0 {
		t.Errorf("SinceSeconds = %d, want 0", opts.SinceSeconds)
	}
	if opts.TailLines != 0 {
		t.Errorf("TailLines = %d, want 0", opts.TailLines)
	}
	if opts.LimitBytes != 0 {
		t.Errorf("LimitBytes = %d, want 0", opts.LimitBytes)
	}
	if opts.Timeout != 60*time.Second {
		t.Errorf("Timeout = %v, want 60s", opts.Timeout)
	}
}

// TestNewPodSelector tests the NewPodSelector constructor
func TestNewPodSelector(t *testing.T) {
	namespace := "test-namespace"
	selector := NewPodSelector(namespace)

	if selector == nil {
		t.Fatal("NewPodSelector() returned nil")
	}

	if selector.Namespace != namespace {
		t.Errorf("Namespace = %q, want %q", selector.Namespace, namespace)
	}
	if selector.Labels == nil {
		t.Error("Labels map should not be nil")
	}
	if len(selector.Labels) != 0 {
		t.Errorf("Labels length = %d, want 0", len(selector.Labels))
	}
	if selector.FieldSelector != "" {
		t.Errorf("FieldSelector = %q, want empty string", selector.FieldSelector)
	}
	if selector.Names == nil {
		t.Error("Names slice should not be nil")
	}
	if len(selector.Names) != 0 {
		t.Errorf("Names length = %d, want 0", len(selector.Names))
	}
}

// TestNewExecOptions tests the NewExecOptions constructor
func TestNewExecOptions(t *testing.T) {
	command := []string{"sh", "-c", "echo hello"}
	opts := NewExecOptions(command)

	if opts == nil {
		t.Fatal("NewExecOptions() returned nil")
	}

	if opts.Container != "" {
		t.Errorf("Container = %q, want empty string", opts.Container)
	}
	if opts.Command == nil {
		t.Fatal("Command should not be nil")
	}
	if len(opts.Command) != len(command) {
		t.Errorf("Command length = %d, want %d", len(opts.Command), len(command))
	}
	for i, cmd := range command {
		if opts.Command[i] != cmd {
			t.Errorf("Command[%d] = %q, want %q", i, opts.Command[i], cmd)
		}
	}
	if opts.Stdin {
		t.Error("Stdin = true, want false")
	}
	if !opts.Stdout {
		t.Error("Stdout = false, want true")
	}
	if !opts.Stderr {
		t.Error("Stderr = false, want true")
	}
	if opts.TTY {
		t.Error("TTY = true, want false")
	}
	if opts.Timeout != 60*time.Second {
		t.Errorf("Timeout = %v, want 60s", opts.Timeout)
	}
}

// TestNewPortForwardOptions tests the NewPortForwardOptions constructor
func TestNewPortForwardOptions(t *testing.T) {
	ports := []PortMapping{
		{Local: 8080, Remote: 80},
		{Local: 8443, Remote: 443},
	}
	opts := NewPortForwardOptions(ports)

	if opts == nil {
		t.Fatal("NewPortForwardOptions() returned nil")
	}

	if opts.Ports == nil {
		t.Fatal("Ports should not be nil")
	}
	if len(opts.Ports) != len(ports) {
		t.Errorf("Ports length = %d, want %d", len(opts.Ports), len(ports))
	}
	for i, port := range ports {
		if opts.Ports[i].Local != port.Local {
			t.Errorf("Ports[%d].Local = %d, want %d", i, opts.Ports[i].Local, port.Local)
		}
		if opts.Ports[i].Remote != port.Remote {
			t.Errorf("Ports[%d].Remote = %d, want %d", i, opts.Ports[i].Remote, port.Remote)
		}
	}
	if opts.StopChannel == nil {
		t.Error("StopChannel should not be nil")
	}
	if opts.ReadyChannel == nil {
		t.Error("ReadyChannel should not be nil")
	}
	if opts.Address != "localhost" {
		t.Errorf("Address = %q, want 'localhost'", opts.Address)
	}
	if opts.Timeout != 60*time.Second {
		t.Errorf("Timeout = %v, want 60s", opts.Timeout)
	}
}

// TestNewDescribeOptions tests the NewDescribeOptions constructor
func TestNewDescribeOptions(t *testing.T) {
	opts := NewDescribeOptions()

	if opts == nil {
		t.Fatal("NewDescribeOptions() returned nil")
	}

	if !opts.ShowEvents {
		t.Error("ShowEvents = false, want true")
	}
	if opts.ShowManagedFields {
		t.Error("ShowManagedFields = true, want false")
	}
	if opts.Timeout != 30*time.Second {
		t.Errorf("Timeout = %v, want 30s", opts.Timeout)
	}
}

// TestNewMetricsOptions tests the NewMetricsOptions constructor
func TestNewMetricsOptions(t *testing.T) {
	opts := NewMetricsOptions()

	if opts == nil {
		t.Fatal("NewMetricsOptions() returned nil")
	}

	if opts.AllNamespaces {
		t.Error("AllNamespaces = true, want false")
	}
	if opts.Selector == nil {
		t.Error("Selector map should not be nil")
	}
	if len(opts.Selector) != 0 {
		t.Errorf("Selector length = %d, want 0", len(opts.Selector))
	}
	if opts.Timeout != 30*time.Second {
		t.Errorf("Timeout = %v, want 30s", opts.Timeout)
	}
}

// TestNewWatchOptions tests the NewWatchOptions constructor
func TestNewWatchOptions(t *testing.T) {
	opts := NewWatchOptions()

	if opts == nil {
		t.Fatal("NewWatchOptions() returned nil")
	}

	if opts.ResourceVersion != "" {
		t.Errorf("ResourceVersion = %q, want empty string", opts.ResourceVersion)
	}
	if opts.Labels == nil {
		t.Error("Labels map should not be nil")
	}
	if len(opts.Labels) != 0 {
		t.Errorf("Labels length = %d, want 0", len(opts.Labels))
	}
	if opts.FieldSelector != "" {
		t.Errorf("FieldSelector = %q, want empty string", opts.FieldSelector)
	}
	if opts.TimeoutSeconds != 0 {
		t.Errorf("TimeoutSeconds = %d, want 0", opts.TimeoutSeconds)
	}
	if opts.Timeout != 0 {
		t.Errorf("Timeout = %v, want 0", opts.Timeout)
	}
}

// TestFormatCPU tests the FormatCPU function
func TestFormatCPU(t *testing.T) {
	tests := []struct {
		name       string
		millicores int64
		want       string
	}{
		{
			name:       "zero millicores",
			millicores: 0,
			want:       "0m",
		},
		{
			name:       "small value in millicores",
			millicores: 500,
			want:       "500m",
		},
		{
			name:       "exactly 1 core",
			millicores: 1000,
			want:       "1.00",
		},
		{
			name:       "1.5 cores",
			millicores: 1500,
			want:       "1.50",
		},
		{
			name:       "multiple cores",
			millicores: 3250,
			want:       "3.25",
		},
		{
			name:       "large value",
			millicores: 12000,
			want:       "12.00",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := FormatCPU(tt.millicores)
			if got != tt.want {
				t.Errorf("FormatCPU(%d) = %q, want %q", tt.millicores, got, tt.want)
			}
		})
	}
}

// TestFormatMemory tests the FormatMemory function
func TestFormatMemory(t *testing.T) {
	const (
		KB = 1024
		MB = 1024 * KB
		GB = 1024 * MB
	)

	tests := []struct {
		name  string
		bytes int64
		want  string
	}{
		{
			name:  "zero bytes",
			bytes: 0,
			want:  "0B",
		},
		{
			name:  "bytes only",
			bytes: 512,
			want:  "512B",
		},
		{
			name:  "exactly 1 KB",
			bytes: KB,
			want:  "1Ki",
		},
		{
			name:  "kilobytes",
			bytes: 512 * KB,
			want:  "512Ki",
		},
		{
			name:  "exactly 1 MB",
			bytes: MB,
			want:  "1Mi",
		},
		{
			name:  "megabytes",
			bytes: 256 * MB,
			want:  "256Mi",
		},
		{
			name:  "exactly 1 GB",
			bytes: GB,
			want:  "1.00Gi",
		},
		{
			name:  "gigabytes",
			bytes: 2*GB + 512*MB,
			want:  "2.50Gi",
		},
		{
			name:  "large gigabytes",
			bytes: 16 * GB,
			want:  "16.00Gi",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := FormatMemory(tt.bytes)
			if got != tt.want {
				t.Errorf("FormatMemory(%d) = %q, want %q", tt.bytes, got, tt.want)
			}
		})
	}
}

// TestPortForwardStatus_Constants tests port forward status constants
func TestPortForwardStatus_Constants(t *testing.T) {
	if PortForwardStatusReady != "ready" {
		t.Errorf("PortForwardStatusReady = %q, want 'ready'", PortForwardStatusReady)
	}
	if PortForwardStatusRunning != "running" {
		t.Errorf("PortForwardStatusRunning = %q, want 'running'", PortForwardStatusRunning)
	}
	if PortForwardStatusStopped != "stopped" {
		t.Errorf("PortForwardStatusStopped = %q, want 'stopped'", PortForwardStatusStopped)
	}
	if PortForwardStatusFailed != "failed" {
		t.Errorf("PortForwardStatusFailed = %q, want 'failed'", PortForwardStatusFailed)
	}
}

// TestWatchEventType_Constants tests watch event type constants
func TestWatchEventType_Constants(t *testing.T) {
	if WatchEventTypeAdded != "ADDED" {
		t.Errorf("WatchEventTypeAdded = %q, want 'ADDED'", WatchEventTypeAdded)
	}
	if WatchEventTypeModified != "MODIFIED" {
		t.Errorf("WatchEventTypeModified = %q, want 'MODIFIED'", WatchEventTypeModified)
	}
	if WatchEventTypeDeleted != "DELETED" {
		t.Errorf("WatchEventTypeDeleted = %q, want 'DELETED'", WatchEventTypeDeleted)
	}
	if WatchEventTypeError != "ERROR" {
		t.Errorf("WatchEventTypeError = %q, want 'ERROR'", WatchEventTypeError)
	}
	if WatchEventTypeBookmark != "BOOKMARK" {
		t.Errorf("WatchEventTypeBookmark = %q, want 'BOOKMARK'", WatchEventTypeBookmark)
	}
}

// TestLogOptions_Modification tests modifying log options
func TestLogOptions_Modification(t *testing.T) {
	opts := NewLogOptions()

	// Modify all fields
	opts.Container = "nginx"
	opts.Follow = true
	opts.Previous = true
	opts.Timestamps = true
	now := time.Now()
	opts.SinceTime = &now
	opts.SinceSeconds = 3600
	opts.TailLines = 100
	opts.LimitBytes = 1024
	opts.Timeout = 120 * time.Second

	// Verify modifications
	if opts.Container != "nginx" {
		t.Errorf("Container = %q, want 'nginx'", opts.Container)
	}
	if !opts.Follow {
		t.Error("Follow not set")
	}
	if !opts.Previous {
		t.Error("Previous not set")
	}
	if !opts.Timestamps {
		t.Error("Timestamps not set")
	}
	if opts.SinceTime == nil || !opts.SinceTime.Equal(now) {
		t.Error("SinceTime not set correctly")
	}
	if opts.SinceSeconds != 3600 {
		t.Errorf("SinceSeconds = %d, want 3600", opts.SinceSeconds)
	}
	if opts.TailLines != 100 {
		t.Errorf("TailLines = %d, want 100", opts.TailLines)
	}
	if opts.LimitBytes != 1024 {
		t.Errorf("LimitBytes = %d, want 1024", opts.LimitBytes)
	}
	if opts.Timeout != 120*time.Second {
		t.Errorf("Timeout = %v, want 120s", opts.Timeout)
	}
}

// TestExecOptions_Modification tests modifying exec options
func TestExecOptions_Modification(t *testing.T) {
	opts := NewExecOptions([]string{"ls"})

	opts.Container = "app"
	opts.Command = []string{"sh", "-c", "ls -la"}
	opts.Stdin = true
	opts.TTY = true

	if opts.Container != "app" {
		t.Errorf("Container = %q, want 'app'", opts.Container)
	}
	if len(opts.Command) != 3 {
		t.Errorf("Command length = %d, want 3", len(opts.Command))
	}
	if !opts.Stdin {
		t.Error("Stdin not set")
	}
	if !opts.TTY {
		t.Error("TTY not set")
	}
}

// TestMetricsOptions_Modification tests modifying metrics options
func TestMetricsOptions_Modification(t *testing.T) {
	opts := NewMetricsOptions()

	opts.AllNamespaces = true
	opts.Selector["app"] = "nginx"
	opts.Selector["env"] = "prod"
	opts.Timeout = 60 * time.Second

	if !opts.AllNamespaces {
		t.Error("AllNamespaces not set")
	}
	if len(opts.Selector) != 2 {
		t.Errorf("Selector length = %d, want 2", len(opts.Selector))
	}
	if opts.Selector["app"] != "nginx" {
		t.Errorf("Selector[app] = %q, want 'nginx'", opts.Selector["app"])
	}
	if opts.Timeout != 60*time.Second {
		t.Errorf("Timeout = %v, want 60s", opts.Timeout)
	}
}

// TestPodSelector_Modification tests modifying pod selector
func TestPodSelector_Modification(t *testing.T) {
	selector := NewPodSelector("default")

	selector.Labels["app"] = "web"
	selector.FieldSelector = "status.phase=Running"
	selector.Names = []string{"pod-1", "pod-2"}

	if len(selector.Labels) != 1 {
		t.Errorf("Labels length = %d, want 1", len(selector.Labels))
	}
	if selector.FieldSelector != "status.phase=Running" {
		t.Errorf("FieldSelector = %q", selector.FieldSelector)
	}
	if len(selector.Names) != 2 {
		t.Errorf("Names length = %d, want 2", len(selector.Names))
	}
}
