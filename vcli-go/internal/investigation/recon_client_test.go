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
// RECON CLIENT TESTS
// ============================================================================

func TestNewReconClient(t *testing.T) {
	t.Run("creates client with endpoint and token", func(t *testing.T) {
		client := NewReconClient("http://localhost:8080", "test-token")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8080", client.baseURL)
		assert.Equal(t, "test-token", client.authToken)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("creates client without auth token", func(t *testing.T) {
		client := NewReconClient("http://localhost:8080", "")

		require.NotNil(t, client)
		assert.Equal(t, "", client.authToken)
	})
}

// ============================================================================
// RECON STATUS ENUM TESTS
// ============================================================================

func TestReconStatus(t *testing.T) {
	t.Run("recon status constants", func(t *testing.T) {
		assert.Equal(t, ReconStatus("pending"), ReconStatusPending)
		assert.Equal(t, ReconStatus("running"), ReconStatusRunning)
		assert.Equal(t, ReconStatus("completed"), ReconStatusCompleted)
		assert.Equal(t, ReconStatus("failed"), ReconStatusFailed)
		assert.Equal(t, ReconStatus("cancelled"), ReconStatusCancelled)
	})
}

// ============================================================================
// START RECON TESTS
// ============================================================================

func TestStartRecon(t *testing.T) {
	t.Run("successful recon start", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/start_recon", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// Verify request body
			var req StartReconRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "192.168.1.0/24", req.Target)
			assert.Equal(t, "nmap_full", req.ScanType)

			resp := ReconTask{
				ID:        "task-123",
				Target:    "192.168.1.0/24",
				ScanType:  "nmap_full",
				StartTime: "2024-01-01T00:00:00Z",
				Status:    ReconStatusPending,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")
		params := map[string]interface{}{"aggressive": true}

		result, err := client.StartRecon("192.168.1.0/24", "nmap_full", params)

		require.NoError(t, err)
		assert.Equal(t, "task-123", result.ID)
		assert.Equal(t, "192.168.1.0/24", result.Target)
		assert.Equal(t, "nmap_full", result.ScanType)
		assert.Equal(t, ReconStatusPending, result.Status)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := ReconTask{
				ID:     "task-456",
				Status: ReconStatusRunning,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "")

		result, err := client.StartRecon("target", "type", nil)

		require.NoError(t, err)
		assert.Equal(t, "task-456", result.ID)
		assert.Equal(t, ReconStatusRunning, result.Status)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid target"))
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.StartRecon("invalid", "type", nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
		assert.Contains(t, err.Error(), "invalid target")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.StartRecon("target", "type", nil)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewReconClient("://invalid-url", "test-token")

		result, err := client.StartRecon("target", "type", nil)

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET RECON STATUS TESTS
// ============================================================================

func TestGetReconStatus(t *testing.T) {
	t.Run("successful status retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/recon_task/task-123/status", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := ReconTask{
				ID:        "task-123",
				Target:    "example.com",
				ScanType:  "masscan_ports",
				Status:    ReconStatusRunning,
				StartTime: "2024-01-01T00:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.GetReconStatus("task-123")

		require.NoError(t, err)
		assert.Equal(t, "task-123", result.ID)
		assert.Equal(t, ReconStatusRunning, result.Status)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := ReconTask{
				ID:     "task-456",
				Status: ReconStatusCompleted,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "")

		result, err := client.GetReconStatus("task-456")

		require.NoError(t, err)
		assert.Equal(t, "task-456", result.ID)
		assert.Equal(t, ReconStatusCompleted, result.Status)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("task not found"))
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.GetReconStatus("task-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
		assert.Contains(t, err.Error(), "task not found")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewReconClient("://invalid-url", "test-token")

		result, err := client.GetReconStatus("task-123")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET RECON RESULTS TESTS
// ============================================================================

func TestGetReconResults(t *testing.T) {
	t.Run("successful results retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/recon_task/task-123/results", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := ReconResult{
				TaskID: "task-123",
				Status: "completed",
				Output: map[string]interface{}{
					"open_ports": []interface{}{80, 443, 22},
					"services":   map[string]interface{}{"http": "nginx"},
				},
				Timestamp: "2024-01-01T00:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.GetReconResults("task-123")

		require.NoError(t, err)
		assert.Equal(t, "task-123", result.TaskID)
		assert.Equal(t, "completed", result.Status)
		assert.NotNil(t, result.Output)
		assert.Contains(t, result.Output, "open_ports")
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := ReconResult{
				TaskID: "task-456",
				Status: "completed",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "")

		result, err := client.GetReconResults("task-456")

		require.NoError(t, err)
		assert.Equal(t, "task-456", result.TaskID)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("access denied"))
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.GetReconResults("task-123")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "403")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewReconClient("://invalid-url", "test-token")

		result, err := client.GetReconResults("task-123")

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET METRICS TESTS
// ============================================================================

func TestGetMetrics(t *testing.T) {
	t.Run("successful metrics retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/metrics", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := ReconMetrics{
				TotalScans:      100,
				ActiveScans:     5,
				CompletedScans:  90,
				FailedScans:     5,
				AverageDuration: 45.5,
				ScansByType: map[string]int{
					"nmap_full":     50,
					"masscan_ports": 50,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.GetMetrics()

		require.NoError(t, err)
		assert.Equal(t, 100, result.TotalScans)
		assert.Equal(t, 5, result.ActiveScans)
		assert.Equal(t, 90, result.CompletedScans)
		assert.Equal(t, 5, result.FailedScans)
		assert.Equal(t, 45.5, result.AverageDuration)
		assert.Len(t, result.ScansByType, 2)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := ReconMetrics{
				TotalScans: 42,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "")

		result, err := client.GetMetrics()

		require.NoError(t, err)
		assert.Equal(t, 42, result.TotalScans)
	})

	t.Run("error on non-200 status code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("metrics unavailable"))
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.GetMetrics()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewReconClient("://invalid-url", "test-token")

		result, err := client.GetMetrics()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestReconHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			resp := ReconHealthResponse{
				Status:  "healthy",
				Message: "Recon service operational",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
		assert.Equal(t, "Recon service operational", result.Message)
	})

	t.Run("successful without auth token", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Empty(t, r.Header.Get("Authorization"))

			resp := ReconHealthResponse{
				Status: "healthy",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "")

		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
	})

	t.Run("error on unhealthy service", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service down"))
		}))
		defer server.Close()

		client := NewReconClient(server.URL, "test-token")

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
		assert.Contains(t, err.Error(), "service down")
	})

	t.Run("error on request creation failure", func(t *testing.T) {
		client := NewReconClient("://invalid-url", "test-token")

		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}
