package situational

import (
	"context"
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"

	"github.com/verticedev/vcli-go/internal/visual"
	"github.com/verticedev/vcli-go/internal/workspace"
)

// TickMsg signals a refresh
type TickMsg time.Time

// DataMsg contains fetched cluster data
type DataMsg struct {
	Nodes      *corev1.NodeList
	Pods       *corev1.PodList
	Events     *corev1.EventList
	Error      error
	FetchTime  time.Time
}

// Workspace is the Situational Awareness workspace
type Workspace struct {
	workspace.BaseWorkspace
	styles    *visual.Styles
	palette   *visual.VerticePalette
	clientset *kubernetes.Clientset
	ctx       context.Context

	// Data
	nodes      *corev1.NodeList
	pods       *corev1.PodList
	events     *corev1.EventList
	lastFetch  time.Time
	fetchError error

	// UI state
	width      int
	height     int
	loading    bool
}

// New creates a new Situational Awareness workspace
func New() *Workspace {
	base := workspace.NewBaseWorkspace(
		"situational",
		"Situational",
		"🎯",
		"Real-time cluster monitoring and vital signs",
	)

	w := &Workspace{
		BaseWorkspace: base,
		styles:        visual.DefaultStyles(),
		palette:       visual.DefaultPalette(),
		ctx:           context.Background(),
		loading:       true,
		width:         80,
		height:        24,
	}

	// Initialize K8s client
	w.initClient()

	return w
}

// initClient initializes the Kubernetes client
func (w *Workspace) initClient() {
	// Load kubeconfig
	loadingRules := clientcmd.NewDefaultClientConfigLoadingRules()
	configOverrides := &clientcmd.ConfigOverrides{}
	kubeConfig := clientcmd.NewNonInteractiveDeferredLoadingClientConfig(loadingRules, configOverrides)

	config, err := kubeConfig.ClientConfig()
	if err != nil {
		w.fetchError = fmt.Errorf("failed to load kubeconfig: %w", err)
		return
	}

	// Create clientset
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		w.fetchError = fmt.Errorf("failed to create kubernetes client: %w", err)
		return
	}

	w.clientset = clientset
}

// Init initializes the workspace
func (w *Workspace) Init() tea.Cmd {
	return tea.Batch(
		w.fetchData(),
		w.tickCmd(),
	)
}

// Update handles messages
func (w *Workspace) Update(msg tea.Msg) (workspace.Workspace, tea.Cmd) {
	switch msg := msg.(type) {
	case TickMsg:
		// Auto-refresh timer
		return w, tea.Batch(
			w.fetchData(),
			w.tickCmd(),
		)

	case DataMsg:
		// Data fetched
		w.nodes = msg.Nodes
		w.pods = msg.Pods
		w.events = msg.Events
		w.fetchError = msg.Error
		w.lastFetch = msg.FetchTime
		w.loading = false
		return w, nil
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

	var output strings.Builder

	// Cluster overview
	output.WriteString(w.renderClusterOverview())
	output.WriteString("\n\n")

	// Vital signs
	output.WriteString(w.renderVitalSigns())
	output.WriteString("\n\n")

	// Event feed
	output.WriteString(w.renderEventFeed())

	return output.String()
}

// renderLoading renders loading state
func (w *Workspace) renderLoading() string {
	gradient := w.palette.PrimaryGradient()
	return fmt.Sprintf("\n\n%s\n\nFetching cluster data...\n",
		visual.GradientText("🎯 Situational Awareness", gradient))
}

// renderError renders error state
func (w *Workspace) renderError() string {
	return fmt.Sprintf("\n\n%s\n\n%s\n\nError: %v\n",
		w.styles.Error.Render("❌ Failed to connect to cluster"),
		w.styles.Muted.Render("Make sure kubectl is configured and cluster is accessible"),
		w.fetchError)
}

// renderClusterOverview renders cluster overview
func (w *Workspace) renderClusterOverview() string {
	gradient := w.palette.PrimaryGradient()

	nodeCount := 0
	if w.nodes != nil {
		nodeCount = len(w.nodes.Items)
	}

	podCount := 0
	runningPods := 0
	if w.pods != nil {
		podCount = len(w.pods.Items)
		for _, pod := range w.pods.Items {
			if pod.Status.Phase == corev1.PodRunning {
				runningPods++
			}
		}
	}

	return fmt.Sprintf("%s\n%s\n%s │ %s │ %s │ Last update: %s",
		visual.GradientText("🎯 Situational Awareness Dashboard", gradient),
		w.styles.Muted.Render(strings.Repeat("─", 80)),
		w.styles.Info.Render(fmt.Sprintf("Nodes: %d", nodeCount)),
		w.styles.Success.Render(fmt.Sprintf("Pods: %d/%d running", runningPods, podCount)),
		w.styles.Accent.Render("Auto-refresh: 5s"),
		w.styles.Muted.Render(w.lastFetch.Format("15:04:05")),
	)
}

// renderVitalSigns renders vital signs panel
func (w *Workspace) renderVitalSigns() string {
	var output strings.Builder

	output.WriteString(w.styles.Accent.Bold(true).Render("📊 VITAL SIGNS"))
	output.WriteString("\n")
	output.WriteString(w.styles.Muted.Render(strings.Repeat("─", 80)))
	output.WriteString("\n")

	if w.pods == nil {
		return output.String()
	}

	// Count pod statuses
	statusCounts := make(map[corev1.PodPhase]int)
	for _, pod := range w.pods.Items {
		statusCounts[pod.Status.Phase]++
	}

	// Display counts
	output.WriteString(fmt.Sprintf("%s: %s  ",
		w.styles.Success.Render("Running"),
		w.styles.Success.Bold(true).Render(fmt.Sprintf("%d", statusCounts[corev1.PodRunning]))))

	output.WriteString(fmt.Sprintf("%s: %s  ",
		w.styles.Warning.Render("Pending"),
		w.styles.Warning.Bold(true).Render(fmt.Sprintf("%d", statusCounts[corev1.PodPending]))))

	output.WriteString(fmt.Sprintf("%s: %s  ",
		w.styles.Error.Render("Failed"),
		w.styles.Error.Bold(true).Render(fmt.Sprintf("%d", statusCounts[corev1.PodFailed]))))

	output.WriteString(fmt.Sprintf("%s: %s",
		w.styles.Info.Render("Succeeded"),
		w.styles.Info.Bold(true).Render(fmt.Sprintf("%d", statusCounts[corev1.PodSucceeded]))))

	return output.String()
}

// renderEventFeed renders recent events
func (w *Workspace) renderEventFeed() string {
	var output strings.Builder

	output.WriteString(w.styles.Accent.Bold(true).Render("📡 EVENT FEED (Last 10)"))
	output.WriteString("\n")
	output.WriteString(w.styles.Muted.Render(strings.Repeat("─", 80)))
	output.WriteString("\n")

	if w.events == nil || len(w.events.Items) == 0 {
		output.WriteString(w.styles.Muted.Render("No recent events"))
		return output.String()
	}

	// Show last 10 events
	count := 0
	maxEvents := 10

	for i := len(w.events.Items) - 1; i >= 0 && count < maxEvents; i-- {
		event := w.events.Items[i]

		// Icon based on type
		icon := "ℹ️"
		style := w.styles.Info
		if event.Type == corev1.EventTypeWarning {
			icon = "⚠️"
			style = w.styles.Warning
		}

		// Format time
		timeStr := event.LastTimestamp.Format("15:04:05")
		if event.LastTimestamp.IsZero() {
			timeStr = event.EventTime.Format("15:04:05")
		}

		// Format message
		msg := event.Message
		if len(msg) > 60 {
			msg = msg[:57] + "..."
		}

		output.WriteString(fmt.Sprintf("%s %s  %s  %s\n",
			icon,
			w.styles.Muted.Render(timeStr),
			style.Render(event.Reason),
			w.styles.Muted.Render(msg),
		))

		count++
	}

	return output.String()
}

// tickCmd creates a tick command for auto-refresh
func (w *Workspace) tickCmd() tea.Cmd {
	return tea.Tick(5*time.Second, func(t time.Time) tea.Msg {
		return TickMsg(t)
	})
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

		// Fetch nodes
		nodes, err := w.clientset.CoreV1().Nodes().List(w.ctx, metav1.ListOptions{})
		if err != nil {
			return DataMsg{
				Error:     fmt.Errorf("failed to list nodes: %w", err),
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

		// Fetch events
		events, err := w.clientset.CoreV1().Events("").List(w.ctx, metav1.ListOptions{})
		if err != nil {
			return DataMsg{
				Error:     fmt.Errorf("failed to list events: %w", err),
				FetchTime: time.Now(),
			}
		}

		return DataMsg{
			Nodes:     nodes,
			Pods:      pods,
			Events:    events,
			FetchTime: time.Now(),
		}
	}
}
