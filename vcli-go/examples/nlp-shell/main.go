// Package main - NLP Interactive Shell Demo
//
// Lead Architect: Juan Carlos (Inspiration: Jesus Christ)
// Co-Author: Claude (MAXIMUS AI Assistant)
//
// Interactive shell demonstrating complete NLP pipeline integration
package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/verticedev/vcli-go/internal/nlp"
	"github.com/verticedev/vcli-go/internal/nlp/learning"
	nlptypes "github.com/verticedev/vcli-go/pkg/nlp"
)

const (
	colorReset  = "\033[0m"
	colorRed    = "\033[31m"
	colorGreen  = "\033[32m"
	colorYellow = "\033[33m"
	colorBlue   = "\033[34m"
	colorPurple = "\033[35m"
	colorCyan   = "\033[36m"
	colorWhite  = "\033[37m"
	colorBold   = "\033[1m"
)

func main() {
	fmt.Printf("%s%s", colorBold, colorCyan)
	fmt.Println("╔════════════════════════════════════════════════════════════════╗")
	fmt.Println("║          VCLI Natural Language Processing Shell                ║")
	fmt.Println("║              Powered by MAXIMUS AI Engine                      ║")
	fmt.Println("╚════════════════════════════════════════════════════════════════╝")
	fmt.Printf("%s\n", colorReset)

	// Create learning database path
	homeDir, err := os.UserHomeDir()
	if err != nil {
		homeDir = "/tmp"
	}
	dbPath := filepath.Join(homeDir, ".vcli", "nlp-learning.db")

	// Ensure directory exists
	if err := os.MkdirAll(filepath.Dir(dbPath), 0755); err != nil {
		fmt.Printf("%sError creating config directory: %v%s\n", colorRed, err, colorReset)
		return
	}

	// Create orchestrator
	fmt.Printf("%sInitializing NLP engine...%s ", colorYellow, colorReset)
	orch, err := nlp.NewOrchestrator(dbPath)
	if err != nil {
		fmt.Printf("%s✗%s\n", colorRed, colorReset)
		fmt.Printf("%sError: %v%s\n", colorRed, err, colorReset)
		return
	}
	defer orch.Close()
	fmt.Printf("%s✓%s\n", colorGreen, colorReset)

	// Create session
	sessionID := "shell-session-" + fmt.Sprintf("%d", os.Getpid())

	// Show help
	showHelp()

	// Main shell loop
	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Printf("\n%s%svcli>%s ", colorBold, colorGreen, colorReset)

		if !scanner.Scan() {
			break
		}

		input := strings.TrimSpace(scanner.Text())

		// Handle special commands
		if input == "" {
			continue
		}

		switch input {
		case "exit", "quit", "q":
			fmt.Printf("%sGoodbye! 👋%s\n", colorCyan, colorReset)
			printStats(orch)
			return

		case "help", "?":
			showHelp()
			continue

		case "stats":
			printStats(orch)
			continue

		case "popular":
			showPopularCommands(orch)
			continue

		case "clear":
			fmt.Print("\033[H\033[2J")
			continue

		case "suggest":
			fmt.Printf("%sEnter partial command: %s", colorYellow, colorReset)
			if scanner.Scan() {
				partial := scanner.Text()
				suggestions := orch.GetSuggestions(partial)
				if len(suggestions) > 0 {
					fmt.Printf("\n%sSuggestions:%s\n", colorCyan, colorReset)
					for i, sug := range suggestions {
						fmt.Printf("  %d. %s (confidence: %.2f)\n", i+1, sug.Text, sug.Confidence)
					}
				} else {
					fmt.Printf("%sNo suggestions found%s\n", colorYellow, colorReset)
				}
			}
			continue
		}

		// Process natural language input
		processInput(orch, input, sessionID)
	}

	if err := scanner.Err(); err != nil {
		fmt.Printf("%sError reading input: %v%s\n", colorRed, err, colorReset)
	}
}

func processInput(orch *nlp.Orchestrator, input string, sessionID string) {
	fmt.Printf("\n%s⚙  Processing...%s\n", colorYellow, colorReset)

	// Process with orchestrator
	result, err := orch.Process(input, sessionID)
	if err != nil {
		fmt.Printf("%s✗ Error: %v%s\n", colorRed, err, colorReset)
		return
	}

	// Show results
	fmt.Printf("\n%s┌─ Analysis%s\n", colorBlue, colorReset)
	fmt.Printf("%s│%s Input: %s%s%s\n", colorBlue, colorReset, colorWhite, result.Input, colorReset)

	if result.Intent != nil {
		fmt.Printf("%s│%s Intent: %s%s%s (%s%.1f%% confidence%s)\n",
			colorBlue, colorReset,
			colorCyan, result.Intent.Verb, colorReset,
			colorYellow, result.Intent.Confidence*100, colorReset)
	}

	if len(result.Entities) > 0 {
		fmt.Printf("%s│%s Entities: ", colorBlue, colorReset)
		for i, entity := range result.Entities {
			if i > 0 {
				fmt.Print(", ")
			}
			fmt.Printf("%s%s%s=%s", colorPurple, entity.Type, colorReset, entity.Value)
		}
		fmt.Println()
	}

	fmt.Printf("%s│%s Latency: %s%.2fms%s\n",
		colorBlue, colorReset, colorYellow, result.LatencyMs, colorReset)
	fmt.Printf("%s└─────────%s\n", colorBlue, colorReset)

	// Check validation
	if !result.Success {
		fmt.Printf("\n%s✗ Invalid Command%s\n", colorRed, colorReset)
		fmt.Printf("  %s%s%s\n", colorRed, result.Error, colorReset)

		// Show suggestions
		if result.Validation != nil && len(result.Validation.Suggestions) > 0 {
			fmt.Printf("\n%s💡 Did you mean:%s\n", colorYellow, colorReset)
			for i, sug := range result.Validation.Suggestions {
				fmt.Printf("  %d. %s\n", i+1, sug)
			}
		}
		return
	}

	// Show command
	if result.Command != nil {
		fmt.Printf("\n%s┌─ Generated Command%s\n", colorGreen, colorReset)
		cmdStr := formatCommand(result.Command)
		fmt.Printf("%s│%s %s%s%s\n", colorGreen, colorReset, colorBold, cmdStr, colorReset)
		fmt.Printf("%s└──────────────────%s\n", colorGreen, colorReset)
	}

	// Check if dangerous
	if result.Validation != nil && result.Validation.RequiresConfirmation {
		fmt.Printf("\n%s⚠️  WARNING:%s %s\n", colorRed, colorReset, result.Validation.Warnings[0])
		fmt.Printf("%sProceed? (yes/no): %s", colorYellow, colorReset)

		scanner := bufio.NewScanner(os.Stdin)
		if scanner.Scan() {
			response := strings.ToLower(strings.TrimSpace(scanner.Text()))
			if response != "yes" && response != "y" {
				fmt.Printf("%s✗ Operation cancelled%s\n", colorRed, colorReset)
				return
			}
		}
	}

	// Show pattern info
	if result.PatternLearned {
		fmt.Printf("\n%s💾 Pattern learned (ID: %s)%s\n", colorCyan, result.PatternID[:8]+"...", colorReset)
	}

	if result.SimilarPatterns > 0 {
		fmt.Printf("%s🔍 Found %d similar patterns%s\n", colorCyan, result.SimilarPatterns, colorReset)
	}

	// In a real implementation, you would execute the command here
	fmt.Printf("\n%s✓ Ready to execute%s\n", colorGreen, colorReset)
	fmt.Printf("%s(In production, command would be executed here)%s\n", colorYellow, colorReset)

	// Record positive feedback
	feedback := &learning.Feedback{
		PatternID: result.PatternID,
		Success:   true,
		Accepted:  true,
	}
	orch.ProcessWithFeedback(input, sessionID, feedback)
}

func formatCommand(cmd *nlptypes.Command) string {
	parts := []string{"vcli"}
	parts = append(parts, cmd.Path...)

	for k, v := range cmd.Flags {
		parts = append(parts, k, v)
	}

	parts = append(parts, cmd.Args...)

	return strings.Join(parts, " ")
}

func showHelp() {
	fmt.Printf("\n%s%s📖 Available Commands:%s\n", colorBold, colorCyan, colorReset)
	fmt.Printf("  %shelp, ?%s       - Show this help\n", colorGreen, colorReset)
	fmt.Printf("  %sstats%s         - Show processing statistics\n", colorGreen, colorReset)
	fmt.Printf("  %spopular%s       - Show popular commands\n", colorGreen, colorReset)
	fmt.Printf("  %ssuggest%s       - Get suggestions for partial input\n", colorGreen, colorReset)
	fmt.Printf("  %sclear%s         - Clear screen\n", colorGreen, colorReset)
	fmt.Printf("  %sexit, quit, q%s - Exit shell\n", colorGreen, colorReset)

	fmt.Printf("\n%s%s💬 Example Queries:%s\n", colorBold, colorCyan, colorReset)
	fmt.Printf("  %s• Portuguese:%s\n", colorYellow, colorReset)
	fmt.Printf("    - mostra os pods\n")
	fmt.Printf("    - lista pods no namespace production\n")
	fmt.Printf("    - escala nginx para 5 replicas\n")
	fmt.Printf("    - pods com problema no prod\n")

	fmt.Printf("  %s• English:%s\n", colorYellow, colorReset)
	fmt.Printf("    - show me the pods\n")
	fmt.Printf("    - list pods in production namespace\n")
	fmt.Printf("    - scale nginx to 5 replicas\n")
	fmt.Printf("    - show failed pods in prod\n")
}

func printStats(orch *nlp.Orchestrator) {
	stats := orch.GetStats()
	if stats == nil {
		fmt.Printf("%sNo statistics available%s\n", colorYellow, colorReset)
		return
	}

	fmt.Printf("\n%s%s📊 Statistics:%s\n", colorBold, colorCyan, colorReset)
	fmt.Printf("  Total Requests:    %s%d%s\n", colorWhite, stats.TotalRequests, colorReset)
	fmt.Printf("  Successful:        %s%d%s\n", colorGreen, stats.SuccessfulRequests, colorReset)
	fmt.Printf("  Failed:            %s%d%s\n", colorRed, stats.FailedRequests, colorReset)
	fmt.Printf("  Validation Errors: %s%d%s\n", colorYellow, stats.ValidationFailures, colorReset)
	fmt.Printf("  Avg Latency:       %s%.2fms%s\n", colorCyan, stats.AverageLatencyMs, colorReset)

	// Get detailed stats
	detailed := orch.GetDetailedStats()
	if learning, ok := detailed["learning"].(*learning.EngineStats); ok {
		fmt.Printf("\n%s%s📚 Learning Engine:%s\n", colorBold, colorCyan, colorReset)
		fmt.Printf("  Total Patterns:  %s%d%s\n", colorWhite, learning.TotalPatterns, colorReset)
		fmt.Printf("  Cache Hit Rate:  %s%.1f%%%s\n", colorGreen, learning.CacheHitRate*100, colorReset)
		fmt.Printf("  Avg Success:     %s%.1f%%%s\n", colorGreen, learning.AverageSuccessRate*100, colorReset)
	}

	if sessions, ok := detailed["active_sessions"].(int); ok {
		fmt.Printf("\n%s%s👥 Sessions:%s\n", colorBold, colorCyan, colorReset)
		fmt.Printf("  Active Sessions: %s%d%s\n", colorWhite, sessions, colorReset)
	}
}

func showPopularCommands(orch *nlp.Orchestrator) {
	popular, err := orch.GetPopularCommands(10)
	if err != nil {
		fmt.Printf("%sError getting popular commands: %v%s\n", colorRed, err, colorReset)
		return
	}

	if len(popular) == 0 {
		fmt.Printf("%sNo patterns learned yet%s\n", colorYellow, colorReset)
		return
	}

	fmt.Printf("\n%s%s🔥 Popular Commands (Top %d):%s\n", colorBold, colorCyan, len(popular), colorReset)
	for i, pattern := range popular {
		fmt.Printf("  %s%d.%s %s%s%s (used %s%d%s times, success rate: %s%.1f%%%s)\n",
			colorYellow, i+1, colorReset,
			colorWhite, pattern.Input, colorReset,
			colorCyan, pattern.Frequency, colorReset,
			colorGreen, pattern.SuccessRate*100, colorReset)
	}
}
