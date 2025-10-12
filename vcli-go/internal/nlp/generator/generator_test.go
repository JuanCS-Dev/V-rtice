// Package generator - Unit tests
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package generator

import (
	"testing"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

func TestGenerator_BasicQuery(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:       "show",
		Target:     "pods",
		Category:   nlp.IntentCategoryQUERY,
		Confidence: 0.95,
	}

	entities := []nlp.Entity{}

	cmd, err := gen.Generate(intent, entities)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Should generate: k8s get pods
	if len(cmd.Path) != 3 {
		t.Errorf("Path length = %d, want 3", len(cmd.Path))
	}

	if cmd.Path[0] != "k8s" {
		t.Errorf("Path[0] = %v, want k8s", cmd.Path[0])
	}

	if cmd.Path[1] != "get" {
		t.Errorf("Path[1] = %v, want get", cmd.Path[1])
	}

	if cmd.Path[2] != "pods" {
		t.Errorf("Path[2] = %v, want pods", cmd.Path[2])
	}
}

func TestGenerator_WithNamespace(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "show",
		Target: "pods",
	}

	entities := []nlp.Entity{
		{
			Type:       nlp.EntityTypeNAMESPACE,
			Normalized: "production",
		},
	}

	cmd, err := gen.Generate(intent, entities)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Should have -n flag
	if cmd.Flags["-n"] != "production" {
		t.Errorf("Flags[-n] = %v, want production", cmd.Flags["-n"])
	}
}

func TestGenerator_WithFilter(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "show",
		Target: "pods",
	}

	entities := []nlp.Entity{
		{
			Type:       nlp.EntityTypeSTATUS,
			Normalized: "error",
			Metadata: map[string]interface{}{
				"field_selector": "status.phase=Failed",
			},
		},
	}

	cmd, err := gen.Generate(intent, entities)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Should have field-selector flag
	if cmd.Flags["--field-selector"] != "status.phase=Failed" {
		t.Errorf("Flags[--field-selector] = %v, want status.phase=Failed", cmd.Flags["--field-selector"])
	}
}

func TestGenerator_ScaleCommand(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "scale",
		Target: "deployments",
	}

	entities := []nlp.Entity{
		{
			Type:       nlp.EntityTypeNAME,
			Normalized: "nginx",
		},
		{
			Type:       nlp.EntityTypeNUMBER,
			Normalized: "5",
			Metadata: map[string]interface{}{
				"numeric_value": 5,
			},
		},
	}

	cmd, err := gen.Generate(intent, entities)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Should generate: k8s scale deployment/nginx --replicas=5
	if cmd.Path[1] != "scale" {
		t.Errorf("Path[1] = %v, want scale", cmd.Path[1])
	}

	if cmd.Flags["--replicas"] != "5" {
		t.Errorf("Flags[--replicas] = %v, want 5", cmd.Flags["--replicas"])
	}

	// Should have deployment/nginx in args
	if len(cmd.Args) == 0 || cmd.Args[0] != "deployment/nginx" {
		t.Errorf("Args = %v, want [deployment/nginx]", cmd.Args)
	}
}

func TestGenerator_DeleteCommand(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "delete",
		Target: "pods",
	}

	entities := []nlp.Entity{
		{
			Type:       nlp.EntityTypeNAME,
			Normalized: "nginx-abc123",
		},
	}

	cmd, err := gen.Generate(intent, entities)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Should generate: k8s delete pods nginx-abc123
	if cmd.Path[1] != "delete" {
		t.Errorf("Path[1] = %v, want delete", cmd.Path[1])
	}

	if len(cmd.Args) == 0 || cmd.Args[0] != "nginx-abc123" {
		t.Errorf("Args = %v, want [nginx-abc123]", cmd.Args)
	}
}

func TestGenerator_ValidateCommand(t *testing.T) {
	gen := NewGenerator()

	tests := []struct {
		name      string
		cmd       *nlp.Command
		expectErr bool
	}{
		{
			name: "valid k8s command",
			cmd: &nlp.Command{
				Path: []string{"k8s", "get", "pods"},
			},
			expectErr: false,
		},
		{
			name: "empty path",
			cmd: &nlp.Command{
				Path: []string{},
			},
			expectErr: true,
		},
		{
			name: "unknown subsystem",
			cmd: &nlp.Command{
				Path: []string{"unknown", "get"},
			},
			expectErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := gen.ValidateCommand(tt.cmd)
			if (err != nil) != tt.expectErr {
				t.Errorf("ValidateCommand() error = %v, expectErr %v", err, tt.expectErr)
			}
		})
	}
}

func TestGenerator_ExplainCommand(t *testing.T) {
	gen := NewGenerator()

	tests := []struct {
		name     string
		cmd      *nlp.Command
		contains string
	}{
		{
			name: "simple get",
			cmd: &nlp.Command{
				Path: []string{"k8s", "get", "pods"},
			},
			contains: "Show pods",
		},
		{
			name: "with namespace",
			cmd: &nlp.Command{
				Path: []string{"k8s", "get", "pods"},
				Flags: map[string]string{
					"-n": "production",
				},
			},
			contains: "namespace production",
		},
		{
			name: "scale",
			cmd: &nlp.Command{
				Path: []string{"k8s", "scale", "deployments"},
				Flags: map[string]string{
					"--replicas": "5",
				},
			},
			contains: "5 replicas",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			explanation := gen.ExplainCommand(tt.cmd)
			if explanation == "" {
				t.Error("ExplainCommand() returned empty string")
			}
			if len(tt.contains) > 0 && !containsIgnoreCase(explanation, tt.contains) {
				t.Errorf("ExplainCommand() = %q, should contain %q", explanation, tt.contains)
			}
		})
	}
}

func containsIgnoreCase(s, substr string) bool {
	s = toLower(s)
	substr = toLower(substr)
	return contains(s, substr)
}

func toLower(s string) string {
	result := make([]rune, len(s))
	for i, r := range s {
		if r >= 'A' && r <= 'Z' {
			result[i] = r + 32
		} else {
			result[i] = r
		}
	}
	return string(result)
}

func contains(s, substr string) bool {
	if len(substr) > len(s) {
		return false
	}
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

func BenchmarkGenerator_Generate(b *testing.B) {
	gen := NewGenerator()
	intent := &nlp.Intent{
		Verb:   "show",
		Target: "pods",
	}
	entities := []nlp.Entity{
		{Type: nlp.EntityTypeNAMESPACE, Normalized: "prod"},
		{Type: nlp.EntityTypeSTATUS, Normalized: "error"},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = gen.Generate(intent, entities)
	}
}
