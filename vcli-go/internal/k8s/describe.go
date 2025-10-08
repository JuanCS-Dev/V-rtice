package k8s

import (
	"context"
	"fmt"
	"strings"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
)

// DescribeResource provides detailed information about a resource
func (cm *ClusterManager) DescribeResource(kind, name, namespace string, opts *DescribeOptions) (*DescribeResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if kind == "" || name == "" {
		return nil, fmt.Errorf("kind and name are required")
	}

	if opts == nil {
		opts = NewDescribeOptions()
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), opts.Timeout)
	defer cancel()

	// Get GVR for the resource
	obj := &unstructured.Unstructured{}
	obj.SetKind(kind)
	gvr, err := cm.getGVR(obj)
	if err != nil {
		return nil, fmt.Errorf("failed to get GVR for kind %s: %w", kind, err)
	}

	// Get the resource
	resourceInterface := cm.getDynamicResourceInterface(gvr, namespace)
	resource, err := resourceInterface.Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get %s/%s: %w", kind, name, err)
	}

	// Build description
	description := cm.buildDescription(resource, opts)

	// Get events if requested
	var events []Event
	if opts.ShowEvents {
		events, err = cm.getResourceEvents(ctx, kind, name, namespace)
		if err != nil {
			// Don't fail on event errors, just log them
			events = []Event{}
		}
	}

	return &DescribeResult{
		Kind:        kind,
		Name:        name,
		Namespace:   namespace,
		Description: description,
		Events:      events,
		Raw:         resource.Object,
	}, nil
}

// DescribePod provides detailed information about a pod
func (cm *ClusterManager) DescribePod(name, namespace string, opts *DescribeOptions) (*DescribeResult, error) {
	return cm.DescribeResource("Pod", name, namespace, opts)
}

// DescribeDeployment provides detailed information about a deployment
func (cm *ClusterManager) DescribeDeployment(name, namespace string, opts *DescribeOptions) (*DescribeResult, error) {
	return cm.DescribeResource("Deployment", name, namespace, opts)
}

// DescribeService provides detailed information about a service
func (cm *ClusterManager) DescribeService(name, namespace string, opts *DescribeOptions) (*DescribeResult, error) {
	return cm.DescribeResource("Service", name, namespace, opts)
}

// DescribeNode provides detailed information about a node
func (cm *ClusterManager) DescribeNode(name string, opts *DescribeOptions) (*DescribeResult, error) {
	return cm.DescribeResource("Node", name, "", opts)
}

// buildDescription builds a human-readable description of a resource
func (cm *ClusterManager) buildDescription(obj *unstructured.Unstructured, opts *DescribeOptions) string {
	var b strings.Builder

	// Header
	b.WriteString(fmt.Sprintf("Name:         %s\n", obj.GetName()))
	b.WriteString(fmt.Sprintf("Namespace:    %s\n", obj.GetNamespace()))
	if labels := obj.GetLabels(); len(labels) > 0 {
		b.WriteString(fmt.Sprintf("Labels:       %s\n", formatLabels(labels)))
	}
	if annotations := obj.GetAnnotations(); len(annotations) > 0 && opts.ShowManagedFields {
		b.WriteString(fmt.Sprintf("Annotations:  %s\n", formatAnnotations(annotations)))
	}

	// API version and kind
	b.WriteString(fmt.Sprintf("API Version:  %s\n", obj.GetAPIVersion()))
	b.WriteString(fmt.Sprintf("Kind:         %s\n", obj.GetKind()))

	// Metadata
	b.WriteString(fmt.Sprintf("Created:      %s\n", obj.GetCreationTimestamp().Format(time.RFC3339)))
	if uid := obj.GetUID(); uid != "" {
		b.WriteString(fmt.Sprintf("UID:          %s\n", uid))
	}
	if resourceVersion := obj.GetResourceVersion(); resourceVersion != "" {
		b.WriteString(fmt.Sprintf("Resource Version: %s\n", resourceVersion))
	}

	// Owner references
	if ownerRefs := obj.GetOwnerReferences(); len(ownerRefs) > 0 {
		b.WriteString("Controlled By:  ")
		for i, owner := range ownerRefs {
			if i > 0 {
				b.WriteString(", ")
			}
			b.WriteString(fmt.Sprintf("%s/%s", owner.Kind, owner.Name))
		}
		b.WriteString("\n")
	}

	// Spec
	if spec, ok, _ := unstructured.NestedMap(obj.Object, "spec"); ok && len(spec) > 0 {
		b.WriteString("\nSpec:\n")
		b.WriteString(formatNestedMap(spec, "  "))
	}

	// Status
	if status, ok, _ := unstructured.NestedMap(obj.Object, "status"); ok && len(status) > 0 {
		b.WriteString("\nStatus:\n")
		b.WriteString(formatNestedMap(status, "  "))
	}

	return b.String()
}

// getResourceEvents retrieves events related to a resource
func (cm *ClusterManager) getResourceEvents(ctx context.Context, kind, name, namespace string) ([]Event, error) {
	// Get events
	eventList, err := cm.clientset.CoreV1().Events(namespace).List(ctx, metav1.ListOptions{
		FieldSelector: fmt.Sprintf("involvedObject.kind=%s,involvedObject.name=%s", kind, name),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get events: %w", err)
	}

	// Convert to our Event type
	events := make([]Event, 0, len(eventList.Items))
	for _, e := range eventList.Items {
		events = append(events, Event{
			Type:           e.Type,
			Reason:         e.Reason,
			Message:        e.Message,
			Count:          e.Count,
			FirstTimestamp: e.FirstTimestamp.Time,
			LastTimestamp:  e.LastTimestamp.Time,
			Source:         e.Source.Component,
		})
	}

	return events, nil
}

// formatLabels formats labels for display
func formatLabels(labels map[string]string) string {
	if len(labels) == 0 {
		return "<none>"
	}

	parts := make([]string, 0, len(labels))
	for k, v := range labels {
		parts = append(parts, fmt.Sprintf("%s=%s", k, v))
	}
	return strings.Join(parts, ",")
}

// formatAnnotations formats annotations for display
func formatAnnotations(annotations map[string]string) string {
	if len(annotations) == 0 {
		return "<none>"
	}

	parts := make([]string, 0, len(annotations))
	for k, v := range annotations {
		if len(v) > 50 {
			v = v[:50] + "..."
		}
		parts = append(parts, fmt.Sprintf("%s=%s", k, v))
	}
	return strings.Join(parts, ",")
}

// formatNestedMap formats nested map for display
func formatNestedMap(m map[string]interface{}, indent string) string {
	if len(m) == 0 {
		return indent + "<none>\n"
	}

	var b strings.Builder
	for k, v := range m {
		b.WriteString(fmt.Sprintf("%s%s: ", indent, k))

		switch val := v.(type) {
		case map[string]interface{}:
			b.WriteString("\n")
			b.WriteString(formatNestedMap(val, indent+"  "))
		case []interface{}:
			if len(val) == 0 {
				b.WriteString("[]")
			} else {
				b.WriteString("\n")
				for i, item := range val {
					b.WriteString(fmt.Sprintf("%s  [%d]: ", indent, i))
					if itemMap, ok := item.(map[string]interface{}); ok {
						b.WriteString("\n")
						b.WriteString(formatNestedMap(itemMap, indent+"    "))
					} else {
						b.WriteString(fmt.Sprintf("%v\n", item))
					}
				}
			}
		case string:
			if strings.Contains(val, "\n") {
				b.WriteString("|\n")
				lines := strings.Split(val, "\n")
				for _, line := range lines {
					b.WriteString(fmt.Sprintf("%s  %s\n", indent, line))
				}
			} else {
				b.WriteString(fmt.Sprintf("%v\n", val))
			}
		default:
			b.WriteString(fmt.Sprintf("%v\n", val))
		}
	}

	return b.String()
}

// FormatEvents formats events for display
func FormatEvents(events []Event) string {
	if len(events) == 0 {
		return "Events: <none>\n"
	}

	var b strings.Builder
	b.WriteString("\nEvents:\n")
	b.WriteString("  Type    Reason              Age    From               Message\n")
	b.WriteString("  ----    ------              ---    ----               -------\n")

	for _, e := range events {
		age := time.Since(e.LastTimestamp)
		ageStr := formatDuration(age)

		eventType := e.Type
		if len(eventType) > 7 {
			eventType = eventType[:7]
		}

		reason := e.Reason
		if len(reason) > 18 {
			reason = reason[:18]
		}

		source := e.Source
		if len(source) > 18 {
			source = source[:18]
		}

		message := e.Message
		if len(message) > 50 {
			message = message[:47] + "..."
		}

		b.WriteString(fmt.Sprintf("  %-7s %-18s %-6s %-18s %s\n",
			eventType, reason, ageStr, source, message))
	}

	return b.String()
}

// formatDuration formats duration in human-readable format
func formatDuration(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%ds", int(d.Seconds()))
	} else if d < time.Hour {
		return fmt.Sprintf("%dm", int(d.Minutes()))
	} else if d < 24*time.Hour {
		return fmt.Sprintf("%dh", int(d.Hours()))
	}
	return fmt.Sprintf("%dd", int(d.Hours()/24))
}
