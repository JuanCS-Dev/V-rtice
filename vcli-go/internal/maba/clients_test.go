package maba

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// ============================================================================
// TEST HELPERS
// ============================================================================

// mockMABAServer creates a test HTTP server that mimics MABA backend behavior
func mockMABAServer(t *testing.T, handler http.HandlerFunc) *httptest.Server {
	server := httptest.NewServer(handler)
	t.Cleanup(server.Close)
	return server
}

// assertError checks that an error occurred with expected message substring
func assertError(t *testing.T, err error, wantSubstring string) {
	t.Helper()
	if err == nil {
		t.Fatalf("expected error containing %q, got nil", wantSubstring)
	}
	if wantSubstring != "" && !contains(err.Error(), wantSubstring) {
		t.Errorf("expected error to contain %q, got %q", wantSubstring, err.Error())
	}
}

// assertNoError checks that no error occurred
func assertNoError(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
}

func contains(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// ============================================================================
// SESSION MANAGEMENT TESTS
// ============================================================================

func TestCreateSession_Success(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/sessions" {
			t.Errorf("unexpected request: %s %s", r.Method, r.URL.Path)
			w.WriteHeader(http.StatusNotFound)
			return
		}

		var req SessionRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			t.Errorf("failed to decode request: %v", err)
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		// Verify conservative defaults were applied
		if req.ViewportWidth != 1920 && req.ViewportWidth != 0 {
			t.Errorf("unexpected viewport width: %d", req.ViewportWidth)
		}

		resp := SessionResponse{
			SessionID: "test-session-123",
			Status:    "active",
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &SessionRequest{
		Headless:       true,
		ViewportWidth:  1920,
		ViewportHeight: 1080,
	}

	result, err := client.CreateSession(ctx, req)
	assertNoError(t, err)

	if result.SessionID != "test-session-123" {
		t.Errorf("expected session_id 'test-session-123', got %q", result.SessionID)
	}
	if result.Status != "active" {
		t.Errorf("expected status 'active', got %q", result.Status)
	}
}

func TestCreateSession_NilRequest(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server with nil request")
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	_, err := client.CreateSession(ctx, nil)
	assertError(t, err, "cannot be nil")
}

func TestCreateSession_AppliesDefaults(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		var req SessionRequest
		json.NewDecoder(r.Body).Decode(&req)

		// Verify defaults were applied
		if req.ViewportWidth != 1920 {
			t.Errorf("expected default width 1920, got %d", req.ViewportWidth)
		}
		if req.ViewportHeight != 1080 {
			t.Errorf("expected default height 1080, got %d", req.ViewportHeight)
		}

		resp := SessionResponse{SessionID: "session-456", Status: "active"}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &SessionRequest{Headless: true} // No viewport dimensions
	result, err := client.CreateSession(ctx, req)

	assertNoError(t, err)
	if result.SessionID != "session-456" {
		t.Errorf("expected session_id 'session-456', got %q", result.SessionID)
	}
}

func TestCloseSession_Success(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodDelete {
			t.Errorf("expected DELETE, got %s", r.Method)
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if r.URL.Path != "/sessions/test-session-789" {
			t.Errorf("unexpected path: %s", r.URL.Path)
			w.WriteHeader(http.StatusNotFound)
			return
		}
		w.WriteHeader(http.StatusOK)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	err := client.CloseSession(ctx, "test-session-789")
	assertNoError(t, err)
}

func TestCloseSession_EmptySessionID(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server with empty session_id")
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	err := client.CloseSession(ctx, "")
	assertError(t, err, "cannot be empty")
}

// ============================================================================
// NAVIGATION TESTS
// ============================================================================

func TestNavigate_Success(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}

		sessionID := r.URL.Query().Get("session_id")
		if sessionID != "nav-session-001" {
			t.Errorf("expected session_id 'nav-session-001', got %q", sessionID)
		}

		var req NavigateRequest
		json.NewDecoder(r.Body).Decode(&req)

		if req.URL != "https://example.com" {
			t.Errorf("unexpected URL: %s", req.URL)
		}

		resp := NavigateResult{
			Status:          "success",
			ExecutionTimeMs: 123.45,
			Result:          map[string]interface{}{"title": "Example Domain"},
		}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &NavigateRequest{
		URL:       "https://example.com",
		WaitUntil: "networkidle",
		TimeoutMs: 30000,
	}

	result, err := client.Navigate(ctx, "nav-session-001", req)
	assertNoError(t, err)

	if result.Status != "success" {
		t.Errorf("expected status 'success', got %q", result.Status)
	}
	if result.ExecutionTimeMs != 123.45 {
		t.Errorf("expected execution time 123.45ms, got %.2f", result.ExecutionTimeMs)
	}
}

func TestNavigate_EmptySessionID(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server with empty session_id")
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &NavigateRequest{URL: "https://example.com"}
	_, err := client.Navigate(ctx, "", req)
	assertError(t, err, "cannot be empty")
}

func TestNavigate_NilRequest(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server with nil request")
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	_, err := client.Navigate(ctx, "session-123", nil)
	assertError(t, err, "cannot be nil")
}

func TestNavigate_EmptyURL(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server with empty URL")
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &NavigateRequest{URL: ""}
	_, err := client.Navigate(ctx, "session-123", req)
	assertError(t, err, "cannot be empty")
}

func TestNavigate_AppliesDefaults(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		var req NavigateRequest
		json.NewDecoder(r.Body).Decode(&req)

		if req.WaitUntil != "networkidle" {
			t.Errorf("expected default WaitUntil 'networkidle', got %q", req.WaitUntil)
		}
		if req.TimeoutMs != 30000 {
			t.Errorf("expected default TimeoutMs 30000, got %d", req.TimeoutMs)
		}

		resp := NavigateResult{Status: "success", ExecutionTimeMs: 100.0}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &NavigateRequest{URL: "https://example.com"} // No WaitUntil or TimeoutMs
	_, err := client.Navigate(ctx, "session-xyz", req)
	assertNoError(t, err)
}

func TestNavigate_ApplicationError(t *testing.T) {
	errorMsg := "navigation timeout"
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		resp := NavigateResult{
			Status: "error",
			Error:  &errorMsg,
		}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &NavigateRequest{URL: "https://example.com"}
	_, err := client.Navigate(ctx, "session-123", req)
	assertError(t, err, "navigation timeout")
}

// ============================================================================
// BROWSER ACTIONS TESTS
// ============================================================================

func TestClick_Success(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		sessionID := r.URL.Query().Get("session_id")
		if sessionID != "click-session-001" {
			t.Errorf("expected session_id 'click-session-001', got %q", sessionID)
		}

		var req ClickRequest
		json.NewDecoder(r.Body).Decode(&req)

		if req.Selector != "button#submit" {
			t.Errorf("unexpected selector: %s", req.Selector)
		}

		resp := ActionResponse{
			Status:          "success",
			ExecutionTimeMs: 50.0,
		}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &ClickRequest{
		Selector:   "button#submit",
		Button:     "left",
		ClickCount: 1,
		TimeoutMs:  30000,
	}

	result, err := client.Click(ctx, "click-session-001", req)
	assertNoError(t, err)

	if result.Status != "success" {
		t.Errorf("expected status 'success', got %q", result.Status)
	}
}

func TestClick_EmptySelector(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server with empty selector")
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &ClickRequest{Selector: ""}
	_, err := client.Click(ctx, "session-123", req)
	assertError(t, err, "cannot be empty")
}

func TestClick_AppliesDefaults(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		var req ClickRequest
		json.NewDecoder(r.Body).Decode(&req)

		if req.Button != "left" {
			t.Errorf("expected default button 'left', got %q", req.Button)
		}
		if req.ClickCount != 1 {
			t.Errorf("expected default click_count 1, got %d", req.ClickCount)
		}
		if req.TimeoutMs != 30000 {
			t.Errorf("expected default timeout_ms 30000, got %d", req.TimeoutMs)
		}

		resp := ActionResponse{Status: "success", ExecutionTimeMs: 25.0}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &ClickRequest{Selector: "a.link"} // No button, click_count, or timeout
	_, err := client.Click(ctx, "session-abc", req)
	assertNoError(t, err)
}

func TestType_Success(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		var req TypeRequest
		json.NewDecoder(r.Body).Decode(&req)

		if req.Selector != "input#username" {
			t.Errorf("unexpected selector: %s", req.Selector)
		}
		if req.Text != "testuser" {
			t.Errorf("unexpected text: %s", req.Text)
		}

		resp := ActionResponse{Status: "success", ExecutionTimeMs: 75.0}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &TypeRequest{
		Selector: "input#username",
		Text:     "testuser",
		DelayMs:  0,
	}

	result, err := client.Type(ctx, "type-session-001", req)
	assertNoError(t, err)

	if result.Status != "success" {
		t.Errorf("expected status 'success', got %q", result.Status)
	}
}

func TestScreenshot_Success(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		var req ScreenshotRequest
		json.NewDecoder(r.Body).Decode(&req)

		if req.Format != "png" {
			t.Errorf("expected format 'png', got %q", req.Format)
		}

		resp := ActionResponse{
			Status:          "success",
			ExecutionTimeMs: 200.0,
			Result:          map[string]interface{}{"base64": "iVBORw0KGgo="},
		}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &ScreenshotRequest{
		FullPage: true,
		Format:   "png",
	}

	result, err := client.Screenshot(ctx, "screenshot-session-001", req)
	assertNoError(t, err)

	if result.Status != "success" {
		t.Errorf("expected status 'success', got %q", result.Status)
	}
}

// ============================================================================
// DATA EXTRACTION TESTS
// ============================================================================

func TestExtract_Success(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		sessionID := r.URL.Query().Get("session_id")
		if sessionID != "extract-session-001" {
			t.Errorf("expected session_id 'extract-session-001', got %q", sessionID)
		}

		var req ExtractRequest
		json.NewDecoder(r.Body).Decode(&req)

		if len(req.Selectors) != 2 {
			t.Errorf("expected 2 selectors, got %d", len(req.Selectors))
		}

		resp := ExtractResult{
			Status:          "success",
			ExecutionTimeMs: 150.0,
			Result: map[string]interface{}{
				"title": "Example Domain",
				"price": "$99.99",
			},
		}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &ExtractRequest{
		Selectors: map[string]string{
			"title": "h1",
			"price": ".price",
		},
		ExtractAll: false,
	}

	result, err := client.Extract(ctx, "extract-session-001", req)
	assertNoError(t, err)

	if result.Status != "success" {
		t.Errorf("expected status 'success', got %q", result.Status)
	}
	if len(result.Result) != 2 {
		t.Errorf("expected 2 results, got %d", len(result.Result))
	}
}

func TestExtract_EmptySelectors(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server with empty selectors")
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &ExtractRequest{Selectors: map[string]string{}}
	_, err := client.Extract(ctx, "session-123", req)
	assertError(t, err, "cannot be empty")
}

// ============================================================================
// COGNITIVE MAP TESTS
// ============================================================================

func TestQueryCognitiveMap_Success(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/cognitive-map/query" {
			t.Errorf("unexpected path: %s", r.URL.Path)
		}

		var req CognitiveMapQueryRequest
		json.NewDecoder(r.Body).Decode(&req)

		if req.QueryType != "get_path" {
			t.Errorf("unexpected query_type: %s", req.QueryType)
		}

		resp := CognitiveMapQueryResponse{
			Found:      true,
			Confidence: 0.95,
			Result: map[string]interface{}{
				"path": []string{"/home", "/products", "/checkout"},
			},
		}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &CognitiveMapQueryRequest{
		QueryType: "get_path",
		Parameters: map[string]interface{}{
			"from_url": "https://example.com",
			"to_url":   "https://example.com/checkout",
		},
	}

	result, err := client.QueryCognitiveMap(ctx, req)
	assertNoError(t, err)

	if !result.Found {
		t.Error("expected found=true")
	}
	if result.Confidence != 0.95 {
		t.Errorf("expected confidence 0.95, got %.2f", result.Confidence)
	}
}

func TestQueryCognitiveMap_InvalidQueryType(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server with invalid query_type")
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &CognitiveMapQueryRequest{
		QueryType:  "invalid_type",
		Parameters: map[string]interface{}{},
	}

	_, err := client.QueryCognitiveMap(ctx, req)
	assertError(t, err, "invalid query_type")
}

func TestQueryCognitiveMap_EmptyQueryType(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server with empty query_type")
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	req := &CognitiveMapQueryRequest{
		QueryType:  "",
		Parameters: map[string]interface{}{},
	}

	_, err := client.QueryCognitiveMap(ctx, req)
	assertError(t, err, "cannot be empty")
}

// ============================================================================
// STATS & HEALTH TESTS
// ============================================================================

func TestGetStats_Success(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if r.URL.Path != "/stats" {
			t.Errorf("unexpected path: %s", r.URL.Path)
		}

		resp := StatsResult{
			UptimeSeconds: 3600.0,
			CognitiveMap: map[string]interface{}{
				"total_nodes": float64(150),
				"total_edges": float64(320),
			},
			Browser: map[string]interface{}{
				"active_sessions": float64(3),
				"total_sessions":  float64(47),
			},
		}
		json.NewEncoder(w).Encode(resp)
	})

	client := NewMABAClient(server.URL)
	ctx := context.Background()

	result, err := client.GetStats(ctx)
	assertNoError(t, err)

	if result.UptimeSeconds != 3600.0 {
		t.Errorf("expected uptime 3600.0, got %.1f", result.UptimeSeconds)
	}
	if result.CognitiveMap["total_nodes"] != float64(150) {
		t.Errorf("unexpected cognitive_map data")
	}
}

// ============================================================================
// CONTEXT & TIMEOUT TESTS
// ============================================================================

func TestCreateSession_ContextCanceled(t *testing.T) {
	server := mockMABAServer(t, func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(100 * time.Millisecond)
		json.NewEncoder(w).Encode(SessionResponse{SessionID: "test", Status: "active"})
	})

	client := NewMABAClient(server.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel()

	req := &SessionRequest{Headless: true}
	_, err := client.CreateSession(ctx, req)

	if err == nil {
		t.Error("expected context deadline exceeded error")
	}
}

// ============================================================================
// CONSTRUCTOR TESTS
// ============================================================================

func TestNewMABAClient_WithEndpoint(t *testing.T) {
	client := NewMABAClient("http://localhost:8152")
	if client == nil {
		t.Fatal("expected non-nil client")
	}
	if client.endpoint != "http://localhost:8152" {
		t.Errorf("expected endpoint 'http://localhost:8152', got %q", client.endpoint)
	}
}

func TestNewMABAClient_EmptyEndpoint(t *testing.T) {
	// Should use config default
	client := NewMABAClient("")
	if client == nil {
		t.Fatal("expected non-nil client")
	}
	// Endpoint should be set from config (not empty)
	if client.endpoint == "" {
		t.Error("expected endpoint from config, got empty string")
	}
}

// ============================================================================
// BENCHMARKS
// ============================================================================

func BenchmarkNavigate(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := NavigateResult{
			Status:          "success",
			ExecutionTimeMs: 100.0,
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	ctx := context.Background()
	req := &NavigateRequest{URL: "https://example.com"}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Navigate(ctx, "bench-session", req)
	}
}

func BenchmarkExtract(b *testing.B) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		response := ExtractResult{
			Status:          "success",
			ExecutionTimeMs: 50.0,
			Result:          map[string]interface{}{"item": "1"},
		}
		json.NewEncoder(w).Encode(response)
	}))
	defer server.Close()

	client := NewMABAClient(server.URL)
	ctx := context.Background()
	req := &ExtractRequest{Selectors: map[string]string{"item": "div"}}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		client.Extract(ctx, "bench-session", req)
	}
}
