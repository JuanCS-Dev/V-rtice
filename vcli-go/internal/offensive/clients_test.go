package offensive

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewOffensiveClient(t *testing.T) {
	client := NewOffensiveClient("http://test-offensive:9700")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-offensive:9700", client.endpoint)
}

// ============================================================================
// TOOLS Tests
// ============================================================================

func TestListTools_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/tools/list", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := ToolsListResult{
			Tools: []OffensiveTool{
				{
					Name:         "nmap",
					Phase:        "reconnaissance",
					Category:     "scanner",
					RequiresAuth: false,
					Description:  "Network mapper for discovery",
				},
				{
					Name:         "metasploit",
					Phase:        "exploitation",
					Category:     "framework",
					RequiresAuth: true,
					Description:  "Exploitation framework",
				},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.ListTools(&ToolsListRequest{Phase: "reconnaissance"})

	require.NoError(t, err)
	assert.Len(t, result.Tools, 2)
	assert.Equal(t, "nmap", result.Tools[0].Name)
	assert.Equal(t, "reconnaissance", result.Tools[0].Phase)
	assert.False(t, result.Tools[0].RequiresAuth)
}

func TestListTools_EmptyResult(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ToolsListResult{Tools: []OffensiveTool{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.ListTools(&ToolsListRequest{Phase: "unknown"})

	require.NoError(t, err)
	assert.Empty(t, result.Tools)
}

// ============================================================================
// C2 (Command & Control) Tests
// ============================================================================

func TestLaunchC2_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/c2/launch", r.URL.Path)

		response := C2LaunchResult{
			ServerURL:       "https://c2.example.com:443",
			ActiveListeners: 3,
			AccessToken:     "c2-token-abc123",
			Status:          "running",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.LaunchC2(&C2LaunchRequest{
		Target: "test-network",
		Config: "stealth-mode",
	})

	require.NoError(t, err)
	assert.Equal(t, "running", result.Status)
	assert.Equal(t, 3, result.ActiveListeners)
	assert.NotEmpty(t, result.AccessToken)
	assert.Contains(t, result.ServerURL, "https://")
}

func TestLaunchC2_Initializing(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := C2LaunchResult{
			ServerURL:       "https://c2.example.com:8443",
			ActiveListeners: 0,
			Status:          "initializing",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.LaunchC2(&C2LaunchRequest{Target: "test"})

	require.NoError(t, err)
	assert.Equal(t, "initializing", result.Status)
	assert.Equal(t, 0, result.ActiveListeners)
}

// ============================================================================
// Social Engineering Tests
// ============================================================================

func TestLaunchSocialEngCampaign_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/social/campaign", r.URL.Path)

		response := SocialEngCampaignResult{
			CampaignID:  "camp-567",
			Template:    "phishing-awareness",
			TargetCount: 150,
			Duration:    "2 weeks",
			Status:      "active",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.LaunchSocialEngCampaign(&SocialEngCampaignRequest{
		Template: "phishing-awareness",
		Config:   "standard",
	})

	require.NoError(t, err)
	assert.Equal(t, "active", result.Status)
	assert.Equal(t, "camp-567", result.CampaignID)
	assert.Greater(t, result.TargetCount, 100)
}

func TestLaunchSocialEngCampaign_Scheduled(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SocialEngCampaignResult{
			CampaignID:  "camp-568",
			Template:    "vishing-test",
			TargetCount: 25,
			Duration:    "1 week",
			Status:      "scheduled",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.LaunchSocialEngCampaign(&SocialEngCampaignRequest{Template: "vishing-test"})

	require.NoError(t, err)
	assert.Equal(t, "scheduled", result.Status)
}

// ============================================================================
// Malware Analysis Tests
// ============================================================================

func TestAnalyzeMalware_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/malware/analyze", r.URL.Path)

		response := MalwareAnalyzeResult{
			SampleHash:  "abc123def456",
			ThreatLevel: "high",
			Family:      "emotet",
			IOCs:        []string{"192.168.1.100", "malicious.com"},
			Behaviors:   []string{"keylogging", "lateral_movement"},
			Report:      "Full analysis report available",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.AnalyzeMalware(&MalwareAnalyzeRequest{
		SamplePath: "/samples/suspicious.exe",
		Mode:       "dynamic",
	})

	require.NoError(t, err)
	assert.Equal(t, "high", result.ThreatLevel)
	assert.Equal(t, "emotet", result.Family)
	assert.Len(t, result.IOCs, 2)
	assert.Contains(t, result.Behaviors, "keylogging")
	assert.NotEmpty(t, result.Report)
}

func TestAnalyzeMalware_LowThreat(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := MalwareAnalyzeResult{
			SampleHash:  "xyz789",
			ThreatLevel: "low",
			Family:      "unknown",
			IOCs:        []string{},
			Behaviors:   []string{"file_access"},
			Report:      "Minimal suspicious activity",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.AnalyzeMalware(&MalwareAnalyzeRequest{
		SamplePath: "/samples/benign.exe",
		Mode:       "static",
	})

	require.NoError(t, err)
	assert.Equal(t, "low", result.ThreatLevel)
	assert.Empty(t, result.IOCs)
}

// ============================================================================
// Wargaming Tests
// ============================================================================

func TestStartWargame_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/wargame/start", r.URL.Path)

		response := WargameStartResult{
			GameID:            "game-999",
			ScenarioName:      "ransomware-attack",
			EstimatedDuration: "4 hours",
			Status:            "in_progress",
			Phases: []WargamePhase{
				{Name: "initial_access", Duration: "1h", Status: "active"},
				{Name: "lateral_movement", Duration: "1.5h", Status: "pending"},
				{Name: "exfiltration", Duration: "1.5h", Status: "pending"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.StartWargame(&WargameStartRequest{Scenario: "ransomware-attack"})

	require.NoError(t, err)
	assert.Equal(t, "game-999", result.GameID)
	assert.Equal(t, "ransomware-attack", result.ScenarioName)
	assert.Equal(t, "in_progress", result.Status)
	assert.Len(t, result.Phases, 3)
	assert.Equal(t, "active", result.Phases[0].Status)
}

func TestStartWargame_Planning(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := WargameStartResult{
			GameID:            "game-1000",
			ScenarioName:      "apt-simulation",
			EstimatedDuration: "6 hours",
			Status:            "planning",
			Phases:            []WargamePhase{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.StartWargame(&WargameStartRequest{Scenario: "apt-simulation"})

	require.NoError(t, err)
	assert.Equal(t, "planning", result.Status)
	assert.Empty(t, result.Phases)
}

// ============================================================================
// Gateway Status Tests
// ============================================================================

func TestGetGatewayStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/gateway/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := GatewayStatus{
			OverallStatus: "operational",
			Components: []GatewayComponent{
				{Name: "c2-server", Status: "running", Uptime: "24h", ActiveOps: 5},
				{Name: "payload-delivery", Status: "running", Uptime: "24h", ActiveOps: 2},
				{Name: "exfil-handler", Status: "running", Uptime: "24h", ActiveOps: 0},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.GetGatewayStatus()

	require.NoError(t, err)
	assert.Equal(t, "operational", result.OverallStatus)
	assert.Len(t, result.Components, 3)
	assert.Equal(t, "c2-server", result.Components[0].Name)
	assert.Equal(t, 5, result.Components[0].ActiveOps)
}

func TestGetGatewayStatus_Degraded(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := GatewayStatus{
			OverallStatus: "degraded",
			Components: []GatewayComponent{
				{Name: "c2-server", Status: "running", Uptime: "12h", ActiveOps: 3},
				{Name: "payload-delivery", Status: "error", Uptime: "0h", ActiveOps: 0},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.GetGatewayStatus()

	require.NoError(t, err)
	assert.Equal(t, "degraded", result.OverallStatus)
	assert.Equal(t, "error", result.Components[1].Status)
}

// ============================================================================
// Orchestrator Tests
// ============================================================================

func TestExecuteWorkflow_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/orchestrator/workflow", r.URL.Path)

		response := OrchestratorWorkflowResult{
			WorkflowID:   "wf-234",
			PlaybookName: "red-team-exercise",
			TotalPhases:  5,
			CurrentPhase: "reconnaissance",
			Status:       "executing",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.ExecuteWorkflow(&OrchestratorWorkflowRequest{
		Playbook: "red-team-exercise",
		Config:   "aggressive",
	})

	require.NoError(t, err)
	assert.Equal(t, "wf-234", result.WorkflowID)
	assert.Equal(t, "red-team-exercise", result.PlaybookName)
	assert.Equal(t, 5, result.TotalPhases)
	assert.Equal(t, "executing", result.Status)
}

func TestExecuteWorkflow_Completed(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := OrchestratorWorkflowResult{
			WorkflowID:   "wf-235",
			PlaybookName: "purple-team-validation",
			TotalPhases:  3,
			CurrentPhase: "reporting",
			Status:       "completed",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	result, err := client.ExecuteWorkflow(&OrchestratorWorkflowRequest{
		Playbook: "purple-team-validation",
	})

	require.NoError(t, err)
	assert.Equal(t, "completed", result.Status)
}

// ============================================================================
// Error Handling Tests
// ============================================================================

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)

	t.Run("ListTools", func(t *testing.T) {
		_, err := client.ListTools(&ToolsListRequest{})
		assert.Error(t, err)
	})

	t.Run("LaunchC2", func(t *testing.T) {
		_, err := client.LaunchC2(&C2LaunchRequest{})
		assert.Error(t, err)
	})

	t.Run("LaunchSocialEngCampaign", func(t *testing.T) {
		_, err := client.LaunchSocialEngCampaign(&SocialEngCampaignRequest{})
		assert.Error(t, err)
	})

	t.Run("AnalyzeMalware", func(t *testing.T) {
		_, err := client.AnalyzeMalware(&MalwareAnalyzeRequest{})
		assert.Error(t, err)
	})

	t.Run("StartWargame", func(t *testing.T) {
		_, err := client.StartWargame(&WargameStartRequest{})
		assert.Error(t, err)
	})

	t.Run("GetGatewayStatus", func(t *testing.T) {
		_, err := client.GetGatewayStatus()
		assert.Error(t, err)
	})

	t.Run("ExecuteWorkflow", func(t *testing.T) {
		_, err := client.ExecuteWorkflow(&OrchestratorWorkflowRequest{})
		assert.Error(t, err)
	})
}

// ============================================================================
// WebAttackClient Tests
// ============================================================================

func TestNewWebAttackClient(t *testing.T) {
	client := NewWebAttackClient("http://test-web-attack:8080", "test-token")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-web-attack:8080", client.baseURL)
	assert.Equal(t, "test-token", client.authToken)
}

func TestLaunchAttack_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/launch_attack", r.URL.Path)
		assert.Equal(t, "POST", r.Method)
		assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

		response := AttackResponse{
			AttackID:        "attack-456",
			Status:          "running",
			Vulnerabilities: []string{"SQL Injection", "XSS"},
			Findings: map[string]interface{}{
				"severity": "high",
				"count":    2,
			},
			Timestamp: "2025-01-14T12:00:00Z",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewWebAttackClient(server.URL, "test-token")
	result, err := client.LaunchAttack("https://target.com", "full-scan", map[string]interface{}{
		"depth": 3,
	})

	require.NoError(t, err)
	assert.Equal(t, "attack-456", result.AttackID)
	assert.Equal(t, "running", result.Status)
	assert.Len(t, result.Vulnerabilities, 2)
	assert.Contains(t, result.Vulnerabilities, "SQL Injection")
}

func TestLaunchAttack_NoAuth(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Empty(t, r.Header.Get("Authorization"))

		response := AttackResponse{
			AttackID: "attack-457",
			Status:   "queued",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewWebAttackClient(server.URL, "")
	result, err := client.LaunchAttack("https://target.com", "quick-scan", nil)

	require.NoError(t, err)
	assert.Equal(t, "queued", result.Status)
}

func TestLaunchAttack_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("Invalid target URL"))
	}))
	defer server.Close()

	client := NewWebAttackClient(server.URL, "test-token")
	_, err := client.LaunchAttack("invalid-url", "scan", nil)

	assert.Error(t, err)
	assert.Contains(t, err.Error(), "400")
}

func TestGetAttackStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/attack_status/attack-789", r.URL.Path)
		assert.Equal(t, "GET", r.Method)
		assert.Equal(t, "Bearer auth-123", r.Header.Get("Authorization"))

		response := AttackResponse{
			AttackID:        "attack-789",
			Status:          "completed",
			Vulnerabilities: []string{"CSRF", "Open Redirect"},
			Findings: map[string]interface{}{
				"total_checks": 150,
				"passed":       145,
				"failed":       5,
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewWebAttackClient(server.URL, "auth-123")
	result, err := client.GetAttackStatus("attack-789")

	require.NoError(t, err)
	assert.Equal(t, "attack-789", result.AttackID)
	assert.Equal(t, "completed", result.Status)
	assert.Len(t, result.Vulnerabilities, 2)
}

func TestGetAttackStatus_NotFound(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := AttackResponse{
			AttackID: "attack-999",
			Status:   "not_found",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewWebAttackClient(server.URL, "token")
	result, err := client.GetAttackStatus("attack-999")

	require.NoError(t, err)
	assert.Equal(t, "not_found", result.Status)
}

func TestHealth_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/health", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := map[string]string{
			"status":  "healthy",
			"version": "2.0.0",
			"uptime":  "48h",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewWebAttackClient(server.URL, "")
	result, err := client.Health()

	require.NoError(t, err)
	assert.Equal(t, "healthy", result["status"])
	assert.Equal(t, "2.0.0", result["version"])
}

func TestHealth_Unhealthy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := map[string]string{
			"status": "degraded",
			"issue":  "database connection slow",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewWebAttackClient(server.URL, "")
	result, err := client.Health()

	require.NoError(t, err)
	assert.Equal(t, "degraded", result["status"])
}

// ============================================================================
// Benchmark Tests
// ============================================================================

func BenchmarkListTools(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ToolsListResult{Tools: []OffensiveTool{}})
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)
	req := &ToolsListRequest{Phase: "recon"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.ListTools(req)
	}
}

func BenchmarkGetGatewayStatus(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(GatewayStatus{OverallStatus: "operational"})
	}))
	defer server.Close()

	client := NewOffensiveClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GetGatewayStatus()
	}
}

func BenchmarkLaunchAttack(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(AttackResponse{AttackID: "test", Status: "running"})
	}))
	defer server.Close()

	client := NewWebAttackClient(server.URL, "token")

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.LaunchAttack("https://target.com", "scan", nil)
	}
}
