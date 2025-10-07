package investigation

import (
	"fmt"
	"strings"

	"github.com/verticedev/vcli-go/internal/visual"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
)

// ResourceType represents the type of Kubernetes resource
type ResourceType int

const (
	ResourceTypeNamespace ResourceType = iota
	ResourceTypeDeployment
	ResourceTypeReplicaSet
	ResourceTypePod
	ResourceTypeService
)

// TreeNode represents a node in the resource tree
type TreeNode struct {
	Type     ResourceType
	Name     string
	Status   string
	Children []*TreeNode
	Expanded bool
	Metadata map[string]string
}

// ResourceTree manages the resource tree view
type ResourceTree struct {
	root      *TreeNode
	selected  *TreeNode
	cursor    int
	flatList  []*TreeNode
	styles    *visual.Styles
	palette   *visual.VerticePalette
}

// NewResourceTree creates a new resource tree
func NewResourceTree() *ResourceTree {
	return &ResourceTree{
		root: &TreeNode{
			Type:     ResourceTypeNamespace,
			Name:     "default",
			Expanded: true,
			Children: make([]*TreeNode, 0),
			Metadata: make(map[string]string),
		},
		flatList: make([]*TreeNode, 0),
		styles:   visual.DefaultStyles(),
		palette:  visual.DefaultPalette(),
		cursor:   0,
	}
}

// LoadFromCluster populates the tree from cluster data
func (t *ResourceTree) LoadFromCluster(deployments []appsv1.Deployment, pods []corev1.Pod, services []corev1.Service) {
	// Group resources by namespace
	namespaceMap := make(map[string]*TreeNode)

	// Create namespace nodes
	for _, deploy := range deployments {
		ns := deploy.Namespace
		if _, exists := namespaceMap[ns]; !exists {
			namespaceMap[ns] = &TreeNode{
				Type:     ResourceTypeNamespace,
				Name:     ns,
				Expanded: ns == "default",
				Children: make([]*TreeNode, 0),
				Metadata: make(map[string]string),
			}
		}
	}

	// Add deployments
	for _, deploy := range deployments {
		ns := deploy.Namespace
		status := fmt.Sprintf("%d/%d", deploy.Status.ReadyReplicas, deploy.Status.Replicas)

		deployNode := &TreeNode{
			Type:     ResourceTypeDeployment,
			Name:     deploy.Name,
			Status:   status,
			Expanded: false,
			Children: make([]*TreeNode, 0),
			Metadata: map[string]string{
				"namespace": ns,
				"replicas":  fmt.Sprintf("%d", deploy.Status.Replicas),
				"ready":     fmt.Sprintf("%d", deploy.Status.ReadyReplicas),
			},
		}

		// Find matching pods
		for _, pod := range pods {
			if pod.Namespace == ns {
				// Check if pod belongs to this deployment
				if owner := pod.OwnerReferences; len(owner) > 0 {
					podNode := &TreeNode{
						Type:   ResourceTypePod,
						Name:   pod.Name,
						Status: string(pod.Status.Phase),
						Metadata: map[string]string{
							"namespace": pod.Namespace,
							"node":      pod.Spec.NodeName,
							"phase":     string(pod.Status.Phase),
						},
					}
					deployNode.Children = append(deployNode.Children, podNode)
				}
			}
		}

		namespaceMap[ns].Children = append(namespaceMap[ns].Children, deployNode)
	}

	// Add services
	for _, svc := range services {
		ns := svc.Namespace
		if nsNode, exists := namespaceMap[ns]; exists {
			svcNode := &TreeNode{
				Type:   ResourceTypeService,
				Name:   svc.Name,
				Status: string(svc.Spec.Type),
				Metadata: map[string]string{
					"namespace":  ns,
					"clusterIP":  svc.Spec.ClusterIP,
					"type":       string(svc.Spec.Type),
				},
			}
			nsNode.Children = append(nsNode.Children, svcNode)
		}
	}

	// Build root
	t.root = &TreeNode{
		Type:     ResourceTypeNamespace,
		Name:     "cluster",
		Expanded: true,
		Children: make([]*TreeNode, 0),
		Metadata: make(map[string]string),
	}

	for _, ns := range namespaceMap {
		t.root.Children = append(t.root.Children, ns)
	}

	// Flatten for cursor navigation
	t.rebuildFlatList()
}

// rebuildFlatList rebuilds the flat list for cursor navigation
func (t *ResourceTree) rebuildFlatList() {
	t.flatList = make([]*TreeNode, 0)
	t.flattenNode(t.root, 0)

	// Set selected to first item if not set
	if t.selected == nil && len(t.flatList) > 0 {
		t.selected = t.flatList[0]
	}
}

// flattenNode recursively flattens the tree
func (t *ResourceTree) flattenNode(node *TreeNode, depth int) {
	if node == nil {
		return
	}

	t.flatList = append(t.flatList, node)

	if node.Expanded {
		for _, child := range node.Children {
			t.flattenNode(child, depth+1)
		}
	}
}

// Toggle toggles expansion of current node
func (t *ResourceTree) Toggle() {
	if t.selected != nil {
		t.selected.Expanded = !t.selected.Expanded
		t.rebuildFlatList()
	}
}

// MoveUp moves cursor up
func (t *ResourceTree) MoveUp() {
	if t.cursor > 0 {
		t.cursor--
		if t.cursor < len(t.flatList) {
			t.selected = t.flatList[t.cursor]
		}
	}
}

// MoveDown moves cursor down
func (t *ResourceTree) MoveDown() {
	if t.cursor < len(t.flatList)-1 {
		t.cursor++
		if t.cursor < len(t.flatList) {
			t.selected = t.flatList[t.cursor]
		}
	}
}

// GetSelected returns the currently selected node
func (t *ResourceTree) GetSelected() *TreeNode {
	return t.selected
}

// Render renders the tree view
func (t *ResourceTree) Render(width, height int) string {
	var output strings.Builder

	gradient := t.palette.PrimaryGradient()
	output.WriteString(visual.GradientText("📁 RESOURCE TREE", gradient))
	output.WriteString("\n")
	output.WriteString(t.styles.Muted.Render(strings.Repeat("─", width)))
	output.WriteString("\n")

	// Render visible nodes
	startIdx := 0
	endIdx := len(t.flatList)

	// Limit visible area
	maxVisible := height - 3
	if endIdx-startIdx > maxVisible {
		// Center cursor in view
		if t.cursor > maxVisible/2 {
			startIdx = t.cursor - maxVisible/2
			endIdx = startIdx + maxVisible
			if endIdx > len(t.flatList) {
				endIdx = len(t.flatList)
				startIdx = endIdx - maxVisible
			}
		} else {
			endIdx = maxVisible
		}
	}

	for i := startIdx; i < endIdx && i < len(t.flatList); i++ {
		node := t.flatList[i]
		depth := t.getDepth(node)

		line := t.renderNode(node, depth, i == t.cursor)
		output.WriteString(line)
		output.WriteString("\n")
	}

	return output.String()
}

// getDepth calculates the depth of a node
func (t *ResourceTree) getDepth(target *TreeNode) int {
	return t.getDepthRecursive(t.root, target, 0)
}

// getDepthRecursive recursively calculates depth
func (t *ResourceTree) getDepthRecursive(current, target *TreeNode, depth int) int {
	if current == target {
		return depth
	}

	for _, child := range current.Children {
		if result := t.getDepthRecursive(child, target, depth+1); result > 0 {
			return result
		}
	}

	return 0
}

// renderNode renders a single node
func (t *ResourceTree) renderNode(node *TreeNode, depth int, selected bool) string {
	// Indent
	indent := strings.Repeat("  ", depth)

	// Expand/collapse indicator
	indicator := "  "
	if len(node.Children) > 0 {
		if node.Expanded {
			indicator = "▼ "
		} else {
			indicator = "▶ "
		}
	}

	// Icon based on type
	icon := ""
	statusStyle := t.styles.Muted

	switch node.Type {
	case ResourceTypeNamespace:
		icon = "📁"
		statusStyle = t.styles.Accent
	case ResourceTypeDeployment:
		icon = "🚀"
		statusStyle = t.styles.Info
	case ResourceTypePod:
		icon = "📦"
		if node.Status == "Running" {
			statusStyle = t.styles.Success
		} else if node.Status == "Pending" {
			statusStyle = t.styles.Warning
		} else {
			statusStyle = t.styles.Error
		}
	case ResourceTypeService:
		icon = "🌐"
		statusStyle = t.styles.Info
	}

	// Name
	nameStyle := t.styles.Info
	if selected {
		nameStyle = t.styles.Accent.Bold(true)
	}

	// Build line
	line := fmt.Sprintf("%s%s%s %s",
		indent,
		indicator,
		icon,
		nameStyle.Render(node.Name))

	// Add status
	if node.Status != "" {
		line += fmt.Sprintf("  %s", statusStyle.Render(fmt.Sprintf("[%s]", node.Status)))
	}

	// Selection indicator
	if selected {
		line = t.styles.Accent.Render("❯ ") + line
	} else {
		line = "  " + line
	}

	return line
}
