package governance

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// HTTP CLIENT CONSTRUCTOR TESTS
// ============================================================================

func TestNewHTTPClient(t *testing.T) {
	t.Run("creates client with base URL and operator ID", func(t *testing.T) {
		client := NewHTTPClient("http://localhost:8080", "operator-1")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8080", client.baseURL)
		assert.Equal(t, "operator-1", client.operatorID)
		assert.NotNil(t, client.client)
		assert.Empty(t, client.sessionID)
	})
}

func TestHTTPClientSetSessionID(t *testing.T) {
	t.Run("sets session ID", func(t *testing.T) {
		client := NewHTTPClient("http://localhost:8080", "operator-1")

		client.SetSessionID("session-123")

		assert.Equal(t, "session-123", client.sessionID)
	})
}

// ============================================================================
// APPROVE DECISION TESTS
// ============================================================================

func TestHTTPClientApproveDecision(t *testing.T) {
	t.Run("successful approval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/decision/dec-123/approve", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "operator-1", r.Header.Get("X-Operator-ID"))

			var req struct {
				SessionID string `json:"session_id"`
				Comment   string `json:"comment"`
			}
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "session-123", req.SessionID)
			assert.Equal(t, "Looks good", req.Comment)

			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")
		client.SetSessionID("session-123")

		err := client.ApproveDecision(context.Background(), "dec-123", "Looks good")

		require.NoError(t, err)
	})

	t.Run("successful with 202 Accepted", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusAccepted)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")
		client.SetSessionID("session-123")

		err := client.ApproveDecision(context.Background(), "dec-123", "comment")

		require.NoError(t, err)
	})

	t.Run("error on non-200/202 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid decision"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")
		client.SetSessionID("session-123")

		err := client.ApproveDecision(context.Background(), "dec-123", "comment")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "approval failed with status 400")
		assert.Contains(t, err.Error(), "invalid decision")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewHTTPClient("://invalid-url", "operator-1")

		err := client.ApproveDecision(context.Background(), "dec-123", "comment")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to create request")
	})
}

// ============================================================================
// REJECT DECISION TESTS
// ============================================================================

func TestHTTPClientRejectDecision(t *testing.T) {
	t.Run("successful rejection", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/decision/dec-456/reject", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "operator-1", r.Header.Get("X-Operator-ID"))

			var req struct {
				SessionID string `json:"session_id"`
				Reason    string `json:"reason"`
				Comment   string `json:"comment"`
			}
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "session-123", req.SessionID)
			assert.Equal(t, "False positive", req.Reason)
			assert.Equal(t, "False positive", req.Comment)

			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")
		client.SetSessionID("session-123")

		err := client.RejectDecision(context.Background(), "dec-456", "False positive")

		require.NoError(t, err)
	})

	t.Run("successful with 202 Accepted", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusAccepted)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		err := client.RejectDecision(context.Background(), "dec-456", "reason")

		require.NoError(t, err)
	})

	t.Run("error on non-200/202 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("access denied"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		err := client.RejectDecision(context.Background(), "dec-456", "reason")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "rejection failed with status 403")
		assert.Contains(t, err.Error(), "access denied")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewHTTPClient("://invalid-url", "operator-1")

		err := client.RejectDecision(context.Background(), "dec-456", "reason")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to create request")
	})
}

// ============================================================================
// ESCALATE DECISION TESTS
// ============================================================================

func TestHTTPClientEscalateDecision(t *testing.T) {
	t.Run("successful escalation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/decision/dec-789/escalate", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "operator-1", r.Header.Get("X-Operator-ID"))

			var req struct {
				SessionID        string `json:"session_id"`
				EscalationReason string `json:"escalation_reason"`
			}
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "session-123", req.SessionID)
			assert.Equal(t, "Need senior review", req.EscalationReason)

			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")
		client.SetSessionID("session-123")

		err := client.EscalateDecision(context.Background(), "dec-789", "Need senior review")

		require.NoError(t, err)
	})

	t.Run("successful with 202 Accepted", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusAccepted)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		err := client.EscalateDecision(context.Background(), "dec-789", "reason")

		require.NoError(t, err)
	})

	t.Run("error on non-200/202 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("server error"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		err := client.EscalateDecision(context.Background(), "dec-789", "reason")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "escalation failed with status 500")
		assert.Contains(t, err.Error(), "server error")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewHTTPClient("://invalid-url", "operator-1")

		err := client.EscalateDecision(context.Background(), "dec-789", "reason")

		require.Error(t, err)
		assert.Contains(t, err.Error(), "failed to create request")
	})
}

// ============================================================================
// GET DECISION TESTS
// ============================================================================

func TestHTTPClientGetDecision(t *testing.T) {
	t.Run("successful retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/governance/decisions/dec-123", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "operator-1", r.Header.Get("X-Operator-ID"))

			decision := Decision{
				DecisionID: "dec-123",
				ActionType: "block_ip",
				Target:     "192.168.1.1",
				Status:     DecisionStatusPending,
			}
			json.NewEncoder(w).Encode(decision)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.GetDecision(context.Background(), "dec-123")

		require.NoError(t, err)
		assert.Equal(t, "dec-123", result.DecisionID)
		assert.Equal(t, "block_ip", result.ActionType)
		assert.Equal(t, "192.168.1.1", result.Target)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("decision not found"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.GetDecision(context.Background(), "dec-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "unexpected status 404")
		assert.Contains(t, err.Error(), "decision not found")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.GetDecision(context.Background(), "dec-123")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewHTTPClient("://invalid-url", "operator-1")

		result, err := client.GetDecision(context.Background(), "dec-123")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to create request")
	})
}

// ============================================================================
// LIST DECISIONS TESTS
// ============================================================================

func TestHTTPClientListDecisions(t *testing.T) {
	t.Run("successful list without filter", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/governance/decisions", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "operator-1", r.Header.Get("X-Operator-ID"))

			response := struct {
				Decisions []*Decision `json:"decisions"`
				Total     int         `json:"total"`
			}{
				Decisions: []*Decision{
					{DecisionID: "dec-1", Status: DecisionStatusPending},
					{DecisionID: "dec-2", Status: DecisionStatusPending},
				},
				Total: 2,
			}
			json.NewEncoder(w).Encode(response)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.ListDecisions(context.Background(), nil)

		require.NoError(t, err)
		assert.Len(t, result, 2)
		assert.Equal(t, "dec-1", result[0].DecisionID)
		assert.Equal(t, "dec-2", result[1].DecisionID)
	})

	t.Run("successful list with filter", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/governance/decisions", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			// Check query parameters
			query := r.URL.Query()
			assert.Equal(t, "PENDING", query.Get("status"))
			assert.Equal(t, "HIGH", query.Get("risk_level"))
			assert.Equal(t, "10", query.Get("limit"))
			assert.Equal(t, "5", query.Get("offset"))

			response := struct {
				Decisions []*Decision `json:"decisions"`
				Total     int         `json:"total"`
			}{
				Decisions: []*Decision{
					{DecisionID: "dec-1", Status: DecisionStatusPending, RiskLevel: RiskLevelHigh},
				},
				Total: 1,
			}
			json.NewEncoder(w).Encode(response)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		filter := &DecisionFilter{
			Status:    []DecisionStatus{DecisionStatusPending},
			RiskLevel: []RiskLevel{RiskLevelHigh},
			Limit:     10,
			Offset:    5,
		}

		result, err := client.ListDecisions(context.Background(), filter)

		require.NoError(t, err)
		assert.Len(t, result, 1)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service unavailable"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.ListDecisions(context.Background(), nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "unexpected status 503")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.ListDecisions(context.Background(), nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewHTTPClient("://invalid-url", "operator-1")

		result, err := client.ListDecisions(context.Background(), nil)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET METRICS TESTS
// ============================================================================

func TestHTTPClientGetMetrics(t *testing.T) {
	t.Run("successful metrics retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/session/operator-1/stats", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "operator-1", r.Header.Get("X-Operator-ID"))

			stats := SessionStats{
				TotalDecisions:  100,
				Approved:        60,
				Rejected:        30,
				Escalated:       10,
				AvgResponseTime: 45.5,
			}
			json.NewEncoder(w).Encode(stats)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.GetMetrics(context.Background())

		require.NoError(t, err)
		assert.Equal(t, 60, result.TotalApproved)
		assert.Equal(t, 30, result.TotalRejected)
		assert.Equal(t, 10, result.TotalEscalated)
		assert.Equal(t, 45.5, result.AvgResponseTime)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("internal error"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.GetMetrics(context.Background())

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "unexpected status 500")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.GetMetrics(context.Background())

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewHTTPClient("://invalid-url", "operator-1")

		result, err := client.GetMetrics(context.Background())

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET SESSION STATS TESTS
// ============================================================================

func TestHTTPClientGetSessionStats(t *testing.T) {
	t.Run("successful session stats retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/session/operator-1/stats", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			stats := SessionStats{
				TotalDecisions:   150,
				Approved:         90,
				Rejected:         40,
				Escalated:        20,
				AvgResponseTime:  42.5,
				SessionDuration:  3600.0,
				DecisionsPerHour: 25.0,
			}
			json.NewEncoder(w).Encode(stats)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.GetSessionStats(context.Background())

		require.NoError(t, err)
		assert.Equal(t, 150, result.TotalDecisions)
		assert.Equal(t, 90, result.Approved)
		assert.Equal(t, 40, result.Rejected)
		assert.Equal(t, 20, result.Escalated)
		assert.Equal(t, 42.5, result.AvgResponseTime)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("session not found"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.GetSessionStats(context.Background())

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "unexpected status 404")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewHTTPClient("://invalid-url", "operator-1")

		result, err := client.GetSessionStats(context.Background())

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// CREATE SESSION TESTS
// ============================================================================

func TestHTTPClientCreateSession(t *testing.T) {
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
			assert.Equal(t, "soc_operator", req.OperatorRole)

			session := Session{
				SessionID:    "session-123",
				OperatorID:   req.OperatorID,
				OperatorName: req.OperatorName,
				OperatorRole: req.OperatorRole,
				CreatedAt:    time.Now(),
				ExpiresAt:    time.Now().Add(8 * time.Hour),
				Active:       true,
			}
			json.NewEncoder(w).Encode(session)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.CreateSession(context.Background(), "John Doe", "soc_operator")

		require.NoError(t, err)
		assert.Equal(t, "session-123", result.SessionID)
		assert.Equal(t, "operator-1", result.OperatorID)
		assert.Equal(t, "John Doe", result.OperatorName)
		assert.Equal(t, "soc_operator", result.OperatorRole)
		assert.True(t, result.Active)
		// Session ID should be stored in client
		assert.Equal(t, "session-123", client.sessionID)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte("unauthorized"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.CreateSession(context.Background(), "John Doe", "soc_operator")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "session creation failed with status 401")
		assert.Contains(t, err.Error(), "unauthorized")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		result, err := client.CreateSession(context.Background(), "John Doe", "soc_operator")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewHTTPClient("://invalid-url", "operator-1")

		result, err := client.CreateSession(context.Background(), "John Doe", "soc_operator")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestHTTPClientHealthCheck(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/api/v1/governance/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		healthy, err := client.HealthCheck(context.Background())

		require.NoError(t, err)
		assert.True(t, healthy)
	})

	t.Run("unhealthy service", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		healthy, err := client.HealthCheck(context.Background())

		require.NoError(t, err)
		assert.False(t, healthy)
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewHTTPClient("://invalid-url", "operator-1")

		healthy, err := client.HealthCheck(context.Background())

		require.Error(t, err)
		assert.False(t, healthy)
	})
}

// ============================================================================
// PING SERVER TESTS
// ============================================================================

func TestHTTPClientPingServer(t *testing.T) {
	t.Run("successful ping", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		duration, err := client.PingServer(context.Background())

		require.NoError(t, err)
		assert.Greater(t, duration, time.Duration(0))
	})

	t.Run("error when backend unhealthy", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
		}))
		defer server.Close()

		client := NewHTTPClient(server.URL, "operator-1")

		duration, err := client.PingServer(context.Background())

		require.Error(t, err)
		assert.Equal(t, time.Duration(0), duration)
		assert.Contains(t, err.Error(), "backend unhealthy")
	})

	t.Run("error on request failure", func(t *testing.T) {
		client := NewHTTPClient("http://invalid-host:99999", "operator-1")

		duration, err := client.PingServer(context.Background())

		require.Error(t, err)
		assert.Equal(t, time.Duration(0), duration)
	})
}

// ============================================================================
// CLOSE TESTS
// ============================================================================

func TestHTTPClientClose(t *testing.T) {
	t.Run("closes without error", func(t *testing.T) {
		client := NewHTTPClient("http://localhost:8080", "operator-1")

		err := client.Close()

		require.NoError(t, err)
	})
}
