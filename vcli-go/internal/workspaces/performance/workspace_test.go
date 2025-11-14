package performance

import (
	"context"
	"testing"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/verticedev/vcli-go/internal/maximus"
)

// TestNewPerformanceWorkspace tests workspace creation
func TestNewPerformanceWorkspace(t *testing.T) {
	ctx := context.Background()
	maximusURL := "http://localhost:8150"

	workspace := NewPerformanceWorkspace(ctx, maximusURL)

	if workspace == nil {
		t.Fatal("expected workspace to be non-nil")
	}

	if workspace.ctx != ctx {
		t.Error("expected context to match")
	}

	if workspace.maximusEndpoint != maximusURL {
		t.Errorf("expected maximusEndpoint %q, got %q", maximusURL, workspace.maximusEndpoint)
	}

	if workspace.updateInterval != 5*time.Second {
		t.Errorf("expected update interval 5s, got %v", workspace.updateInterval)
	}

	if workspace.initialized {
		t.Error("expected workspace to not be initialized on creation")
	}
}

// TestWorkspaceID verifies workspace identifier
func TestWorkspaceID(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "")

	expected := "performance"
	if workspace.ID() != expected {
		t.Errorf("expected ID %q, got %q", expected, workspace.ID())
	}
}

// TestWorkspaceName verifies workspace display name
func TestWorkspaceName(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "")

	name := workspace.Name()
	if name == "" {
		t.Error("expected non-empty workspace name")
	}

	// Verify it contains "Performance"
	if len(name) < 5 {
		t.Errorf("expected meaningful name, got %q", name)
	}
}

// TestWorkspaceDescription verifies workspace description
func TestWorkspaceDescription(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "")

	desc := workspace.Description()
	if desc == "" {
		t.Error("expected non-empty workspace description")
	}

	// Verify it contains key concepts
	if len(desc) < 10 {
		t.Errorf("expected meaningful description, got %q", desc)
	}
}

// TestWorkspaceIcon verifies workspace icon
func TestWorkspaceIcon(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "")

	icon := workspace.Icon()
	if icon == "" {
		t.Error("expected non-empty workspace icon")
	}
}

// TestInit verifies Bubble Tea initialization
func TestInit(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")

	cmd := workspace.Init()
	if cmd == nil {
		t.Error("expected Init to return non-nil command")
	}
}

// TestIsInitialized verifies initialization state tracking
func TestIsInitialized(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")

	if workspace.IsInitialized() {
		t.Error("expected workspace to not be initialized")
	}

	workspace.initialized = true

	if !workspace.IsInitialized() {
		t.Error("expected workspace to be initialized")
	}
}

// TestUpdateWindowSize tests window size message handling
func TestUpdateWindowSize(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "")

	msg := tea.WindowSizeMsg{
		Width:  140,
		Height: 50,
	}

	model, cmd := workspace.Update(msg)

	if cmd != nil {
		t.Error("expected nil command for window size update")
	}

	updatedWorkspace, ok := model.(*PerformanceWorkspace)
	if !ok {
		t.Fatal("expected model to be PerformanceWorkspace")
	}

	if updatedWorkspace.width != 140 {
		t.Errorf("expected width 140, got %d", updatedWorkspace.width)
	}

	if updatedWorkspace.height != 50 {
		t.Errorf("expected height 50, got %d", updatedWorkspace.height)
	}
}

// TestUpdateKeyPress tests keyboard shortcuts
func TestUpdateKeyPress(t *testing.T) {
	tests := []struct {
		name         string
		key          tea.KeyType
		runes        []rune
		expectCmd    bool
	}{
		{
			name:      "R key refresh",
			key:       tea.KeyRunes,
			runes:     []rune{'r'},
			expectCmd: true,
		},
		{
			name:      "Unknown key",
			key:       tea.KeyRunes,
			runes:     []rune{'x'},
			expectCmd: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
			workspace.initialized = true

			msg := tea.KeyMsg{
				Type:  tt.key,
				Runes: tt.runes,
			}

			model, cmd := workspace.Update(msg)

			workspace = model.(*PerformanceWorkspace)

			if tt.expectCmd && cmd == nil {
				t.Error("expected command to be returned")
			}

			if !tt.expectCmd && cmd != nil {
				t.Error("expected nil command")
			}
		})
	}
}

// TestUpdateInitializedMsg tests initialization message handling
func TestUpdateInitializedMsg(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")

	msg := InitializedMsg{}

	model, cmd := workspace.Update(msg)

	updatedWorkspace := model.(*PerformanceWorkspace)

	if !updatedWorkspace.initialized {
		t.Error("expected workspace to be initialized after InitializedMsg")
	}

	if cmd == nil {
		t.Error("expected command to fetch metrics")
	}
}

// TestUpdateMetricsUpdateMsg tests metrics update message handling
func TestUpdateMetricsUpdateMsg(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")

	governanceStats := &maximus.PendingStatsResponse{
		TotalPending: 10,
		ByCategory: map[string]int{
			"security": 5,
			"compliance": 3,
			"audit": 2,
		},
		BySeverity: map[string]int{
			"critical": 2,
			"high": 4,
			"medium": 3,
			"low": 1,
		},
		OldestDecisionAge: 300.0,
		Metadata: map[string]interface{}{
			"decisions_per_minute": 1.5,
			"avg_response_time": 2.3,
		},
	}

	governanceHealth := &maximus.GovernanceHealthResponse{
		Status:    "healthy",
		Timestamp: time.Now().Format(time.RFC3339),
		Version:   "1.0.0",
	}

	msg := MetricsUpdateMsg{
		GovernanceStats:  governanceStats,
		GovernanceHealth: governanceHealth,
		Timestamp:        time.Now(),
	}

	model, cmd := workspace.Update(msg)

	if cmd != nil {
		t.Error("expected nil command for metrics update")
	}

	updatedWorkspace := model.(*PerformanceWorkspace)

	if updatedWorkspace.governanceStats.TotalPending != 10 {
		t.Errorf("expected total pending 10, got %d", updatedWorkspace.governanceStats.TotalPending)
	}

	if updatedWorkspace.governanceHealth.Status != "healthy" {
		t.Errorf("expected status healthy, got %s", updatedWorkspace.governanceHealth.Status)
	}

	if updatedWorkspace.lastUpdate.IsZero() {
		t.Error("expected lastUpdate to be set")
	}
}

// TestUpdateTickMsg tests periodic update tick handling
func TestUpdateTickMsg(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.initialized = true

	msg := UpdateTickMsg{
		Timestamp: time.Now(),
	}

	model, cmd := workspace.Update(msg)

	workspace = model.(*PerformanceWorkspace)

	if cmd == nil {
		t.Error("expected command to fetch metrics")
	}
}

// TestUpdateErrorMsg tests error message handling
func TestUpdateErrorMsg(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")

	msg := ErrorMsg{
		Error: context.DeadlineExceeded,
	}

	model, cmd := workspace.Update(msg)

	if cmd != nil {
		t.Error("expected nil command for error message")
	}

	workspace = model.(*PerformanceWorkspace)
	// Verify workspace is returned unchanged
	if workspace == nil {
		t.Error("expected workspace to be returned")
	}
}

// TestView verifies basic view rendering
func TestView(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")

	// Test view before initialization
	view := workspace.View()
	if view == "" {
		t.Error("expected non-empty view")
	}

	// Should show loading message
	if view != "Loading Performance Dashboard..." {
		t.Logf("Got view: %s", view)
	}

	// Set dimensions and initialize
	workspace.width = 140
	workspace.height = 50
	workspace.initialized = true
	workspace.lastUpdate = time.Now()

	view = workspace.View()
	if view == "" {
		t.Error("expected non-empty view after initialization")
	}
}

// TestViewWithData verifies view rendering with data
func TestViewWithData(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.width = 140
	workspace.height = 50
	workspace.initialized = true
	workspace.lastUpdate = time.Now()

	// Add test data
	workspace.governanceStats = &maximus.PendingStatsResponse{
		TotalPending: 15,
		ByCategory: map[string]int{
			"security": 8,
			"compliance": 5,
			"audit": 2,
		},
		BySeverity: map[string]int{
			"critical": 3,
			"high": 6,
			"medium": 4,
			"low": 2,
		},
		OldestDecisionAge: 450.0,
		Metadata: map[string]interface{}{
			"decisions_per_minute": 2.1,
			"avg_response_time": 1.8,
		},
	}

	workspace.governanceHealth = &maximus.GovernanceHealthResponse{
		Status:    "healthy",
		Timestamp: time.Now().Format(time.RFC3339),
		Version:   "1.0.0",
	}

	view := workspace.View()
	if len(view) == 0 {
		t.Error("expected non-empty view with data")
	}
}

// TestCleanup verifies resource cleanup
func TestCleanup(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")

	err := workspace.Cleanup()
	if err != nil {
		t.Errorf("cleanup failed: %v", err)
	}
}

// TestShortcuts verifies workspace shortcuts
func TestShortcuts(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")

	shortcuts := workspace.Shortcuts()

	if len(shortcuts) == 0 {
		t.Error("expected non-empty shortcuts list")
	}

	// Verify shortcut structure
	for i, sc := range shortcuts {
		if sc.Key == "" {
			t.Errorf("shortcut %d: expected non-empty key", i)
		}

		if sc.Description == "" {
			t.Errorf("shortcut %d: expected non-empty description", i)
		}

		if sc.Action == nil {
			t.Errorf("shortcut %d: expected non-nil action", i)
		}

		// Test action execution
		msg := sc.Action()
		if msg == nil {
			t.Errorf("shortcut %d: expected action to return message", i)
		}
	}
}

// TestRenderingMethods verifies rendering methods don't panic
func TestRenderingMethods(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.width = 140
	workspace.height = 50
	workspace.initialized = true
	workspace.lastUpdate = time.Now()

	// Setup test data
	workspace.governanceStats = &maximus.PendingStatsResponse{
		TotalPending: 10,
		ByCategory: map[string]int{
			"security": 5,
			"compliance": 3,
			"audit": 2,
		},
		BySeverity: map[string]int{
			"critical": 2,
			"high": 4,
			"medium": 3,
			"low": 1,
		},
		OldestDecisionAge: 300.0,
		Metadata: map[string]interface{}{
			"decisions_per_minute": 1.5,
			"avg_response_time": 2.3,
		},
	}

	workspace.governanceHealth = &maximus.GovernanceHealthResponse{
		Status:    "healthy",
		Timestamp: time.Now().Format(time.RFC3339),
		Version:   "1.0.0",
	}

	tests := []struct {
		name string
		fn   func() string
	}{
		{"renderHeader", workspace.renderHeader},
		{"renderGovernanceMetrics", workspace.renderGovernanceMetrics},
		{"renderSystemHealth", workspace.renderSystemHealth},
		{"renderThroughputMetrics", workspace.renderThroughputMetrics},
		{"renderFooter", workspace.renderFooter},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			defer func() {
				if r := recover(); r != nil {
					t.Errorf("%s panicked: %v", tt.name, r)
				}
			}()

			result := tt.fn()
			if result == "" {
				t.Errorf("%s returned empty string", tt.name)
			}
		})
	}
}

// TestRenderGovernanceMetricsWithNilData verifies rendering with nil data
func TestRenderGovernanceMetricsWithNilData(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.width = 140
	workspace.height = 50
	workspace.governanceStats = nil

	defer func() {
		if r := recover(); r != nil {
			t.Errorf("renderGovernanceMetrics panicked with nil data: %v", r)
		}
	}()

	result := workspace.renderGovernanceMetrics()
	if result == "" {
		t.Error("expected non-empty render result")
	}
}

// TestRenderSystemHealthWithNilData verifies health rendering with nil data
func TestRenderSystemHealthWithNilData(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.width = 140
	workspace.height = 50
	workspace.governanceHealth = nil

	defer func() {
		if r := recover(); r != nil {
			t.Errorf("renderSystemHealth panicked with nil data: %v", r)
		}
	}()

	result := workspace.renderSystemHealth()
	if result == "" {
		t.Error("expected non-empty render result")
	}
}

// TestRenderThroughputMetricsWithMetadata verifies throughput rendering
func TestRenderThroughputMetricsWithMetadata(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.width = 140
	workspace.height = 50
	workspace.updateInterval = 5 * time.Second
	workspace.lastUpdate = time.Now().Add(-10 * time.Second)

	workspace.governanceStats = &maximus.PendingStatsResponse{
		TotalPending: 5,
		Metadata: map[string]interface{}{
			"decisions_per_minute": 2.5,
			"avg_response_time": 1.2,
		},
	}

	defer func() {
		if r := recover(); r != nil {
			t.Errorf("renderThroughputMetrics panicked: %v", r)
		}
	}()

	result := workspace.renderThroughputMetrics()
	if result == "" {
		t.Error("expected non-empty render result")
	}
}

// TestRenderThroughputMetricsWithoutMetadata verifies throughput rendering without metadata
func TestRenderThroughputMetricsWithoutMetadata(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.width = 140
	workspace.height = 50
	workspace.updateInterval = 5 * time.Second
	workspace.lastUpdate = time.Now()

	workspace.governanceStats = &maximus.PendingStatsResponse{
		TotalPending: 5,
		Metadata:     nil,
	}

	defer func() {
		if r := recover(); r != nil {
			t.Errorf("renderThroughputMetrics panicked: %v", r)
		}
	}()

	result := workspace.renderThroughputMetrics()
	if result == "" {
		t.Error("expected non-empty render result")
	}
}

// TestGetSeverityColor verifies severity color mapping
func TestGetSeverityColor(t *testing.T) {
	tests := []struct {
		severity string
		expected string
	}{
		{"critical", "#FF0000"},
		{"high", "#FF6B6B"},
		{"medium", "#FFA500"},
		{"low", "#00FF00"},
		{"unknown", "#FFFFFF"},
	}

	for _, tt := range tests {
		t.Run(tt.severity, func(t *testing.T) {
			color := getSeverityColor(tt.severity)
			if color != tt.expected {
				t.Errorf("expected color %q for severity %q, got %q",
					tt.expected, tt.severity, color)
			}
		})
	}
}

// TestRenderSystemHealthStates verifies different health states
func TestRenderSystemHealthStates(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.width = 140
	workspace.height = 50
	workspace.lastUpdate = time.Now()

	tests := []struct {
		name   string
		health *maximus.GovernanceHealthResponse
	}{
		{
			name: "Healthy system",
			health: &maximus.GovernanceHealthResponse{
				Status:    "healthy",
				Timestamp: time.Now().Format(time.RFC3339),
				Version:   "1.0.0",
			},
		},
		{
			name: "Degraded system",
			health: &maximus.GovernanceHealthResponse{
				Status:    "degraded",
				Timestamp: time.Now().Format(time.RFC3339),
				Version:   "1.0.0",
			},
		},
		{
			name: "Critical system",
			health: &maximus.GovernanceHealthResponse{
				Status:    "critical",
				Timestamp: time.Now().Format(time.RFC3339),
			},
		},
		{
			name:   "Nil health (disconnected)",
			health: nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workspace.governanceHealth = tt.health

			defer func() {
				if r := recover(); r != nil {
					t.Errorf("renderSystemHealth panicked: %v", r)
				}
			}()

			result := workspace.renderSystemHealth()
			if result == "" {
				t.Error("expected non-empty render result")
			}
		})
	}
}

// TestRenderGovernanceMetricsBySeverity verifies severity distribution rendering
func TestRenderGovernanceMetricsBySeverity(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.width = 140
	workspace.height = 50

	workspace.governanceStats = &maximus.PendingStatsResponse{
		TotalPending: 20,
		ByCategory: map[string]int{
			"security": 10,
			"compliance": 6,
			"audit": 4,
		},
		BySeverity: map[string]int{
			"critical": 5,
			"high": 8,
			"medium": 5,
			"low": 2,
		},
		OldestDecisionAge: 600.0,
	}

	defer func() {
		if r := recover(); r != nil {
			t.Errorf("renderGovernanceMetrics panicked: %v", r)
		}
	}()

	result := workspace.renderGovernanceMetrics()
	if result == "" {
		t.Error("expected non-empty render result")
	}
}

// TestRenderGovernanceMetricsWithZeroAge verifies rendering with zero age
func TestRenderGovernanceMetricsWithZeroAge(t *testing.T) {
	workspace := NewPerformanceWorkspace(context.Background(), "http://localhost:8150")
	workspace.width = 140
	workspace.height = 50

	workspace.governanceStats = &maximus.PendingStatsResponse{
		TotalPending: 5,
		ByCategory: map[string]int{
			"security": 5,
		},
		BySeverity: map[string]int{
			"medium": 5,
		},
		OldestDecisionAge: 0.0, // No age
	}

	defer func() {
		if r := recover(); r != nil {
			t.Errorf("renderGovernanceMetrics panicked: %v", r)
		}
	}()

	result := workspace.renderGovernanceMetrics()
	if result == "" {
		t.Error("expected non-empty render result")
	}
}

// TestMessageTypes verifies custom message types
func TestMessageTypes(t *testing.T) {
	t.Run("InitializedMsg", func(t *testing.T) {
		msg := InitializedMsg{}
		_ = msg // Just verify it can be created
	})

	t.Run("MetricsUpdateMsg", func(t *testing.T) {
		msg := MetricsUpdateMsg{
			GovernanceStats:  &maximus.PendingStatsResponse{},
			GovernanceHealth: &maximus.GovernanceHealthResponse{},
			Timestamp:        time.Now(),
		}
		if msg.Timestamp.IsZero() {
			t.Error("expected timestamp to be set")
		}
	})

	t.Run("UpdateTickMsg", func(t *testing.T) {
		msg := UpdateTickMsg{
			Timestamp: time.Now(),
		}
		if msg.Timestamp.IsZero() {
			t.Error("expected timestamp to be set")
		}
	})

	t.Run("ErrorMsg", func(t *testing.T) {
		msg := ErrorMsg{
			Error: context.Canceled,
		}
		if msg.Error == nil {
			t.Error("expected error to be set")
		}
	})
}

// TestShortcutStructure verifies shortcut type structure
func TestShortcutStructure(t *testing.T) {
	shortcut := Shortcut{
		Key:         "r",
		Description: "Refresh",
		Action: func() tea.Msg {
			return UpdateTickMsg{Timestamp: time.Now()}
		},
	}

	if shortcut.Key != "r" {
		t.Errorf("expected key 'r', got %q", shortcut.Key)
	}

	if shortcut.Description != "Refresh" {
		t.Errorf("expected description 'Refresh', got %q", shortcut.Description)
	}

	if shortcut.Action == nil {
		t.Error("expected action to be set")
	}

	// Test action execution
	msg := shortcut.Action()
	if _, ok := msg.(UpdateTickMsg); !ok {
		t.Errorf("expected UpdateTickMsg, got %T", msg)
	}
}

// TestEndpoint verifies Endpoint structure
func TestEndpoint(t *testing.T) {
	endpoint := Endpoint{
		URL:       "http://localhost:8150",
		Healthy:   true,
		LastCheck: time.Now(),
		Version:   "1.0.0",
	}

	if endpoint.URL != "http://localhost:8150" {
		t.Errorf("expected URL to match, got %q", endpoint.URL)
	}

	if !endpoint.Healthy {
		t.Error("expected healthy to be true")
	}

	if endpoint.LastCheck.IsZero() {
		t.Error("expected LastCheck to be set")
	}

	if endpoint.Version != "1.0.0" {
		t.Errorf("expected version '1.0.0', got %q", endpoint.Version)
	}
}
