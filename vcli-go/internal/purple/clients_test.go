package purple

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewPurpleClient(t *testing.T) {
	client := NewPurpleClient("http://test-purple:7777")
	assert.NotNil(t, client)
	assert.Equal(t, "http://test-purple:7777", client.endpoint)
}

// ============================================================================
// RunExercise Tests
// ============================================================================

func TestRunExercise_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/exercise/run", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := ExerciseResult{
			ExerciseID: "exercise-123",
			Scenario:   "ransomware-simulation",
			Status:     "completed",
			AttackSteps: []string{
				"Initial access via phishing",
				"Lateral movement to file servers",
				"Encryption of critical files",
			},
			DefenseSteps: []string{
				"EDR detected suspicious process",
				"Network segmentation prevented lateral movement",
				"Backup recovery initiated",
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPurpleClient(server.URL)
	result, err := client.RunExercise(&ExerciseRequest{
		Scenario: "ransomware-simulation",
	})

	require.NoError(t, err)
	assert.Equal(t, "exercise-123", result.ExerciseID)
	assert.Equal(t, "ransomware-simulation", result.Scenario)
	assert.Equal(t, "completed", result.Status)
	assert.Len(t, result.AttackSteps, 3)
	assert.Len(t, result.DefenseSteps, 3)

	// Validate attack steps
	assert.Contains(t, result.AttackSteps[0], "phishing")
	assert.Contains(t, result.AttackSteps[1], "Lateral movement")

	// Validate defense steps
	assert.Contains(t, result.DefenseSteps[0], "EDR")
	assert.Contains(t, result.DefenseSteps[1], "segmentation")
}

func TestRunExercise_InProgress(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ExerciseResult{
			ExerciseID: "exercise-456",
			Scenario:   "apt-intrusion",
			Status:     "in_progress",
			AttackSteps: []string{
				"Reconnaissance phase ongoing",
			},
			DefenseSteps: []string{},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPurpleClient(server.URL)
	result, err := client.RunExercise(&ExerciseRequest{Scenario: "apt-intrusion"})

	require.NoError(t, err)
	assert.Equal(t, "in_progress", result.Status)
	assert.NotEmpty(t, result.AttackSteps)
}

// ============================================================================
// GetReport Tests
// ============================================================================

func TestGetReport_HighCoverage(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/exercise/report", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		response := ReportResult{
			ExerciseID: "exercise-123",
			Detected:   18,
			Total:      20,
			Coverage:   0.90,
			Gaps: []string{
				"PowerShell execution not logged",
				"USB device insertion not monitored",
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPurpleClient(server.URL)
	result, err := client.GetReport(&ReportRequest{ExerciseID: "exercise-123"})

	require.NoError(t, err)
	assert.Equal(t, "exercise-123", result.ExerciseID)
	assert.Equal(t, 18, result.Detected)
	assert.Equal(t, 20, result.Total)
	assert.Equal(t, 0.90, result.Coverage)
	assert.Len(t, result.Gaps, 2)
	assert.Contains(t, result.Gaps[0], "PowerShell")
}

func TestGetReport_LowCoverage(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ReportResult{
			ExerciseID: "exercise-789",
			Detected:   5,
			Total:      15,
			Coverage:   0.33,
			Gaps: []string{
				"No detection on file exfiltration",
				"Credential dumping not detected",
				"Registry persistence not monitored",
				"No alerts on privilege escalation",
			},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPurpleClient(server.URL)
	result, err := client.GetReport(&ReportRequest{ExerciseID: "exercise-789"})

	require.NoError(t, err)
	assert.Less(t, result.Coverage, 0.5)
	assert.Greater(t, len(result.Gaps), 3)
}

// ============================================================================
// GetStatus Tests
// ============================================================================

func TestGetStatus_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/status", r.URL.Path)
		assert.Equal(t, "GET", r.Method)

		response := StatusResult{
			Status:             "operational",
			ExercisesCompleted: 42,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPurpleClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "operational", result.Status)
	assert.Equal(t, 42, result.ExercisesCompleted)
}

func TestGetStatus_NoExercises(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := StatusResult{
			Status:             "idle",
			ExercisesCompleted: 0,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewPurpleClient(server.URL)
	result, err := client.GetStatus()

	require.NoError(t, err)
	assert.Equal(t, "idle", result.Status)
	assert.Equal(t, 0, result.ExercisesCompleted)
}

// ============================================================================
// Error Handling Tests
// ============================================================================

func TestServerErrors(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	client := NewPurpleClient(server.URL)

	t.Run("RunExercise", func(t *testing.T) {
		_, err := client.RunExercise(&ExerciseRequest{})
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

func BenchmarkRunExercise(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ExerciseResult{Status: "completed"})
	}))
	defer server.Close()

	client := NewPurpleClient(server.URL)
	req := &ExerciseRequest{Scenario: "test"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.RunExercise(req)
	}
}

func BenchmarkGetReport(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(ReportResult{Coverage: 0.9})
	}))
	defer server.Close()

	client := NewPurpleClient(server.URL)
	req := &ReportRequest{ExerciseID: "test"}

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

	client := NewPurpleClient(server.URL)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.GetStatus()
	}
}
