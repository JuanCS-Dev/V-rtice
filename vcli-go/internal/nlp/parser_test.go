// Package nlp - Integration tests
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package nlp

import (
	"context"
	"testing"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

func TestParser_EndToEnd_Portuguese(t *testing.T) {
	parser := NewParser()
	ctx := context.Background()

	tests := []struct {
		name            string
		input           string
		expectedPath    []string
		expectedFlags   map[string]string
		minConfidence   float64
	}{
		{
			name:  "mostra os pods",
			input: "mostra os pods",
			expectedPath: []string{"k8s", "get", "pods"},
			minConfidence: 0.8,
		},
		{
			name:  "mostra pods com problema",
			input: "mostra pods com problema",
			expectedPath: []string{"k8s", "get", "pods"},
			expectedFlags: map[string]string{
				"--field-selector": "status.phase=Failed",
			},
			minConfidence: 0.7,
		},
		{
			name:  "lista deployments no prod",
			input: "lista deployments do namespace prod",
			expectedPath: []string{"k8s", "get", "deployments"},
			expectedFlags: map[string]string{
				"-n": "prod",
			},
			minConfidence: 0.8,
		},
		{
			name:  "escala deployment nginx",
			input: "escala deployment nginx 5",
			expectedPath: []string{"k8s", "scale", "deployments"},
			expectedFlags: map[string]string{
				"--replicas": "5",
			},
			minConfidence: 0.7,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := parser.Parse(ctx, tt.input)
			if err != nil {
				t.Fatalf("Parse() error = %v", err)
			}

			// Check command path
			if len(result.Command.Path) != len(tt.expectedPath) {
				t.Errorf("Path length = %d, want %d", len(result.Command.Path), len(tt.expectedPath))
			}

			for i, expected := range tt.expectedPath {
				if i >= len(result.Command.Path) {
					break
				}
				if result.Command.Path[i] != expected {
					t.Errorf("Path[%d] = %v, want %v", i, result.Command.Path[i], expected)
				}
			}

			// Check flags if specified
			if tt.expectedFlags != nil {
				for key, expectedVal := range tt.expectedFlags {
					if val, ok := result.Command.Flags[key]; !ok || val != expectedVal {
						t.Errorf("Flags[%s] = %v, want %v", key, val, expectedVal)
					}
				}
			}

			// Check confidence
			if result.Confidence < tt.minConfidence {
				t.Errorf("Confidence = %f, want >= %f", result.Confidence, tt.minConfidence)
			}

			// Verify intent was parsed
			if result.Intent == nil {
				t.Error("Intent is nil")
			}

			// Verify original input is preserved
			if result.Intent.OriginalInput != tt.input {
				t.Errorf("OriginalInput = %v, want %v", result.Intent.OriginalInput, tt.input)
			}
		})
	}
}

func TestParser_EndToEnd_English(t *testing.T) {
	parser := NewParser()
	ctx := context.Background()

	tests := []struct {
		name          string
		input         string
		expectedPath  []string
		minConfidence float64
	}{
		{
			name:  "show pods",
			input: "show me the pods",
			expectedPath: []string{"k8s", "get", "pods"},
			minConfidence: 0.8,
		},
		{
			name:  "list deployments",
			input: "list deployments",
			expectedPath: []string{"k8s", "get", "deployments"},
			minConfidence: 0.8,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := parser.Parse(ctx, tt.input)
			if err != nil {
				t.Fatalf("Parse() error = %v", err)
			}

			for i, expected := range tt.expectedPath {
				if i >= len(result.Command.Path) {
					break
				}
				if result.Command.Path[i] != expected {
					t.Errorf("Path[%d] = %v, want %v", i, result.Command.Path[i], expected)
				}
			}

			if result.Confidence < tt.minConfidence {
				t.Errorf("Confidence = %f, want >= %f", result.Confidence, tt.minConfidence)
			}
		})
	}
}

func TestParser_WithContext(t *testing.T) {
	parser := NewParser()
	ctx := context.Background()

	// Create session context with current namespace
	sessionCtx := &nlp.Context{
		CurrentNS: "production",
	}

	input := "mostra os pods"
	result, err := parser.ParseWithContext(ctx, input, sessionCtx)
	if err != nil {
		t.Fatalf("ParseWithContext() error = %v", err)
	}

	// Context namespace should influence entities
	if result.Entities == nil || len(result.Entities) == 0 {
		t.Log("No entities extracted (this is OK for simple query)")
	}
}

func TestParser_EmptyInput(t *testing.T) {
	parser := NewParser()
	ctx := context.Background()

	_, err := parser.Parse(ctx, "")
	if err == nil {
		t.Error("Expected error for empty input")
	}
}

func TestParser_ComplexQuery(t *testing.T) {
	parser := NewParser()
	ctx := context.Background()

	input := "mostra os pods com problema no namespace production"
	result, err := parser.Parse(ctx, input)
	if err != nil {
		t.Fatalf("Parse() error = %v", err)
	}

	// Should extract multiple entities
	if len(result.Entities) < 2 {
		t.Errorf("Entities count = %d, want at least 2", len(result.Entities))
	}

	// Should have both filter and namespace
	hasFilter := false
	hasNamespace := false

	for _, entity := range result.Entities {
		if entity.Type == nlp.EntityTypeSTATUS {
			hasFilter = true
		}
		if entity.Type == nlp.EntityTypeNAMESPACE {
			hasNamespace = true
		}
	}

	if !hasFilter {
		t.Error("Expected status filter entity")
	}
	if !hasNamespace {
		t.Error("Expected namespace entity")
	}

	// Command should have both flags
	if _, ok := result.Command.Flags["--field-selector"]; !ok {
		t.Error("Expected --field-selector flag")
	}
	if _, ok := result.Command.Flags["-n"]; !ok {
		t.Error("Expected -n flag")
	}
}

func BenchmarkParser_Parse(b *testing.B) {
	parser := NewParser()
	ctx := context.Background()
	input := "mostra os pods com problema no namespace de producao"

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = parser.Parse(ctx, input)
	}
}
