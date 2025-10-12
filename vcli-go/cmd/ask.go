package main

import (
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/nlp"
	"github.com/verticedev/vcli-go/pkg/nlp/orchestrator"
)

// askCmd represents the NLP natural language interface
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// This is the CLI entrypoint for the "Guardian of Intent" v2.0
// Zero Trust NLP parser with 7 layers of security validation
var askCmd = &cobra.Command{
	Use:   "ask [query]",
	Short: "🧠 Natural Language Interface - Ask in your own words",
	Long: `Natural Language Interface for vCLI with Zero Trust Security.

The "Guardian of Intent" v2.0 implements 7 layers of security:
  1. Authentication    - MFA, crypto keys, JWT
  2. Authorization     - RBAC, ABAC, risk scoring
  3. Sandboxing        - Namespaces, capabilities, seccomp
  4. Intent Validation - HITL, reverse translation, signing
  5. Rate Limiting     - Token bucket, circuit breakers
  6. Behavioral        - Anomaly detection, adaptive response
  7. Audit             - Immutable logs, Merkle integrity

Examples:
  # Portuguese
  vcli ask "mostra os pods com problema"
  vcli ask "deleta pods antigos no staging"
  vcli ask "escala o nginx pra 5 replicas"
  
  # English
  vcli ask "show pods with errors"
  vcli ask "delete old pods in staging"
  vcli ask "scale nginx to 5 replicas"
  
  # Informal/Colloquial (Juan's style 😄)
  vcli ask "bora ver uns pods ae"
  vcli ask "da um jeito naqueles pods bugados"
  vcli ask "aumenta o nginx pra dar conta do tranco"

Security:
  - ALL commands require authentication
  - Destructive operations require explicit confirmation (HITL)
  - Critical operations require cryptographic signing
  - All actions are logged immutably

Architect: Juan Carlos (Inspired by Jesus Christ)
Co-Author: Claude (MAXIMUS AI Assistant)`,
	Example: `  # Simple queries
  vcli ask "list pods"
  vcli ask "mostra deployments"
  
  # With filters
  vcli ask "show pods in production namespace"
  vcli ask "lista pods com status error"
  
  # Operations (will require confirmation)
  vcli ask "delete pod nginx-abc123"
  vcli ask "scale deployment api to 3 replicas"`,
	Args: cobra.MinimumNArgs(1),
	RunE: runNLPQuery,
}

var (
	// askCmd flags
	askDryRun         bool
	askConfirm        bool
	askVerbose        bool
	askSkipValidation bool // DANGEROUS - only for dev/testing
	askTimeout        time.Duration
)

func init() {
	rootCmd.AddCommand(askCmd)

	// Flags
	askCmd.Flags().BoolVarP(&askDryRun, "dry-run", "d", false, "Simulate without executing (safe preview)")
	askCmd.Flags().BoolVarP(&askConfirm, "yes", "y", false, "Auto-confirm low-risk operations (not for destructive ops)")
	askCmd.Flags().BoolVarP(&askVerbose, "verbose", "v", false, "Show detailed parsing and validation steps")
	askCmd.Flags().BoolVar(&askSkipValidation, "skip-validation", false, "DANGEROUS: Skip security validation (dev only)")
	askCmd.Flags().DurationVar(&askTimeout, "timeout", 30*time.Second, "Query timeout")

	// Mark dangerous flags as hidden in production
	if os.Getenv("VCLI_ENV") == "production" {
		askCmd.Flags().MarkHidden("skip-validation")
	}
}

// runNLPQuery executes the NLP query through the Guardian orchestrator
func runNLPQuery(cmd *cobra.Command, args []string) error {
	// Combine args into single query
	query := strings.Join(args, " ")
	
	if askVerbose {
		fmt.Printf("🧠 Parsing query: %q\n\n", query)
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), askTimeout)
	defer cancel()

	// Initialize NLP parser (basic pattern matching)
	parser := nlp.NewParser()
	
	// Parse query into structured intent
	if askVerbose {
		fmt.Println("📖 Step 1/7: Tokenizing and parsing...")
	}
	
	intent, err := parser.Parse(ctx, query)
	if err != nil {
		return fmt.Errorf("❌ Failed to parse query: %w", err)
	}

	if askVerbose {
		fmt.Printf("✅ Parsed intent: %s\n", intent.Action)
		fmt.Printf("   Resource: %s\n", intent.Resource)
		if intent.ResourceName != "" {
			fmt.Printf("   Name: %s\n", intent.ResourceName)
		}
		if intent.Namespace != "" {
			fmt.Printf("   Namespace: %s\n", intent.Namespace)
		}
		fmt.Println()
	}

	// Build command from intent
	if askVerbose {
		fmt.Println("🔨 Step 2/7: Building command...")
	}

	generator := nlp.NewGenerator()
	command, err := generator.Generate(intent)
	if err != nil {
		return fmt.Errorf("❌ Failed to generate command: %w", err)
	}

	if askVerbose {
		fmt.Printf("✅ Generated command: %s\n\n", command)
	}

	// Create orchestrator with full security stack
	orch, err := orchestrator.NewOrchestrator(orchestrator.Config{
		SkipValidation: askSkipValidation,
		DryRun:        askDryRun,
		Verbose:       askVerbose,
	})
	if err != nil {
		return fmt.Errorf("❌ Failed to initialize security orchestrator: %w", err)
	}
	defer orch.Close()

	// Execute through Guardian (7 layers of security)
	if askVerbose {
		fmt.Println("🛡️  Executing through Guardian (7-layer security)...\n")
	}

	result, err := orch.Execute(ctx, intent)
	if err != nil {
		return fmt.Errorf("❌ Execution failed: %w", err)
	}

	// Display results
	displayResult(result, askVerbose)

	return nil
}

// displayResult formats and displays the execution result
func displayResult(result *orchestrator.ExecutionResult, verbose bool) {
	if verbose {
		fmt.Println("\n" + strings.Repeat("─", 60))
		fmt.Println("📊 EXECUTION REPORT")
		fmt.Println(strings.Repeat("─", 60))
		
		// Security validation steps
		fmt.Println("\n🛡️  Security Validation:")
		for i, step := range result.ValidationSteps {
			status := "✅"
			if !step.Passed {
				status = "❌"
			}
			fmt.Printf("  %d. [%s] %s: %s\n", i+1, status, step.Layer, step.Message)
		}

		// Command executed
		fmt.Printf("\n💻 Command: %s\n", result.Command)
		
		// Execution metadata
		fmt.Printf("\n⏱️  Duration: %v\n", result.Duration)
		fmt.Printf("📝 Audit Log ID: %s\n", result.AuditID)
	}

	// Output from command
	if result.Success {
		fmt.Println("\n✅ Success!")
		if result.Output != "" {
			fmt.Println("\n" + result.Output)
		}
	} else {
		fmt.Printf("\n❌ Failed: %s\n", result.Error)
		if result.Output != "" {
			fmt.Println("\n" + result.Output)
		}
	}

	// Warnings
	if len(result.Warnings) > 0 {
		fmt.Println("\n⚠️  Warnings:")
		for _, w := range result.Warnings {
			fmt.Printf("  - %s\n", w)
		}
	}

	if verbose {
		fmt.Println("\n" + strings.Repeat("─", 60))
	}
}
