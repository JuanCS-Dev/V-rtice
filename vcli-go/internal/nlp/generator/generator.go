// Package generator implements command generation from NLP results
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This generator converts Intent + Entities into executable vcli commands.
package generator

import (
	"fmt"
	"strings"

	"github.com/verticedev/vcli-go/pkg/nlp"
)

// Generator handles command generation
type Generator struct{}

// NewGenerator creates a new command generator
func NewGenerator() *Generator {
	return &Generator{}
}

// Generate creates a vcli command from intent and entities
//
// Generation strategy:
// 1. Map intent verb to command path
// 2. Add resource type from entities
// 3. Add filters and modifiers as flags
// 4. Construct full command with arguments
func (g *Generator) Generate(intent *nlp.Intent, entities []nlp.Entity) (*nlp.Command, error) {
	if intent == nil {
		return nil, &nlp.ParseError{
			Type:    nlp.ErrorTypeGeneration,
			Message: "Intent is required",
		}
	}

	// Build command path (e.g., ["k8s", "get", "pods"])
	path := g.buildPath(intent, entities)

	// Build flags (e.g., -n namespace, --field-selector)
	flags := g.buildFlags(intent, entities)

	// Build arguments
	args := g.buildArgs(intent, entities)

	cmd := &nlp.Command{
		Path:       path,
		Flags:      flags,
		Args:       args,
		Confidence: intent.Confidence,
	}

	return cmd, nil
}

// buildPath constructs command path from intent
func (g *Generator) buildPath(intent *nlp.Intent, entities []nlp.Entity) []string {
	path := []string{"k8s"} // vcli k8s subsystem

	// Map verb to kubectl verb
	kubectlVerb := g.mapVerbToKubectl(intent.Verb)
	path = append(path, kubectlVerb)

	// Add resource type
	if intent.Target != "" {
		path = append(path, intent.Target)
	}

	return path
}

// mapVerbToKubectl maps NLP verb to kubectl verb
func (g *Generator) mapVerbToKubectl(verb string) string {
	mapping := map[string]string{
		"show":     "get",
		"list":     "get",
		"delete":   "delete",
		"remove":   "delete",
		"scale":    "scale",
		"create":   "create",
		"apply":    "apply",
		"describe": "describe",
	}

	if mapped, ok := mapping[verb]; ok {
		return mapped
	}

	return verb
}

// buildFlags constructs command flags from intent modifiers and entities
func (g *Generator) buildFlags(intent *nlp.Intent, entities []nlp.Entity) map[string]string {
	flags := make(map[string]string)

	// Extract namespace from entities
	for _, entity := range entities {
		if entity.Type == nlp.EntityTypeNAMESPACE {
			flags["-n"] = entity.Normalized
		}
	}

	// Extract status filters
	for _, entity := range entities {
		if entity.Type == nlp.EntityTypeSTATUS && entity.Metadata != nil {
			if selector, ok := entity.Metadata["field_selector"].(string); ok {
				flags["--field-selector"] = selector
			}
		}
	}

	// Extract replicas count for scale
	if intent.Verb == "scale" {
		for _, entity := range entities {
			if entity.Type == nlp.EntityTypeNUMBER && entity.Metadata != nil {
				if count, ok := entity.Metadata["numeric_value"].(int); ok {
					flags["--replicas"] = fmt.Sprintf("%d", count)
				}
			}
		}
	}

	// Process intent modifiers (but don't override entity-derived values)
	for _, mod := range intent.Modifiers {
		switch mod.Type {
		case "namespace":
			if _, exists := flags["-n"]; !exists {
				flags[mod.Key] = mod.Value
			}
		case "filter":
			// Only set if entity didn't already provide field-selector
			if _, exists := flags["--field-selector"]; !exists {
				flags["--field-selector"] = fmt.Sprintf("status.phase!=%s", strings.Title(mod.Value))
			}
		case "count":
			if _, exists := flags[mod.Key]; !exists {
				flags[mod.Key] = mod.Value
			}
		}
	}

	return flags
}

// buildArgs constructs command arguments
func (g *Generator) buildArgs(intent *nlp.Intent, entities []nlp.Entity) []string {
	args := make([]string, 0)

	// Add resource name if present
	for _, entity := range entities {
		if entity.Type == nlp.EntityTypeNAME {
			// For scale, need deployment/name format
			if intent.Verb == "scale" && intent.Target != "" {
				resourceName := fmt.Sprintf("%s/%s", strings.TrimSuffix(intent.Target, "s"), entity.Normalized)
				args = append(args, resourceName)
			} else {
				args = append(args, entity.Normalized)
			}
		}
	}

	return args
}

// GenerateAlternatives generates alternative command interpretations
func (g *Generator) GenerateAlternatives(intent *nlp.Intent, entities []nlp.Entity, alternatives []*nlp.Intent) ([]*nlp.Command, error) {
	commands := make([]*nlp.Command, 0)

	for _, altIntent := range alternatives {
		cmd, err := g.Generate(altIntent, entities)
		if err == nil {
			commands = append(commands, cmd)
		}
	}

	return commands, nil
}

// ValidateCommand checks if generated command is valid
func (g *Generator) ValidateCommand(cmd *nlp.Command) error {
	if len(cmd.Path) == 0 {
		return &nlp.ParseError{
			Type:    nlp.ErrorTypeGeneration,
			Message: "Command path is empty",
		}
	}

	// Check if command is a known vcli command
	if cmd.Path[0] != "k8s" && cmd.Path[0] != "security" && cmd.Path[0] != "workflow" {
		return &nlp.ParseError{
			Type:    nlp.ErrorTypeGeneration,
			Message: fmt.Sprintf("Unknown command subsystem: %s", cmd.Path[0]),
			Suggestion: "Try k8s, security, or workflow commands",
		}
	}

	return nil
}

// ExplainCommand generates human-readable explanation of command
func (g *Generator) ExplainCommand(cmd *nlp.Command) string {
	explanation := strings.Builder{}

	// Describe action
	if len(cmd.Path) >= 2 {
		verb := cmd.Path[1]
		switch verb {
		case "get":
			explanation.WriteString("Show")
		case "delete":
			explanation.WriteString("Delete")
		case "scale":
			explanation.WriteString("Scale")
		case "describe":
			explanation.WriteString("Describe")
		default:
			explanation.WriteString(strings.Title(verb))
		}
	}

	// Describe target
	if len(cmd.Path) >= 3 {
		explanation.WriteString(" ")
		explanation.WriteString(cmd.Path[2])
	}

	// Describe filters
	if selector, ok := cmd.Flags["--field-selector"]; ok {
		explanation.WriteString(" with ")
		explanation.WriteString(selector)
	}

	// Describe namespace
	if ns, ok := cmd.Flags["-n"]; ok {
		explanation.WriteString(" in namespace ")
		explanation.WriteString(ns)
	}

	// Describe replicas
	if replicas, ok := cmd.Flags["--replicas"]; ok {
		explanation.WriteString(" to ")
		explanation.WriteString(replicas)
		explanation.WriteString(" replicas")
	}

	return explanation.String()
}
