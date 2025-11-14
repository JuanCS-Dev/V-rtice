package data

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

func TestNewIngestionClient(t *testing.T) {
	t.Run("creates client with endpoint and token", func(t *testing.T) {
		client := NewIngestionClient("http://localhost:8000", "test-token")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Equal(t, "test-token", client.authToken)
		assert.NotNil(t, client.httpClient)
	})

	t.Run("creates client without token", func(t *testing.T) {
		client := NewIngestionClient("http://localhost:8000", "")

		require.NotNil(t, client)
		assert.Equal(t, "http://localhost:8000", client.baseURL)
		assert.Empty(t, client.authToken)
	})
}

// ============================================================================
// CREATE JOB TESTS
// ============================================================================

func TestIngestionClientCreateJob(t *testing.T) {
	t.Run("successful job creation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/jobs", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			// Decode and validate request body
			var req IngestJobRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, DataSourceSinesp, req.Source)
			assert.True(t, req.LoadToPostgres)

			resp := IngestJobResponse{
				JobID:     "job-123",
				Status:    JobStatusPending,
				Source:    DataSourceSinesp,
				CreatedAt: "2024-01-01T10:00:00Z",
				Message:   "Job created successfully",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		entityType := EntityTypePessoa
		result, err := client.CreateJob(IngestJobRequest{
			Source:         DataSourceSinesp,
			EntityType:     &entityType,
			Filters:        map[string]interface{}{"cpf": "12345678900"},
			LoadToPostgres: true,
			LoadToNeo4j:    false,
			Metadata:       map[string]interface{}{"user": "admin"},
		})

		require.NoError(t, err)
		assert.Equal(t, "job-123", result.JobID)
		assert.Equal(t, JobStatusPending, result.Status)
		assert.Equal(t, DataSourceSinesp, result.Source)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte("invalid request"))
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.CreateJob(IngestJobRequest{
			Source:         DataSourceSinesp,
			LoadToPostgres: true,
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

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.CreateJob(IngestJobRequest{
			Source:         DataSourceSinesp,
			LoadToPostgres: true,
		})

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET JOB STATUS TESTS
// ============================================================================

func TestIngestionClientGetJobStatus(t *testing.T) {
	t.Run("successful status retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/jobs/job-123", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "Bearer test-token", r.Header.Get("Authorization"))

			startedAt := "2024-01-01T10:01:00Z"
			resp := IngestJobStatus{
				JobID:            "job-123",
				Status:           JobStatusRunning,
				Source:           DataSourceSinesp,
				CreatedAt:        "2024-01-01T10:00:00Z",
				StartedAt:        &startedAt,
				RecordsProcessed: 100,
				RecordsFailed:    5,
				Metadata:         map[string]interface{}{"user": "admin"},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.GetJobStatus("job-123")

		require.NoError(t, err)
		assert.Equal(t, "job-123", result.JobID)
		assert.Equal(t, JobStatusRunning, result.Status)
		assert.Equal(t, 100, result.RecordsProcessed)
		assert.Equal(t, 5, result.RecordsFailed)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusNotFound)
			w.Write([]byte("job not found"))
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.GetJobStatus("job-999")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "404")
	})
}

// ============================================================================
// LIST JOBS TESTS
// ============================================================================

func TestIngestionClientListJobs(t *testing.T) {
	t.Run("successful list with status filter", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/jobs", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Equal(t, "pending", r.URL.Query().Get("status"))
			assert.Equal(t, "10", r.URL.Query().Get("limit"))

			resp := []IngestJobStatus{
				{
					JobID:            "job-1",
					Status:           JobStatusPending,
					Source:           DataSourceSinesp,
					CreatedAt:        "2024-01-01T10:00:00Z",
					RecordsProcessed: 0,
				},
				{
					JobID:            "job-2",
					Status:           JobStatusPending,
					Source:           DataSourcePrisional,
					CreatedAt:        "2024-01-01T10:05:00Z",
					RecordsProcessed: 0,
				},
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		status := JobStatusPending
		result, err := client.ListJobs(&status, 10)

		require.NoError(t, err)
		assert.Len(t, result, 2)
		assert.Equal(t, "job-1", result[0].JobID)
		assert.Equal(t, JobStatusPending, result[0].Status)
	})

	t.Run("successful list without filters", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/jobs", r.URL.Path)
			assert.Equal(t, "GET", r.Method)
			assert.Empty(t, r.URL.Query().Get("status"))

			resp := []IngestJobStatus{}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.ListJobs(nil, 0)

		require.NoError(t, err)
		assert.Empty(t, result)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte("server error"))
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.ListJobs(nil, 0)

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "500")
	})
}

// ============================================================================
// TRIGGER INGESTION TESTS
// ============================================================================

func TestIngestionClientTriggerIngestion(t *testing.T) {
	t.Run("successful trigger", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/ingest/trigger", r.URL.Path)
			assert.Equal(t, "POST", r.Method)
			assert.Equal(t, "application/json", r.Header.Get("Content-Type"))

			var req TriggerIngestRequest
			err := json.NewDecoder(r.Body).Decode(&req)
			require.NoError(t, err)
			assert.Equal(t, DataSourceANPR, req.Source)

			resp := IngestJobResponse{
				JobID:     "job-456",
				Status:    JobStatusPending,
				Source:    DataSourceANPR,
				CreatedAt: "2024-01-01T10:00:00Z",
				Message:   "Ingestion triggered",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		entityType := EntityTypeVeiculo
		result, err := client.TriggerIngestion(TriggerIngestRequest{
			Source:     DataSourceANPR,
			EntityType: &entityType,
			Filters:    map[string]interface{}{"placa": "ABC1234"},
		})

		require.NoError(t, err)
		assert.Equal(t, "job-456", result.JobID)
		assert.Equal(t, DataSourceANPR, result.Source)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service unavailable"))
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.TriggerIngestion(TriggerIngestRequest{
			Source:  DataSourceSinesp,
			Filters: map[string]interface{}{},
		})

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "503")
	})
}

// ============================================================================
// LIST SOURCES TESTS
// ============================================================================

func TestIngestionClientListSources(t *testing.T) {
	t.Run("successful sources list", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/sources", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := SourcesResponse{
				Sources: map[string]DataSourceInfo{
					"sinesp": {
						Enabled:     true,
						Description: "SINESP vehicle data",
						Entities:    []string{"veiculo"},
						Status:      "operational",
					},
					"prisional": {
						Enabled:     false,
						Description: "Prisional records",
						Entities:    []string{"pessoa"},
						Status:      "maintenance",
					},
				},
				Total:   2,
				Enabled: 1,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.ListSources()

		require.NoError(t, err)
		assert.Equal(t, 2, result.Total)
		assert.Equal(t, 1, result.Enabled)
		assert.Contains(t, result.Sources, "sinesp")
		assert.True(t, result.Sources["sinesp"].Enabled)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusForbidden)
			w.Write([]byte("forbidden"))
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.ListSources()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "403")
	})
}

// ============================================================================
// LIST ENTITY TYPES TESTS
// ============================================================================

func TestIngestionClientListEntityTypes(t *testing.T) {
	t.Run("successful entity types list", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/entities", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := EntitiesResponse{
				Entities: map[string]EntityInfo{
					"pessoa": {
						Description:   "Person entity",
						Fields:        []string{"cpf", "nome", "data_nascimento"},
						PrimaryKey:    "cpf",
						Relationships: []string{"endereco", "ocorrencia"},
					},
					"veiculo": {
						Description:   "Vehicle entity",
						Fields:        []string{"placa", "chassi", "modelo"},
						PrimaryKey:    "placa",
						Relationships: []string{"pessoa"},
					},
				},
				Total: 2,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.ListEntityTypes()

		require.NoError(t, err)
		assert.Equal(t, 2, result.Total)
		assert.Contains(t, result.Entities, "pessoa")
		assert.Contains(t, result.Entities, "veiculo")
		assert.Equal(t, "cpf", result.Entities["pessoa"].PrimaryKey)
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("invalid json"))
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.ListEntityTypes()

		require.Error(t, err)
		assert.Nil(t, result)
	})
}

// ============================================================================
// GET STATISTICS TESTS
// ============================================================================

func TestIngestionClientGetStatistics(t *testing.T) {
	t.Run("successful statistics retrieval", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/stats", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := StatisticsResponse{
				TotalJobs: 150,
				ByStatus: map[string]int{
					"completed": 100,
					"failed":    30,
					"running":   10,
					"pending":   10,
				},
				BySource: map[string]int{
					"sinesp":     80,
					"prisional":  40,
					"anpr":       30,
				},
				RecordsProcessed: 50000,
				RecordsFailed:    1200,
				ActiveJobs:       10,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.GetStatistics()

		require.NoError(t, err)
		assert.Equal(t, 150, result.TotalJobs)
		assert.Equal(t, 50000, result.RecordsProcessed)
		assert.Equal(t, 10, result.ActiveJobs)
		assert.Equal(t, 100, result.ByStatus["completed"])
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte("unauthorized"))
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.GetStatistics()

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "401")
	})
}

// ============================================================================
// CANCEL JOB TESTS
// ============================================================================

func TestIngestionClientCancelJob(t *testing.T) {
	t.Run("successful job cancellation", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/jobs/job-123", r.URL.Path)
			assert.Equal(t, "DELETE", r.Method)

			resp := CancelJobResponse{
				JobID:   "job-123",
				Status:  "cancelled",
				Message: "Job cancelled successfully",
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.CancelJob("job-123")

		require.NoError(t, err)
		assert.Equal(t, "job-123", result.JobID)
		assert.Equal(t, "cancelled", result.Status)
	})

	t.Run("error on non-200 status", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusConflict)
			w.Write([]byte("job already completed"))
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.CancelJob("job-789")

		require.Error(t, err)
		assert.Nil(t, result)
		assert.Contains(t, err.Error(), "409")
	})
}

// ============================================================================
// HEALTH CHECK TESTS
// ============================================================================

func TestIngestionClientHealth(t *testing.T) {
	t.Run("successful health check", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			assert.Equal(t, "/health", r.URL.Path)
			assert.Equal(t, "GET", r.Method)

			resp := HealthResponse{
				Status:          "healthy",
				Service:         "data-ingestion",
				Version:         "1.0.0",
				PostgresHealthy: true,
				Neo4jHealthy:    true,
				ActiveJobs:      5,
			}
			json.NewEncoder(w).Encode(resp)
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.Health()

		require.NoError(t, err)
		assert.Equal(t, "healthy", result.Status)
		assert.Equal(t, "data-ingestion", result.Service)
		assert.True(t, result.PostgresHealthy)
		assert.True(t, result.Neo4jHealthy)
		assert.Equal(t, 5, result.ActiveJobs)
	})

	t.Run("error on invalid JSON response", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("service unhealthy"))
		}))
		defer server.Close()

		client := NewIngestionClient(server.URL, "test-token")
		result, err := client.Health()

		require.Error(t, err)
		assert.Nil(t, result)
		// Health doesn't check status code, so error will be JSON parsing
	})
}
