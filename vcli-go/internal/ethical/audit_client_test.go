package ethical

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// CONSTRUCTOR TESTS
// ============================================================================

func TestNewAuditClient(t *testing.T) {
	t.Run("creates client with endpoint and token", func(t *testing.T) {
		client := NewAuditClient("http://localhost:8000", "test-token")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Equal(t, "test-token", client.authToken)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("creates client without token", func(t *testing.T) {
		client := NewAuditClient("http://localhost:8000", "")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Empty(t, client.authToken)
	})
}

// ============================================================================
// LOG DECISION TESTS
// ============================================================================

func TestAuditClientLogDecision(t *testing.T) {
	t.Run("successful decision logging", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/audit/decision", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// Decode and validate request body
			var req EthicalDecisionLog
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "decision-123", req.DecisionID)
			assert.Equal(t, "request-456", req.RequestID)
			assert.Equal(t, "maximus", req.ServiceName)

			resp := map[string]interface{}{
				"audit_id":    "audit-789",
				"decision_id": "decision-123",
				"status":      "logged",
				"timestamp":   "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.LogDecision(EthicalDecisionLog{
			DecisionID:  "decision-123",
			RequestID:   "request-456",
			ServiceName: "maximus",
			DecisionType: "access_control",
			Context: map[string]interface{}{
				"user": "admin",
				"resource": "sensitive_data",
			},
			KantianResult: map[string]interface{}{
				"approved": true,
				"confidence": 0.9,
			},
			FinalDecision: map[string]interface{}{
				"action": "allow",
			},
		})

		require.NoError(t, err)
		assert.Equal(t, "audit-789", result["audit_id"])
		assert.Equal(t, "logged", result["status"])
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid decision log"))
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.LogDecision(EthicalDecisionLog{
			DecisionID:  "decision-123",
			ServiceName: "maximus",
		})

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.LogDecision(EthicalDecisionLog{
			DecisionID:  "decision-123",
			ServiceName: "maximus",
		})

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})
}

// ============================================================================
// GET DECISION TESTS
// ============================================================================

func TestAuditClientGetDecision(t *testing.T) {
	t.Run("successful decision retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/audit/decision/decision-123", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := map[string]interface{}{
				"decision_id":   "decision-123",
				"request_id":    "request-456",
				"service_name":  "maximus",
				"decision_type": "access_control",
				"final_decision": map[string]interface{}{
					"action": "allow",
				},
				"timestamp": "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.GetDecision("decision-123")

		require.NoError(t, err)
		assert.Equal(t, "decision-123", result["decision_id"])
		assert.Equal(t, "maximus", result["service_name"])
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("decision not found"))
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.GetDecision("decision-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
	})
}

// ============================================================================
// QUERY DECISIONS TESTS
// ============================================================================

func TestAuditClientQueryDecisions(t *testing.T) {
	t.Run("successful query with filters", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/audit/decisions/query", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var query DecisionHistoryQuery
			err := json.NewDecoder(r.Body).Decode(&query)
			require.NoError(t, err)
			assert.Equal(t, "access_control", query.DecisionType)
			assert.Equal(t, "maximus", query.ServiceName)
			assert.Equal(t, 10, query.Limit)

			resp := DecisionHistoryResponse{
				Total:  25,
				Offset: 0,
				Limit:  10,
				Decisions: []map[string]interface{}{
					{
						"decision_id": "decision-1",
						"service_name": "maximus",
					},
					{
						"decision_id": "decision-2",
						"service_name": "maximus",
					},
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.QueryDecisions(DecisionHistoryQuery{
			DecisionType: "access_control",
			ServiceName:  "maximus",
			Limit:        10,
			Offset:       0,
		})

		require.NoError(t, err)
		assert.Equal(t, 25, result.Total)
		assert.Len(t, result.Decisions, 2)
		assert.Equal(t, "decision-1", result.Decisions[0]["decision_id"])
	})

	t.Run("successful query without filters", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/audit/decisions/query", r.URL.Path)

			resp := DecisionHistoryResponse{
				Total:     100,
				Offset:    0,
				Limit:     50,
				Decisions: []map[string]interface{}{},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.QueryDecisions(DecisionHistoryQuery{})

		require.NoError(t, err)
		assert.Equal(t, 100, result.Total)
		assert.Empty(t, result.Decisions)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("database error"))
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.QueryDecisions(DecisionHistoryQuery{})

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})
}

// ============================================================================
// LOG OVERRIDE TESTS
// ============================================================================

func TestAuditClientLogOverride(t *testing.T) {
	t.Run("successful override logging", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/audit/override", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var override HumanOverrideRequest
			err := json.NewDecoder(r.Body).Decode(&override)
			require.NoError(t, err)
			assert.Equal(t, "decision-123", override.DecisionID)
			assert.Equal(t, "operator-1", override.Operator)
			assert.Equal(t, "safety_concern", override.OverrideReason)

			resp := map[string]interface{}{
				"override_id": "override-789",
				"decision_id": "decision-123",
				"status":      "logged",
				"timestamp":   "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.LogOverride(HumanOverrideRequest{
			DecisionID:     "decision-123",
			OverrideReason: "safety_concern",
			OverrideDecision: map[string]interface{}{
				"action": "deny",
			},
			Operator:      "operator-1",
			Justification: "High risk detected",
		})

		require.NoError(t, err)
		assert.Equal(t, "override-789", result["override_id"])
		assert.Equal(t, "logged", result["status"])
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("unauthorized override"))
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.LogOverride(HumanOverrideRequest{
			DecisionID:     "decision-123",
			OverrideReason: "test",
		})

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "403")
	})
}

// ============================================================================
// GET METRICS TESTS
// ============================================================================

func TestAuditClientGetMetrics(t *testing.T) {
	t.Run("successful metrics retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/audit/metrics", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := EthicalMetrics{
				TotalDecisions: 1000,
				DecisionsByType: map[string]int{
					"access_control": 500,
					"data_processing": 300,
					"resource_allocation": 200,
				},
				HighRiskCount:       50,
				OverrideRate:        0.05,
				ComplianceRate:      0.98,
				AverageDecisionTime: 125.5,
				Timestamp:           "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.GetMetrics()

		require.NoError(t, err)
		assert.Equal(t, 1000, result.TotalDecisions)
		assert.Equal(t, 50, result.HighRiskCount)
		assert.Equal(t, 0.98, result.ComplianceRate)
		assert.Equal(t, 500, result.DecisionsByType["access_control"])
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("metrics unavailable"))
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.GetMetrics()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})
}

// ============================================================================
// GET FRAMEWORK METRICS TESTS
// ============================================================================

func TestAuditClientGetFrameworkMetrics(t *testing.T) {
	t.Run("successful framework metrics retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/audit/metrics/frameworks", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := []FrameworkPerformance{
				{
					Framework:         "kantian",
					TotalEvaluations:  1000,
					ApprovalRate:      0.85,
					AverageConfidence: 0.90,
					AverageLatency:    45.2,
				},
				{
					Framework:         "consequentialist",
					TotalEvaluations:  1000,
					ApprovalRate:      0.78,
					AverageConfidence: 0.82,
					AverageLatency:    52.1,
				},
				{
					Framework:         "virtue",
					TotalEvaluations:  1000,
					ApprovalRate:      0.92,
					AverageConfidence: 0.88,
					AverageLatency:    38.5,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.GetFrameworkMetrics()

		require.NoError(t, err)
		assert.Len(t, result, 3)
		assert.Equal(t, "kantian", result[0].Framework)
		assert.Equal(t, 0.85, result[0].ApprovalRate)
		assert.Equal(t, "virtue", result[2].Framework)
		assert.Equal(t, 0.92, result[2].ApprovalRate)
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("invalid json"))
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.GetFrameworkMetrics()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestAuditClientHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := AuditHealthResponse{
				Status:    "healthy",
				Service:   "ethical-audit",
				Timestamp: "2024-01-01T10:00:00Z",
				Database:  "postgres:connected",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
		assert.Equal(t, "ethical-audit", result.Service)
		assert.Equal(t, "postgres:connected", result.Database)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service unhealthy"))
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})
}

// ============================================================================
// GET STATUS TESTS
// ============================================================================

func TestAuditClientGetStatus(t *testing.T) {
	t.Run("successful status retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/status", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := AuditStatusResponse{
				Service: "ethical-audit",
				Status:  "operational",
				Database: map[string]interface{}{
					"postgres": map[string]interface{}{
						"status":      "connected",
						"latency_ms":  5.2,
						"connections": 10,
					},
				},
				Timestamp: "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.GetStatus()

		require.NoError(t, err)
		assert.Equal(t, "ethical-audit", result.Service)
		assert.Equal(t, "operational", result.Status)
		assert.Contains(t, result.Database, "postgres")
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte("unauthorized"))
		}))
		defer server.Close()

		client := NewAuditClient(server.URL, "test-token")
		result, err := client.GetStatus()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "401")
	})
}
