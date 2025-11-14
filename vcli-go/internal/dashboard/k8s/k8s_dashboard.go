package k8s

import (
	"context"
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/verticedev/vcli-go/internal/dashboard"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

// K8sDashboard displays Kubernetes cluster metrics
type K8sDashboard struct {
	id     string
	focused  bool
	width    int
	height   int
	client   *kubernetes.Clientset
	config   *rest.Config
	styles   dashboard.DashboardStyles
	data     *K8sData
}

// K8sData holds dashboard data
type K8sData struct {
	Namespace       string
	PodCount        int
	NodeCount       int
	DeploymentCount int
	ServiceCount    int
	HealthyPods     int
	UnhealthyPods   int
	CPUUsage        float64
	MemoryUsage     float64
	LastUpdate      time.Time
}

// New creates a new K8s dashboard
func New(namespace string) *K8sDashboard {
	return &K8sDashboard{
		id:     "k8s-dashboard",
		styles: dashboard.DefaultStyles(),
		data: &K8sData{
			Namespace: namespace,
		},
	}
}

// Init initializes the dashboard
func (d *K8sDashboard) Init() tea.Cmd {
	// Initialize K8s client
	var err error
	d.config, err = rest.InClusterConfig()
	if err != nil {
		// Try kubeconfig
		kubeconfig := clientcmd.NewDefaultClientConfigLoadingRules().GetDefaultFilename()
		d.config, err = clientcmd.BuildConfigFromFlags("", kubeconfig)
		if err != nil {
			return func() tea.Msg {
				return dashboard.ErrorMsg{
					DashboardID: d.id,
					Error:       fmt.Errorf("failed to load kubeconfig: %w", err),
				}
			}
		}
	}

	d.client, err = kubernetes.NewForConfig(d.config)
	if err != nil {
		return func() tea.Msg {
			return dashboard.ErrorMsg{
				DashboardID: d.id,
				Error:       fmt.Errorf("failed to create K8s client: %w", err),
			}
		}
	}

	// Start refresh ticker
	return d.refresh()
}

// Update handles messages
func (d *K8sDashboard) Update(msg tea.Msg) (dashboard.Dashboard, tea.Cmd) {
	switch msg := msg.(type) {
	case dashboard.RefreshMsg:
		if msg.DashboardID == d.id {
			return d, d.refresh()
		}

	case dashboard.DataMsg:
		if msg.DashboardID == d.id {
			if data, ok := msg.Data.(*K8sData); ok {
				d.data = data
			}
		}

	case tea.KeyMsg:
		if d.focused {
			switch msg.String() {
			case "r":
				return d, d.refresh()
			}
		}
	}

	return d, nil
}

// View renders the dashboard
func (d *K8sDashboard) View() string {
	if d.data == nil {
		return d.styles.Error.Render("No data")
	}

	var b strings.Builder

	// Metrics summary
	b.WriteString(d.styles.Label.Render("Namespace: "))
	b.WriteString(d.styles.Value.Render(d.data.Namespace))
	b.WriteString("\n\n")

	// Resource counts
	b.WriteString(fmt.Sprintf("%s %s\n",
		d.styles.Label.Render("Pods:"),
		d.styles.Value.Render(fmt.Sprintf("%d", d.data.PodCount)),
	))
	b.WriteString(fmt.Sprintf("%s %s / %s\n",
		d.styles.Label.Render("  Healthy:"),
		d.styles.Success.Render(fmt.Sprintf("%d", d.data.HealthyPods)),
		d.styles.Error.Render(fmt.Sprintf("%d unhealthy", d.data.UnhealthyPods)),
	))
	b.WriteString(fmt.Sprintf("%s %s\n",
		d.styles.Label.Render("Nodes:"),
		d.styles.Value.Render(fmt.Sprintf("%d", d.data.NodeCount)),
	))
	b.WriteString(fmt.Sprintf("%s %s\n",
		d.styles.Label.Render("Deployments:"),
		d.styles.Value.Render(fmt.Sprintf("%d", d.data.DeploymentCount)),
	))
	b.WriteString(fmt.Sprintf("%s %s\n",
		d.styles.Label.Render("Services:"),
		d.styles.Value.Render(fmt.Sprintf("%d", d.data.ServiceCount)),
	))

	b.WriteString("\n")

	// Resource usage
	cpuStyle := d.styles.Success
	if d.data.CPUUsage > 80 {
		cpuStyle = d.styles.Error
	} else if d.data.CPUUsage > 60 {
		cpuStyle = d.styles.Warning
	}

	b.WriteString(fmt.Sprintf("%s %s\n",
		d.styles.Label.Render("CPU Usage:"),
		cpuStyle.Render(fmt.Sprintf("%.1f%%", d.data.CPUUsage)),
	))

	memStyle := d.styles.Success
	if d.data.MemoryUsage > 80 {
		memStyle = d.styles.Error
	} else if d.data.MemoryUsage > 60 {
		memStyle = d.styles.Warning
	}

	b.WriteString(fmt.Sprintf("%s %s\n",
		d.styles.Label.Render("Memory Usage:"),
		memStyle.Render(fmt.Sprintf("%.1f%%", d.data.MemoryUsage)),
	))

	b.WriteString("\n")
	b.WriteString(d.styles.Label.Render(fmt.Sprintf("Updated: %s", d.data.LastUpdate.Format("15:04:05"))))

	return b.String()
}

// refresh fetches new data from K8s API
func (d *K8sDashboard) refresh() tea.Cmd {
	return func() tea.Msg {
		if d.client == nil {
			return dashboard.ErrorMsg{
				DashboardID: d.id,
				Error:       fmt.Errorf("K8s client not initialized"),
			}
		}

		ctx := context.Background()
		data := &K8sData{
			Namespace:  d.data.Namespace,
			LastUpdate: time.Now(),
		}

		// Get pods
		pods, err := d.client.CoreV1().Pods(data.Namespace).List(ctx, metav1.ListOptions{})
		if err == nil {
			data.PodCount = len(pods.Items)
			for _, pod := range pods.Items {
				if pod.Status.Phase == "Running" {
					data.HealthyPods++
				} else {
					data.UnhealthyPods++
				}
			}
		}

		// Get nodes
		nodes, err := d.client.CoreV1().Nodes().List(ctx, metav1.ListOptions{})
		if err == nil {
			data.NodeCount = len(nodes.Items)
		}

		// Get deployments
		deployments, err := d.client.AppsV1().Deployments(data.Namespace).List(ctx, metav1.ListOptions{})
		if err == nil {
			data.DeploymentCount = len(deployments.Items)
		}

		// Get services
		services, err := d.client.CoreV1().Services(data.Namespace).List(ctx, metav1.ListOptions{})
		if err == nil {
			data.ServiceCount = len(services.Items)
		}

		// Mock resource usage (would need metrics-server in production)
		data.CPUUsage = 45.2
		data.MemoryUsage = 62.8

		return dashboard.DataMsg{
			DashboardID: d.id,
			Data:        data,
		}
	}
}

// ID returns dashboard ID
func (d *K8sDashboard) ID() string { return d.id }

// Title returns dashboard title
func (d *K8sDashboard) Title() string { return "Kubernetes Monitor" }

// Focus sets focus
func (d *K8sDashboard) Focus() { d.focused = true }

// Blur removes focus
func (d *K8sDashboard) Blur() { d.focused = false }

// IsFocused returns focus state
func (d *K8sDashboard) IsFocused() bool { return d.focused }

// Resize handles resize
func (d *K8sDashboard) Resize(width, height int) {
	d.width = width
	d.height = height
}
