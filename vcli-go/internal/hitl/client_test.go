package hitl

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// HITL CLIENT - 90%+ COVERAGE
// ============================================================================
// PHASE 3: WEAK TIER → 90%+
// Target: 0% → 90%+

func TestNewClient(t *testing.T) {
	client := NewClient("https://hitl.vertice.dev")

	assert.NotNil(t, client)
	assert.Equal(t, "https://hitl.vertice.dev", client.baseURL)
	assert.NotNil(t, client.httpClient)
	assert.Equal(t, 30*time.Second, client.httpClient.Timeout)
	assert.Empty(t, client.accessToken)
}

func TestSetToken(t *testing.T) {
	client := NewClient("https://test.com")
	client.SetToken("test-token-123")

	assert.Equal(t, "test-token-123", client.accessToken)
}

func TestLogin_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "POST", r.Method)
		assert.Equal(t, "/auth/login", r.URL.Path)
		assert.Equal(t, "application/x-www-form-urlencoded", r.Header.Get("Content-Type"))

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(LoginResponse{
			AccessToken:  "access-token-123",
			RefreshToken: "refresh-token-456",
			TokenType:    "Bearer",
			ExpiresIn:    3600,
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)
	err := client.Login("admin", "password123")

	require.NoError(t, err)
	assert.Equal(t, "access-token-123", client.accessToken)
}

func TestLogin_InvalidCredentials(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte("Invalid credentials"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	err := client.Login("wrong", "password")

	require.Error(t, err)
	assert.Contains(t, err.Error(), "login failed with status 401")
	assert.Contains(t, err.Error(), "Invalid credentials")
	assert.Empty(t, client.accessToken)
}

func TestLogin_InvalidJSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("invalid json"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	err := client.Login("admin", "password")

	require.Error(t, err)
	assert.Contains(t, err.Error(), "failed to decode response")
}

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "GET", r.Method)
		assert.Equal(t, "/status", r.URL.Path)
		assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(SystemStatus{
			Status:             "healthy",
			PendingDecisions:   5,
			CriticalPending:    2,
			InReviewDecisions:  3,
			TotalDecisionsToday: 25,
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	status, err := client.GetStatus()

	require.NoError(t, err)
	require.NotNil(t, status)
	assert.Equal(t, "healthy", status.Status)
	assert.Equal(t, 5, status.PendingDecisions)
	assert.Equal(t, 2, status.CriticalPending)
}

func TestGetStatus_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("Internal error"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	status, err := client.GetStatus()

	require.Error(t, err)
	assert.Nil(t, status)
	assert.Contains(t, err.Error(), "request failed with status 500")
}

func TestListPendingDecisions_NoPriority(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "GET", r.Method)
		assert.Equal(t, "/decisions/pending", r.URL.Path)
		assert.Empty(t, r.URL.Query().Get("priority"))

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode([]Decision{
			{
				DecisionID:  "DEC-001",
				AnalysisID:  "ANA-001",
				IncidentID:  "INC-001",
				ThreatLevel: "high",
				Priority:    "critical",
				Status:      "pending",
			},
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	decisions, err := client.ListPendingDecisions("")

	require.NoError(t, err)
	require.Len(t, decisions, 1)
	assert.Equal(t, "DEC-001", decisions[0].DecisionID)
	assert.Equal(t, "high", decisions[0].ThreatLevel)
}

func TestListPendingDecisions_WithPriority(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "GET", r.Method)
		assert.Equal(t, "/decisions/pending", r.URL.Path)
		assert.Equal(t, "critical", r.URL.Query().Get("priority"))

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode([]Decision{
			{DecisionID: "DEC-002", Priority: "critical"},
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	decisions, err := client.ListPendingDecisions("critical")

	require.NoError(t, err)
	require.Len(t, decisions, 1)
	assert.Equal(t, "critical", decisions[0].Priority)
}

func TestGetDecision_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "GET", r.Method)
		assert.Equal(t, "/decisions/ANA-123", r.URL.Path)

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(Decision{
			DecisionID: "DEC-123",
			AnalysisID: "ANA-123",
			Status:     "pending",
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	decision, err := client.GetDecision("ANA-123")

	require.NoError(t, err)
	require.NotNil(t, decision)
	assert.Equal(t, "ANA-123", decision.AnalysisID)
}

func TestGetDecision_NotFound(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	decision, err := client.GetDecision("ANA-999")

	require.Error(t, err)
	assert.Nil(t, decision)
	assert.Contains(t, err.Error(), "decision not found")
}

func TestGetDecisionResponse_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/decisions/ANA-123/response", r.URL.Path)

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(DecisionResponse{
			DecisionID:      "DEC-123",
			AnalysisID:      "ANA-123",
			Status:          "approved",
			ApprovedActions: []string{"block_ip", "quarantine"},
			Notes:           "Threat confirmed",
			DecidedBy:       "analyst@company.com",
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.GetDecisionResponse("ANA-123")

	require.NoError(t, err)
	require.NotNil(t, response)
	assert.Equal(t, "approved", response.Status)
	assert.Len(t, response.ApprovedActions, 2)
}

func TestGetDecisionResponse_NotYetMade(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.GetDecisionResponse("ANA-123")

	require.NoError(t, err)
	assert.Nil(t, response) // Decision not yet made
}

func TestMakeDecision_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "POST", r.Method)
		assert.Equal(t, "/decisions/ANA-123/decide", r.URL.Path)
		assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

		var decision DecisionCreate
		json.NewDecoder(r.Body).Decode(&decision)
		assert.Equal(t, "approved", decision.Status)

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(DecisionResponse{
			DecisionID: "DEC-123",
			Status:     "approved",
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.MakeDecision("ANA-123", DecisionCreate{
		Status:          "approved",
		ApprovedActions: []string{"block_ip"},
		Notes:           "Confirmed threat",
	})

	require.NoError(t, err)
	require.NotNil(t, response)
	assert.Equal(t, "approved", response.Status)
}

func TestEscalateDecision_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "POST", r.Method)
		assert.Equal(t, "/decisions/ANA-123/escalate", r.URL.Path)

		var req EscalateRequest
		json.NewDecoder(r.Body).Decode(&req)
		assert.Equal(t, "Need senior analyst review", req.Reason)

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(DecisionResponse{
			DecisionID: "DEC-123",
			Status:     "escalated",
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.EscalateDecision("ANA-123", "Need senior analyst review")

	require.NoError(t, err)
	require.NotNil(t, response)
	assert.Equal(t, "escalated", response.Status)
}

func TestGetStats_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/decisions/stats/summary", r.URL.Path)

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(DecisionStats{
			TotalPending:           10,
			CriticalPending:        3,
			TotalApproved:          45,
			TotalRejected:          12,
			ApprovalRate:           0.79,
			AvgResponseTimeMinutes: 15.5,
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	stats, err := client.GetStats()

	require.NoError(t, err)
	require.NotNil(t, stats)
	assert.Equal(t, 10, stats.TotalPending)
	assert.Equal(t, 0.79, stats.ApprovalRate)
}

func TestHealth_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/health", r.URL.Path)

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(HealthResponse{
			Status:  "healthy",
			Message: "All systems operational",
		})
	}))
	defer server.Close()

	client := NewClient(server.URL)

	health, err := client.Health()

	require.NoError(t, err)
	require.NotNil(t, health)
	assert.Equal(t, "healthy", health.Status)
}

func TestHealth_Unhealthy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte("Service down"))
	}))
	defer server.Close()

	client := NewClient(server.URL)

	health, err := client.Health()

	require.Error(t, err)
	assert.Nil(t, health)
	assert.Contains(t, err.Error(), "request failed with status 503")
}

func TestSetAuthHeader_WithToken(t *testing.T) {
	client := NewClient("https://test.com")
	client.SetToken("my-token")

	req, _ := http.NewRequest("GET", "https://test.com/test", nil)
	client.setAuthHeader(req)

	assert.Equal(t, "Bearer my-token", req.Header.Get("Authorization"))
}

func TestSetAuthHeader_NoToken(t *testing.T) {
	client := NewClient("https://test.com")

	req, _ := http.NewRequest("GET", "https://test.com/test", nil)
	client.setAuthHeader(req)

	assert.Empty(t, req.Header.Get("Authorization"))
}

// Edge case: Network errors
func TestLogin_NetworkError(t *testing.T) {
	client := NewClient("http://invalid-url-that-does-not-exist.local:99999")

	err := client.Login("user", "pass")

	require.Error(t, err)
	assert.Contains(t, err.Error(), "failed to execute request")
}

// Edge case: Decode errors
func TestGetStats_InvalidJSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("not json"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	stats, err := client.GetStats()

	require.Error(t, err)
	assert.Nil(t, stats)
	assert.Contains(t, err.Error(), "failed to decode response")
}

// Error case: Request creation failures (invalid URLs)
func TestGetStatus_InvalidURL(t *testing.T) {
	// Use invalid characters in baseURL to trigger http.NewRequest error
	client := NewClient("http://[::1]:namedport")
	client.SetToken("test-token")

	status, err := client.GetStatus()

	require.Error(t, err)
	assert.Nil(t, status)
	assert.Contains(t, err.Error(), "failed to create request")
}

func TestListPendingDecisions_InvalidURL(t *testing.T) {
	client := NewClient("http://[::1]:namedport")
	client.SetToken("test-token")

	decisions, err := client.ListPendingDecisions("critical")

	require.Error(t, err)
	assert.Nil(t, decisions)
	assert.Contains(t, err.Error(), "failed to create request")
}

func TestGetDecision_InvalidURL(t *testing.T) {
	client := NewClient("http://[::1]:namedport")
	client.SetToken("test-token")

	decision, err := client.GetDecision("ANA-123")

	require.Error(t, err)
	assert.Nil(t, decision)
	assert.Contains(t, err.Error(), "failed to create request")
}

func TestGetDecisionResponse_InvalidURL(t *testing.T) {
	client := NewClient("http://[::1]:namedport")
	client.SetToken("test-token")

	response, err := client.GetDecisionResponse("ANA-123")

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "failed to create request")
}

func TestMakeDecision_InvalidURL(t *testing.T) {
	client := NewClient("http://[::1]:namedport")
	client.SetToken("test-token")

	response, err := client.MakeDecision("ANA-123", DecisionCreate{Status: "approved"})

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "failed to create request")
}

func TestEscalateDecision_InvalidURL(t *testing.T) {
	client := NewClient("http://[::1]:namedport")
	client.SetToken("test-token")

	response, err := client.EscalateDecision("ANA-123", "reason")

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "failed to create request")
}

func TestGetStats_InvalidURL(t *testing.T) {
	client := NewClient("http://[::1]:namedport")
	client.SetToken("test-token")

	stats, err := client.GetStats()

	require.Error(t, err)
	assert.Nil(t, stats)
	assert.Contains(t, err.Error(), "failed to create request")
}

func TestHealth_InvalidURL(t *testing.T) {
	client := NewClient("http://[::1]:namedport")

	health, err := client.Health()

	require.Error(t, err)
	assert.Nil(t, health)
	assert.Contains(t, err.Error(), "failed to create request")
}

// Network errors for each method
func TestGetStatus_NetworkError(t *testing.T) {
	client := NewClient("http://invalid.local:99999")
	client.SetToken("test-token")

	status, err := client.GetStatus()

	require.Error(t, err)
	assert.Nil(t, status)
	assert.Contains(t, err.Error(), "failed to execute request")
}

func TestGetDecision_NetworkError(t *testing.T) {
	client := NewClient("http://invalid.local:99999")
	client.SetToken("test-token")

	decision, err := client.GetDecision("ANA-123")

	require.Error(t, err)
	assert.Nil(t, decision)
	assert.Contains(t, err.Error(), "failed to execute request")
}

func TestMakeDecision_NetworkError(t *testing.T) {
	client := NewClient("http://invalid.local:99999")
	client.SetToken("test-token")

	response, err := client.MakeDecision("ANA-123", DecisionCreate{Status: "approved"})

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "failed to execute request")
}

// Decode errors for remaining methods
func TestGetDecision_InvalidJSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("invalid json"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	decision, err := client.GetDecision("ANA-123")

	require.Error(t, err)
	assert.Nil(t, decision)
	assert.Contains(t, err.Error(), "failed to decode response")
}

func TestGetDecisionResponse_InvalidJSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("not json"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.GetDecisionResponse("ANA-123")

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "failed to decode response")
}

func TestMakeDecision_InvalidJSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("bad json"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.MakeDecision("ANA-123", DecisionCreate{Status: "approved"})

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "failed to decode response")
}

func TestEscalateDecision_InvalidJSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("invalid"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.EscalateDecision("ANA-123", "reason")

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "failed to decode response")
}

func TestHealth_InvalidJSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("bad"))
	}))
	defer server.Close()

	client := NewClient(server.URL)

	health, err := client.Health()

	require.Error(t, err)
	assert.Nil(t, health)
	assert.Contains(t, err.Error(), "failed to decode response")
}

func TestListPendingDecisions_InvalidJSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("not valid json"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	decisions, err := client.ListPendingDecisions("")

	require.Error(t, err)
	assert.Nil(t, decisions)
	assert.Contains(t, err.Error(), "failed to decode response")
}

func TestGetStatus_InvalidJSON(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("bad json here"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	status, err := client.GetStatus()

	require.Error(t, err)
	assert.Nil(t, status)
	assert.Contains(t, err.Error(), "failed to decode response")
}

// Additional error cases for specific HTTP status codes
func TestListPendingDecisions_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("Internal error"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	decisions, err := client.ListPendingDecisions("")

	require.Error(t, err)
	assert.Nil(t, decisions)
	assert.Contains(t, err.Error(), "request failed with status 500")
}

func TestGetDecision_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("Bad request"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	decision, err := client.GetDecision("ANA-123")

	require.Error(t, err)
	assert.Nil(t, decision)
	assert.Contains(t, err.Error(), "request failed with status 400")
}

func TestGetDecisionResponse_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("Error"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.GetDecisionResponse("ANA-123")

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "request failed with status 500")
}

func TestMakeDecision_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusForbidden)
		w.Write([]byte("Forbidden"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.MakeDecision("ANA-123", DecisionCreate{Status: "approved"})

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "request failed with status 403")
}

func TestEscalateDecision_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte("Service unavailable"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	response, err := client.EscalateDecision("ANA-123", "reason")

	require.Error(t, err)
	assert.Nil(t, response)
	assert.Contains(t, err.Error(), "request failed with status 503")
}

func TestGetStats_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte("Unauthorized"))
	}))
	defer server.Close()

	client := NewClient(server.URL)
	client.SetToken("test-token")

	stats, err := client.GetStats()

	require.Error(t, err)
	assert.Nil(t, stats)
	assert.Contains(t, err.Error(), "request failed with status 401")
}

// Integration test: Full workflow
func TestFullWorkflow(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/auth/login":
			json.NewEncoder(w).Encode(LoginResponse{AccessToken: "token-123"})

		case "/status":
			json.NewEncoder(w).Encode(SystemStatus{Status: "healthy", PendingDecisions: 1})

		case "/decisions/pending":
			json.NewEncoder(w).Encode([]Decision{{AnalysisID: "ANA-001"}})

		case "/decisions/ANA-001":
			json.NewEncoder(w).Encode(Decision{AnalysisID: "ANA-001", Status: "pending"})

		case "/decisions/ANA-001/decide":
			json.NewEncoder(w).Encode(DecisionResponse{Status: "approved"})

		default:
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	defer server.Close()

	client := NewClient(server.URL)

	// 1. Login
	err := client.Login("admin", "password")
	require.NoError(t, err)

	// 2. Check status
	status, err := client.GetStatus()
	require.NoError(t, err)
	assert.Equal(t, "healthy", status.Status)

	// 3. List pending
	decisions, err := client.ListPendingDecisions("")
	require.NoError(t, err)
	require.Len(t, decisions, 1)

	// 4. Get specific decision
	decision, err := client.GetDecision("ANA-001")
	require.NoError(t, err)
	assert.Equal(t, "pending", decision.Status)

	// 5. Make decision
	response, err := client.MakeDecision("ANA-001", DecisionCreate{Status: "approved"})
	require.NoError(t, err)
	assert.Equal(t, "approved", response.Status)
}
