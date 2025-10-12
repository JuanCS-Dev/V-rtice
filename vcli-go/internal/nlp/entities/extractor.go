// Package entities implements entity extraction
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This extractor identifies and extracts structured entities from tokens.
package entities

import (
	"strconv"
	"strings"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// Extractor handles entity extraction from tokens
type Extractor struct{}

// NewExtractor creates a new entity extractor
func NewExtractor() *Extractor {
	return &Extractor{}
}

// Extract extracts entities from tokens based on intent
//
// Extraction strategy:
// 1. Identify K8s resources (pods, deployments, etc.)
// 2. Extract names and identifiers
// 3. Extract filters and conditions
// 4. Extract numeric values
// 5. Extract time ranges
func (e *Extractor) Extract(tokens []nlp.Token, intent *nlp.Intent) ([]nlp.Entity, error) {
	entities := make([]nlp.Entity, 0)

	for i, token := range tokens {
		var entity *nlp.Entity

		switch token.Type {
		case nlp.TokenTypeNOUN:
			// K8s resource types
			entity = &nlp.Entity{
				Type:       nlp.EntityTypeK8S_RESOURCE,
				Value:      token.Raw,
				Normalized: token.Normalized,
				Span:       [2]int{i, i + 1},
			}

		case nlp.TokenTypeIDENTIFIER:
			// Check if this is a namespace
			if i > 0 && tokens[i-1].Normalized == "namespaces" {
				entity = &nlp.Entity{
					Type:       nlp.EntityTypeNAMESPACE,
					Value:      token.Raw,
					Normalized: token.Normalized,
					Span:       [2]int{i, i + 1},
				}
			} else {
				// Generic name/identifier
				entity = &nlp.Entity{
					Type:       nlp.EntityTypeNAME,
					Value:      token.Raw,
					Normalized: token.Normalized,
					Span:       [2]int{i, i + 1},
				}
			}

		case nlp.TokenTypeNUMBER:
			// Numeric value
			entity = &nlp.Entity{
				Type:       nlp.EntityTypeNUMBER,
				Value:      token.Raw,
				Normalized: token.Normalized,
				Span:       [2]int{i, i + 1},
				Metadata: map[string]interface{}{
					"numeric_value": e.parseNumber(token.Normalized),
				},
			}

		case nlp.TokenTypeFILTER:
			// Status filter
			entity = &nlp.Entity{
				Type:       nlp.EntityTypeSTATUS,
				Value:      token.Raw,
				Normalized: token.Normalized,
				Span:       [2]int{i, i + 1},
				Metadata: map[string]interface{}{
					"field_selector": e.toFieldSelector(token.Normalized),
				},
			}
		}

		if entity != nil {
			entities = append(entities, *entity)
		}
	}

	return entities, nil
}

// parseNumber converts string to number
func (e *Extractor) parseNumber(s string) int {
	n, err := strconv.Atoi(s)
	if err != nil {
		return 0
	}
	return n
}

// toFieldSelector converts status filter to K8s field selector
func (e *Extractor) toFieldSelector(status string) string {
	switch status {
	case "error", "failed", "fail":
		return "status.phase=Failed"
	case "running":
		return "status.phase=Running"
	case "pending":
		return "status.phase=Pending"
	case "completed", "complete":
		return "status.phase=Succeeded"
	default:
		return "status.phase!=" + strings.Title(status)
	}
}

// ExtractK8sResource extracts K8s-specific resource information
func (e *Extractor) ExtractK8sResource(tokens []nlp.Token) *K8sResourceEntity {
	for _, token := range tokens {
		if token.Type == nlp.TokenTypeNOUN {
			return &K8sResourceEntity{
				ResourceType: token.Normalized,
				Plural:       strings.HasSuffix(token.Normalized, "s"),
			}
		}
	}
	return nil
}

// K8sResourceEntity represents a Kubernetes resource
type K8sResourceEntity struct {
	ResourceType string
	Plural       bool
	Name         string
	Namespace    string
	Labels       map[string]string
}

// ExtractNamespace finds namespace from tokens
func (e *Extractor) ExtractNamespace(tokens []nlp.Token) string {
	for i, token := range tokens {
		if token.Normalized == "namespaces" || token.Normalized == "namespace" {
			// Next token should be the namespace name
			if i+1 < len(tokens) {
				return tokens[i+1].Normalized
			}
		}
	}
	return ""
}

// ExtractResourceName finds resource name from tokens
func (e *Extractor) ExtractResourceName(tokens []nlp.Token) string {
	// Look for identifier after resource type
	foundResource := false
	for _, token := range tokens {
		if token.Type == nlp.TokenTypeNOUN {
			foundResource = true
			continue
		}
		if foundResource && token.Type == nlp.TokenTypeIDENTIFIER {
			return token.Normalized
		}
	}
	return ""
}

// ExtractCount finds numeric count (replicas, limits, etc.)
func (e *Extractor) ExtractCount(tokens []nlp.Token) int {
	for _, token := range tokens {
		if token.Type == nlp.TokenTypeNUMBER {
			return e.parseNumber(token.Normalized)
		}
	}
	return 0
}

// ResolveAmbiguity resolves ambiguous entities using context
func (e *Extractor) ResolveAmbiguity(entities []nlp.Entity, context *nlp.Context) ([]nlp.Entity, error) {
	resolved := make([]nlp.Entity, len(entities))
	copy(resolved, entities)

	for i := range resolved {
		entity := &resolved[i]

		// Use context to resolve namespace if not specified
		if entity.Type == nlp.EntityTypeK8S_RESOURCE && entity.Metadata == nil {
			if context != nil && context.CurrentNS != "" {
				if entity.Metadata == nil {
					entity.Metadata = make(map[string]interface{})
				}
				entity.Metadata["namespace"] = context.CurrentNS
			}
		}
	}

	return resolved, nil
}
