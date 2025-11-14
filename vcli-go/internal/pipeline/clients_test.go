package pipeline

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewPipelineClient(t *testing.T) {
	client := NewPipelineClient("http://test-pipeline:4444")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-pipeline:4444", client.endpoint)
}

// ============================================================================
// Tataca Ingestion Tests
// ============================================================================

func TestIngest_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/tataca/ingest", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := IngestResult{
			Source:          "threat-feed-alpha",
			RecordsIngested: 15000,
			Status:          "completed",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.Ingest(&IngestRequest{
		Source: "threat-feed-alpha",
		Format: "json",
	})

	require.NoError(t, err)
	assert.Equal(t, "threat-feed-alpha", result.Source)
	assert.Equal(t, 15000, result.RecordsIngested)
	assert.Equal(t, "completed", result.Status)
}

func TestIngest_Processing(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := IngestResult{
			Source:          "large-dataset",
			RecordsIngested: 5000,
			Status:          "processing",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.Ingest(&IngestRequest{Source: "large-dataset", Format: "csv"})

	require.NoError(t, err)
	assert.Equal(t, "processing", result.Status)
}

// ============================================================================
// Seriema Graph Tests
// ============================================================================

func TestGraphQuery_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/seriema/query", r.URL.Path)

		response := GraphQueryResult{
			Results: []map[string]interface{}{
				{"node": "APT29", "attacks": 45},
				{"node": "APT28", "attacks": 32},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.GraphQuery(&GraphQueryRequest{
		Cypher: "MATCH (n:ThreatActor) RETURN n",
	})

	require.NoError(t, err)
	assert.Len(t, result.Results, 2)
}

func TestGraphQuery_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := GraphQueryResult{Results: []map[string]interface{}{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.GraphQuery(&GraphQueryRequest{Cypher: "MATCH (n:NonExistent) RETURN n"})

	require.NoError(t, err)
	assert.Empty(t, result.Results)
}

func TestVisualize_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/seriema/visualize", r.URL.Path)

		response := VisualizeResult{
			Entity:    "APT29",
			NodeCount: 150,
			EdgeCount: 320,
			GraphURL:  "https://viz.example.com/graph/apt29",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.Visualize(&VisualizeRequest{Entity: "APT29"})

	require.NoError(t, err)
	assert.Equal(t, "APT29", result.Entity)
	assert.Greater(t, result.NodeCount, 100)
	assert.NotEmpty(t, result.GraphURL)
}

// ============================================================================
// Command Bus Tests
// ============================================================================

func TestPublishCommand_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/command_bus/publish", r.URL.Path)

		response := CommandResult{
			Topic:     "threat-updates",
			MessageID: "msg-12345",
			Status:    "published",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.PublishCommand(&CommandRequest{
		Topic:   "threat-updates",
		Message: `{"threat":"ransomware","severity":"high"}`,
	})

	require.NoError(t, err)
	assert.Equal(t, "threat-updates", result.Topic)
	assert.Equal(t, "msg-12345", result.MessageID)
	assert.Equal(t, "published", result.Status)
}

func TestPublishCommand_Queued(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := CommandResult{
			Topic:     "low-priority",
			MessageID: "msg-67890",
			Status:    "queued",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.PublishCommand(&CommandRequest{Topic: "low-priority", Message: "test"})

	require.NoError(t, err)
	assert.Equal(t, "queued", result.Status)
}

func TestListTopics_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/command_bus/topics", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := TopicListResult{
			Topics: []TopicInfo{
				{Name: "threat-updates", Subscribers: 5, MessageCount: 1200},
				{Name: "incident-reports", Subscribers: 3, MessageCount: 450},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.ListTopics()

	require.NoError(t, err)
	assert.Len(t, result.Topics, 2)
	assert.Equal(t, "threat-updates", result.Topics[0].Name)
	assert.Greater(t, result.Topics[0].MessageCount, 1000)
}

func TestListTopics_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := TopicListResult{Topics: []TopicInfo{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.ListTopics()

	require.NoError(t, err)
	assert.Empty(t, result.Topics)
}

// ============================================================================
// Status Tests
// ============================================================================

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:         "operational",
			TatacaIngested: 2500000,
			SeriemaNodes:   15000,
			BusMessages:    850000,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "operational", result.Status)
	assert.Greater(t, result.TatacaIngested, 2000000)
	assert.Greater(t, result.SeriemaNodes, 10000)
}

// ============================================================================
// Error Handling Tests
// ============================================================================

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)

	t.Run("Ingest", func(t *testing.T) {
		_, err := client.Ingest(&IngestRequest{})
		assert.Error(t, err)
	})

	t.Run("GraphQuery", func(t *testing.T) {
		_, err := client.GraphQuery(&GraphQueryRequest{})
		assert.Error(t, err)
	})

	t.Run("Visualize", func(t *testing.T) {
		_, err := client.Visualize(&VisualizeRequest{})
		assert.Error(t, err)
	})

	t.Run("PublishCommand", func(t *testing.T) {
		_, err := client.PublishCommand(&CommandRequest{})
		assert.Error(t, err)
	})

	t.Run("ListTopics", func(t *testing.T) {
		_, err := client.ListTopics()
		assert.Error(t, err)
	})

	t.Run("GetStatus", func(t *testing.T) {
		_, err := client.GetStatus()
		assert.Error(t, err)
	})
}

// ============================================================================
// Benchmark Tests
// ============================================================================

func BenchmarkIngest(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(IngestResult{Source: "test", Status: "completed"})
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	req := &IngestRequest{Source: "test", Format: "json"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Ingest(req)
	}
}

func BenchmarkGraphQuery(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(GraphQueryResult{Results: []map[string]interface{}{}})
	}))
	defer server.Close()

	client := NewPipelineClient(server.URL)
	req := &GraphQueryRequest{Cypher: "MATCH (n) RETURN n"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GraphQuery(req)
	}
}
