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

// ADDITIONAL TESTS FOR 90%+ COVERAGE

func TestGenerator_GenerateNilIntent(t *testing.T) {
	gen := NewGenerator()

	_, err := gen.Generate(nil, []nlp.Entity{})
	if err == nil {
		t.Error("Expected error when intent is nil")
	}
}

func TestGenerator_GenerateAlternatives(t *testing.T) {
	gen := NewGenerator()

	entities := []nlp.Entity{
		{Type: nlp.EntityTypeNAMESPACE, Normalized: "prod"},
	}

	alternatives := []*nlp.Intent{
		{Verb: "show", Target: "pods", Confidence: 0.9},
		{Verb: "list", Target: "deployments", Confidence: 0.8},
		{Verb: "describe", Target: "services", Confidence: 0.7},
	}

	commands, err := gen.GenerateAlternatives(&nlp.Intent{Verb: "show", Target: "pods"}, entities, alternatives)
	if err != nil {
		t.Fatalf("GenerateAlternatives() error = %v", err)
	}

	if len(commands) != 3 {
		t.Errorf("GenerateAlternatives() returned %d commands, want 3", len(commands))
	}

	// Verify first alternative
	if commands[0].Path[1] != "get" {
		t.Errorf("First alternative verb = %v, want get", commands[0].Path[1])
	}
}

func TestGenerator_GenerateAlternatives_WithInvalidIntents(t *testing.T) {
	gen := NewGenerator()

	// Include nil intent to test error handling
	alternatives := []*nlp.Intent{
		{Verb: "show", Target: "pods", Confidence: 0.9},
		nil, // This should be skipped
		{Verb: "list", Target: "deployments", Confidence: 0.8},
	}

	commands, err := gen.GenerateAlternatives(&nlp.Intent{Verb: "show", Target: "pods"}, []nlp.Entity{}, alternatives)
	if err != nil {
		t.Fatalf("GenerateAlternatives() error = %v", err)
	}

	// Should only have 2 valid commands (nil skipped)
	if len(commands) != 2 {
		t.Errorf("GenerateAlternatives() returned %d commands, want 2", len(commands))
	}
}

func TestGenerator_MapVerbToKubectl_UnknownVerb(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "unknown_verb",
		Target: "pods",
	}

	cmd, err := gen.Generate(intent, []nlp.Entity{})
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Should pass through unknown verb
	if cmd.Path[1] != "unknown_verb" {
		t.Errorf("Unknown verb should be passed through, got %v", cmd.Path[1])
	}
}

func TestGenerator_BuildFlags_WithModifiers(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "show",
		Target: "pods",
		Modifiers: []nlp.Modifier{
			{Type: "namespace", Key: "-n", Value: "staging"},
			{Type: "filter", Key: "--field-selector", Value: "pending"},
		},
	}

	cmd, err := gen.Generate(intent, []nlp.Entity{})
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Should have namespace from modifier
	if cmd.Flags["-n"] != "staging" {
		t.Errorf("Namespace flag = %v, want staging", cmd.Flags["-n"])
	}
}

func TestGenerator_BuildFlags_EntityOverridesModifier(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "show",
		Target: "pods",
		Modifiers: []nlp.Modifier{
			{Type: "namespace", Key: "-n", Value: "modifier-ns"},
		},
	}

	entities := []nlp.Entity{
		{Type: nlp.EntityTypeNAMESPACE, Normalized: "entity-ns"},
	}

	cmd, err := gen.Generate(intent, entities)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Entity should override modifier
	if cmd.Flags["-n"] != "entity-ns" {
		t.Errorf("Namespace = %v, want entity-ns (entity should override modifier)", cmd.Flags["-n"])
	}
}

func TestGenerator_BuildFlags_CountModifier(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "scale",
		Target: "deployments",
		Modifiers: []nlp.Modifier{
			{Type: "count", Key: "--replicas", Value: "10"},
		},
	}

	cmd, err := gen.Generate(intent, []nlp.Entity{})
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Should have replicas from modifier
	if cmd.Flags["--replicas"] != "10" {
		t.Errorf("Replicas flag = %v, want 10", cmd.Flags["--replicas"])
	}
}

func TestGenerator_BuildArgs_NonScaleResource(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "describe",
		Target: "pods",
	}

	entities := []nlp.Entity{
		{Type: nlp.EntityTypeNAME, Normalized: "nginx-pod"},
	}

	cmd, err := gen.Generate(intent, entities)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// For non-scale commands, should just be the name
	if len(cmd.Args) != 1 || cmd.Args[0] != "nginx-pod" {
		t.Errorf("Args = %v, want [nginx-pod]", cmd.Args)
	}
}

func TestGenerator_BuildPath_EmptyTarget(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "show",
		Target: "", // Empty target
	}

	cmd, err := gen.Generate(intent, []nlp.Entity{})
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Should have only k8s and verb
	if len(cmd.Path) != 2 {
		t.Errorf("Path length = %d, want 2 (k8s + verb only)", len(cmd.Path))
	}
}

func TestGenerator_ExplainCommand_AllVerbTypes(t *testing.T) {
	gen := NewGenerator()

	tests := []struct {
		name     string
		verb     string
		expected string
	}{
		{"get", "get", "Show"},
		{"delete", "delete", "Delete"},
		{"scale", "scale", "Scale"},
		{"describe", "describe", "Describe"},
		{"unknown", "custom", "Custom"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cmd := &nlp.Command{
				Path: []string{"k8s", tt.verb, "pods"},
			}

			explanation := gen.ExplainCommand(cmd)
			if !containsIgnoreCase(explanation, tt.expected) {
				t.Errorf("ExplainCommand() = %q, should contain %q", explanation, tt.expected)
			}
		})
	}
}

func TestGenerator_ExplainCommand_ShortPath(t *testing.T) {
	gen := NewGenerator()

	cmd := &nlp.Command{
		Path: []string{"k8s"}, // Only subsystem, no verb or resource
	}

	explanation := gen.ExplainCommand(cmd)
	// Should not panic, should return empty or minimal string
	if explanation != "" {
		// Verify it doesn't crash with short path
		t.Logf("Explanation for short path: %q", explanation)
	}
}

func TestGenerator_ValidateCommand_ValidSubsystems(t *testing.T) {
	gen := NewGenerator()

	validSubsystems := []string{"k8s", "security", "workflow"}

	for _, subsystem := range validSubsystems {
		t.Run(subsystem, func(t *testing.T) {
			cmd := &nlp.Command{
				Path: []string{subsystem, "get", "resource"},
			}

			err := gen.ValidateCommand(cmd)
			if err != nil {
				t.Errorf("ValidateCommand() error = %v for valid subsystem %s", err, subsystem)
			}
		})
	}
}

func TestGenerator_ComplexCommand(t *testing.T) {
	gen := NewGenerator()

	intent := &nlp.Intent{
		Verb:   "show",
		Target: "pods",
		Modifiers: []nlp.Modifier{
			{Type: "filter", Key: "--field-selector", Value: "running"},
		},
	}

	entities := []nlp.Entity{
		{Type: nlp.EntityTypeNAMESPACE, Normalized: "prod"},
		{
			Type:       nlp.EntityTypeSTATUS,
			Normalized: "failed",
			Metadata: map[string]interface{}{
				"field_selector": "status.phase=Failed",
			},
		},
		{Type: nlp.EntityTypeNAME, Normalized: "nginx"},
	}

	cmd, err := gen.Generate(intent, entities)
	if err != nil {
		t.Fatalf("Generate() error = %v", err)
	}

	// Verify all components
	if len(cmd.Path) != 3 {
		t.Errorf("Path length = %d, want 3", len(cmd.Path))
	}

	if cmd.Flags["-n"] != "prod" {
		t.Error("Should have namespace flag")
	}

	if cmd.Flags["--field-selector"] != "status.phase=Failed" {
		t.Error("Should have field-selector from entity (not modifier)")
	}

	if len(cmd.Args) != 1 || cmd.Args[0] != "nginx" {
		t.Error("Should have resource name in args")
	}
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
