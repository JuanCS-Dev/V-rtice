package k8s

import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/charmbracelet/lipgloss"
	"gopkg.in/yaml.v3"
)

// OutputFormat represents the output format type
type OutputFormat string

const (
	// OutputFormatTable is the default kubectl-style table format
	OutputFormatTable OutputFormat = "table"
	// OutputFormatJSON outputs resources as JSON
	OutputFormatJSON OutputFormat = "json"
	// OutputFormatYAML outputs resources as YAML
	OutputFormatYAML OutputFormat = "yaml"
)

// Formatter defines the interface for formatting Kubernetes resources
type Formatter interface {
	// FormatPods formats a list of pods
	FormatPods(pods []Pod) (string, error)
	// FormatNamespaces formats a list of namespaces
	FormatNamespaces(namespaces []Namespace) (string, error)
	// FormatNodes formats a list of nodes
	FormatNodes(nodes []Node) (string, error)
	// FormatDeployments formats a list of deployments
	FormatDeployments(deployments []Deployment) (string, error)
	// FormatServices formats a list of services
	FormatServices(services []Service) (string, error)
	// FormatConfigMaps formats a list of configmaps
	FormatConfigMaps(configmaps []ConfigMap) (string, error)
	// FormatSecrets formats a list of secrets
	FormatSecrets(secrets []Secret) (string, error)
	// FormatNodeMetrics formats node metrics
	FormatNodeMetrics(metrics []NodeMetrics) (string, error)
	// FormatPodMetrics formats pod metrics
	FormatPodMetrics(metrics []PodMetrics, showContainers bool) (string, error)
}

// NewFormatter creates a new formatter based on the specified format
func NewFormatter(format OutputFormat) (Formatter, error) {
	switch format {
	case OutputFormatTable:
		return NewTableFormatter(), nil
	case OutputFormatJSON:
		return NewJSONFormatter(), nil
	case OutputFormatYAML:
		return NewYAMLFormatter(), nil
	default:
		return nil, fmt.Errorf("unsupported output format: %s", format)
	}
}

// ============================================================================
// TABLE FORMATTER
// ============================================================================

// TableFormatter formats resources as kubectl-style tables
type TableFormatter struct {
	// Color styles for different status types
	styleRunning    lipgloss.Style
	stylePending    lipgloss.Style
	styleFailed     lipgloss.Style
	styleSucceeded  lipgloss.Style
	styleUnknown    lipgloss.Style
	styleHeader     lipgloss.Style
	styleReady      lipgloss.Style
	styleNotReady   lipgloss.Style
}

// NewTableFormatter creates a new TableFormatter with design system colors
func NewTableFormatter() *TableFormatter {
	// Using design system palette from internal/visual/design_system.go
	return &TableFormatter{
		styleRunning:   lipgloss.NewStyle().Foreground(lipgloss.Color("#50FA7B")), // ColorSuccess (Green)
		stylePending:   lipgloss.NewStyle().Foreground(lipgloss.Color("#FFB86C")), // ColorWarning (Yellow)
		styleFailed:    lipgloss.NewStyle().Foreground(lipgloss.Color("#FF5555")), // ColorDanger (Red)
		styleSucceeded: lipgloss.NewStyle().Foreground(lipgloss.Color("#50FA7B")), // ColorSuccess (Green)
		styleUnknown:   lipgloss.NewStyle().Foreground(lipgloss.Color("#6C6C6C")), // ColorMuted (DarkGray)
		styleHeader:    lipgloss.NewStyle().Foreground(lipgloss.Color("#00D9FF")).Bold(true).Underline(true), // ColorPrimary (Cyan)
		styleReady:     lipgloss.NewStyle().Foreground(lipgloss.Color("#50FA7B")), // ColorSuccess (Green)
		styleNotReady:  lipgloss.NewStyle().Foreground(lipgloss.Color("#FF5555")), // ColorDanger (Red)
	}
}

// FormatPods formats pods as a table
func (tf *TableFormatter) FormatPods(pods []Pod) (string, error) {
	if len(pods) == 0 {
		return "No resources found.\n", nil
	}

	// Calculate column widths
	nameWidth := max(4, maxLen(pods, func(p Pod) string { return p.Name }))
	nsWidth := max(9, maxLen(pods, func(p Pod) string { return p.Namespace }))
	statusWidth := 7 // Fixed width for status
	nodeWidth := max(4, maxLen(pods, func(p Pod) string { return p.NodeName }))

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-*s  %-*s  %-*s  %s",
			nameWidth, "NAME",
			nsWidth, "NAMESPACE",
			statusWidth, "STATUS",
			nodeWidth, "NODE",
			"AGE"))

	// Rows
	var rows []string
	for _, pod := range pods {
		status := tf.colorizeStatus(string(pod.Phase))
		nodeName := pod.NodeName
		if nodeName == "" {
			nodeName = "<none>"
		}
		age := formatAge(pod.CreatedAt)

		row := fmt.Sprintf("%-*s  %-*s  %s  %-*s  %s",
			nameWidth, truncate(pod.Name, nameWidth),
			nsWidth, truncate(pod.Namespace, nsWidth),
			status,
			nodeWidth, truncate(nodeName, nodeWidth),
			age)
		rows = append(rows, row)
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// FormatNamespaces formats namespaces as a table
func (tf *TableFormatter) FormatNamespaces(namespaces []Namespace) (string, error) {
	if len(namespaces) == 0 {
		return "No resources found.\n", nil
	}

	// Calculate column widths
	nameWidth := max(4, maxLen(namespaces, func(ns Namespace) string { return ns.Name }))
	statusWidth := 7 // Fixed width for status

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-*s  %s",
			nameWidth, "NAME",
			statusWidth, "STATUS",
			"AGE"))

	// Rows
	var rows []string
	for _, ns := range namespaces {
		status := tf.colorizeStatus(ns.Status)
		age := formatAge(ns.CreatedAt)

		row := fmt.Sprintf("%-*s  %s  %s",
			nameWidth, truncate(ns.Name, nameWidth),
			status,
			age)
		rows = append(rows, row)
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// FormatNodes formats nodes as a table
func (tf *TableFormatter) FormatNodes(nodes []Node) (string, error) {
	if len(nodes) == 0 {
		return "No resources found.\n", nil
	}

	// Calculate column widths
	nameWidth := max(4, maxLen(nodes, func(n Node) string { return n.Name }))
	statusWidth := 7
	rolesWidth := max(5, maxLen(nodes, func(n Node) string { return strings.Join(n.Roles, ",") }))
	versionWidth := max(7, maxLen(nodes, func(n Node) string { return n.Version }))

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-*s  %-*s  %-*s  %s",
			nameWidth, "NAME",
			statusWidth, "STATUS",
			rolesWidth, "ROLES",
			versionWidth, "VERSION",
			"AGE"))

	// Rows
	var rows []string
	for _, node := range nodes {
		status := tf.colorizeStatus(node.Status)
		roles := strings.Join(node.Roles, ",")
		if roles == "" {
			roles = "<none>"
		}
		age := formatAge(node.CreatedAt)

		row := fmt.Sprintf("%-*s  %s  %-*s  %-*s  %s",
			nameWidth, truncate(node.Name, nameWidth),
			status,
			rolesWidth, truncate(roles, rolesWidth),
			versionWidth, truncate(node.Version, versionWidth),
			age)
		rows = append(rows, row)
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// FormatDeployments formats deployments as a table
func (tf *TableFormatter) FormatDeployments(deployments []Deployment) (string, error) {
	if len(deployments) == 0 {
		return "No resources found.\n", nil
	}

	// Calculate column widths
	nameWidth := max(4, maxLen(deployments, func(d Deployment) string { return d.Name }))
	nsWidth := max(9, maxLen(deployments, func(d Deployment) string { return d.Namespace }))

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-*s  %-10s  %-10s  %-10s  %s",
			nameWidth, "NAME",
			nsWidth, "NAMESPACE",
			"READY", "UP-TO-DATE", "AVAILABLE", "AGE"))

	// Rows
	var rows []string
	for _, dep := range deployments {
		ready := fmt.Sprintf("%d/%d", dep.ReadyReplicas, dep.Replicas)
		upToDate := fmt.Sprintf("%d", dep.UpdatedReplicas)
		available := fmt.Sprintf("%d", dep.AvailableReplicas)
		age := formatAge(dep.CreatedAt)

		// Colorize ready status
		readyColored := ready
		if dep.ReadyReplicas == dep.Replicas && dep.Replicas > 0 {
			readyColored = tf.styleReady.Render(ready)
		} else {
			readyColored = tf.styleNotReady.Render(ready)
		}

		row := fmt.Sprintf("%-*s  %-*s  %-10s  %-10s  %-10s  %s",
			nameWidth, truncate(dep.Name, nameWidth),
			nsWidth, truncate(dep.Namespace, nsWidth),
			readyColored,
			upToDate,
			available,
			age)
		rows = append(rows, row)
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// FormatServices formats services as a table
func (tf *TableFormatter) FormatServices(services []Service) (string, error) {
	if len(services) == 0 {
		return "No resources found.\n", nil
	}

	// Calculate column widths
	nameWidth := max(4, maxLen(services, func(s Service) string { return s.Name }))
	nsWidth := max(9, maxLen(services, func(s Service) string { return s.Namespace }))
	typeWidth := max(4, maxLen(services, func(s Service) string { return string(s.Type) }))
	clusterIPWidth := max(10, maxLen(services, func(s Service) string { return s.ClusterIP }))

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-*s  %-*s  %-*s  %-10s  %s",
			nameWidth, "NAME",
			nsWidth, "NAMESPACE",
			typeWidth, "TYPE",
			clusterIPWidth, "CLUSTER-IP",
			"PORTS",
			"AGE"))

	// Rows
	var rows []string
	for _, svc := range services {
		ports := formatServicePorts(svc.Ports)
		age := formatAge(svc.CreatedAt)

		row := fmt.Sprintf("%-*s  %-*s  %-*s  %-*s  %-10s  %s",
			nameWidth, truncate(svc.Name, nameWidth),
			nsWidth, truncate(svc.Namespace, nsWidth),
			typeWidth, string(svc.Type),
			clusterIPWidth, svc.ClusterIP,
			truncate(ports, 10),
			age)
		rows = append(rows, row)
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// FormatConfigMaps formats configmaps as a table
func (tf *TableFormatter) FormatConfigMaps(configmaps []ConfigMap) (string, error) {
	if len(configmaps) == 0 {
		return "No resources found.\n", nil
	}

	// Calculate column widths
	nameWidth := max(4, maxLen(configmaps, func(cm ConfigMap) string { return cm.Name }))
	nsWidth := max(9, maxLen(configmaps, func(cm ConfigMap) string { return cm.Namespace }))

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-*s  %-4s  %s",
			nameWidth, "NAME",
			nsWidth, "NAMESPACE",
			"DATA",
			"AGE"))

	// Rows
	var rows []string
	for _, cm := range configmaps {
		dataCount := len(cm.Data) + len(cm.BinaryData)
		age := formatAge(cm.CreatedAt)

		row := fmt.Sprintf("%-*s  %-*s  %-4d  %s",
			nameWidth, truncate(cm.Name, nameWidth),
			nsWidth, truncate(cm.Namespace, nsWidth),
			dataCount,
			age)
		rows = append(rows, row)
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// FormatSecrets formats secrets as a table
func (tf *TableFormatter) FormatSecrets(secrets []Secret) (string, error) {
	if len(secrets) == 0 {
		return "No resources found.\n", nil
	}

	// Calculate column widths
	nameWidth := max(4, maxLen(secrets, func(s Secret) string { return s.Name }))
	nsWidth := max(9, maxLen(secrets, func(s Secret) string { return s.Namespace }))
	typeWidth := max(4, maxLen(secrets, func(s Secret) string { return string(s.Type) }))

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-*s  %-*s  %-4s  %s",
			nameWidth, "NAME",
			nsWidth, "NAMESPACE",
			typeWidth, "TYPE",
			"DATA",
			"AGE"))

	// Rows
	var rows []string
	for _, secret := range secrets {
		dataCount := len(secret.Data)
		age := formatAge(secret.CreatedAt)

		row := fmt.Sprintf("%-*s  %-*s  %-*s  %-4d  %s",
			nameWidth, truncate(secret.Name, nameWidth),
			nsWidth, truncate(secret.Namespace, nsWidth),
			typeWidth, truncate(string(secret.Type), typeWidth),
			dataCount,
			age)
		rows = append(rows, row)
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// FormatNodeMetrics formats node metrics as a table
func (tf *TableFormatter) FormatNodeMetrics(metrics []NodeMetrics) (string, error) {
	if len(metrics) == 0 {
		return "No resources found.\n", nil
	}

	// Calculate column widths
	nameWidth := max(4, maxLen(metrics, func(m NodeMetrics) string { return m.Name }))

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-10s  %-10s",
			nameWidth, "NAME",
			"CPU(cores)",
			"MEMORY(bytes)"))

	// Rows
	var rows []string
	for _, m := range metrics {
		cpuStr := FormatCPU(m.CPUUsage)
		memStr := FormatMemory(m.MemoryUsage)

		row := fmt.Sprintf("%-*s  %-10s  %-10s",
			nameWidth, truncate(m.Name, nameWidth),
			cpuStr,
			memStr)
		rows = append(rows, row)
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// FormatPodMetrics formats pod metrics as a table
func (tf *TableFormatter) FormatPodMetrics(metrics []PodMetrics, showContainers bool) (string, error) {
	if len(metrics) == 0 {
		return "No resources found.\n", nil
	}

	if showContainers {
		return tf.formatPodMetricsWithContainers(metrics)
	}

	// Calculate column widths
	nameWidth := max(4, maxLen(metrics, func(m PodMetrics) string { return m.Name }))
	nsWidth := max(9, maxLen(metrics, func(m PodMetrics) string { return m.Namespace }))

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-*s  %-10s  %-10s",
			nameWidth, "NAME",
			nsWidth, "NAMESPACE",
			"CPU(cores)",
			"MEMORY(bytes)"))

	// Rows
	var rows []string
	for _, m := range metrics {
		cpuStr := FormatCPU(m.CPUUsage)
		memStr := FormatMemory(m.MemoryUsage)

		row := fmt.Sprintf("%-*s  %-*s  %-10s  %-10s",
			nameWidth, truncate(m.Name, nameWidth),
			nsWidth, truncate(m.Namespace, nsWidth),
			cpuStr,
			memStr)
		rows = append(rows, row)
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// formatPodMetricsWithContainers formats pod metrics showing individual containers
func (tf *TableFormatter) formatPodMetricsWithContainers(metrics []PodMetrics) (string, error) {
	if len(metrics) == 0 {
		return "No resources found.\n", nil
	}

	// Calculate column widths
	var allPodNames []string
	var allContainerNames []string
	for _, m := range metrics {
		allPodNames = append(allPodNames, m.Name)
		for _, c := range m.Containers {
			allContainerNames = append(allContainerNames, c.Name)
		}
	}

	podWidth := max(4, maxLenSlice(allPodNames))
	containerWidth := max(9, maxLenSlice(allContainerNames))

	// Header
	header := tf.styleHeader.Render(
		fmt.Sprintf("%-*s  %-*s  %-10s  %-10s",
			podWidth, "POD",
			containerWidth, "CONTAINER",
			"CPU(cores)",
			"MEMORY(bytes)"))

	// Rows
	var rows []string
	for _, m := range metrics {
		for _, c := range m.Containers {
			cpuStr := FormatCPU(c.CPUUsage)
			memStr := FormatMemory(c.MemoryUsage)

			row := fmt.Sprintf("%-*s  %-*s  %-10s  %-10s",
				podWidth, truncate(m.Name, podWidth),
				containerWidth, truncate(c.Name, containerWidth),
				cpuStr,
				memStr)
			rows = append(rows, row)
		}
	}

	return header + "\n" + strings.Join(rows, "\n") + "\n", nil
}

// colorizeStatus applies color to status based on its value
func (tf *TableFormatter) colorizeStatus(status string) string {
	// Normalize status to match exact width
	status = fmt.Sprintf("%-7s", status)

	switch strings.ToLower(strings.TrimSpace(status)) {
	case "running", "active", "ready":
		return tf.styleRunning.Render(status)
	case "pending", "waiting":
		return tf.stylePending.Render(status)
	case "failed", "error", "crashloopbackoff":
		return tf.styleFailed.Render(status)
	case "succeeded", "completed":
		return tf.styleSucceeded.Render(status)
	default:
		return tf.styleUnknown.Render(status)
	}
}

// ============================================================================
// JSON FORMATTER
// ============================================================================

// JSONFormatter formats resources as JSON
type JSONFormatter struct {
	// Indent controls whether to use indented JSON output
	Indent bool
}

// NewJSONFormatter creates a new JSONFormatter with pretty printing
func NewJSONFormatter() *JSONFormatter {
	return &JSONFormatter{
		Indent: true,
	}
}

// FormatPods formats pods as JSON
func (jf *JSONFormatter) FormatPods(pods []Pod) (string, error) {
	return jf.marshal(pods)
}

// FormatNamespaces formats namespaces as JSON
func (jf *JSONFormatter) FormatNamespaces(namespaces []Namespace) (string, error) {
	return jf.marshal(namespaces)
}

// FormatNodes formats nodes as JSON
func (jf *JSONFormatter) FormatNodes(nodes []Node) (string, error) {
	return jf.marshal(nodes)
}

// FormatDeployments formats deployments as JSON
func (jf *JSONFormatter) FormatDeployments(deployments []Deployment) (string, error) {
	return jf.marshal(deployments)
}

// FormatServices formats services as JSON
func (jf *JSONFormatter) FormatServices(services []Service) (string, error) {
	return jf.marshal(services)
}

// FormatConfigMaps formats configmaps as JSON
func (jf *JSONFormatter) FormatConfigMaps(configmaps []ConfigMap) (string, error) {
	return jf.marshal(configmaps)
}

// FormatSecrets formats secrets as JSON
func (jf *JSONFormatter) FormatSecrets(secrets []Secret) (string, error) {
	return jf.marshal(secrets)
}

// FormatNodeMetrics formats node metrics as JSON
func (jf *JSONFormatter) FormatNodeMetrics(metrics []NodeMetrics) (string, error) {
	return jf.marshal(metrics)
}

// FormatPodMetrics formats pod metrics as JSON
func (jf *JSONFormatter) FormatPodMetrics(metrics []PodMetrics, showContainers bool) (string, error) {
	return jf.marshal(metrics)
}

// marshal converts data to JSON string
func (jf *JSONFormatter) marshal(v interface{}) (string, error) {
	var data []byte
	var err error

	if jf.Indent {
		data, err = json.MarshalIndent(v, "", "  ")
	} else {
		data, err = json.Marshal(v)
	}

	if err != nil {
		return "", fmt.Errorf("failed to marshal JSON: %w", err)
	}

	return string(data) + "\n", nil
}

// ============================================================================
// YAML FORMATTER
// ============================================================================

// YAMLFormatter formats resources as YAML
type YAMLFormatter struct{}

// NewYAMLFormatter creates a new YAMLFormatter
func NewYAMLFormatter() *YAMLFormatter {
	return &YAMLFormatter{}
}

// FormatPods formats pods as YAML
func (yf *YAMLFormatter) FormatPods(pods []Pod) (string, error) {
	return yf.marshal(pods)
}

// FormatNamespaces formats namespaces as YAML
func (yf *YAMLFormatter) FormatNamespaces(namespaces []Namespace) (string, error) {
	return yf.marshal(namespaces)
}

// FormatNodes formats nodes as YAML
func (yf *YAMLFormatter) FormatNodes(nodes []Node) (string, error) {
	return yf.marshal(nodes)
}

// FormatDeployments formats deployments as YAML
func (yf *YAMLFormatter) FormatDeployments(deployments []Deployment) (string, error) {
	return yf.marshal(deployments)
}

// FormatServices formats services as YAML
func (yf *YAMLFormatter) FormatServices(services []Service) (string, error) {
	return yf.marshal(services)
}

// FormatConfigMaps formats configmaps as YAML
func (yf *YAMLFormatter) FormatConfigMaps(configmaps []ConfigMap) (string, error) {
	return yf.marshal(configmaps)
}

// FormatSecrets formats secrets as YAML
func (yf *YAMLFormatter) FormatSecrets(secrets []Secret) (string, error) {
	return yf.marshal(secrets)
}

// FormatNodeMetrics formats node metrics as YAML
func (yf *YAMLFormatter) FormatNodeMetrics(metrics []NodeMetrics) (string, error) {
	return yf.marshal(metrics)
}

// FormatPodMetrics formats pod metrics as YAML
func (yf *YAMLFormatter) FormatPodMetrics(metrics []PodMetrics, showContainers bool) (string, error) {
	return yf.marshal(metrics)
}

// marshal converts data to YAML string
func (yf *YAMLFormatter) marshal(v interface{}) (string, error) {
	data, err := yaml.Marshal(v)
	if err != nil {
		return "", fmt.Errorf("failed to marshal YAML: %w", err)
	}
	return string(data), nil
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

// formatAge formats a timestamp as a human-readable age
func formatAge(t time.Time) string {
	duration := time.Since(t)

	if duration < time.Minute {
		return fmt.Sprintf("%ds", int(duration.Seconds()))
	} else if duration < time.Hour {
		return fmt.Sprintf("%dm", int(duration.Minutes()))
	} else if duration < 24*time.Hour {
		return fmt.Sprintf("%dh", int(duration.Hours()))
	} else {
		days := int(duration.Hours() / 24)
		hours := int(duration.Hours()) % 24
		if hours > 0 {
			return fmt.Sprintf("%dd%dh", days, hours)
		}
		return fmt.Sprintf("%dd", days)
	}
}

// formatServicePorts formats service ports as a compact string
func formatServicePorts(ports []ServicePort) string {
	if len(ports) == 0 {
		return "<none>"
	}

	var parts []string
	for _, port := range ports {
		if port.NodePort > 0 {
			parts = append(parts, fmt.Sprintf("%d:%d/%s", port.Port, port.NodePort, port.Protocol))
		} else {
			parts = append(parts, fmt.Sprintf("%d/%s", port.Port, port.Protocol))
		}
	}

	// Sort for consistent output
	sort.Strings(parts)

	return strings.Join(parts, ",")
}

// truncate truncates a string to the specified length
func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	if maxLen <= 3 {
		return s[:maxLen]
	}
	return s[:maxLen-3] + "..."
}

// maxLen finds the maximum length of a string field across a slice
func maxLen[T any](items []T, getter func(T) string) int {
	maxLength := 0
	for _, item := range items {
		length := len(getter(item))
		if length > maxLength {
			maxLength = length
		}
	}
	return maxLength
}

// maxLenSlice finds the maximum length of strings in a slice
func maxLenSlice(items []string) int {
	maxLength := 0
	for _, item := range items {
		if len(item) > maxLength {
			maxLength = len(item)
		}
	}
	return maxLength
}

// max returns the maximum of two integers
func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

// Repr returns a string representation of the Formatter
func (tf *TableFormatter) Repr() string {
	return "TableFormatter{colorized=true}"
}

// Repr returns a string representation of the JSONFormatter
func (jf *JSONFormatter) Repr() string {
	return fmt.Sprintf("JSONFormatter{indent=%v}", jf.Indent)
}

// Repr returns a string representation of the YAMLFormatter
func (yf *YAMLFormatter) Repr() string {
	return "YAMLFormatter{}"
}
