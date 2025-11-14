package cmd

import (
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/spf13/cobra"
	"github.com/verticedev/vcli-go/internal/maximus"
	"github.com/verticedev/vcli-go/internal/immune"
)

var troubleshootCmd = &cobra.Command{
	Use:   "troubleshoot [service]",
	Short: "Diagnose and troubleshoot service connectivity issues",
	Long: `Troubleshoot performs automated diagnostics for vCLI services.

It checks:
- Service reachability
- Health endpoint status
- Configuration validity
- Common connectivity issues

Available services: maximus, immune, hitl, consciousness, all

Examples:
  # Troubleshoot MAXIMUS Governance
  vcli troubleshoot maximus

  # Troubleshoot Immune Core
  vcli troubleshoot immune

  # Troubleshoot all services
  vcli troubleshoot all`,
	ValidArgs: []string{"maximus", "immune", "hitl", "consciousness", "all"},
	Args:      cobra.ExactArgs(1),
	RunE:      runTroubleshoot,
}

func runTroubleshoot(cmd *cobra.Command, args []string) error {
	service := args[0]

	fmt.Println("🔍 vCLI Troubleshooter")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println()

	switch service {
	case "maximus":
		return troubleshootMaximus()
	case "immune":
		return troubleshootImmune()
	case "hitl":
		return troubleshootHITL()
	case "consciousness":
		return troubleshootConsciousness()
	case "all":
		troubleshootMaximus()
		fmt.Println()
		troubleshootImmune()
		fmt.Println()
		troubleshootHITL()
		return nil
	default:
		return fmt.Errorf("unknown service: %s (use: maximus, immune, hitl, consciousness, or all)", service)
	}
}

func troubleshootMaximus() error {
	fmt.Println("📊 MAXIMUS Governance API")
	fmt.Println("─────────────────────────")

	// 1. Check configuration
	endpoint := getMaximusServer()
	if endpoint == "" {
		endpoint = "http://localhost:8150" // default
	}

	fmt.Printf("✓ Configuration loaded\n")
	fmt.Printf("  Endpoint: %s\n", endpoint)

	// 2. Check connectivity
	client := maximus.NewGovernanceClient(endpoint)

	fmt.Print("  Testing connectivity... ")
	health, err := client.Health()
	if err != nil {
		fmt.Printf("❌ FAILED\n")
		fmt.Printf("  Error: %v\n", err)
		fmt.Println()
		printMaximusSuggestions()
		return nil
	}
	fmt.Printf("✓ SUCCESS\n")

	// 3. Check health
	fmt.Printf("  Service status: %s\n", health.Status)
	if health.Version != "" {
		fmt.Printf("  Version: %s\n", health.Version)
	}

	// 4. Try listing decisions
	fmt.Print("  Testing API functionality... ")
	_, err = client.GetPendingStats()
	if err != nil {
		fmt.Printf("⚠️  WARNING\n")
		fmt.Printf("  Error: %v\n", err)
	} else {
		fmt.Printf("✓ SUCCESS\n")
	}

	fmt.Println()
	fmt.Println("✅ MAXIMUS Governance is operational")
	return nil
}

func troubleshootImmune() error {
	fmt.Println("🛡️  Active Immune Core")
	fmt.Println("─────────────────────────")

	// 1. Check configuration
	endpoint := getImmuneServer()
	if endpoint == "" {
		endpoint = "http://localhost:8200" // default
	}

	fmt.Printf("✓ Configuration loaded\n")
	fmt.Printf("  Endpoint: %s\n", endpoint)

	// 2. Check connectivity
	client := immune.NewImmuneClient(endpoint)

	fmt.Print("  Testing connectivity... ")
	health, err := client.Health()
	if err != nil {
		fmt.Printf("❌ FAILED\n")
		fmt.Printf("  Error: %v\n", err)
		fmt.Println()
		printImmuneSuggestions()
		return nil
	}
	fmt.Printf("✓ SUCCESS\n")

	// 3. Check health
	fmt.Printf("  Service status: %s\n", health.Status)
	if health.Version != "" {
		fmt.Printf("  Version: %s\n", health.Version)
	}
	fmt.Printf("  Agents active: %d\n", health.AgentsActive)
	fmt.Printf("  Lymphnodes active: %d\n", health.LymphnodesActive)

	// 4. Try listing agents
	fmt.Print("  Testing API functionality... ")
	_, err = client.ListAgents("", "", "", 1, 5)
	if err != nil {
		fmt.Printf("⚠️  WARNING\n")
		fmt.Printf("  Error: %v\n", err)
	} else {
		fmt.Printf("✓ SUCCESS\n")
	}

	fmt.Println()
	fmt.Println("✅ Active Immune Core is operational")
	return nil
}

func troubleshootHITL() error {
	fmt.Println("👤 HITL Console")
	fmt.Println("────────────────")

	// 1. Check configuration
	endpoint := getHITLEndpoint()
	if endpoint == "" {
		endpoint = "http://localhost:8000/api" // default
	}

	fmt.Printf("✓ Configuration loaded\n")
	fmt.Printf("  Endpoint: %s\n", endpoint)

	// 2. Check connectivity (simple HTTP check)
	fmt.Print("  Testing connectivity... ")

	httpClient := &http.Client{Timeout: 5 * time.Second}
	resp, err := httpClient.Get(endpoint + "/health")
	if err != nil {
		fmt.Printf("❌ FAILED\n")
		fmt.Printf("  Error: %v\n", err)
		fmt.Println()
		printHITLSuggestions()
		return nil
	}
	defer resp.Body.Close()

	fmt.Printf("✓ SUCCESS\n")
	fmt.Printf("  HTTP Status: %d\n", resp.StatusCode)

	fmt.Println()
	if resp.StatusCode == 200 {
		fmt.Println("✅ HITL Console is operational")
	} else {
		fmt.Println("⚠️  HITL Console responded but with non-200 status")
	}
	return nil
}

func troubleshootConsciousness() error {
	fmt.Println("🧠 MAXIMUS Consciousness")
	fmt.Println("────────────────────────")

	endpoint := "http://localhost:8022" // default
	if env := os.Getenv("VCLI_CONSCIOUSNESS_ENDPOINT"); env != "" {
		endpoint = env
	}

	fmt.Printf("✓ Configuration loaded\n")
	fmt.Printf("  Endpoint: %s\n", endpoint)

	// Check connectivity
	fmt.Print("  Testing connectivity... ")

	httpClient := &http.Client{Timeout: 5 * time.Second}
	resp, err := httpClient.Get(endpoint + "/health")
	if err != nil {
		fmt.Printf("❌ FAILED\n")
		fmt.Printf("  Error: %v\n", err)
		return nil
	}
	defer resp.Body.Close()

	fmt.Printf("✓ SUCCESS\n")
	fmt.Printf("  HTTP Status: %d\n", resp.StatusCode)

	fmt.Println()
	if resp.StatusCode == 200 {
		fmt.Println("✅ MAXIMUS Consciousness is operational")
	} else {
		fmt.Println("⚠️  MAXIMUS Consciousness responded but with non-200 status")
	}
	return nil
}

func printMaximusSuggestions() {
	fmt.Println("💡 Troubleshooting Suggestions:")
	fmt.Println()
	fmt.Println("  1. Verify MAXIMUS service is running:")
	fmt.Println("     $ systemctl status maximus-governance")
	fmt.Println()
	fmt.Println("  2. Check endpoint configuration:")
	fmt.Println("     $ vcli configure show | grep maximus")
	fmt.Println()
	fmt.Println("  3. Test connectivity manually:")
	fmt.Println("     $ curl http://localhost:8150/governance/health")
	fmt.Println()
	fmt.Println("  4. Check service logs:")
	fmt.Println("     $ journalctl -u maximus-governance -n 50")
	fmt.Println()
	fmt.Println("  5. Verify firewall rules allow port 8150")
}

func printImmuneSuggestions() {
	fmt.Println("💡 Troubleshooting Suggestions:")
	fmt.Println()
	fmt.Println("  1. Verify Immune Core service is running:")
	fmt.Println("     $ systemctl status immune-core")
	fmt.Println()
	fmt.Println("  2. Check endpoint configuration:")
	fmt.Println("     $ vcli configure show | grep immune")
	fmt.Println()
	fmt.Println("  3. Test connectivity manually:")
	fmt.Println("     $ curl http://localhost:8200/health")
	fmt.Println()
	fmt.Println("  4. Check service logs:")
	fmt.Println("     $ journalctl -u immune-core -n 50")
	fmt.Println()
	fmt.Println("  5. Verify firewall rules allow port 8200")
}

func printHITLSuggestions() {
	fmt.Println("💡 Troubleshooting Suggestions:")
	fmt.Println()
	fmt.Println("  1. Verify HITL Console service is running:")
	fmt.Println("     $ systemctl status hitl-console")
	fmt.Println()
	fmt.Println("  2. Check endpoint configuration:")
	fmt.Println("     $ vcli configure show | grep hitl")
	fmt.Println()
	fmt.Println("  3. Test connectivity manually:")
	fmt.Println("     $ curl http://localhost:8000/api/health")
	fmt.Println()
	fmt.Println("  4. Check service logs:")
	fmt.Println("     $ journalctl -u hitl-console -n 50")
	fmt.Println()
	fmt.Println("  5. Verify firewall rules allow port 8000")
}

func init() {
	rootCmd.AddCommand(troubleshootCmd)
}
