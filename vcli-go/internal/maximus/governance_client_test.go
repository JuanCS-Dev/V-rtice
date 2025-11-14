package maximus

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
// CONSTRUCTOR TESTS
// ============================================================================

func TestNewGovernanceClient(t *testing.T) {
	t.Run("creates client with provided URL", func(t *testing.T) {
		client := NewGovernanceClient("http://localhost:8150")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8150", client.baseURL)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("adds http protocol to localhost without protocol", func(t *testing.T) {
		client := NewGovernanceClient("localhost:8150")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8150", client.baseURL)
	})

	t.Run("adds https protocol to remote without protocol", func(t *testing.T) {
		client := NewGovernanceClient("maximus.vertice.ai:8150")

		require.NotNil(t, client)
		assert.Equal(t, "https://maximus.vertice.ai:8150", client.baseURL)
	})

	t.Run("trims trailing slash from URL", func(t *testing.T) {
		client := NewGovernanceClient("http://localhost:8150/")

		assert.Equal(t, "http://localhost:8150", client.baseURL)
	})

	t.Run("uses default localhost when empty", func(t *testing.T) {
		client := NewGovernanceClient("")

		require.NotNil(t, client)
		assert.Contains(t, client.baseURL, "localhost")
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestGovernanceClientHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := GovernanceHealthResponse{
				Status:    "healthy",
				Timestamp: time.Now().Format(time.RFC3339),
				Version:   "1.0.0",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
		assert.NotEmpty(t, result.Timestamp)
		assert.Equal(t, "1.0.0", result.Version)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service unavailable"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on connection failure", func(t *testing.T) {
		client := NewGovernanceClient("http://invalid-host:99999")

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET PENDING STATS TESTS
// ============================================================================

func TestGovernanceClientGetPendingStats(t *testing.T) {
	t.Run("successful stats retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/pending", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := PendingStatsResponse{
				TotalPending: 42,
				ByCategory: map[string]int{
					"security":   25,
					"compliance": 17,
				},
				BySeverity: map[string]int{
					"high":   10,
					"medium": 32,
				},
				OldestDecisionAge: 3600.5,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetPendingStats()

		require.NoError(t, err)
		assert.Equal(t, 42, result.TotalPending)
		assert.Equal(t, 25, result.ByCategory["security"])
		assert.Equal(t, 10, result.BySeverity["high"])
		assert.Equal(t, 3600.5, result.OldestDecisionAge)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("internal error"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetPendingStats()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetPendingStats()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET DECISION TESTS
// ============================================================================

func TestGovernanceClientGetDecision(t *testing.T) {
	t.Run("successful decision retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/decision/dec-123", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			slaDeadline := "2024-01-01T12:00:00Z"
			resp := DecisionResponse{
				DecisionID:      "dec-123",
				Status:          "pending",
				RiskLevel:       "high",
				AutomationLevel: "supervised",
				CreatedAt:       "2024-01-01T10:00:00Z",
				SLADeadline:     &slaDeadline,
				Context: map[string]interface{}{
					"source": "firewall",
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetDecision("dec-123")

		require.NoError(t, err)
		assert.Equal(t, "dec-123", result.DecisionID)
		assert.Equal(t, "pending", result.Status)
		assert.Equal(t, "high", result.RiskLevel)
		assert.NotNil(t, result.SLADeadline)
	})

	t.Run("error when decision not found", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("not found"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetDecision("dec-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "not found")
	})

	t.Run("error on non-200/404 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("forbidden"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetDecision("dec-123")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "403")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetDecision("dec-123")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// CREATE SESSION TESTS
// ============================================================================

func TestGovernanceClientCreateSession(t *testing.T) {
	t.Run("successful session creation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/session/create", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var req SessionCreateRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "operator-1", req.OperatorID)
			assert.Equal(t, "John Doe", req.OperatorName)

			resp := SessionCreateResponse{
				SessionID:  "session-123",
				OperatorID: req.OperatorID,
				CreatedAt:  time.Now(),
				ExpiresAt:  time.Now().Add(8 * time.Hour),
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := SessionCreateRequest{
			OperatorID:   "operator-1",
			OperatorName: "John Doe",
		}

		result, err := client.CreateSession(req)

		require.NoError(t, err)
		assert.Equal(t, "session-123", result.SessionID)
		assert.Equal(t, "operator-1", result.OperatorID)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid request"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := SessionCreateRequest{OperatorID: "operator-1"}

		result, err := client.CreateSession(req)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := SessionCreateRequest{OperatorID: "operator-1"}

		result, err := client.CreateSession(req)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET OPERATOR STATS TESTS
// ============================================================================

func TestGovernanceClientGetOperatorStats(t *testing.T) {
	t.Run("successful stats retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/session/operator-1/stats", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := OperatorStatsResponse{
				OperatorID:      "operator-1",
				TotalDecisions:  100,
				Approved:        60,
				Rejected:        30,
				Escalated:       10,
				AvgResponseTime: 45.5,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetOperatorStats("operator-1")

		require.NoError(t, err)
		assert.Equal(t, "operator-1", result.OperatorID)
		assert.Equal(t, 100, result.TotalDecisions)
		assert.Equal(t, 60, result.Approved)
		assert.Equal(t, 30, result.Rejected)
		assert.Equal(t, 10, result.Escalated)
		assert.Equal(t, 45.5, result.AvgResponseTime)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("operator not found"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetOperatorStats("operator-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		result, err := client.GetOperatorStats("operator-1")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// APPROVE DECISION TESTS
// ============================================================================

func TestGovernanceClientApproveDecision(t *testing.T) {
	t.Run("successful approval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/decision/dec-123/approve", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var req ApproveDecisionRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "session-123", req.SessionID)

			resp := DecisionActionResponse{
				Success:    true,
				DecisionID: "dec-123",
				Action:     "approve",
				Timestamp:  time.Now().Format(time.RFC3339),
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := ApproveDecisionRequest{SessionID: "session-123"}

		result, err := client.ApproveDecision("dec-123", req)

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, "dec-123", result.DecisionID)
		assert.Equal(t, "approve", result.Action)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid request"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := ApproveDecisionRequest{SessionID: "session-123"}

		result, err := client.ApproveDecision("dec-123", req)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := ApproveDecisionRequest{SessionID: "session-123"}

		result, err := client.ApproveDecision("dec-123", req)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// REJECT DECISION TESTS
// ============================================================================

func TestGovernanceClientRejectDecision(t *testing.T) {
	t.Run("successful rejection", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/decision/dec-456/reject", r.URL.Path)
			assert.Equal(t, "POST", r.Method)

			var req RejectDecisionRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "session-123", req.SessionID)

			resp := DecisionActionResponse{
				Success:    true,
				DecisionID: "dec-456",
				Action:     "reject",
				Timestamp:  time.Now().Format(time.RFC3339),
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := RejectDecisionRequest{SessionID: "session-123"}

		result, err := client.RejectDecision("dec-456", req)

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, "dec-456", result.DecisionID)
		assert.Equal(t, "reject", result.Action)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("forbidden"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := RejectDecisionRequest{SessionID: "session-123"}

		result, err := client.RejectDecision("dec-456", req)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "403")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := RejectDecisionRequest{SessionID: "session-123"}

		result, err := client.RejectDecision("dec-456", req)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// ESCALATE DECISION TESTS
// ============================================================================

func TestGovernanceClientEscalateDecision(t *testing.T) {
	t.Run("successful escalation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/decision/dec-789/escalate", r.URL.Path)
			assert.Equal(t, "POST", r.Method)

			var req EscalateDecisionRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "session-123", req.SessionID)
			assert.Equal(t, "Need senior review", req.Reasoning)

			resp := DecisionActionResponse{
				Success:    true,
				DecisionID: "dec-789",
				Action:     "escalate",
				Timestamp:  time.Now().Format(time.RFC3339),
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := EscalateDecisionRequest{
			SessionID: "session-123",
			Reasoning: "Need senior review",
		}

		result, err := client.EscalateDecision("dec-789", req)

		require.NoError(t, err)
		assert.True(t, result.Success)
		assert.Equal(t, "dec-789", result.DecisionID)
		assert.Equal(t, "escalate", result.Action)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("server error"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := EscalateDecisionRequest{
			SessionID: "session-123",
			Reasoning: "reason",
		}

		result, err := client.EscalateDecision("dec-789", req)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		req := EscalateDecisionRequest{
			SessionID: "session-123",
			Reasoning: "reason",
		}

		result, err := client.EscalateDecision("dec-789", req)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// ENQUEUE TEST DECISION TESTS
// ============================================================================

func TestGovernanceClientEnqueueTestDecision(t *testing.T) {
	t.Run("successful test decision enqueue", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/test/enqueue", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var req map[string]interface{}
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "test-decision", req["decision_id"])

			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		decision := map[string]interface{}{
			"decision_id": "test-decision",
			"category":    "security",
			"severity":    "high",
		}

		err := client.EnqueueTestDecision(decision)

		require.NoError(t, err)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid decision"))
		}))
		defer server.Close()

		client := NewGovernanceClient(server.URL)

		decision := map[string]interface{}{"decision_id": "test"}

		err := client.EnqueueTestDecision(decision)

		require.Error(t, err)
		assert.Contains(t, err.Error(), "400")
	})

	t.Run("error on connection failure", func(t *testing.T) {
		client := NewGovernanceClient("http://invalid-host:99999")

		decision := map[string]interface{}{"decision_id": "test"}

		err := client.EnqueueTestDecision(decision)

		require.Error(t, err)
	})
}
