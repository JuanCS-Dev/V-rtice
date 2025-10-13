// Package main - Simple NLP API Usage Example
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// Demonstrates basic NLP API usage
package main

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/verticedev/vcli-go/internal/nlp"
	"github.com/verticedev/vcli-go/internal/nlp/learning"
	nlptypes "github.com/verticedev/vcli-go/pkg/nlp"
)

func main() {
	// Example 1: Simple Query (Portuguese)
	fmt.Println("=== Example 1: Simple Query (Portuguese) ===")
	processExample("mostra os pods")

	// Example 2: Query with Namespace (Portuguese)
	fmt.Println("\n=== Example 2: Query with Namespace ===")
	processExample("lista pods no namespace production")

	// Example 3: Scale Command (English)
	fmt.Println("\n=== Example 3: Scale Command (English) ===")
	processExample("scale nginx deployment to 5 replicas")

	// Example 4: Query with Filter (English)
	fmt.Println("\n=== Example 4: Query with Filter ===")
	processExample("show failed pods in prod")

	// Example 5: Invalid Command (Typo)
	fmt.Println("\n=== Example 5: Invalid Command (Typo) ===")
	processExample("gte pods")

	// Example 6: Dangerous Operation
	fmt.Println("\n=== Example 6: Dangerous Operation ===")
	processExample("delete all pods in production")
}

func processExample(input string) {
	// Create temporary database for this example
	dbPath := filepath.Join(os.TempDir(), "nlp-example.db")
	defer os.RemoveAll(dbPath)

	// Create orchestrator
	orch, err := nlp.NewOrchestrator(dbPath)
	if err != nil {
		fmt.Printf("Error creating orchestrator: %v\n", err)
		return
	}
	defer orch.Close()

	fmt.Printf("Input: \"%s\"\n\n", input)

	// Process with feedback
	feedback := &learning.Feedback{
		Success:  true,
		Accepted: true,
	}

	result, err := orch.ProcessWithFeedback(input, "example-session", feedback)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	// Display results
	fmt.Printf("Success: %v\n", result.Success)

	if result.Intent != nil {
		fmt.Printf("Intent: %s (%s, confidence: %.1f%%)\n",
			result.Intent.Verb,
			result.Intent.Category,
			result.Intent.Confidence*100)
	}

	if len(result.Entities) > 0 {
		fmt.Println("Entities:")
		for _, entity := range result.Entities {
			fmt.Printf("  - %s: %s\n", entity.Type, entity.Value)
		}
	}

	if result.Command != nil {
		fmt.Printf("Command: %s\n", formatCommand(result.Command))
	}

	if result.Validation != nil {
		fmt.Printf("Valid: %v\n", result.Validation.Valid)
		if result.Validation.Dangerous {
			fmt.Printf("⚠️  WARNING: Dangerous operation!\n")
			fmt.Printf("Requires Confirmation: %v\n", result.Validation.RequiresConfirmation)
		}
		if len(result.Validation.Suggestions) > 0 {
			fmt.Println("Suggestions:")
			for _, sug := range result.Validation.Suggestions {
				fmt.Printf("  - %s\n", sug)
			}
		}
	}

	if !result.Success && result.Error != "" {
		fmt.Printf("Error: %s\n", result.Error)
	}

	fmt.Printf("Latency: %.2fms\n", result.LatencyMs)

	if result.PatternLearned {
		fmt.Printf("Pattern Learned: %s\n", result.PatternID[:8]+"...")
	}
}

func formatCommand(cmd *nlptypes.Command) string {
	result := "vcli"
	for _, p := range cmd.Path {
		result += " " + p
	}
	for k, v := range cmd.Flags {
		result += " " + k + " " + v
	}
	for _, a := range cmd.Args {
		result += " " + a
	}
	return result
}
