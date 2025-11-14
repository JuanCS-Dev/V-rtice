package edge

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewEdgeClient(t *testing.T) {
	client := NewEdgeClient("http://test-edge:8888")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-edge:8888", client.endpoint)
}

func TestDeploy_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/agents/deploy", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := DeployResult{
			Agent:  "sensor-v2",
			Target: "web-cluster-01",
			Status: "deployed",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewEdgeClient(server.URL)
	result, err := client.Deploy(&DeployRequest{
		Agent:  "sensor-v2",
		Target: "web-cluster-01",
	})

	require.NoError(t, err)
	assert.Equal(t, "sensor-v2", result.Agent)
	assert.Equal(t, "deployed", result.Status)
}

func TestDeploy_Pending(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := DeployResult{
			Agent:  "monitor-v1",
			Target: "database-cluster",
			Status: "pending",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewEdgeClient(server.URL)
	result, err := client.Deploy(&DeployRequest{
		Agent:  "monitor-v1",
		Target: "database-cluster",
	})

	require.NoError(t, err)
	assert.Equal(t, "pending", result.Status)
}

func TestList_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/agents", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := ListResult{
			Agents: []AgentInfo{
				{Name: "sensor-01", Target: "web-01", Status: "active", Version: "2.1.0"},
				{Name: "sensor-02", Target: "web-02", Status: "active", Version: "2.1.0"},
				{Name: "monitor-01", Target: "db-01", Status: "inactive", Version: "1.9.5"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewEdgeClient(server.URL)
	result, err := client.List()

	require.NoError(t, err)
	assert.Len(t, result.Agents, 3)
	assert.Equal(t, "sensor-01", result.Agents[0].Name)
	assert.Equal(t, "active", result.Agents[0].Status)
	assert.Equal(t, "2.1.0", result.Agents[0].Version)
}

func TestList_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ListResult{Agents: []AgentInfo{}}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewEdgeClient(server.URL)
	result, err := client.List()

	require.NoError(t, err)
	assert.Empty(t, result.Agents)
}

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:       "operational",
			ActiveAgents: 47,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewEdgeClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "operational", result.Status)
	assert.Greater(t, result.ActiveAgents, 40)
}

func TestGetStatus_NoAgents(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:       "idle",
			ActiveAgents: 0,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewEdgeClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "idle", result.Status)
	assert.Equal(t, 0, result.ActiveAgents)
}

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewEdgeClient(server.URL)

	t.Run("Deploy", func(t *testing.T) {
		_, err := client.Deploy(&DeployRequest{})
		assert.Error(t, err)
	})

	t.Run("List", func(t *testing.T) {
		_, err := client.List()
		assert.Error(t, err)
	})

	t.Run("GetStatus", func(t *testing.T) {
		_, err := client.GetStatus()
		assert.Error(t, err)
	})
}

func BenchmarkDeploy(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(DeployResult{Agent: "test", Status: "deployed"})
	}))
	defer server.Close()

	client := NewEdgeClient(server.URL)
	req := &DeployRequest{Agent: "test", Target: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Deploy(req)
	}
}
