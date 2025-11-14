package vulnscan

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewVulnScanClient(t *testing.T) {
	client := NewVulnScanClient("http://test-vulnscan:8888")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-vulnscan:8888", client.endpoint)
}

// ============================================================================
// Scan Tests
// ============================================================================

func TestScan_CriticalVulnerabilities(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/scan", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := ScanResult{
			ScanID: "scan-abc123",
			Target: "production-server-01",
			Vulnerabilities: []Vulnerability{
				{
					CVE:      "CVE-2024-1234",
					Title:    "Critical Remote Code Execution",
					Severity: "CRITICAL",
					CVSS:     9.8,
				},
				{
					CVE:      "CVE-2024-5678",
					Title:    "SQL Injection in API endpoint",
					Severity: "HIGH",
					CVSS:     8.5,
				},
				{
					CVE:      "CVE-2024-9012",
					Title:    "Cross-Site Scripting (XSS)",
					Severity: "MEDIUM",
					CVSS:     6.1,
				},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)
	result, err := client.Scan(&ScanRequest{
		Target: "production-server-01",
		Full:   true,
	})

	require.NoError(t, err)
	assert.Equal(t, "scan-abc123", result.ScanID)
	assert.Equal(t, "production-server-01", result.Target)
	assert.Len(t, result.Vulnerabilities, 3)

	// Validate critical vulnerability
	critVuln := result.Vulnerabilities[0]
	assert.Equal(t, "CVE-2024-1234", critVuln.CVE)
	assert.Equal(t, "CRITICAL", critVuln.Severity)
	assert.Greater(t, critVuln.CVSS, 9.0)

	// Validate high vulnerability
	highVuln := result.Vulnerabilities[1]
	assert.Equal(t, "HIGH", highVuln.Severity)
	assert.Contains(t, highVuln.Title, "SQL Injection")

	// Validate medium vulnerability
	medVuln := result.Vulnerabilities[2]
	assert.Equal(t, "MEDIUM", medVuln.Severity)
	assert.Contains(t, medVuln.Title, "XSS")
}

func TestScan_NoVulnerabilities(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ScanResult{
			ScanID:          "scan-xyz789",
			Target:          "secure-server",
			Vulnerabilities: []Vulnerability{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)
	result, err := client.Scan(&ScanRequest{Target: "secure-server", Full: false})

	require.NoError(t, err)
	assert.Empty(t, result.Vulnerabilities)
}

func TestScan_QuickScan(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ScanResult{
			ScanID: "scan-quick-001",
			Target: "web-app",
			Vulnerabilities: []Vulnerability{
				{CVE: "CVE-2024-0001", Title: "Outdated dependency", Severity: "LOW", CVSS: 3.1},
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)
	result, err := client.Scan(&ScanRequest{Target: "web-app", Full: false})

	require.NoError(t, err)
	assert.Equal(t, "LOW", result.Vulnerabilities[0].Severity)
	assert.Less(t, result.Vulnerabilities[0].CVSS, 4.0)
}

// ============================================================================
// GetReport Tests
// ============================================================================

func TestGetReport_HighRisk(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/scan/report", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := ReportResult{
			ScanID:    "scan-abc123",
			Critical:  3,
			High:      7,
			Medium:    12,
			Low:       25,
			RiskScore: 8.7,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)
	result, err := client.GetReport(&ReportRequest{ScanID: "scan-abc123"})

	require.NoError(t, err)
	assert.Equal(t, "scan-abc123", result.ScanID)
	assert.Equal(t, 3, result.Critical)
	assert.Equal(t, 7, result.High)
	assert.Equal(t, 12, result.Medium)
	assert.Equal(t, 25, result.Low)
	assert.Equal(t, 8.7, result.RiskScore)
	assert.Greater(t, result.RiskScore, 8.0)

	// Validate total vulnerabilities
	totalVulns := result.Critical + result.High + result.Medium + result.Low
	assert.Equal(t, 47, totalVulns)
}

func TestGetReport_LowRisk(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ReportResult{
			ScanID:    "scan-xyz789",
			Critical:  0,
			High:      0,
			Medium:    2,
			Low:       5,
			RiskScore: 2.3,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)
	result, err := client.GetReport(&ReportRequest{ScanID: "scan-xyz789"})

	require.NoError(t, err)
	assert.Equal(t, 0, result.Critical)
	assert.Equal(t, 0, result.High)
	assert.Less(t, result.RiskScore, 3.0)
}

// ============================================================================
// GetStatus Tests
// ============================================================================

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:              "operational",
			ScansCompleted:      156,
			TotalVulnerabilities: 2847,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "operational", result.Status)
	assert.Equal(t, 156, result.ScansCompleted)
	assert.Equal(t, 2847, result.TotalVulnerabilities)
	assert.Greater(t, result.ScansCompleted, 100)
	assert.Greater(t, result.TotalVulnerabilities, 2000)
}

func TestGetStatus_NoScans(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:              "idle",
			ScansCompleted:      0,
			TotalVulnerabilities: 0,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "idle", result.Status)
	assert.Equal(t, 0, result.ScansCompleted)
	assert.Equal(t, 0, result.TotalVulnerabilities)
}

// ============================================================================
// Error Handling Tests
// ============================================================================

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)

	t.Run("Scan", func(t *testing.T) {
		_, err := client.Scan(&ScanRequest{})
		assert.Error(t, err)
	})

	t.Run("GetReport", func(t *testing.T) {
		_, err := client.GetReport(&ReportRequest{})
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

func BenchmarkScan(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ScanResult{ScanID: "test", Vulnerabilities: []Vulnerability{}})
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)
	req := &ScanRequest{Target: "test", Full: false}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Scan(req)
	}
}

func BenchmarkGetReport(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ReportResult{RiskScore: 5.0})
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)
	req := &ReportRequest{ScanID: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GetReport(req)
	}
}

func BenchmarkGetStatus(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(StatusResult{Status: "operational"})
	}))
	defer server.Close()

	client := NewVulnScanClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GetStatus()
	}
}
