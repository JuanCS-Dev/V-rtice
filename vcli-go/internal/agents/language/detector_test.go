package language

import (
	"testing"
)

func TestDetector(t *testing.T) {
	detector := NewDetector()

	// Test Python detection
	result, err := detector.Detect([]string{"/home/juan/vertice-dev/backend/services/immunis_api_service"})
	if err != nil {
		t.Fatalf("Detect failed: %v", err)
	}

	t.Logf("Primary: %s", result.Primary)
	t.Logf("All: %v", result.All)
	t.Logf("Confidence: %.2f", result.Confidence)

	if result.Primary != LanguagePython {
		t.Errorf("Expected primary language to be Python, got %s", result.Primary)
	}

	if !result.HasLanguage(LanguagePython) {
		t.Error("Expected Python to be detected")
	}
}

func TestDetectorGo(t *testing.T) {
	detector := NewDetector()

	// Test Go detection
	result, err := detector.Detect([]string{"/home/juan/vertice-dev/vcli-go/internal/agents"})
	if err != nil {
		t.Fatalf("Detect failed: %v", err)
	}

	t.Logf("Primary: %s", result.Primary)
	t.Logf("All: %v", result.All)
	t.Logf("Confidence: %.2f", result.Confidence)

	if result.Primary != LanguageGo {
		t.Errorf("Expected primary language to be Go, got %s", result.Primary)
	}
}
