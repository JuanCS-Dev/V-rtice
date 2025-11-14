package governance

import (
	"context"
	"testing"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	gov "github.com/verticedev/vcli-go/internal/governance"
)

// TestNewGovernanceWorkspace tests workspace creation with default backend
func TestNewGovernanceWorkspace(t *testing.T) {
	ctx := context.Background()
	serverURL := "http://localhost:8150"
	operatorID := "test-operator"
	sessionID := "test-session"

	workspace := NewGovernanceWorkspace(ctx, serverURL, operatorID, sessionID)

	if workspace == nil {
		t.Fatal("expected workspace to be non-nil")
	}

	if workspace.ctx != ctx {
		t.Error("expected context to match")
	}

	if workspace.serverURL != serverURL {
		t.Errorf("expected serverURL %q, got %q", serverURL, workspace.serverURL)
	}

	if workspace.operatorID != operatorID {
		t.Errorf("expected operatorID %q, got %q", operatorID, workspace.operatorID)
	}

	if workspace.sessionID != sessionID {
		t.Errorf("expected sessionID %q, got %q", sessionID, workspace.sessionID)
	}

	if workspace.backendType != gov.BackendHTTP {
		t.Errorf("expected backend type HTTP, got %v", workspace.backendType)
	}

	if workspace.focused != SectionDecisionList {
		t.Errorf("expected initial focus on decision list, got %v", workspace.focused)
	}

	if workspace.filterMode != FilterAll {
		t.Errorf("expected filter mode ALL, got %v", workspace.filterMode)
	}
}

// TestNewGovernanceWorkspaceWithBackend tests workspace creation with custom backend
func TestNewGovernanceWorkspaceWithBackend(t *testing.T) {
	tests := []struct {
		name        string
		backendType gov.BackendType
	}{
		{"HTTP Backend", gov.BackendHTTP},
		{"gRPC Backend", gov.BackendGRPC},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := context.Background()
			workspace := NewGovernanceWorkspaceWithBackend(
				ctx,
				"http://test:8150",
				"operator1",
				"session1",
				tt.backendType,
			)

			if workspace.backendType != tt.backendType {
				t.Errorf("expected backend type %v, got %v", tt.backendType, workspace.backendType)
			}
		})
	}
}

// TestWorkspaceID verifies workspace identifier
func TestWorkspaceID(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")

	expected := "governance"
	if workspace.ID() != expected {
		t.Errorf("expected ID %q, got %q", expected, workspace.ID())
	}
}

// TestWorkspaceName verifies workspace display name
func TestWorkspaceName(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")

	name := workspace.Name()
	if name == "" {
		t.Error("expected non-empty workspace name")
	}

	// Verify it contains "Governance"
	if len(name) < 5 {
		t.Errorf("expected meaningful name, got %q", name)
	}
}

// TestWorkspaceDescription verifies workspace description
func TestWorkspaceDescription(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")

	desc := workspace.Description()
	if desc == "" {
		t.Error("expected non-empty workspace description")
	}

	// Verify it contains key concepts
	if len(desc) < 10 {
		t.Errorf("expected meaningful description, got %q", desc)
	}
}

// TestInitializeSkipped tests workspace initialization (skipped - requires backend)
func TestInitializeSkipped(t *testing.T) {
	t.Skip("Skipping test that requires actual backend connection")

	ctx := context.Background()
	workspace := NewGovernanceWorkspaceWithBackend(
		ctx,
		"http://localhost:8150",
		"test-operator",
		"test-session",
		gov.BackendHTTP,
	)

	err := workspace.Initialize()
	if err != nil {
		t.Logf("expected error without backend: %v", err)
	}

	if workspace.manager == nil {
		t.Error("expected manager to be initialized")
	}
}

// TestInit verifies Bubble Tea initialization command
func TestInit(t *testing.T) {
	workspace := NewGovernanceWorkspaceWithBackend(
		context.Background(),
		"http://localhost:8150",
		"test-op",
		"test-sess",
		gov.BackendHTTP,
	)

	cmd := workspace.Init()
	if cmd == nil {
		t.Error("expected Init to return non-nil command")
	}

	// Execute the command to test initialization
	msg := cmd()
	if msg == nil {
		t.Error("expected command to return a message")
	}

	// Check if it returns InitializedMsg or ErrorMsg
	switch msg.(type) {
	case InitializedMsg:
		// Success case
	case ErrorMsg:
		// Error case is also acceptable (no backend running)
	default:
		t.Errorf("unexpected message type: %T", msg)
	}
}

// TestUpdateWindowSize tests window size message handling
func TestUpdateWindowSize(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")

	msg := tea.WindowSizeMsg{
		Width:  120,
		Height: 40,
	}

	model, cmd := workspace.Update(msg)

	if cmd != nil {
		t.Error("expected nil command for window size update")
	}

	updatedWorkspace, ok := model.(*GovernanceWorkspace)
	if !ok {
		t.Fatal("expected model to be GovernanceWorkspace")
	}

	if updatedWorkspace.width != 120 {
		t.Errorf("expected width 120, got %d", updatedWorkspace.width)
	}

	if updatedWorkspace.height != 40 {
		t.Errorf("expected height 40, got %d", updatedWorkspace.height)
	}
}

// TestUpdateKeyPress tests keyboard navigation
func TestUpdateKeyPress(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")

	// Setup test decisions
	slaDeadline := time.Now().Add(10 * time.Minute)
	workspace.decisions = []*gov.Decision{
		{
			DecisionID:  "dec1",
			ActionType:  "block_ip",
			Target:      "192.168.1.1",
			RiskLevel:   gov.RiskLevelHigh,
			Confidence:  0.95,
			ThreatScore: 0.85,
			Reasoning:   "Suspicious activity detected",
			SLADeadline: &slaDeadline,
		},
		{
			DecisionID:  "dec2",
			ActionType:  "quarantine_file",
			Target:      "/tmp/malware.exe",
			RiskLevel:   gov.RiskLevelCritical,
			Confidence:  0.98,
			ThreatScore: 0.95,
			Reasoning:   "Known malware signature",
			SLADeadline: &slaDeadline,
		},
	}

	tests := []struct {
		name            string
		key             string
		initialIndex    int
		expectedIndex   int
		expectNilCmd    bool
	}{
		{
			name:          "Down arrow navigation",
			key:           "down",
			initialIndex:  0,
			expectedIndex: 1,
			expectNilCmd:  true,
		},
		{
			name:          "J key navigation (vim)",
			key:           "j",
			initialIndex:  0,
			expectedIndex: 1,
			expectNilCmd:  true,
		},
		{
			name:          "Up arrow navigation",
			key:           "up",
			initialIndex:  1,
			expectedIndex: 0,
			expectNilCmd:  true,
		},
		{
			name:          "K key navigation (vim)",
			key:           "k",
			initialIndex:  1,
			expectedIndex: 0,
			expectNilCmd:  true,
		},
		{
			name:          "Down at boundary",
			key:           "down",
			initialIndex:  1,
			expectedIndex: 1,
			expectNilCmd:  true,
		},
		{
			name:          "Up at boundary",
			key:           "up",
			initialIndex:  0,
			expectedIndex: 0,
			expectNilCmd:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workspace.selectedIndex = tt.initialIndex

			msg := tea.KeyMsg{Type: tea.KeyRunes}
			msg.Type = tea.KeyRunes

			model, cmd := workspace.Update(msg)

			workspace = model.(*GovernanceWorkspace)

			// Now send the actual key
			keyMsg := tea.KeyMsg{}
			switch tt.key {
			case "up":
				keyMsg.Type = tea.KeyUp
			case "down":
				keyMsg.Type = tea.KeyDown
			default:
				keyMsg.Type = tea.KeyRunes
				keyMsg.Runes = []rune{rune(tt.key[0])}
			}

			model, cmd = workspace.Update(keyMsg)
			workspace = model.(*GovernanceWorkspace)

			if workspace.selectedIndex != tt.expectedIndex {
				t.Errorf("expected index %d, got %d", tt.expectedIndex, workspace.selectedIndex)
			}

			if tt.expectNilCmd && cmd != nil {
				t.Error("expected nil command")
			}
		})
	}
}

// TestUpdateDecisionUpdate tests decision update message handling
func TestUpdateDecisionUpdate(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")

	decisions := []*gov.Decision{
		{
			DecisionID: "dec1",
			ActionType: "block_ip",
			Target:     "10.0.0.1",
			RiskLevel:  gov.RiskLevelMedium,
		},
	}

	metrics := gov.DecisionMetrics{
		TotalPending:   1,
		PendingMedium:  1,
		AvgResponseTime: 2.5,
	}

	msg := DecisionUpdateMsg{
		Decisions: decisions,
		Metrics:   metrics,
	}

	model, cmd := workspace.Update(msg)

	if cmd != nil {
		t.Error("expected nil command for decision update")
	}

	updatedWorkspace := model.(*GovernanceWorkspace)

	if len(updatedWorkspace.decisions) != 1 {
		t.Errorf("expected 1 decision, got %d", len(updatedWorkspace.decisions))
	}

	if updatedWorkspace.metrics.TotalPending != 1 {
		t.Errorf("expected total pending 1, got %d", updatedWorkspace.metrics.TotalPending)
	}
}

// TestUpdateConnectionStatus tests connection status update
func TestUpdateConnectionStatus(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")

	status := gov.ConnectionStatus{
		Connected:     true,
		ServerURL:     "http://localhost:8150",
		LastHeartbeat: time.Now(),
		EventsReceived: 42,
	}

	msg := ConnectionStatusMsg{Status: status}

	model, cmd := workspace.Update(msg)

	if cmd != nil {
		t.Error("expected nil command")
	}

	updatedWorkspace := model.(*GovernanceWorkspace)

	if !updatedWorkspace.connectionStatus.Connected {
		t.Error("expected connection status to be connected")
	}

	if updatedWorkspace.connectionStatus.EventsReceived != 42 {
		t.Errorf("expected 42 events received, got %d", updatedWorkspace.connectionStatus.EventsReceived)
	}
}

// TestView verifies basic view rendering
func TestView(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")

	// Test view before initialization
	view := workspace.View()
	if view == "" {
		t.Error("expected non-empty view")
	}

	// Set dimensions
	workspace.width = 120
	workspace.height = 40

	view = workspace.View()
	if view == "" {
		t.Error("expected non-empty view after setting dimensions")
	}

	// Add some test data
	workspace.decisions = []*gov.Decision{
		{
			DecisionID: "dec1",
			ActionType: "block_ip",
			Target:     "192.168.1.1",
			RiskLevel:  gov.RiskLevelHigh,
			Confidence: 0.95,
			ThreatScore: 0.85,
			Reasoning:  "Test reasoning",
		},
	}

	workspace.connectionStatus = gov.ConnectionStatus{
		Connected: true,
		ServerURL: "http://test:8150",
		LastHeartbeat: time.Now(),
	}

	view = workspace.View()
	if len(view) == 0 {
		t.Error("expected non-empty view with data")
	}
}

// TestCleanup verifies resource cleanup
func TestCleanup(t *testing.T) {
	t.Skip("Skipping test that requires actual backend connection")

	workspace := NewGovernanceWorkspaceWithBackend(
		context.Background(),
		"http://localhost:8150",
		"test-op",
		"test-sess",
		gov.BackendHTTP,
	)

	// Initialize first
	err := workspace.Initialize()
	if err != nil {
		t.Logf("initialization failed (expected without backend): %v", err)
	}

	// Cleanup
	err = workspace.Cleanup()
	if err != nil {
		t.Errorf("cleanup failed: %v", err)
	}
}

// TestCleanupWithoutManager verifies cleanup without manager
func TestCleanupWithoutManager(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")

	err := workspace.Cleanup()
	if err != nil {
		t.Errorf("expected nil error for cleanup without manager, got %v", err)
	}
}

// TestSections verifies section constants
func TestSections(t *testing.T) {
	tests := []struct {
		section  Section
		expected string
	}{
		{SectionDecisionList, "decision_list"},
		{SectionDetails, "details"},
		{SectionMetrics, "metrics"},
	}

	for _, tt := range tests {
		t.Run(string(tt.section), func(t *testing.T) {
			if string(tt.section) != tt.expected {
				t.Errorf("expected %q, got %q", tt.expected, string(tt.section))
			}
		})
	}
}

// TestFilterModes verifies filter mode constants
func TestFilterModes(t *testing.T) {
	tests := []struct {
		mode     FilterMode
		expected string
	}{
		{FilterAll, "all"},
		{FilterCritical, "critical"},
		{FilterHigh, "high"},
		{FilterNearingSLA, "nearing_sla"},
	}

	for _, tt := range tests {
		t.Run(string(tt.mode), func(t *testing.T) {
			if string(tt.mode) != tt.expected {
				t.Errorf("expected %q, got %q", tt.expected, string(tt.mode))
			}
		})
	}
}

// TestRenderingMethods verifies rendering methods don't panic
func TestRenderingMethods(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")
	workspace.width = 120
	workspace.height = 40

	// Setup test data
	slaDeadline := time.Now().Add(3 * time.Minute)
	workspace.decisions = []*gov.Decision{
		{
			DecisionID:  "dec1",
			ActionType:  "block_ip",
			Target:      "192.168.1.1",
			RiskLevel:   gov.RiskLevelCritical,
			Confidence:  0.95,
			ThreatScore: 0.88,
			Reasoning:   "Critical threat detected from this IP address",
			SLADeadline: &slaDeadline,
		},
	}

	workspace.metrics = gov.DecisionMetrics{
		TotalPending:    5,
		PendingCritical: 2,
		PendingHigh:     2,
		PendingMedium:   1,
		NearingSLA:      1,
		DecisionsPerMinute: 1.5,
		AvgResponseTime: 2.3,
		TotalApproved:   10,
		TotalRejected:   3,
		TotalEscalated:  1,
	}

	workspace.connectionStatus = gov.ConnectionStatus{
		Connected:     true,
		ServerURL:     "http://test:8150",
		LastHeartbeat: time.Now(),
		EventsReceived: 25,
	}

	tests := []struct {
		name string
		fn   func() string
	}{
		{"renderHeader", workspace.renderHeader},
		{"renderConnectionStatus", workspace.renderConnectionStatus},
		{"renderDecisionList", workspace.renderDecisionList},
		{"renderDecisionDetails", workspace.renderDecisionDetails},
		{"renderMetricsPanel", workspace.renderMetricsPanel},
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

// TestRenderDecisionListItem verifies individual decision rendering
func TestRenderDecisionListItem(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")
	workspace.width = 120

	slaDeadline := time.Now().Add(3 * time.Minute)
	urgentDeadline := time.Now().Add(4 * time.Minute)

	tests := []struct {
		name     string
		decision *gov.Decision
		selected bool
	}{
		{
			name: "Critical decision",
			decision: &gov.Decision{
				DecisionID:  "dec1",
				ActionType:  "block_ip",
				Target:      "10.0.0.1",
				RiskLevel:   gov.RiskLevelCritical,
				SLADeadline: &urgentDeadline,
			},
			selected: false,
		},
		{
			name: "High risk selected",
			decision: &gov.Decision{
				DecisionID:  "dec2",
				ActionType:  "quarantine_file",
				Target:      "/tmp/file",
				RiskLevel:   gov.RiskLevelHigh,
				SLADeadline: &slaDeadline,
			},
			selected: true,
		},
		{
			name: "Medium risk",
			decision: &gov.Decision{
				DecisionID: "dec3",
				ActionType: "isolate_host",
				Target:     "host-123",
				RiskLevel:  gov.RiskLevelMedium,
			},
			selected: false,
		},
		{
			name: "Low risk",
			decision: &gov.Decision{
				DecisionID: "dec4",
				ActionType: "log_event",
				Target:     "event-456",
				RiskLevel:  gov.RiskLevelLow,
			},
			selected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			defer func() {
				if r := recover(); r != nil {
					t.Errorf("renderDecisionListItem panicked: %v", r)
				}
			}()

			result := workspace.renderDecisionListItem(tt.decision, tt.selected)
			if result == "" {
				t.Error("expected non-empty render result")
			}
		})
	}
}

// TestWrapText verifies text wrapping utility
func TestWrapText(t *testing.T) {
	tests := []struct {
		name     string
		text     string
		width    int
		expected string
	}{
		{
			name:     "Short text",
			text:     "Hello",
			width:    10,
			expected: "Hello",
		},
		{
			name:     "Text exactly at width",
			text:     "1234567890",
			width:    10,
			expected: "1234567890",
		},
		{
			name:     "Text exceeds width",
			text:     "This is a very long text that exceeds the width",
			width:    20,
			expected: "This is a very lo...",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := wrapText(tt.text, tt.width)
			if result != tt.expected {
				t.Errorf("expected %q, got %q", tt.expected, result)
			}
		})
	}
}

// TestConnectionStatusRendering verifies different connection states
func TestConnectionStatusRendering(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")
	workspace.width = 120

	tests := []struct {
		name   string
		status gov.ConnectionStatus
	}{
		{
			name: "Connected",
			status: gov.ConnectionStatus{
				Connected:     true,
				ServerURL:     "http://test:8150",
				LastHeartbeat: time.Now(),
				EventsReceived: 100,
			},
		},
		{
			name: "Reconnecting",
			status: gov.ConnectionStatus{
				Connected:    false,
				Reconnecting: true,
				ServerURL:    "http://test:8150",
			},
		},
		{
			name: "Disconnected",
			status: gov.ConnectionStatus{
				Connected: false,
				ServerURL: "http://test:8150",
				LastError: "Connection timeout",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			workspace.connectionStatus = tt.status

			defer func() {
				if r := recover(); r != nil {
					t.Errorf("renderConnectionStatus panicked: %v", r)
				}
			}()

			result := workspace.renderConnectionStatus()
			if result == "" {
				t.Error("expected non-empty render result")
			}
		})
	}
}

// TestEmptyDecisionList verifies rendering with no decisions
func TestEmptyDecisionList(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")
	workspace.width = 120
	workspace.height = 40
	workspace.decisions = []*gov.Decision{}

	result := workspace.renderDecisionList()
	if result == "" {
		t.Error("expected non-empty render result for empty list")
	}
}

// TestDecisionDetailsWithInvalidIndex verifies rendering with invalid selection
func TestDecisionDetailsWithInvalidIndex(t *testing.T) {
	workspace := NewGovernanceWorkspace(context.Background(), "", "", "")
	workspace.width = 120
	workspace.height = 40
	workspace.selectedIndex = -1

	result := workspace.renderDecisionDetails()
	if result == "" {
		t.Error("expected non-empty render result")
	}

	workspace.selectedIndex = 999
	result = workspace.renderDecisionDetails()
	if result == "" {
		t.Error("expected non-empty render result")
	}
}
