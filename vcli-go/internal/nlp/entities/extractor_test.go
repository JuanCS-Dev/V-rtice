// Package entities - Unit tests
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package entities

import (
	"testing"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

func TestExtractor_BasicExtraction(t *testing.T) {
	extractor := NewExtractor()
	intent := &nlp.Intent{Category: nlp.IntentCategoryQUERY}

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
	}

	entities, err := extractor.Extract(tokens, intent)
	if err != nil {
		t.Fatalf("Extract() error = %v", err)
	}

	if len(entities) == 0 {
		t.Error("Expected at least one entity")
	}

	// Should extract "pods" as K8s resource
	foundResource := false
	for _, entity := range entities {
		if entity.Type == nlp.EntityTypeK8S_RESOURCE && entity.Normalized == "pods" {
			foundResource = true
			break
		}
	}

	if !foundResource {
		t.Error("Expected to extract pods as K8S_RESOURCE")
	}
}

func TestExtractor_WithNamespace(t *testing.T) {
	extractor := NewExtractor()
	intent := &nlp.Intent{Category: nlp.IntentCategoryQUERY}

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
		{Normalized: "namespaces", Type: nlp.TokenTypeNOUN},
		{Normalized: "prod", Type: nlp.TokenTypeIDENTIFIER},
	}

	entities, err := extractor.Extract(tokens, intent)
	if err != nil {
		t.Fatalf("Extract() error = %v", err)
	}

	// Should extract namespace
	foundNamespace := false
	for _, entity := range entities {
		if entity.Type == nlp.EntityTypeNAMESPACE && entity.Normalized == "prod" {
			foundNamespace = true
			break
		}
	}

	if !foundNamespace {
		t.Error("Expected to extract prod as NAMESPACE")
	}
}

func TestExtractor_WithFilter(t *testing.T) {
	extractor := NewExtractor()
	intent := &nlp.Intent{Category: nlp.IntentCategoryQUERY}

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
		{Normalized: "error", Type: nlp.TokenTypeFILTER},
	}

	entities, err := extractor.Extract(tokens, intent)
	if err != nil {
		t.Fatalf("Extract() error = %v", err)
	}

	// Should extract status filter
	foundFilter := false
	for _, entity := range entities {
		if entity.Type == nlp.EntityTypeSTATUS {
			foundFilter = true
			// Check field selector metadata
			if entity.Metadata != nil {
				selector, ok := entity.Metadata["field_selector"].(string)
				if !ok || selector == "" {
					t.Error("Expected field_selector in metadata")
				}
			}
			break
		}
	}

	if !foundFilter {
		t.Error("Expected to extract error as STATUS filter")
	}
}

func TestExtractor_WithNumber(t *testing.T) {
	extractor := NewExtractor()
	intent := &nlp.Intent{Category: nlp.IntentCategoryACTION}

	tokens := []nlp.Token{
		{Normalized: "scale", Type: nlp.TokenTypeVERB},
		{Normalized: "deployments", Type: nlp.TokenTypeNOUN},
		{Normalized: "5", Type: nlp.TokenTypeNUMBER},
	}

	entities, err := extractor.Extract(tokens, intent)
	if err != nil {
		t.Fatalf("Extract() error = %v", err)
	}

	// Should extract number
	foundNumber := false
	for _, entity := range entities {
		if entity.Type == nlp.EntityTypeNUMBER {
			foundNumber = true
			// Check numeric value in metadata
			if entity.Metadata != nil {
				val, ok := entity.Metadata["numeric_value"].(int)
				if !ok || val != 5 {
					t.Errorf("Expected numeric_value=5, got %v", val)
				}
			}
			break
		}
	}

	if !foundNumber {
		t.Error("Expected to extract 5 as NUMBER")
	}
}

func TestExtractor_ExtractK8sResource(t *testing.T) {
	extractor := NewExtractor()

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
	}

	resource := extractor.ExtractK8sResource(tokens)
	if resource == nil {
		t.Fatal("Expected K8s resource, got nil")
	}

	if resource.ResourceType != "pods" {
		t.Errorf("ResourceType = %v, want pods", resource.ResourceType)
	}

	if !resource.Plural {
		t.Error("Expected plural form")
	}
}

func TestExtractor_ExtractNamespace(t *testing.T) {
	extractor := NewExtractor()

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
		{Normalized: "namespaces", Type: nlp.TokenTypeNOUN},
		{Normalized: "production", Type: nlp.TokenTypeIDENTIFIER},
	}

	ns := extractor.ExtractNamespace(tokens)
	if ns != "production" {
		t.Errorf("ExtractNamespace() = %v, want production", ns)
	}
}

func TestExtractor_ExtractCount(t *testing.T) {
	extractor := NewExtractor()

	tokens := []nlp.Token{
		{Normalized: "scale", Type: nlp.TokenTypeVERB},
		{Normalized: "to", Type: nlp.TokenTypePREP},
		{Normalized: "10", Type: nlp.TokenTypeNUMBER},
	}

	count := extractor.ExtractCount(tokens)
	if count != 10 {
		t.Errorf("ExtractCount() = %v, want 10", count)
	}
}

func TestExtractor_FieldSelector(t *testing.T) {
	extractor := NewExtractor()

	tests := []struct {
		status   string
		expected string
	}{
		{"error", "status.phase=Failed"},
		{"failed", "status.phase=Failed"},
		{"running", "status.phase=Running"},
		{"pending", "status.phase=Pending"},
	}

	for _, tt := range tests {
		t.Run(tt.status, func(t *testing.T) {
			selector := extractor.toFieldSelector(tt.status)
			if selector != tt.expected {
				t.Errorf("toFieldSelector(%v) = %v, want %v", tt.status, selector, tt.expected)
			}
		})
	}
}

// ADDITIONAL TESTS FOR 90%+ COVERAGE

func TestExtractor_ExtractResourceName(t *testing.T) {
	extractor := NewExtractor()

	tests := []struct {
		name     string
		tokens   []nlp.Token
		expected string
	}{
		{
			name: "resource with name",
			tokens: []nlp.Token{
				{Normalized: "show", Type: nlp.TokenTypeVERB},
				{Normalized: "pods", Type: nlp.TokenTypeNOUN},
				{Normalized: "nginx", Type: nlp.TokenTypeIDENTIFIER},
			},
			expected: "nginx",
		},
		{
			name: "no identifier after resource",
			tokens: []nlp.Token{
				{Normalized: "show", Type: nlp.TokenTypeVERB},
				{Normalized: "pods", Type: nlp.TokenTypeNOUN},
			},
			expected: "",
		},
		{
			name: "no resource type",
			tokens: []nlp.Token{
				{Normalized: "show", Type: nlp.TokenTypeVERB},
				{Normalized: "nginx", Type: nlp.TokenTypeIDENTIFIER},
			},
			expected: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractor.ExtractResourceName(tt.tokens)
			if result != tt.expected {
				t.Errorf("ExtractResourceName() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestExtractor_ResolveAmbiguity(t *testing.T) {
	extractor := NewExtractor()

	tests := []struct {
		name     string
		entities []nlp.Entity
		context  *nlp.Context
		check    func(*testing.T, []nlp.Entity)
	}{
		{
			name: "adds namespace from context",
			entities: []nlp.Entity{
				{
					Type:       nlp.EntityTypeK8S_RESOURCE,
					Value:      "pods",
					Normalized: "pods",
				},
			},
			context: &nlp.Context{
				CurrentNS: "production",
			},
			check: func(t *testing.T, resolved []nlp.Entity) {
				if len(resolved) != 1 {
					t.Fatalf("Expected 1 entity, got %d", len(resolved))
				}
				if resolved[0].Metadata == nil {
					t.Fatal("Expected metadata to be set")
				}
				ns, ok := resolved[0].Metadata["namespace"]
				if !ok {
					t.Error("Expected namespace in metadata")
				}
				if ns != "production" {
					t.Errorf("Expected namespace=production, got %v", ns)
				}
			},
		},
		{
			name: "no context provided",
			entities: []nlp.Entity{
				{
					Type:       nlp.EntityTypeK8S_RESOURCE,
					Value:      "pods",
					Normalized: "pods",
				},
			},
			context: nil,
			check: func(t *testing.T, resolved []nlp.Entity) {
				if len(resolved) != 1 {
					t.Fatalf("Expected 1 entity, got %d", len(resolved))
				}
				// Should still work without context
			},
		},
		{
			name: "entity already has metadata",
			entities: []nlp.Entity{
				{
					Type:       nlp.EntityTypeK8S_RESOURCE,
					Value:      "pods",
					Normalized: "pods",
					Metadata: map[string]interface{}{
						"existing": "data",
					},
				},
			},
			context: &nlp.Context{
				CurrentNS: "staging",
			},
			check: func(t *testing.T, resolved []nlp.Entity) {
				if len(resolved) != 1 {
					t.Fatalf("Expected 1 entity, got %d", len(resolved))
				}
				// Should not add namespace if metadata exists
				if resolved[0].Metadata["existing"] != "data" {
					t.Error("Existing metadata should be preserved")
				}
			},
		},
		{
			name: "non-k8s resource entity",
			entities: []nlp.Entity{
				{
					Type:       nlp.EntityTypeNAME,
					Value:      "nginx",
					Normalized: "nginx",
				},
			},
			context: &nlp.Context{
				CurrentNS: "production",
			},
			check: func(t *testing.T, resolved []nlp.Entity) {
				if len(resolved) != 1 {
					t.Fatalf("Expected 1 entity, got %d", len(resolved))
				}
				// Non-K8s entities should not get namespace
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			resolved, err := extractor.ResolveAmbiguity(tt.entities, tt.context)
			if err != nil {
				t.Fatalf("ResolveAmbiguity() error = %v", err)
			}
			tt.check(t, resolved)
		})
	}
}

func TestExtractor_FieldSelector_AllCases(t *testing.T) {
	extractor := NewExtractor()

	tests := []struct {
		status   string
		expected string
	}{
		{"error", "status.phase=Failed"},
		{"failed", "status.phase=Failed"},
		{"fail", "status.phase=Failed"},
		{"running", "status.phase=Running"},
		{"pending", "status.phase=Pending"},
		{"completed", "status.phase=Succeeded"},
		{"complete", "status.phase=Succeeded"},
		{"unknown", "status.phase!=Unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.status, func(t *testing.T) {
			selector := extractor.toFieldSelector(tt.status)
			if selector != tt.expected {
				t.Errorf("toFieldSelector(%v) = %v, want %v", tt.status, selector, tt.expected)
			}
		})
	}
}

func TestExtractor_ParseNumber_InvalidInput(t *testing.T) {
	extractor := NewExtractor()

	tests := []struct {
		name     string
		input    string
		expected int
	}{
		{"valid number", "42", 42},
		{"invalid string", "abc", 0},
		{"empty string", "", 0},
		{"mixed", "12abc", 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractor.parseNumber(tt.input)
			if result != tt.expected {
				t.Errorf("parseNumber(%q) = %d, want %d", tt.input, result, tt.expected)
			}
		})
	}
}

func TestExtractor_ExtractK8sResource_NoResource(t *testing.T) {
	extractor := NewExtractor()

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "something", Type: nlp.TokenTypeIDENTIFIER},
	}

	resource := extractor.ExtractK8sResource(tokens)
	if resource != nil {
		t.Errorf("Expected nil for no resource, got %v", resource)
	}
}

func TestExtractor_ExtractNamespace_EdgeCases(t *testing.T) {
	extractor := NewExtractor()

	tests := []struct {
		name     string
		tokens   []nlp.Token
		expected string
	}{
		{
			name: "namespace at end (no following token)",
			tokens: []nlp.Token{
				{Normalized: "show", Type: nlp.TokenTypeVERB},
				{Normalized: "pods", Type: nlp.TokenTypeNOUN},
				{Normalized: "namespace", Type: nlp.TokenTypeNOUN},
			},
			expected: "",
		},
		{
			name: "no namespace keyword",
			tokens: []nlp.Token{
				{Normalized: "show", Type: nlp.TokenTypeVERB},
				{Normalized: "pods", Type: nlp.TokenTypeNOUN},
			},
			expected: "",
		},
		{
			name: "singular namespace keyword",
			tokens: []nlp.Token{
				{Normalized: "show", Type: nlp.TokenTypeVERB},
				{Normalized: "namespace", Type: nlp.TokenTypeNOUN},
				{Normalized: "dev", Type: nlp.TokenTypeIDENTIFIER},
			},
			expected: "dev",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := extractor.ExtractNamespace(tt.tokens)
			if result != tt.expected {
				t.Errorf("ExtractNamespace() = %q, want %q", result, tt.expected)
			}
		})
	}
}

func TestExtractor_ExtractCount_NoNumber(t *testing.T) {
	extractor := NewExtractor()

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
	}

	count := extractor.ExtractCount(tokens)
	if count != 0 {
		t.Errorf("ExtractCount() = %d, want 0", count)
	}
}

func TestExtractor_ExtractWithIdentifier_NotAfterNamespace(t *testing.T) {
	extractor := NewExtractor()
	intent := &nlp.Intent{Category: nlp.IntentCategoryQUERY}

	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "nginx-deployment", Type: nlp.TokenTypeIDENTIFIER},
	}

	entities, err := extractor.Extract(tokens, intent)
	if err != nil {
		t.Fatalf("Extract() error = %v", err)
	}

	// Should extract identifier as NAME (not NAMESPACE)
	found := false
	for _, entity := range entities {
		if entity.Type == nlp.EntityTypeNAME && entity.Normalized == "nginx-deployment" {
			found = true
			break
		}
	}

	if !found {
		t.Error("Expected to extract nginx-deployment as NAME")
	}
}

func BenchmarkExtractor_Extract(b *testing.B) {
	extractor := NewExtractor()
	intent := &nlp.Intent{Category: nlp.IntentCategoryQUERY}
	tokens := []nlp.Token{
		{Normalized: "show", Type: nlp.TokenTypeVERB},
		{Normalized: "pods", Type: nlp.TokenTypeNOUN},
		{Normalized: "error", Type: nlp.TokenTypeFILTER},
		{Normalized: "namespaces", Type: nlp.TokenTypeNOUN},
		{Normalized: "prod", Type: nlp.TokenTypeIDENTIFIER},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = extractor.Extract(tokens, intent)
	}
}
