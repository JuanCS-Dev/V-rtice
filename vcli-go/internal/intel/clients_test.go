package intel

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewIntelClient(t *testing.T) {
	client := NewIntelClient("http://test-intel:9500")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-intel:9500", client.endpoint)
}

func TestSearchGoogle_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/google/search", r.URL.Path)
		response := GoogleSearchResult{
			Query:          "vertice security",
			TotalResults:   150,
			ProcessingTime: 0.45,
			Results: []GoogleResult{
				{Title: "Test Result", URL: "https://test.com", Snippet: "Test snippet"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.SearchGoogle(&GoogleSearchRequest{Query: "vertice security", Depth: "normal"})

	require.NoError(t, err)
	assert.Equal(t, "vertice security", result.Query)
	assert.Equal(t, 150, result.TotalResults)
	assert.Len(t, result.Results, 1)
}

func TestGoogleDork_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := GoogleDorkResult{
			Dork: "filetype:pdf site:example.com",
			Findings: []GoogleDorkFinding{
				{URL: "https://example.com/secret.pdf", RiskLevel: "high", Description: "Exposed document"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.GoogleDork(&GoogleDorkRequest{Dork: "filetype:pdf site:example.com"})

	require.NoError(t, err)
	assert.Len(t, result.Findings, 1)
	assert.Equal(t, "high", result.Findings[0].RiskLevel)
}

func TestLookupIP_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := IPLookupResult{
			IP:               "8.8.8.8",
			Country:          "United States",
			CountryCode:      "US",
			ISP:              "Google LLC",
			Reputation:       "clean",
			ThreatScore:      0,
			ThreatIndicators: []string{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.LookupIP(&IPLookupRequest{IP: "8.8.8.8"})

	require.NoError(t, err)
	assert.Equal(t, "8.8.8.8", result.IP)
	assert.Equal(t, "clean", result.Reputation)
	assert.Equal(t, 0, result.ThreatScore)
}

func TestLookupIP_MaliciousIP(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := IPLookupResult{
			IP:               "192.0.2.1",
			Reputation:       "malicious",
			ThreatScore:      95,
			ThreatIndicators: []string{"botnet", "malware_c2"},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.LookupIP(&IPLookupRequest{IP: "192.0.2.1"})

	require.NoError(t, err)
	assert.Equal(t, "malicious", result.Reputation)
	assert.Greater(t, result.ThreatScore, 90)
	assert.Contains(t, result.ThreatIndicators, "botnet")
}

func TestGeolocationIP_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := IPGeoResult{
			IP:        "8.8.8.8",
			Latitude:  37.386,
			Longitude: -122.084,
			Country:   "United States",
			Region:    "California",
			City:      "Mountain View",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.GeolocationIP(&IPGeoRequest{IP: "8.8.8.8"})

	require.NoError(t, err)
	assert.Equal(t, "Mountain View", result.City)
	assert.InDelta(t, 37.386, result.Latitude, 0.01)
}

func TestSinespPlate_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SinespPlateResult{
			Plate: "ABC1234",
			State: "SP",
			City:  "São Paulo",
			Make:  "Honda",
			Model: "Civic",
			Year:  2020,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.SinespPlate(&SinespPlateRequest{Plate: "ABC1234"})

	require.NoError(t, err)
	assert.Equal(t, "ABC1234", result.Plate)
	assert.Equal(t, "SP", result.State)
	assert.Equal(t, 2020, result.Year)
}

func TestSinespDocument_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SinespDocumentResult{
			Document: "12345678901",
			Name:     "Test Person",
			Status:   "valid",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.SinespDocument(&SinespDocumentRequest{Document: "12345678901"})

	require.NoError(t, err)
	assert.Equal(t, "valid", result.Status)
}

func TestCheckSSL_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SSLCheckResult{
			Domain:          "example.com",
			Status:          "valid",
			DaysUntilExpiry: 90,
			Issuer:          "Let's Encrypt",
			Protocol:        "TLSv1.3",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.CheckSSL(&SSLCheckRequest{Domain: "example.com"})

	require.NoError(t, err)
	assert.Equal(t, "valid", result.Status)
	assert.Equal(t, "TLSv1.3", result.Protocol)
	assert.Equal(t, 90, result.DaysUntilExpiry)
}

func TestCheckSSL_ExpiringSoon(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SSLCheckResult{
			Domain:          "expiring.com",
			Status:          "expiring_soon",
			DaysUntilExpiry: 5,
			Issuer:          "DigiCert",
			Warnings:        []string{"Certificate expires in 5 days"},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.CheckSSL(&SSLCheckRequest{Domain: "expiring.com"})

	require.NoError(t, err)
	assert.Less(t, result.DaysUntilExpiry, 7, "Certificate expiring soon")
	assert.NotEmpty(t, result.Warnings)
}

func TestMonitorSSL_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := SSLMonitorResult{
			Domain:        "example.com",
			MonitorID:     "mon-123",
			CheckInterval: "24h",
			Status:        "active",
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.MonitorSSL(&SSLMonitorRequest{Domain: "example.com"})

	require.NoError(t, err)
	assert.Equal(t, "active", result.Status)
	assert.NotEmpty(t, result.MonitorID)
}

func TestAnalyzeNarrative_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := NarrativeAnalyzeResult{
			ManipulationScore: 0.85,
			CredibilityScore:  0.35,
			Sentiment:         "negative",
			Language:          "en",
			Techniques: []ManipulationTechnique{
				{Name: "emotional_manipulation"},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.AnalyzeNarrative(&NarrativeAnalyzeRequest{Text: "Test narrative content"})

	require.NoError(t, err)
	assert.Equal(t, 0.85, result.ManipulationScore)
	assert.Less(t, result.CredibilityScore, 0.5)
	assert.Len(t, result.Techniques, 1)
}

func TestDetectNarrative_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := NarrativeDetectResult{}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	result, err := client.DetectNarrative(&NarrativeDetectRequest{})

	require.NoError(t, err)
	assert.NotNil(t, result)
}

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)

	t.Run("SearchGoogle", func(t *testing.T) {
		_, err := client.SearchGoogle(&GoogleSearchRequest{Query: "test"})
		assert.Error(t, err)
	})

	t.Run("GoogleDork", func(t *testing.T) {
		_, err := client.GoogleDork(&GoogleDorkRequest{Dork: "test"})
		assert.Error(t, err)
	})

	t.Run("LookupIP", func(t *testing.T) {
		_, err := client.LookupIP(&IPLookupRequest{IP: "1.1.1.1"})
		assert.Error(t, err)
	})
}

func BenchmarkSearchGoogle(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(GoogleSearchResult{Query: "test"})
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	req := &GoogleSearchRequest{Query: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.SearchGoogle(req)
	}
}

func BenchmarkLookupIP(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(IPLookupResult{IP: "1.1.1.1"})
	}))
	defer server.Close()

	client := NewIntelClient(server.URL)
	req := &IPLookupRequest{IP: "1.1.1.1"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.LookupIP(req)
	}
}
