package maba

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestNewMABAClient verifies client creation
func TestNewMABAClient(t *testing.T) {
	client := NewMABAClient("http://test-maba:9700")
	assert.NotNil(t, client)
	assert.NotNil(t, client.httpClient)
	assert.Equal(t, "http://test-maba:9700", client.endpoint)
}

// TestNewMABAClient_DefaultEndpoint verifies default endpoint from config
func TestNewMABAClient_DefaultEndpoint(t *testing.T) {
	client := NewMABAClient("")
	assert.NotNil(t, client)
	assert.NotEmpty(t, client.endpoint, "Should use config default endpoint")
}

// TestNavigate_Success verifies successful navigation
func TestNavigate_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/navigate", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		// Verify request body
		var req NavigateRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "https://example.com", req.URL)
		assert.Equal(t, "click", req.Action)

		// Send response
		response := NavigateResult{
			URL:      "https://example.com",
			Title:    "Example Domain",
			LoadTime: 250,
			Status:   "success",
			ExtractedData: map[string]interface{}{
				"links": 5,
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.Navigate(&NavigateRequest{
		URL:    "https://example.com",
		Action: "click",
		Wait:   true,
	})

	require.NoError(t, err)
	assert.Equal(t, "https://example.com", result.URL)
	assert.Equal(t, "Example Domain", result.Title)
	assert.Equal(t, 250, result.LoadTime)
	assert.Equal(t, "success", result.Status)
	assert.Equal(t, float64(5), result.ExtractedData["links"])
}

// TestNavigate_ServerError verifies error handling
func TestNavigate_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.Navigate(&NavigateRequest{URL: "https://example.com"})

	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "navigate failed")
}

// TestExtract_Success verifies successful data extraction
func TestExtract_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/extract", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req ExtractRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "https://example.com", req.URL)
		assert.Equal(t, "div.content", req.Query)

		response := ExtractResult{
			URL: "https://example.com",
			Data: []map[string]interface{}{
				{"text": "Item 1", "id": float64(1)},
				{"text": "Item 2", "id": float64(2)},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.Extract(&ExtractRequest{
		URL:   "https://example.com",
		Query: "div.content",
	})

	require.NoError(t, err)
	assert.Equal(t, "https://example.com", result.URL)
	assert.Len(t, result.Data, 2)
	assert.Equal(t, "Item 1", result.Data[0]["text"])
	assert.Equal(t, float64(1), result.Data[0]["id"])
}

// TestExtract_EmptyResults verifies handling of empty extraction
func TestExtract_EmptyResults(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ExtractResult{
			URL:  "https://example.com",
			Data: []map[string]interface{}{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.Extract(&ExtractRequest{
		URL:   "https://example.com",
		Query: "div.nonexistent",
	})

	require.NoError(t, err)
	assert.Empty(t, result.Data)
}

// TestListSessions_Success verifies session listing
func TestListSessions_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/sessions", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := SessionListResult{
			Sessions: []BrowserSession{
				{
					ID:            "session-1",
					CurrentURL:    "https://example.com",
					Duration:      3600,
					ResourceUsage: 256,
					Status:        "active",
				},
				{
					ID:            "session-2",
					CurrentURL:    "https://test.com",
					Duration:      1800,
					ResourceUsage: 128,
					Status:        "idle",
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.ListSessions()

	require.NoError(t, err)
	assert.Len(t, result.Sessions, 2)
	assert.Equal(t, "session-1", result.Sessions[0].ID)
	assert.Equal(t, "active", result.Sessions[0].Status)
	assert.Equal(t, 3600, result.Sessions[0].Duration)
}

// TestListSessions_Empty verifies empty session list
func TestListSessions_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SessionListResult{
			Sessions: []BrowserSession{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.ListSessions()

	require.NoError(t, err)
	assert.Empty(t, result.Sessions)
}

// TestQueryMap_Success verifies cognitive map querying
func TestQueryMap_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/cognitive-map/query", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req MapQueryRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "example.com", req.Domain)

		response := MapQueryResult{
			Domain:     "example.com",
			PageCount:  50,
			PathCount:  120,
			Confidence: 0.95,
			CommonPaths: []NavigationPath{
				{Path: "/home -> /products", Usage: 45},
				{Path: "/products -> /cart", Usage: 30},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.QueryMap(&MapQueryRequest{Domain: "example.com"})

	require.NoError(t, err)
	assert.Equal(t, "example.com", result.Domain)
	assert.Equal(t, 50, result.PageCount)
	assert.Equal(t, 120, result.PathCount)
	assert.Equal(t, 0.95, result.Confidence)
	assert.Len(t, result.CommonPaths, 2)
	assert.Equal(t, "/home -> /products", result.CommonPaths[0].Path)
	assert.Equal(t, 45, result.CommonPaths[0].Usage)
}

// TestQueryMap_UnknownDomain verifies handling of unknown domain
func TestQueryMap_UnknownDomain(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := MapQueryResult{
			Domain:      "unknown.com",
			PageCount:   0,
			PathCount:   0,
			Confidence:  0.0,
			CommonPaths: []NavigationPath{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.QueryMap(&MapQueryRequest{Domain: "unknown.com"})

	require.NoError(t, err)
	assert.Equal(t, 0, result.PageCount)
	assert.Equal(t, 0.0, result.Confidence)
}

// TestMapStats_Success verifies map statistics retrieval
func TestMapStats_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/cognitive-map/stats", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := MapStatsResult{
			TotalDomains:      25,
			TotalPages:        1500,
			TotalPaths:        4500,
			TotalInteractions: 12000,
			TopDomains: []DomainStats{
				{Domain: "example.com", Visits: 500},
				{Domain: "test.com", Visits: 300},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.MapStats()

	require.NoError(t, err)
	assert.Equal(t, 25, result.TotalDomains)
	assert.Equal(t, 1500, result.TotalPages)
	assert.Equal(t, 4500, result.TotalPaths)
	assert.Equal(t, 12000, result.TotalInteractions)
	assert.Len(t, result.TopDomains, 2)
	assert.Equal(t, "example.com", result.TopDomains[0].Domain)
	assert.Equal(t, 500, result.TopDomains[0].Visits)
}

// TestMapStats_Empty verifies empty map statistics
func TestMapStats_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := MapStatsResult{
			TotalDomains:      0,
			TotalPages:        0,
			TotalPaths:        0,
			TotalInteractions: 0,
			TopDomains:        []DomainStats{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.MapStats()

	require.NoError(t, err)
	assert.Equal(t, 0, result.TotalDomains)
	assert.Empty(t, result.TopDomains)
}

// TestListTools_Success verifies tool listing
func TestListTools_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/tools", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := ToolListResult{
			Tools: []MABATool{
				{
					Name:        "web-scraper",
					Description: "Extracts data from web pages",
					Status:      "active",
					UsageCount:  150,
				},
				{
					Name:        "form-filler",
					Description: "Fills web forms automatically",
					Status:      "idle",
					UsageCount:  75,
				},
			},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.ListTools()

	require.NoError(t, err)
	assert.Len(t, result.Tools, 2)
	assert.Equal(t, "web-scraper", result.Tools[0].Name)
	assert.Equal(t, "active", result.Tools[0].Status)
	assert.Equal(t, 150, result.Tools[0].UsageCount)
}

// TestListTools_Empty verifies empty tool list
func TestListTools_Empty(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ToolListResult{
			Tools: []MABATool{},
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.ListTools()

	require.NoError(t, err)
	assert.Empty(t, result.Tools)
}

// TestGetStatus_Success verifies status retrieval
func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/health", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:          "healthy",
			ActiveSessions:  5,
			MapSize:         1024,
			ResourceUsage:   75.5,
			ToolsRegistered: 8,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "healthy", result.Status)
	assert.Equal(t, 5, result.ActiveSessions)
	assert.Equal(t, 1024, result.MapSize)
	assert.Equal(t, 75.5, result.ResourceUsage)
	assert.Equal(t, 8, result.ToolsRegistered)
}

// TestGetStatus_Unhealthy verifies unhealthy status
func TestGetStatus_Unhealthy(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:          "degraded",
			ActiveSessions:  0,
			MapSize:         0,
			ResourceUsage:   95.8,
			ToolsRegistered: 2,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "degraded", result.Status)
	assert.Equal(t, 95.8, result.ResourceUsage)
}

// TestGetStatus_ServerError verifies error handling
func TestGetStatus_ServerError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	result, err := client.GetStatus()

	assert.Error(t, err)
	assert.Nil(t, result)
	assert.Contains(t, err.Error(), "get status failed")
}

// BenchmarkNavigate measures Navigate performance
func BenchmarkNavigate(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := NavigateResult{
			URL:      "https://example.com",
			Title:    "Example",
			LoadTime: 100,
			Status:   "success",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	req := &NavigateRequest{URL: "https://example.com"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Navigate(req)
	}
}

// BenchmarkExtract measures Extract performance
func BenchmarkExtract(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ExtractResult{
			URL:  "https://example.com",
			Data: []map[string]interface{}{{"item": "1"}},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	req := &ExtractRequest{URL: "https://example.com", Query: "div"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Extract(req)
	}
}
