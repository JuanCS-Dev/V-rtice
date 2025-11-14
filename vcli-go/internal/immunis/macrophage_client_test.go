package immunis

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ============================================================================
// CONSTRUCTOR TESTS
// ============================================================================

func TestNewMacrophageClient(t *testing.T) {
	t.Run("creates client with endpoint and token", func(t *testing.T) {
		client := NewMacrophageClient("http://localhost:8000", "test-token")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Equal(t, "test-token", client.authToken)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("creates client without token", func(t *testing.T) {
		client := NewMacrophageClient("http://localhost:8000", "")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Empty(t, client.authToken)
	})
}

// ============================================================================
// PHAGOCYTOSE TESTS
// ============================================================================

func TestMacrophageClientPhagocytose(t *testing.T) {
	t.Run("successful file upload", func(t *testing.T) {
		// Create temporary test file
		tmpDir := t.TempDir()
		testFile := filepath.Join(tmpDir, "malware.exe")
		err := os.WriteFile(testFile, []byte("fake malware content"), 0644)
		require.NoError(t, err)

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/phagocytose", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Contains(t, r.Header.Get("Content-Type"), "multipart/form-data")
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// Parse multipart form
			err := r.ParseMultipartForm(10 << 20) // 10 MB
			require.NoError(t, err)

			// Check file field
			_, fileHeader, err := r.FormFile("file")
			require.NoError(t, err)
			assert.Equal(t, "malware.exe", fileHeader.Filename)

			// Check malware_family field
			assert.Equal(t, "trojan", r.FormValue("malware_family"))

			resp := PhagocytoseResponse{
				Status: "processed",
				Artifact: map[string]interface{}{
					"id":      "artifact-123",
					"family":  "trojan",
					"sha256":  "abc123",
				},
				Timestamp: "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.Phagocytose(testFile, "trojan")

		require.NoError(t, err)
		assert.Equal(t, "processed", result.Status)
		assert.Equal(t, "artifact-123", result.Artifact["id"])
	})

	t.Run("error on non-existent file", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			t.Fatal("should not reach server")
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.Phagocytose("/nonexistent/file.exe", "trojan")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to open file")
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		tmpDir := t.TempDir()
		testFile := filepath.Join(tmpDir, "test.exe")
		err := os.WriteFile(testFile, []byte("test"), 0644)
		require.NoError(t, err)

		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid malware file"))
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.Phagocytose(testFile, "trojan")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "400")
	})
}

// ============================================================================
// PRESENT ANTIGEN TESTS
// ============================================================================

func TestMacrophageClientPresentAntigen(t *testing.T) {
	t.Run("successful antigen presentation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/present_antigen", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			var req PresentAntigenRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, "artifact-123", req.Artifact["id"])

			resp := PresentAntigenResponse{
				Status:    "presented",
				Message:   "Antigen presented to dendritic cells",
				Timestamp: "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.PresentAntigen(map[string]interface{}{
			"id":     "artifact-123",
			"family": "trojan",
			"sha256": "abc123",
		})

		require.NoError(t, err)
		assert.Equal(t, "presented", result.Status)
		assert.Contains(t, result.Message, "dendritic cells")
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("dendritic cells offline"))
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.PresentAntigen(map[string]interface{}{
			"id": "artifact-123",
		})

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("not json"))
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.PresentAntigen(map[string]interface{}{})

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})
}

// ============================================================================
// CLEANUP TESTS
// ============================================================================

func TestMacrophageClientCleanup(t *testing.T) {
	t.Run("successful cleanup", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/cleanup", r.URL.Path)
			assert.Equal(t, "POST", r.Method)

			resp := CleanupResponse{
				Status:           "cleaned",
				ArtifactsRemoved: 42,
				Timestamp:        "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.Cleanup()

		require.NoError(t, err)
		assert.Equal(t, "cleaned", result.Status)
		assert.Equal(t, 42, result.ArtifactsRemoved)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("cleanup failed"))
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.Cleanup()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})
}

// ============================================================================
// GET STATUS TESTS
// ============================================================================

func TestMacrophageClientGetStatus(t *testing.T) {
	t.Run("successful status retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/status", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := StatusResponse{
				CuckooEnabled:            true,
				KafkaEnabled:             true,
				ProcessedArtifactsCount:  150,
				GeneratedSignaturesCount: 75,
				Timestamp:                "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.GetStatus()

		require.NoError(t, err)
		assert.True(t, result.CuckooEnabled)
		assert.True(t, result.KafkaEnabled)
		assert.Equal(t, 150, result.ProcessedArtifactsCount)
		assert.Equal(t, 75, result.GeneratedSignaturesCount)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte("unauthorized"))
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.GetStatus()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "401")
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestMacrophageClientHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := HealthResponse{
				Status:          "healthy",
				Service:         "immunis-macrophage",
				CuckooEnabled:   true,
				KafkaEnabled:    true,
				ArtifactsCount:  250,
				SignaturesCount: 125,
				Timestamp:       "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
		assert.Equal(t, "immunis-macrophage", result.Service)
		assert.True(t, result.CuckooEnabled)
		assert.Equal(t, 250, result.ArtifactsCount)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service unhealthy"))
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})
}

// ============================================================================
// GET ARTIFACTS TESTS
// ============================================================================

func TestMacrophageClientGetArtifacts(t *testing.T) {
	t.Run("successful artifacts retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/artifacts", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := ArtifactsResponse{
				Status: "success",
				Artifacts: []map[string]interface{}{
					{
						"id":     "artifact-1",
						"family": "trojan",
						"sha256": "abc123",
					},
					{
						"id":     "artifact-2",
						"family": "ransomware",
						"sha256": "def456",
					},
				},
				Count:     2,
				Timestamp: "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.GetArtifacts()

		require.NoError(t, err)
		assert.Equal(t, "success", result.Status)
		assert.Equal(t, 2, result.Count)
		assert.Len(t, result.Artifacts, 2)
		assert.Equal(t, "artifact-1", result.Artifacts[0]["id"])
		assert.Equal(t, "trojan", result.Artifacts[0]["family"])
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("no artifacts found"))
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.GetArtifacts()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
	})
}

// ============================================================================
// GET SIGNATURES TESTS
// ============================================================================

func TestMacrophageClientGetSignatures(t *testing.T) {
	t.Run("successful signatures retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/signatures", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := SignaturesResponse{
				Status: "success",
				Signatures: []map[string]interface{}{
					{
						"id":          "sig-1",
						"family":      "trojan",
						"pattern":     "malicious_pattern_1",
						"confidence":  0.95,
					},
					{
						"id":          "sig-2",
						"family":      "ransomware",
						"pattern":     "malicious_pattern_2",
						"confidence":  0.88,
					},
				},
				Count:     2,
				Timestamp: "2024-01-01T10:00:00Z",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.GetSignatures()

		require.NoError(t, err)
		assert.Equal(t, "success", result.Status)
		assert.Equal(t, 2, result.Count)
		assert.Len(t, result.Signatures, 2)
		assert.Equal(t, "sig-1", result.Signatures[0]["id"])
		assert.Equal(t, "trojan", result.Signatures[0]["family"])
		assert.Equal(t, 0.95, result.Signatures[0]["confidence"])
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("invalid json"))
		}))
		defer server.Close()

		client := NewMacrophageClient(server.URL, "test-token")
		result, err := client.GetSignatures()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "failed to decode response")
	})
}
