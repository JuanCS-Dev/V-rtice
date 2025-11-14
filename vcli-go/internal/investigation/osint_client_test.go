package investigation

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// OSINT CLIENT TESTS
// ============================================================================

func TestNewOSINTClient(t *testing.T) {
	t.Run("creates client with endpoint and token", func(t *testing.T) {
		client := NewOSINTClient("http://localhost:8080", "test-token")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8080", client.baseURL)
		assert.Equal(t, "test-token", client.authToken)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("creates client without auth token", func(t *testing.T) {
		client := NewOSINTClient("http://localhost:8080", "")

		require.NotNil(t, client)
		assert.Equal(t, "", client.authToken)
	})
}

// ============================================================================
// START INVESTIGATION TESTS
// ============================================================================

func TestStartInvestigation(t *testing.T) {
	t.Run("successful investigation start", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/start_investigation", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// Verify request body
			var req StartInvestigationRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "test-query", req.Query)
			assert.Equal(t, "person_recon", req.InvestigationType)

			resp := StartInvestigationResponse{
				InvestigationID: "inv-12345",
				Status:          "started",
				Timestamp:       "2024-01-01T00:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")
		params := map[string]interface{}{"depth": "full"}

		result, err := client.StartInvestigation("test-query", "person_recon", params)

		require.NoError(t, err)
		assert.Equal(t, "inv-12345", result.InvestigationID)
		assert.Equal(t, "started", result.Status)
		assert.Equal(t, "2024-01-01T00:00:00Z", result.Timestamp)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := StartInvestigationResponse{
				InvestigationID: "inv-67890",
				Status:          "started",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "")

		result, err := client.StartInvestigation("query", "type", nil)

		require.NoError(t, err)
		assert.Equal(t, "inv-67890", result.InvestigationID)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid request"))
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.StartInvestigation("query", "type", nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
		assert.Contains(t, err.Error(), "invalid request")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("invalid json"))
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.StartInvestigation("query", "type", nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewOSINTClient("://invalid-url", "test-token")

		result, err := client.StartInvestigation("query", "type", nil)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET INVESTIGATION STATUS TESTS
// ============================================================================

func TestGetInvestigationStatus(t *testing.T) {
	t.Run("successful status retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/investigation/inv-123/status", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := InvestigationStatus{
				ID:          "inv-123",
				Query:       "test query",
				Type:        "person_recon",
				Status:      "in_progress",
				Progress:    0.5,
				StartTime:   "2024-01-01T00:00:00Z",
				CurrentStep: "analyzing_data",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.GetInvestigationStatus("inv-123")

		require.NoError(t, err)
		assert.Equal(t, "inv-123", result.ID)
		assert.Equal(t, "in_progress", result.Status)
		assert.Equal(t, 0.5, result.Progress)
		assert.Equal(t, "analyzing_data", result.CurrentStep)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := InvestigationStatus{
				ID:     "inv-456",
				Status: "completed",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "")

		result, err := client.GetInvestigationStatus("inv-456")

		require.NoError(t, err)
		assert.Equal(t, "inv-456", result.ID)
		assert.Equal(t, "completed", result.Status)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("investigation not found"))
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.GetInvestigationStatus("inv-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
		assert.Contains(t, err.Error(), "investigation not found")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.GetInvestigationStatus("inv-123")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewOSINTClient("://invalid-url", "test-token")

		result, err := client.GetInvestigationStatus("inv-123")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET INVESTIGATION REPORT TESTS
// ============================================================================

func TestGetInvestigationReport(t *testing.T) {
	t.Run("successful report retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/investigation/inv-123/report", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// API returns raw map that gets converted to InvestigationReport
			rawReport := map[string]interface{}{
				"investigation_id":   "inv-123",
				"query":              "test query",
				"investigation_type": "person_recon",
				"summary":            "Test summary",
				"findings": []interface{}{
					map[string]interface{}{"key": "value"},
				},
				"collected_data": []interface{}{
					map[string]interface{}{"source": "twitter"},
				},
				"analysis_results": map[string]interface{}{
					"confidence": 0.9,
				},
				"recommendations": []interface{}{"Review findings"},
				"timestamp":       "2024-01-01T00:00:00Z",
			}
			json.NewEncoder(w).Encode(rawReport)
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.GetInvestigationReport("inv-123")

		require.NoError(t, err)
		assert.Equal(t, "inv-123", result.InvestigationID)
		assert.Equal(t, "test query", result.Query)
		assert.Equal(t, "person_recon", result.InvestigationType)
		assert.Equal(t, "Test summary", result.Summary)
		assert.Len(t, result.Findings, 1)
		assert.Len(t, result.CollectedData, 1)
		assert.NotNil(t, result.AnalysisResults)
		assert.Len(t, result.Recommendations, 1)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			rawReport := map[string]interface{}{
				"investigation_id": "inv-456",
				"summary":          "Test",
			}
			json.NewEncoder(w).Encode(rawReport)
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "")

		result, err := client.GetInvestigationReport("inv-456")

		require.NoError(t, err)
		assert.Equal(t, "inv-456", result.InvestigationID)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("access denied"))
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.GetInvestigationReport("inv-123")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "403")
		assert.Contains(t, err.Error(), "access denied")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("invalid"))
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.GetInvestigationReport("inv-123")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewOSINTClient("://invalid-url", "test-token")

		result, err := client.GetInvestigationReport("inv-123")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := OSINTHealthResponse{
				Status:  "healthy",
				Message: "Service is running",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
		assert.Equal(t, "Service is running", result.Message)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := OSINTHealthResponse{
				Status: "healthy",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "")

		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
	})

	t.Run("error on unhealthy service", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service unavailable"))
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
		assert.Contains(t, err.Error(), "service unavailable")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewOSINTClient(server.URL, "test-token")

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewOSINTClient("://invalid-url", "test-token")

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}
