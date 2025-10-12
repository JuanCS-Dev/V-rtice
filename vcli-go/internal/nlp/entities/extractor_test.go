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
