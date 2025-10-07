package investigation

import (
	"context"
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"

	"github.com/verticedev/vcli-go/internal/visual"
	"github.com/verticedev/vcli-go/internal/workspace"
)

// ViewMode represents the current view mode
type ViewMode int

const (
	ViewModeTree ViewMode = iota
	ViewModeLogs
	ViewModeFilter
)

// DataMsg contains fetched cluster data
type DataMsg struct {
	Deployments []appsv1.Deployment
	Pods        []corev1.Pod
	Services    []corev1.Service
	Error       error
	FetchTime   time.Time
}

// LogsLoadedMsg indicates logs have been loaded
type LogsLoadedMsg struct {
	Success bool
	Error   error
}

// Workspace is the Investigation workspace
type Workspace struct {
	workspace.BaseWorkspace
	styles    *visual.Styles
	palette   *visual.VerticePalette
	clientset *kubernetes.Clientset
	ctx       context.Context

	// Data
	deployments []appsv1.Deployment
	pods        []corev1.Pod
	services    []corev1.Service
	lastFetch   time.Time
	fetchError  error

	// Components
	tree       *ResourceTree
	logViewer  *LogViewer

	// UI state
	width       int
	height      int
	loading     bool
	viewMode    ViewMode
	filterInput string
}

// New creates a new Investigation workspace
func New() *Workspace {
	base := workspace.NewBaseWorkspace(
		"investigation",
		"Investigation",
		"🔍",
		"Deep-dive resource inspection and log analysis",
	)

	w := &Workspace{
		BaseWorkspace: base,
		styles:        visual.DefaultStyles(),
		palette:       visual.DefaultPalette(),
		ctx:           context.Background(),
		loading:       true,
		width:         80,
		height:        24,
		viewMode:      ViewModeTree,
		tree:          NewResourceTree(),
		logViewer:     NewLogViewer(),
		filterInput:   "",
	}

	// Initialize K8s client
	w.initClient()

	return w
}

// initClient initializes the Kubernetes client
func (w *Workspace) initClient() {
	loadingRules := clientcmd.NewDefaultClientConfigLoadingRules()
	configOverrides := &clientcmd.ConfigOverrides{}
	kubeConfig := clientcmd.NewNonInteractiveDeferredLoadingClientConfig(loadingRules, configOverrides)

	config, err := kubeConfig.ClientConfig()
	if err != nil {
		w.fetchError = fmt.Errorf("failed to load kubeconfig: %w", err)
		return
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		w.fetchError = fmt.Errorf("failed to create kubernetes client: %w", err)
		return
	}

	w.clientset = clientset
}

// Init initializes the workspace
func (w *Workspace) Init() tea.Cmd {
	return w.fetchData()
}

// Update handles messages
func (w *Workspace) Update(msg tea.Msg) (workspace.Workspace, tea.Cmd) {
	switch msg := msg.(type) {
	case DataMsg:
		// Data fetched
		w.deployments = msg.Deployments
		w.pods = msg.Pods
		w.services = msg.Services
		w.fetchError = msg.Error
		w.lastFetch = msg.FetchTime
		w.loading = false

		// Load into tree
		w.tree.LoadFromCluster(w.deployments, w.pods, w.services)

		return w, nil

	case LogsLoadedMsg:
		if !msg.Success {
			w.fetchError = msg.Error
		}
		return w, nil

	case tea.KeyMsg:
		return w.handleKeyPress(msg)
	}

	return w, nil
}

// handleKeyPress handles keyboard input
func (w *Workspace) handleKeyPress(msg tea.KeyMsg) (workspace.Workspace, tea.Cmd) {
	switch w.viewMode {
	case ViewModeTree:
		return w.handleTreeKeys(msg)
	case ViewModeLogs:
		return w.handleLogsKeys(msg)
	case ViewModeFilter:
		return w.handleFilterKeys(msg)
	}
	return w, nil
}

// handleTreeKeys handles keys in tree view mode
func (w *Workspace) handleTreeKeys(msg tea.KeyMsg) (workspace.Workspace, tea.Cmd) {
	switch msg.String() {
	case "up", "k":
		w.tree.MoveUp()
	case "down", "j":
		w.tree.MoveDown()
	case "enter", " ":
		w.tree.Toggle()
	case "l":
		// Load logs for selected pod
		selected := w.tree.GetSelected()
		if selected != nil && selected.Type == ResourceTypePod {
			return w, w.loadLogs(
				selected.Metadata["namespace"],
				selected.Name,
				"", // Auto-detect container
			)
		}
	case "r":
		// Refresh data
		w.loading = true
		return w, w.fetchData()
	}
	return w, nil
}

// handleLogsKeys handles keys in logs view mode
func (w *Workspace) handleLogsKeys(msg tea.KeyMsg) (workspace.Workspace, tea.Cmd) {
	switch msg.String() {
	case "up", "k":
		w.logViewer.ScrollUp()
	case "down", "j":
		w.logViewer.ScrollDown()
	case "pgup":
		w.logViewer.PageUp(10)
	case "pgdown":
		w.logViewer.PageDown(10)
	case "f":
		w.logViewer.ToggleFollow()
	case "esc":
		// Return to tree view
		w.viewMode = ViewModeTree
	case "/":
		// Enter filter mode
		w.viewMode = ViewModeFilter
		w.filterInput = ""
	case "ctrl+x":
		// Clear filter
		w.logViewer.ClearFilter()
	}
	return w, nil
}

// handleFilterKeys handles keys in filter input mode
func (w *Workspace) handleFilterKeys(msg tea.KeyMsg) (workspace.Workspace, tea.Cmd) {
	switch msg.String() {
	case "esc":
		// Cancel filter
		w.viewMode = ViewModeLogs
		w.filterInput = ""
	case "enter":
		// Apply filter
		w.logViewer.SetFilter(w.filterInput)
		w.viewMode = ViewModeLogs
	case "backspace":
		if len(w.filterInput) > 0 {
			w.filterInput = w.filterInput[:len(w.filterInput)-1]
		}
	default:
		// Add character to filter
		if len(msg.String()) == 1 {
			w.filterInput += msg.String()
		}
	}
	return w, nil
}

// View renders the workspace
func (w *Workspace) View(width, height int) string {
	w.width = width
	w.height = height

	if w.loading {
		return w.renderLoading()
	}

	if w.fetchError != nil {
		return w.renderError()
	}

	// Split view: tree on left, logs/details on right
	leftWidth := width / 3
	rightWidth := width - leftWidth - 3 // Account for separator

	var output strings.Builder

	// Render header
	output.WriteString(w.renderHeader())
	output.WriteString("\n")

	// Calculate content height
	contentHeight := height - 4 // Header + footer

	// Render split view
	leftPane := w.renderLeftPane(leftWidth, contentHeight)
	rightPane := w.renderRightPane(rightWidth, contentHeight)

	// Combine panes side by side
	leftLines := strings.Split(leftPane, "\n")
	rightLines := strings.Split(rightPane, "\n")

	maxLines := len(leftLines)
	if len(rightLines) > maxLines {
		maxLines = len(rightLines)
	}

	for i := 0; i < maxLines && i < contentHeight; i++ {
		// Left pane
		if i < len(leftLines) {
			line := leftLines[i]
			// Pad to width
			if len(line) < leftWidth {
				line += strings.Repeat(" ", leftWidth-len(line))
			}
			output.WriteString(line)
		} else {
			output.WriteString(strings.Repeat(" ", leftWidth))
		}

		// Separator
		output.WriteString(" │ ")

		// Right pane
		if i < len(rightLines) {
			output.WriteString(rightLines[i])
		}

		output.WriteString("\n")
	}

	// Render footer
	output.WriteString(w.renderFooter())

	// Filter overlay if in filter mode
	if w.viewMode == ViewModeFilter {
		return w.renderFilterOverlay(output.String())
	}

	return output.String()
}

// renderLoading renders loading state
func (w *Workspace) renderLoading() string {
	gradient := w.palette.PrimaryGradient()
	return fmt.Sprintf("\n\n%s\n\nFetching cluster resources...\n",
		visual.GradientText("🔍 Investigation Workspace", gradient))
}

// renderError renders error state
func (w *Workspace) renderError() string {
	return fmt.Sprintf("\n\n%s\n\n%s\n\nError: %v\n",
		w.styles.Error.Render("❌ Failed to connect to cluster"),
		w.styles.Muted.Render("Make sure kubectl is configured and cluster is accessible"),
		w.fetchError)
}

// renderHeader renders the workspace header
func (w *Workspace) renderHeader() string {
	gradient := w.palette.PrimaryGradient()
	title := visual.GradientText("🔍 Investigation Workspace", gradient)

	info := fmt.Sprintf("Resources: %d deployments, %d pods, %d services │ Last update: %s",
		len(w.deployments),
		len(w.pods),
		len(w.services),
		w.lastFetch.Format("15:04:05"))

	return fmt.Sprintf("%s\n%s",
		title,
		w.styles.Muted.Render(info))
}

// renderLeftPane renders the left pane (tree view)
func (w *Workspace) renderLeftPane(width, height int) string {
	style := lipgloss.NewStyle().Width(width).Height(height)

	// Highlight if active
	if w.viewMode == ViewModeTree {
		style = style.BorderStyle(lipgloss.RoundedBorder()).
			BorderForeground(w.palette.Cyan.ToTermenv())
	}

	content := w.tree.Render(width-2, height-2)
	return style.Render(content)
}

// renderRightPane renders the right pane (logs or details)
func (w *Workspace) renderRightPane(width, height int) string {
	style := lipgloss.NewStyle().Width(width).Height(height)

	// Highlight if active
	if w.viewMode == ViewModeLogs {
		style = style.BorderStyle(lipgloss.RoundedBorder()).
			BorderForeground(w.palette.Cyan.ToTermenv())
	}

	var content string

	if w.viewMode == ViewModeLogs && w.logViewer.GetInfo() != "" {
		content = w.logViewer.Render(width-2, height-2)
	} else {
		// Show selected resource details
		selected := w.tree.GetSelected()
		if selected != nil {
			content = w.renderResourceDetails(selected, width-2, height-2)
		} else {
			gradient := w.palette.PrimaryGradient()
			content = visual.GradientText("📄 DETAILS\n", gradient)
			content += w.styles.Muted.Render("Select a resource to view details\nPress 'L' on a pod to view logs")
		}
	}

	return style.Render(content)
}

// renderResourceDetails renders details for a selected resource
func (w *Workspace) renderResourceDetails(node *TreeNode, width, height int) string {
	var output strings.Builder

	gradient := w.palette.PrimaryGradient()
	output.WriteString(visual.GradientText("📄 RESOURCE DETAILS", gradient))
	output.WriteString("\n")
	output.WriteString(w.styles.Muted.Render(strings.Repeat("─", width)))
	output.WriteString("\n\n")

	output.WriteString(w.styles.Accent.Bold(true).Render(node.Name))
	output.WriteString("\n\n")

	// Type
	typeStr := "Unknown"
	switch node.Type {
	case ResourceTypeNamespace:
		typeStr = "Namespace"
	case ResourceTypeDeployment:
		typeStr = "Deployment"
	case ResourceTypePod:
		typeStr = "Pod"
	case ResourceTypeService:
		typeStr = "Service"
	}
	output.WriteString(fmt.Sprintf("%s: %s\n", w.styles.Info.Render("Type"), typeStr))

	// Status
	if node.Status != "" {
		output.WriteString(fmt.Sprintf("%s: %s\n", w.styles.Info.Render("Status"), node.Status))
	}

	// Metadata
	if len(node.Metadata) > 0 {
		output.WriteString("\n")
		output.WriteString(w.styles.Accent.Render("Metadata:"))
		output.WriteString("\n")
		for key, value := range node.Metadata {
			output.WriteString(fmt.Sprintf("  %s: %s\n",
				w.styles.Muted.Render(key),
				value))
		}
	}

	// Children count
	if len(node.Children) > 0 {
		output.WriteString("\n")
		output.WriteString(fmt.Sprintf("%s: %d\n",
			w.styles.Info.Render("Children"),
			len(node.Children)))
	}

	// Hint for pods
	if node.Type == ResourceTypePod {
		output.WriteString("\n")
		output.WriteString(w.styles.Warning.Render("💡 Press 'L' to view pod logs"))
	}

	return output.String()
}

// renderFooter renders the workspace footer
func (w *Workspace) renderFooter() string {
	var shortcuts string

	switch w.viewMode {
	case ViewModeTree:
		shortcuts = "↑↓: Navigate │ Enter: Expand/Collapse │ L: View Logs │ R: Refresh"
	case ViewModeLogs:
		shortcuts = "↑↓: Scroll │ PgUp/PgDn: Page │ F: Follow │ /: Filter │ Ctrl+X: Clear Filter │ Esc: Back"
	case ViewModeFilter:
		shortcuts = "Type to filter │ Enter: Apply │ Esc: Cancel"
	}

	return w.styles.Muted.Render(shortcuts)
}

// renderFilterOverlay renders the filter input overlay
func (w *Workspace) renderFilterOverlay(content string) string {
	filterStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(w.palette.Warning.ToTermenv()).
		Padding(1, 2).
		Width(60).
		Align(lipgloss.Left)

	filterText := fmt.Sprintf("🔍 Filter Logs\n\n%s\n\n%s",
		w.styles.Accent.Render(w.filterInput+"_"),
		w.styles.Muted.Render("Enter: Apply │ Esc: Cancel"))

	filter := filterStyle.Render(filterText)

	return lipgloss.Place(w.width, w.height, lipgloss.Center, lipgloss.Center, filter, lipgloss.WithWhitespaceChars(" "))
}

// fetchData fetches cluster data
func (w *Workspace) fetchData() tea.Cmd {
	return func() tea.Msg {
		if w.clientset == nil {
			return DataMsg{
				Error:     fmt.Errorf("kubernetes client not initialized"),
				FetchTime: time.Now(),
			}
		}

		// Fetch deployments
		deployments, err := w.clientset.AppsV1().Deployments("").List(w.ctx, metav1.ListOptions{})
		if err != nil {
			return DataMsg{
				Error:     fmt.Errorf("failed to list deployments: %w", err),
				FetchTime: time.Now(),
			}
		}

		// Fetch pods
		pods, err := w.clientset.CoreV1().Pods("").List(w.ctx, metav1.ListOptions{})
		if err != nil {
			return DataMsg{
				Error:     fmt.Errorf("failed to list pods: %w", err),
				FetchTime: time.Now(),
			}
		}

		// Fetch services
		services, err := w.clientset.CoreV1().Services("").List(w.ctx, metav1.ListOptions{})
		if err != nil {
			return DataMsg{
				Error:     fmt.Errorf("failed to list services: %w", err),
				FetchTime: time.Now(),
			}
		}

		return DataMsg{
			Deployments: deployments.Items,
			Pods:        pods.Items,
			Services:    services.Items,
			FetchTime:   time.Now(),
		}
	}
}

// loadLogs loads logs for a pod
func (w *Workspace) loadLogs(namespace, podName, container string) tea.Cmd {
	return func() tea.Msg {
		if w.clientset == nil {
			return LogsLoadedMsg{
				Success: false,
				Error:   fmt.Errorf("kubernetes client not initialized"),
			}
		}

		// Load logs
		err := w.logViewer.LoadLogs(w.clientset, namespace, podName, container, 100)
		if err != nil {
			return LogsLoadedMsg{
				Success: false,
				Error:   err,
			}
		}

		// Switch to logs view
		w.viewMode = ViewModeLogs

		return LogsLoadedMsg{
			Success: true,
		}
	}
}
